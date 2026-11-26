def test_search_filters_category_and_sorts_by_time(new_client):
    c = new_client()
    c.login("keisa@gmail.com", "Keisa#2026")
    html = c.get("/cari?jenis=dessert&urut=tercepat").get_data(as_text=True)
    assert "Es Teler" in html and "Rendang Sapi" not in html
    assert html.index("Es Teler") < html.index("Klepon")


def test_preference_filter_hides_non_halal_for_keisa(new_client):
    c = new_client()
    c.login("keisa@gmail.com", "Keisa#2026")
    assert "Babi Kecap" not in c.get("/cari?sesuai=1").get_data(as_text=True)


def test_pages_render(new_client):
    c = new_client()
    c.login("keisa@gmail.com", "Keisa#2026")
    for url in ["/", "/?rasa=pedas", "/cari?q=nasi", "/resep", "/resep/tersimpan", "/resep/1", "/resep/1?tab=langkah", "/resep/1/masak"]:
        assert c.get(url).status_code == 200, url
    assert c.get("/resep/9999").status_code == 404


def test_bookmark_toggle_and_review(new_client, sql):
    c = new_client()
    c.login("sari@gmail.com", "Sari#2026")
    h = {"Accept": "application/json", "X-CSRFToken": c.token}
    assert c.c.post("/resep/2/simpan", headers=h).get_json() == {"bookmarked": True}
    assert c.c.post("/resep/2/simpan", headers=h).get_json() == {"bookmarked": False}
    c.post("/resep/2/ulasan", {"rating": "4", "comment": "Mantap"})
    row = sql("SELECT rating, comment FROM reviews WHERE recipe_id = 2 AND user_id = (SELECT id FROM users WHERE email = 'sari@gmail.com')")[0]
    assert tuple(row) == (4, "Mantap")
