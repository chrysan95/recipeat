def test_change_password_rejects_reuse_and_signs_out_other_devices(new_client):
    other = new_client()
    other.login("budi@gmail.com", "Budi#2026")
    c = new_client()
    c.login("budi@gmail.com", "Budi#2026")
    assert c.post("/profil/kata-sandi", {"current": "Budi#2026", "password": "Budi#2026", "confirm": "Budi#2026"}).status_code == 400
    assert c.post("/profil/kata-sandi", {"current": "Budi#2026", "password": "BaruSekali99", "confirm": "BaruSekali99"}).status_code == 302
    assert c.get("/").status_code == 200, "current device stays signed in"
    assert other.get("/").status_code == 302, "other device is signed out"
    c.refresh_token("/profil/kata-sandi")
    assert c.post("/profil/kata-sandi", {"current": "BaruSekali99", "password": "Budi#2026", "confirm": "Budi#2026"}).status_code == 400
    assert new_client().login("budi@gmail.com", "BaruSekali99").status_code == 302


def test_preferences_drive_filters(new_client, sql):
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    c.post("/profil/preferensi", {"portions": "personal", "tastes": "manis", "diet": "vegan", "halal_only": "1"})
    html = c.get("/cari?sesuai=1").get_data(as_text=True)
    assert "Nasi Goreng" not in html and "Tempe Orek" in html
    assert tuple(sql("SELECT diet, tastes FROM preferences WHERE user_id = (SELECT id FROM users WHERE email = 'sari@gmail.com')")[0]) == ("vegan", ["manis"])
    for url in ["/profil", "/profil/kata-sandi", "/profil/preferensi?baru=1"]:
        assert c.get(url).status_code == 200


def test_change_and_remove_profile_picture(new_client, sql):
    import io
    PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4f30000000049454e44ae426082")
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    r = c.c.post("/profil/foto", data={"csrf_token": c.token, "next": "/profil", "photo": (io.BytesIO(PNG), "me.png")},
                 content_type="multipart/form-data")
    assert r.status_code == 302 and r.headers["Location"].endswith("/profil")
    url = sql("SELECT avatar_url FROM users WHERE email = 'sari@gmail.com'")[0][0]
    assert url.startswith("/img/") and url in c.c.get("/profil").get_data(as_text=True)
    c.c.post("/profil/foto", data={"csrf_token": c.token, "action": "remove"})
    assert sql("SELECT avatar_url FROM users WHERE email = 'sari@gmail.com'")[0][0] is None
    assert sql("SELECT COUNT(*) FROM images WHERE id = :i", i=url[5:])[0][0] == 0
