import customtkinter as ctk
import tkinter as tk
import os, time, pywinstyles
import shutil
from tkinter import messagebox
from pathlib import Path
from tkinter import filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Clase para el arbol de archivos, hereda de la clase padre: CTkScrollableFrame
class FileTreeView(ctk.CTkScrollableFrame):
    def __init__(self, master, path, **kwargs):
        super().__init__(master, **kwargs)

        self.path = path
        self.checkboxes = {}
        self.folder_children = {}

        self.populate_tree(self.path, 0)

    # Se ejecuta cuando se hace clic en cualquier checkbox
    def on_checkbox_toggle(self, path):
        # Obtenemos el estado actual (1=marcado, 0=desmarcado)
        is_checked = self.checkboxes[path].get()

        # Si el checkbox es de una carpeta, actualizamos a todos sus hijos
        if path in self.folder_children:
            self.update_children_state(path, is_checked)
    
    # Función auxiliar recursiva para actualizar los hijos
    def update_children_state(self, parent_path, state):
        if parent_path in self.folder_children:
            for child_path in self.folder_children[parent_path]:
                # Cambiamos el estado del checkbox del hijo
                if state == 1:
                    self.checkboxes[child_path].select()
                else:
                    self.checkboxes[child_path].deselect()
                
                # Si el hijo también es una carpeta, repetimos el proceso (recursión)
                self.update_children_state(child_path, state)

    def populate_tree(self, current_path, row, indent=0):
        try:
            items = sorted(os.listdir(current_path))
        except (FileNotFoundError, PermissionError) as e:
            print(f"Error al acceder a {current_path}: {e}")
            return row

        # Inicializamos la lista de hijos para la carpeta actual
        parent_path = os.path.dirname(current_path)
        if parent_path not in self.folder_children:
            self.folder_children[parent_path] = []

        dirs = [item for item in items if os.path.isdir(os.path.join(current_path, item))]
        files = [item for item in items if not os.path.isdir(os.path.join(current_path, item))]
        
        all_items = dirs + files # Procesamos carpetas y luego archivos

        # Creamos una lista de hijos para la carpeta actual
        self.folder_children[current_path] = [os.path.join(current_path, item) for item in all_items]

        for item in all_items:
            item_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(item_path)
            icon = "📁" if is_dir else "📄"
            
            # MODIFICADO: Añadimos el 'command' al checkbox
            cb = ctk.CTkCheckBox(self, text=f"{icon} {item}", 
                                 command=lambda p=item_path: self.on_checkbox_toggle(p))
            cb.grid(row=row, column=0, sticky="w", padx=(indent * 20, 0), pady=2)
            
            self.checkboxes[item_path] = cb
            row += 1
            
            if is_dir:
                row = self.populate_tree(item_path, row, indent + 1)
                
        return row

    def get_checked_items(self):
        checked_paths = []
        for path, checkbox in self.checkboxes.items():
            if checkbox.get() == 1:
                checked_paths.append(path)
        return checked_paths
        
    def refresh(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.checkboxes = {}
        self.folder_children = {}
        self.populate_tree(self.path, 0)

# Esta clase se encarga de checar si hubo actualizaciones en la carpeta
# de la USB y hace que la interfaz también se actualice
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, app_instance):
        self.app = app_instance
        self.last_event_time = 0
        self.debounce_time = 0.5  # 500ms de espera para actualizar muchas seguidas

    def on_any_event(self, event):
        current_time = time.time()
        # Checa si ya pasaron los 500ms
        if current_time - self.last_event_time > self.debounce_time:
            self.last_event_time = current_time
            if self.app.winfo_exists(): # Verifica que la venta si quiera exista todavía
                # Si todo se cumple, watchdog estando en un hilo secundario le pide al hilo principal
                # osea la interfaz que dentro de 100ms se actualice
                self.app.after(100, self.app.tree_view.refresh)

