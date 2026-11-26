"""Admin: Verify Ingredient · Sponsor: Manage Promotion · Notifications for everyone"""
import re
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import text

from ..auth_utils import role_required
from ..extensions import db
from ..recipes import list_recipes
from ..redis_store import cache_clear
from ..uploads import UploadError, remove_upload, save_image

bp = Blueprint("roles", __name__)
LINK_RE = re.compile(r"^(/(?!/)\S*|https://\S+)$")


def notify(user_id, title, body, link=None):
    db.session.execute(text("INSERT INTO notifications (user_id, sender, title, body, link) VALUES (:u, 'Recipeat', :t, :b, :l)"),
                       {"u": user_id, "t": title, "b": body, "l": link})


# ================= Admin: Verify Ingredient =================
@bp.get("/admin/bahan")
@role_required("admin")
def admin_ingredients():
    s = db.session
    pending = s.execute(text("""SELECT i.*, c.name AS category, u.name AS requester FROM ingredients i
        JOIN ingredient_categories c ON c.id = i.category_id LEFT JOIN users u ON u.id = i.requested_by
        WHERE i.status = 'pending' ORDER BY i.created_at""")).mappings().all()
    show_all = request.args.get("semua") == "1"
    history = s.execute(text("""SELECT i.name, i.status, i.review_note, u.name AS requester FROM ingredients i
        LEFT JOIN users u ON u.id = i.requested_by WHERE i.requested_by IS NOT NULL
        ORDER BY i.created_at DESC""" + ("" if show_all else " LIMIT 10"))).mappings().all()
    cats = s.execute(text("SELECT id, name FROM ingredient_categories ORDER BY position")).mappings().all()
    return render_template("admin/ingredients.html", title="Verifikasi Bahan", active="resep", pending=pending, history=history,
                           cats=cats, show_all=show_all)


@bp.post("/admin/bahan/<int:ing_id>")
@role_required("admin")
def admin_decide(ing_id):
    s = db.session
    ing = s.execute(text("SELECT * FROM ingredients WHERE id = :id AND status = 'pending'"), {"id": ing_id}).mappings().first()
    if not ing:
        flash("Pengajuan tidak ditemukan atau sudah diproses.", "error")
        return redirect("/admin/bahan")
    action = request.form.get("action")
    if action == "approve":
        name = " ".join((request.form.get("name") or ing["name"]).split())
        try:
            category_id = int(request.form.get("category_id") or ing["category_id"])
        except ValueError:
            category_id = ing["category_id"]
        if not 2 <= len(name) <= 40:
            flash("Nama bahan 2–40 karakter.", "error")
            return redirect("/admin/bahan")
        if s.execute(text("SELECT 1 FROM ingredients WHERE lower(name) = lower(:n) AND status = 'approved'"), {"n": name}).first():
            flash(f'"{name}" sudah ada. Tolak pengajuan ini sebagai duplikat.', "error")
            return redirect("/admin/bahan")
        try:  # the admin may replace the requester's photo (pencil on the photo)
            new_photo = save_image(request.files.get("photo"))
        except UploadError as e:
            flash(str(e), "error")
            return redirect("/admin/bahan")
        vegan = bool(request.form.get("is_vegan"))
        s.execute(text("""UPDATE ingredients SET name = :n, category_id = :c, is_vegan = :v, is_vegetarian = :vg, is_halal = :h,
            image_url = COALESCE(:img, image_url), status = 'approved', reviewed_by = :a, reviewed_at = now(), review_note = NULL WHERE id = :id"""),
                  {"n": name, "c": category_id, "v": vegan, "vg": vegan or bool(request.form.get("is_vegetarian")),
                   "h": bool(request.form.get("is_halal")), "img": new_photo, "a": current_user.id, "id": ing_id})
        if ing["requested_by"]:
            notify(ing["requested_by"], f'Bahan "{name}" disetujui', "Bahan ajuanmu sekarang bisa dipakai di Racik dan resep.", "/racik")
        s.commit()
        if new_photo:
            remove_upload(ing["image_url"])
        cache_clear("ingredients")
        flash(f'"{name}" disetujui.', "ok")
    elif action == "reject":
        note = request.form.get("review_note", "").strip()[:200]
        if not note:
            flash("Tulis alasan penolakan agar pengaju paham.", "error")
            return redirect("/admin/bahan")
        s.execute(text("""UPDATE ingredients SET status = 'rejected', reviewed_by = :a, reviewed_at = now(), review_note = :n, image_url = NULL
            WHERE id = :id"""), {"a": current_user.id, "n": note, "id": ing_id})
        if ing["requested_by"]:
            notify(ing["requested_by"], f'Bahan "{ing["name"]}" ditolak', note, "/bahan/ajukan")
        s.commit()
        remove_upload(ing["image_url"])
        flash(f'"{ing["name"]}" ditolak.', "ok")
    return redirect("/admin/bahan")


