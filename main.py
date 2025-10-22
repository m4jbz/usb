import customtkinter as ctk
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileTreeView(ctk.CTkScrollableFrame):
    """
    A CustomTkinter frame that displays a file tree view with checkboxes.
    """
    def __init__(self, master, path, **kwargs):
        """
        Initializes the FileTreeView.

        Args:
            master: The parent widget.
            path (str): The root path to display in the tree view.
            **kwargs: Additional arguments for the CTkScrollableFrame.
        """
        super().__init__(master, **kwargs)
        self.path = path
        self.checkboxes = {}

        # Configure the grid layout to have a single expanding column
        self.grid_columnconfigure(0, weight=1)

        # Start populating the tree from the root path
        self.populate_tree(self.path, 0)

    def populate_tree(self, current_path, row, indent=0):
        """
        Recursively populates the tree view with files and directories.

        Args:
            current_path (str): The directory path to scan.
            row (int): The starting grid row for the new widgets.
            indent (int): The indentation level for the current path.

        Returns:
            int: The next available grid row.
        """
        try:
            # Get a sorted list of items in the directory
            items = sorted(os.listdir(current_path))
        except FileNotFoundError:
            print(f"Error: Directory not found at {current_path}")
            return row
        except PermissionError:
            print(f"Error: Permission denied for {current_path}")
            return row

        # Separate directories and files to display directories first
        dirs = [item for item in items if os.path.isdir(os.path.join(current_path, item))]
        files = [item for item in items if not os.path.isdir(os.path.join(current_path, item))]

        # Process directories first
        for item in dirs:
            item_path = os.path.join(current_path, item)
            
            # Create a checkbox for the directory
            cb = ctk.CTkCheckBox(self, text=f"📁 {item}")
            cb.grid(row=row, column=0, sticky="w", padx=(indent * 20, 0), pady=2)
            
            # Store the checkbox and its path
            self.checkboxes[item_path] = cb
            row += 1
            
            # Recursively populate for the subdirectory
            row = self.populate_tree(item_path, row, indent + 1)

        # Process files next
        for item in files:
            item_path = os.path.join(current_path, item)

            # Create a checkbox for the file
            cb = ctk.CTkCheckBox(self, text=f"📄 {item}")
            cb.grid(row=row, column=0, sticky="w", padx=(indent * 20, 0), pady=2)

            # Store the checkbox and its path
            self.checkboxes[item_path] = cb
            row += 1
            
        return row

    def get_checked_items(self):
        """
        Returns a list of paths for all checked items.
        
        Returns:
            list: A list of strings, where each string is the full path of a checked item.
        """
        checked_paths = []
        for path, checkbox in self.checkboxes.items():
            if checkbox.get() == 1: # 1 means checked
                checked_paths.append(path)
        return checked_paths
        
    def refresh(self):
        """
        Clears and repopulates the tree view.
        """
        # Destroy all current widgets in the frame
        for widget in self.winfo_children():
            widget.destroy()

        # Reset the checkboxes dictionary and repopulate
        self.checkboxes = {}
        self.populate_tree(self.path, 0)


class ChangeHandler(FileSystemEventHandler):
    """
    Handles file system events and triggers a UI refresh.
    """
    def __init__(self, app_instance):
        self.app = app_instance
        self.last_event_time = 0
        self.debounce_time = 0.5  # 500ms debounce period

    def on_any_event(self, event):
        """
        Called on any file system event. Refreshes the tree view.
        """
        current_time = time.time()
        # Debounce to prevent rapid, successive refreshes
        if current_time - self.last_event_time > self.debounce_time:
            self.last_event_time = current_time
            if self.app.winfo_exists():
                # Schedule the refresh on the main GUI thread
                self.app.after(100, self.app.tree_view.refresh)


class App(ctk.CTk):
    """
    Main application window.
    """
    def __init__(self, start_path="."):
        super().__init__()

        self.title("File Tree View")
        self.geometry("600x700")

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Label
        label = ctk.CTkLabel(main_frame, text=f"File tree for: {os.path.abspath(start_path)}", font=ctk.CTkFont(weight="bold"))
        label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Create the FileTreeView instance
        self.tree_view = FileTreeView(main_frame, path=start_path)
        self.tree_view.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Button to get checked items
        self.get_checked_button = ctk.CTkButton(main_frame, text="Get Checked Items", command=self.show_checked_items)
        self.get_checked_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Textbox to display results
        self.result_textbox = ctk.CTkTextbox(main_frame, height=150)
        self.result_textbox.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.result_textbox.configure(state="disabled") # Make it read-only initially

        # --- Watchdog Setup ---
        self.observer = Observer()
        event_handler = ChangeHandler(self)
        self.observer.schedule(event_handler, start_path, recursive=True)
        self.observer.start()

        # Handle window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """
        Called when the application window is closed.
        Stops the watchdog observer thread.
        """
        self.observer.stop()
        self.observer.join() # Wait for the thread to finish
        self.destroy()

    def show_checked_items(self):
        """
        Callback for the button. Gets checked items and displays them.
        """
        checked_items = self.tree_view.get_checked_items()
        
        self.result_textbox.configure(state="normal") # Enable writing
        self.result_textbox.delete("1.0", "end") # Clear previous content
        
        if checked_items:
            self.result_textbox.insert("1.0", "Checked items:\n\n")
            for item in checked_items:
                self.result_textbox.insert("end", f"- {item}\n")
        else:
            self.result_textbox.insert("1.0", "No items are checked.")
            
        self.result_textbox.configure(state="disabled") # Make it read-only again

if __name__ == "__main__":
    # You can change the starting path here.
    # For example, use "C:/" on Windows or "/" on macOS/Linux.
    # Using "." starts the tree in the current directory of the script.
    app = App(start_path="E:/Baul")
    app.mainloop()
