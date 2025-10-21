from tkinter import Tk, Label
from tkinterdnd2 import DND_FILES, TkinterDnD

def drop(event):
    print("Elemento seleccionado:", event.data)

root = TkinterDnD.Tk()
root.title("Arrastra un archivo o carpeta aquí")

label = Label(root, text="Arrastra aquí un archivo o carpeta", width=50, height=5, bg="lightgray")
label.pack(padx=10, pady=10)

label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', drop)

root.mainloop()
