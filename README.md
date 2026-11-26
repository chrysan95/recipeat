<p align="center"><img src="public/static/img/logo.webp" width="350" alt="Recipeat Logo"></p>
<h1 align="center">Recipeat</h1>
<p align="center">A recipe website for home cooks. Find what to cook today, cook from what's already in your kitchen (Racik), follow recipes step by step, and get recommendations that respect your taste, portion size, diet and allergies.</p>

**Category:** Web · **Stack:** Flask 3 + Gunicorn · PostgreSQL 16 · Redis 7 · Vercel (Neon + Upstash)

## Features
- Sign up / log in with bcrypt-hashed passwords (no reuse of the last 10 passwords)
- **Search** recipes with category filter (Makanan Berat, Keluarga, Snack, Dessert), taste filter and sorting
- **Racik**: pick the ingredients you have into the **Keranjang**, get recipes ranked by how many ingredients match
- **Recipe page**: prep/cook time, price range, origin, portion scaling, copy ingredient list, cook mode, bookmarks and reviews
- **Add recipe** with photo, video link and per-step media
- **Request a new ingredient** with a photo; an **admin** approves (and can replace the photo) or rejects it with a reason
- **Preferences**: portion, taste, meal time, diet (vegetarian/vegan/halal) and allergies
- **Profile**: name/email, password and profile picture (food preferences for regular users only)
- **Promotions**: sponsors and admins create promotions shown on the home page and sent as notifications

### What each role sees
| Role | Navbar | Resep tab | Notifikasi tab |
|---|---|---|---|
| User | Home · Racik · Resep · Notifikasi | Resep Tersimpan + Resep Anda | Notifications |
| Sponsor | Resep · Notifikasi | Resep Anda (+ Ajukan bahan baru) | Kelola Promosi |
| Admin | Resep · Notifikasi | Verifikasi Bahan + Riwayat Bahan | Kelola Promosi |

## Architecture
```
Browser ──► Vercel CDN (public/static) 
        └─► Vercel Function [Flask app: wsgi.py] ──► Neon   [PostgreSQL]  data + uploaded images
                                                └─► Upstash [Redis]       sessions, rate limits, cache
Local:  docker compose → PostgreSQL :5432 + Redis :6379, app on :5000
```

## Routes
| Path | Page |
|---|---|
| `/masuk`, `/daftar`, `POST /keluar` | Log in, sign up, log out |
| `/` | Home: search, quick ingredients, recommendations |
| `/cari` | Search with filters and sorting |
| `/racik`, `/racik/hasil?bahan=` | Pick ingredients, matching recipes |
| `/resep`, `/resep/tersimpan` | Saved recipes + my recipes (sponsors: my recipes only), saved recipes |
| `/resep/<id>`, `/resep/<id>/masak` | Recipe detail, cook mode |
| `/resep/baru`, `/resep/<id>/ubah` | Add / edit recipe |
| `/bahan/ajukan` | Request a new ingredient |
| `/notifikasi` | Notifications (sponsors and admins are sent to `/sponsor/promosi`) |
| `/profil`, `/profil/kata-sandi`, `/profil/preferensi`, `POST /profil/foto` | Profile pages, profile picture |
| `/admin/bahan` | Admin's Resep tab: verify ingredients, ingredient history |
| `/sponsor/promosi` | Sponsor's and admin's Notifikasi tab: manage promotions |
| `/img/<id>` | Uploaded images |
| `/healthz` | Health check |

## Run on localhost
```bash
git clone https://github.com/chrysan95/recipeat.git
cd recipeat
docker compose up -d                                   # PostgreSQL + Redis
python -m venv .venv 
.venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
flask db upgrade; flask seed
flask run --debug
```
Open http://localhost:5000. The database only contains dummy data.

| Role | Email | Password |
|---|---|---|
| User | keisa@gmail.com | `Keisa#2026` |
| User (vegan) | sari@gmail.com | `Sari#2026` |
| Admin | admin@recipeat.id | `Admin#2026` |
| Sponsor | sponsor@dapurnusa.id | `Sponsor#2026` |

