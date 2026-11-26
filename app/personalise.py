"""Personalise Preference → filters and recommendations (taste, portion, meal time, diet, allergies)"""
import time

from sqlalchemy import bindparam, text

from .extensions import db
from .recipes import list_recipes


def get_prefs(user_id):
    row = db.session.execute(text("SELECT * FROM preferences WHERE user_id = :u"), {"u": user_id}).mappings().first()
    p = dict(row) if row else {"portions": [], "tastes": [], "meal_times": [], "diet": "none", "halal_only": False}
    p["allergies"] = [dict(x) for x in db.session.execute(text(
        "SELECT i.id, i.name FROM user_allergies a JOIN ingredients i ON i.id = a.ingredient_id WHERE a.user_id = :u ORDER BY i.name"), {"u": user_id}).mappings()]
    return p


def avoid_for(user_id):
    p = get_prefs(user_id)
    return {"ingredient_ids": [a["id"] for a in p["allergies"]], "vegan": p["diet"] == "vegan",
            "vegetarian": p["diet"] == "vegetarian", "halal": p["halal_only"]}


def _portion_fits(portion, servings, tags):
    if portion == "personal":
        return servings <= 2
    if portion == "keluarga":
        return 3 <= servings <= 4 or "keluarga" in tags
    if portion == "rame":
        return servings >= 5 or "keluarga" in tags
    return False


def recommend(user_id, limit=4):
    p = get_prefs(user_id)
    candidates = list_recipes(user_id=user_id, avoid=avoid_for(user_id), sort="rating")
    if not candidates:
        return []
    rows = db.session.execute(text("SELECT rt.recipe_id, t.slug FROM recipe_tags rt JOIN tags t ON t.id = rt.tag_id WHERE rt.recipe_id IN :ids")
                              .bindparams(bindparam("ids", expanding=True)), {"ids": [c["id"] for c in candidates]})
    tags_of = {}
    for rid, slug in rows:
        tags_of.setdefault(rid, []).append(slug)
    for r in candidates:
        tags = tags_of.get(r["id"], [])
        score = r["rating"]
        score += 2 * sum(t in tags for t in p["tastes"])
        score += sum(t in tags for t in p["meal_times"])
        if any(_portion_fits(x, r["servings"], tags) for x in p["portions"]):
            score += 1.5
        r["score"] = score
    scored = sorted(candidates, key=lambda r: -r["score"])
    # Rotate the top picks daily so "Rekomendasi Hari Ini" changes each day
    top = scored[:max(limit, 3)]
    off = int(time.time() // 86400) % len(top)
    return (top[off:] + top[:off])[:limit]
