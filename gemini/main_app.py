import customtkinter as ctk
import tkinter as tk
import os, time, pywinstyles
import shutil
from tkinter import messagebox
from pathlib import Path
from tkinter import filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cryptography.fernet import Fernet, InvalidToken # <-- CORRECCIÓN AQUÍ

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Clase para el arbol de archivos, hereda de la clase padre: CTkScrollableFrame
class FileTreeView(ctk.CTkScrollableFrame):
    def __init__(self, master, path, fernet: Fernet, **kwargs):
        super().__init__(master, **kwargs)

        self.path = path
        self.fernet = fernet # La llave de sesión descifrada
        self.checkboxes = {}
        self.folder_children = {}
        self.real_path_map = {} # Mapea el texto del checkbox al path cifrado real

        self.populate_tree(self.path, 0)

    def on_checkbox_toggle(self, display_path):
        is_checked = self.checkboxes[display_path].get()
        if display_path in self.folder_children:
            self.update_children_state(display_path, is_checked)
    
    def update_children_state(self, parent_display_path, state):
        if parent_display_path in self.folder_children:
            for child_display_path in self.folder_children[parent_display_path]:
                if state == 1:
                    self.checkboxes[child_display_path].select()
                else:
                    self.checkboxes[child_display_path].deselect()
                self.update_children_state(child_display_path, state)

    def populate_tree(self, current_path, row, indent=0, parent_display_path=""):
        try:
            # Leemos los nombres de archivo cifrados del disco
            items = sorted(os.listdir(current_path))
        except (FileNotFoundError, PermissionError) as e:
            print(f"Error al acceder a {current_path}: {e}")
            return row

        parent_path = os.path.dirname(current_path)
        if parent_display_path not in self.folder_children:
            self.folder_children[parent_display_path] = []

        dirs = [item for item in items if os.path.isdir(os.path.join(current_path, item))]
        # MODIFICADO: Solo listamos archivos que terminan en .enc
        files = [item for item in items if not os.path.isdir(os.path.join(current_path, item)) and item.endswith(".enc")]
        
        all_items = dirs + files

        current_display_children = []

        for item in all_items:
            real_item_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(real_item_path)
            
            display_name = ""
            if is_dir:
                icon = "📁"
                display_name = item # Las carpetas no están cifradas
            else:
                icon = "📄"
                try:
                    # Desciframos el nombre del archivo para mostrarlo
                    encrypted_name_hex = item.replace(".enc", "")
                    decrypted_name_bytes = self.fernet.decrypt(bytes.fromhex(encrypted_name_hex))
                    display_name = decrypted_name_bytes.decode()
                except (InvalidToken, ValueError, TypeError):
                    display_name = f"¡Archivo corrupto! ({item[:10]}...)"
                except Exception:
                     display_name = f"¡Error al leer! ({item[:10]}...)"

            # Usamos el 'display_name' para el arbol y los diccionarios
            # El 'display_path' es la ruta visual, no la real
            display_path = os.path.join(parent_display_path, display_name)
            current_display_children.append(display_path)

            cb = ctk.CTkCheckBox(self, text=f"{icon} {display_name}", 
                                 command=lambda p=display_path: self.on_checkbox_toggle(p))
            cb.grid(row=row, column=0, sticky="w", padx=(indent * 20, 0), pady=2)
            
            self.checkboxes[display_path] = cb
            # Guardamos el mapeo: "Ruta/Visual/Archivo.txt" -> "E:/Baul/...hex...enc"
            self.real_path_map[display_path] = real_item_path 
            row += 1
            
            if is_dir:
                row = self.populate_tree(real_item_path, row, indent + 1, parent_display_path=display_path)
        
        if parent_display_path:
            self.folder_children[parent_display_path] = current_display_children
        
        return row

    def get_checked_items(self):
        """Retorna una lista de las RUTAS REALES (cifradas) de los items seleccionados."""
        checked_real_paths = []
        for display_path, checkbox in self.checkboxes.items():
            if checkbox.get() == 1:
                # Añadimos la ruta real cifrada, no la visual
                checked_real_paths.append(self.real_path_map[display_path])
        return checked_real_paths
        
    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.checkboxes = {}
        self.folder_children = {}
        self.real_path_map = {}
        self.populate_tree(self.path, 0, parent_display_path="")

