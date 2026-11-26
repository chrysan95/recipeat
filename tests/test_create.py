import io

PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63f8ffff3f0005fe02fea7d6a4f30000000049454e44ae426082")


def test_add_recipe_with_visual_reference(app, new_client, sql):
    c = new_client()
    c.login("budi@gmail.com", "Budi#2026")
    data = {"csrf_token": c.token, "title": "Mie Goreng Jawa", "description": "Mie goreng manis.", "prep_minutes": "10", "cook_minutes": "15",
            "servings": "2", "price_min": "15000", "price_max": "20000", "tags": ["1", "6"],
            "ing_id": ["51", "3"], "ing_qty": ["200", ""], "ing_unit": ["gr", ""], "ing_note": ["", "Secukupnya"],
            "step_title": ["Rebus"], "step_body": ["Rebus mie."], "step_media": [""], "image": (io.BytesIO(PNG), "foto.png")}
    r = c.c.post("/resep/baru", data=data, content_type="multipart/form-data")
    assert r.status_code == 302, r.get_data(as_text=True)[:500]
    rid, img = sql("SELECT id, image_url FROM recipes WHERE title = 'Mie Goreng Jawa'")[0]
    assert img.startswith("/img/")
    served = c.get(img)
    assert served.status_code == 200 and served.mimetype == "image/png" and served.data == PNG
    assert "immutable" in served.headers["Cache-Control"]
    assert sql("SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :r", r=rid)[0][0] == 2
    assert sql("SELECT COUNT(*) FROM recipe_tags WHERE recipe_id = :r", r=rid)[0][0] == 2
    assert c.get(f"/resep/{rid}/ubah").status_code == 200


def test_add_recipe_rejects_missing_steps(new_client):
    c = new_client()
    c.login("budi@gmail.com", "Budi#2026")
    r = c.post("/resep/baru", {"title": "Kosong", "prep_minutes": "1", "cook_minutes": "1", "servings": "1", "ing_id": "3"})
    assert r.status_code == 400


def test_fake_image_rejected(new_client):
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    r = c.c.post("/bahan/ajukan", data={"csrf_token": c.token, "name": "Bahan Palsu", "category_id": "7", "photo": (io.BytesIO(b"<script>"), "x.png")},
                 content_type="multipart/form-data")
    assert r.status_code == 400 and "Format gambar" in r.get_data(as_text=True)


def test_request_new_ingredient_goes_to_pending(app, new_client, sql):
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    r = c.c.post("/bahan/ajukan", data={"csrf_token": c.token, "name": "Daun Kemangi", "category_id": "7", "note": "Untuk lalapan",
                                        "photo": (io.BytesIO(PNG), "k.png")}, content_type="multipart/form-data")
    assert r.status_code == 302
    status, img = sql("SELECT status, image_url FROM ingredients WHERE name = 'Daun Kemangi'")[0]
    assert status == "pending" and img.startswith("/img/")
    assert sql("SELECT size FROM images WHERE id = :i", i=img[5:])[0][0] == len(PNG)


def test_concoct_ranks_by_basket(new_client):
    c = new_client()
    c.login("budi@gmail.com", "Budi#2026")
    html = c.get("/racik/hasil?bahan=3,26,27,28,48").get_data(as_text=True)
    assert html.index("Telur Balado") < html.index("Sayur Asem")
    assert c.get("/racik").status_code == 200 and c.get("/resep/baru").status_code == 200


def test_rejected_request_photo_is_deleted(new_client, sql):
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    c.c.post("/bahan/ajukan", data={"csrf_token": c.token, "name": "Daun Ruku", "category_id": "7", "photo": (io.BytesIO(PNG), "r.png")},
             content_type="multipart/form-data")
    ing, img = sql("SELECT id, image_url FROM ingredients WHERE name = 'Daun Ruku'")[0]
    a = new_client()
    a.login("admin@recipeat.id", "Admin#2026")
    a.post(f"/admin/bahan/{ing}", {"action": "reject", "review_note": "Duplikat"})
    assert sql("SELECT COUNT(*) FROM images WHERE id = :i", i=img[5:])[0][0] == 0
    assert a.get(img).status_code == 404
