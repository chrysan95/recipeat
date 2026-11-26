import re

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from ..extensions import db, limiter
from ..redis_store import login_blocked, login_failed, login_reset
from ..models import PasswordHistory, Preference, User
from ..security import hash_password, validate_password, verify_password

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")


def _start_session(user, default="/"):
    return_to = session.get("return_to")
    session.clear()
    current_app.session_interface.regenerate(session)  # new session id in Redis (prevents fixation)
    login_user(user)
    session.permanent = True
    target = return_to if return_to and return_to.startswith("/") and not return_to.startswith("//") else default
    return redirect(target)


@bp.route("/masuk", methods=["GET", "POST"])
@limiter.limit("30 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    if request.method == "GET":
        return render_template("auth/login.html", title="Masuk", error=None, values={})
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    key = f"{request.remote_addr}|{email}"

    def fail(error, status=400):
        return render_template("auth/login.html", title="Masuk", error=error, values={"email": email}), status

    if login_blocked(key):
        return fail("Terlalu banyak percobaan. Coba lagi dalam 15 menit.", 429)
    if not email or not password:
        return fail("Email dan kata sandi wajib diisi.")
    user = db.session.query(User).filter_by(email=email).first()
    if not verify_password(password, user.password_hash if user else None) or not user:
        login_failed(key)
        return fail("Email atau kata sandi salah.", 401)
    login_reset(key)
    return _start_session(user)


@bp.route("/daftar", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def signup():
    if current_user.is_authenticated:
        return redirect("/")
    if request.method == "GET":
        return render_template("auth/signup.html", title="Daftar", error=None, values={})
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    def fail(error):
        return render_template("auth/signup.html", title="Daftar", error=error, values={"name": name, "email": email}), 400

    if not 2 <= len(name) <= 60:
        return fail("Nama lengkap 2–60 karakter.")
    if not EMAIL_RE.match(email):
        return fail("Format email tidak valid.")
    if err := validate_password(password):
        return fail(err)
    if password != confirm:
        return fail("Konfirmasi kata sandi tidak sama.")
    if db.session.query(User).filter_by(email=email).first():
        return fail("Email sudah terdaftar. Silakan masuk.")

    h = hash_password(password)
    user = User(name=name, email=email, password_hash=h, role="user")
    db.session.add(user)
    db.session.flush()
    db.session.add_all([PasswordHistory(user_id=user.id, password_hash=h), Preference(user_id=user.id)])
    db.session.commit()
    session["return_to"] = "/profil/preferensi?baru=1"  # onboarding: personalise right after sign-up
    return _start_session(user)


@bp.post("/keluar")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
