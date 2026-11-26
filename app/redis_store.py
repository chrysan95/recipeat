"""Redis: server-side sessions (Flask-Session), rate limits (Flask-Limiter),
login throttle and a tiny JSON cache for reference data."""
import json

import redis
from flask import current_app


def get_redis():
    return current_app.extensions["redis"]


def init_redis(app):
    client = redis.Redis.from_url(app.config["REDIS_URL"], decode_responses=False)
    app.extensions["redis"] = client
    app.config["SESSION_REDIS"] = client
    return client


# ---------- cache ----------
def cached(key, ttl, producer):
    """Return JSON-serialisable data from Redis, or compute + store it."""
    r = get_redis()
    full = f"cache:{key}"
    raw = r.get(full)
    if raw is not None:
        return json.loads(raw)
    value = producer()
    r.setex(full, ttl, json.dumps(value, default=str))
    return value


def cache_clear(prefix=""):
    r = get_redis()
    for k in r.scan_iter(f"cache:{prefix}*"):
        r.delete(k)


# ---------- login throttle (5 failures / 15 min per IP + email) ----------
WINDOW, MAX_FAILS = 15 * 60, 5


def _tkey(key):
    return f"throttle:login:{key}"


def login_blocked(key):
    v = get_redis().get(_tkey(key))
    return v is not None and int(v) >= MAX_FAILS


def login_failed(key):
    r = get_redis()
    pipe = r.pipeline()
    pipe.incr(_tkey(key))
    pipe.expire(_tkey(key), WINDOW, nx=True)
    pipe.execute()


def login_reset(key):
    get_redis().delete(_tkey(key))
