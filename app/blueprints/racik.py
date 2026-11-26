"""Concoct Recipe (Racik) and Request New Ingredient"""
from flask import Blueprint, flash, redirect, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import bindparam, text

from ..extensions import db, limiter
from ..personalise import avoid_for
from ..recipes import approved_ingredients, categories, list_recipes
from ..uploads import UploadError, save_image

bp = Blueprint("racik", __name__)
STAPLES = ("Garam", "Gula", "Minyak Goreng", "Air")  # treated as already in the kitchen


@bp.before_request
@login_required
def _auth():
    pass


@bp.get("/racik")
def index():
    cats = categories()
    all_ing = approved_ingredients()
    active = next((c for c in cats if c["slug"] == request.args.get("kategori")), None) or next((c for c in cats if c["slug"] == "sayur"), cats[0])
    popular = sorted(all_ing, key=lambda i: -i["popularity"])[:6]
    return render_template("racik/index.html", title="Racik", active="racik", cats=cats, all=all_ing, current=active, popular=popular)


@bp.get("/racik/hasil")
def results():
    ids = [int(x) for x in request.args.get("bahan", "").split(",") if x.strip().isdigit()][:40]
    by_id = {i["id"]: i for i in approved_ingredients()}
    basket = [by_id[i] for i in dict.fromkeys(ids) if i in by_id]
    recipes = []
    if basket:
        staples = [i["id"] for i in by_id.values() if i["name"] in STAPLES]
        have = list({*(b["id"] for b in basket), *staples})
        stmt = text("""SELECT ri.recipe_id,
              SUM(CASE WHEN ri.ingredient_id IN :have THEN 1 ELSE 0 END) AS matched,
              SUM(CASE WHEN ri.ingredient_id IN :basket THEN 1 ELSE 0 END) AS from_basket,
              COUNT(*) AS total
            FROM recipe_ingredients ri GROUP BY ri.recipe_id
            HAVING SUM(CASE WHEN ri.ingredient_id IN :basket THEN 1 ELSE 0 END) > 0""").bindparams(
            bindparam("have", expanding=True), bindparam("basket", expanding=True))
        m = {r.recipe_id: r for r in db.session.execute(stmt, {"have": have, "basket": [b["id"] for b in basket]})}
        recipes = list_recipes(user_id=current_user.id, ids=list(m), avoid=avoid_for(current_user.id))
        for r in recipes:
            r["matched"], r["ingredient_total"] = m[r["id"]].matched, m[r["id"]].total
        recipes.sort(key=lambda r: (-r["matched"] / r["ingredient_total"], -r["matched"], -r["rating"]))
    return render_template("racik/results.html", title="Hasil Racik", active="racik", basket=basket, recipes=recipes)


# ---------- Request New Ingredient ----------
def request_page(error=None, values=None):
    mine = db.session.execute(text("""SELECT i.name, i.status, i.review_note, i.created_at, c.name AS category FROM ingredients i
        JOIN ingredient_categories c ON c.id = i.category_id WHERE i.requested_by = :u ORDER BY i.created_at DESC"""), {"u": current_user.id}).mappings().all()
    return render_template("racik/request.html", title="Ajukan Bahan Baru", active="racik" if current_user.role == "user" else "resep",
                           back={"admin": "/admin/bahan", "sponsor": "/resep"}.get(current_user.role, "/racik"), cats=categories(), mine=mine,
                           error=error, values=values or {}), 400 if error else 200


@bp.get("/bahan/ajukan")
def request_form():
    return request_page()


@bp.post("/bahan/ajukan")
@limiter.limit("10 per hour")
def request_submit():
    name = " ".join(request.form.get("name", "").split())
    try:
        category_id = int(request.form.get("category_id", ""))
    except ValueError:
        category_id = 0
    note = request.form.get("note", "").strip()[:300]
    values = {"name": name, "category_id": category_id, "note": note}
    if not 2 <= len(name) <= 40:
        return request_page("Nama bahan 2–40 karakter.", values)
    if category_id not in {c["id"] for c in categories()}:
        return request_page("Pilih kategori bahan.", values)
    dup = db.session.execute(text("SELECT status FROM ingredients WHERE lower(name) = lower(:n) AND status IN ('approved','pending')"), {"n": name}).scalar()
    if dup:
        return request_page(f'"{name}" sudah tersedia di daftar bahan.' if dup == "approved" else f'"{name}" sedang menunggu verifikasi.', values)
    open_count = db.session.execute(text("SELECT COUNT(*) FROM ingredients WHERE requested_by = :u AND status = 'pending'"), {"u": current_user.id}).scalar()
    if open_count >= 5:
        return request_page("Maksimal 5 pengajuan yang menunggu verifikasi.", values)
    try:
        photo = save_image(request.files.get("photo"))
    except UploadError as e:
        return request_page(str(e), values)
    if not photo:
        return request_page("Sertakan foto bahan agar admin bisa memverifikasi.", values)
    try:
        db.session.execute(text("""INSERT INTO ingredients (name, category_id, image_url, status, requested_by, request_note)
            VALUES (:n, :c, :img, 'pending', :u, :note)"""), {"n": name, "c": category_id, "img": photo, "u": current_user.id, "note": note})
        db.session.commit()
    except Exception:
        db.session.rollback()  # also discards the uploaded image (same transaction)
        raise
    flash(f'Pengajuan "{name}" terkirim. Kami kabari setelah admin memverifikasi.', "ok")
    return redirect("/bahan/ajukan")
