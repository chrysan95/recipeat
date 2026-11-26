"""Add Recipe (+add visual ref) and edit/delete own recipes"""
import re

from flask import Blueprint, abort, flash, redirect, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import text

from ..extensions import db, limiter
from ..recipes import approved_ingredients, get_recipe
from ..uploads import UploadError, remove_upload, save_image

bp = Blueprint("editor", __name__)
URL_RE = re.compile(r"^https?://\S+$", re.I)


@bp.before_request
@login_required
def _auth():
    pass


def _int(v, lo, hi):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def parse(form):
    v = {
        "title": form.get("title", "").strip(), "description": form.get("description", "").strip(),
        "origin": form.get("origin", "").strip(), "video_url": form.get("video_url", "").strip(),
        "prep_minutes": _int(form.get("prep_minutes"), 0, 1440), "cook_minutes": _int(form.get("cook_minutes"), 0, 1440),
        "price_min": _int(form.get("price_min"), 0, 100_000_000) if form.get("price_min") else None,
        "price_max": _int(form.get("price_max"), 0, 100_000_000) if form.get("price_max") else None,
        "servings": _int(form.get("servings"), 1, 50), "status": "draft" if form.get("status") == "draft" else "published",
        "tag_ids": [int(t) for t in form.getlist("tags") if t.isdigit()], "ingredients": [], "steps": [],
    }
    ids, qty, unit, note = (form.getlist(k) for k in ("ing_id", "ing_qty", "ing_unit", "ing_note"))
    for i, iid in enumerate(ids):
        if not iid.isdigit():
            continue
        q = (qty[i] if i < len(qty) else "").replace(",", ".").strip()
        try:
            qv = float(q) if q else None
        except ValueError:
            qv = -1.0
        v["ingredients"].append({"ingredient_id": int(iid), "quantity": qv, "unit": (unit[i] if i < len(unit) else "").strip()[:20],
                                 "note": (note[i] if i < len(note) else "").strip()[:40]})
    titles, bodies, medias = (form.getlist(k) for k in ("step_title", "step_body", "step_media"))
    for i, t in enumerate(titles):
        t, b = t.strip(), (bodies[i] if i < len(bodies) else "").strip()
        if t or b:
            v["steps"].append({"title": t[:60], "body": b[:1000], "media_url": (medias[i] if i < len(medias) else "").strip() or None})
    return v


def validate(v):
    if not 3 <= len(v["title"]) <= 80:
        return "Nama resep 3–80 karakter."
    if len(v["description"]) > 400:
        return "Deskripsi maksimal 400 karakter."
    if v["prep_minutes"] is None or v["cook_minutes"] is None:
        return "Isi waktu persiapan dan memasak (menit)."
    if v["servings"] is None:
        return "Porsi harus 1–50."
    if v["price_min"] is not None and v["price_max"] is not None and v["price_min"] > v["price_max"]:
        return "Harga minimum tidak boleh lebih besar dari maksimum."
    if v["video_url"] and not URL_RE.match(v["video_url"]):
        return "Link video harus diawali http:// atau https://"
    if not v["ingredients"]:
        return "Tambahkan minimal satu bahan."
    if any(i["quantity"] is not None and not i["quantity"] > 0 for i in v["ingredients"]):
        return "Jumlah bahan harus angka lebih dari 0 (kosongkan jika secukupnya)."
    if not v["steps"]:
        return "Tambahkan minimal satu langkah."
    if any(not s["title"] or not s["body"] for s in v["steps"]):
        return "Setiap langkah butuh judul dan penjelasan."
    if any(s["media_url"] and not URL_RE.match(s["media_url"]) for s in v["steps"]):
        return "Link media langkah harus diawali http:// atau https://"
    ok = {i["id"] for i in approved_ingredients()}
    if any(i["ingredient_id"] not in ok for i in v["ingredients"]):
        return "Ada bahan yang belum terverifikasi."
    return None


