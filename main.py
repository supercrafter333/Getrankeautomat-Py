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

        image = load_image(getraenk.get("pic", "img/placeholder.png"))

        button = ttk.Button(
            frame,
            text=f'{getraenk["name"]}\n{getraenk["preis"]:.2f} €',
            width=30,
            image=image,
            compound=tk.TOP,
            command=lambda: play_sound("yeah-yeah.wav")
        )

        button.image = image
        button.grid(
            row=row,
            column=column,
            padx=20,
            pady=20,
            ipadx=20,
            ipady=20
        )


#PROGRAM
root = tk.Tk()
root.title("Getränkeautomat")
root.geometry("820x860")

#create frame
frame = ttk.Frame(
    root,
    borderwidth=2,
    relief="solid",
    padding=10
)

frame.pack(padx=20, pady=20)

getraenke = load_json()
create_drink_buttons(getraenke)

root.mainloop()