# ================= Sponsor: Manage Promotion =================
def parse_promo(form):
    def d(v):
        try:
            return date.fromisoformat(v)
        except (TypeError, ValueError):
            return None
    return {
        "brand": form.get("brand", "").strip()[:40], "title": form.get("title", "").strip()[:80], "body": form.get("body", "").strip()[:300],
        "cta_label": form.get("cta_label", "").strip()[:30], "cta_url": form.get("cta_url", "").strip(),
        "recipe_ids": [int(x) for x in form.getlist("recipe_ids") if x.isdigit()][:4],
        "starts_on": d(form.get("starts_on")), "ends_on": d(form.get("ends_on")) if form.get("ends_on") else None,
        "active": bool(form.get("active")), "broadcast": bool(form.get("broadcast")),
    }


def validate_promo(v):
    if len(v["brand"]) < 2:
        return "Isi nama brand."
    if len(v["title"]) < 3:
        return "Judul promosi minimal 3 karakter."
    if v["cta_url"] and not LINK_RE.match(v["cta_url"]):
        return 'Link harus diawali "/" (halaman Recipeat) atau "https://".'
    if not v["starts_on"]:
        return "Tanggal mulai tidak valid."
    if v["ends_on"] and v["ends_on"] < v["starts_on"]:
        return "Tanggal selesai harus setelah tanggal mulai."
    return None


def promo_form(v, error=None):
    recipes = list_recipes(user_id=current_user.id, sort="populer")
    return render_template("sponsor/form.html", title="Ubah Promosi" if v.get("id") else "Promosi Baru", active="notifikasi",
                           v=v, recipes=recipes, error=error), 400 if error else 200


def save_promo(v, sponsor_id, promo_id=None):
    s = db.session
    p = {k: v[k] for k in ("brand", "title", "body", "recipe_ids", "starts_on", "ends_on", "active")}
    p.update(cta_label=v["cta_label"] or None, cta_url=v["cta_url"] or None)
    if promo_id:
        s.execute(text("""UPDATE promotions SET brand=:brand, title=:title, body=:body, cta_label=:cta_label, cta_url=:cta_url,
            recipe_ids=:recipe_ids, starts_on=:starts_on, ends_on=:ends_on, active=:active WHERE id = :id"""), {**p, "id": promo_id})
    else:
        promo_id = s.execute(text("""INSERT INTO promotions (sponsor_id, brand, title, body, cta_label, cta_url, recipe_ids, starts_on, ends_on, active)
            VALUES (:sid, :brand, :title, :body, :cta_label, :cta_url, :recipe_ids, :starts_on, :ends_on, :active) RETURNING id"""),
                             {**p, "sid": sponsor_id}).scalar_one()
    if v["broadcast"] and v["active"]:
        s.execute(text("""INSERT INTO notifications (user_id, sender, title, body, link, recipe_ids, promotion_id)
            VALUES (NULL, :brand, :title, :body, :link, :ids, :pid)"""),
                  {"brand": v["brand"], "title": v["title"], "body": v["body"], "link": v["cta_url"] or None, "ids": v["recipe_ids"], "pid": promo_id})
    s.commit()


