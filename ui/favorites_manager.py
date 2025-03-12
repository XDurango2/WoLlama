# gui/favorites_manager.py
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import threading
from utils.logger import log_action
from utils.network import wake_on_lan, shutdown_remote, restart_remote, connect_rdp
from config.setup import fernet_key, encrypt_data, decrypt_data
class FavoritesManager:
    def __init__(self, parent):
        self.parent = parent
        self.favorite_devices = self.load_favorites()
        
    def load_favorites(self):
        """Carga la lista de favoritos desde un archivo JSON encriptado."""
        if os.path.exists("favorites.json"):
            with open("favorites.json", "r") as f:
                encrypted_data = json.load(f).get("favorites", "")
                if encrypted_data:
                    decrypted_data = decrypt_data(encrypted_data, fernet_key)
                    return decrypted_data  # Devuelve los datos desencriptados
        return []

    def save_favorites(self):
        """Guarda la lista de favoritos en un archivo JSON encriptado."""
        encrypted_favorites = encrypt_data(self.favorite_devices, fernet_key)
        with open("favorites.json", "w") as f:
            json.dump({"favorites": encrypted_favorites}, f)
            
    def is_favorite(self, ip):
        """Comprueba si un dispositivo es favorito por su IP."""
        return any(device['ip'] == ip for device in self.favorite_devices)
    
    def get_favorite_name(self, ip):
        """Obtiene el nombre de un dispositivo favorito por su IP."""
        for device in self.favorite_devices:
            if device['ip'] == ip:
                return device.get('name', f"Dispositivo {ip}")
        return None
    
    def toggle_favorite(self, ip=None, mac=None, event=None):
        """Marca o desmarca una IP como favorita."""
        if event:  # Si se llamó desde un clic
            item = self.parent.tree.identify_row(event.y)
            if not item:
                return
            ip = self.parent.tree.item(item, "values")[1]
            mac = self.parent.tree.item(item, "values")[2]
        elif not ip:  # Si no hay IP ni evento
            return
        
        # Buscar si el dispositivo ya está en favoritos
        favorite_device = next((device for device in self.favorite_devices if device['ip'] == ip), None)
        
        if favorite_device:
            self.favorite_devices.remove(favorite_device)
            log_action("Favorito", ip, "Desmarcado")
        else:
            # Crear un cuadro de diálogo para ingresar el nombre del dispositivo
            device_name = simpledialog.askstring(
                "Nombre del dispositivo", 
                f"Ingrese un nombre para el dispositivo {ip}:",
                parent=self.parent
            )
            
            # Si no se proporciona un nombre, usar la IP como nombre predeterminado
            if not device_name:
                device_name = f"Dispositivo {ip}"
            
            # Agregar a favoritos con el nombre
            self.favorite_devices.append({
                'ip': ip, 
                'mac': mac, 
                'name': device_name
            })
            log_action("Favorito", ip, f"Marcado como '{device_name}'")
        
        self.save_favorites()
        self.parent.filter_devices()  # Actualizar la lista de dispositivos
    
    def show_context_menu(self, event):
        """Muestra el menú contextual al hacer clic derecho en un ítem de la tabla."""
        item = self.parent.tree.identify_row(event.y)
        if not item:
            return  # Si no hay un ítem seleccionado, salir
        
        ip = self.parent.tree.item(item, "values")[1]  # Obtener la IP
        mac = self.parent.tree.item(item, "values")[2]  # Obtener la MAC
        self.selected_item = (ip, mac)  # Guardar la IP y MAC seleccionadas
        
        # Borrar el menú actual y agregar la opción correcta
        self.parent.context_menu.delete(0, tk.END)
        
        # Verificar si está en favoritos
        is_favorite = self.is_favorite(ip)
        
        if is_favorite:
            self.parent.context_menu.add_command(label="Quitar de favoritos", command=self.toggle_favorite_from_menu)
        else:
            self.parent.context_menu.add_command(label="Marcar como favorito", command=self.toggle_favorite_from_menu)
        
        # Mostrar el menú en la posición del clic
        self.parent.context_menu.post(event.x_root, event.y_root)

    def toggle_favorite_from_menu(self):
        """Llama a toggle_favorite() para marcar/desmarcar desde el menú contextual."""
        if hasattr(self, "selected_item"):
            ip, mac = self.selected_item
            self.toggle_favorite(ip=ip, mac=mac)

    def show_favorites_window(self):
        """Muestra una ventana con la lista de dispositivos favoritos."""
        favorites_window = tk.Toplevel(self.parent)
        favorites_window.title("Dispositivos Favoritos")
        favorites_window.geometry("600x300")
        
        # Frame principal
        main_frame = ttk.Frame(favorites_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear un Treeview para mostrar los favoritos
        favorites_tree = ttk.Treeview(main_frame, columns=("Nombre", "IP", "MAC", "Estado"), show="headings")
        
        # Configurar las columnas
        favorites_tree.heading("Nombre", text="Nombre")
        favorites_tree.heading("IP", text="IP")
        favorites_tree.heading("MAC", text="MAC")
        favorites_tree.heading("Estado", text="Estado")
        favorites_tree.column("Nombre", width=150)
        favorites_tree.column("IP", width=120)
        favorites_tree.column("MAC", width=180)
        favorites_tree.column("Estado", width=100)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=favorites_tree.yview)
        favorites_tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar el árbol y el scrollbar
        favorites_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Función para actualizar la lista de favoritos
        def update_favorites_list():
            # Limpiar el árbol
            favorites_tree.delete(*favorites_tree.get_children())
            # Rellenar con la lista actualizada
            for device in self.favorite_devices:
                ip = device['ip']
                mac = device['mac']
                name = device.get('name', f"Dispositivo {ip}")
                # Verificar si el dispositivo está en línea
                online = any(dev_ip == ip for dev_ip, _ in self.parent.all_devices)
                estado = "En línea" if online else "Desconectado"
                favorites_tree.insert("", "end", values=(name, ip, mac, estado))
        
        # Función para remover un favorito
        def remove_favorite():
            selected_item = favorites_tree.selection()
            if not selected_item:
                messagebox.showwarning("Selección", "Por favor, seleccione un dispositivo para remover.")
                return
            
            ip = favorites_tree.item(selected_item[0])['values'][1]
            # Buscar y eliminar el dispositivo favorito
            favorite_device = next((device for device in self.favorite_devices if device['ip'] == ip), None)
            if favorite_device:
                self.favorite_devices.remove(favorite_device)
                self.save_favorites()
                log_action("Favorito", ip, "Removido de favoritos")
                update_favorites_list()
                # Actualizar la vista principal si está en modo "Solo Favoritos"
                if self.parent.show_favorites.get():
                    self.parent.filter_devices()
        
        # Función para editar el nombre de un favorito
        def edit_favorite_name():
            selected_item = favorites_tree.selection()
            if not selected_item:
                messagebox.showwarning("Selección", "Por favor, seleccione un dispositivo para editar.")
                return
            
            values = favorites_tree.item(selected_item[0])['values']
            current_name = values[0]
            ip = values[1]
            
            # Solicitar nuevo nombre
            new_name = simpledialog.askstring(
                "Editar nombre", 
                "Ingrese el nuevo nombre para el dispositivo:",
                initialvalue=current_name,
                parent=favorites_window
            )
            
            if new_name:
                # Actualizar el nombre en la lista de favoritos
                for device in self.favorite_devices:
                    if device['ip'] == ip:
                        device['name'] = new_name
                        break
                
                self.save_favorites()
                log_action("Favorito", ip, f"Nombre actualizado a '{new_name}'")
                update_favorites_list()
                # Actualizar la vista principal
                self.parent.filter_devices()
        
        # Función para mostrar menú de acciones
        def show_actions_menu(event):
            selected_item = favorites_tree.selection()
            if not selected_item:
                return
            
            values = favorites_tree.item(selected_item[0])['values']
            name = values[0]
            ip = values[1]
            mac = values[2]
            
            # Crear menú contextual para acciones
            actions_menu = tk.Menu(favorites_window, tearoff=0)
            actions_menu.add_command(label=f"Editar nombre: {name}", 
                                    command=edit_favorite_name)
            actions_menu.add_separator()
            actions_menu.add_command(label="Encender (WoL)", 
                                    command=lambda: perform_action("wol", ip, mac, name))
            actions_menu.add_command(label="Apagar Equipo", 
                                    command=lambda: perform_action("shutdown", ip, mac, name))
            actions_menu.add_command(label="Reiniciar Equipo", 
                                    command=lambda: perform_action("restart", ip, mac, name))
            actions_menu.add_command(label="Conectar por RDP", 
                                    command=lambda: perform_action("rdp", ip, mac, name))
            
            # Mostrar el menú en la posición del clic
            actions_menu.post(event.x_root, event.y_root)
        
        # Función para realizar la acción seleccionada
        def perform_action(action, ip, mac, name):
            def process_action():
                if action == "wol":
                    wake_on_lan(mac)
                    log_action("Wake-on-LAN", name, f"({ip}) Enviado desde favoritos")
                elif action == "shutdown":
                    shutdown_remote([ip])
                    log_action("Apagar", name, f"({ip}) Enviado desde favoritos")
                elif action == "restart":
                    restart_remote([ip])
                    log_action("Reiniciar", name, f"({ip}) Enviado desde favoritos")
                elif action == "rdp":
                    connect_rdp(ip)
                    log_action("Conexión RDP", name, f"({ip}) Iniciada desde favoritos")
                
                # Mostrar mensaje de confirmación
                favorites_window.after(0, lambda: messagebox.showinfo("Acción completada", 
                    f"Acción {action} ejecutada en '{name}' ({ip})."))
            
            # Ejecutar en un hilo separado para no bloquear la interfaz
            threading.Thread(target=process_action, daemon=True).start()
        
        # Frame para botones
        button_frame = ttk.Frame(favorites_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botones
        remove_button = ttk.Button(button_frame, text="Remover de Favoritos", command=remove_favorite)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        edit_button = ttk.Button(button_frame, text="Editar Nombre", command=edit_favorite_name)
        edit_button.pack(side=tk.LEFT, padx=5)
        
        close_button = ttk.Button(button_frame, text="Cerrar", command=favorites_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Asociar doble clic a mostrar menú de acciones
        favorites_tree.bind("<Button-3>", show_actions_menu)
        
        # Llenar inicialmente la lista
        update_favorites_list()
        
        # Hacer la ventana modal
        favorites_window.transient(self.parent)
        favorites_window.grab_set()