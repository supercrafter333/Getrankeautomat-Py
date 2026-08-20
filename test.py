import tkinter as tk
from tkinter import ttk

# Hauptfenster erstellen
root = tk.Tk()
root.title("Modernes TTK Button Design")
root.geometry("300x200")

# Beispiel-Bild laden (Achtung: Muss PNG oder GIF sein, 
# und die Referenz muss in einer Variable gespeichert bleiben!)
# icon_image = tk.PhotoImage(file="dein_bild.png")

# 1. PNG-Bild direkt mit Tkinter laden (muss eine PNG- oder GIF-Datei sein!)
original_img = tk.PhotoImage(file="img/cartoon-coffee.png").subsample(4, 4)

# 2. Bild verkleinern (Teilt die Originalgröße durch den übergebenen Wert)
# Beispiel: Ein 512x512 Bild wird mit (8, 8) zu einem perfekten 64x64 Icon.
button_img = original_img.subsample(4, 4) 

# Modernen TTK-Button mit Bild über dem Text definieren
#btn = ttk.Button(
#    root, 
#    text="Aktion", 
#    image=button_img, 
#    compound=tk.TOP,  # Platziert das Bild über dem Text
#    command=lambda: print("Button gedrückt"),
#)

# Wichtig: Referenz auf das Bild am Widget sichern, 
# damit der Garbage Collector es nicht löscht
#btn.image = button_img

#btn.place(width=50, height=70)
#btn.pack(expand=True, ipadx=10, ipady=10)

# todo: json import

frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0)

for row in range(3):
    for col in range(3):
        btn = ttk.Button(frame, text=f"Btn {row}-{col}")
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        btn.place(width=30, height=50)

# Spalten/Zeilen gleichmäßig verteilen
for i in range(3):
    frame.columnconfigure(i, weight=1)
    frame.rowconfigure(i, weight=1)


root.mainloop()