"""CSV-Import und -Export des Getränkeautomaten. Alle Beträge sind int in Cent."""

import csv
import sqlite3

from datenbank import Datenbank, Getraenk
from logik import format_euro, parse_euro

KODIERUNG = "utf-8-sig"
TRENNZEICHEN = ";"

KOPF_GETRAENKE = ["fach", "name", "preis", "bestand", "kapazitaet", "bild"]
KOPF_WECHSELGELD = ["muenze", "anzahl", "sollbestand"]
KOPF_EINZAHLUNG = ["geldsorte", "anzahl"]
KOPF_VERKAEUFE = ["id", "zeitpunkt", "getraenk", "preis", "bezahlt", "rueckgeld"]


class ImportFehler(Exception):
    """Fehler beim Import mit Zeilennummer (0, wenn keine Zeile betroffen ist)."""

    def __init__(self, zeile: int, grund: str):
        super().__init__(zeile, grund)
        self.zeile = zeile
        self.grund = grund

    def __str__(self) -> str:
        return f"Zeile {self.zeile}: {self.grund}"


def _betrag(cent: int) -> str:
    """230 wird zu '2,30' (ohne Währungszeichen)."""
    return format_euro(cent).removesuffix(" €")


def _schreiben(pfad, kopf: list[str], zeilen):
    with open(pfad, "w", encoding=KODIERUNG, newline="") as datei:
        schreiber = csv.writer(datei, delimiter=TRENNZEICHEN)
        schreiber.writerow(kopf)
        schreiber.writerows(zeilen)


# ---------- Export ----------

def export_getraenke(db: Datenbank, pfad):
    """Schreibt alle Getränke mit Bestand."""
    _schreiben(pfad, KOPF_GETRAENKE, (
        [g.fach, g.name, _betrag(g.preis_cent), g.bestand, g.kapazitaet, g.bild or ""]
        for g in db.getraenke()
    ))


def export_wechselgeld(db: Datenbank, pfad):
    """Schreibt die Wechselgeldkasse."""
    _schreiben(pfad, KOPF_WECHSELGELD, (
        [_betrag(wert), anzahl, soll] for wert, anzahl, soll in db.wechselgeld_tabelle()
    ))


def export_einzahlung(db: Datenbank, pfad):
    """Schreibt die Einzahlungskasse für alle Geldsorten."""
    bestand = db.einzahlung()
    _schreiben(pfad, KOPF_EINZAHLUNG, (
        [_betrag(wert), bestand.get(wert, 0)] for wert, _ in db.geldsorten()
    ))


def export_verkaeufe(db: Datenbank, pfad):
    """Schreibt alle Verkäufe."""
    _schreiben(pfad, KOPF_VERKAEUFE, (
        [vid, zeit, name, _betrag(preis), _betrag(bezahlt), _betrag(rueckgeld)]
        for vid, zeit, name, preis, bezahlt, rueckgeld in db.verkaeufe()
    ))


# ---------- Import ----------

def _lesen(pfad, kopf: list[str]) -> list[tuple[int, list[str]]]:
    """Liest die Datei und prüft Kopfzeile und Spaltenzahl. Liefert (Zeilennummer, Zellen)."""
    try:
        with open(pfad, "r", encoding=KODIERUNG, newline="") as datei:
            zeilen = list(enumerate(csv.reader(datei, delimiter=TRENNZEICHEN), start=1))
    except UnicodeDecodeError:
        raise ImportFehler(0, "Datei ist nicht UTF-8-kodiert") from None
    except csv.Error as fehler:
        raise ImportFehler(0, f"Datei ist keine gültige CSV-Datei: {fehler}") from None
    except OSError as fehler:
        raise ImportFehler(0, f"Datei nicht lesbar: {fehler.strerror or fehler}") from None
    if not zeilen:
        raise ImportFehler(1, "Kopfzeile fehlt")
    if zeilen[0][1] != kopf:
        raise ImportFehler(1, f"Kopfzeile muss {TRENNZEICHEN.join(kopf)} lauten")
    daten = []
    for nummer, zellen in zeilen[1:]:
        if not zellen or (len(zellen) == 1 and not zellen[0].strip()):
            continue
        if len(zellen) != len(kopf):
            raise ImportFehler(
                nummer, f"{len(kopf)} Spalten erwartet, {len(zellen)} gefunden")
        daten.append((nummer, zellen))
    return daten


