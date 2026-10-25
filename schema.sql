CREATE TABLE IF NOT EXISTS geldsorte (
    wert_cent INTEGER PRIMARY KEY,
    art TEXT NOT NULL CHECK (art IN ('Muenze', 'Schein'))
);

CREATE TABLE IF NOT EXISTS getraenk (
    id INTEGER PRIMARY KEY,
    fach INTEGER NOT NULL UNIQUE CHECK (fach > 0),
    name TEXT NOT NULL,
    preis_cent INTEGER NOT NULL CHECK (preis_cent > 0 AND preis_cent % 10 = 0),
    bestand INTEGER NOT NULL,
    kapazitaet INTEGER NOT NULL CHECK (kapazitaet > 0),
    bild TEXT,
    CHECK (bestand >= 0 AND bestand <= kapazitaet)
);

CREATE TABLE IF NOT EXISTS kasse_einzahlung (
    wert_cent INTEGER PRIMARY KEY REFERENCES geldsorte (wert_cent),
    anzahl INTEGER NOT NULL CHECK (anzahl >= 0)
);

CREATE TABLE IF NOT EXISTS kasse_wechselgeld (
    wert_cent INTEGER PRIMARY KEY REFERENCES geldsorte (wert_cent),
    anzahl INTEGER NOT NULL CHECK (anzahl >= 0),
    sollbestand INTEGER NOT NULL CHECK (sollbestand >= 0)
);

CREATE TABLE IF NOT EXISTS verkauf (
    id INTEGER PRIMARY KEY,
    getraenk_id INTEGER NOT NULL REFERENCES getraenk (id),
    zeitpunkt TEXT NOT NULL,
    preis_cent INTEGER NOT NULL,
    bezahlt_cent INTEGER NOT NULL,
    rueckgeld_cent INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS verkauf_geld (
    verkauf_id INTEGER NOT NULL REFERENCES verkauf (id),
    wert_cent INTEGER NOT NULL REFERENCES geldsorte (wert_cent),
    richtung TEXT NOT NULL CHECK (richtung IN ('EIN', 'AUS')),
    anzahl INTEGER NOT NULL CHECK (anzahl > 0),
    PRIMARY KEY (verkauf_id, wert_cent, richtung)
);
