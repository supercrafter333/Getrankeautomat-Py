"""Technikerbereich des Getränkeautomaten (tkinter/ttk)."""

import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import csv_io
from datenbank import Datenbank
from logik import format_euro, pin_pruefen

CSV_TYPEN = [("CSV-Dateien", "*.csv")]
EXPORTE = {
    "getraenke": csv_io.export_getraenke,
    "wechselgeld": csv_io.export_wechselgeld,
    "einzahlung": csv_io.export_einzahlung,
    "verkaeufe": csv_io.export_verkaeufe,
}
IMPORTE = {
    "getraenke": csv_io.import_getraenke,
    "wechselgeld": csv_io.import_wechselgeld,
    "einzahlung": csv_io.import_einzahlung,
}
ERSETZEN_ARTEN = ("wechselgeld", "einzahlung")


def zahl_text(zahl: int) -> str:
    """10000 wird zu '10.000'."""
    return f"{zahl:,}".replace(",", ".")


class PinDialog(tk.Toplevel):
    """Modale PIN-Abfrage für den Technikerbereich."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("PIN eingeben")
        self.resizable(False, False)
        self.transient(parent)
        self._ergebnis = False
        self._eingabe = tk.StringVar()

        rahmen = ttk.Frame(self, padding=16)
        rahmen.pack(fill="both", expand=True)
        ttk.Label(rahmen, text="Techniker-PIN:").grid(row=0, column=0, sticky="w")
        self._feld = ttk.Entry(rahmen, textvariable=self._eingabe, show="•", width=16)
        self._feld.grid(row=0, column=1, padx=(8, 0))
        knoepfe = ttk.Frame(rahmen)
        knoepfe.grid(row=1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(knoepfe, text="OK", command=self._ok_geklickt).pack(side="left", padx=4)
        ttk.Button(knoepfe, text="Abbrechen", command=self._abbrechen_geklickt).pack(
            side="left")

        self.bind("<Return>", lambda _e: self._ok_geklickt())
        self.bind("<Escape>", lambda _e: self._abbrechen_geklickt())
        self.protocol("WM_DELETE_WINDOW", self._abbrechen_geklickt)
        self.update_idletasks()
        self.grab_set()
        self._feld.focus_set()

    def _ok_geklickt(self):
        """Prüft die PIN und schließt bei Erfolg das Fenster."""
        if pin_pruefen(self._eingabe.get()):
            self._ergebnis = True
            self._schliessen()
        else:
            messagebox.showerror("PIN", "Falsche PIN.", parent=self)
            self._eingabe.set("")
            self._feld.focus_set()

    def _abbrechen_geklickt(self):
        """Schließt das Fenster ohne Erfolg."""
        self._ergebnis = False
        self._schliessen()

    def _schliessen(self):
        self.grab_release()
        self.destroy()

    def ergebnis(self) -> bool:
        """Wartet, bis das Fenster geschlossen ist, und liefert True bei richtiger PIN."""
        self.wait_window(self)
        return self._ergebnis


class TechnikerFenster(tk.Toplevel):
    """Technikerbereich mit Reitern für Getränke, Wechselgeld, Einnahmen, Statistik und CSV."""

    def __init__(self, parent, db: Datenbank, bei_aenderung):
        super().__init__(parent)
        self.db = db
        self._bei_aenderung = bei_aenderung
        self.title("Technikerbereich")
        self.geometry("820x580")
        self.transient(parent)

        rahmen = ttk.Frame(self, padding=10)
        rahmen.pack(fill="both", expand=True)
        rahmen.columnconfigure(0, weight=1)
        rahmen.rowconfigure(1, weight=1)
        ttk.Button(rahmen, text="Abmelden", command=self._abmelden).grid(
            row=0, column=0, sticky="e", pady=(0, 8))
        self._notebook = ttk.Notebook(rahmen)
        self._notebook.grid(row=1, column=0, sticky="nsew")

        self._von = tk.StringVar()
        self._bis = tk.StringVar()
        self._reiter_getraenke()
        self._reiter_wechselgeld()
        self._reiter_einnahmen()
        self._reiter_statistik()
        self._reiter_csv()

        self.protocol("WM_DELETE_WINDOW", self._abmelden)
        self._tabellen_laden()
        self.update_idletasks()
        self.grab_set()

    # ---------- Aufbau ----------

    def _reiter(self, titel: str) -> ttk.Frame:
        seite = ttk.Frame(self._notebook, padding=10)
        seite.columnconfigure(0, weight=1)
        self._notebook.add(seite, text=titel)
        return seite

    def _tabelle(self, eltern, spalten, breiten, zeile=0) -> ttk.Treeview:
        """Legt ein Treeview mit Bildlaufleiste an; spalten sind (Schlüssel, Titel)."""
        eltern.rowconfigure(zeile, weight=1)
        tabelle = ttk.Treeview(eltern, columns=[s for s, _ in spalten], show="headings",
                               selectmode="browse")
        for (schluessel, titel), breite in zip(spalten, breiten):
            ausrichtung = "w" if schluessel in ("name", "getraenk", "muenze", "sorte") else "e"
            tabelle.heading(schluessel, text=titel)
            tabelle.column(schluessel, width=breite, anchor=ausrichtung)
        leiste = ttk.Scrollbar(eltern, orient="vertical", command=tabelle.yview)
        tabelle.configure(yscrollcommand=leiste.set)
        tabelle.grid(row=zeile, column=0, sticky="nsew")
        leiste.grid(row=zeile, column=1, sticky="ns")
        return tabelle

    def _reiter_getraenke(self):
        seite = self._reiter("Getränke")
        self._tab_getraenke = self._tabelle(
            seite,
            [("fach", "Fach"), ("name", "Name"), ("preis", "Preis"),
             ("bestand", "Bestand"), ("kapazitaet", "Kapazität")],
            [60, 260, 100, 100, 100])
        knoepfe = ttk.Frame(seite)
        knoepfe.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(knoepfe, text="Ausgewähltes Fach auffüllen",
                   command=self._fach_auffuellen_geklickt).pack(side="left", padx=(0, 8))
        ttk.Button(knoepfe, text="Alle Fächer auffüllen",
                   command=self._alle_auffuellen_geklickt).pack(side="left")
        ttk.Label(seite, text="Aufgefüllt wird jeweils bis zur Kapazität.").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _reiter_wechselgeld(self):
        seite = self._reiter("Wechselgeld")
        self._tab_wechselgeld = self._tabelle(
            seite,
            [("muenze", "Münze"), ("anzahl", "Anzahl"), ("soll", "Sollbestand")],
            [140, 140, 140])
        ttk.Button(seite, text="Auf Sollbestand auffüllen",
                   command=self._wechselgeld_auffuellen_geklickt).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _reiter_einnahmen(self):
        seite = self._reiter("Einnahmen")
        self._tab_einnahmen = self._tabelle(
            seite,
            [("sorte", "Geldsorte"), ("anzahl", "Anzahl"), ("summe", "Summe")],
            [140, 140, 140])
        ttk.Button(seite, text="Kasse leeren", command=self._kasse_leeren_geklickt).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _reiter_statistik(self):
        seite = self._reiter("Statistik")
        filter_zeile = ttk.Frame(seite)
        filter_zeile.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(filter_zeile, text="von (TT.MM.JJJJ):").pack(side="left")
        ttk.Entry(filter_zeile, textvariable=self._von, width=12).pack(side="left", padx=(4, 12))
        ttk.Label(filter_zeile, text="bis (TT.MM.JJJJ):").pack(side="left")
        ttk.Entry(filter_zeile, textvariable=self._bis, width=12).pack(side="left", padx=(4, 12))
        ttk.Button(filter_zeile, text="Anzeigen",
                   command=self._statistik_anzeigen_geklickt).pack(side="left")
        self._tab_statistik = self._tabelle(
            seite,
            [("getraenk", "Getränk"), ("menge", "Menge"), ("umsatz", "Umsatz")],
            [260, 120, 140], zeile=1)

    def _reiter_csv(self):
        seite = self._reiter("CSV")
        arten = (("Getränke", "getraenke"), ("Wechselgeld", "wechselgeld"),
                 ("Einnahmen", "einzahlung"), ("Verkäufe", "verkaeufe"))
        export = ttk.LabelFrame(seite, text="Export", padding=10)
        export.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for text, art in arten:
            ttk.Button(export, text=text, command=lambda a=art: self._export_geklickt(a)).pack(
                side="left", padx=(0, 8))
        importe = ttk.LabelFrame(seite, text="Import", padding=10)
        importe.grid(row=1, column=0, sticky="ew")
        for text, art in arten[:3]:
            ttk.Button(importe, text=text, command=lambda a=art: self._import_geklickt(a)).pack(
                side="left", padx=(0, 8))
        ttk.Label(seite, text="Aus Excel als ‚CSV UTF-8 (durch Trennzeichen getrennt)‘ "
                              "speichern.").grid(row=2, column=0, sticky="w", pady=(10, 0))

    # ---------- Tabellen ----------

    def _tabellen_laden(self):
        """Liest alle Tabellen neu aus der Datenbank."""
        self._getraenke_laden()
        self._wechselgeld_laden()
        self._einnahmen_laden()
        self._statistik_laden(None, None)

    @staticmethod
    def _leeren(tabelle: ttk.Treeview):
        tabelle.delete(*tabelle.get_children())

    def _getraenke_laden(self):
        self._leeren(self._tab_getraenke)
        for g in self.db.getraenke():
            self._tab_getraenke.insert("", "end", iid=str(g.fach), values=(
                g.fach, g.name, format_euro(g.preis_cent), g.bestand, g.kapazitaet))

    def _wechselgeld_laden(self):
        self._leeren(self._tab_wechselgeld)
        for wert, anzahl, soll in self.db.wechselgeld_tabelle():
            self._tab_wechselgeld.insert("", "end", values=(
                format_euro(wert), zahl_text(anzahl), zahl_text(soll)))

    def _einnahmen_laden(self):
        self._leeren(self._tab_einnahmen)
        bestand = self.db.einzahlung()
        gesamt = 0
        for wert, _art in self.db.geldsorten():
            anzahl = bestand.get(wert, 0)
            gesamt += wert * anzahl
            self._tab_einnahmen.insert("", "end", values=(
                format_euro(wert), zahl_text(anzahl), format_euro(wert * anzahl)))
        self._tab_einnahmen.insert("", "end", values=("Gesamt", "", format_euro(gesamt)))

    def _statistik_laden(self, von: str | None, bis: str | None):
        self._leeren(self._tab_statistik)
        menge_gesamt = 0
        umsatz_gesamt = 0
        for name, menge, umsatz in self.db.statistik(von, bis):
            menge_gesamt += menge
            umsatz_gesamt += umsatz
            self._tab_statistik.insert("", "end", values=(name, menge, format_euro(umsatz)))
        self._tab_statistik.insert("", "end", values=(
            "Gesamt", menge_gesamt, format_euro(umsatz_gesamt)))

    def _geaendert(self):
        """Lädt die Tabellen neu und benachrichtigt die Kundenansicht."""
        self._tabellen_laden()
        self._bei_aenderung()

    # ---------- Ereignisse ----------

    def _abmelden(self):
        """Schließt den Technikerbereich und lädt die Kundenansicht neu."""
        self.grab_release()
        self.destroy()
        self._bei_aenderung()

    def _fach_auffuellen_geklickt(self):
        """Füllt das ausgewählte Fach bis zur Kapazität auf."""
        auswahl = self._tab_getraenke.selection()
        if not auswahl:
            messagebox.showinfo("Auffüllen", "Bitte zuerst eine Zeile auswählen.", parent=self)
            return
        self.db.fach_auffuellen(int(self._tab_getraenke.item(auswahl[0], "values")[0]))
        self._geaendert()

    def _alle_auffuellen_geklickt(self):
        """Füllt alle Fächer bis zur Kapazität auf."""
        self.db.alle_auffuellen()
        self._geaendert()

    def _wechselgeld_auffuellen_geklickt(self):
        """Füllt die Wechselgeldkasse auf den Sollbestand auf."""
        self.db.wechselgeld_auffuellen()
        self._geaendert()

    def _kasse_leeren_geklickt(self):
        """Leert die Einzahlungskasse nach Rückfrage."""
        if messagebox.askyesno("Kasse leeren", "Einzahlungskasse wirklich leeren?",
                               parent=self):
            self.db.einnahmen_leeren()
            self._geaendert()

    def _datum_umwandeln(self, text: str) -> str | None:
        """'31.01.2026' wird zu '2026-01-31', leer zu None. ValueError bei ungültigem Datum."""
        text = text.strip()
        if not text:
            return None
        return datetime.strptime(text, "%d.%m.%Y").date().isoformat()

    def _statistik_anzeigen_geklickt(self):
        """Zeigt die Statistik für den eingegebenen Zeitraum."""
        try:
            von = self._datum_umwandeln(self._von.get())
            bis = self._datum_umwandeln(self._bis.get())
        except ValueError:
            messagebox.showerror("Statistik", "Ungültiges Datum. Bitte TT.MM.JJJJ eingeben.",
                                 parent=self)
            return
        self._statistik_laden(von, bis)

    def _export_geklickt(self, art: str):
        """Exportiert die gewählte Tabelle als CSV-Datei."""
        pfad = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv", initialfile=f"{art}.csv",
            filetypes=CSV_TYPEN)
        if not pfad:
            return
        EXPORTE[art](self.db, pfad)
        messagebox.showinfo("Export", f"Gespeichert: {pfad}", parent=self)

    def _import_geklickt(self, art: str):
        """Importiert eine CSV-Datei, bei Fehlern bleibt die Datenbank unverändert."""
        pfad = filedialog.askopenfilename(parent=self, filetypes=CSV_TYPEN)
        if not pfad:
            return
        if art in ERSETZEN_ARTEN and not messagebox.askyesno(
                "Import", "Der Bestand wird durch die Datei ersetzt. Fortfahren?", parent=self):
            return
        try:
            IMPORTE[art](self.db, pfad)
        except csv_io.ImportFehler as fehler:
            messagebox.showerror("Import", str(fehler), parent=self)
            return
        self._geaendert()
        messagebox.showinfo("Import", "Import abgeschlossen.", parent=self)
