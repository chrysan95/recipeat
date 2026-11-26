"""Dummy data + CLI commands.

    flask seed            # insert dummy data if the database is empty
    flask seed --reset    # wipe all rows and insert dummy data again
    flask dump-sql        # write database/recipeat_dummy.sql (schema + data, PostgreSQL)
"""
import json
import os
import re
from datetime import date, datetime, timedelta, timezone

import click
from flask import current_app
from sqlalchemy import text
from sqlalchemy.schema import CreateIndex, CreateTable

from .photo_credits import ingredient_image, recipe_image
from .extensions import db
from .models import (Bookmark, Ingredient, IngredientCategory, Notification, PasswordHistory, Preference, Promotion,
                     Recipe, RecipeIngredient, RecipeStep, RecipeTag, Review, Tag, User, UserAllergy)
from .security import hash_password

DATA = json.load(open(os.path.join(os.path.dirname(__file__), "seed_data.json"), encoding="utf-8"))


def slugify(s):
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "dan")))


def seed():
    now = datetime.now(timezone.utc)
    users = {}
    for u in DATA["USERS"]:
        h = hash_password(u["password"])
        user = User(name=u["name"], email=u["email"], password_hash=h, role=u["role"], newsletter=u["newsletter"])
        db.session.add(user)
        db.session.flush()
        db.session.add(PasswordHistory(user_id=user.id, password_hash=h))
        users[u["email"]] = user.id
    admin = users["admin@recipeat.id"]

    cats = {}
    for i, name in enumerate(DATA["CATEGORIES"]):
        c = IngredientCategory(name=name, slug=slugify(name), position=i)
        db.session.add(c)
        db.session.flush()
        cats[name] = c.id

    ings = {}
    for name, cat, flags, pop in DATA["INGREDIENTS"]:
        vegan = "v" in flags
        i = Ingredient(name=name, category_id=cats[cat], is_vegan=vegan, is_vegetarian=vegan or "g" in flags,
                       is_halal="x" not in flags, popularity=pop, status="approved", reviewed_by=admin, reviewed_at=now,
                       image_url=ingredient_image(name))
        db.session.add(i)
        db.session.flush()
        ings[name] = i.id

    # Ingredient requests waiting for admin verification
    db.session.add_all([
        Ingredient(name="Andaliman", category_id=cats["Rempah"], status="pending", requested_by=users["keisa@gmail.com"], request_note="Rempah khas Batak untuk arsik."),
        Ingredient(name="Kecombrang", category_id=cats["Sayur"], status="pending", requested_by=users["budi@gmail.com"], request_note="Bunga honje untuk sambal dan pecak."),
        Ingredient(name="Bawang Merah Brebes", category_id=cats["Bumbu Dapur"], status="rejected", requested_by=users["sari@gmail.com"],
                   reviewed_by=admin, reviewed_at=now, review_note='Sudah tersedia sebagai "Bawang Merah".'),
    ])

    tags = {}
    for name, slug, kind in DATA["TAGS"]:
        t = Tag(name=name, slug=slug, kind=kind)
        db.session.add(t)
        db.session.flush()
        tags[slug] = t.id

    recipe_ids = []
    n = len(DATA["RECIPES"])
    for idx, r in enumerate(DATA["RECIPES"]):
        when = now - timedelta(days=(n - idx) * 3)
        rec = Recipe(author_id=users[r["author"]], title=r["title"], description=r["description"], origin=r.get("origin"),
                     video_url=r.get("video"), prep_minutes=r["prep"], cook_minutes=r["cook"], price_min=r["price"][0],
                     price_max=r["price"][1], servings=r["servings"], image_url=recipe_image(r["title"]), created_at=when, updated_at=when)
        db.session.add(rec)
        db.session.flush()
        recipe_ids.append(rec.id)
        db.session.add_all([RecipeTag(recipe_id=rec.id, tag_id=tags[t]) for t in r["tags"]])
        for pos, row in enumerate(r["ingredients"]):
            name, qty, unit = row[0], row[1], row[2]
            note = row[3] if len(row) > 3 else ""
            db.session.add(RecipeIngredient(recipe_id=rec.id, ingredient_id=ings[name], quantity=qty, unit=unit or "", note=note or "", position=pos))
        for pos, (title, body) in enumerate(r["steps"], start=1):
            db.session.add(RecipeStep(recipe_id=rec.id, position=pos, title=title, body=body))

    reviewers = [users[e] for e in ("keisa@gmail.com", "budi@gmail.com", "sari@gmail.com")]
    lines = DATA["REVIEW_LINES"]
    for i, rid in enumerate(recipe_ids):
        for j, uid in enumerate(reviewers):
            if (i + j) % 3 == 2:
                continue
            db.session.add(Review(recipe_id=rid, user_id=uid, rating=[5, 4, 5, 3, 4, 5, 5, 4, 5][(i * 2 + j * 5) % 9], comment=lines[(i + j) % len(lines)]))
    for email, picks in (("keisa@gmail.com", [0, 1, 4, 8]), ("budi@gmail.com", [0, 2, 3, 13]), ("sari@gmail.com", [0, 6, 7, 12])):
        db.session.add_all([Bookmark(user_id=users[email], recipe_id=recipe_ids[i]) for i in picks])

    # Keisa matches the Figma "Preferensi Makanan" screen
    db.session.add_all([
        Preference(user_id=users["keisa@gmail.com"], portions=["rame"], tastes=["pedas", "gurih"], meal_times=["makan-malam"], diet="none", halal_only=True),
        Preference(user_id=users["budi@gmail.com"], portions=["keluarga"], tastes=["asin", "gurih"], meal_times=["makan-siang", "makan-malam"]),
        Preference(user_id=users["sari@gmail.com"], portions=["personal"], tastes=["manis", "pedas"], meal_times=["sarapan", "camilan"], diet="vegan", halal_only=True),
        Preference(user_id=admin), Preference(user_id=users["sponsor@dapurnusa.id"]),
        UserAllergy(user_id=users["keisa@gmail.com"], ingredient_id=ings["Udang"]),
    ])

    featured = [recipe_ids[i] for i in (0, 1, 5, 9)]
    promo = Promotion(sponsor_id=users["sponsor@dapurnusa.id"], brand="Dapurnusa", title="Masak apa ya hari ini?",
                      body="Cobain rekomendasi resep di bawah ini. Jangan lupa recook, ya!", cta_label="Lihat resep",
                      cta_url="/cari?jenis=berat", recipe_ids=featured, ends_on=date.today() + timedelta(days=30))
    db.session.add(promo)
    db.session.flush()
    db.session.add_all([
        Notification(sender="Dapurnusa", title=promo.title, body=promo.body, recipe_ids=featured, promotion_id=promo.id, created_at=now - timedelta(hours=1)),
        Notification(user_id=users["keisa@gmail.com"], title="Resepmu disimpan 12 orang", body="Martabak Manis Coklat Keju makin populer minggu ini.",
                     link="/resep", created_at=now - timedelta(days=2)),
    ])
    db.session.commit()


