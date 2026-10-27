# Projektdokumentation: Getränkeautomat

**Projekt:** Simulation eines Getränkeautomaten (Lernfeld 12)
**Team:** _Namen eintragen_
**Stand:** 27.10.2026
**Repository:** https://github.com/supercrafter333/Getrankeautomat-Py

---

## 1. Projektziel

Wir haben einen Getränkeautomaten als Python-Programm simuliert. Auf einer grafischen Oberfläche werden das Display, die Auswahl der Getränke und der Geldeinwurf nachgebildet. Der Kunde wählt ein Getränk, wirft Münzen oder Scheine ein und erhält Getränk und Rückgeld. Das Rückgeld wird nach Münzen aufgeschlüsselt angezeigt.

Beispiel: Eine Cola kostet 2,30 €, der Kunde zahlt mit einem 5-€-Schein. Der Automat gibt 2,70 € zurück, und zwar 1× 2 €, 1× 50 ct und 1× 20 ct.

Alle Daten liegen in einer SQLite-Datenbank: Sortiment, Bestände, Verkäufe und zwei strikt getrennte Kassen. Ein durch eine PIN geschützter Technikerbereich dient zum Auffüllen, Leeren der Kasse, Auswerten und für den CSV-Import und -Export.

---

## 2. Vorgehen

Wir haben zuerst vollständig geplant und erst danach programmiert.

| Phase | Ergebnis | Datei |
|---|---|---|
| Analyse | Anforderungsanalyse, an eine Simulation angepasst | [Anforderungsanalyse.md](../Anforderungsanalyse/Anforderungsanalyse.md) |
| Planung | Projektplan mit allen Entscheidungen und Schnittstellen | [Projektplan.md](../Planung/Projektplan.md) |
| Entwurf | Aktivitätsdiagramm des Kaufprozesses | [Aktivitaetsdiagramm-Kaufprozess.uxf](../Diagramme/Aktivitaetsdiagramm-Kaufprozess.uxf) |
| | Use-Case-Diagramm | [Use-Case-Diagram.uxf](../Diagramme/Use-Case-Diagram.uxf) |
| | ER-Diagramm der Datenbank | [ER-Diagramm-Datenbank.uxf](../Diagramme/ER-Diagramm-Datenbank.uxf) |
| | Mockup der Oberfläche | [Mockup-Oberflaeche.uxf](../Mockups/Mockup-Oberflaeche.uxf) |
| | Klassendiagramm | [Klassendiagramm.uxf](../Diagramme/Klassendiagramm.uxf) |
| Umsetzung | Datenbank, Logik, CSV, Kundenansicht, Technikerbereich in dieser Reihenfolge | Programmdateien, siehe Abschnitt 4.3 |
| Test | 63 automatische Tests sowie automatische und manuelle Durchläufe der Oberfläche | `tests/` |

Die Diagramme sind mit UMLet erstellt (Dateiendung `.uxf`). In VS Code öffnet man sie mit der Erweiterung UMLet.

---

## 3. Anforderungen in Kürze

Die vollständige Liste steht in der [Anforderungsanalyse](../Anforderungsanalyse/Anforderungsanalyse.md).

**Umgesetzt:**
- Pro Kauf genau ein Getränk. Ausverkaufte Getränke sind gesperrt.
- Angenommen werden Münzen von 10 ct bis 2 € und Scheine zu 5 €, 10 € und 20 €.
- Das Rückgeld wird automatisch berechnet und nach Münzen aufgeschlüsselt angezeigt.
- Kann der Automat das Rückgeld nicht herausgeben, kommt kein Kauf zustande. Der Kunde erhält sein Geld zurück.
- Eingezahltes Geld und Wechselgeld liegen in zwei strikt getrennten Kassen.
- Jeder Verkauf wird gespeichert. Die Statistik zeigt Menge und Umsatz je Getränk, auch für einen Zeitraum.
- CSV-Export für Getränke, beide Kassen und Verkäufe. CSV-Import für Getränke und beide Kassen.
- Technikerbereich mit PIN.

**Bewusst nicht umgesetzt**, weil das nur einen echten Automaten betrifft:
- Hardware-Anbindung
- Touchscreen
- Netzwerk
- Kartenzahlung
- Benutzerverwaltung

