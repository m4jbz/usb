import customtkinter as ctk
import psutil
import os
from pathlib import Path
from tkinter import messagebox
import setup_gui  # Importamos la nueva ventana de configuración
import login_gui  # Importamos la nueva ventana de login

class UsbSelector(ctk.CTkToplevel):
    """Una ventana emergente para seleccionar una USB cuando hay varias."""
    def __init__(self, master, usbs):
        super().__init__(master)
        self.title("Seleccionar USB")
        self.geometry("350x200")
        self.transient(master) # Mantiene esta ventana por encima de la principal
        self.grab_set() # Bloquea la interacción con la ventana principal

        self.selected_usb = None
        self.usb_var = ctk.StringVar(value=usbs[0].mountpoint)

        label = ctk.CTkLabel(self, text="Se detectaron varias USB.\nPor favor, selecciona una:")
        label.pack(pady=10, padx=10)

        for usb in usbs:
            rb = ctk.CTkRadioButton(self, text=f"{usb.mountpoint} ({usb.device})",
                                    variable=self.usb_var, value=usb.mountpoint)
            rb.pack(anchor="w", padx=20)

        button = ctk.CTkButton(self, text="Aceptar", command=self.on_select)
        button.pack(pady=20)
    
    def on_select(self):
        self.selected_usb = Path(self.usb_var.get())
        self.destroy()

    def get_selection(self):
        """Espera a que la ventana se cierre y devuelve la selección."""
        self.master.wait_window(self)
        return self.selected_usb

def find_usb():
    """Busca unidades USB y maneja los diferentes escenarios."""
    partitions = psutil.disk_partitions()
    # Ampliamos la detección para incluir 'REMOVABLE' en mayúsculas (común en algunos sistemas)
    usbs = [p for p in partitions if 'removable' in p.opts or 'REMOVABLE' in p.opts]

    if len(usbs) == 0:
        return "NO_USB", None
    
    if len(usbs) > 1:
        return "MULTIPLE_USB", usbs

    return "ONE_USB", Path(usbs[0].mountpoint)

def main_bootstrapper():
    """
    Función principal de arranque. Verifica la USB y lanza la
    interfaz de configuración o de login apropiada.
    """
    # 1. Verificar la USB primero, ANTES de crear cualquier ventana
    status, usb_info = find_usb()
    selected_path = None

    # 2. Manejar los casos de la USB
    if status == "NO_USB":
        # Creamos una raíz temporal SOLO para el messagebox
        root_msg = ctk.CTk()
        root_msg.withdraw()
        messagebox.showerror("Error", "No se detectó ninguna unidad USB.\nPor favor, inserta una USB antes de iniciar el programa.")
        root_msg.destroy()
        return # Salimos del programa

    if status == "MULTIPLE_USB":
        # Creamos una raíz temporal SOLO para el selector
        root_selector = ctk.CTk()
        root_selector.withdraw() # La ocultamos
        selector = UsbSelector(root_selector, usb_info)
        selected_path = selector.get_selection()
        root_selector.destroy() # La destruimos después de la selección
        
        if not selected_path:
            return # El usuario cerró el selector, salimos del programa
    
    elif status == "ONE_USB":
        selected_path = usb_info

    # 3. Si llegamos aquí, tenemos un 'selected_path' válido.
    # Definimos las rutas clave
    BAUL_PATH = selected_path / "Baul"
    CREDENTIALS_PATH = BAUL_PATH / ".credentials"
    KEY_FILE_PATH = CREDENTIALS_PATH / "vault.key"

    # 4. Ahora, lanzamos la ventana de aplicación PRINCIPAL.
    # Esta será la única instancia de ctk.CTk() que entrará en mainloop().
    if not KEY_FILE_PATH.exists():
        # Fase 2: Flujo de Configuración (Primera Vez)
        setup_app = setup_gui.SetupWindow(baul_path=BAUL_PATH, key_file_path=KEY_FILE_PATH)
        setup_app.mainloop()
    else:
        # Fase 3: Flujo de Uso Regular (Desbloqueo)
        login_app = login_gui.LoginWindow(baul_path=BAUL_PATH, key_file_path=KEY_FILE_PATH)
        login_app.mainloop()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    main_bootstrapper()

