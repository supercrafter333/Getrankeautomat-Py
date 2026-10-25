"""Kundenansicht des Getränkeautomaten (tkinter/ttk)."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from datenbank import Datenbank
from logik import Automat, Kaufergebnis, Zustand, format_euro

ORDNER = Path(__file__).parent
PLATZHALTER = ORDNER / "img" / "placeholder.png"
SPALTEN = 3
FARBE_MUENZE = "#f5e6b8"
FARBE_SCHEIN = "#d5e8d0"
FARBE_ABBRECHEN = "#f4c7c3"
FARBE_GEWAEHLT = "#fff2b3"
FARBE_DISPLAY = "#dff0d8"
ZEILE_NORMAL = 44
ZEILE_MIN = 26


def geld_text(wert: int) -> str:
    """10 wird zu '10 ct', 2000 zu '20 €'."""
    if wert < 100:
        return f"{wert} ct"
    return f"{wert // 100} €"


class KundenAnsicht:
    """Oberfläche für den Kunden: Getränke wählen, Geld einwerfen, Ausgabefach."""

    def __init__(self, root, automat: Automat, db: Datenbank):
        self.root = root
        self.automat = automat
        self.db = db
        self._ergebnis: Kaufergebnis | None = None
        self._bilder: dict[str, tk.PhotoImage] = {}
        self._getraenke_bilder: list[tk.PhotoImage] = []
        self._ausgabe_bild: tk.PhotoImage | None = None
        self._geld_buttons: list[ttk.Button] = []
        self._geldsorten = db.geldsorten()

        root.title("Getränkeautomat")
        root.geometry("1150x800")
        root.minsize(950, 700)
        self._styles_anlegen()
        self._aufbauen()
        self.aktualisieren()

    # ---------- Aufbau ----------

    def _styles_anlegen(self):
        """Legt die ttk-Styles an."""
        stil = ttk.Style(self.root)
        stil.theme_use("clam")
        stil.configure("Getraenk.TButton", font=("Helvetica", 11, "bold"), padding=6)
        stil.configure("Gewaehlt.TButton", font=("Helvetica", 11, "bold"), padding=6,
                       background=FARBE_GEWAEHLT)
        stil.map("Gewaehlt.TButton", background=[("disabled", FARBE_GEWAEHLT)])
        stil.configure("Muenze.TButton", background=FARBE_MUENZE, padding=8,
                       font=("Helvetica", 11, "bold"))
        stil.map("Muenze.TButton", background=[("active", FARBE_MUENZE),
                                               ("disabled", "#eeeeee")])
        stil.configure("Schein.TButton", background=FARBE_SCHEIN, padding=8,
                       font=("Helvetica", 11, "bold"))
        stil.map("Schein.TButton", background=[("active", FARBE_SCHEIN),
                                               ("disabled", "#eeeeee")])
        stil.configure("Abbrechen.TButton", background=FARBE_ABBRECHEN, padding=8,
                       font=("Helvetica", 11, "bold"))
        stil.map("Abbrechen.TButton", background=[("active", FARBE_ABBRECHEN),
                                                  ("disabled", "#eeeeee")])
        stil.configure("Display.TLabel", background=FARBE_DISPLAY, foreground="#1b3a1b",
                       font=("Courier", 16, "bold"), padding=12)
        stil.configure("Fach.TLabel", font=("Helvetica", 12, "bold"))

    def _aufbauen(self):
        hauptrahmen = ttk.Frame(self.root, padding=12)
        hauptrahmen.pack(fill="both", expand=True)
        hauptrahmen.columnconfigure(0, weight=3)
        hauptrahmen.columnconfigure(1, weight=2)
        hauptrahmen.rowconfigure(0, weight=1)

        self._getraenke_rahmen = ttk.LabelFrame(hauptrahmen, text="Getränke", padding=10)
        self._getraenke_rahmen.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        for spalte in range(SPALTEN):
            self._getraenke_rahmen.columnconfigure(spalte, weight=1, uniform="getraenk")

        ttk.Button(hauptrahmen, text="Service", command=self._service_geklickt).grid(
            row=1, column=0, sticky="w", pady=(8, 0))

        rechts = ttk.Frame(hauptrahmen)
        rechts.grid(row=0, column=1, rowspan=2, sticky="nsew")
        rechts.columnconfigure(0, weight=1)
        rechts.rowconfigure(2, weight=1)

        display_rahmen = ttk.LabelFrame(rechts, text="Display", padding=6)
        display_rahmen.grid(row=0, column=0, sticky="ew")
        display_rahmen.columnconfigure(0, weight=1)
        self._display = ttk.Label(display_rahmen, style="Display.TLabel", justify="left",
                                  anchor="nw", wraplength=380)
        self._display.grid(row=0, column=0, sticky="ew")
        self._display.configure(width=30)

        self._aufbau_geld(rechts)
        self._aufbau_ausgabe(rechts)

    def _aufbau_geld(self, eltern):
        rahmen = ttk.LabelFrame(eltern, text="Geld einwerfen", padding=8)
        rahmen.grid(row=1, column=0, sticky="ew", pady=10)
        rahmen.columnconfigure(0, weight=1)
        for zeile, art, stil in ((0, "Muenze", "Muenze.TButton"),
                                 (1, "Schein", "Schein.TButton")):
            reihe = ttk.Frame(rahmen)
            reihe.grid(row=zeile, column=0, sticky="ew", pady=2)
            sorten = [w for w, a in self._geldsorten if a == art]
            for spalte, wert in enumerate(sorten):
                reihe.columnconfigure(spalte, weight=1, uniform=art)
                knopf = ttk.Button(reihe, text=geld_text(wert), style=stil, width=6,
                                   command=lambda w=wert: self._geld_geklickt(w))
                knopf.grid(row=0, column=spalte, padx=2, sticky="ew")
                self._geld_buttons.append(knopf)
        self._abbrechen_knopf = ttk.Button(rahmen, text="Abbrechen",
                                           style="Abbrechen.TButton",
                                           command=self._abbrechen_geklickt)
        self._abbrechen_knopf.grid(row=2, column=0, sticky="ew", pady=(8, 0), padx=2)
        self._geld_buttons.append(self._abbrechen_knopf)

    def _aufbau_ausgabe(self, eltern):
        rahmen = ttk.LabelFrame(eltern, text="Ausgabefach", padding=8)
        rahmen.grid(row=2, column=0, sticky="nsew")
        rahmen.columnconfigure(1, weight=1)
        rahmen.rowconfigure(1, weight=1, minsize=130)

        links = ttk.Frame(rahmen)
        links.grid(row=0, column=0, rowspan=3, sticky="n", padx=(0, 10))
        self._ausgabe_bild_label = ttk.Label(links)
        self._ausgabe_bild_label.grid(row=0, column=0)
        self._ausgabe_name = ttk.Label(links, style="Fach.TLabel")
        self._ausgabe_name.grid(row=1, column=0)

        self._ausgabe_titel = ttk.Label(rahmen, style="Fach.TLabel")
        self._ausgabe_titel.grid(row=0, column=1, sticky="w")
        self._canvas = tk.Canvas(rahmen, height=110, background="white",
                                 highlightthickness=1, highlightbackground="#bbbbbb")
        self._canvas.grid(row=1, column=1, sticky="nsew", pady=6)
        self._canvas.bind("<Configure>", self._canvas_geaendert)
        self._entnehmen_knopf = ttk.Button(rahmen, text="Entnehmen",
                                           command=self._entnehmen_geklickt)
        self._entnehmen_knopf.grid(row=2, column=1, sticky="ew")

    # ---------- Hilfen ----------

    def _bild_laden(self, pfad: str | None) -> tk.PhotoImage:
        """Lädt ein Bild (verkleinert), bei Fehler den Platzhalter."""
        schluessel = pfad or ""
        if schluessel in self._bilder:
            return self._bilder[schluessel]
        bild = None
        if pfad:
            try:
                bild = tk.PhotoImage(master=self.root, file=str(ORDNER / pfad))
            except tk.TclError:
                bild = None
        if bild is None:
            bild = tk.PhotoImage(master=self.root, file=str(PLATZHALTER))
        bild = bild.subsample(3, 3)
        self._bilder[schluessel] = bild
        return bild

    def _fehler(self, fehler: ValueError):
        messagebox.showwarning("Hinweis", str(fehler))

    # ---------- Aktualisieren ----------

    def aktualisieren(self):
        """Liest die Getränke neu ein und zeichnet die gesamte Ansicht neu."""
        self._getraenke_aufbauen()
        self._display_aktualisieren()
        self._geld_aktualisieren()
        self._ausgabe_aktualisieren()

    def _getraenke_aufbauen(self):
        for kind in self._getraenke_rahmen.winfo_children():
            kind.destroy()
        self._getraenke_bilder = []
        getraenke = self.automat.getraenke()
        zeilen = (len(getraenke) + SPALTEN - 1) // SPALTEN
        for zeile in range(zeilen):
            self._getraenke_rahmen.rowconfigure(zeile, weight=1, uniform="getraenk")
        bereit = self.automat.zustand == Zustand.BEREIT
        gewaehlt = self.automat.gewaehlt
        for i, g in enumerate(getraenke):
            bild = self._bild_laden(g.bild)
            self._getraenke_bilder.append(bild)
            if g.ausverkauft():
                text = f"{g.name}\nausverkauft"
            else:
                text = f"{g.name}\n{format_euro(g.preis_cent)}"
            ist_gewaehlt = gewaehlt is not None and gewaehlt.fach == g.fach
            knopf = ttk.Button(
                self._getraenke_rahmen, text=text, image=bild, compound="top",
                style="Gewaehlt.TButton" if ist_gewaehlt else "Getraenk.TButton",
                command=lambda fach=g.fach: self._getraenk_geklickt(fach))
            if g.ausverkauft() or not bereit:
                knopf.state(["disabled"])
            knopf.grid(row=i // SPALTEN, column=i % SPALTEN, padx=6, pady=6, sticky="nsew")

    def _display_aktualisieren(self):
        a = self.automat
        if a.zustand == Zustand.BEREIT or a.gewaehlt is None:
            text = "Bitte Getränk wählen"
        else:
            zeilen = [
                a.gewaehlt.name,
                f"Preis: {format_euro(a.gewaehlt.preis_cent)}",
                f"Eingeworfen: {format_euro(a.eingeworfen())}",
            ]
            if a.zustand == Zustand.GEWAEHLT:
                zeilen.append(f"Noch zu zahlen: {format_euro(a.restbetrag())}")
            else:
                e = self._ergebnis
                if e is not None and e.verkauft:
                    zeilen.append(f"Rückgeld: {format_euro(sum(w * n for w, n in e.geld.items()))}")
                if e is not None:
                    zeilen.append("")
                    zeilen.append(e.meldung)
            text = "\n".join(zeilen)
        self._display.configure(text=text)

    def _geld_aktualisieren(self):
        zustand = "!disabled" if self.automat.zustand == Zustand.GEWAEHLT else "disabled"
        for knopf in self._geld_buttons:
            knopf.state([zustand])

    def _ausgabe_aktualisieren(self):
        self._canvas.delete("all")
        e = self._ergebnis if self.automat.zustand == Zustand.AUSGABE else None
        if e is None:
            self._ausgabe_bild_label.configure(image="")
            self._ausgabe_bild = None
            self._ausgabe_name.configure(text="")
            self._ausgabe_titel.configure(text="")
            self._entnehmen_knopf.state(["disabled"])
            return
        if e.verkauft and e.getraenk is not None:
            self._ausgabe_bild = self._bild_laden(e.getraenk.bild)
            self._ausgabe_bild_label.configure(image=self._ausgabe_bild)
            self._ausgabe_name.configure(text=e.getraenk.name)
        else:
            self._ausgabe_bild_label.configure(image="")
            self._ausgabe_bild = None
            self._ausgabe_name.configure(text="")
        summe = sum(w * n for w, n in e.geld.items())
        titel = "Rückgeld" if e.verkauft else "Rückgabe"
        self._ausgabe_titel.configure(text=f"{titel}: {format_euro(summe)}")
        self._geld_zeichnen(e)
        self._entnehmen_knopf.state(["!disabled"])

    def _geld_zeichnen(self, e: Kaufergebnis):
        """Zeichnet je Geldsorte eine Zeile mit Symbol, Anzahl und Teilsumme, von groß nach klein."""
        canvas = self._canvas
        breite = canvas.winfo_width()
        hoehe = canvas.winfo_height()
        if not e.geld:
            canvas.create_text(10, hoehe // 2, anchor="w", text="Kein Rückgeld",
                               font=("Helvetica", 12))
            return
        art = dict(self._geldsorten)
        sorten = sorted(e.geld, reverse=True)
        zeile_h = max(ZEILE_MIN, min(ZEILE_NORMAL, hoehe // len(sorten)))
        symbol_h = zeile_h - 6
        symbol_schrift = ("Helvetica", 11 if zeile_h >= 36 else 9, "bold")
        symbol_mitte = 10 + 35
        for i, wert in enumerate(sorten):
            anzahl = e.geld[wert]
            y = i * zeile_h + zeile_h / 2
            if art.get(wert) == "Schein":
                halb_b = max(symbol_h * 1.7 / 2, 18)
                canvas.create_rectangle(symbol_mitte - halb_b, y - symbol_h / 2,
                                        symbol_mitte + halb_b, y + symbol_h / 2,
                                        fill=FARBE_SCHEIN, outline="#6a8f66")
            else:
                canvas.create_oval(symbol_mitte - symbol_h / 2, y - symbol_h / 2,
                                   symbol_mitte + symbol_h / 2, y + symbol_h / 2,
                                   fill=FARBE_MUENZE, outline="#a58a3c")
            canvas.create_text(symbol_mitte, y, text=geld_text(wert), font=symbol_schrift)
            canvas.create_text(symbol_mitte + 50, y, anchor="w", text=f"{anzahl} Stück",
                               font=("Helvetica", 14, "bold"))
            canvas.create_text(breite - 10, y, anchor="e",
                               text=format_euro(wert * anzahl), font=("Helvetica", 12))

    def _canvas_geaendert(self, _ereignis=None):
        """Zeichnet das Ausgabefach bei Größenänderung neu."""
        if self.automat.zustand != Zustand.AUSGABE or self._ergebnis is None:
            return
        self._canvas.delete("all")
        self._geld_zeichnen(self._ergebnis)

    # ---------- Ereignisse ----------

    def _getraenk_geklickt(self, fach: int):
        """Wählt das Getränk im Fach."""
        try:
            self.automat.waehlen(fach)
        except ValueError as fehler:
            self._fehler(fehler)
        self.aktualisieren()

    def _geld_geklickt(self, wert: int):
        """Wirft eine Geldsorte ein."""
        try:
            ergebnis = self.automat.einwerfen(wert)
        except ValueError as fehler:
            self._fehler(fehler)
        else:
            if ergebnis is not None:
                self._ergebnis = ergebnis
        self.aktualisieren()

    def _abbrechen_geklickt(self):
        """Bricht den Kauf ab."""
        try:
            ergebnis = self.automat.abbrechen()
        except ValueError as fehler:
            self._fehler(fehler)
        else:
            self._ergebnis = ergebnis
        self.aktualisieren()

    def _entnehmen_geklickt(self):
        """Leert das Ausgabefach."""
        try:
            self.automat.entnehmen()
        except ValueError as fehler:
            self._fehler(fehler)
        else:
            self._ergebnis = None
        self.aktualisieren()

    def _service_geklickt(self):
        """Öffnet nach PIN-Eingabe den Technikerbereich, nur im Zustand BEREIT."""
        if self.automat.zustand != Zustand.BEREIT:
            messagebox.showinfo("Service", "Bitte zuerst den Kauf abschließen.")
            return
        try:
            from gui_techniker import PinDialog, TechnikerFenster
        except ImportError:
            messagebox.showinfo("Service", "Der Technikerbereich folgt im nächsten Schritt.")
            return
        if PinDialog(self.root).ergebnis():
            TechnikerFenster(self.root, self.db, self.aktualisieren)