---

## 4. Entwurf

### 4.1 Ablauf eines Kaufs

Das Aktivitätsdiagramm hat drei Bahnen: Kunde, Programm und Datenbank. Der Ablauf:

1. Das Programm liest die Getränke aus der Datenbank und zeigt sie an.
2. Der Kunde wählt ein Getränk und wirft Geld ein. Er kann jederzeit abbrechen.
3. Sobald der eingeworfene Betrag mindestens dem Preis entspricht, berechnet das Programm das Rückgeld aus der Wechselgeldkasse.
4. Ist das Rückgeld möglich, wird der Kauf in **einer** Datenbank-Transaktion gebucht, und Getränk und Rückgeld landen im Ausgabefach.
5. Ist es nicht möglich, erscheint „Bitte passend zahlen“, und der Kunde erhält sein eingeworfenes Geld zurück.

Bis zum Kaufabschluss liegt das eingeworfene Geld nur in einem **Zwischenspeicher** im Programm. Bei einem Abbruch wird die Datenbank deshalb gar nicht verändert.

### 4.2 Anwendungsfälle

| Akteur | Anwendungsfälle |
|---|---|
| Kunde | Getränk kaufen (schließt „Getränk auswählen“ und „Geld einwerfen“ ein), Kauf abbrechen (Erweiterung) |
| Techniker | Mit PIN anmelden, Getränke auffüllen, Wechselgeld auffüllen, Einnahmen leeren, Statistik ansehen, CSV exportieren, CSV importieren |

### 4.3 Architektur

Das Programm ist in drei Schichten aufgeteilt. Eine Schicht nutzt jeweils nur die darunterliegende:

```
Oberfläche     gui_kunde.py, gui_techniker.py     (tkinter, kein SQL)
     ↓
Logik          logik.py, csv_io.py                (Regeln, kein tkinter)
     ↓
Datenhaltung   datenbank.py, schema.sql           (einzige Stelle mit SQL)
```

Dadurch lässt sich die Logik, z. B. die Rückgeld-Berechnung, ohne Oberfläche testen.

| Datei | Inhalt |
|---|---|
| `main.py` | Start: erzeugt Datenbank, Automat und Kundenansicht |
| `datenbank.py` | Klasse `Datenbank` mit allen Lese- und Schreibzugriffen, Datenklasse `Getraenk` |
| `schema.sql`, `startdaten.sql` | Tabellen und Startbestand (9 Getränke, Geldsorten, Wechselgeld) |
| `logik.py` | Klasse `Automat` (Kaufablauf), Rückgeld-Berechnung, Geld-Formatierung, PIN-Prüfung |
| `csv_io.py` | CSV-Export und -Import mit Prüfung jeder Zeile |
| `gui_kunde.py` | Kundenansicht: Getränke, Display, Geldeinwurf, Ausgabefach |
| `gui_techniker.py` | PIN-Dialog und Technikerfenster mit fünf Reitern |
| `tests/` | Automatische Tests für Datenbank, Logik und CSV |

Die Klassen und ihre Methoden zeigt das [Klassendiagramm](../Diagramme/Klassendiagramm.uxf). Die genauen Signaturen stehen im [Projektplan, Abschnitt 8](../Planung/Projektplan.md).

### 4.4 Datenbank

| Tabelle | Inhalt |
|---|---|
| `geldsorte` | angenommene Münzen und Scheine (10 ct bis 20 €) |
| `getraenk` | Fach, Name, Preis, Bestand, Kapazität, Bild |
| `kasse_einzahlung` | Anzahl je Geldsorte aus Käufen |
| `kasse_wechselgeld` | Anzahl und Sollbestand je Münze für das Rückgeld |
| `verkauf` | ein Eintrag pro Kauf: Getränk, Zeitpunkt, Preis, bezahlt, Rückgeld |
| `verkauf_geld` | eingeworfene und herausgegebene Münzen und Scheine je Kauf |

