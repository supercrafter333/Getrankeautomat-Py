"""Startpunkt des Getränkeautomaten."""

import tkinter as tk

from datenbank import Datenbank
from gui_kunde import KundenAnsicht
from logik import Automat


def main():
    """Startet die Kundenansicht."""
    db = Datenbank()
    automat = Automat(db)
    root = tk.Tk()
    KundenAnsicht(root, automat, db)
    root.mainloop()
    db.schliessen()


if __name__ == "__main__":
    main()
