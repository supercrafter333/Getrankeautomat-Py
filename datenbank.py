"""Datenschicht des Getränkeautomaten (SQLite). Alle Beträge sind int in Cent."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

ORDNER = Path(__file__).parent
DB_DATEI = ORDNER / "automat.db"
SCHEMA_DATEI = ORDNER / "schema.sql"
STARTDATEN_DATEI = ORDNER / "startdaten.sql"


@dataclass
class Getraenk:
    """Ein Getränk in einem Fach."""

    id: int | None
    fach: int
    name: str
    preis_cent: int
    bestand: int
    kapazitaet: int
    bild: str | None

    def ausverkauft(self) -> bool:
        """True, wenn kein Getränk mehr im Fach liegt."""
        return self.bestand == 0


class Datenbank:
    """Zugriff auf die SQLite-Datenbank des Automaten."""

    def __init__(self, pfad=DB_DATEI):
        # isolation_level=None: Transaktionen steuern wir selbst mit BEGIN/COMMIT
        self._verbindung = sqlite3.connect(str(pfad), isolation_level=None)
        self._verbindung.execute("PRAGMA foreign_keys = ON")
        vorhanden = self._verbindung.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'geldsorte'"
        ).fetchone()
        if vorhanden is None:
            self._verbindung.executescript(SCHEMA_DATEI.read_text(encoding="utf-8"))
            self._verbindung.executescript(STARTDATEN_DATEI.read_text(encoding="utf-8"))

    def schliessen(self):
        """Schließt die Verbindung."""
        self._verbindung.close()

    def _transaktion(self, aktion):
        """Führt aktion(cursor) in einer Transaktion aus, bei Fehler Rollback."""
        self._verbindung.execute("BEGIN")
        try:
            ergebnis = aktion(self._verbindung)
        except BaseException:
            self._verbindung.execute("ROLLBACK")
            raise
        self._verbindung.execute("COMMIT")
        return ergebnis

    def _muenzen(self) -> set[int]:
        zeilen = self._verbindung.execute(
            "SELECT wert_cent FROM geldsorte WHERE art = 'Muenze'"
        ).fetchall()
        return {z[0] for z in zeilen}

    def _geldwerte(self) -> set[int]:
        zeilen = self._verbindung.execute("SELECT wert_cent FROM geldsorte").fetchall()
        return {z[0] for z in zeilen}

    # ---------- Lesen ----------

    def geldsorten(self) -> list[tuple[int, str]]:
        """(wert_cent, art), aufsteigend."""
        zeilen = self._verbindung.execute(
            "SELECT wert_cent, art FROM geldsorte ORDER BY wert_cent"
        ).fetchall()
        return [(z[0], z[1]) for z in zeilen]

    def getraenke(self) -> list[Getraenk]:
        """Alle Getränke, nach Fach sortiert."""
        zeilen = self._verbindung.execute(
            "SELECT id, fach, name, preis_cent, bestand, kapazitaet, bild "
            "FROM getraenk ORDER BY fach"
        ).fetchall()
        return [Getraenk(*z) for z in zeilen]

    def wechselgeld(self) -> dict[int, int]:
        """Anzahl je Münze in der Wechselgeldkasse."""
        zeilen = self._verbindung.execute(
            "SELECT wert_cent, anzahl FROM kasse_wechselgeld ORDER BY wert_cent"
        ).fetchall()
        return {z[0]: z[1] for z in zeilen}

    def wechselgeld_tabelle(self) -> list[tuple[int, int, int]]:
        """(wert_cent, anzahl, sollbestand) je Münze."""
        zeilen = self._verbindung.execute(
            "SELECT wert_cent, anzahl, sollbestand FROM kasse_wechselgeld ORDER BY wert_cent"
        ).fetchall()
        return [(z[0], z[1], z[2]) for z in zeilen]

    def einzahlung(self) -> dict[int, int]:
        """Anzahl je Geldsorte in der Einzahlungskasse."""
        zeilen = self._verbindung.execute(
            "SELECT wert_cent, anzahl FROM kasse_einzahlung ORDER BY wert_cent"
        ).fetchall()
        return {z[0]: z[1] for z in zeilen}

    def verkaeufe(self) -> list[tuple]:
        """(id, zeitpunkt, getraenkename, preis_cent, bezahlt_cent, rueckgeld_cent)."""
        return self._verbindung.execute(
            "SELECT v.id, v.zeitpunkt, g.name, v.preis_cent, v.bezahlt_cent, v.rueckgeld_cent "
            "FROM verkauf v JOIN getraenk g ON g.id = v.getraenk_id ORDER BY v.id"
        ).fetchall()

    def statistik(self, von: str | None, bis: str | None) -> list[tuple[str, int, int]]:
        """(name, menge, umsatz_cent) je Getränk, Grenzen JJJJ-MM-TT eingeschlossen."""
        zeilen = self._verbindung.execute(
            "SELECT g.name, COUNT(*), SUM(v.preis_cent) "
            "FROM verkauf v JOIN getraenk g ON g.id = v.getraenk_id "
            "WHERE (:von IS NULL OR date(v.zeitpunkt) >= :von) "
            "AND (:bis IS NULL OR date(v.zeitpunkt) <= :bis) "
            "GROUP BY g.id, g.name ORDER BY g.name",
            {"von": von, "bis": bis},
        ).fetchall()
        return [(z[0], z[1], z[2]) for z in zeilen]

    # ---------- Kauf ----------

    def kauf_buchen(self, getraenk: Getraenk, eingeworfen: dict[int, int],
                    rueckgeld: dict[int, int]):
        """Bucht einen Kauf in einer Transaktion, bei jedem Fehler Rollback."""
        bezahlt = sum(w * a for w, a in eingeworfen.items())
        zurueck = sum(w * a for w, a in rueckgeld.items())
        if bezahlt - getraenk.preis_cent != zurueck:
            raise ValueError("Bezahlt minus Preis stimmt nicht mit dem Rückgeld überein")
        if any(a < 0 for a in eingeworfen.values()) or any(a < 0 for a in rueckgeld.values()):
            raise ValueError("Negative Anzahl")

        def buchen(v):
            ergebnis = v.execute(
                "UPDATE getraenk SET bestand = bestand - 1 WHERE id = ? AND bestand > 0",
                (getraenk.id,),
            )
            if ergebnis.rowcount != 1:
                raise RuntimeError("Getränk ausverkauft oder unbekannt")
            for wert, anzahl in eingeworfen.items():
                if anzahl == 0:
                    continue
                ergebnis = v.execute(
                    "UPDATE kasse_einzahlung SET anzahl = anzahl + ? WHERE wert_cent = ?",
                    (anzahl, wert),
                )
                if ergebnis.rowcount != 1:
                    raise ValueError(f"Unbekannte Geldsorte {wert}")
            for wert, anzahl in rueckgeld.items():
                if anzahl == 0:
                    continue
                ergebnis = v.execute(
                    "UPDATE kasse_wechselgeld SET anzahl = anzahl - ? "
                    "WHERE wert_cent = ? AND anzahl >= ?",
                    (anzahl, wert, anzahl),
                )
                if ergebnis.rowcount != 1:
                    raise RuntimeError(f"Nicht genug Wechselgeld für {wert} Cent")
            verkauf_id = v.execute(
                "INSERT INTO verkauf (getraenk_id, zeitpunkt, preis_cent, bezahlt_cent, "
                "rueckgeld_cent) VALUES (?, datetime('now', 'localtime'), ?, ?, ?)",
                (getraenk.id, getraenk.preis_cent, bezahlt, zurueck),
            ).lastrowid
            for richtung, geld in (("EIN", eingeworfen), ("AUS", rueckgeld)):
                for wert, anzahl in geld.items():
                    if anzahl > 0:
                        v.execute(
                            "INSERT INTO verkauf_geld (verkauf_id, wert_cent, richtung, anzahl) "
                            "VALUES (?, ?, ?, ?)",
                            (verkauf_id, wert, richtung, anzahl),
                        )

        self._transaktion(buchen)

    # ---------- Technikerbereich ----------

    def fach_auffuellen(self, fach: int):
        """Setzt den Bestand des Fachs auf die Kapazität."""
        self._transaktion(lambda v: v.execute(
            "UPDATE getraenk SET bestand = kapazitaet WHERE fach = ?", (fach,)))

    def alle_auffuellen(self):
        """Setzt den Bestand aller Fächer auf die Kapazität."""
        self._transaktion(lambda v: v.execute("UPDATE getraenk SET bestand = kapazitaet"))

    def wechselgeld_auffuellen(self):
        """Füllt jede Münze mindestens auf den Sollbestand."""
        self._transaktion(lambda v: v.execute(
            "UPDATE kasse_wechselgeld SET anzahl = MAX(anzahl, sollbestand)"))

    def einnahmen_leeren(self):
        """Setzt die Einzahlungskasse auf 0."""
        self._transaktion(lambda v: v.execute("UPDATE kasse_einzahlung SET anzahl = 0"))

    def getraenke_importieren(self, liste: list[Getraenk]):
        """Gleicht Getränke über die Fachnummer ab: aktualisieren oder anlegen, nichts löschen."""
        def importieren(v):
            for g in liste:
                v.execute(
                    "INSERT INTO getraenk (fach, name, preis_cent, bestand, kapazitaet, bild) "
                    "VALUES (?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT (fach) DO UPDATE SET name = excluded.name, "
                    "preis_cent = excluded.preis_cent, bestand = excluded.bestand, "
                    "kapazitaet = excluded.kapazitaet, bild = excluded.bild",
                    (g.fach, g.name, g.preis_cent, g.bestand, g.kapazitaet, g.bild),
                )

        self._transaktion(importieren)

    def wechselgeld_setzen(self, zeilen: list[tuple[int, int, int]]):
        """Ersetzt den Bestand: übergebene Münzen setzen, die übrigen auf anzahl 0."""
        muenzen = self._muenzen()
        for wert, _, _ in zeilen:
            if wert not in muenzen:
                raise ValueError(f"{wert} Cent ist keine Münze")

        def setzen(v):
            v.execute("UPDATE kasse_wechselgeld SET anzahl = 0")
            for wert, anzahl, soll in zeilen:
                v.execute(
                    "INSERT INTO kasse_wechselgeld (wert_cent, anzahl, sollbestand) "
                    "VALUES (?, ?, ?) ON CONFLICT (wert_cent) DO UPDATE SET "
                    "anzahl = excluded.anzahl, sollbestand = excluded.sollbestand",
                    (wert, anzahl, soll),
                )

        self._transaktion(setzen)

    def einzahlung_setzen(self, bestand: dict[int, int]):
        """Ersetzt den Bestand: übergebene Geldsorten setzen, die übrigen auf 0."""
        geldwerte = self._geldwerte()
        for wert in bestand:
            if wert not in geldwerte:
                raise ValueError(f"Unbekannte Geldsorte {wert}")

        def setzen(v):
            v.execute("UPDATE kasse_einzahlung SET anzahl = 0")
            for wert, anzahl in bestand.items():
                v.execute(
                    "INSERT INTO kasse_einzahlung (wert_cent, anzahl) VALUES (?, ?) "
                    "ON CONFLICT (wert_cent) DO UPDATE SET anzahl = excluded.anzahl",
                    (wert, anzahl),
                )

        self._transaktion(setzen)
