"""real food photos from Wikimedia Commons for the dummy data

Revision ID: 5f2c7a9d1e44
Revises: cbc6dc1000f9
Create Date: 2026-11-25 21:30:00

Data-only migration: fills image_url for the seeded recipes/ingredients that still have no picture.
Rows that already have an uploaded image are left untouched.
"""
from urllib.parse import quote

from alembic import op
import sqlalchemy as sa

revision = '5f2c7a9d1e44'
down_revision = 'cbc6dc1000f9'
branch_labels = None
depends_on = None

BASE = "https://commons.wikimedia.org/wiki/Special:FilePath/"
RECIPES = {
    "Nasi Goreng": "Nasi_Goreng_Udang_Istimewa.JPG", "Soto Mie": "Soto_Mie_Bogor_1.JPG",
    "Martabak Manis Coklat Keju": "Martabak_manis_Indonesia.jpg", "Klepon": "Klepon_CC_BY_SA_4.0_Suhendro_Winarso.jpg",
    "Sayur Asem": "Sayur_asem_vegetable_soup.jpg", "Ayam Goreng Lengkuas": "Ayam_goreng.JPG", "Tempe Orek": "Tempe_Orek.jpg",
    "Pisang Goreng": "Goreng_pisang.jpg", "Rendang Sapi": "Nasi_Rendang.JPG", "Telur Balado": "Telur_Balado.jpg",
    "Sop Ayam": "Sup_Ayam_Kampung.jpg", "Perkedel Kentang": "Perkedel_kentang_tanpa_daging.JPG",
    "Tumis Kangkung": "Tumis_kangkung.JPG", "Es Teler": "Es_teler_di_Bandung.jpg", "Gado-Gado": "Gado-gado_in_Jakarta.JPG",
}
INGREDIENTS = {"Bawang Merah": "Shallots-Whole.jpg", "Bawang Bombay": "Onion_on_White.JPG", "Wortel": "Carrot_vegetable_on_white_background.jpg"}


def upgrade():
    conn = op.get_bind()
    for table, key, rows, width in (("recipes", "title", RECIPES, 640), ("ingredients", "name", INGREDIENTS, 320)):
        for name, file_name in rows.items():
            conn.execute(sa.text(f"UPDATE {table} SET image_url = :u WHERE {key} = :n AND image_url IS NULL"),
                         {"u": f"{BASE}{quote(file_name)}?width={width}", "n": name})


def downgrade():
    conn = op.get_bind()
    for table in ("recipes", "ingredients"):
        conn.execute(sa.text(f"UPDATE {table} SET image_url = NULL WHERE image_url LIKE :p"), {"p": BASE + "%"})
