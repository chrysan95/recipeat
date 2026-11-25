import os


def _db_url():
    url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/recipeat")
    # Some hosts give postgres:// , SQLAlchemy + psycopg 3 wants postgresql+psycopg://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret")
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # Neon scales to zero, reconnect transparently
        "pool_recycle": 300,
        "pool_size": 2, "max_overflow": 3,  # serverless: many small instances
        "connect_args": {"prepare_threshold": None},  # safe with Neon's pooled (PgBouncer) endpoint
    }
    BCRYPT_ROUNDS = int(os.environ.get("BCRYPT_ROUNDS", "12"))
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 3 MB image + form fields (Vercel caps request bodies at 4.5 MB)
    SESSION_COOKIE_NAME = "recipeat"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production" or os.environ.get("VERCEL_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 3600
    WTF_CSRF_TIME_LIMIT = None
    PRODUCTION = os.environ.get("VERCEL_ENV") == "production" or os.environ.get("FLASK_ENV") == "production"

    # Redis for sessions, rate limits, login throttle, cache
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    SESSION_TYPE = "redis"
    SESSION_KEY_PREFIX = "session:"
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = True
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STRATEGY = "fixed-window"