def _ganzzahl(zeile: int, spalte: str, text: str) -> int:
    text = text.strip()
    if not (text.isascii() and text.isdigit()):
        raise ImportFehler(zeile, f"{spalte}: ganze Zahl ohne Vorzeichen erwartet")
    return int(text)


def _cent(zeile: int, spalte: str, text: str) -> int:
    try:
        return parse_euro(text)
    except ValueError:
        raise ImportFehler(zeile, f"{spalte}: ungültiger Betrag {text.strip()!r}") from None


def _uebernehmen(aktion):
    try:
        aktion()
    except (ValueError, sqlite3.Error) as fehler:
        raise ImportFehler(0, f"Datenbank hat den Import abgelehnt: {fehler}") from None


def import_getraenke(db: Datenbank, pfad):
    """Gleicht die Getränke über die Fachnummer ab. Bei einem Fehler bleibt alles unverändert."""
    liste = []
    faecher = set()
    for nummer, (fach, name, preis, bestand, kapazitaet, bild) in _lesen(pfad, KOPF_GETRAENKE):
        fach = _ganzzahl(nummer, "fach", fach)
        if fach <= 0:
            raise ImportFehler(nummer, "fach: muss größer als 0 sein")
        if fach in faecher:
            raise ImportFehler(nummer, f"fach {fach} kommt in der Datei doppelt vor")
        faecher.add(fach)
        name = name.strip()
        if not name:
            raise ImportFehler(nummer, "name: darf nicht leer sein")
        preis = _cent(nummer, "preis", preis)
        if preis <= 0 or preis % 10 != 0:
            raise ImportFehler(nummer, "preis: muss größer als 0 und ein Vielfaches von 0,10 sein")
        bestand = _ganzzahl(nummer, "bestand", bestand)
        kapazitaet = _ganzzahl(nummer, "kapazitaet", kapazitaet)
        if kapazitaet <= 0:
            raise ImportFehler(nummer, "kapazitaet: muss größer als 0 sein")
        if bestand > kapazitaet:
            raise ImportFehler(nummer, "bestand: darf die Kapazität nicht überschreiten")
        liste.append(Getraenk(None, fach, name, preis, bestand, kapazitaet, bild.strip() or None))
    _uebernehmen(lambda: db.getraenke_importieren(liste))


def import_wechselgeld(db: Datenbank, pfad):
    """Ersetzt die Wechselgeldkasse. Bei einem Fehler bleibt alles unverändert."""
    muenzen = {wert for wert, art in db.geldsorten() if art == "Muenze"}
    zeilen = []
    gesehen = set()
    for nummer, (muenze, anzahl, soll) in _lesen(pfad, KOPF_WECHSELGELD):
        wert = _cent(nummer, "muenze", muenze)
        if wert not in muenzen:
            raise ImportFehler(nummer, f"muenze: {muenze.strip()} ist keine Münze")
        if wert in gesehen:
            raise ImportFehler(nummer, f"muenze {muenze.strip()} kommt in der Datei doppelt vor")
        gesehen.add(wert)
        zeilen.append((wert, _ganzzahl(nummer, "anzahl", anzahl),
                       _ganzzahl(nummer, "sollbestand", soll)))
    _uebernehmen(lambda: db.wechselgeld_setzen(zeilen))


def import_einzahlung(db: Datenbank, pfad):
    """Ersetzt die Einzahlungskasse. Bei einem Fehler bleibt alles unverändert."""
    geldwerte = {wert for wert, _ in db.geldsorten()}
    bestand = {}
    for nummer, (sorte, anzahl) in _lesen(pfad, KOPF_EINZAHLUNG):
        wert = _cent(nummer, "geldsorte", sorte)
        if wert not in geldwerte:
            raise ImportFehler(nummer, f"geldsorte: {sorte.strip()} ist unbekannt")
        if wert in bestand:
            raise ImportFehler(nummer, f"geldsorte {sorte.strip()} kommt in der Datei doppelt vor")
        bestand[wert] = _ganzzahl(nummer, "anzahl", anzahl)
    _uebernehmen(lambda: db.einzahlung_setzen(bestand))
