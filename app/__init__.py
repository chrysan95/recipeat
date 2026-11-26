import hashlib
import os
from functools import lru_cache

from dotenv import load_dotenv
from flask import Flask, render_template, url_for
from flask_wtf.csrf import CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .extensions import csrf, db, limiter, login_manager, migrate, server_session
from .helpers import TEMPLATE_HELPERS
from .icons import icon, solid_icon
from .redis_store import init_redis

load_dotenv()


def create_app(overrides=None):
    # Static files live in public/static: Vercel serves public/** from its CDN; Flask serves them locally.
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "static"))
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    if app.config["PRODUCTION"] and app.config["SECRET_KEY"] in ("", "change-me", "dev-only-secret"):
        raise RuntimeError("SECRET_KEY wajib diisi di production.")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # behind Vercel's proxy

    init_redis(app)
    app.config["RATELIMIT_STORAGE_URI"] = app.config["REDIS_URL"]
    server_session.init_app(app)
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    from . import models  # noqa: F401  (register tables for migrations)
    from .auth_utils import home_for  # also registers the user loader
    from .blueprints import auth, editor, media, profile, racik, recipes, roles
    from .seed import register_commands

    app.register_blueprint(auth.bp)
    app.register_blueprint(recipes.bp)
    app.register_blueprint(editor.bp)
    app.register_blueprint(racik.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(roles.bp)
    app.register_blueprint(media.bp)

    register_commands(app)

    from .photo_credits import credit_for
    @lru_cache(maxsize=None)
    def asset(filename):
        """Static URL with a content hash (?v=…) so browsers/CDN can cache files for a year and still get new versions."""
        try:
            with open(os.path.join(app.static_folder, filename), "rb") as f:
                return url_for("static", filename=filename, v=hashlib.md5(f.read()).hexdigest()[:10])
        except FileNotFoundError:
            return url_for("static", filename=filename)

    app.jinja_env.globals.update(icon=icon, solid_icon=solid_icon, home_for=home_for, credit_for=credit_for, asset=asset, **TEMPLATE_HELPERS)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return resp

    @app.get("/healthz")
    @limiter.exempt
    def healthz():
        from sqlalchemy import text as sql
        db.session.execute(sql("SELECT 1"))
        app.extensions["redis"].ping()
        return {"ok": True, "db": "postgresql", "cache": "redis"}

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("error.html", title="Terlalu banyak permintaan", message="Tunggu sebentar lalu coba lagi."), 429

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", title="Halaman tidak ditemukan", message="Halaman yang kamu cari tidak ada."), 404

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return render_template("error.html", title="Sesi kedaluwarsa", message="Formulir sudah kedaluwarsa. Muat ulang halaman lalu coba lagi."), 403

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", title="File terlalu besar", message="Ukuran gambar maksimal 3 MB."), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", title="Terjadi kesalahan", message="Coba lagi beberapa saat."), 500

    return app
