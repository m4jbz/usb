import customtkinter as ctk
from tkinter import messagebox
import crypto_utils
import main_app # La app principal del explorador de archivos
from cryptography.fernet import Fernet, InvalidToken # <-- CORRECCIÓN AQUÍ

class LoginWindow(ctk.CTk):
    """
    Ventana para la Fase 3: Desbloqueo del Baúl.
    """
    def __init__(self, baul_path, key_file_path):
        super().__init__()

        self.baul_path = baul_path
        self.key_file_path = key_file_path
        
        self.title("Desbloquear Baúl")
        self.geometry("350x200")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(self, text="Ingresa tu Contraseña Maestra", font=ctk.CTkFont(size=16))
        label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=300)
        self.pass_entry.grid(row=1, column=0, padx=20, pady=5)
        # Bindeamos Enter a la función de login
        self.pass_entry.bind("<Return>", self.attempt_login)

        self.login_button = ctk.CTkButton(self, text="Desbloquear", command=self.attempt_login, width=300)
        self.login_button.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self, text="", text_color="red")
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 10))
        
        # Enfocar el campo de contraseña al iniciar
        self.pass_entry.focus()

    def attempt_login(self, event=None):
        """Intenta descifrar la llave y lanzar la app principal."""
        password = self.pass_entry.get()
        if not password:
            self.status_label.configure(text="Ingresa una contraseña.")
            return

        self.status_label.configure(text="Descifrando...", text_color="gray")
        self.login_button.configure(state="disabled")
        self.pass_entry.configure(state="disabled")
        self.update_idletasks() # Forzar actualización de UI

        try:
            # 1. Leer el contenido del 'vault.key'
            with open(self.key_file_path, "rb") as f:
                vault_key_content = f.read()
            
            # 2. Intentar desbloquear
            session_key = crypto_utils.unlock_vault_key(password, vault_key_content)
            
            # 3. ¡Éxito! Lanzar la app principal
            self.destroy() # Cerrar ventana de login
            app = main_app.App(baul_path=str(self.baul_path), session_key=session_key)
            app.mainloop()

        except ValueError as e: # Captura "Contraseña incorrecta"
            self.status_label.configure(text=str(e), text_color="red")
            self.login_button.configure(state="normal")
            self.pass_entry.configure(state="normal")
            self.pass_entry.delete(0, "end")
        except FileNotFoundError:
            self.status_label.configure(text="Error: No se encontró el archivo 'vault.key'.", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Error inesperado: {e}", text_color="red")
            self.login_button.configure(state="normal")
            self.pass_entry.configure(state="normal")

if __name__ == "__main__":
    # Para pruebas (ejecutar este archivo directamente)
    from pathlib import Path
    app = LoginWindow(baul_path=Path("E:/Baul"), 
                      key_file_path=Path("E:/Baul/.credentials/vault.key"))
    app.mainloop()