- **Strikte Trennung der Kassen:** Es gibt zwei eigene Tabellen. Käufe legen Geld nur in die Einzahlungskasse, Rückgeld kommt nur aus der Wechselgeldkasse. Eingeworfenes Geld wird nie als Rückgeld verwendet.
- **Preis im Verkauf:** `verkauf` speichert den Preis zum Zeitpunkt des Kaufs. So stimmt die Statistik auch nach einer Preisänderung.
- **Prüfregeln:** Die Datenbank prüft selbst, dass Preise größer als 0 und Vielfache von 10 ct sind, dass der Bestand zwischen 0 und Kapazität liegt und dass keine Anzahl negativ wird.

Die Datenbank ist eine einzige Datei (`automat.db`). Das Programm legt sie beim ersten Start selbst an. Sie steht in der `.gitignore`, damit jedes Teammitglied mit dem gleichen Startbestand beginnt.

### 4.5 Oberfläche

Die Oberfläche folgt dem [Mockup](../Mockups/Mockup-Oberflaeche.uxf). Wir haben nur Bausteine eingeplant, die tkinter wirklich bietet, z. B. `ttk.Button` mit Bild, `ttk.LabelFrame`, `ttk.Notebook`, `ttk.Treeview` und `tk.Canvas`.

- **Kundenansicht:**
  - Links ein Raster mit 3 Spalten, jedes Fach ist ein Button mit Bild, Name und Preis. Bei mehr Getränken kommen Zeilen hinzu.
  - Rechts das Display, der Geldeinwurf (8 Buttons und „Abbrechen“) und das Ausgabefach.
  - Im Ausgabefach steht je Geldsorte eine Zeile mit Symbol, Anzahl („4 Stück“) und Teilsumme.
- **Technikerbereich:** Reiter Getränke, Wechselgeld, Einnahmen, Statistik und CSV.

---

## 5. Wichtige Lösungen

### 5.1 Geldbeträge in Cent

Alle Beträge werden intern und in der Datenbank als **ganze Zahl in Cent** geführt (230 statt 2,30). Kommazahlen rechnen im Computer ungenau: 1 − 0,9 ergibt 0,09999999999999998. Die Rückgeld-Berechnung fände dafür keine passende 10-ct-Münze und würde einen gültigen Kauf ablehnen.

In Euro mit Komma umgewandelt wird nur für Anzeige und CSV, und zwar über Text statt über Kommazahlen (`format_euro`, `parse_euro`).

### 5.2 Rückgeld-Berechnung

Der naheliegende Ansatz „immer die größte passende Münze zuerst“ scheitert, wenn der Bestand begrenzt ist. Beispiel: 60 ct sollen herausgegeben werden, in der Kasse liegen 1× 50 ct und 3× 20 ct, aber keine 10 ct. „Größte zuerst“ nimmt die 50 ct und kommt nicht weiter. Richtig wäre 3× 20 ct.

`berechne_rueckgeld` arbeitet deshalb mit **dynamischer Programmierung**. Das Verfahren berechnet für jeden Teilbetrag die Lösung mit den wenigsten Münzen und hält dabei den Bestand jeder Münzsorte ein. Gibt es eine Lösung, wird sie garantiert gefunden.

### 5.3 Kauf als Transaktion

`kauf_buchen` führt vier Schritte in **einer** Datenbank-Transaktion aus:
1. Bestand um 1 verringern
2. eingeworfenes Geld in die Einzahlungskasse buchen
3. Rückgeld aus der Wechselgeldkasse abziehen
4. Verkauf speichern

Scheitert ein Schritt, wird alles zurückgenommen (Rollback). Es gibt keine halben Buchungen.

### 5.4 Zustände des Automaten

Die Klasse `Automat` kennt drei Zustände: `BEREIT`, `GEWAEHLT` und `AUSGABE`. Die Oberfläche aktiviert nur die Buttons, die im aktuellen Zustand erlaubt sind. Geld lässt sich z. B. erst nach der Getränkewahl einwerfen, und „Entnehmen“ ist nur bei gefülltem Ausgabefach aktiv.

### 5.5 CSV-Import und -Export

