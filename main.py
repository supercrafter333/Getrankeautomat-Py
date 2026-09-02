import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
import winsound

ROOT_DIR = Path(__file__).parent
DATA_FILE = ROOT_DIR / "mock" / "daten.json"
SOUNDS_DIR = ROOT_DIR / "sounds"

COLUMNS = 3


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


def choose_drink(getraenk):
    play_sound("yeah-yeah.wav")
    updatePriceDisplay(getraenk["preis"])
    updateProductDisplay(getraenk["name"])


def updatePriceDisplay(price):
    paidAmount.config(text=f"Zu zahlender Betrag: {price:.2f} €")


def updateProductDisplay(name):
    product.config(text=f"Gewähltes Produkt: {name}")


def create_drink_buttons(getraenke):
    for column in range(COLUMNS):
        frame.grid_columnconfigure(column, weight=1)

    for i, getraenk in enumerate(getraenke):
        row = i // COLUMNS
        column = i % COLUMNS
        frame.grid_rowconfigure(row, weight=1)

        image = load_image(getraenk.get("pic", "img/placeholder.png"))

        drink_frame = ttk.Frame(frame, style="Drink.TFrame", padding=10)
        drink_frame.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")
        drink_frame.grid_columnconfigure(0, weight=1)

        drink_button = ttk.Button(
            drink_frame,
            text=f'{getraenk["name"]}\n{getraenk["preis"]:.2f} €',
            image=image,
            compound=tk.TOP,
            style="Drink.TButton",
        )
        drink_button.image = image
        drink_button.grid(row=0, column=0, sticky="nsew")

        choose_button = ttk.Button(
            drink_frame,
            text="Wählen",
            command=lambda g=getraenk: choose_drink(g),
            style="Choose.TButton",
        )
        choose_button.grid(row=1, column=0, sticky="ew", pady=(8, 0))


root = tk.Tk()
root.title("Getränkeautomat")
root.geometry("1200x900")
root.minsize(800, 600)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("Drink.TFrame", background="#2b2b2b")
style.configure("Drink.TButton", font=("Segoe UI", 11, "bold"), padding=10)
style.configure("Choose.TButton", font=("Segoe UI", 10), padding=6)
style.configure("Info.TLabel", font=("Segoe UI", 13), background="#f5f5f5")

main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)
main_frame.grid_columnconfigure(0, weight=3)
main_frame.grid_columnconfigure(1, weight=2)
main_frame.grid_rowconfigure(0, weight=1)

frame = tk.Frame(main_frame, bg="#1f1f1f", bd=12, relief="ridge")
frame.grid(row=0, column=0, sticky="nsew")

side_frame = ttk.Frame(main_frame, padding=20, relief="solid", borderwidth=2)
side_frame.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
side_frame.grid_columnconfigure(0, weight=1)
side_frame.grid_rowconfigure(0, weight=0)
side_frame.grid_rowconfigure(1, weight=0)
side_frame.grid_rowconfigure(2, weight=1)

paidAmount = ttk.Label(side_frame, text="Zu zahlender Betrag: 0,00 €", style="Info.TLabel")
paidAmount.grid(row=0, column=0, sticky="w", pady=(0, 10))

product = ttk.Label(side_frame, text="Gewähltes Produkt: ", style="Info.TLabel")
product.grid(row=1, column=0, sticky="w")

getraenke = load_json()
create_drink_buttons(getraenke)

root.mainloop()
