import psutil, os
import customtkinter as ctk
from pathlib import Path

def find_usb():
    partitions = psutil.disk_partitions()
    usbs = [p for p in partitions if 'removable' in p.opts]

    if len(usbs) < 1:
        return None
    elif len(usbs) > 1:
        return usbs

    return Path(usbs[0].mountpoint)

def on_checkbox_toggle(path):
    print(path)

if __name__ == "__main__":
    app = ctk.CTk()
    app.title("Check")
    app.minsize(400, 300)

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)
    app.grid_rowconfigure(2, weight=2)
    app.grid_rowconfigure(0, weight=1)

    path_usb = find_usb()

    if isinstance(path_usb, list):

        label = ctk.CTkLabel(
            app,
            text="Escoge cual USB ocupar:",
            font=("Arial", 16)
        )
        label.grid(row=0, column=0, sticky="NEW", pady=10, padx=10)

        i = 1
        for x in path_usb:
            cb = ctk.CTkCheckBox(
                app,
                text=f"{x.mountpoint}",
                command=on_checkbox_toggle(x.mountpoint),
            )
            cb.grid(row=i, column=0, sticky="NEW", padx=110, pady=1)
            i += 1
            print(cb.get())

    elif path_usb:
        print(f"{path_usb}")
        
        ruta_directorio = path_usb / "Baul"
        
        if not ruta_directorio.exists():
            print(f"No existe el directorio {ruta_directorio}. Se creara uno nuevo.")
            ruta_directorio.mkdir()
    else:
        label = ctk.CTkLabel(
            app,
            text="No existe ninguna unidad USB.\nInserte una USB antes de iniciar el programa.",
            font=("Arial", 16)
        )
        label.grid(row=0, column=0, sticky="NSEW", pady=10, padx=10)

    app.mainloop()