import tkinter as tk
from tkinter import messagebox
import subprocess
import socket
import struct
import os
import re
import threading

# Configuración de usuario administrador predefinido
ADMIN_USER = "FDM-soporte"  # Cambia esto según tu configuración

# Función para escanear la red y obtener MACs e IPs, excluyendo direcciones de multidifusión
def get_mac_ip_list():
    devices = []
    
    result = subprocess.run("arp -a", capture_output=True, text=True, shell=True)
    
    for line in result.stdout.split("\n"):
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]+)", line)
        if match:
            ip, mac = match.groups()
            if mac != "ff-ff-ff-ff-ff-ff":  # Filtrar broadcasts
                # Excluir direcciones de multidifusión
                if not ip.startswith("239.") and not ip.startswith("224."):
                    devices.append((ip, mac))
    
    # Ordenar las direcciones IP de menor a mayor
    devices.sort(key=lambda x: socket.inet_aton(x[0]))
    
    return devices

# Función para enviar Wake-on-LAN
def wake_on_lan(mac_address):
    try:
        mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
        magic_packet = b'\xff' * 6 + mac_bytes * 16

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ("255.255.255.255", 9))
        sock.close()

        messagebox.showinfo("WoL", f"Paquete Wake-on-LAN enviado a {mac_address}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo enviar WoL: {e}")

# Función para apagar un equipo remoto con la solicitud de credenciales de Windows
def shutdown_remote(ip):
    try:
        command = f'powershell -Command "Stop-Computer -ComputerName {ip} -Force -Credential {ADMIN_USER}"'
        subprocess.run(command, shell=True)
        messagebox.showinfo("Apagado", f"Orden de apagado enviada a {ip}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo apagar el equipo: {e}")

# Función para conectarse por RDP
def connect_rdp(ip):
    try:
        command = f"mstsc /v:{ip}"
        os.system(command)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar por RDP: {e}")

# Función para actualizar la lista de dispositivos
def update_device_list():
    device_listbox.delete(0, tk.END)
    devices = get_mac_ip_list()
    
    if not devices:
        messagebox.showwarning("Escaneo", "No se encontraron dispositivos en la red.")
    
    for ip, mac in devices:
        device_listbox.insert(tk.END, f"{ip} - {mac}")

# Función para apagar el equipo en un hilo separado
def shutdown_thread(ip):
    threading.Thread(target=shutdown_remote, args=(ip,)).start()

# Crear la ventana principal
root = tk.Tk()
root.title("Control Remoto - WoL, Apagado & RDP")
root.geometry("500x350")

# Etiqueta principal
tk.Label(root, text="Equipos en la Red", font=("Arial", 14)).pack(pady=5)

# Lista de dispositivos
device_listbox = tk.Listbox(root, width=50, height=10)
device_listbox.pack(pady=5)

# Botón para actualizar lista
tk.Button(root, text="Escanear Red", command=update_device_list, font=("Arial", 12), bg="blue", fg="white").pack(pady=5)

# Botón para encender equipo (WoL)
tk.Button(root, text="Encender (WoL)", command=lambda: wake_on_lan(device_listbox.get(tk.ACTIVE).split(" - ")[1]), font=("Arial", 12), bg="green", fg="white").pack(pady=5)

# Botón para apagar equipo remoto
tk.Button(root, text="Apagar Equipo", command=lambda: shutdown_thread(device_listbox.get(tk.ACTIVE).split(" - ")[0]), font=("Arial", 12), bg="red", fg="white").pack(pady=5)

# Botón para conectarse por RDP
tk.Button(root, text="Conectar por RDP", command=lambda: connect_rdp(device_listbox.get(tk.ACTIVE).split(" - ")[0]), font=("Arial", 12), bg="purple", fg="white").pack(pady=5)

# Ejecutar la interfaz
update_device_list()
root.mainloop()
