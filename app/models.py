"""PostgreSQL data model
Mirrors the use-case diagram:
User: search/concoct/read/add recipe, request ingredient, personalise preference, log in, sign up
Admin: verify ingredient
Sponsor: manage promotion
"""
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY

from .extensions import db

TS = db.DateTime(timezone=True)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True)  # always stored lower-case
    password_hash = db.Column(db.String(72), nullable=False)        # bcrypt hash, never plain text
    role = db.Column(db.String(10), nullable=False, server_default="user")
    newsletter = db.Column(db.Boolean, nullable=False, server_default=text("false"))
    avatar_url = db.Column(db.String(255))  # /img/<id> (uploaded profile picture) or NULL → initials
    session_version = db.Column(db.Integer, nullable=False, server_default="1")  # bump to sign out all devices
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("role IN ('user','admin','sponsor')", name="ck_users_role"),)

    def get_id(self):
        # Session stores "id:version" so a password change invalidates other sessions
        return f"{self.id}:{self.session_version}"


class PasswordHistory(db.Model):
    """Previous hashes so a new password can't reuse an old one."""
    __tablename__ = "password_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = db.Column(db.String(72), nullable=False)
    created_at = db.Column(TS, nullable=False, server_default=func.now())


class Preference(db.Model):
    """Personalise Preference."""
    __tablename__ = "preferences"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    portions = db.Column(ARRAY(db.String(20)), nullable=False, server_default="{}")    # personal, keluarga, rame
    tastes = db.Column(ARRAY(db.String(20)), nullable=False, server_default="{}")      # asin, manis, pedas, asam, gurih
    meal_times = db.Column(ARRAY(db.String(20)), nullable=False, server_default="{}")  # sarapan, makan-siang, …
    diet = db.Column(db.String(12), nullable=False, server_default="none")
    halal_only = db.Column(db.Boolean, nullable=False, server_default=text("false"))
    __table_args__ = (CheckConstraint("diet IN ('none','vegetarian','vegan')", name="ck_preferences_diet"),)


class IngredientCategory(db.Model):
    __tablename__ = "ingredient_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)
    slug = db.Column(db.String(40), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, server_default="0")


class Ingredient(db.Model):
    """User requests start as 'pending' until an admin verifies them."""
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("ingredient_categories.id"), nullable=False, index=True)
    image_url = db.Column(db.String(255))
    is_vegan = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    is_vegetarian = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    is_halal = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    popularity = db.Column(db.Integer, nullable=False, server_default="0")
    status = db.Column(db.String(10), nullable=False, server_default="approved")
    requested_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    request_note = db.Column(db.String(300))
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = db.Column(TS)
    review_note = db.Column(db.String(200))
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected')", name="ck_ingredients_status"),
        Index("ux_ingredients_name_approved", func.lower(name), unique=True, postgresql_where=text("status = 'approved'")),
    )


class UserAllergy(db.Model):
    """Allergies are stored as ingredients the user must avoid."""
    __tablename__ = "user_allergies"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True)


class Tag(db.Model):
    """kind 'jenis' = Makanan Berat / Makanan Keluarga / Snack / Dessert · 'rasa' · 'waktu'."""
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    slug = db.Column(db.String(40), nullable=False, unique=True)
    kind = db.Column(db.String(10), nullable=False)
    __table_args__ = (CheckConstraint("kind IN ('jenis','rasa','waktu')", name="ck_tags_kind"),)


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(400), nullable=False, server_default="")
    origin = db.Column(db.String(60))                 # asal hidangan
    image_url = db.Column(db.String(255))             # visual reference
    video_url = db.Column(db.String(500))
    prep_minutes = db.Column(db.Integer, nullable=False, server_default="0")
    cook_minutes = db.Column(db.Integer, nullable=False, server_default="0")
    price_min = db.Column(db.Integer)                 # estimasi biaya (Rupiah)
    price_max = db.Column(db.Integer)
    servings = db.Column(db.Integer, nullable=False, server_default="1")  # base portion for quantities
    status = db.Column(db.String(10), nullable=False, server_default="published")
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    updated_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (
        CheckConstraint("status IN ('draft','published')", name="ck_recipes_status"),
        CheckConstraint("servings BETWEEN 1 AND 50", name="ck_recipes_servings"),
    )


class RecipeTag(db.Model):
    __tablename__ = "recipe_tags"
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True)


class RecipeIngredient(db.Model):
    __tablename__ = "recipe_ingredients"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False, index=True)
    quantity = db.Column(db.Float)                    # NULL = secukupnya
    unit = db.Column(db.String(20), nullable=False, server_default="")
    note = db.Column(db.String(40), nullable=False, server_default="")
    position = db.Column(db.Integer, nullable=False, server_default="0")


class RecipeStep(db.Model):
    __tablename__ = "recipe_steps"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(60), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    media_url = db.Column(db.String(500))
    __table_args__ = (Index("ix_steps_recipe", "recipe_id", "position"),)


class Bookmark(db.Model):
    __tablename__ = "bookmarks"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True, index=True)
    created_at = db.Column(TS, nullable=False, server_default=func.now())


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.String(500), nullable=False, server_default="")
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (
        UniqueConstraint("recipe_id", "user_id", name="uq_reviews_recipe_user"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )


class Promotion(db.Model):
    """Manage Promotion (sponsor)."""
    __tablename__ = "promotions"
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.String(300), nullable=False, server_default="")
    cta_label = db.Column(db.String(30))
    cta_url = db.Column(db.String(500))
    recipe_ids = db.Column(ARRAY(db.Integer), nullable=False, server_default="{}")
    starts_on = db.Column(db.Date, nullable=False, server_default=func.current_date())
    ends_on = db.Column(db.Date)
    active = db.Column(db.Boolean, nullable=False, server_default=text("true"))
    created_at = db.Column(TS, nullable=False, server_default=func.now())


class Notification(db.Model):
    """user_id NULL = broadcast to everyone."""
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    sender = db.Column(db.String(40), nullable=False, server_default="Recipeat")
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(300), nullable=False, server_default="")
    link = db.Column(db.String(500))
    recipe_ids = db.Column(ARRAY(db.Integer), nullable=False, server_default="{}")
    promotion_id = db.Column(db.Integer, db.ForeignKey("promotions.id", ondelete="CASCADE"), index=True)
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (Index("ix_notifications_user", "user_id", "created_at"),)


class Image(db.Model):
    """Uploaded photos (recipe visual reference, ingredient requests).
    Stored in PostgreSQL because serverless hosts such as Vercel have no writable disk."""
    __tablename__ = "images"
    id = db.Column(db.String(32), primary_key=True)          # random hex token → /img/<id>
    mime = db.Column(db.String(20), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    size = db.Column(db.Integer, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(TS, nullable=False, server_default=func.now())
    __table_args__ = (CheckConstraint("size <= 3145728", name="ck_images_size"),)
