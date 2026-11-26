def test_regular_user_cannot_open_admin_or_sponsor(new_client):
    c = new_client()
    c.login("keisa@gmail.com", "Keisa#2026")
    assert c.get("/admin/bahan").status_code == 403
    assert c.get("/sponsor/promosi").status_code == 403


def test_admin_approves_and_requester_notified(new_client, sql):
    c = new_client()
    c.login("admin@recipeat.id", "Admin#2026")
    assert c.get("/admin/bahan").status_code == 200
    ing = sql("SELECT id FROM ingredients WHERE name = 'Andaliman'")[0][0]
    assert c.post(f"/admin/bahan/{ing}", {"action": "approve", "name": "Andaliman", "category_id": "7", "is_vegan": "1", "is_halal": "1"}).status_code == 302
    assert sql("SELECT status FROM ingredients WHERE id = :i", i=ing)[0][0] == "approved"
    assert "disetujui" in sql("SELECT title FROM notifications WHERE user_id = (SELECT id FROM users WHERE email = 'keisa@gmail.com') ORDER BY id DESC LIMIT 1")[0][0]
    k = new_client()
    k.login("keisa@gmail.com", "Keisa#2026")
    assert "Andaliman" in k.get("/racik?kategori=rempah").get_data(as_text=True), "cache cleared after approval"


def test_admin_rejection_needs_reason(new_client, sql):
    c = new_client()
    c.login("admin@recipeat.id", "Admin#2026")
    ing = sql("SELECT id FROM ingredients WHERE name = 'Kecombrang'")[0][0]
    c.post(f"/admin/bahan/{ing}", {"action": "reject", "review_note": ""})
    assert sql("SELECT status FROM ingredients WHERE id = :i", i=ing)[0][0] == "pending"


def test_sponsor_promotion_broadcast(new_client):
    c = new_client()
    c.login("sponsor@dapurnusa.id", "Sponsor#2026")
    assert c.get("/sponsor/promosi").status_code == 200 and c.get("/sponsor/promosi/1").status_code == 200
    r = c.post("/sponsor/promosi/baru", {"brand": "Dapurnusa", "title": "Promo Rendang", "body": "Diskon bumbu", "cta_url": "/resep/9",
                                         "starts_on": "2026-01-01", "recipe_ids": "9", "active": "1", "broadcast": "1"})
    assert r.status_code == 302
    u = new_client()
    u.login("budi@gmail.com", "Budi#2026")
    assert "Promo Rendang" in u.get("/notifikasi").get_data(as_text=True)


def test_sponsor_link_must_be_internal_or_https(new_client):
    c = new_client()
    c.login("sponsor@dapurnusa.id", "Sponsor#2026")
    assert c.post("/sponsor/promosi/baru", {"brand": "X", "title": "Bad link", "cta_url": "javascript:alert(1)", "starts_on": "2026-01-01"}).status_code == 400


def test_admin_and_sponsor_get_their_own_workspace(new_client):
    a = new_client()
    a.login("admin@recipeat.id", "Admin#2026")
    assert a.c.get("/").headers["Location"].endswith("/admin/bahan")
    assert a.c.get("/resep").headers["Location"].endswith("/admin/bahan")
    assert a.c.get("/profil/preferensi").headers["Location"].endswith("/profil")
    assert a.c.get("/notifikasi").headers["Location"].endswith("/sponsor/promosi")
    nav = a.c.get("/admin/bahan").get_data(as_text=True)
    assert 'href="/racik"' not in nav and "Riwayat Bahan" in nav
    s = new_client()
    s.login("sponsor@dapurnusa.id", "Sponsor#2026")
    assert s.c.get("/").headers["Location"].endswith("/resep")
    assert s.c.get("/notifikasi").headers["Location"].endswith("/sponsor/promosi")
    lib = s.c.get("/resep").get_data(as_text=True)
    assert "Ajukan bahan baru" in lib and "Resep Tersimpan" not in lib
    profile = s.c.get("/profil").get_data(as_text=True)
    assert "Preferensi Makanan" not in profile and "Ganti Kata Sandi" in profile
    assert s.c.get("/kredit-foto").status_code == 404