def save(v, recipe_id=None, image_url=None):
    s = db.session
    cols = {k: v[k] or None if k in ("origin", "video_url") else v[k] for k in
            ("title", "description", "origin", "video_url", "prep_minutes", "cook_minutes", "price_min", "price_max", "servings", "status")}
    if recipe_id:
        s.execute(text("""UPDATE recipes SET title=:title, description=:description, origin=:origin, video_url=:video_url,
            prep_minutes=:prep_minutes, cook_minutes=:cook_minutes, price_min=:price_min, price_max=:price_max, servings=:servings,
            status=:status, image_url = COALESCE(:img, image_url), updated_at = now() WHERE id = :id AND author_id = :u"""),
                  {**cols, "img": image_url, "id": recipe_id, "u": current_user.id})
        for t in ("recipe_tags", "recipe_ingredients", "recipe_steps"):
            s.execute(text(f"DELETE FROM {t} WHERE recipe_id = :id"), {"id": recipe_id})
    else:
        recipe_id = s.execute(text("""INSERT INTO recipes (title, description, origin, video_url, prep_minutes, cook_minutes, price_min, price_max,
            servings, status, image_url, author_id) VALUES (:title, :description, :origin, :video_url, :prep_minutes, :cook_minutes,
            :price_min, :price_max, :servings, :status, :img, :u) RETURNING id"""), {**cols, "img": image_url, "u": current_user.id}).scalar_one()
    valid_tags = {x for (x,) in s.execute(text("SELECT id FROM tags"))}
    for t in set(v["tag_ids"]) & valid_tags:
        s.execute(text("INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (:r, :t)"), {"r": recipe_id, "t": t})
    for pos, i in enumerate(v["ingredients"]):
        s.execute(text("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, note, position) VALUES (:r, :i, :q, :u, :n, :p)"),
                  {"r": recipe_id, "i": i["ingredient_id"], "q": i["quantity"], "u": i["unit"], "n": i["note"], "p": pos})
    for pos, st in enumerate(v["steps"], start=1):
        s.execute(text("INSERT INTO recipe_steps (recipe_id, position, title, body, media_url) VALUES (:r, :p, :t, :b, :m)"),
                  {"r": recipe_id, "p": pos, "t": st["title"], "b": st["body"], "m": st["media_url"]})
    s.commit()
    return recipe_id


def render(v, error=None):
    groups = {}
    for i in approved_ingredients():
        groups.setdefault(i["category_name"], []).append(i)
    tags = [dict(t) for t in db.session.execute(text("SELECT id, name, slug, kind FROM tags ORDER BY kind, id")).mappings()]
    pending = [n for (n,) in db.session.execute(text("SELECT name FROM ingredients WHERE status = 'pending' AND requested_by = :u"), {"u": current_user.id})]
    return render_template("recipes/editor.html", title="Ubah Resep" if v.get("id") else "Tambah Resep", active="resep",
                           v=v, error=error, groups=groups, tags=tags, pending=pending), 400 if error else 200


EMPTY = {"title": "", "description": "", "origin": "", "video_url": "", "prep_minutes": 10, "cook_minutes": 20, "price_min": "", "price_max": "",
         "servings": 2, "status": "published", "tag_ids": [], "ingredients": [{}], "steps": [{}]}


@bp.get("/resep/baru")
def new():
    return render(EMPTY)


@bp.post("/resep/baru")
@limiter.limit("20 per hour")
def create():
    v = parse(request.form)
    if err := validate(v):
        return render(v, err)
    try:
        img = save_image(request.files.get("image"))
    except UploadError as e:
        return render(v, str(e))
    rid = save(v, image_url=img)
    flash("Draf resep tersimpan." if v["status"] == "draft" else "Resepmu sudah terbit. Terima kasih sudah berbagi!", "ok")
    return redirect("/resep" if v["status"] == "draft" else f"/resep/{rid}")


def own(recipe_id):
    r = get_recipe(recipe_id, current_user.id)
    if not r or r["author_id"] != current_user.id:
        abort(404)
    return r


@bp.get("/resep/<int:recipe_id>/ubah")
def edit(recipe_id):
    r = own(recipe_id)
    r["tag_ids"] = [t["id"] for t in r["tags"]]
    r["price_min"] = r["price_min"] if r["price_min"] is not None else ""
    r["price_max"] = r["price_max"] if r["price_max"] is not None else ""
    return render(r)


@bp.post("/resep/<int:recipe_id>/ubah")
def update(recipe_id):
    r = own(recipe_id)
    v = {**parse(request.form), "id": r["id"], "image_url": r["image_url"]}
    if err := validate(v):
        return render(v, err)
    try:
        img = save_image(request.files.get("image"))
    except UploadError as e:
        return render(v, str(e))
    save(v, recipe_id=r["id"], image_url=img)
    if img:
        remove_upload(r["image_url"])
    flash("Perubahan resep tersimpan.", "ok")
    return redirect(f"/resep/{r['id']}")


@bp.post("/resep/<int:recipe_id>/hapus")
def delete(recipe_id):
    r = own(recipe_id)
    db.session.execute(text("DELETE FROM recipes WHERE id = :id AND author_id = :u"), {"id": r["id"], "u": current_user.id})
    db.session.commit()
    remove_upload(r["image_url"])
    flash(f'Resep "{r["title"]}" dihapus.', "ok")
    return redirect("/resep")