# ... (Clase ChangeHandler sin cambios) ...
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, app_instance):
        self.app = app_instance
        self.last_event_time = 0
        self.debounce_time = 0.5

    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_event_time > self.debounce_time:
            self.last_event_time = current_time
            if self.app.winfo_exists():
                self.app.after(100, self.app.tree_view.refresh)

class App(ctk.CTk):
    # MODIFICADO: __init__ ahora acepta la llave de sesión
    def __init__(self, baul_path, session_key: Fernet):
        super().__init__()

        self.baul_path = baul_path
        self.fernet = session_key # La llave de sesión descifrada

        if not os.path.exists(self.baul_path):
            messagebox.showerror("Error", "No se encontró la carpeta 'Baul'.")
            exit(1)

        self.title("Baúl Seguro")
        self.minsize(800, 600)

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        file_tree = ctk.CTkFrame(self)
        file_tree.grid(row=0, column=0, pady=10, sticky="NSEW")
        file_tree.grid_rowconfigure(1, weight=1)
        file_tree.grid_columnconfigure(0, weight=1)

        # MODIFICADO: Pasamos la llave 'fernet' al FileTreeView
        self.tree_view = FileTreeView(file_tree, path=self.baul_path, fernet=self.fernet)
        self.tree_view.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        drop_area = ctk.CTkFrame(self)
        drop_area.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")

        goto_button = ctk.CTkButton(self, text="Enviar a", fg_color="green", hover=True, command=self.button_event)
        goto_button.grid(row=1, column=1, sticky="SE", padx=10, pady=10)

        label = ctk.CTkLabel(drop_area, text="Arrastra y suelta archivos aquí\n(para CIFRAR y guardar)", font=("Arial", 16))
        label.pack(expand=True)

        self.observer = Observer()
        event_handler = ChangeHandler(self)
        self.observer.schedule(event_handler, self.baul_path, recursive=True)
        self.observer.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        pywinstyles.apply_dnd(drop_area, self.on_drop_to_usb)

    # MODIFICADO: Esta función ahora CIFRA todo lo que se le arrastra
    def on_drop_to_usb(self, files_dragged):
        if not files_dragged:
            return
        
        try:
            for item_path_str in files_dragged:
                item_path = Path(item_path_str)
                self.encrypt_and_copy_item(item_path, self.baul_path)
            
            messagebox.showinfo("Éxito", f"{len(files_dragged)} elemento(s) cifrados y copiados a la USB.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cifrar y copiar:\n{e}")

    def encrypt_and_copy_item(self, source_path: Path, destination_folder: str):
        """
        Cifra y copia un item (archivo o carpeta) al baúl.
        Las carpetas se recrean y los archivos dentro se cifran.
        """
        if source_path.is_dir():
            # Si es una carpeta, la creamos (sin cifrar) en el destino
            new_dest_folder = os.path.join(destination_folder, source_path.name)
            os.makedirs(new_dest_folder, exist_ok=True)
            # Recursión: Ciframos todo el contenido de esta carpeta
            for sub_item in source_path.iterdir():
                self.encrypt_and_copy_item(sub_item, new_dest_folder)
        
        elif source_path.is_file():
            # Si es un archivo, ciframos el nombre y el contenido
            
            # 1. Cifrar nombre
            encrypted_name_hex = self.fernet.encrypt(source_path.name.encode()).hex()
            destination_path = os.path.join(destination_folder, encrypted_name_hex + ".enc")
            
            # 2. Cifrar contenido (¡Cuidado con archivos grandes!)
            # Fernet carga todo en RAM. Para archivos > 1GB esto puede ser lento.
            # Como pediste, mantenemos la implementación simple por ahora.
            with open(source_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = self.fernet.encrypt(data)
            
            with open(destination_path, 'wb') as f:
                f.write(encrypted_data)

    # MODIFICADO: Esta función ahora DESCIFRA todo lo seleccionado
    def button_event(self):
        # get_checked_items() ya nos da las rutas reales (cifradas)
        checked_items_real_paths = self.tree_view.get_checked_items()

        if not checked_items_real_paths:
            messagebox.showwarning("Nada seleccionado", "Primero selecciona los archivos que quieres copiar.")
            return

        # Filtramos la lista para evitar copias duplicadas
        top_level_items = []
        checked_set = set(checked_items_real_paths)
        for item_path in checked_items_real_paths:
            parent = os.path.dirname(item_path)
            if parent not in checked_set or parent == self.baul_path:
                 # Añadimos si su padre no está en la lista, O si su padre es la raíz del baúl
                if item_path != self.baul_path: # Evitamos añadir la propia raíz
                    top_level_items.append(item_path)

        if not top_level_items:
            # Esto puede pasar si solo se seleccionó la raíz o nada
            return

        destination_folder = filedialog.askdirectory(title="Selecciona una carpeta de destino")

        if destination_folder:
            try:
                for item_path_str in top_level_items:
                    self.decrypt_and_copy_item(Path(item_path_str), destination_folder)
                
                messagebox.showinfo("Éxito", f"{len(top_level_items)} elemento(s) descifrados y copiados a:\n{destination_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al descifrar y copiar:\n{e}")

    def decrypt_and_copy_item(self, source_path: Path, destination_folder: str):
        """
        Descifra y copia un item (archivo o carpeta) del baúl a la PC.
        """
        if source_path.is_dir():
            # Si es una carpeta, creamos la carpeta (descifrada = nombre normal)
            new_dest_folder = os.path.join(destination_folder, source_path.name)
            os.makedirs(new_dest_folder, exist_ok=True)
            # Recursión: Desciframos todo su contenido
            for sub_item in source_path.iterdir():
                self.decrypt_and_copy_item(sub_item, new_dest_folder)

        elif source_path.is_file() and source_path.name.endswith(".enc"):
            # Si es un archivo .enc...
            
            # 1. Descifrar nombre
            try:
                encrypted_name_hex = source_path.name.replace(".enc", "")
                decrypted_name = self.fernet.decrypt(bytes.fromhex(encrypted_name_hex)).decode()
                destination_path = os.path.join(destination_folder, decrypted_name)
            except Exception as e:
                print(f"No se pudo descifrar el nombre {source_path.name}: {e}")
                messagebox.showwarning("Error de nombre", f"No se pudo descifrar el nombre del archivo {source_path.name}. Se omitirá.")
                return

            # 2. Descifrar contenido
            try:
                with open(source_path, 'rb') as f:
                    encrypted_data = f.read()
                
                data = self.fernet.decrypt(encrypted_data)
                
                with open(destination_path, 'wb') as f:
                    f.write(data)
            except InvalidToken:
                messagebox.showerror("Error", f"Error de llave al descifrar {decrypted_name}. ¿Archivo corrupto?")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo descifrar el contenido de {decrypted_name}: {e}")


    def on_closing(self):
        self.observer.stop()
        self.observer.join()
        self.destroy()

if __name__ == "__main__":
    # --- Para Pruebas (asumiendo que ya está configurado) ---
    # 1. Ejecuta setup_gui.py primero para crear un 'vault.key' de prueba.
    # 2. Ejecuta login_gui.py para desbloquear y lanzar esta app.
    
    # Este bloque 'if' es solo para evitar que se lance sin un login.
    # Deberías ejecutar 'run.py' para el flujo normal.
    print("Este archivo no debe ejecutarse directamente.")
    print("Ejecuta 'run.py' para iniciar la aplicación.")
    
    # Si de todas formas quieres probarlo, necesitas una llave y contraseña:
    # 1. Crea una contraseña y una llave:
    #    import crypto_utils
    #    key_content = crypto_utils.generate_vault_key("tu_password")
    #    with open("E:/Baul/.credentials/vault.key", "wb") as f: f.write(key_content)
    # 2. Desbloquea la llave:
    #    with open("E:/Baul/.credentials/vault.key", "rb") as f: key_content = f.read()
    #    llave = crypto_utils.unlock_vault_key("tu_password", key_content)
    # 3. Lanza la app:
    #    app = App(baul_path="E:/Baul", session_key=llave)
    #    app.mainloop()
    pass
