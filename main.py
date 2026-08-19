import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path


directory = Path(__file__).parent / "mock" / "daten.json"


def load_json():
    with open(directory, "r", encoding="utf-8") as file:
        data = json.load(file)

    getraenke = data.get("getraenke", [])

    for i, getraenk in enumerate(getraenke):
        row = i // 3
        column = i % 3

        name = getraenk["name"]
        preis = getraenk["preis"]

        button = ttk.Button(
            root,
            text=f"{name}\n{preis:.2f} €",
            width=15
        )

        button.grid(
            row=row,
            column=column,
            padx=10,
            pady=10,
            ipadx=10,
            ipady=10
        )


root = tk.Tk()
root.title("Getränkeautomat")
root.geometry("500x300")

load_json()

root.mainloop()