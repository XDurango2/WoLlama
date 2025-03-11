# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
from config.constants import APP_NAME, APP_VERSION
from utils.network import get_mac_ip_list, wake_on_lan, shutdown_remote, restart_remote, connect_rdp
from utils.logger import create_logging_window, log_action
from .about_window import AboutWindow
from .favorites_manager import FavoritesManager
from .export_favorites import export_favorites
from .import_favorites import import_favorites
from .change_admin import change_admin_user
import os, subprocess

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("800x400")
        
        self.device_vars = {}
        self.all_devices = []
        self.app_config = self.load_config()
        
        # Inicializar el gestor de favoritos
        self.favorites_manager = FavoritesManager(self)
        
        self.setup_ui()
        self.setup_menu()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame superior
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Checkbox favoritos
        self.show_favorites = tk.BooleanVar()
        ttk.Checkbutton(
            top_frame, 
            text="Solo Favoritos",
            variable=self.show_favorites,
            command=self.filter_devices
        ).pack(side=tk.LEFT)
        
        # Barra de búsqueda
        ttk.Label(top_frame, text="Buscar:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_devices)
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Tabla de dispositivos - Añadimos columna para estrella y nombre
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("check", "ip", "mac", "info"),
            show="headings",
            height=10
        )
        
        self.tree.heading("check", text="")
        self.tree.heading("ip", text="Dirección IP")
        self.tree.heading("mac", text="Dirección MAC")
        self.tree.heading("info", text="Información")
        
        self.tree.column("check", width=30, anchor="center")
        self.tree.column("ip", width=120)
        self.tree.column("mac", width=150)
        self.tree.column("info", width=150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons = [
            ("Escanear Red", self.update_device_list),
            ("Encender (WoL)", lambda: self.handle_selection("wol")),
            ("Apagar Equipos", lambda: self.handle_selection("shutdown")),
            ("Reiniciar Equipos", lambda: self.handle_selection("restart")),
            ("Conectar por RDP", lambda: self.handle_selection("rdp"))
        ]
        
        for text, command in buttons:
            ttk.Button(
                button_frame,
                text=text,
                command=command
            ).pack(side=tk.LEFT, padx=5)
        
        # Barra de estado
        self.status_var = tk.StringVar(value="Listo")
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            relief=tk.SUNKEN
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Eventos
        self.tree.bind('<Button-1>', self.handle_click)
        # Crear menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        # Asociar el clic derecho con el menú contextual
        self.tree.bind("<Button-3>", self.favorites_manager.show_context_menu)
            
    def setup_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        
        # Menú Ver
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_command(label="Ver registro de actividad", command=self.show_activity_log)
        view_menu.add_command(label="Ver Favoritos", command=self.favorites_manager.show_favorites_window)

         # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Cambiar usuario", command=lambda: change_admin_user(self))
        tools_menu.add_separator()
        tools_menu.add_command(label="Exportar favoritos", command=lambda: export_favorites(self))
        tools_menu.add_command(label="Importar favoritos", command=lambda: import_favorites(self))

            # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Buscar actualizaciones", command=run_updater)
        help_menu.add_command(label="Acerca de", command=self.open_about_window)

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'favorites': []}
    
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump({'favorites': self.favorites_manager.favorite_devices}, f)
    
    def filter_devices(self, *args):
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().lower()
        
        for ip, mac in self.all_devices:
            # Verificar si el dispositivo está en favoritos
            is_favorite = self.favorites_manager.is_favorite(ip)
            fav_name = None
            
            if is_favorite:
                fav_name = self.favorites_manager.get_favorite_name(ip)
            
            if ((not self.show_favorites.get() or is_favorite) and
                (search_term in ip.lower() or search_term in mac.lower() or 
                    (fav_name and search_term in fav_name.lower()))):
                
                # Agregar estrella e información si es favorito
                info = f"★ {fav_name}" if is_favorite else ""
                
                item = self.tree.insert("", "end", values=("☐", ip, mac, info))
                self.device_vars[item] = False

    def handle_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":
                item = self.tree.identify_row(event.y)
                if item in self.device_vars:
                    self.device_vars[item] = not self.device_vars.get(item, False)
                    self.update_checkbox(item)

    def update_checkbox(self, item):
        checked = "☒" if self.device_vars[item] else "☐"
        self.tree.set(item, "check", checked)

    def update_device_list(self):
        # Eliminar todos los dispositivos previos en la interfaz
        self.tree.delete(*self.tree.get_children())  
        self.device_vars.clear()
        
        # Limpiar la lista antes de actualizar
        self.all_devices = []  
        
        # Obtener los dispositivos únicos de la red
        devices = get_mac_ip_list()
        unique_devices = list(devices)  # Lista de dispositivos únicos
        
        if not unique_devices:
            messagebox.showwarning("Escaneo", "No se encontraron dispositivos en la red.")
            log_action("Escanear red", "Error", "No se encontraron dispositivos")
            return
        
        # Reiniciar la barra de búsqueda
        self.search_var.set("")
        self.all_devices = unique_devices
        
        # Mostrar los dispositivos en la interfaz
        self.filter_devices()
   
    def handle_selection(self, action):
        selected_items = [
            self.tree.item(item)["values"][1] 
            for item in self.device_vars 
            if self.device_vars[item]
        ]
        
        if not selected_items:
            messagebox.showwarning(
                "Selección",
                "Por favor, selecciona al menos un equipo."
            )
            return
        
        def process_devices():
            if action == "wol":
                for ip in selected_items:
                    mac = next((m for i, m in self.all_devices if i == ip), None)
                    if mac:
                        wake_on_lan(mac)
            elif action == "shutdown":
                shutdown_remote(selected_items)  # 🔹 Enviar lista completa de IPs
            elif action == "restart":
                restart_remote(selected_items)  # 🔹 Enviar lista completa de IPs
            elif action == "rdp":
                for ip in selected_items:
                    connect_rdp(ip)

            self.after(0, lambda: messagebox.showinfo("Acción completada", 
                    f"Acción {action} ejecutada en los equipos seleccionados."))

        threading.Thread(target=process_devices, daemon=True).start()

    def _update_ui_after_action(self, results, action):
        """Actualiza la UI con el resultado de cada intento."""
        for item, status_text, status_color in results:
            if self.tree.exists(item):  # Verificar que el item existe en la tabla antes de actualizar
                self.tree.item(item, values=(status_text,))
                self.tree.tag_configure("red", foreground="red")
                self.tree.item(item, tags=("red",) if status_color == "red" else ())
            else:
                print(f"Error: Item {item} no encontrado en Treeview")

        self.status_var.set("Listo")

        
    def open_about_window(self):
        about = AboutWindow(self)
        about.grab_set()
    
    def show_activity_log(self):
        create_logging_window()
    
    def on_closing(self):
            # Realiza cualquier limpieza necesaria aquí
            #logging.shutdown()
            self.destroy()
def run_updater():
    """Ejecuta el actualizador en un proceso independiente sin bloquear la GUI."""
    updater_path = os.path.join(os.getcwd(), "WoLlama_Updater.exe")
    
    if os.path.exists(updater_path):
        def launch_updater():
            subprocess.Popen([updater_path], shell=True)
           # os._exit(0)  # Cierra la aplicación principal después de lanzar el actualizador
        
        threading.Thread(target=launch_updater, daemon=True).start()
    else:
        messagebox.showerror("Error", "El actualizador no se encuentra.")
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()