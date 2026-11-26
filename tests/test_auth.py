def test_protected_pages_redirect_to_login(client):
    r = client.get("/")
    assert r.status_code == 302 and r.headers["Location"].endswith("/masuk")


def test_signup_stores_bcrypt_hash_not_plain_password(client, sql):
    client.refresh_token("/daftar")
    r = client.post("/daftar", {"name": "Tes", "email": "tes@contoh.id", "password": "Rahasia123", "confirm": "Rahasia123"})
    assert r.status_code == 302
    h = sql("SELECT password_hash FROM users WHERE email = :e", e="tes@contoh.id")[0][0]
    assert h.startswith("$2b$") and "Rahasia123" not in h


def test_weak_password_rejected(client):
    client.refresh_token("/daftar")
    r = client.post("/daftar", {"name": "Tes", "email": "lemah@contoh.id", "password": "abc", "confirm": "abc"})
    assert r.status_code == 400


def test_login_success_and_wrong_password(client):
    client.refresh_token()
    assert client.post("/masuk", {"email": "keisa@gmail.com", "password": "salah12345"}).status_code == 401
    assert client.post("/masuk", {"email": "keisa@gmail.com", "password": "Keisa#2026"}).status_code == 302
    r = client.get("/")
    assert r.status_code == 200 and "Halo Keisa" in r.get_data(as_text=True)


def test_post_without_csrf_rejected(app):
    r = app.test_client().post("/masuk", data={"email": "keisa@gmail.com", "password": "Keisa#2026"})
    assert r.status_code == 403


def test_sessions_are_stored_in_redis(app, new_client):
    c = new_client()
    c.login("keisa@gmail.com", "Keisa#2026")
    keys = list(app.extensions["redis"].scan_iter("session:*"))
    assert keys, "server-side session should be in Redis"
    cookie = c.c.get_cookie("recipeat")
    assert cookie and "Keisa" not in cookie.value  # cookie holds only a signed session id


def test_login_throttle_blocks_after_5_failures(new_client):
    c = new_client()
    c.refresh_token()
    for _ in range(5):
        assert c.post("/masuk", {"email": "budi@gmail.com", "password": "salah00000"}).status_code == 401
    r = c.post("/masuk", {"email": "budi@gmail.com", "password": "Budi#2026"})
    assert r.status_code == 429
