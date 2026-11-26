"""Real food photos for the dummy data, hot-linked from Wikimedia Commons (free licences, no AI images)

Images are served by Commons through Special:FilePath (it redirects to a resized thumbnail), so nothing is
copied into the repo. Every photo is credited on /kredit-foto and in CREDITS.md; the file page on Commons
holds the full author/licence details. If a photo ever fails to load, the named placeholder is shown instead
"""
from urllib.parse import quote

COMMONS = "https://commons.wikimedia.org/wiki/"
SEE_FILE = "Lihat halaman berkas"

# recipe title → (Commons file name, author, licence)
RECIPE_PHOTOS = {
    "Nasi Goreng": ("Nasi_Goreng_Udang_Istimewa.JPG", "Gunawan Kartapranata", SEE_FILE),
    "Soto Mie": ("Soto_Mie_Bogor_1.JPG", "Gunawan Kartapranata", SEE_FILE),
    "Martabak Manis Coklat Keju": ("Martabak_manis_Indonesia.jpg", "Malikpb", "CC BY-SA 4.0"),
    "Klepon": ("Klepon_CC_BY_SA_4.0_Suhendro_Winarso.jpg", "Suhendro Winarso", "CC BY-SA 4.0"),
    "Sayur Asem": ("Sayur_asem_vegetable_soup.jpg", "Sakurai Midori", SEE_FILE),
    "Ayam Goreng Lengkuas": ("Ayam_goreng.JPG", "Midori", "GFDL / CC BY-SA 2.1 JP"),
    "Tempe Orek": ("Tempe_Orek.jpg", "Indonesiagood", SEE_FILE),
    "Pisang Goreng": ("Goreng_pisang.jpg", "ProjectManhattan", SEE_FILE),
    "Rendang Sapi": ("Nasi_Rendang.JPG", "Gunawan Kartapranata", SEE_FILE),
    "Telur Balado": ("Telur_Balado.jpg", "Gary Stevens (via Flickr)", SEE_FILE),
    "Sop Ayam": ("Sup_Ayam_Kampung.jpg", "Mdsheth1986", SEE_FILE),
    "Perkedel Kentang": ("Perkedel_kentang_tanpa_daging.JPG", "Midori", SEE_FILE),
    "Tumis Kangkung": ("Tumis_kangkung.JPG", "Midori", "GFDL / CC BY-SA 2.1 JP"),
    "Es Teler": ("Es_teler_di_Bandung.jpg", SEE_FILE, SEE_FILE),
    "Gado-Gado": ("Gado-gado_in_Jakarta.JPG", SEE_FILE, SEE_FILE),
    # "Babi Kecap": no free photo found → keeps its named placeholder
}

# ingredient name → (Commons file name, author, licence). Ingredients without an entry keep a named
# placeholder until an admin approves one with a photo (Request New Ingredient → Verify Ingredient).
INGREDIENT_PHOTOS = {
    "Bawang Merah": ("Shallots-Whole.jpg", "Evan-Amos", "CC BY-SA 3.0"),
    "Bawang Bombay": ("Onion_on_White.JPG", "Colin", "CC BY-SA (lihat halaman berkas)"),
    "Wortel": ("Carrot_vegetable_on_white_background.jpg", "public-domain-image.com", "Domain publik"),
}


def file_url(file_name, width=640):
    return f"{COMMONS}Special:FilePath/{quote(file_name)}?width={width}"


def page_url(file_name):
    return f"{COMMONS}File:{quote(file_name)}"


def recipe_image(title):
    hit = RECIPE_PHOTOS.get(title)
    return file_url(hit[0]) if hit else None


def ingredient_image(name):
    hit = INGREDIENT_PHOTOS.get(name)
    return file_url(hit[0], 320) if hit else None


def credits():
    rows = [("Resep", t, *v) for t, v in RECIPE_PHOTOS.items()] + [("Bahan", n, *v) for n, v in INGREDIENT_PHOTOS.items()]
    return [dict(kind=k, subject=s, file=f, author=a, license=lic, image=file_url(f, 160), page=page_url(f)) for k, s, f, a, lic in rows]
