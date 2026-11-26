"""Login helpers: user loading and role checks (throttle lives in redis_store)"""
from functools import wraps

from flask import jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user

from .extensions import db, login_manager
from .models import User


@login_manager.user_loader
def load_user(token):
    try:
        uid, version = (int(x) for x in str(token).split(":"))
    except ValueError:
        return None
    user = db.session.get(User, uid)
    return user if user and user.session_version == version else None


@login_manager.unauthorized_handler
def unauthorized():
    if request.accept_mimetypes.best == "application/json" or request.headers.get("Accept") == "application/json":
        return jsonify(error="Silakan masuk terlebih dahulu."), 401
    if request.method == "GET":
        session["return_to"] = request.full_path.rstrip("?")
    return redirect(url_for("auth.login"))


ROLE_HOME = {"admin": "/admin/bahan", "sponsor": "/resep"}


def home_for(user):
    """Start page per role: users get Home; admins land on ingredient verification; sponsors on their recipes."""
    return ROLE_HOME.get(getattr(user, "role", None), "/")


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if not current_user.is_authenticated:
                return unauthorized()
            if current_user.role not in roles:
                return render_template("error.html", title="Akses ditolak", message="Halaman ini hanya untuk " + " / ".join(roles) + "."), 403
            return fn(*a, **kw)
        return wrapper
    return deco
