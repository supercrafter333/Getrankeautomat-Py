import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import winsound


def PlayASound(fileName):
    winsound.PlaySound("sounds/" + fileName, winsound.SND_FILENAME | winsound.SND_ASYNC)

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


        try:
            imgPath = getraenk["pic"]
            btn_img = tk.PhotoImage(file=imgPath)
            btn_img = btn_img.subsample(4, 4)
        except:
            btn_img = tk.PhotoImage(file="img/placeholder.png")
            btn_img = btn_img.subsample(4, 4)

        button = ttk.Button(
            root,
            text=f"{name}\n{preis:.2f} €",
            width=30,
            image=btn_img,
            compound=tk.TOP,
            command=lambda: PlayASound("yeah-yeah.wav")
        )

        button.image = btn_img


        button.grid(
            row=row,
            column=column,
            padx=20,
            pady=20,
            ipadx=20,
            ipady=20
        )


root = tk.Tk()
root.title("Getränkeautomat")
root.geometry("820x860")

load_json()

root.mainloop()