Tests: `docker compose exec db createdb -U postgres recipeat_test`, then `pytest`.

## Deploy
Push to GitHub, import the repo in Vercel and set `DATABASE_URL` (Neon, pooled), `REDIS_URL` (Upstash, `rediss://`) and `SECRET_KEY`. Tables and dummy data are created on the first request (`app/bootstrap.py`). Set `SEED_DUMMY_DATA=0` to skip the dummy data. Static files are linked with a version (`style.css?v=…`). Versioned files are cached for a year, others are always revalidated (`vercel.json`), so a new deploy shows up immediately.

## Project structure
```
wsgi.py                     entry point for Vercel, Gunicorn and the flask CLI
vercel.json                 Vercel function settings and static cache headers
.vercelignore               files left out of the Vercel bundle
.python-version             Python version for Vercel and CI
gunicorn.conf.py            local production-like server
docker-compose.yml          local PostgreSQL + Redis
.env.example                environment variables template
requirements.txt            app dependencies (requirements-dev.txt adds pytest, 
                            gunicorn)
app/
  __init__.py               create_app(): extensions, blueprints, error pages
  config.py                 settings read from environment variables
  extensions.py             db, migrate, login manager, CSRF, rate limiter, sessions
  models.py                 database tables
  bootstrap.py              migrates + seeds on Vercel's first cold start
  security.py               bcrypt hashing and password rules
  auth_utils.py             loads the logged-in user and checks roles
  redis_store.py            Redis cache and login throttle
  recipes.py                search, filter and sort queries
  personalise.py            preferences → filters and recommendations
  uploads.py                validates image uploads and stores them in PostgreSQL
  helpers.py                Jinja helpers (dates, prices, initials, quantities)
  icons.py                  inline SVG icons
  photo_credits.py          food photos from Wikimedia Commons + their hover 
                            credit
  seed.py, seed_data.json   `flask seed` dummy data and `flask dump-sql`
  blueprints/               routes: auth, recipes, editor (add/edit recipe), racik,
                            profile, roles (admin + sponsor), media (/img/<id>)
  templates/                pages; partials/ has the navbar, macros and profile layout
public/static/              css/style.css (design system), js/, img/ (logo.webp, 
                            logo@2x.webp, weblogo.png)
migrations/                 Alembic database migrations (schema, images, food     
                            photos, profile picture, indexes)
database/recipeat_dummy.sql same dummy data as a plain SQL dump
tests/                      pytest tests against PostgreSQL + Redis
.github/workflows/ci.yml    runs the tests on every push
```

## Credits
Font: Font: Figtree (Google Fonts, OFL). Food photos: Wikimedia Commons, listed below and shown when hovering a photo. Libraries: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Flask-Session, Flask-Limiter, psycopg, redis-py, bcrypt, Gunicorn. Libraries: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Flask-Session, Flask-Limiter, psycopg, redis-py, bcrypt, Gunicorn.

