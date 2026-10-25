"""Programmlogik des Getränkeautomaten. Alle Beträge sind int in Cent."""

from dataclasses import dataclass
from enum import Enum

from datenbank import Datenbank, Getraenk

TECHNIKER_PIN = "1234"


def pin_pruefen(eingabe: str) -> bool:
    """True, wenn die Eingabe der Techniker-PIN entspricht."""
    return eingabe == TECHNIKER_PIN


def format_euro(cent: int) -> str:
    """230 wird zu '2,30 €'."""
    vorzeichen = "-" if cent < 0 else ""
    cent = abs(cent)
    return f"{vorzeichen}{cent // 100},{cent % 100:02d} €"


def parse_euro(text: str) -> int:
    """'2,30' wird zu 230. Nur über Text, ValueError bei ungültiger Eingabe."""
    text = text.strip()
    if text.endswith("€"):
        text = text[:-1].strip()
    euro, komma, nachkomma = text.partition(",")
    if not (euro.isascii() and euro.isdigit()):
        raise ValueError(f"Ungültiger Betrag: {text!r}")
    if komma:
        if not (nachkomma.isascii() and nachkomma.isdigit()) or len(nachkomma) > 2:
            raise ValueError(f"Ungültiger Betrag: {text!r}")
        nachkomma = nachkomma.ljust(2, "0")
    else:
        nachkomma = "00"
    return int(euro) * 100 + int(nachkomma)


def berechne_rueckgeld(betrag: int, bestand: dict[int, int]) -> dict[int, int] | None:
    """Stellt betrag mit möglichst wenigen Münzen aus bestand zusammen, sonst None."""
    if betrag < 0:
        raise ValueError("Negativer Betrag")
    if betrag == 0:
        return {}
    # beste[b] = (Anzahl Münzen, Verwendung je Münzwert) für Betrag b, None wenn unmöglich
    beste: list[tuple[int, dict[int, int]] | None] = [None] * (betrag + 1)
    beste[0] = (0, {})
    for wert, anzahl in sorted(bestand.items()):
        if wert <= 0 or anzahl <= 0:
            continue
        neu = list(beste)
        for b in range(betrag + 1):
            if beste[b] is None:
                continue
            muenzen, verwendet = beste[b]
            for k in range(1, anzahl + 1):
                ziel = b + k * wert
                if ziel > betrag:
                    break
                if neu[ziel] is None or neu[ziel][0] > muenzen + k:
                    neu[ziel] = (muenzen + k, {**verwendet, wert: k})
        beste = neu
    if beste[betrag] is None:
        return None
    return beste[betrag][1]


class Zustand(Enum):
    """Zustände des Automaten."""

    BEREIT = "bereit"
    GEWAEHLT = "gewaehlt"
    AUSGABE = "ausgabe"


@dataclass
class Kaufergebnis:
    """Ergebnis eines Kaufs oder Abbruchs; geld liegt im Ausgabefach."""

    verkauft: bool
    getraenk: Getraenk | None
    geld: dict[int, int]
    meldung: str


class Automat:
    """Ablaufsteuerung eines Kaufs."""

    def __init__(self, db: Datenbank):
        self._db = db
        self.zustand = Zustand.BEREIT
        self.gewaehlt: Getraenk | None = None
        self.zwischenspeicher: dict[int, int] = {}

    def getraenke(self) -> list[Getraenk]:
        """Alle Getränke aus der Datenbank."""
        return self._db.getraenke()

    def waehlen(self, fach: int):
        """Wählt das Getränk im Fach. Nur im Zustand BEREIT."""
        if self.zustand != Zustand.BEREIT:
            raise ValueError("Auswahl jetzt nicht möglich")
        for g in self._db.getraenke():
            if g.fach == fach:
                if g.ausverkauft():
                    raise ValueError(f"Fach {fach} ist ausverkauft")
                self.gewaehlt = g
                self.zustand = Zustand.GEWAEHLT
                return
        raise ValueError(f"Unbekanntes Fach {fach}")

    def einwerfen(self, wert: int) -> Kaufergebnis | None:
        """Wirft Geld ein. Liefert das Ergebnis, sobald der Betrag reicht, sonst None."""
        if self.zustand != Zustand.GEWAEHLT:
            raise ValueError("Einwurf jetzt nicht möglich")
        if wert not in {w for w, _ in self._db.geldsorten()}:
            raise ValueError(f"Geldsorte {wert} wird nicht angenommen")
        self.zwischenspeicher[wert] = self.zwischenspeicher.get(wert, 0) + 1
        if self.eingeworfen() < self.gewaehlt.preis_cent:
            return None
        rueckgeld = berechne_rueckgeld(
            self.eingeworfen() - self.gewaehlt.preis_cent, self._db.wechselgeld())
        if rueckgeld is None:
            ergebnis = Kaufergebnis(False, self.gewaehlt, dict(self.zwischenspeicher),
                                    "Kein passendes Wechselgeld. Bitte passend zahlen.")
        else:
            try:
                self._db.kauf_buchen(self.gewaehlt, dict(self.zwischenspeicher), rueckgeld)
            except RuntimeError:
                ergebnis = Kaufergebnis(False, self.gewaehlt, dict(self.zwischenspeicher),
                                        "Kauf nicht möglich. Bitte Geld entnehmen.")
            else:
                ergebnis = Kaufergebnis(True, self.gewaehlt, rueckgeld,
                                        "Vielen Dank! Bitte Getränk und Rückgeld entnehmen.")
        self.zustand = Zustand.AUSGABE
        return ergebnis

    def abbrechen(self) -> Kaufergebnis:
        """Bricht den Kauf ab. Nur im Zustand GEWAEHLT, die Datenbank bleibt unverändert."""
        if self.zustand != Zustand.GEWAEHLT:
            raise ValueError("Abbruch jetzt nicht möglich")
        if not self.zwischenspeicher:
            self.zustand = Zustand.BEREIT
            self.gewaehlt = None
            return Kaufergebnis(False, None, {}, "Abgebrochen.")
        self.zustand = Zustand.AUSGABE
        return Kaufergebnis(False, self.gewaehlt, dict(self.zwischenspeicher),
                            "Abgebrochen. Bitte Geld entnehmen.")

    def entnehmen(self):
        """Leert das Ausgabefach und setzt den Automaten zurück."""
        if self.zustand != Zustand.AUSGABE:
            raise ValueError("Nichts zu entnehmen")
        self.gewaehlt = None
        self.zwischenspeicher = {}
        self.zustand = Zustand.BEREIT

    def eingeworfen(self) -> int:
        """Summe des eingeworfenen Geldes."""
        return sum(w * a for w, a in self.zwischenspeicher.items())

    def restbetrag(self) -> int:
        """Noch zu zahlender Betrag, nie negativ."""
        if self.gewaehlt is None:
            return 0
        return max(0, self.gewaehlt.preis_cent - self.eingeworfen())
