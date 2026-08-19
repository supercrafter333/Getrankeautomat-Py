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
original_img = tk.PhotoImage(file="img/cartoon-coffee.png")

# 2. Bild verkleinern (Teilt die Originalgröße durch den übergebenen Wert)
# Beispiel: Ein 512x512 Bild wird mit (8, 8) zu einem perfekten 64x64 Icon.
button_img = original_img.subsample(4, 4) 

# Modernen TTK-Button mit Bild über dem Text definieren
btn = ttk.Button(
    root, 
    text="Aktion", 
    image=button_img, 
    compound=tk.TOP,  # Platziert das Bild über dem Text
    command=lambda: print("Button gedrückt"),
)

# Wichtig: Referenz auf das Bild am Widget sichern, 
# damit der Garbage Collector es nicht löscht
btn.image = button_img

btn.place(width=50, height=70)
btn.pack(expand=True, ipadx=10, ipady=10)

root.mainloop()