def own_promo(promo_id):
    p = db.session.execute(text("SELECT * FROM promotions WHERE id = :id"), {"id": promo_id}).mappings().first()
    if not p or (p["sponsor_id"] != current_user.id and current_user.role != "admin"):
        abort(404)
    return dict(p)


@bp.get("/sponsor/promosi")
@role_required("sponsor", "admin")
def promos():
    rows = db.session.execute(text("""SELECT p.*, (SELECT COUNT(*) FROM notifications n WHERE n.promotion_id = p.id) AS sent
        FROM promotions p WHERE p.sponsor_id = :u OR :role = 'admin' ORDER BY p.created_at DESC"""),
                              {"u": current_user.id, "role": current_user.role}).mappings().all()
    return render_template("sponsor/list.html", title="Kelola Promosi", active="notifikasi", promos=rows, today=date.today())


@bp.route("/sponsor/promosi/baru", methods=["GET", "POST"])
@role_required("sponsor", "admin")
def promo_new():
    if request.method == "GET":
        return promo_form({"brand": current_user.name, "title": "", "body": "", "cta_label": "Lihat resep", "cta_url": "", "recipe_ids": [],
                           "starts_on": date.today(), "ends_on": None, "active": True, "broadcast": True})
    v = parse_promo(request.form)
    if err := validate_promo(v):
        return promo_form(v, err)
    save_promo(v, current_user.id)
    flash("Promosi tayang dan notifikasi terkirim." if v["broadcast"] and v["active"] else "Promosi tersimpan.", "ok")
    return redirect("/sponsor/promosi")


@bp.route("/sponsor/promosi/<int:promo_id>", methods=["GET", "POST"])
@role_required("sponsor", "admin")
def promo_edit(promo_id):
    p = own_promo(promo_id)
    if request.method == "GET":
        return promo_form({**p, "broadcast": False})
    action = request.form.get("action")
    if action == "delete":
        db.session.execute(text("DELETE FROM promotions WHERE id = :id"), {"id": promo_id})
        db.session.commit()
        flash("Promosi dihapus.", "ok")
        return redirect("/sponsor/promosi")
    if action == "toggle":
        db.session.execute(text("UPDATE promotions SET active = NOT active WHERE id = :id"), {"id": promo_id})
        db.session.commit()
        return redirect("/sponsor/promosi")
    v = {**parse_promo(request.form), "id": promo_id}
    if err := validate_promo(v):
        return promo_form(v, err)
    save_promo(v, p["sponsor_id"], promo_id)
    flash("Promosi diperbarui.", "ok")
    return redirect("/sponsor/promosi")


# ================= Notifications =================
@bp.get("/notifikasi")
@login_required
def notifications():
    if current_user.role == "sponsor":  # a sponsor's bell tab is where they manage promotions
        return redirect("/sponsor/promosi")
    rows = db.session.execute(text("""SELECT n.* FROM notifications n LEFT JOIN promotions p ON p.id = n.promotion_id
        WHERE (n.user_id = :u OR n.user_id IS NULL) AND (n.promotion_id IS NULL OR p.active)
        ORDER BY n.created_at DESC LIMIT 50"""), {"u": current_user.id}).mappings().all()
    items = [dict(n) for n in rows]
    wanted = {i for n in items for i in (n["recipe_ids"] or [])}
    by_id = {r["id"]: r for r in list_recipes(user_id=current_user.id, ids=wanted)} if wanted else {}
    for n in items:
        n["recipes"] = [by_id[i] for i in (n["recipe_ids"] or []) if i in by_id]
    today = date.today()
    groups = [("Hari ini", [n for n in items if n["created_at"].date() == today]), ("Sebelumnya", [n for n in items if n["created_at"].date() != today])]
    return render_template("notifications.html", title="Notifikasi", active="notifikasi", groups=groups)