class App(ctk.CTk):
    def __init__(self, start_path="./"):
        super().__init__()

        self.usb_path = start_path

        if not os.path.exists(self.usb_path):
            print("Path doesn't exist.")
            exit(1)

        # Ventana principal
        self.title("Baúl")
        self.minsize(800, 600)

        # weight es para que sea resizable
        self.grid_columnconfigure(0, weight=3) # weight=3 hace que tenga mas width que otras columnas
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Muestra los archivos
        file_tree = ctk.CTkFrame(self)
        file_tree.grid(row=0, column=0, pady=10, sticky="NSEW")
        file_tree.grid_rowconfigure(1, weight=1)
        file_tree.grid_columnconfigure(0, weight=1)

        self.tree_view = FileTreeView(file_tree, path=start_path)
        self.tree_view.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # DnD frame
        drop_area = ctk.CTkFrame(self)
        drop_area.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")

        # Botón para seleccionar el directorio a donde
        # se enviaran los archivos
        goto_button = ctk.CTkButton(self, text="Enviar a", fg_color="green", hover=True, command=self.button_event)
        goto_button.grid(row=1, column=1, sticky="SE", padx=10, pady=10)

        label = ctk.CTkLabel(
            drop_area, # frame del que forma parte
            text="Arrastra y suelta archivos aquí",
            font=("Arial", 16)
        )

        label.pack(expand=True)

        # Watchdog Setup
        self.observer = Observer()
        event_handler = ChangeHandler(self)
        self.observer.schedule(event_handler, start_path, recursive=True)
        self.observer.start()

        # Esto es necesario para evitar errores al cerrar la interfaz,
        # permite que todo cierre correctamente
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Aplicar drag & drop usando pywinstyles
        pywinstyles.apply_dnd(drop_area, self.on_drop_to_usb)

    # Función para manejar el evento de soltar archivos (copiar A la USB)
    def on_drop_to_usb(self, files_dragged):
        if not files_dragged:
            return

        try:
            for item_path in files_dragged:
                base_name = os.path.basename(item_path)
                # El destino es la ruta inicial de la app (la USB)
                destination_path = os.path.join(self.usb_path, base_name)

                if os.path.isdir(item_path):
                    # Copia una carpeta entera y su contenido
                    shutil.copytree(item_path, destination_path, dirs_exist_ok=True)
                else:
                    # Copia un solo archivo
                    shutil.copy2(item_path, destination_path)
            
            messagebox.showinfo("Éxito", f"{len(files_dragged)} elemento(s) copiados a la USB.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al copiar a la USB:\n{e}")

    # Función que se activa al pulsar el botón, se encarga de copiar archivos de la USB
    # a una carpeta dada
    def button_event(self):
        checked_items = self.tree_view.get_checked_items()

        if not checked_items:
            messagebox.showwarning("No has seleccionado nada")
            return

        items = []
        checked_set = set(checked_items) 
        
        # Itera cada ruta de los archivos seleccionados
        for item_path in checked_items:
            # Checa si la ruta en la que esta el archivo ya esta seleccionada, si no lo esta
            # se añade a la lista, si lo está no.
            parent = os.path.dirname(item_path)
            if parent not in checked_set:
                items.append(item_path)

        # File dialog de Windows para escoger la carpeta
        destination_folder = filedialog.askdirectory(title="Selecciona una carpeta de destino")

        if destination_folder:
            try:
                for item_path in items:
                    base_name = os.path.basename(item_path)
                    destination_path = os.path.join(destination_folder, base_name)

                    if os.path.isdir(item_path):
                        shutil.copytree(item_path, destination_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item_path, destination_path)
                
                messagebox.showinfo("Éxito", f"{len(items)} elemento(s) copiados a:\n{destination_folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al copiar:\n{e}")

    # Cierra todo
    def on_closing(self):
        self.observer.stop()
        self.observer.join() # Espera que el hilo termine 
        self.destroy()

if __name__ == "__main__":
    path = "E:/Baul"
    app = App(start_path=path)
    app.mainloop()