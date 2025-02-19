# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
from config.constants import APP_NAME, APP_VERSION
from utils.network import get_mac_ip_list, wake_on_lan, shutdown_remote, restart_remote, connect_rdp
from utils.logger import create_logging_window,log_action
from .about_window import AboutWindow

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("800x400")
        
        self.device_vars = {}
        self.all_devices = []
        self.app_config = self.load_config()
        self.favorite_devices = self.load_favorites()
        
        self.setup_ui()
        self.setup_menu()
        
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
        
        # Tabla de dispositivos
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("check", "ip", "mac"),
            show="headings",
            height=10
        )
        
        self.tree.heading("check", text="")
        self.tree.heading("ip", text="Dirección IP")
        self.tree.heading("mac", text="Dirección MAC")
        
        self.tree.column("check", width=30, anchor="center")
        self.tree.column("ip", width=150)
        self.tree.column("mac", width=150)
        
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
        # 🔹 Crear menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        # 🔹 Asociar el clic derecho con la función toggle_favorite
        self.tree.bind("<Button-3>", self.show_context_menu)
            
    def setup_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        #file_menu.add_command(label="Exportar dispositivos", command=self.export_devices)
        #file_menu.add_command(label="Importar dispositivos", command=self.import_devices)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        
        # Menú Ver
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_command(label="Ver registro de actividad", command=self.show_activity_log)
        view_menu.add_command(label="Ver Favoritos", command=self.show_favorites_window)

        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
       # tools_menu.add_command(label="Ping masivo", command=self.mass_ping)
       # tools_menu.add_command(label="Verificar puertos", command=self.check_ports)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.open_about_window)

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'favorites': []}
    
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump({'favorites': self.favorite_devices}, f)
    
    def filter_devices(self, *args):
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().lower()
        
        for ip, mac in self.all_devices:
            if ((not self.show_favorites.get() or ip in self.favorite_devices) and
                (search_term in ip.lower() or search_term in mac.lower())):
                item = self.tree.insert("", "end", values=("☐", ip, mac))
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
        # 🔹 1. Eliminar todos los dispositivos previos en la interfaz
        self.tree.delete(*self.tree.get_children())  
        self.device_vars.clear()
        
        # 🔹 2. Limpiar la lista antes de actualizar
        self.all_devices = []  
        
        # 🔹 3. Obtener los dispositivos únicos de la red
        devices = get_mac_ip_list()
        unique_devices = list(devices)  # Evita duplicados usando set()

        if not unique_devices:
            messagebox.showwarning("Escaneo", "No se encontraron dispositivos en la red.")
            log_action("Escanear red", "Error", "No se encontraron dispositivos")
            return
        
        # 🔹 4. Insertar los dispositivos detectados en la interfaz
        self.search_var.set("")  # Reiniciar la barra de búsqueda
        self.all_devices = unique_devices  # Guardar dispositivos sin duplicados

        for ip, mac in unique_devices:
            item = self.tree.insert("", "end", values=("☐", ip, mac))
            self.device_vars[item] = False
    def load_favorites(self):
        """Carga la lista de favoritos desde un archivo JSON."""
        if os.path.exists("favorites.json"):
            with open("favorites.json", "r") as f:
                return json.load(f)
        return []
    
    def save_favorites(self):
        """Guarda la lista de favoritos en un archivo JSON."""
        with open("favorites.json", "w") as f:
            json.dump(self.favorite_devices, f)

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
            
        for ip in selected_items:
            mac = next((m for i, m in self.all_devices if i == ip), None)
            if action == "wol" and mac:
                wake_on_lan(mac)
            elif action == "shutdown":
                shutdown_remote(ip)
            elif action == "restart":
                restart_remote(ip)
            elif action == "rdp":
                connect_rdp(ip)

        messagebox.showinfo("Acción completada", f"Acción {action} ejecutada.")
    
    def export_devices(self):
        messagebox.showinfo("Exportar", "Exportando lista de dispositivos...")
    def import_devices(self):
        messagebox.showinfo("Importar", "Importando lista de dispositivos...")
    def open_about_window(self):
        about = AboutWindow(self)
        about.grab_set()  # Para que la ventana de "Acerca de" esté en primer plano
    def show_activity_log(self):
        live_log=create_logging_window()
    
    def toggle_favorite(self, ip=None, event=None):
        """Marca o desmarca una IP como favorita."""
        if event:  # Si se llamó desde un clic
            item = self.tree.identify_row(event.y)
            if not item:
                return
            ip = self.tree.item(item, "values")[1]
        elif not ip:  # Si no hay IP ni evento
            return

        if ip in self.favorite_devices:
            self.favorite_devices.remove(ip)
        else:
            self.favorite_devices.append(ip)

        self.save_favorites()
        log_action("Favorito", ip, "Marcado" if ip in self.favorite_devices else "Desmarcado")

    def show_context_menu(self, event):
        """Muestra el menú contextual al hacer clic derecho en un ítem de la tabla."""
        item = self.tree.identify_row(event.y)
        if not item:
            return  # Si no hay un ítem seleccionado, salir

        ip = self.tree.item(item, "values")[1]  # Obtener la IP
        self.selected_item = ip  # Guardar la IP seleccionada

        # 🔹 Borrar el menú actual y agregar la opción correcta
        self.context_menu.delete(0, tk.END)

        if ip in self.favorite_devices:
            self.context_menu.add_command(label="Quitar de favoritos", command=self.toggle_favorite_from_menu)
        else:
            self.context_menu.add_command(label="Marcar como favorito", command=self.toggle_favorite_from_menu)

        # 🔹 Mostrar el menú en la posición del clic
        self.context_menu.post(event.x_root, event.y_root)

    def toggle_favorite_from_menu(self):
        """Llama a toggle_favorite() para marcar/desmarcar desde el menú contextual."""
        if hasattr(self, "selected_item"):
            self.toggle_favorite(ip=self.selected_item)

    def show_favorites_window(self):
        """Muestra una ventana con la lista de dispositivos favoritos."""
        favorites_window = tk.Toplevel(self)
        favorites_window.title("Dispositivos Favoritos")
        favorites_window.geometry("400x300")

        # Función para actualizar la lista de favoritos
        def update_favorites_list():
            # Limpiar el árbol
            favorites_tree.delete(*favorites_tree.get_children())
            # Rellenar con la lista actualizada
            for ip in self.favorite_devices:
                estado = "En línea" if ip in [dev[0] for dev in self.all_devices] else "Desconectado"
                favorites_tree.insert("", "end", values=(ip, estado))

        # Función para remover un favorito
        def remove_favorite():
            selected_item = favorites_tree.selection()
            if not selected_item:
                messagebox.showwarning("Selección", "Por favor, seleccione un dispositivo para remover.")
                return
            
            ip = favorites_tree.item(selected_item[0])['values'][0]
            if ip in self.favorite_devices:
                self.favorite_devices.remove(ip)
                self.save_favorites()
                log_action("Favorito", ip, "Removido de favoritos")
                update_favorites_list()
                # Actualizar la vista principal si está en modo "Solo Favoritos"
                if self.show_favorites.get():
                    self.filter_devices()

        # Frame principal
        main_frame = ttk.Frame(favorites_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Crear un Treeview para mostrar los favoritos
        favorites_tree = ttk.Treeview(main_frame, columns=("IP", "Estado"), show="headings")
        
        # Configurar las columnas
        favorites_tree.heading("IP", text="IP")
        favorites_tree.heading("Estado", text="Estado")
        favorites_tree.column("IP", width=200)
        favorites_tree.column("Estado", width=100)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=favorites_tree.yview)
        favorites_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar el árbol y el scrollbar
        favorites_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame para botones
        button_frame = ttk.Frame(favorites_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones
        remove_button = ttk.Button(button_frame, text="Remover de Favoritos", command=remove_favorite)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        close_button = ttk.Button(button_frame, text="Cerrar", command=favorites_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Llenar inicialmente la lista
        update_favorites_list()
        
        # Hacer la ventana modal
        favorites_window.transient(self)
        favorites_window.grab_set()
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
