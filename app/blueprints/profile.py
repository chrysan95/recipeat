"""Profile: acc info, change pass, personalize pref"""
import re

import bcrypt
from flask import Blueprint, flash, redirect, render_template, request
from flask_login import current_user, login_required, login_user
from sqlalchemy import text

from ..extensions import db, limiter
from ..models import PasswordHistory, User
from ..personalise import get_prefs
from ..recipes import approved_ingredients
from ..uploads import UploadError, remove_upload, save_image
from ..security import hash_password, validate_password, verify_password

bp = Blueprint("profile", __name__, url_prefix="/profil")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")
OPTIONS = {
    "portions": [("personal", "Personal (1–2)"), ("keluarga", "Keluarga (3–4)"), ("rame", "Rame-rame (5+)")],
    "tastes": [("asin", "Asin"), ("manis", "Manis"), ("pedas", "Pedas"), ("asam", "Asam"), ("gurih", "Gurih")],
    "meal_times": [("sarapan", "Sarapan"), ("makan-siang", "Makan Siang"), ("makan-malam", "Makan Malam"), ("camilan", "Camilan")],
    "diets": [("none", "Semua"), ("vegetarian", "Vegetarian"), ("vegan", "Vegan")],
}
COMMON_ALLERGENS = {"Udang", "Telur", "Kacang Tanah", "Susu Kental Manis", "Keju", "Ikan Kembung", "Tepung Terigu"}


@bp.before_request
@login_required
def _auth():
    pass


@bp.route("", methods=["GET", "POST"])
def account():
    values = {"name": current_user.name, "email": current_user.email, "newsletter": current_user.newsletter}
    if request.method == "GET":
        return render_template("profile/account.html", title="Profil", section="akun", values=values, error=None)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    values = {"name": name, "email": email, "newsletter": bool(request.form.get("newsletter"))}

    def fail(error):
        return render_template("profile/account.html", title="Profil", section="akun", values=values, error=error), 400

    if not 2 <= len(name) <= 60:
        return fail("Nama lengkap 2–60 karakter.")
    if not EMAIL_RE.match(email):
        return fail("Format email tidak valid.")
    user = db.session.get(User, current_user.id)
    if email != user.email:
        if db.session.query(User).filter(User.email == email, User.id != user.id).first():
            return fail("Email sudah dipakai akun lain.")
        if not verify_password(request.form.get("current_password", ""), user.password_hash):
            return fail("Masukkan kata sandi saat ini untuk mengubah email.")
    user.name, user.email, user.newsletter = name, email, values["newsletter"]
    db.session.commit()
    flash("Perubahan tersimpan.", "ok")
    return redirect("/profil")


@bp.route("/kata-sandi", methods=["GET", "POST"])
def password():
    if request.method == "GET":
        return render_template("profile/password.html", title="Profil", section="sandi", error=None)
    user = db.session.get(User, current_user.id)
    current, new, confirm = (request.form.get(k, "") for k in ("current", "password", "confirm"))

    def fail(error):
        return render_template("profile/password.html", title="Profil", section="sandi", error=error), 400

    if not verify_password(current, user.password_hash):
        return fail("Kata sandi lama salah.")
    if err := validate_password(new):
        return fail(err)
    if new != confirm:
        return fail("Konfirmasi kata sandi tidak sama.")
    history = db.session.query(PasswordHistory).filter_by(user_id=user.id).order_by(PasswordHistory.id.desc()).limit(10).all()
    if any(bcrypt.checkpw(new.encode("utf-8"), h.password_hash.encode("ascii")) for h in history):
        return fail("Kata sandi baru harus berbeda dari kata sandi yang pernah digunakan sebelumnya.")
    user.password_hash = hash_password(new)
    user.session_version += 1  # every other signed-in device is logged out
    db.session.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash))
    db.session.commit()
    login_user(user)  # keep this device signed in with the new version
    flash("Kata sandi berhasil diganti. Perangkat lain sudah dikeluarkan.", "ok")
    return redirect("/profil/kata-sandi")


@bp.route("/preferensi", methods=["GET", "POST"])
def preferences():
    if current_user.role != "user":  # food preferences only matter for regular users
        return redirect("/profil")
    valid_ids = {i["id"] for i in approved_ingredients()}
    if request.method == "POST":
        def pick(key, allowed):
            ok = {k for k, _ in allowed}
            return [v for v in request.form.getlist(key) if v in ok]
        diet = request.form.get("diet") if request.form.get("diet") in {k for k, _ in OPTIONS["diets"]} else "none"
        allergies = {int(x) for x in request.form.getlist("allergies") + [request.form.get("allergy_add", "")] if x.isdigit()} & valid_ids
        p = {"u": current_user.id, "portions": pick("portions", OPTIONS["portions"]), "tastes": pick("tastes", OPTIONS["tastes"]),
             "meal_times": pick("meal_times", OPTIONS["meal_times"]), "diet": diet, "halal": bool(request.form.get("halal_only"))}
        db.session.execute(text("""INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only)
            VALUES (:u, :portions, :tastes, :meal_times, :diet, :halal)
            ON CONFLICT (user_id) DO UPDATE SET portions = EXCLUDED.portions, tastes = EXCLUDED.tastes, meal_times = EXCLUDED.meal_times,
              diet = EXCLUDED.diet, halal_only = EXCLUDED.halal_only"""), p)
        db.session.execute(text("DELETE FROM user_allergies WHERE user_id = :u"), {"u": current_user.id})
        for a in allergies:
            db.session.execute(text("INSERT INTO user_allergies (user_id, ingredient_id) VALUES (:u, :i)"), {"u": current_user.id, "i": a})
        db.session.commit()
        flash("Preferensi tersimpan. Rekomendasi resep sudah disesuaikan.", "ok")
        return redirect("/" if request.form.get("welcome") else "/profil/preferensi")

    prefs = get_prefs(current_user.id)
    chosen = {a["id"] for a in prefs["allergies"]}
    all_ing = sorted(approved_ingredients(), key=lambda i: i["name"])
    chips = [i for i in all_ing if i["name"] in COMMON_ALLERGENS or i["id"] in chosen]
    return render_template("profile/preferences.html", title="Profil", section="preferensi", prefs=prefs, options=OPTIONS,
                           chips=chips, others=[i for i in all_ing if i not in chips], chosen=chosen, welcome=request.args.get("baru") == "1")


@bp.post("/foto")
@limiter.limit("20 per hour")
def photo():
    """Change or remove the profile picture (stored in the images table like other uploads)."""
    back = request.form.get("next", "")
    back = back if back.startswith("/") and not back.startswith("//") else "/profil"
    old = current_user.avatar_url
    if request.form.get("action") == "remove":
        current_user.avatar_url = None
        db.session.commit()
        remove_upload(old)
        flash("Foto profil dihapus.", "ok")
    else:
        try:
            url = save_image(request.files.get("photo"))
        except UploadError as e:
            flash(str(e), "error")
            return redirect(back)
        if not url:
            flash("Pilih foto terlebih dahulu.", "error")
            return redirect(back)
        current_user.avatar_url = url
        db.session.commit()
        remove_upload(old)
        flash("Foto profil diperbarui.", "ok")
    return redirect(back)