- **Format:** Trennzeichen Semikolon, UTF-8 mit BOM, Beträge in Euro mit Komma (`2,30`). So öffnet ein deutsch eingestelltes Excel die Dateien direkt.
- **Import prüft zuerst alle Zeilen:** Kopfzeile, Spaltenzahl, Zahlen und Beträge, Preis als Vielfaches von 10 ct, Bestand höchstens so groß wie die Kapazität, bekannte Geldsorten und keine doppelten Fächer.
- **Fehler:** Ist eine Zeile fehlerhaft, wird nichts übernommen, und das Programm meldet die Zeilennummer.
- **Abgleich:** Getränke werden über die Fachnummer abgeglichen, also aktualisiert oder neu angelegt, aber nie gelöscht. Beim Import einer Kasse wird ihr Bestand ersetzt.

---

## 6. Bedienung

### 6.1 Starten

Voraussetzung ist **Python 3.10 oder neuer**. tkinter und SQLite sind bei den Installern von python.org schon enthalten. Das vorinstallierte Python 3.9 von macOS reicht nicht.

```bash
cd Getrankeautomat-Py
python3 main.py
```

Beim ersten Start entsteht die Datei `automat.db` mit 9 Getränken und 10.000 Münzen je Sorte als Wechselgeld. Zum Zurücksetzen löscht man die Datei, beim nächsten Start entsteht sie neu.

### 6.2 Kundenansicht

1. Ein Getränk anklicken. Das Display zeigt Preis und Restbetrag.
2. Münzen oder Scheine einwerfen, bis der Betrag reicht. Der Kauf schließt dann automatisch ab.
3. Im Ausgabefach liegen Getränk und Rückgeld. Mit „Entnehmen“ ist der Automat wieder bereit.

„Abbrechen“ gibt das bisher eingeworfene Geld zurück.

### 6.3 Technikerbereich

Über den Button „Service“ und die PIN **1234** öffnet sich der Technikerbereich. Er ist nur erreichbar, wenn gerade kein Kauf läuft.

| Reiter | Funktionen |
|---|---|
| Getränke | Bestand je Fach, ein Fach oder alle Fächer bis zur Kapazität auffüllen |
| Wechselgeld | Bestand und Sollbestand je Münze, auf Sollbestand auffüllen |
| Einnahmen | Inhalt der Einzahlungskasse mit Gesamtsumme, Kasse leeren (mit Rückfrage) |
| Statistik | Menge und Umsatz je Getränk, wahlweise für einen Zeitraum (TT.MM.JJJJ) |
| CSV | Export und Import, siehe Abschnitt 5.5 |

### 6.4 CSV-Dateien in Excel

Ob Excel eine CSV-Datei beim Doppelklick in Spalten aufteilt, hängt vom Zahlenformat des Systems ab. Bei deutschem Format trennt Excel bei `;`, bei englischem landet alles in Spalte A.

Dann öffnet man die Datei über *Daten → Aus Text/CSV* und wählt als Trennzeichen Semikolon. Damit Umlaute beim Import stimmen, speichert man in Excel als „CSV UTF-8 (durch Trennzeichen getrennt)“.

---

## 7. Test

### 7.1 Automatische Tests

Die Tests nutzen `unittest` aus der Standardbibliothek und eine Datenbank im Arbeitsspeicher. Sie verändern also keine echte Datenbank.

```bash
cd Getrankeautomat-Py
python3 -m unittest discover -s tests -v
```

| Datei | Anzahl | Prüft unter anderem |
|---|---|---|
| `tests/test_datenbank.py` | 16 | Startdaten, Kauf buchen, Rollback bei Fehlern, Auffüllen, Statistik mit Zeitraum, Import |
| `tests/test_logik.py` | 24 | Rückgeld-Berechnung, Geld-Formatierung, Zustandswechsel, Testfälle T1 bis T6 |
| `tests/test_csv.py` | 23 | Export, Import hin und zurück, Datei mit und ohne BOM, Fehlerfälle mit Zeilennummer |
| **Summe** | **63** | alle grün |

Die Testfälle T1 bis T6 aus der Planung:

