"""Tests run against a real PostgreSQL database (TEST_DATABASE_URL)
Each test module starts from freshly seeded dummy data"""
import os
import re

import pytest

os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/recipeat_test"))
os.environ["BCRYPT_ROUNDS"] = "4"
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import seed, wipe  # noqa: E402


@pytest.fixture(scope="session")
def app():
    app = create_app({"TESTING": True, "BCRYPT_ROUNDS": 4, "RATELIMIT_ENABLED": False})
    app.extensions["redis"].flushdb()
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app


@pytest.fixture(scope="module", autouse=True)
def fresh_data(app):
    with app.app_context():
        wipe()
        seed()
    app.extensions["redis"].flushdb()
    yield


@pytest.fixture
def sql(app):
    """Run SQL in a short-lived app context (keeping a context open across requests would share `g`)."""
    from sqlalchemy import text

    def run(query, **params):
        with app.app_context():
            return db.session.execute(text(query), params).all()
    return run


class Client:
    """Test client that knows how to fetch CSRF tokens and log in."""

    def __init__(self, app):
        self.c = app.test_client()
        self.token = None

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def refresh_token(self, url="/masuk"):
        html = self.c.get(url, follow_redirects=True).get_data(as_text=True)
        self.token = re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)
        return self.token

    def post(self, url, data=None, **kw):
        if not self.token:
            self.refresh_token()
        data = dict(data or {})
        data.setdefault("csrf_token", self.token)
        return self.c.post(url, data=data, **kw)

    def login(self, email, password):
        self.refresh_token("/masuk")
        r = self.post("/masuk", {"email": email, "password": password})
        self.refresh_token("/")
        return r


@pytest.fixture
def client(app):
    return Client(app)


@pytest.fixture
def new_client(app):
    return lambda: Client(app)
