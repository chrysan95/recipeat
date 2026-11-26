-- Recipeat dummy database for PostgreSQL (generated 2026-11-25 by `flask dump-sql`)
-- Passwords are bcrypt hashes. Demo logins are listed in README.md.
-- Load with: psql "$DATABASE_URL" -f database/recipeat_dummy.sql

CREATE TABLE ingredient_categories (
	id SERIAL NOT NULL, 
	name VARCHAR(40) NOT NULL, 
	slug VARCHAR(40) NOT NULL, 
	position INTEGER DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (slug)
);

CREATE TABLE tags (
	id SERIAL NOT NULL, 
	name VARCHAR(40) NOT NULL, 
	slug VARCHAR(40) NOT NULL, 
	kind VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_tags_kind CHECK (kind IN ('jenis','rasa','waktu')), 
	UNIQUE (slug)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(72) NOT NULL, 
	role VARCHAR(10) DEFAULT 'user' NOT NULL, 
	newsletter BOOLEAN DEFAULT false NOT NULL, 
	session_version INTEGER DEFAULT '1' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_users_role CHECK (role IN ('user','admin','sponsor')), 
	UNIQUE (email)
);

CREATE TABLE images (
	id VARCHAR(32) NOT NULL, 
	mime VARCHAR(20) NOT NULL, 
	data BYTEA NOT NULL, 
	size INTEGER NOT NULL, 
	uploaded_by INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_images_size CHECK (size <= 3145728), 
	FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE ingredients (
	id SERIAL NOT NULL, 
	name VARCHAR(40) NOT NULL, 
	category_id INTEGER NOT NULL, 
	image_url VARCHAR(255), 
	is_vegan BOOLEAN DEFAULT true NOT NULL, 
	is_vegetarian BOOLEAN DEFAULT true NOT NULL, 
	is_halal BOOLEAN DEFAULT true NOT NULL, 
	popularity INTEGER DEFAULT '0' NOT NULL, 
	status VARCHAR(10) DEFAULT 'approved' NOT NULL, 
	requested_by INTEGER, 
	request_note VARCHAR(300), 
	reviewed_by INTEGER, 
	reviewed_at TIMESTAMP WITH TIME ZONE, 
	review_note VARCHAR(200), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_ingredients_status CHECK (status IN ('pending','approved','rejected')), 
	FOREIGN KEY(category_id) REFERENCES ingredient_categories (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE SET NULL, 
	FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE SET NULL
);
CREATE INDEX ix_ingredients_category_id ON ingredients (category_id);
CREATE UNIQUE INDEX ux_ingredients_name_approved ON ingredients (lower(name)) WHERE status = 'approved';

CREATE TABLE password_history (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	password_hash VARCHAR(72) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_password_history_user_id ON password_history (user_id);

CREATE TABLE preferences (
	user_id INTEGER NOT NULL, 
	portions VARCHAR(20)[] DEFAULT '{}' NOT NULL, 
	tastes VARCHAR(20)[] DEFAULT '{}' NOT NULL, 
	meal_times VARCHAR(20)[] DEFAULT '{}' NOT NULL, 
	diet VARCHAR(12) DEFAULT 'none' NOT NULL, 
	halal_only BOOLEAN DEFAULT false NOT NULL, 
	PRIMARY KEY (user_id), 
	CONSTRAINT ck_preferences_diet CHECK (diet IN ('none','vegetarian','vegan')), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE promotions (
	id SERIAL NOT NULL, 
	sponsor_id INTEGER NOT NULL, 
	brand VARCHAR(40) NOT NULL, 
	title VARCHAR(80) NOT NULL, 
	body VARCHAR(300) DEFAULT '' NOT NULL, 
	cta_label VARCHAR(30), 
	cta_url VARCHAR(500), 
	recipe_ids INTEGER[] DEFAULT '{}' NOT NULL, 
	starts_on DATE DEFAULT CURRENT_DATE NOT NULL, 
	ends_on DATE, 
	active BOOLEAN DEFAULT true NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sponsor_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_promotions_sponsor_id ON promotions (sponsor_id);

CREATE TABLE recipes (
	id SERIAL NOT NULL, 
	author_id INTEGER NOT NULL, 
	title VARCHAR(80) NOT NULL, 
	description VARCHAR(400) DEFAULT '' NOT NULL, 
	origin VARCHAR(60), 
	image_url VARCHAR(255), 
	video_url VARCHAR(500), 
	prep_minutes INTEGER DEFAULT '0' NOT NULL, 
	cook_minutes INTEGER DEFAULT '0' NOT NULL, 
	price_min INTEGER, 
	price_max INTEGER, 
	servings INTEGER DEFAULT '1' NOT NULL, 
	status VARCHAR(10) DEFAULT 'published' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_recipes_status CHECK (status IN ('draft','published')), 
	CONSTRAINT ck_recipes_servings CHECK (servings BETWEEN 1 AND 50), 
	FOREIGN KEY(author_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_recipes_author_id ON recipes (author_id);

CREATE TABLE bookmarks (
	user_id INTEGER NOT NULL, 
	recipe_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id, recipe_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
);

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	sender VARCHAR(40) DEFAULT 'Recipeat' NOT NULL, 
	title VARCHAR(120) NOT NULL, 
	body VARCHAR(300) DEFAULT '' NOT NULL, 
	link VARCHAR(500), 
	recipe_ids INTEGER[] DEFAULT '{}' NOT NULL, 
	promotion_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(promotion_id) REFERENCES promotions (id) ON DELETE CASCADE
);
CREATE INDEX ix_notifications_user ON notifications (user_id, created_at);

CREATE TABLE recipe_ingredients (
	id SERIAL NOT NULL, 
	recipe_id INTEGER NOT NULL, 
	ingredient_id INTEGER NOT NULL, 
	quantity FLOAT, 
	unit VARCHAR(20) DEFAULT '' NOT NULL, 
	note VARCHAR(40) DEFAULT '' NOT NULL, 
	position INTEGER DEFAULT '0' NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE CASCADE, 
	FOREIGN KEY(ingredient_id) REFERENCES ingredients (id)
);
CREATE INDEX ix_recipe_ingredients_ingredient_id ON recipe_ingredients (ingredient_id);
CREATE INDEX ix_recipe_ingredients_recipe_id ON recipe_ingredients (recipe_id);

CREATE TABLE recipe_steps (
	id SERIAL NOT NULL, 
	recipe_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	title VARCHAR(60) NOT NULL, 
	body VARCHAR(1000) NOT NULL, 
	media_url VARCHAR(500), 
	PRIMARY KEY (id), 
	FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
);
CREATE INDEX ix_steps_recipe ON recipe_steps (recipe_id, position);

CREATE TABLE recipe_tags (
	recipe_id INTEGER NOT NULL, 
	tag_id INTEGER NOT NULL, 
	PRIMARY KEY (recipe_id, tag_id), 
	FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE CASCADE, 
	FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE
);

CREATE TABLE reviews (
	id SERIAL NOT NULL, 
	recipe_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	rating SMALLINT NOT NULL, 
	comment VARCHAR(500) DEFAULT '' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reviews_recipe_user UNIQUE (recipe_id, user_id), 
	CONSTRAINT ck_reviews_rating CHECK (rating BETWEEN 1 AND 5), 
	FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_reviews_recipe_id ON reviews (recipe_id);

CREATE TABLE user_allergies (
	user_id INTEGER NOT NULL, 
	ingredient_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, ingredient_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE CASCADE
);

BEGIN;

-- ingredient_categories (14)
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (1, 'Daging', 'daging', 0);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (2, 'Telur', 'telur', 1);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (3, 'Sayur', 'sayur', 2);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (4, 'Buah', 'buah', 3);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (5, 'Ikan', 'ikan', 4);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (6, 'Bumbu Dapur', 'bumbu-dapur', 5);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (7, 'Rempah', 'rempah', 6);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (8, 'Bahan Masakan', 'bahan-masakan', 7);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (9, 'Susu & Olahan', 'susu-dan-olahan', 8);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (10, 'Sarapan', 'sarapan', 9);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (11, 'Minuman', 'minuman', 10);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (12, 'Dessert & Juice', 'dessert-dan-juice', 11);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (13, 'Bahan Kue', 'bahan-kue', 12);
INSERT INTO ingredient_categories (id, name, slug, position) VALUES (14, 'Non Halal', 'non-halal', 13);
SELECT setval(pg_get_serial_sequence('ingredient_categories', 'id'), (SELECT MAX(id) FROM ingredient_categories));

-- tags (13)
INSERT INTO tags (id, name, slug, kind) VALUES (1, 'Makanan Berat', 'berat', 'jenis');
INSERT INTO tags (id, name, slug, kind) VALUES (2, 'Makanan Keluarga', 'keluarga', 'jenis');
INSERT INTO tags (id, name, slug, kind) VALUES (3, 'Snack', 'snack', 'jenis');
INSERT INTO tags (id, name, slug, kind) VALUES (4, 'Dessert', 'dessert', 'jenis');
INSERT INTO tags (id, name, slug, kind) VALUES (5, 'Asin', 'asin', 'rasa');
INSERT INTO tags (id, name, slug, kind) VALUES (6, 'Manis', 'manis', 'rasa');
INSERT INTO tags (id, name, slug, kind) VALUES (7, 'Pedas', 'pedas', 'rasa');
INSERT INTO tags (id, name, slug, kind) VALUES (8, 'Asam', 'asam', 'rasa');
INSERT INTO tags (id, name, slug, kind) VALUES (9, 'Gurih', 'gurih', 'rasa');
INSERT INTO tags (id, name, slug, kind) VALUES (10, 'Sarapan', 'sarapan', 'waktu');
INSERT INTO tags (id, name, slug, kind) VALUES (11, 'Makan Siang', 'makan-siang', 'waktu');
INSERT INTO tags (id, name, slug, kind) VALUES (12, 'Makan Malam', 'makan-malam', 'waktu');
INSERT INTO tags (id, name, slug, kind) VALUES (13, 'Camilan', 'camilan', 'waktu');
SELECT setval(pg_get_serial_sequence('tags', 'id'), (SELECT MAX(id) FROM tags));

-- users (5)
INSERT INTO users (id, name, email, password_hash, role, newsletter, session_version, created_at) VALUES (1, 'Admin Recipeat', 'admin@recipeat.id', '$2b$12$CYVVpsNfIqtNKt5Edd06JOii4rB/bkyzewvGohDlc2zUeM.8A/14e', 'admin', FALSE, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO users (id, name, email, password_hash, role, newsletter, session_version, created_at) VALUES (2, 'Dapurnusa', 'sponsor@dapurnusa.id', '$2b$12$soh.iE/0lOEVzb4PO60tB.B56Z5eQ.KgYwsu1M/PBfM5LJWwKgz9W', 'sponsor', FALSE, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO users (id, name, email, password_hash, role, newsletter, session_version, created_at) VALUES (3, 'Keisa', 'keisa@gmail.com', '$2b$12$XKZQ95kdlPvoPwU7/eVg7uZxhh5FPLMOFE3YkxjYH2hIFQYrAu9OW', 'user', TRUE, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO users (id, name, email, password_hash, role, newsletter, session_version, created_at) VALUES (4, 'Budi', 'budi@gmail.com', '$2b$12$ISVeF2ymL1b8fONtv5tkKO0bx3EdYX0TlHMuHFNgQA6YqK1WOpwz2', 'user', FALSE, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO users (id, name, email, password_hash, role, newsletter, session_version, created_at) VALUES (5, 'Sari Wulandari', 'sari@gmail.com', '$2b$12$UZg.8l/UzkXglxe0Ft66t.v8Vw7Uolo1g/nH0.quxLB0w18vefi3u', 'user', FALSE, 1, '2026-11-25T22:20:13.658016+07:00');
SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));

-- ingredients (71)
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (1, 'Ayam', 1, NULL, FALSE, FALSE, TRUE, 98, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (2, 'Daging Sapi', 1, NULL, FALSE, FALSE, TRUE, 80, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (3, 'Telur', 2, NULL, FALSE, TRUE, TRUE, 97, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (4, 'Bawang Bombay', 3, 'https://commons.wikimedia.org/wiki/Special:FilePath/Onion_on_White.JPG?width=320', TRUE, TRUE, TRUE, 90, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (5, 'Wortel', 3, 'https://commons.wikimedia.org/wiki/Special:FilePath/Carrot_vegetable_on_white_background.jpg?width=320', TRUE, TRUE, TRUE, 89, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (6, 'Kentang', 3, NULL, TRUE, TRUE, TRUE, 88, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (7, 'Tomat', 3, NULL, TRUE, TRUE, TRUE, 87, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (8, 'Daun Singkong', 3, NULL, TRUE, TRUE, TRUE, 40, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (9, 'Jagung', 3, NULL, TRUE, TRUE, TRUE, 60, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (10, 'Kangkung', 3, NULL, TRUE, TRUE, TRUE, 65, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (11, 'Kacang Panjang', 3, NULL, TRUE, TRUE, TRUE, 55, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (12, 'Kol', 3, NULL, TRUE, TRUE, TRUE, 58, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (13, 'Tauge', 3, NULL, TRUE, TRUE, TRUE, 50, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (14, 'Labu Siam', 3, NULL, TRUE, TRUE, TRUE, 45, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (15, 'Daun Bawang', 3, NULL, TRUE, TRUE, TRUE, 62, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (16, 'Seledri', 3, NULL, TRUE, TRUE, TRUE, 52, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (17, 'Timun', 3, NULL, TRUE, TRUE, TRUE, 57, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (18, 'Melinjo', 3, NULL, TRUE, TRUE, TRUE, 30, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (19, 'Pisang', 4, NULL, TRUE, TRUE, TRUE, 70, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (20, 'Alpukat', 4, NULL, TRUE, TRUE, TRUE, 54, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (21, 'Nangka', 4, NULL, TRUE, TRUE, TRUE, 35, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (22, 'Kelapa Muda', 4, NULL, TRUE, TRUE, TRUE, 38, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (23, 'Kelapa Parut', 4, NULL, TRUE, TRUE, TRUE, 44, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (24, 'Ikan Kembung', 5, NULL, FALSE, FALSE, TRUE, 42, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (25, 'Udang', 5, NULL, FALSE, FALSE, TRUE, 61, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (26, 'Bawang Merah', 6, 'https://commons.wikimedia.org/wiki/Special:FilePath/Shallots-Whole.jpg?width=320', TRUE, TRUE, TRUE, 96, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (27, 'Bawang Putih', 6, NULL, TRUE, TRUE, TRUE, 95, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (28, 'Cabe Merah Besar', 6, NULL, TRUE, TRUE, TRUE, 84, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (29, 'Cabe Rawit', 6, NULL, TRUE, TRUE, TRUE, 79, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (30, 'Garam', 6, NULL, TRUE, TRUE, TRUE, 99, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (31, 'Gula', 6, NULL, TRUE, TRUE, TRUE, 93, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (32, 'Gula Merah', 6, NULL, TRUE, TRUE, TRUE, 59, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (33, 'Kecap Manis', 6, NULL, TRUE, TRUE, TRUE, 85, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (34, 'Merica', 6, NULL, TRUE, TRUE, TRUE, 75, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (35, 'Kemiri', 6, NULL, TRUE, TRUE, TRUE, 48, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (36, 'Terasi', 6, NULL, FALSE, FALSE, TRUE, 46, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (37, 'Asam Jawa', 6, NULL, TRUE, TRUE, TRUE, 41, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (38, 'Lengkuas', 7, NULL, TRUE, TRUE, TRUE, 53, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (39, 'Jahe', 7, NULL, TRUE, TRUE, TRUE, 64, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (40, 'Kunyit', 7, NULL, TRUE, TRUE, TRUE, 56, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (41, 'Serai', 7, NULL, TRUE, TRUE, TRUE, 58, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (42, 'Daun Salam', 7, NULL, TRUE, TRUE, TRUE, 60, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (43, 'Daun Jeruk', 7, NULL, TRUE, TRUE, TRUE, 49, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (44, 'Ketumbar', 7, NULL, TRUE, TRUE, TRUE, 47, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (45, 'Kayu Manis', 7, NULL, TRUE, TRUE, TRUE, 33, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (46, 'Perasa Pandan', 7, NULL, TRUE, TRUE, TRUE, 36, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (47, 'Minyak Goreng', 8, NULL, TRUE, TRUE, TRUE, 94, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (48, 'Nasi', 8, NULL, TRUE, TRUE, TRUE, 92, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (49, 'Tempe', 8, NULL, TRUE, TRUE, TRUE, 74, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (50, 'Tahu', 8, NULL, TRUE, TRUE, TRUE, 73, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (51, 'Mie Kuning', 8, NULL, TRUE, TRUE, TRUE, 63, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (52, 'Santan', 8, NULL, TRUE, TRUE, TRUE, 66, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (53, 'Kacang Tanah', 8, NULL, TRUE, TRUE, TRUE, 51, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (54, 'Air', 8, NULL, TRUE, TRUE, TRUE, 20, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (55, 'Susu Kental Manis', 9, NULL, FALSE, TRUE, TRUE, 57, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (56, 'Keju', 9, NULL, FALSE, TRUE, TRUE, 62, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (57, 'Mentega', 9, NULL, FALSE, TRUE, TRUE, 61, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (58, 'Roti Tawar', 10, NULL, FALSE, TRUE, TRUE, 55, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (59, 'Teh', 11, NULL, TRUE, TRUE, TRUE, 40, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (60, 'Sirup Cocopandan', 12, NULL, TRUE, TRUE, TRUE, 37, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (61, 'Es Batu', 12, NULL, TRUE, TRUE, TRUE, 39, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (62, 'Tepung Terigu', 13, NULL, TRUE, TRUE, TRUE, 72, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (63, 'Tepung Ketan', 13, NULL, TRUE, TRUE, TRUE, 34, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (64, 'Tepung Beras', 13, NULL, TRUE, TRUE, TRUE, 43, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (65, 'Ragi Instan', 13, NULL, TRUE, TRUE, TRUE, 31, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (66, 'Cokelat Meses', 13, NULL, FALSE, TRUE, TRUE, 45, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (67, 'Daging Babi', 14, NULL, FALSE, FALSE, FALSE, 25, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (68, 'Angciu', 14, NULL, TRUE, TRUE, FALSE, 15, 'approved', NULL, NULL, 1, '2026-11-25T22:20:13.659107+07:00', NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (69, 'Andaliman', 7, NULL, TRUE, TRUE, TRUE, 0, 'pending', 3, 'Rempah khas Batak untuk arsik.', NULL, NULL, NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (70, 'Kecombrang', 3, NULL, TRUE, TRUE, TRUE, 0, 'pending', 4, 'Bunga honje untuk sambal dan pecak.', NULL, NULL, NULL, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO ingredients (id, name, category_id, image_url, is_vegan, is_vegetarian, is_halal, popularity, status, requested_by, request_note, reviewed_by, reviewed_at, review_note, created_at) VALUES (71, 'Bawang Merah Brebes', 6, NULL, TRUE, TRUE, TRUE, 0, 'rejected', 5, NULL, 1, '2026-11-25T22:20:13.659107+07:00', 'Sudah tersedia sebagai "Bawang Merah".', '2026-11-25T22:20:13.658016+07:00');
SELECT setval(pg_get_serial_sequence('ingredients', 'id'), (SELECT MAX(id) FROM ingredients));

-- password_history (5)
INSERT INTO password_history (id, user_id, password_hash, created_at) VALUES (1, 1, '$2b$12$CYVVpsNfIqtNKt5Edd06JOii4rB/bkyzewvGohDlc2zUeM.8A/14e', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO password_history (id, user_id, password_hash, created_at) VALUES (2, 2, '$2b$12$soh.iE/0lOEVzb4PO60tB.B56Z5eQ.KgYwsu1M/PBfM5LJWwKgz9W', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO password_history (id, user_id, password_hash, created_at) VALUES (3, 3, '$2b$12$XKZQ95kdlPvoPwU7/eVg7uZxhh5FPLMOFE3YkxjYH2hIFQYrAu9OW', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO password_history (id, user_id, password_hash, created_at) VALUES (4, 4, '$2b$12$ISVeF2ymL1b8fONtv5tkKO0bx3EdYX0TlHMuHFNgQA6YqK1WOpwz2', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO password_history (id, user_id, password_hash, created_at) VALUES (5, 5, '$2b$12$UZg.8l/UzkXglxe0Ft66t.v8Vw7Uolo1g/nH0.quxLB0w18vefi3u', '2026-11-25T22:20:13.658016+07:00');
SELECT setval(pg_get_serial_sequence('password_history', 'id'), (SELECT MAX(id) FROM password_history));

-- preferences (5)
INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only) VALUES (1, '{}', '{}', '{}', 'none', FALSE);
INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only) VALUES (2, '{}', '{}', '{}', 'none', FALSE);
INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only) VALUES (3, '{rame}', '{pedas,gurih}', '{makan-malam}', 'none', TRUE);
INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only) VALUES (4, '{keluarga}', '{asin,gurih}', '{makan-siang,makan-malam}', 'none', FALSE);
INSERT INTO preferences (user_id, portions, tastes, meal_times, diet, halal_only) VALUES (5, '{personal}', '{manis,pedas}', '{sarapan,camilan}', 'vegan', TRUE);

-- promotions (1)
INSERT INTO promotions (id, sponsor_id, brand, title, body, cta_label, cta_url, recipe_ids, starts_on, ends_on, active, created_at) VALUES (1, 2, 'Dapurnusa', 'Masak apa ya hari ini?', 'Cobain rekomendasi resep di bawah ini. Jangan lupa recook, ya!', 'Lihat resep', '/cari?jenis=berat', '{1,2,6,10}', '2026-11-25', '2026-12-25', TRUE, '2026-11-25T22:20:13.658016+07:00');
SELECT setval(pg_get_serial_sequence('promotions', 'id'), (SELECT MAX(id) FROM promotions));

-- recipes (16)
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (1, 4, 'Nasi Goreng', 'Sajian nasi yang ditumis dengan kecap manis, rempah, dan sayuran, serta sering disajikan dengan tambahan telur ceplok.', 'Indonesia', 'https://commons.wikimedia.org/wiki/Special:FilePath/Nasi_Goreng_Udang_Istimewa.JPG?width=640', 'https://www.youtube.com/watch?v=placeholder01', 10, 25, 15000, 25000, 1, 'published', '2026-10-08T22:20:13.659107+07:00', '2026-10-08T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (2, 4, 'Soto Mie', 'Soto berkuah kuning gurih khas Bogor dengan mie kuning, irisan daging sapi, kol, dan tomat.', 'Bogor', 'https://commons.wikimedia.org/wiki/Special:FilePath/Soto_Mie_Bogor_1.JPG?width=640', NULL, 20, 40, 40000, 60000, 4, 'published', '2026-10-11T22:20:13.659107+07:00', '2026-10-11T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (3, 3, 'Martabak Manis Coklat Keju', 'Martabak tebal bersarang dengan olesan mentega, taburan cokelat meses, keju parut, dan susu kental manis.', 'Bangka', 'https://commons.wikimedia.org/wiki/Special:FilePath/Martabak_manis_Indonesia.jpg?width=640', NULL, 70, 15, 30000, 45000, 4, 'published', '2026-10-14T22:20:13.659107+07:00', '2026-10-14T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (4, 3, 'Klepon', 'Bola ketan hijau beraroma pandan berisi gula merah cair dan dibalut kelapa parut.', 'Jawa', 'https://commons.wikimedia.org/wiki/Special:FilePath/Klepon_CC_BY_SA_4.0_Suhendro_Winarso.jpg?width=640', NULL, 20, 15, 15000, 25000, 4, 'published', '2026-10-17T22:20:13.659107+07:00', '2026-10-17T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (5, 4, 'Sayur Asem', 'Sayur berkuah segar asam-manis berisi labu siam, kacang panjang, jagung, dan melinjo.', 'Betawi', 'https://commons.wikimedia.org/wiki/Special:FilePath/Sayur_asem_vegetable_soup.jpg?width=640', NULL, 15, 30, 20000, 30000, 4, 'published', '2026-10-20T22:20:13.659107+07:00', '2026-10-20T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (6, 4, 'Ayam Goreng Lengkuas', 'Ayam diungkep bumbu kuning lalu digoreng renyah bersama serundeng lengkuas.', 'Sunda', 'https://commons.wikimedia.org/wiki/Special:FilePath/Ayam_goreng.JPG?width=640', NULL, 15, 45, 35000, 50000, 4, 'published', '2026-10-23T22:20:13.659107+07:00', '2026-10-23T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (7, 5, 'Tempe Orek', 'Tempe goreng kering yang ditumis kecap manis dan cabai, cocok untuk bekal.', 'Jawa', 'https://commons.wikimedia.org/wiki/Special:FilePath/Tempe_Orek.jpg?width=640', NULL, 10, 15, 10000, 15000, 2, 'published', '2026-10-26T22:20:13.659107+07:00', '2026-10-26T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (8, 5, 'Pisang Goreng', 'Pisang berbalut adonan tepung renyah, camilan sore yang paling gampang.', 'Indonesia', 'https://commons.wikimedia.org/wiki/Special:FilePath/Goreng_pisang.jpg?width=640', NULL, 10, 10, 8000, 12000, 2, 'published', '2026-10-29T22:20:13.659107+07:00', '2026-10-29T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (9, 4, 'Rendang Sapi', 'Daging sapi dimasak perlahan dalam santan dan rempah hingga kering dan bumbunya meresap.', 'Padang', 'https://commons.wikimedia.org/wiki/Special:FilePath/Nasi_Rendang.JPG?width=640', NULL, 30, 180, 120000, 180000, 6, 'published', '2026-11-01T22:20:13.659107+07:00', '2026-11-01T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (10, 3, 'Telur Balado', 'Telur rebus goreng yang dibalut sambal balado merah pedas-manis.', 'Minang', 'https://commons.wikimedia.org/wiki/Special:FilePath/Telur_Balado.jpg?width=640', NULL, 10, 15, 12000, 18000, 2, 'published', '2026-11-04T22:20:13.659107+07:00', '2026-11-04T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (11, 5, 'Sop Ayam', 'Sup bening hangat berisi ayam, wortel, kentang, dan kol.', 'Indonesia', 'https://commons.wikimedia.org/wiki/Special:FilePath/Sup_Ayam_Kampung.jpg?width=640', NULL, 15, 40, 35000, 45000, 4, 'published', '2026-11-07T22:20:13.659107+07:00', '2026-11-07T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (12, 3, 'Perkedel Kentang', 'Kentang goreng yang dihaluskan, dibentuk bulat pipih, dicelup telur, lalu digoreng.', 'Indonesia', 'https://commons.wikimedia.org/wiki/Special:FilePath/Perkedel_kentang_tanpa_daging.JPG?width=640', NULL, 20, 20, 15000, 20000, 4, 'published', '2026-11-10T22:20:13.659107+07:00', '2026-11-10T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (13, 5, 'Tumis Kangkung', 'Kangkung ditumis cepat dengan bawang, cabai rawit, dan tomat. Siap dalam 12 menit.', 'Indonesia', 'https://commons.wikimedia.org/wiki/Special:FilePath/Tumis_kangkung.JPG?width=640', NULL, 5, 7, 8000, 12000, 2, 'published', '2026-11-13T22:20:13.659107+07:00', '2026-11-13T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (14, 3, 'Es Teler', 'Minuman segar berisi alpukat, kelapa muda, dan nangka dengan susu kental manis dan sirup.', 'Jakarta', 'https://commons.wikimedia.org/wiki/Special:FilePath/Es_teler_di_Bandung.jpg?width=640', NULL, 15, 0, 35000, 50000, 4, 'published', '2026-11-16T22:20:13.659107+07:00', '2026-11-16T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (15, 4, 'Gado-Gado', 'Sayuran rebus, tahu, tempe, dan telur yang disiram bumbu kacang kental.', 'Betawi', 'https://commons.wikimedia.org/wiki/Special:FilePath/Gado-gado_in_Jakarta.JPG?width=640', NULL, 20, 20, 20000, 30000, 2, 'published', '2026-11-19T22:20:13.659107+07:00', '2026-11-19T22:20:13.659107+07:00');
INSERT INTO recipes (id, author_id, title, description, origin, image_url, video_url, prep_minutes, cook_minutes, price_min, price_max, servings, status, created_at, updated_at) VALUES (16, 4, 'Babi Kecap', 'Daging babi dimasak kecap manis, jahe, dan arak masak hingga empuk. (Non halal)', 'Tionghoa-Indonesia', NULL, NULL, 15, 60, 70000, 100000, 4, 'published', '2026-11-22T22:20:13.659107+07:00', '2026-11-22T22:20:13.659107+07:00');
SELECT setval(pg_get_serial_sequence('recipes', 'id'), (SELECT MAX(id) FROM recipes));

-- bookmarks (12)
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (3, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (3, 2, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (3, 5, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (3, 9, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (4, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (4, 3, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (4, 4, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (4, 14, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (5, 1, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (5, 7, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (5, 8, '2026-11-25T22:20:13.658016+07:00');
INSERT INTO bookmarks (user_id, recipe_id, created_at) VALUES (5, 13, '2026-11-25T22:20:13.658016+07:00');

-- notifications (2)
INSERT INTO notifications (id, user_id, sender, title, body, link, recipe_ids, promotion_id, created_at) VALUES (1, NULL, 'Dapurnusa', 'Masak apa ya hari ini?', 'Cobain rekomendasi resep di bawah ini. Jangan lupa recook, ya!', NULL, '{1,2,6,10}', 1, '2026-11-25T21:20:13.659107+07:00');
INSERT INTO notifications (id, user_id, sender, title, body, link, recipe_ids, promotion_id, created_at) VALUES (2, 3, 'Recipeat', 'Resepmu disimpan 12 orang', 'Martabak Manis Coklat Keju makin populer minggu ini.', '/resep', '{}', NULL, '2026-11-23T22:20:13.659107+07:00');
SELECT setval(pg_get_serial_sequence('notifications', 'id'), (SELECT MAX(id) FROM notifications));

-- recipe_ingredients (159)
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (1, 1, 48, 300.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (2, 1, 3, 2.0, 'butir', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (3, 1, 26, 3.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (4, 1, 27, 2.0, 'siung', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (5, 1, 28, 1.0, 'buah', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (6, 1, 33, 2.0, 'sdm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (7, 1, 30, 0.5, 'sdt', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (8, 1, 31, 0.5, 'sdt', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (9, 1, 47, 2.0, 'sdm', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (10, 1, 17, NULL, '', 'Secukupnya', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (11, 2, 2, 300.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (12, 2, 51, 200.0, 'gr', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (13, 2, 12, 100.0, 'gr', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (14, 2, 7, 2.0, 'buah', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (15, 2, 15, 2.0, 'batang', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (16, 2, 16, 2.0, 'batang', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (17, 2, 26, 6.0, 'siung', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (18, 2, 27, 4.0, 'siung', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (19, 2, 40, 2.0, 'cm', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (20, 2, 41, 1.0, 'batang', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (21, 2, 42, 2.0, 'lembar', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (22, 2, 30, 1.0, 'sdt', '', 11);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (23, 2, 34, 0.5, 'sdt', '', 12);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (24, 2, 47, 2.0, 'sdm', '', 13);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (25, 2, 54, 1.5, 'liter', '', 14);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (26, 3, 62, 250.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (27, 3, 3, 1.0, 'butir', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (28, 3, 31, 50.0, 'gr', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (29, 3, 54, 300.0, 'ml', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (30, 3, 65, 1.0, 'sdt', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (31, 3, 57, 2.0, 'sdm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (32, 3, 66, 50.0, 'gr', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (33, 3, 56, 50.0, 'gr', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (34, 3, 55, 3.0, 'sdm', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (35, 4, 31, 1.0, 'sdt', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (36, 4, 30, 0.25, 'sdt', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (37, 4, 52, 1.0, 'sdm', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (38, 4, 63, 250.0, 'gr', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (39, 4, 64, 50.0, 'gr', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (40, 4, 32, NULL, '', 'Secukupnya', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (41, 4, 23, NULL, '', 'Secukupnya', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (42, 4, 46, NULL, '', 'Secukupnya', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (43, 5, 14, 1.0, 'buah', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (44, 5, 11, 100.0, 'gr', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (45, 5, 9, 1.0, 'buah', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (46, 5, 18, 50.0, 'gr', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (47, 5, 53, 50.0, 'gr', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (48, 5, 37, 2.0, 'sdm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (49, 5, 32, 1.0, 'sdm', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (50, 5, 26, 5.0, 'siung', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (51, 5, 27, 3.0, 'siung', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (52, 5, 28, 2.0, 'buah', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (53, 5, 36, 1.0, 'sdt', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (54, 5, 38, 2.0, 'cm', '', 11);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (55, 5, 42, 2.0, 'lembar', '', 12);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (56, 5, 30, 1.0, 'sdt', '', 13);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (57, 5, 54, 1.5, 'liter', '', 14);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (58, 6, 1, 1.0, 'ekor', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (59, 6, 38, 150.0, 'gr', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (60, 6, 26, 8.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (61, 6, 27, 5.0, 'siung', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (62, 6, 40, 3.0, 'cm', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (63, 6, 44, 1.0, 'sdt', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (64, 6, 35, 3.0, 'butir', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (65, 6, 41, 2.0, 'batang', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (66, 6, 42, 3.0, 'lembar', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (67, 6, 30, 2.0, 'sdt', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (68, 6, 54, 500.0, 'ml', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (69, 6, 47, NULL, '', 'Untuk menggoreng', 11);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (70, 7, 49, 1.0, 'papan', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (71, 7, 26, 4.0, 'siung', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (72, 7, 27, 2.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (73, 7, 28, 2.0, 'buah', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (74, 7, 33, 3.0, 'sdm', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (75, 7, 32, 1.0, 'sdm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (76, 7, 30, 0.5, 'sdt', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (77, 7, 47, 3.0, 'sdm', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (78, 8, 19, 4.0, 'buah', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (79, 8, 62, 100.0, 'gr', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (80, 8, 64, 2.0, 'sdm', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (81, 8, 31, 1.0, 'sdm', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (82, 8, 30, 0.25, 'sdt', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (83, 8, 54, 120.0, 'ml', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (84, 8, 47, NULL, '', 'Untuk menggoreng', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (85, 9, 2, 1.0, 'kg', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (86, 9, 52, 1.0, 'liter', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (87, 9, 28, 15.0, 'buah', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (88, 9, 26, 12.0, 'siung', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (89, 9, 27, 6.0, 'siung', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (90, 9, 39, 3.0, 'cm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (91, 9, 38, 3.0, 'cm', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (92, 9, 40, 2.0, 'cm', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (93, 9, 41, 2.0, 'batang', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (94, 9, 43, 5.0, 'lembar', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (95, 9, 42, 3.0, 'lembar', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (96, 9, 23, 100.0, 'gr', 'Disangrai', 11);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (97, 9, 30, 2.0, 'sdt', '', 12);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (98, 10, 3, 4.0, 'butir', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (99, 10, 28, 6.0, 'buah', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (100, 10, 26, 5.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (101, 10, 27, 2.0, 'siung', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (102, 10, 7, 1.0, 'buah', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (103, 10, 31, 1.0, 'sdt', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (104, 10, 30, 0.5, 'sdt', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (105, 10, 47, 4.0, 'sdm', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (106, 11, 1, 500.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (107, 11, 5, 2.0, 'buah', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (108, 11, 6, 2.0, 'buah', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (109, 11, 12, 100.0, 'gr', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (110, 11, 27, 4.0, 'siung', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (111, 11, 4, 0.5, 'buah', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (112, 11, 15, 1.0, 'batang', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (113, 11, 16, 1.0, 'batang', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (114, 11, 34, 0.5, 'sdt', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (115, 11, 30, 1.5, 'sdt', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (116, 11, 54, 1.5, 'liter', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (117, 12, 6, 500.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (118, 12, 3, 1.0, 'butir', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (119, 12, 26, 4.0, 'siung', 'Goreng', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (120, 12, 16, 1.0, 'batang', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (121, 12, 34, 0.25, 'sdt', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (122, 12, 30, 1.0, 'sdt', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (123, 12, 47, NULL, '', 'Untuk menggoreng', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (124, 13, 10, 2.0, 'ikat', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (125, 13, 26, 4.0, 'siung', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (126, 13, 27, 3.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (127, 13, 29, 5.0, 'buah', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (128, 13, 7, 1.0, 'buah', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (129, 13, 30, 0.5, 'sdt', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (130, 13, 31, 0.5, 'sdt', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (131, 13, 47, 2.0, 'sdm', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (132, 14, 20, 2.0, 'buah', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (133, 14, 22, 1.0, 'buah', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (134, 14, 21, 100.0, 'gr', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (135, 14, 55, 4.0, 'sdm', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (136, 14, 60, 4.0, 'sdm', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (137, 14, 61, NULL, '', 'Secukupnya', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (138, 15, 12, 100.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (139, 15, 13, 100.0, 'gr', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (140, 15, 11, 100.0, 'gr', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (141, 15, 6, 1.0, 'buah', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (142, 15, 50, 2.0, 'potong', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (143, 15, 49, 0.5, 'papan', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (144, 15, 3, 2.0, 'butir', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (145, 15, 17, 1.0, 'buah', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (146, 15, 53, 150.0, 'gr', '', 8);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (147, 15, 32, 2.0, 'sdm', '', 9);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (148, 15, 29, 3.0, 'buah', '', 10);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (149, 15, 30, 0.5, 'sdt', '', 11);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (150, 15, 54, 200.0, 'ml', '', 12);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (151, 16, 67, 500.0, 'gr', '', 0);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (152, 16, 33, 5.0, 'sdm', '', 1);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (153, 16, 27, 6.0, 'siung', '', 2);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (154, 16, 39, 3.0, 'cm', '', 3);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (155, 16, 68, 2.0, 'sdm', '', 4);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (156, 16, 31, 1.0, 'sdm', '', 5);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (157, 16, 30, 0.5, 'sdt', '', 6);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (158, 16, 34, 0.5, 'sdt', '', 7);
INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, quantity, unit, note, position) VALUES (159, 16, 54, 400.0, 'ml', '', 8);
SELECT setval(pg_get_serial_sequence('recipe_ingredients', 'id'), (SELECT MAX(id) FROM recipe_ingredients));

-- recipe_steps (59)
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (1, 1, 1, 'Tumis Bumbu', 'Panaskan minyak dalam wajan, tumis bawang merah, bawang putih, dan cabai hingga harum.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (2, 1, 2, 'Masak Telur', 'Masukkan telur, orak-arik hingga matang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (3, 1, 3, 'Tambahkan Nasi', 'Tambahkan nasi putih dan kecap manis, aduk rata.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (4, 1, 4, 'Bumbui', 'Masukkan garam dan gula, aduk kembali hingga semua bahan tercampur merata dan nasi terasa hangat.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (5, 1, 5, 'Sajikan', 'Sajikan hangat dengan irisan timun.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (6, 2, 1, 'Rebus Daging', 'Rebus daging sapi dalam air hingga empuk, lalu potong dadu. Simpan kaldunya.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (7, 2, 2, 'Haluskan Bumbu', 'Haluskan bawang merah, bawang putih, dan kunyit, lalu tumis bersama serai dan daun salam hingga harum.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (8, 2, 3, 'Masak Kuah', 'Masukkan bumbu tumis ke kaldu, bumbui garam dan merica, didihkan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (9, 2, 4, 'Siapkan Isian', 'Seduh mie kuning dan kol sebentar, tata dalam mangkuk bersama tomat dan daging.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (10, 2, 5, 'Sajikan', 'Siram dengan kuah panas, taburi daun bawang dan seledri.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (11, 3, 1, 'Buat Adonan', 'Campur tepung, gula, telur, ragi, dan air. Aduk hingga licin, diamkan 1 jam.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (12, 3, 2, 'Panggang', 'Tuang adonan ke wajan tebal panas, tunggu hingga bersarang lalu taburi sedikit gula dan tutup.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (13, 3, 3, 'Beri Topping', 'Angkat, olesi mentega, taburi cokelat meses, keju, dan susu kental manis.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (14, 3, 4, 'Sajikan', 'Lipat dua, potong-potong, dan sajikan hangat.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (15, 4, 1, 'Buat Adonan', 'Campur tepung ketan, tepung beras, gula, garam, santan, dan perasa pandan. Uleni hingga kalis.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (16, 4, 2, 'Isi Gula Merah', 'Ambil sedikit adonan, pipihkan, isi dengan gula merah, lalu bulatkan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (17, 4, 3, 'Rebus', 'Rebus klepon dalam air mendidih hingga mengapung, angkat dan tiriskan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (18, 4, 4, 'Gulingkan', 'Gulingkan klepon di atas kelapa parut yang sudah dikukus dengan sedikit garam.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (19, 5, 1, 'Haluskan Bumbu', 'Haluskan bawang merah, bawang putih, cabai, dan terasi.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (20, 5, 2, 'Didihkan Kuah', 'Rebus air bersama bumbu halus, lengkuas, dan daun salam.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (21, 5, 3, 'Masukkan Sayur', 'Masukkan jagung, kacang tanah, dan melinjo, lalu labu siam dan kacang panjang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (22, 5, 4, 'Bumbui', 'Tambahkan asam jawa, gula merah, dan garam. Masak hingga sayur matang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (23, 6, 1, 'Haluskan Bumbu', 'Haluskan bawang, kunyit, ketumbar, dan kemiri. Parut lengkuas.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (24, 6, 2, 'Ungkep Ayam', 'Rebus ayam bersama bumbu, lengkuas, serai, daun salam, garam, dan air hingga meresap.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (25, 6, 3, 'Goreng', 'Goreng ayam hingga kecokelatan, lalu goreng sisa ampas lengkuas hingga kering.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (26, 6, 4, 'Sajikan', 'Taburkan serundeng lengkuas di atas ayam.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (27, 7, 1, 'Goreng Tempe', 'Potong tempe korek api, goreng hingga kering.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (28, 7, 2, 'Tumis Bumbu', 'Tumis irisan bawang dan cabai hingga harum.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (29, 7, 3, 'Campur', 'Masukkan tempe, kecap manis, gula merah, dan garam. Aduk hingga karamel melapisi tempe.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (30, 8, 1, 'Buat Adonan', 'Campur tepung terigu, tepung beras, gula, garam, dan air hingga kental.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (31, 8, 2, 'Celup Pisang', 'Belah pisang, celupkan ke adonan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (32, 8, 3, 'Goreng', 'Goreng dalam minyak panas hingga keemasan, tiriskan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (33, 9, 1, 'Haluskan Bumbu', 'Haluskan cabai, bawang, jahe, lengkuas, dan kunyit.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (34, 9, 2, 'Masak Santan', 'Rebus santan bersama bumbu halus, serai, daun jeruk, dan daun salam sambil diaduk.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (35, 9, 3, 'Masukkan Daging', 'Masukkan daging dan kelapa sangrai, masak dengan api kecil.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (36, 9, 4, 'Masak Hingga Kering', 'Aduk sesekali selama ±3 jam hingga kuah mengering dan berminyak.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (37, 10, 1, 'Rebus Telur', 'Rebus telur 10 menit, kupas, lalu goreng sebentar hingga kulitnya berkerut.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (38, 10, 2, 'Buat Balado', 'Ulek kasar cabai, bawang, dan tomat, lalu tumis hingga matang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (39, 10, 3, 'Campur', 'Bumbui gula dan garam, masukkan telur, aduk hingga terbalut sambal.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (40, 11, 1, 'Rebus Ayam', 'Rebus ayam hingga mendidih, buang busanya.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (41, 11, 2, 'Tumis Aromatik', 'Tumis bawang putih dan bombay, masukkan ke kaldu.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (42, 11, 3, 'Masukkan Sayur', 'Masukkan wortel dan kentang, lalu kol menjelang matang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (43, 11, 4, 'Bumbui', 'Bumbui garam dan merica, taburi daun bawang dan seledri.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (44, 12, 1, 'Goreng Kentang', 'Potong kentang, goreng hingga matang lalu haluskan selagi panas.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (45, 12, 2, 'Bumbui', 'Campur dengan bawang goreng, seledri, merica, dan garam. Bentuk bulat pipih.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (46, 12, 3, 'Goreng', 'Celupkan ke kocokan telur, goreng hingga kecokelatan.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (47, 13, 1, 'Siapkan', 'Petik kangkung, cuci bersih. Iris bawang, cabai, dan tomat.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (48, 13, 2, 'Tumis', 'Tumis bawang dan cabai hingga harum, masukkan tomat.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (49, 13, 3, 'Masak Kangkung', 'Masukkan kangkung, bumbui garam dan gula, masak dengan api besar 2 menit.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (50, 14, 1, 'Potong Buah', 'Keruk alpukat dan kelapa muda, potong nangka.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (51, 14, 2, 'Tata', 'Tata buah dalam gelas, tambahkan es batu.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (52, 14, 3, 'Siram', 'Siram dengan sirup dan susu kental manis, sajikan segera.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (53, 15, 1, 'Rebus Sayur', 'Rebus kol, tauge, kacang panjang, dan kentang. Rebus telur.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (54, 15, 2, 'Goreng', 'Goreng tahu dan tempe.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (55, 15, 3, 'Bumbu Kacang', 'Haluskan kacang goreng, gula merah, cabai, dan garam, encerkan dengan air.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (56, 15, 4, 'Sajikan', 'Tata semua bahan dan siram bumbu kacang.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (57, 16, 1, 'Tumis', 'Tumis bawang putih dan jahe hingga harum.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (58, 16, 2, 'Masak Daging', 'Masukkan daging, aduk hingga berubah warna, tambahkan kecap, angciu, gula, garam, dan merica.', NULL);
INSERT INTO recipe_steps (id, recipe_id, position, title, body, media_url) VALUES (59, 16, 3, 'Ungkep', 'Tuang air, masak dengan api kecil hingga daging empuk dan kuah mengental.', NULL);
SELECT setval(pg_get_serial_sequence('recipe_steps', 'id'), (SELECT MAX(id) FROM recipe_steps));

-- recipe_tags (76)
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 10);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (1, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (2, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (3, 3);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (3, 4);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (3, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (3, 13);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (4, 3);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (4, 4);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (4, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (4, 13);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (5, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (5, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (5, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (5, 8);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (5, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (6, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (7, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (7, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (7, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (7, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (8, 3);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (8, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (8, 13);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (9, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (9, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (9, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (9, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (9, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (10, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (10, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (10, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (10, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (10, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (11, 12);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (12, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (12, 3);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (12, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (12, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (12, 13);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (13, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (13, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (13, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (13, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (14, 4);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (14, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (14, 13);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (15, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (15, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (15, 7);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (15, 9);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (15, 11);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (16, 1);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (16, 2);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (16, 5);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (16, 6);
INSERT INTO recipe_tags (recipe_id, tag_id) VALUES (16, 12);

-- reviews (32)
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (1, 1, 3, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (2, 1, 4, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (3, 2, 3, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (4, 2, 5, 3, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (5, 3, 4, 5, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (6, 3, 5, 5, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (7, 4, 3, 5, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (8, 4, 4, 5, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (9, 5, 3, 5, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (10, 5, 5, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (11, 6, 4, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (12, 6, 5, 5, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (13, 7, 3, 3, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (14, 7, 4, 5, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (15, 8, 3, 5, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (16, 8, 5, 5, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (17, 9, 4, 3, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (18, 9, 5, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (19, 10, 3, 5, 'Langkahnya jelas, terima kasih resepnya.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (20, 10, 4, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (21, 11, 3, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (22, 11, 5, 3, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (23, 12, 4, 5, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (24, 12, 5, 5, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (25, 13, 3, 5, 'Sudah recook dua kali, mantap.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (26, 13, 4, 5, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (27, 14, 3, 5, 'Kurang garam sedikit, sisanya oke.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (28, 14, 5, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (29, 15, 4, 5, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (30, 15, 5, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (31, 16, 3, 3, 'Enak banget, keluarga suka!', '2026-11-25T22:20:13.658016+07:00');
INSERT INTO reviews (id, recipe_id, user_id, rating, comment, created_at) VALUES (32, 16, 4, 5, 'Bumbunya pas, gampang diikuti.', '2026-11-25T22:20:13.658016+07:00');
SELECT setval(pg_get_serial_sequence('reviews', 'id'), (SELECT MAX(id) FROM reviews));

-- user_allergies (1)
INSERT INTO user_allergies (user_id, ingredient_id) VALUES (3, 25);
COMMIT;
