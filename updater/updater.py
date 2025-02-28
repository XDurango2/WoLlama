import os
import subprocess
import shutil
import requests
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Rutas y configuración
APP_DIR = os.path.dirname(os.path.abspath(sys.executable))  # Carpeta de instalación
UPDATE_TEMP_DIR = os.path.join(os.environ.get("TEMP", APP_DIR), "update_temp")  # Carpeta temporal
EXECUTABLE_NAME = "WoLlama.exe"  # Nombre del ejecutable principal
UPDATE_EXE_NAME = "WoLlama_update.exe"  # Nombre del archivo descargado
GITHUB_RELEASE_URL = "https://api.github.com/repos/XDurango2/WoLlama/releases/latest"
class UpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WoLlama Updater")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        # Mensaje de estado
        self.status_label = tk.Label(root, text="Verificando actualizaciones...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, length=300, mode="determinate")
        self.progress_bar.pack(pady=10)

        # Botón de actualización
        self.update_button = ttk.Button(root, text="Actualizar ahora", command=self.start_update)
        self.update_button.pack(pady=10)

        # Iniciar la verificación de actualizaciones en segundo plano
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def check_for_updates(self):
        """Verifica si hay una nueva versión disponible en GitHub."""
        try:
            response = requests.get(GITHUB_RELEASE_URL, timeout=10)
            response.raise_for_status()
            latest_release = response.json()

            latest_version = latest_release.get("tag_name", "0.0.0")
            current_version = "1.0.0"  # Puedes cambiar esto para que lo lea desde un archivo

            if latest_version > current_version:
                self.status_label.config(text=f"Nueva versión disponible: {latest_version}")
            else:
                self.status_label.config(text="No hay actualizaciones disponibles")
                messagebox.showinfo("Actualización", "Ya tienes la última versión.")
                self.root.destroy()
        except requests.RequestException as e:
            self.status_label.config(text="Error al buscar actualización")
            messagebox.showerror("Error", f"No se pudo conectar al servidor.\n{e}")
            self.root.destroy()

    def start_update(self):
        """Inicia la descarga y actualización."""
        self.update_button.config(state=tk.DISABLED)
        threading.Thread(target=self.download_update, daemon=True).start()

    def download_update(self):
        """Descarga la nueva versión y la instala."""
        os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
        update_path = os.path.join(UPDATE_TEMP_DIR, UPDATE_EXE_NAME)

        try:
            response = requests.get(GITHUB_RELEASE_URL, timeout=10)
            response.raise_for_status()
            latest_release = response.json()

            # Buscar el archivo ejecutable en los assets
            download_url = None
            for asset in latest_release.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            if not download_url:
                self.status_label.config(text="No se encontró un archivo de actualización.")
                return

            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get("content-length", 0))

                with open(update_path, "wb") as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        percentage = (downloaded / total_length) * 100
                        self.root.after(0, lambda: self.progress_var.set(percentage))

            self.replace_files(update_path)

        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error al descargar la actualización:\n{e}")

    def close_application(self):
        """Cierra la aplicación antes de actualizar."""
        try:
            subprocess.run(["taskkill", "/F", "/IM", EXECUTABLE_NAME], check=True)
            time.sleep(2)
        except subprocess.CalledProcessError:
            print(f"No se pudo cerrar {EXECUTABLE_NAME}, puede que ya esté cerrado.")

    def replace_files(self, update_path):
        """Reemplaza el ejecutable con la nueva versión."""
        try:
            self.close_application()
            new_executable_path = os.path.join(APP_DIR, EXECUTABLE_NAME)

            if os.path.exists(new_executable_path):
                shutil.move(new_executable_path, new_executable_path + ".bak")

            shutil.move(update_path, new_executable_path)

            messagebox.showinfo("Actualización", "La actualización se completó con éxito.")
            self.restart_application()
        except Exception as e:
            messagebox.showerror("Error", f"Error al reemplazar archivos:\n{e}")

    def restart_application(self):
        """Reinicia la aplicación con la nueva versión."""
        new_executable_path = os.path.join(APP_DIR, EXECUTABLE_NAME)
        subprocess.Popen([new_executable_path], shell=True)
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = UpdaterApp(root)
    root.mainloop()
