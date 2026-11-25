"""Entry point for Vercel (auto-detected `app` in wsgi.py), Gunicorn (`gunicorn wsgi:app`) and the flask CLI."""
import os

from app import create_app

app = create_app()

# On Vercel (or when AUTO_MIGRATE=1) apply migrations + dummy data on cold start.
if os.environ.get("VERCEL") or os.environ.get("AUTO_MIGRATE") == "1":
    from app.bootstrap import ensure_database
    ensure_database(app)

if __name__ == "__main__":
    app.run()
