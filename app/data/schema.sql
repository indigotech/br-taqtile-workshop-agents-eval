-- Valores monetários em reais (REAL). Pra um planejador de rolê a precisão de
-- ponto flutuante basta, e deixa as tools e os prompts sem conversão de centavos.

CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'Brasil',
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    home_city_id INTEGER NOT NULL REFERENCES cities (id)
);

CREATE TABLE budgets (
    user_id INTEGER PRIMARY KEY REFERENCES users (id),
    total_amount REAL NOT NULL,
    lodging_amount REAL NOT NULL,
    food_amount REAL NOT NULL,
    activities_amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'BRL'
);

CREATE TABLE preferences (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    category TEXT NOT NULL CHECK (category IN ('food', 'activity', 'lodging', 'restriction')),
    value TEXT NOT NULL
);

-- Catálogo mockado de airbnb/hotel: o agente de ação reserva a partir daqui.
CREATE TABLE accommodations (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES cities (id),
    kind TEXT NOT NULL CHECK (kind IN ('airbnb', 'hotel')),
    name TEXT NOT NULL,
    neighborhood TEXT NOT NULL,
    nightly_price REAL NOT NULL,
    max_guests INTEGER NOT NULL,
    rating REAL NOT NULL
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id),
    accommodation_id INTEGER NOT NULL REFERENCES accommodations (id),
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    guests INTEGER NOT NULL,
    total_price REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX preferences_user_id_index ON preferences (user_id);
CREATE INDEX reservations_user_id_index ON reservations (user_id);
CREATE INDEX accommodations_city_id_index ON accommodations (city_id);
