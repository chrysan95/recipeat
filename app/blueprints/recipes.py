"""Home, Search Recipe (+filter categories, sort by type), Read Recipe (+bookmark, review, adjust portion, copy list)"""
from datetime import date

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import text

from ..extensions import db
from ..personalise import avoid_for, recommend
from ..recipes import SORT_LABELS, SORTS, approved_ingredients, get_recipe, list_recipes, tags_by_kind

bp = Blueprint("recipes", __name__)


@bp.before_request
@login_required
def _auth():
    pass


@bp.get("/")
def home():
    rasa = request.args.get("rasa", "")
    semua = request.args.get("tab") == "semua" and not rasa
    taste_tags = [t for t in tags_by_kind("rasa") if t["slug"] in ("asin", "manis", "pedas")]
    popular = sorted((i for i in approved_ingredients() if i["category"] != "non-halal"), key=lambda i: -i["popularity"])[:12]
    recipes = list_recipes(user_id=current_user.id, tags=[rasa], sort="terbaru" if semua else "populer", limit=None if semua else 8)
    reco = (recommend(current_user.id, 1) or recipes or [None])[0]
    promo = db.session.execute(text("""SELECT * FROM promotions WHERE active AND starts_on <= :d AND (ends_on IS NULL OR ends_on >= :d)
        ORDER BY created_at DESC LIMIT 1"""), {"d": date.today()}).mappings().first()
    return render_template("index.html", title="Beranda", active="home", rasa=rasa, semua=semua, taste_tags=taste_tags,
                           popular=popular, recipes=recipes, reco=reco, promo=promo)


@bp.get("/cari")
def search():
    q = request.args.get("q", "").strip()[:80]
    jenis = request.args.get("jenis", "")
    rasa = request.args.get("rasa", "")
    sort = request.args.get("urut") if request.args.get("urut") in SORTS else "populer"
    sesuai = request.args.get("sesuai") == "1"
    recipes = list_recipes(user_id=current_user.id, q=q, tags=[jenis, rasa], sort=sort, avoid=avoid_for(current_user.id) if sesuai else None)
    return render_template("recipes/search.html", title="Hasil Pencarian", active="racik", q=q, jenis=jenis, rasa=rasa, sort=sort,
                           sesuai=sesuai, recipes=recipes, jenis_tags=tags_by_kind("jenis"), rasa_tags=tags_by_kind("rasa"), sort_labels=SORT_LABELS)


@bp.get("/resep")
def library():
    saved = list_recipes(user_id=current_user.id, bookmarked_only=True, sort="terbaru", limit=4)
    mine = db.session.execute(text("""SELECT r.id, r.title, r.status, r.updated_at,
          COALESCE((SELECT ROUND(AVG(rating)::numeric,1)::float FROM reviews WHERE recipe_id = r.id), 0) AS rating,
          (SELECT COUNT(*) FROM bookmarks WHERE recipe_id = r.id) AS bookmark_count,
          (SELECT COUNT(*) FROM reviews WHERE recipe_id = r.id) AS review_count
        FROM recipes r WHERE r.author_id = :u ORDER BY r.updated_at DESC"""), {"u": current_user.id}).mappings().all()
    return render_template("recipes/library.html", title="Resep", active="resep", saved=saved, mine=mine, show_all=request.args.get("semua") == "1")


@bp.get("/resep/tersimpan")
def saved():
    rasa = request.args.get("rasa", "")
    q = request.args.get("q", "").strip()[:80]
    recipes = list_recipes(user_id=current_user.id, bookmarked_only=True, q=q, tags=[rasa], sort="terbaru")
    return render_template("recipes/saved.html", title="Resep Tersimpan", active="resep", recipes=recipes, rasa=rasa, q=q, rasa_tags=tags_by_kind("rasa"))


def load_recipe(recipe_id):
    r = get_recipe(recipe_id, current_user.id)
    if not r or (r["status"] != "published" and r["author_id"] != current_user.id):
        abort(404)
    allergy_ids = {x for (x,) in db.session.execute(text("SELECT ingredient_id FROM user_allergies WHERE user_id = :u"), {"u": current_user.id})}
    for i in r["ingredients"]:
        i["allergen"] = i["ingredient_id"] in allergy_ids
    r["allergens"] = [i["name"] for i in r["ingredients"] if i["allergen"]]
    r["my_review"] = next((rv for rv in r["reviews"] if rv["user_id"] == current_user.id), None)
    return r


@bp.get("/resep/<int:recipe_id>")
def detail(recipe_id):
    r = load_recipe(recipe_id)
    return render_template("recipes/detail.html", title=r["title"], active="racik", r=r, tab="langkah" if request.args.get("tab") == "langkah" else "bahan")


@bp.get("/resep/<int:recipe_id>/masak")
def cook(recipe_id):
    r = load_recipe(recipe_id)
    return render_template("recipes/cook.html", title=f"Masak {r['title']}", hide_nav=True, r=r)


@bp.post("/resep/<int:recipe_id>/simpan")
def bookmark(recipe_id):
    if not db.session.execute(text("SELECT 1 FROM recipes WHERE id = :id"), {"id": recipe_id}).first():
        abort(404)
    p = {"u": current_user.id, "r": recipe_id}
    deleted = db.session.execute(text("DELETE FROM bookmarks WHERE user_id = :u AND recipe_id = :r"), p).rowcount
    if not deleted:
        db.session.execute(text("INSERT INTO bookmarks (user_id, recipe_id) VALUES (:u, :r) ON CONFLICT DO NOTHING"), p)
    db.session.commit()
    if request.accept_mimetypes.best == "application/json":
        return jsonify(bookmarked=not deleted)
    return redirect(request.referrer or f"/resep/{recipe_id}")


@bp.post("/resep/<int:recipe_id>/ulasan")
def review(recipe_id):
    r = load_recipe(recipe_id)
    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()[:500]
    if not 1 <= rating <= 5:
        flash("Pilih rating 1–5 bintang.", "error")
    elif r["author_id"] == current_user.id:
        flash("Kamu tidak bisa mengulas resepmu sendiri.", "error")
    else:
        db.session.execute(text("""INSERT INTO reviews (recipe_id, user_id, rating, comment) VALUES (:r, :u, :rt, :c)
            ON CONFLICT (recipe_id, user_id) DO UPDATE SET rating = EXCLUDED.rating, comment = EXCLUDED.comment, created_at = now()"""),
                           {"r": recipe_id, "u": current_user.id, "rt": rating, "c": comment})
        db.session.commit()
        flash("Terima kasih, ulasanmu tersimpan.", "ok")
    return redirect(f"/resep/{recipe_id}#ulasan")
