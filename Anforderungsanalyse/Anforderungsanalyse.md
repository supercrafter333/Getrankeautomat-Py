# Anforderungsanalyse: Steuerungssoftware Getränkeautomat

**Projekt:** Getränkeautomat
**Datum:** 18.08.2026

---

## 1. Ausgangslage und Zielsetzung

Für einen Getränkeautomaten soll eine vollständige Steuerungssoftware inklusive Datenhaltung entwickelt werden. Die Bedienung erfolgt über einen Touchscreen am Automaten. Die Umsetzung erfolgt in **Python** mit **tkinter** als GUI-Framework und einer relationalen Datenbank zur Datenhaltung.

---

## 2. Funktionale Anforderungen

### 2.1 Kaufprozess
- Steuerung ausschließlich über Touchscreen-Oberfläche.
- Auswahl und Kauf **eines einzelnen Getränks** pro Vorgang.
- Kein Warenkorb, keine Mehrfachauswahl in einer Transaktion.
- Anzeige verfügbarer Getränke inkl. Preis und Verfügbarkeit (Bestand).
- Rückmeldung bei nicht ausreichendem Bestand oder fehlendem Wechselgeld.

### 2.2 Geldverwaltung
- Erfassung eingezahlten Geldes (Münzen/Scheine, je nach Hardware-Anbindung).
- **Strikte Trennung** von eingezahltem Geld und Wechselgeldbestand (physisch/logisch getrennte Kassen).
- Automatische Berechnung und Ausgabe von Wechselgeld beim Kauf.
- Verhinderung von Käufen, wenn das benötigte Wechselgeld nicht vorrätig ist.

### 2.3 Statistik
- Protokollierung aller Verkäufe (Getränk, Zeitpunkt, Preis).
- Auswertungsmöglichkeit über verkaufte Getränke (z. B. Menge pro Getränk, Zeitraum, Umsatz).

### 2.4 Datenexport / -import
- Export der Daten als **CSV**-Datei.
- Export der Daten als **JSON**-Datei.
- Import von Daten aus CSV- und JSON-Dateien (z. B. zur Wiederherstellung oder Datenübernahme).

### 2.5 Wartung / Technikerfunktionen
- Auffüllen des Getränkebestands durch Techniker.
- Auffüllen bzw. Zurücksetzen des Wechselgeldbestands durch Techniker.
- Zugriff auf Wartungsfunktionen vermutlich über einen geschützten Bereich (z. B. Techniker-Login/PIN) – **zu klären**.

---

## 3. Nicht-funktionale Anforderungen

- **Bedienbarkeit:** Einfache, intuitive Touchscreen-Oberfläche für Endkunden.
- **Zuverlässigkeit:** Keine Datenverluste bei Stromausfall/Absturz während einer Transaktion.
- **Sicherheit:** Physische/logische Trennung von Einzahlungs- und Wechselgeldbeständen zur Vermeidung von Manipulation oder Fehlbeständen.
- **Wartbarkeit:** Klare Trennung von GUI, Geschäftslogik und Datenhaltung (z. B. MVC-ähnliche Architektur).
- **Portabilität der Daten:** Austauschformate CSV/JSON für einfache externe Weiterverarbeitung.

---

## 4. Technische Anforderungen

| Bereich | Vorgabe |
|---|---|
| Programmiersprache | Python |
| GUI-Framework | tkinter |
| Datenhaltung | Relationale Datenbank (z. B. SQLite als lokale Lösung naheliegend – **zu klären**) |
| Export-Formate | CSV, JSON |
| Import-Formate | CSV, JSON |
| Eingabegerät | Touchscreen |

---

## 5. Vorläufiges Datenmodell (Vorschlag)

- **Getränk**: ID, Name, Preis, Bestand, max. Kapazität, Fach-/Slotnummer
- **Verkauf**: ID, Getränk-ID, Zeitstempel, Preis, gezahlter Betrag, Wechselgeld
- **Kasse_Einzahlung**: Münz-/Scheinwert, Anzahl
- **Kasse_Wechselgeld**: Münz-/Scheinwert, Anzahl, max. Kapazität
- **Techniker-Aktion** (optional): ID, Zeitstempel, Aktion (Auffüllen Getränk/Wechselgeld), Benutzer

---

## 6. Offene Fragen / Klärungsbedarf

1. Welche Hardware-Schnittstelle steuert Münz-/Scheinannahme und -ausgabe (z. B. MDB-Protokoll)? Muss die Software direkt mit Hardware kommunizieren?
2. Welche relationale Datenbank ist gewünscht bzw. vorgegeben (SQLite, MySQL, PostgreSQL)?
3. Muss der Techniker-Zugang zur Wartung (Bestand/Wechselgeld auffüllen) durch Login/PIN abgesichert werden?
4. Ist eine Netzwerkanbindung (z. B. Fernwartung, zentrale Statistikauswertung mehrerer Automaten) vorgesehen?
5. Sollen Zahlungsarten wie Karte/kontaktlos ergänzend zu Bargeld unterstützt werden, oder ist der Automat reiner Bargeldautomat?
6. Welche maximale Anzahl an Getränkesorten/-fächern muss die Software unterstützen?
7. Gibt es Vorgaben zur Aufbewahrungsdauer bzw. Archivierung der Verkaufsstatistik?

---

## 7. Nächste Schritte

- Klärung der offenen Fragen mit dem Kunden.
- Festlegung der konkreten Datenbank-Technologie.
- Erstellung eines detaillierten technischen Konzepts inkl. GUI-Mockups.
- Abstimmung eines Zeit- und Kostenrahmens.
