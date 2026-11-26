"""Recipe queries (PostgreSQL) shared by blueprints."""
from sqlalchemy import bindparam, text

from .extensions import db
from .redis_store import cached

SORTS = {
    "populer": "bookmark_count DESC, rating DESC",
    "rating": "rating DESC, review_count DESC",
    "tercepat": "total_minutes ASC",
    "termurah": "COALESCE(r.price_min, 2147483647) ASC",
    "terbaru": "r.created_at DESC",
}
SORT_LABELS = {"populer": "Terpopuler", "rating": "Rating tertinggi", "tercepat": "Tercepat", "termurah": "Termurah", "terbaru": "Terbaru"}

BASE_SELECT = """
  SELECT r.id, r.title, r.description, r.origin, r.image_url, r.video_url, r.prep_minutes, r.cook_minutes,
         (r.prep_minutes + r.cook_minutes) AS total_minutes, r.price_min, r.price_max, r.servings, r.status,
         r.author_id, r.created_at, r.updated_at,
         COALESCE((SELECT ROUND(AVG(rating)::numeric, 1)::float FROM reviews WHERE recipe_id = r.id), 0) AS rating,
         (SELECT COUNT(*) FROM reviews WHERE recipe_id = r.id) AS review_count,
         (SELECT COUNT(*) FROM bookmarks WHERE recipe_id = r.id) AS bookmark_count,
         EXISTS (SELECT 1 FROM bookmarks WHERE recipe_id = r.id AND user_id = :uid) AS bookmarked
  FROM recipes r"""


def _ing_clause(cond):
    return f"NOT EXISTS (SELECT 1 FROM recipe_ingredients ri JOIN ingredients i ON i.id = ri.ingredient_id WHERE ri.recipe_id = r.id AND {cond})"


def list_recipes(user_id=0, q=None, tags=(), sort="populer", ids=None, author_id=None, bookmarked_only=False, avoid=None, limit=None):
    """avoid = {'ingredient_ids': [...], 'vegan': bool, 'vegetarian': bool, 'halal': bool}"""
    where = ["r.status = 'published'"]
    p = {"uid": user_id or 0}
    expanding = []
    if q:
        where.append("(r.title ILIKE :q OR r.description ILIKE :q OR r.origin ILIKE :q)")
        p["q"] = f"%{q}%"
    for i, slug in enumerate(t for t in tags if t):
        where.append(f"EXISTS (SELECT 1 FROM recipe_tags rt JOIN tags t ON t.id = rt.tag_id WHERE rt.recipe_id = r.id AND t.slug = :tag{i})")
        p[f"tag{i}"] = slug
    if ids is not None:
        where.append("r.id IN :ids")
        p["ids"] = [int(x) for x in ids] or [0]
        expanding.append("ids")
    if author_id:
        where.append("r.author_id = :author")
        p["author"] = author_id
    if bookmarked_only:
        where.append("EXISTS (SELECT 1 FROM bookmarks WHERE recipe_id = r.id AND user_id = :uid)")
    if avoid:
        if avoid.get("ingredient_ids"):
            where.append(_ing_clause("i.id IN :avoid_ids"))
            p["avoid_ids"] = list(avoid["ingredient_ids"])
            expanding.append("avoid_ids")
        if avoid.get("vegan"):
            where.append(_ing_clause("NOT i.is_vegan"))
        elif avoid.get("vegetarian"):
            where.append(_ing_clause("NOT i.is_vegetarian"))
        if avoid.get("halal"):
            where.append(_ing_clause("NOT i.is_halal"))
    sql = f"{BASE_SELECT} WHERE {' AND '.join(where)} ORDER BY {SORTS.get(sort, SORTS['populer'])}, r.id"
    if limit:
        sql += f" LIMIT {int(limit)}"
    stmt = text(sql)
    for name in expanding:
        stmt = stmt.bindparams(bindparam(name, expanding=True))
    return [dict(r) for r in db.session.execute(stmt, p).mappings()]


def get_recipe(recipe_id, user_id=0):
    s = db.session
    row = s.execute(text(f"{BASE_SELECT} WHERE r.id = :id"), {"id": recipe_id, "uid": user_id or 0}).mappings().first()
    if not row:
        return None
    r = dict(row)
    r["author"] = dict(s.execute(text("SELECT id, name FROM users WHERE id = :id"), {"id": r["author_id"]}).mappings().one())
    r["tags"] = [dict(x) for x in s.execute(text(
        "SELECT t.id, t.name, t.slug, t.kind FROM recipe_tags rt JOIN tags t ON t.id = rt.tag_id WHERE rt.recipe_id = :id ORDER BY t.kind, t.id"), {"id": r["id"]}).mappings()]
    r["ingredients"] = [dict(x) for x in s.execute(text("""
        SELECT ri.id, ri.quantity, ri.unit, ri.note, i.id AS ingredient_id, i.name, i.image_url, i.is_vegan, i.is_vegetarian, i.is_halal
        FROM recipe_ingredients ri JOIN ingredients i ON i.id = ri.ingredient_id WHERE ri.recipe_id = :id ORDER BY ri.position"""), {"id": r["id"]}).mappings()]
    r["steps"] = [dict(x) for x in s.execute(text(
        "SELECT position, title, body, media_url FROM recipe_steps WHERE recipe_id = :id ORDER BY position"), {"id": r["id"]}).mappings()]
    r["reviews"] = [dict(x) for x in s.execute(text("""
        SELECT rv.rating, rv.comment, rv.created_at, rv.user_id, u.name FROM reviews rv JOIN users u ON u.id = rv.user_id
        WHERE rv.recipe_id = :id ORDER BY rv.created_at DESC"""), {"id": r["id"]}).mappings()]
    return r


def tags_by_kind(kind):
    return cached(f"tags:{kind}", 3600, lambda: [dict(x) for x in db.session.execute(
        text("SELECT id, name, slug FROM tags WHERE kind = :k ORDER BY id"), {"k": kind}).mappings()])


def categories():
    return cached("categories", 3600, lambda: [dict(x) for x in db.session.execute(
        text("SELECT id, name, slug FROM ingredient_categories ORDER BY position")).mappings()])


def approved_ingredients():
    """All approved ingredients with category slug (cached; cleared when an admin approves one)."""
    return cached("ingredients:approved", 600, lambda: [dict(x) for x in db.session.execute(text("""
        SELECT i.id, i.name, i.image_url, i.popularity, c.slug AS category, c.name AS category_name, c.position
        FROM ingredients i JOIN ingredient_categories c ON c.id = i.category_id
        WHERE i.status = 'approved' ORDER BY c.position, i.popularity DESC, i.name""")).mappings()])
