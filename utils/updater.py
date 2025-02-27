import os
import subprocess
import threading
import requests
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from config.constants import APP_VERSION as CURRENT_VERSION
from config.constants import APP_URL as VERSION_URL

def download_and_install(url, save_path="update.exe"):
    """Descarga la nueva versión y la ejecuta automáticamente"""
    
    def download():
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            messagebox.showinfo("Actualización descargada", "La nueva versión ha sido descargada.\n\nSe procederá a instalarla.")

            # Ejecutar el instalador
            subprocess.Popen([save_path], shell=True)

            # Cerrar la aplicación actual
            os._exit(0)

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error al descargar la actualización: {e}")

    # Ejecuta la descarga en un hilo separado para no bloquear la GUI
    threading.Thread(target=download, daemon=True).start()

def parse_version(version_str):
    """ Extrae los números de la versión y los convierte en una tupla (1,1,0) """
    numbers = re.findall(r'\d+', version_str)  # Encuentra solo los números
    return tuple(map(int, numbers)) if numbers else (0,)

def check_for_updates_gui(root):
    """Verifica actualizaciones en GitHub y muestra un mensaje en la GUI"""
    try:
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        latest_release = response.json()

        latest_version_raw = latest_release.get("tag_name", "0.0.0")  # Ej: "1.2.3-Beta"
        latest_version = parse_version(latest_version_raw)
        current_version = parse_version(CURRENT_VERSION)

        release_name = latest_release.get("name", "Nueva versión")  # Nombre completo del release
        is_prerelease = latest_release.get("prerelease", False)  # ¿Es una versión preliminar?
        download_url = latest_release["html_url"]  # URL de descarga en GitHub

        if latest_version > current_version:
            update_window = tk.Toplevel(root)
            update_window.title("Actualización disponible")
            update_window.geometry("350x150")

            message = f"Una nueva versión {release_name} ({latest_version_raw}) está disponible.\n\n"
            if is_prerelease:
                message += "⚠️ Esta es una versión preliminar (Beta/Pre-release)\n\n"

            label = tk.Label(update_window, text=message, padx=10, pady=10, wraplength=320, justify="left")
            label.pack()

            button = ttk.Button(update_window, text="Actualizar ahora", command=lambda: download_and_install(download_url))
            button.pack(pady=10)
        else:
            messagebox.showinfo("Sin actualizaciones", "Ya tienes la versión más reciente.")
    
    except requests.RequestException as e:
        messagebox.showerror("Error", f"No se pudo buscar actualizaciones.\nError: {e}")

# 📌 Ejemplo de integración en Tkinter
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal
check_for_updates_gui(root)
