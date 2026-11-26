"""profile picture

Revision ID: a3e91c4d7b20
Revises: 5f2c7a9d1e44
Create Date: 2026-11-25 23:40:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3e91c4d7b20'
down_revision = '5f2c7a9d1e44'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('avatar_url', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'avatar_url')
