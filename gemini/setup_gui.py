import customtkinter as ctk
import os
import shutil
from tkinter import filedialog, messagebox
import crypto_utils
import login_gui # Para lanzarlo después de configurar

class SetupWindow(ctk.CTk):
    """
    Ventana para la configuración inicial (Fase 2 de respuesta.txt).
    """
    def __init__(self, baul_path, key_file_path):
        super().__init__()

        self.baul_path = baul_path
        self.key_file_path = key_file_path
        self.credentials_path = os.path.dirname(key_file_path)

        self.title("Configuración del Baúl")
        self.geometry("400x350")
        self.resizable(False, False)

        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.show_initial_options()

    def show_initial_options(self):
        """Muestra los botones 'Crear' o 'Restaurar'."""
        self.clear_frame()
        label = ctk.CTkLabel(self.main_frame, text="No se ha encontrado un Baúl en esta USB.\n¿Qué deseas hacer?",
                             font=ctk.CTkFont(size=14))
        label.pack(pady=20, padx=10)

        btn_create = ctk.CTkButton(self.main_frame, text="Crear un nuevo Baúl", command=self.show_create_vault)
        btn_create.pack(pady=10, fill="x", padx=20)

        btn_restore = ctk.CTkButton(self.main_frame, text="Restaurar desde una copia", command=self.show_restore_vault)
        btn_restore.pack(pady=10, fill="x", padx=20)

    def show_create_vault(self):
        """Muestra la UI para crear una nueva contraseña."""
        self.clear_frame()
        label = ctk.CTkLabel(self.main_frame, text="Crea tu Contraseña Maestra", font=ctk.CTkFont(size=16))
        label.pack(pady=15)

        self.pass_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Contraseña", show="*")
        self.pass_entry.pack(pady=5, fill="x", padx=20)
        
        self.confirm_pass_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Confirmar contraseña", show="*")
        self.confirm_pass_entry.pack(pady=5, fill="x", padx=20)

        btn_create = ctk.CTkButton(self.main_frame, text="Crear y Guardar", command=self.create_new_vault)
        btn_create.pack(pady=20, fill="x", padx=20)
        
        btn_back = ctk.CTkButton(self.main_frame, text="Volver", fg_color="transparent", border_width=1,
                                 command=self.show_initial_options)
        btn_back.pack(pady=5, fill="x", padx=20)

    def create_new_vault(self):
        """Lógica para crear y guardar la nueva llave."""
        password = self.pass_entry.get()
        confirm_password = self.confirm_pass_entry.get()

        if not password or not confirm_password:
            messagebox.showerror("Error", "Ambos campos son obligatorios.")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        try:
            # 1. Generar el contenido de la llave
            vault_key_content = crypto_utils.generate_vault_key(password)

            # 2. Crear directorios
            os.makedirs(self.credentials_path, exist_ok=True)
            
            # 3. Guardar el vault.key en la USB
            with open(self.key_file_path, "wb") as f:
                f.write(vault_key_content)
            
            # 4. Forzar Respaldo OBLIGATORIO
            messagebox.showinfo("Respaldo Obligatorio", 
                                "¡Baúl creado! Ahora DEBES guardar una copia de seguridad de tu llave.\n"
                                "Si pierdes esta USB Y este archivo de respaldo, tus datos serán irrecuperables.")
            
            backup_path = filedialog.asksaveasfilename(
                title="Guardar copia de seguridad de vault.key",
                defaultextension=".key",
                filetypes=[("Vault Key", "*.key")]
            )

            if not backup_path:
                messagebox.showwarning("Advertencia", "No se guardó el respaldo. El Baúl se creó, pero se recomienda "
                                                     "hacer una copia de 'Baul/.credentials/vault.key' manualmente.")
            else:
                with open(backup_path, "wb") as f:
                    f.write(vault_key_content)
                messagebox.showinfo("Éxito", "Respaldo guardado con éxito.")

            # 5. Finalizar y pasar al login
            self.launch_login()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el Baúl: {e}")

    def show_restore_vault(self):
        """Muestra la UI para restaurar desde un .key."""
        self.clear_frame()
        label = ctk.CTkLabel(self.main_frame, text="Restaurar Baúl desde copia", font=ctk.CTkFont(size=16))
        label.pack(pady=15)
        
        self.restore_pass_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Tu Contraseña Maestra", show="*")
        self.restore_pass_entry.pack(pady=5, fill="x", padx=20)

        self.key_file_label = ctk.CTkLabel(self.main_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.key_file_label.pack(pady=5)

        self.key_file_content = None
        
        btn_find_key = ctk.CTkButton(self.main_frame, text="Buscar archivo .key", command=self.find_key_file)
        btn_find_key.pack(pady=5, fill="x", padx=20)

        btn_restore = ctk.CTkButton(self.main_frame, text="Restaurar Baúl", command=self.restore_vault)
        btn_restore.pack(pady=10, fill="x", padx=20)
        
        btn_back = ctk.CTkButton(self.main_frame, text="Volver", fg_color="transparent", border_width=1,
                                 command=self.show_initial_options)
        btn_back.pack(pady=5, fill="x", padx=20)
        
    def find_key_file(self):
        key_path = filedialog.askopenfilename(
            title="Selecciona tu archivo de respaldo vault.key",
            filetypes=[("Vault Key", "*.key")]
        )
        if key_path:
            try:
                with open(key_path, "rb") as f:
                    self.key_file_content = f.read()
                self.key_file_label.configure(text=os.path.basename(key_path), text_color="green")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
                
    def restore_vault(self):
        password = self.restore_pass_entry.get()
        if not password:
            messagebox.showerror("Error", "Ingresa tu contraseña.")
            return
            
        if not self.key_file_content:
            messagebox.showerror("Error", "Selecciona tu archivo de respaldo .key.")
            return
            
        try:
            # 1. Verificar que la contraseña y la llave sean correctas
            crypto_utils.unlock_vault_key(password, self.key_file_content)
            
            # 2. Si es correcto, crear directorios y copiar el archivo
            os.makedirs(self.credentials_path, exist_ok=True)
            with open(self.key_file_path, "wb") as f:
                f.write(self.key_file_content)
                
            messagebox.showinfo("Éxito", "¡Baúl restaurado con éxito en la USB!")
            
            # 3. Finalizar y pasar al login
            self.launch_login()
            
        except ValueError as e: # Captura el "Contraseña incorrecta"
            messagebox.showerror("Error", f"{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {e}")

    def clear_frame(self):
        """Limpia el frame principal."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def launch_login(self):
        """Cierra esta ventana y abre la de login."""
        self.destroy()
        login_app = login_gui.LoginWindow(baul_path=self.baul_path, key_file_path=self.key_file_path)
        login_app.mainloop()

if __name__ == "__main__":
    # Para pruebas (ejecutar este archivo directamente)
    if not os.path.exists("E:/Baul"):
        os.makedirs("E:/Baul", exist_ok=True)
        
    app = SetupWindow(baul_path=Path("E:/Baul"), 
                      key_file_path=Path("E:/Baul/.credentials/vault.key"))
    app.mainloop()
