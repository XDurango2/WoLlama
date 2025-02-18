import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import socket
import struct
import os
import re
import threading

# Configuración de usuario administrador predefinido
ADMIN_USER = "FDM-soporte"

class RemoteControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control Remoto - WoL, Apagado & RDP")
        self.root.geometry("600x400")
        
        self.device_vars = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Crear el frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear Treeview con columna de checkbox
        self.tree = ttk.Treeview(main_frame, columns=("check", "ip", "mac"), show="headings", height=10)
        self.tree.heading("check", text="")
        self.tree.heading("ip", text="Dirección IP")
        self.tree.heading("mac", text="Dirección MAC")
        
        # Configurar anchos de columna
        self.tree.column("check", width=30, anchor="center")
        self.tree.column("ip", width=150)
        self.tree.column("mac", width=150)
        
        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Empaquetar elementos
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botones de acción
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Escanear Red", command=self.update_device_list).pack(pady=2)
        ttk.Button(button_frame, text="Encender (WoL)", command=lambda: self.handle_selection("wol")).pack(pady=2)
        ttk.Button(button_frame, text="Apagar Equipos", command=lambda: self.handle_selection("shutdown")).pack(pady=2)
        ttk.Button(button_frame, text="Reiniciar Equipos", command=lambda: self.handle_selection("restart")).pack(pady=2)
        ttk.Button(button_frame, text="Conectar por RDP", command=lambda: self.handle_selection("rdp")).pack(pady=2)
        
        # Vincular evento de clic
        self.tree.bind('<Button-1>', self.handle_click)
        
    def handle_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # Columna del checkbox
                item = self.tree.identify_row(event.y)
                if item in self.device_vars:
                    self.device_vars[item] = not self.device_vars.get(item, False)
                    self.update_checkbox(item)
    
    def update_checkbox(self, item):
        checked = "☒" if self.device_vars[item] else "☐"
        self.tree.set(item, "check", checked)
    
    def get_mac_ip_list(self):
        devices = []
        result = subprocess.run("arp -a", capture_output=True, text=True, shell=True)
        for line in result.stdout.split("\n"):
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]+)", line)
            if match:
                ip, mac = match.groups()
                if mac != "ff-ff-ff-ff-ff-ff" and not ip.startswith(("239.", "224.")):
                    devices.append((ip, mac))
        return sorted(devices, key=lambda x: socket.inet_aton(x[0]))
    
    def update_device_list(self):
        self.tree.delete(*self.tree.get_children())
        self.device_vars.clear()
        
        devices = self.get_mac_ip_list()
        if not devices:
            messagebox.showwarning("Escaneo", "No se encontraron dispositivos en la red.")
            return
            
        for ip, mac in devices:
            item = self.tree.insert("", "end", values=("☐", ip, mac))
            self.device_vars[item] = False
    
    def handle_selection(self, action):
        selected_items = [self.tree.item(item)["values"][1] 
                         for item in self.device_vars 
                         if self.device_vars[item]]
        
        if not selected_items:
            messagebox.showwarning("Selección", "Por favor, selecciona al menos un equipo.")
            return
            
        if action == "wol":
            for ip in selected_items:
                mac = next(self.tree.item(item)["values"][2] 
                          for item in self.device_vars 
                          if self.tree.item(item)["values"][1] == ip)
                threading.Thread(target=self.wake_on_lan, args=(mac,)).start()
        elif action in ["shutdown", "restart"]:
            # Unir las IPs con comas para el comando
            ips = ",".join(selected_items)
            if action == "shutdown":
                threading.Thread(target=self.shutdown_remote, args=(ips,)).start()
            else:
                threading.Thread(target=self.restart_remote, args=(ips,)).start()
        elif action == "rdp":
            # RDP solo puede conectarse a un equipo a la vez
            if len(selected_items) > 1:
                messagebox.showwarning("RDP", "Solo se puede conectar a un equipo a la vez por RDP.")
                return
            threading.Thread(target=self.connect_rdp, args=(selected_items[0],)).start()
    
    def wake_on_lan(self, mac_address):
        try:
            mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
            magic_packet = b'\xff' * 6 + mac_bytes * 16
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, ("255.255.255.255", 9))
            sock.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo enviar WoL: {e}")
    
    def shutdown_remote(self, ips):
        try:
            command = f'powershell -Command "Stop-Computer -ComputerName {ips} -Force -Credential {ADMIN_USER}"'
            subprocess.run(command, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo apagar los equipos: {e}")
    
    def restart_remote(self, ips):
        try:
            command = f'powershell -Command "Restart-Computer -ComputerName {ips} -Force -Credential {ADMIN_USER}"'
            subprocess.run(command, shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reiniciar los equipos: {e}")
    
    def connect_rdp(self, ip):
        try:
            command = f"mstsc /v:{ip}"
            os.system(command)
            threading.Timer(10, lambda: subprocess.run(f'psexec \\{ip} logoff', shell=True)).start()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar por RDP a {ip}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteControlApp(root)
    root.mainloop()