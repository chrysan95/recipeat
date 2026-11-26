"""Create/upgrade the schema and load dummy data automatically on a fresh deployment

Vercel has no start command, so this runs on the first cold start of each instance (wsgi.py calls it when VERCEL or AUTO_MIGRATE=1 is set)
PostgreSQL advisory lock makessure only one instance migrates at a time, later calls are a quick no-op"""
import os

from flask_migrate import upgrade
from sqlalchemy import text

from .extensions import db

LOCK_ID = 727_327_283  # arbitrary app-wide advisory lock key
MIGRATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")


def ensure_database(app):
    from .models import User
    from .seed import seed

    with app.app_context():
        with db.engine.connect() as lock_conn:
            lock_conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": LOCK_ID})
            try:
                upgrade(directory=MIGRATIONS)
                if os.environ.get("SEED_DUMMY_DATA", "1") == "1" and not db.session.query(User.id).first():
                    seed()
                    app.logger.info("Database kosong, data dummy dimuat.")
            finally:
                lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_ID})
                lock_conn.commit()
                db.session.remove()
