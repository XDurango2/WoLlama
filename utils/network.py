import socket
import subprocess
import re

from config.setup import ADMIN_USER  # 🔹 Asegúrate de importar la función get_config
from utils.logger import log_action  # 🔹 Asegúrate de importar la función de logging



def get_mac_ip_list():
    devices = []
    try:
        result = subprocess.run("arp -a", capture_output=True, text=True, shell=True)
        for line in result.stdout.split("\n"):
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w-]+)", line)
            if match:
                ip, mac = match.groups()
                if mac != "ff-ff-ff-ff-ff-ff" and not ip.startswith(("239.", "224.")):
                    devices.append((ip, mac))

        log_action("Escanear red", "Todos", f"Encontrados {len(devices)} dispositivos")  # 🔹 Log exitoso
        return sorted(devices, key=lambda x: socket.inet_aton(x[0]))
    
    except Exception as e:
        log_action("Escanear red", "Error", str(e))  # 🔹 Log de error
        return []
def wake_on_lan(mac_address):
    try:
        mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, ("255.255.255.255", 9))
        sock.close()

        log_action("WoL", mac_address, "Success")  # 🔹 Log exitoso
        return True, "Success"
    
    except Exception as e:
        log_action("WoL", mac_address, f"Error: {str(e)}")  # 🔹 Log de error
        return False, str(e)

def shutdown_remote(ips):
    try:
        if isinstance(ips, list):  # 🔹 Convertir la lista de IPs en una cadena separada por comas
            ips = ",".join(ips)

        command = f'powershell -Command "Stop-Computer -ComputerName {ips} -Force -Credential {ADMIN_USER}"'
        print(command)
        #subprocess.run(command, shell=True)

        log_action("Shutdown", ips, "Success")  # 🔹 Log exitoso
        return True, "Success"
    
    except Exception as e:
        log_action("Shutdown", ips, f"Error: {str(e)}")  # 🔹 Log de error
        return False, str(e)


    except subprocess.CalledProcessError as e:
        log_action("Shutdown", ", ".join(ips) if isinstance(ips, list) else ips, f"Error: {str(e)}")
        return False, str(e)
    
def restart_remote(ips):
    try:
        if isinstance(ips, list):  # 🔹 Convertir la lista de IPs en una cadena separada por comas
            ips = ",".join(ips)

        command = f'powershell -Command "Restart-Computer -ComputerName {ips} -Force -Credential {ADMIN_USER}"'
        subprocess.run(command, shell=True)

        log_action("Restart", ips, "Success")  # 🔹 Log exitoso
        return True, "Success"
    
    except Exception as e:
        log_action("Restart", ips, f"Error: {str(e)}")  # 🔹 Log de error
        return False, str(e)


def connect_rdp(ip):
    try:
        command = f"mstsc /v:{ip}"
        subprocess.Popen(command, shell=True)

        log_action("RDP", ip, "Success")  # 🔹 Log exitoso
        return True, "Success"
    
    except Exception as e:
        log_action("RDP", ip, f"Error: {str(e)}")  # 🔹 Log de error
        return False, str(e)