| Untuk | Berkas Commons | Penulis | Lisensi |
|---|---|---|---|
| Resep: Nasi Goreng | [Nasi_Goreng_Udang_Istimewa.JPG](https://commons.wikimedia.org/wiki/File:Nasi_Goreng_Udang_Istimewa.JPG) | Gunawan Kartapranata | Lihat halaman berkas |
| Resep: Soto Mie | [Soto_Mie_Bogor_1.JPG](https://commons.wikimedia.org/wiki/File:Soto_Mie_Bogor_1.JPG) | Gunawan Kartapranata | Lihat halaman berkas |
| Resep: Martabak Manis Coklat Keju | [Martabak_manis_Indonesia.jpg](https://commons.wikimedia.org/wiki/File:Martabak_manis_Indonesia.jpg) | Malikpb | CC BY-SA 4.0 |
| Resep: Klepon | [Klepon_CC_BY_SA_4.0_Suhendro_Winarso.jpg](https://commons.wikimedia.org/wiki/File:Klepon_CC_BY_SA_4.0_Suhendro_Winarso.jpg) | Suhendro Winarso | CC BY-SA 4.0 |
| Resep: Sayur Asem | [Sayur_asem_vegetable_soup.jpg](https://commons.wikimedia.org/wiki/File:Sayur_asem_vegetable_soup.jpg) | Sakurai Midori | Lihat halaman berkas |
| Resep: Ayam Goreng Lengkuas | [Ayam_goreng.JPG](https://commons.wikimedia.org/wiki/File:Ayam_goreng.JPG) | Midori | GFDL / CC BY-SA 2.1 JP |
| Resep: Tempe Orek | [Tempe_Orek.jpg](https://commons.wikimedia.org/wiki/File:Tempe_Orek.jpg) | Indonesiagood | Lihat halaman berkas |
| Resep: Pisang Goreng | [Goreng_pisang.jpg](https://commons.wikimedia.org/wiki/File:Goreng_pisang.jpg) | ProjectManhattan | Lihat halaman berkas |
| Resep: Rendang Sapi | [Nasi_Rendang.JPG](https://commons.wikimedia.org/wiki/File:Nasi_Rendang.JPG) | Gunawan Kartapranata | Lihat halaman berkas |
| Resep: Telur Balado | [Telur_Balado.jpg](https://commons.wikimedia.org/wiki/File:Telur_Balado.jpg) | Gary Stevens (via Flickr) | Lihat halaman berkas |
| Resep: Sop Ayam | [Sup_Ayam_Kampung.jpg](https://commons.wikimedia.org/wiki/File:Sup_Ayam_Kampung.jpg) | Mdsheth1986 | Lihat halaman berkas |
| Resep: Perkedel Kentang | [Perkedel_kentang_tanpa_daging.JPG](https://commons.wikimedia.org/wiki/File:Perkedel_kentang_tanpa_daging.JPG) | Midori | Lihat halaman berkas |
| Resep: Tumis Kangkung | [Tumis_kangkung.JPG](https://commons.wikimedia.org/wiki/File:Tumis_kangkung.JPG) | Midori | GFDL / CC BY-SA 2.1 JP |
| Resep: Es Teler | [Es_teler_di_Bandung.jpg](https://commons.wikimedia.org/wiki/File:Es_teler_di_Bandung.jpg) | Lihat halaman berkas | Lihat halaman berkas |
| Resep: Gado-Gado | [Gado-gado_in_Jakarta.JPG](https://commons.wikimedia.org/wiki/File:Gado-gado_in_Jakarta.JPG) | Lihat halaman berkas | Lihat halaman berkas |
| Bahan: Bawang Merah | [Shallots-Whole.jpg](https://commons.wikimedia.org/wiki/File:Shallots-Whole.jpg) | Evan-Amos | CC BY-SA 3.0 |
| Bahan: Bawang Bombay | [Onion_on_White.JPG](https://commons.wikimedia.org/wiki/File:Onion_on_White.JPG) | Colin | CC BY-SA (lihat halaman berkas) |
| Bahan: Wortel | [Carrot_vegetable_on_white_background.jpg](https://commons.wikimedia.org/wiki/File:Carrot_vegetable_on_white_background.jpg) | public-domain-image.com | Domain publik |


## AI Usage Declaration
- **Tool:** Claude
- **Parts assisted:** coding assistance, debugging, writing this README
- **Main prompt example:** 
  - based on the diagram provided, give me a dummy sql
  - in the racik page, the keranjang should be a button that can open to a side bar when pressed, if 0 show Keranjang if >0 show Keranjang (num), for the slider in racik, make it into the blue color and sleek color
  - make sure it is top aligned instead of bottom aligned
  - make sure you use Regular and Bold for fonts
  - change the eye logo on the login and sign up and make sure that its default to censoring and eye open, but when user clicks, uncensor and change to eye closed
  - for navbar, if hovered use a floating blue button with white font and if its on the page use floating white button and blue font like the reference
  - for placeholder food images, find some pictures online, dont use AI to generate photos
  - if the buttons are for captions, dont make it bigger than CTA
  - PADDINGS!
  - make sure that even on different screen sizes, the white space and font % is the same
- **Own work:** Recipeat logo, design, planning, use case, class case, activity case diagrams