| Nr. | Preis | Eingeworfen | Wechselgeldkasse | Ergebnis |
|---|---|---|---|---|
| T1 | 2,30 € | 5-€-Schein | genug Münzen | Kauf, Rückgeld 2,70 € = 1× 2 €, 1× 50 ct, 1× 20 ct |
| T2 | 2,00 € | 2-€-Münze | leer | Kauf, kein Rückgeld |
| T3 | 1,40 € | 2-€-Münze | 1× 50 ct, 3× 20 ct, keine 10 ct | Kauf, Rückgeld 3× 20 ct |
| T4 | 2,30 € | 5-€-Schein | leer | kein Kauf, „Bitte passend zahlen“, 5 € zurück |
| T5 | 1,00 € | 20-€-Schein | genug Münzen | Kauf, Rückgeld 9× 2 €, 1× 1 € |
| T6 | 2,30 € | 1 €, dann Abbruch | beliebig | 1 € zurück, Datenbank unverändert |

### 7.2 Oberfläche

- **Automatisch:** Skripte haben Kunden- und Technikeransicht über ihre Methoden durchgespielt, unter Tk 8.6 und Tk 9. Dazu gehörten Kauf, Abbruch, ausverkauftes Fach, PIN richtig und falsch, Auffüllen, Kasse leeren, ungültiges Datum, CSV hin und zurück, fehlerhafte Datei und ein Exportpfad, den es nicht gibt. Die Skripte haben auch geprüft, dass alle Texte im Ausgabefach vollständig sichtbar sind, bei normaler und bei kleinster Fenstergröße.
- **Von Hand:** Die Oberfläche wurde unter Windows und macOS ausprobiert. Die dabei gefundenen Fehler stehen in Abschnitt 8.

---

## 8. Probleme und Lösungen

| Problem | Ursache | Lösung |
|---|---|---|
| Rundungsfehler bei Beträgen drohen | Kommazahlen sind im Computer ungenau | Alle Beträge als ganze Zahl in Cent (Abschnitt 5.1) |
| „Größte Münze zuerst“ findet manchmal kein Rückgeld | Begrenzter Münzbestand | Dynamische Programmierung (Abschnitt 5.2) |
| Anzahl der Rückgeld-Münzen wurde übersehen | Anzahl stand klein unter nebeneinander gezeichneten Münzen | Ausgabefach als Liste: je Geldsorte Symbol, „N Stück“, Teilsumme |
| Texte im Ausgabefach unter macOS unsichtbar, unter Windows sichtbar | Im Dark Mode ist die Standard-Textfarbe auf dem Canvas weiß, der Hintergrund auch | Feste dunkle Textfarbe für alle Texte auf dem Canvas |
| Programm startet mit dem vorinstallierten Python von macOS nicht | Schreibweisen wie `int \| None` gibt es erst ab Python 3.10 | Python 3.10 oder neuer als Voraussetzung festgelegt |
| CSV-Datei erscheint in Excel in einer Spalte | Excel trennt je nach Zahlenformat des Systems bei `,` statt `;` | Format beibehalten, Hinweis zum Öffnen im Programm und in der Doku |
| Keine Meldung, wenn der Export nicht gespeichert werden kann | Schreibfehler wurden nicht abgefangen | Fehlermeldung mit Grund, z. B. wenn die Datei in Excel geöffnet ist |

---

## 9. Ergebnis und Ausblick

Alle Anforderungen der überarbeiteten Anforderungsanalyse sind umgesetzt. Der Automat lässt sich vollständig über die Oberfläche bedienen, und die Kernlogik ist durch 63 automatische Tests abgesichert.

Mögliche Erweiterungen:
- **Eigene Bilder:** Bilder je Getränk im Ordner `img/` ablegen. Die Spalte `bild` ist vorbereitet.
- **Änderungen ohne Datenverlust:** Bisher entsteht die Datenbank nach einer Änderung an `schema.sql` neu. Eine Migration würde die vorhandenen Daten übernehmen.
- **Excel-Dateien:** Export als `.xlsx` wäre bequemer, bräuchte aber ein zusätzliches Paket wie `openpyxl`.

---

## 10. Eingesetzte Werkzeuge

| Werkzeug | Zweck |
|---|---|
| Python 3, tkinter, sqlite3, unittest | Programm, Oberfläche, Datenbank, Tests (nur Standardbibliothek) |
| UMLet (VS-Code-Erweiterung) | Diagramme und Mockup |
| VS Code, git, GitHub | Entwicklung und Versionsverwaltung |
| Claude Code (KI-Assistent) | Unterstützung bei Planung, Programmierung und Tests |
