"""indexes for the lookups the app runs most

Revision ID: c4d82e6f9a13
Revises: a3e91c4d7b20
Create Date: 2026-11-26 17:50:00

bookmarks.recipe_id → bookmark counts per recipe (the primary key starts with user_id, so it can't serve this)
recipe_tags.tag_id  → tag filters on Home/Cari
ingredients.requested_by → "Pengajuanku" and the admin history
notifications.promotion_id → "sent" count on Kelola Promosi + promotion cascade deletes
"""
from alembic import op

revision = 'c4d82e6f9a13'
down_revision = 'a3e91c4d7b20'
branch_labels = None
depends_on = None

INDEXES = [("ix_bookmarks_recipe_id", "bookmarks", "recipe_id"), ("ix_recipe_tags_tag_id", "recipe_tags", "tag_id"),
           ("ix_ingredients_requested_by", "ingredients", "requested_by"), ("ix_notifications_promotion_id", "notifications", "promotion_id")]


def upgrade():
    for name, table, column in INDEXES:
        op.create_index(name, table, [column])


def downgrade():
    for name, table, _ in INDEXES:
        op.drop_index(name, table_name=table)
