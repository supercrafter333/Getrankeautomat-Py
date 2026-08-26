import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import winsound



#CONFIG
ROOT_DIR = Path(__file__).parent
DATA_FILE = ROOT_DIR / "mock" / "daten.json"
SOUNDS_DIR = ROOT_DIR / "sounds"



#FUNCTIONS
def play_sound(file_name):
    sound_path = SOUNDS_DIR / file_name
    winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)


def load_json():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("getraenke", [])


def load_image(image_path):
    try:
        image = tk.PhotoImage(file=image_path)
    except tk.TclError:
        image = tk.PhotoImage(file="img/placeholder.png")

    return image.subsample(4, 4)


def create_drink_buttons(getraenke):
    for i, getraenk in enumerate(getraenke):
        row = i // 3
        column = i % 3

        image = load_image(
            getraenk.get("pic", "img/placeholder.png")
        )

        drink_frame = ttk.Frame(frame)
        drink_frame.grid(
            row=row,
            column=column,
            padx=20,
            pady=20
        )

        drink_button = ttk.Button(
            drink_frame,
            text=f'{getraenk["name"]}\n{getraenk["preis"]:.2f} €',
            width=30,
            image=image,
            compound=tk.TOP
        )

        drink_button.image = image

        drink_button.pack()

        choose_button = ttk.Button(
            drink_frame,
            text="Wählen",
            width=30,
            command=lambda: play_sound("yeah-yeah.wav")
        )

        choose_button.pack(pady=(5, 0))


# PROGRAM
root = tk.Tk()
root.title("Getränkeautomat")
root.geometry("1200x900")

# create main container
main_frame = ttk.Frame(root)
main_frame.pack(padx=20, pady=20)

# create drink frame
frame = ttk.Frame(
    main_frame,
    width=500,
    height=800,
    borderwidth=10,
    relief="solid",
    padding=10
)

frame.pack(side=tk.LEFT)
frame.pack_propagate(False)

# create side container
side_frame = ttk.Frame(
    main_frame,
    width=500,
    height=800,
    borderwidth=10,
    relief="solid",
    padding=10
)

side_frame.pack(side=tk.LEFT, padx=(20, 20))
side_frame.pack_propagate(False)

# Grid mit 4 Zeilen konfigurieren (weight=1 sorgt für gleichmäßige Aufteilung)
for row_idx in range(4):
    side_frame.grid_rowconfigure(row_idx, weight=1)
side_frame.grid_columnconfigure(0, weight=1)

# Elemente in den 4 Zeilen platzieren
geldAnzeige = ttk.Label(side_frame, text="Eingeworfener Betrag: 00,00€")
geldAnzeige.grid(row=0, column=0, sticky="w")



test2 = ttk.Label(side_frame, text="Test")
test2.grid(row=1, column=0, sticky="w")


getraenke = load_json()
create_drink_buttons(getraenke)

root.mainloop()