def wipe():
    tables = ", ".join(t.name for t in db.metadata.sorted_tables)
    db.session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    db.session.commit()


def _sql_value(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (bytes, memoryview)):
        return "'\\x" + bytes(v).hex() + "'::bytea"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "'{" + ",".join(str(x) for x in v) + "}'"
    if isinstance(v, (datetime, date)):
        return f"'{v.isoformat()}'"
    return "'" + str(v).replace("'", "''") + "'"


def register_commands(app):
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Hapus semua data lalu isi ulang data dummy.")
    def seed_command(reset):
        """Isi database dengan data dummy."""
        if reset:
            wipe()
        if db.session.query(User).count():
            click.echo("Database sudah berisi data. Pakai --reset untuk membuat ulang.")
            return
        seed()
        click.echo("Data dummy dimuat.")

    @app.cli.command("dump-sql")
    def dump_sql():
        """Tulis database/recipeat_dummy.sql (skema + data) dari database saat ini."""
        dialect = db.engine.dialect
        out = [f"-- Recipeat dummy database for PostgreSQL (generated {date.today()} by `flask dump-sql`)",
               "-- Passwords are bcrypt hashes. Demo logins are listed in README.md.",
               "-- Load with: psql \"$DATABASE_URL\" -f database/recipeat_dummy.sql", ""]
        for t in db.metadata.sorted_tables:
            out.append(str(CreateTable(t).compile(dialect=dialect)).strip() + ";")
            out += [str(CreateIndex(ix).compile(dialect=dialect)).strip() + ";" for ix in t.indexes]
            out.append("")
        out.append("BEGIN;")
        for t in db.metadata.sorted_tables:
            rows = db.session.execute(t.select().order_by(*t.primary_key.columns)).mappings().all()
            if not rows:
                continue
            out.append(f"\n-- {t.name} ({len(rows)})")
            cols = ", ".join(rows[0].keys())
            out += [f"INSERT INTO {t.name} ({cols}) VALUES ({', '.join(_sql_value(v) for v in r.values())});" for r in rows]
            if "id" in t.c:
                out.append(f"SELECT setval(pg_get_serial_sequence('{t.name}', 'id'), (SELECT MAX(id) FROM {t.name}));")
        out.append("COMMIT;")
        path = os.path.join(os.path.dirname(current_app.root_path), "database", "recipeat_dummy.sql")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        click.echo(f"Ditulis: database/recipeat_dummy.sql ({len(db.metadata.sorted_tables)} tabel)")
