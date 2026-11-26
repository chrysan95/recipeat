"""Recipe queries (PostgreSQL) shared by blueprints"""
from sqlalchemy import bindparam, text

from .extensions import db
from .redis_store import cached

SORTS = {
    "populer": "bookmark_count DESC, rating DESC",
    "rating": "rating DESC, review_count DESC",
    "tercepat": "total_minutes ASC",
    "termurah": "COALESCE(r.price_min, 2147483647) ASC",
    "terbaru": "r.created_at DESC",
    "diubah": "r.updated_at DESC",
}
SORT_LABELS = {"populer": "Terpopuler", "rating": "Rating tertinggi", "tercepat": "Tercepat", "termurah": "Termurah", "terbaru": "Terbaru"}

# Ratings and bookmark counts are aggregated once per query (grouped joins) instead of per row.
BASE_SELECT = """
  SELECT r.id, r.title, r.description, r.origin, r.image_url, r.video_url, r.prep_minutes, r.cook_minutes,
         (r.prep_minutes + r.cook_minutes) AS total_minutes, r.price_min, r.price_max, r.servings, r.status,
         r.author_id, r.created_at, r.updated_at,
         COALESCE(rv.rating, 0) AS rating, COALESCE(rv.review_count, 0) AS review_count,
         COALESCE(bm.bookmark_count, 0) AS bookmark_count, mine.recipe_id IS NOT NULL AS bookmarked
  FROM recipes r
  LEFT JOIN (SELECT recipe_id, ROUND(AVG(rating)::numeric, 1)::float AS rating, COUNT(*) AS review_count
             FROM reviews GROUP BY recipe_id) rv ON rv.recipe_id = r.id
  LEFT JOIN (SELECT recipe_id, COUNT(*) AS bookmark_count FROM bookmarks GROUP BY recipe_id) bm ON bm.recipe_id = r.id
  LEFT JOIN bookmarks mine ON mine.recipe_id = r.id AND mine.user_id = :uid"""


def _ing_clause(cond):
    return f"NOT EXISTS (SELECT 1 FROM recipe_ingredients ri JOIN ingredients i ON i.id = ri.ingredient_id WHERE ri.recipe_id = r.id AND {cond})"


def list_recipes(user_id=0, q=None, tags=(), sort="populer", ids=None, author_id=None, bookmarked_only=False, avoid=None, limit=None,
                 include_drafts=False):
    """avoid = {'ingredient_ids': [...], 'vegan': bool, 'vegetarian': bool, 'halal': bool}"""
    where = ["TRUE" if include_drafts else "r.status = 'published'"]
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
        where.append("mine.recipe_id IS NOT NULL")
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


# One round trip for the whole recipe page: author, tags, ingredients and steps come back as JSON arrays.
DETAIL_SELECT = f"""
  SELECT b.*, json_build_object('id', u.id, 'name', u.name) AS author,
    COALESCE((SELECT json_agg(json_build_object('id', t.id, 'name', t.name, 'slug', t.slug, 'kind', t.kind) ORDER BY t.kind, t.id)
              FROM recipe_tags rt JOIN tags t ON t.id = rt.tag_id WHERE rt.recipe_id = b.id), '[]') AS tags,
    COALESCE((SELECT json_agg(json_build_object('id', ri.id, 'quantity', ri.quantity, 'unit', ri.unit, 'note', ri.note,
                'ingredient_id', i.id, 'name', i.name, 'image_url', i.image_url, 'is_vegan', i.is_vegan,
                'is_vegetarian', i.is_vegetarian, 'is_halal', i.is_halal) ORDER BY ri.position)
              FROM recipe_ingredients ri JOIN ingredients i ON i.id = ri.ingredient_id WHERE ri.recipe_id = b.id), '[]') AS ingredients,
    COALESCE((SELECT json_agg(json_build_object('position', st.position, 'title', st.title, 'body', st.body, 'media_url', st.media_url)
              ORDER BY st.position) FROM recipe_steps st WHERE st.recipe_id = b.id), '[]') AS steps
  FROM ({BASE_SELECT} WHERE r.id = :id) b JOIN users u ON u.id = b.author_id"""


def get_recipe(recipe_id, user_id=0):
    row = db.session.execute(text(DETAIL_SELECT), {"id": recipe_id, "uid": user_id or 0}).mappings().first()
    if not row:
        return None
    r = dict(row)
    r["reviews"] = [dict(x) for x in db.session.execute(text("""
        SELECT rv.rating, rv.comment, rv.created_at, rv.user_id, u.name FROM reviews rv JOIN users u ON u.id = rv.user_id
        WHERE rv.recipe_id = :id ORDER BY rv.created_at DESC"""), {"id": recipe_id}).mappings()]
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
