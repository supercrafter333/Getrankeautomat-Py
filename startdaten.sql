INSERT INTO geldsorte (wert_cent, art) VALUES
    (10, 'Muenze'),
    (20, 'Muenze'),
    (50, 'Muenze'),
    (100, 'Muenze'),
    (200, 'Muenze'),
    (500, 'Schein'),
    (1000, 'Schein'),
    (2000, 'Schein');

INSERT INTO kasse_einzahlung (wert_cent, anzahl) VALUES
    (10, 0),
    (20, 0),
    (50, 0),
    (100, 0),
    (200, 0),
    (500, 0),
    (1000, 0),
    (2000, 0);

INSERT INTO kasse_wechselgeld (wert_cent, anzahl, sollbestand) VALUES
    (10, 10000, 10000),
    (20, 10000, 10000),
    (50, 10000, 10000),
    (100, 10000, 10000),
    (200, 10000, 10000);

INSERT INTO getraenk (fach, name, preis_cent, bestand, kapazitaet, bild) VALUES
    (1, 'Wasser', 150, 10, 10, NULL),
    (2, 'Cola', 230, 10, 10, NULL),
    (3, 'Fanta', 230, 10, 10, NULL),
    (4, 'Sprite', 230, 10, 10, NULL),
    (5, 'Eistee', 200, 10, 10, NULL),
    (6, 'Apfelschorle', 200, 10, 10, NULL),
    (7, 'Mate', 250, 10, 10, NULL),
    (8, 'Orangensaft', 250, 0, 10, NULL),
    (9, 'Energy', 280, 10, 10, NULL);
