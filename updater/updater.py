import os
import shutil
import requests
import subprocess
import json
import sys
import time
import threading
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
import logging
import argparse
import re
import ctypes

# Verificación de permisos de administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        # Relanzar el programa con derechos de administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
       # sys.exit(0)

# Rutas de la aplicación y datos de usuario
def get_program_path():
    """Ruta donde se instala la aplicación (Program Files)"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "WoLlama")
    # Si se ejecuta desde el código fuente, usar el directorio actual
    return os.path.dirname(os.path.abspath(__file__))

def get_user_data_path():
    """Ruta donde se almacenan los datos del usuario (AppData)"""
    return os.path.join(os.environ["APPDATA"], "WoLlama")

# Configure logging
def setup_logging():
    user_data_path = get_user_data_path()
    os.makedirs(user_data_path, exist_ok=True)
    log_path = os.path.join(user_data_path, "updater_log.txt")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

# Global variables
PROGRAM_PATH = get_program_path()  # Ruta de instalación (Program Files)
USER_DATA_PATH = get_user_data_path()  # Ruta de datos de usuario (AppData)
CONFIG_FILE = os.path.join(USER_DATA_PATH, "config.json")
KEY_FILE = os.path.join(USER_DATA_PATH, "secret.key")
EXECUTABLE_NAME = "WoLlama.exe"
UPDATE_ZIP_NAME = "WoLlama_update.zip"
UPDATE_TEMP_DIR = os.path.join(USER_DATA_PATH, "update_temp")
GITHUB_RELEASE_URL = "https://api.github.com/repos/XDurango2/WoLlama/releases/latest"

# Global tkinter root for handling UI
root = None

def initialize_tkinter():
    """Initialize Tkinter safely if not already running."""
    global root
    try:
        # Check if we already have a root window
        if root is None or not root.winfo_exists():
            root = tk.Tk()
            root.withdraw()  # Hide main window but keep it for messagebox
            # Set a title just in case it becomes visible
            root.title("WoLlama Updater")
        return True
    except tk.TclError:
        logging.error("Failed to initialize Tkinter")
        return False

def show_message(title, message, error=False):
    """Show a message to the user, handling both GUI and command-line modes."""
    logging.info(f"{title}: {message}")
    
    if args.silent:
        # In silent mode, just log the message
        return
    
    try:
        # Try to show a GUI message
        if initialize_tkinter():
            if error:
                messagebox.showerror(title, message)
            else:
                messagebox.showinfo(title, message)
    except Exception as e:
        # Fall back to console if GUI fails
        logging.error(f"Failed to show message box: {e}")
        print(f"{title}: {message}")

def load_key():
    """Load encryption key safely."""
    try:
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        logging.warning("Key file not found. Encryption/decryption will not be available.")
        return None
    except Exception as e:
        logging.error(f"Error loading key: {e}")
        return None

def load_config():
    """Load configuration with error handling."""
    try:
        os.makedirs(USER_DATA_PATH, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logging.warning("Config file not found, creating default configuration")
            default_config = {"app_version": "0.0.0"}
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4)
            return default_config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {"app_version": "0.0.0"}

def update_config(new_version):
    """Actualiza el config.json con la nueva versión."""
    try:
        config = load_config()
        config["app_version"] = new_version  # Actualizar la versión
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        logging.info(f"Config.json actualizado a la versión {new_version}")
        return True
    except Exception as e:
        logging.error(f"Error al actualizar config.json: {e}")
        return False

def get_current_version():
    """Get the current installed version."""
    config = load_config()
    return config.get("app_version", "0.0.0")

def parse_version(version_string):
    """Parse a version string and extract the version components.
    
    Examples:
    "V1.2.3" -> (1, 2, 3, "", 0)
    "v2.0.0-beta" -> (2, 0, 0, "beta", 0)
    "1.0" -> (1, 0, 0, "", 0)
    "V1.1-Stable" -> (1, 1, 0, "Stable", 0)
    "V1.2-prerelease" -> (1, 2, 0, "prerelease", 0)
    "V1.2-rc1" -> (1, 2, 0, "rc", 1)
    """
    try:
        # Remove 'v' or 'V' prefix if present
        if version_string.lower().startswith('v'):
            version_string = version_string[1:]
            
        # Split by hyphen to separate version from label
        parts = version_string.split('-', 1)
        version_part = parts[0]
        label_part = parts[1] if len(parts) > 1 else ""
        
        # Extract numeric version components
        version_numbers = re.findall(r'\d+', version_part)
        major = int(version_numbers[0]) if len(version_numbers) > 0 else 0
        minor = int(version_numbers[1]) if len(version_numbers) > 1 else 0
        patch = int(version_numbers[2]) if len(version_numbers) > 2 else 0
        
        # Extract label and potential number from label
        label_match = re.match(r'([a-zA-Z]+)(\d*)', label_part)
        if label_match:
            label = label_match.group(1)
            label_num = int(label_match.group(2)) if label_match.group(2) else 0
        else:
            label = label_part
            label_num = 0
            
        return (major, minor, patch, label.lower(), label_num)
    except Exception as e:
        logging.error(f"Error parsing version string '{version_string}': {e}")
        return (0, 0, 0, "", 0)

def version_is_newer(current_version, latest_version):
    """Compare version strings to check if latest is newer.
    
    Handles complex version strings like:
    - V1.1-Stable
    - V1.2-prerelease
    - V2.0.0-beta2
    """
    # Parse version strings
    current = parse_version(current_version)
    latest = parse_version(latest_version)
    
    # Log parsed versions for debugging
    logging.info(f"Parsed current version '{current_version}': {current}")
    logging.info(f"Parsed latest version '{latest_version}': {latest}")
    
    # Compare major.minor.patch parts
    for i in range(3):
        if latest[i] > current[i]:
            return True
        elif latest[i] < current[i]:
            return False
    
    # If we get here, the major.minor.patch parts are equal
    # Now handle pre-release labels
    
    # Label priority (lower is more stable/higher priority)
    label_priority = {
        "": 0,         # No label (stable release)
        "stable": 0,   # Explicitly marked stable
        "patch": 1,
        "update": 1,
        "fix": 1,
        "hotfix": 1,
        "rc": 2,       # Release Candidate
        "beta": 3,
        "alpha": 4,
        "dev": 5,
        "snapshot": 5,
        "nightly": 6,
        "prerelease": 7
    }
    
    # Get priority for each label (default to 99 if unknown)
    current_priority = label_priority.get(current[3], 99)
    latest_priority = label_priority.get(latest[3], 99)
    
    # If current is stable and latest is any kind of pre-release, don't update
    if current_priority == 0 and latest_priority > 0:
        # Unless explicitly overridden by command line
        if not getattr(args, 'allow_prerelease', False):
            logging.info("Latest version is a pre-release but current is stable. Skipping update.")
            return False
    
    # Compare labels based on priority
    if latest_priority < current_priority:
        return True  # Latest version has higher priority label
    elif latest_priority > current_priority:
        return False  # Latest version has lower priority label
    
    # If labels have the same priority, compare their numeric part
    if latest[4] > current[4]:
        return True
    
    # Versions are identical or current is newer
    return False

def close_main_application():
    """Cierra el programa principal antes de actualizar."""
    logging.info("Intentando cerrar la aplicación principal...")

    try:
        # Obtener el PID del proceso actual
        current_pid = os.getpid()

        # Intentar cerrar el proceso padre si es válido
        if hasattr(os, 'getppid'):
            parent_pid = os.getppid()
            if parent_pid > 1 and parent_pid != current_pid:  # Asegurarse de no cerrar el propio actualizador
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(parent_pid)],
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   check=False)
                    logging.info(f"Sent termination signal to parent process (PID: {parent_pid})")
                except Exception as e:
                    logging.warning(f"No se pudo cerrar el proceso padre (PID: {parent_pid}): {e}")

        # Como alternativa, intentar cerrar el ejecutable principal
        try:
            subprocess.run(["taskkill", "/F", "/IM", EXECUTABLE_NAME],
                           stderr=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           check=False)
            logging.info(f"Sent termination signal to {EXECUTABLE_NAME}")
        except Exception as e:
            logging.warning(f"No se pudo cerrar el ejecutable principal ({EXECUTABLE_NAME}): {e}")

        # Dar tiempo para que los procesos se terminen
        time.sleep(2)
        return True
    except Exception as e:
        logging.error(f"Error al cerrar la aplicación principal: {e}")
        return False

def cleanup_temp_files():
    """Clean up temporary files and directories."""
    try:
        if os.path.exists(UPDATE_TEMP_DIR):
            shutil.rmtree(UPDATE_TEMP_DIR, ignore_errors=True)
            logging.info("Archivos temporales eliminados")
    except Exception as e:
        logging.error(f"Error al limpiar archivos temporales: {e}")

def extract_and_replace(zip_path, new_version):
    """Extract update files and replace the current installation."""
    try:
        # First close the main application
        if not close_main_application():
            show_message("Advertencia", "No se pudo cerrar la aplicación principal. La actualización puede fallar.")
        
        # Create extraction directory
        extract_path = os.path.join(UPDATE_TEMP_DIR, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        
        # Extract files
        logging.info(f"Extrayendo archivos de {zip_path} a {extract_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Asegurar que tenemos permisos de administrador para escribir en Program Files
        if not is_admin():
            show_message("Error", "Se requieren permisos de administrador para instalar la actualización.", error=True)
            return False
            
        # Asegurar que el directorio de destino existe
        os.makedirs(PROGRAM_PATH, exist_ok=True)
        
        # Replace files
        for item in os.listdir(extract_path):
            src_path = os.path.join(extract_path, item)
            dest_path = os.path.join(PROGRAM_PATH, item)
            
            # Skip updater.py if it's the current running file
            if item == os.path.basename(__file__) and os.path.exists(__file__) and os.path.samefile(src_path, __file__):
                logging.info(f"Skipping replacement of currently running file: {item}")
                continue
                
            logging.info(f"Replacing {dest_path} with {src_path}")
            
            # Remove existing file/directory
            if os.path.exists(dest_path):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)
            
            # Move new file/directory
            shutil.move(src_path, dest_path)
        
        # Update configuration
        update_config(new_version)
        show_message("Actualización", "La actualización se completó con éxito.")
        
        # Cleanup
        cleanup_temp_files()
        
        # Restart the application
        if not args.no_restart:
            restart_application()
        
        return True
    except Exception as e:
        logging.error(f"Error al actualizar archivos: {e}")
        show_message("Error", f"Error al actualizar archivos:\n{e}", error=True)
        return False

def restart_application():
    """Reinicia la aplicación principal después de la actualización."""
    try:
        new_executable_path = os.path.join(PROGRAM_PATH, EXECUTABLE_NAME)
        logging.info(f"Iniciando aplicación: {new_executable_path}")
        
        if os.path.exists(new_executable_path):
            # Use detached process to avoid waiting
            if sys.platform.startswith('win'):
                # On Windows, use start command
                subprocess.Popen(["start", "", new_executable_path], shell=True)
            else:
                # On other platforms
                subprocess.Popen([new_executable_path], start_new_session=True)
            
            # Exit this process
            logging.info("Actualización completada. Saliendo del actualizador.")
            time.sleep(1)  # Brief pause to allow logging to complete
            os._exit(0)
        else:
            logging.error(f"No se encontró el ejecutable: {new_executable_path}")
            show_message("Error", f"No se encontró el ejecutable: {new_executable_path}", error=True)
    except Exception as e:
        logging.error(f"Error al reiniciar la aplicación: {e}")
        show_message("Error", f"Error al reiniciar la aplicación: {e}", error=True)

def check_for_updates():
    """Check if updates are available without applying them."""
    try:
        current_version = get_current_version()
        logging.info(f"Versión actual: {current_version}")
        
        response = requests.get(GITHUB_RELEASE_URL, timeout=10)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release.get("tag_name", "0.0.0")
        logging.info(f"Última versión disponible: {latest_version}")
        
        if version_is_newer(current_version, latest_version):
            release_notes = latest_release.get("body", "No hay notas de versión disponibles.")
            show_message("Actualización disponible", 
                         f"Hay una nueva versión disponible: {latest_version}\n\nNotas de versión:\n{release_notes}")
            return True, latest_version, latest_release
        else:
            if not args.silent:
                show_message("Actualización", "Ya tienes la última versión instalada.")
            return False, current_version, None
    except Exception as e:
        logging.error(f"Error al verificar actualizaciones: {e}")
        show_message("Error", f"Error al verificar actualizaciones:\n{e}", error=True)
        return False, get_current_version(), None

def download_update():
    """Download and apply updates if available."""
    os.makedirs(UPDATE_TEMP_DIR, exist_ok=True)
    update_path = os.path.join(UPDATE_TEMP_DIR, UPDATE_ZIP_NAME)
    
    try:
        # Check for updates
        update_available, latest_version, latest_release = check_for_updates()
        
        if not update_available:
            return False
            
        # If user wants to check only, don't download
        if args.check_only:
            return True
            
        # Find download URL
        download_url = None
        for asset in latest_release.get("assets", []):
            if asset["name"].endswith(".zip"):
                download_url = asset["browser_download_url"]
                break
                
        if not download_url:
            show_message("Error", "No se encontró un archivo de actualización.", error=True)
            return False
            
        # Create a simple progress display if not in silent mode
        if not args.silent:
            initialize_tkinter()
            progress_window = tk.Toplevel(root)
            progress_window.title("Descargando actualización")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            # Center window
            progress_window.update_idletasks()
            width = progress_window.winfo_width()
            height = progress_window.winfo_height()
            x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (progress_window.winfo_screenheight() // 2) - (height // 2)
            progress_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
            
            label = ttk.Label(progress_window, text=f"Descargando WoLlama {latest_version}...")
            label.pack(pady=10)
            
            progress = ttk.Progressbar(progress_window, orient="horizontal", length=250, mode="indeterminate")
            progress.pack(pady=10)
            progress.start()
            
            # Update UI
            progress_window.update()
        
        # Download file
        logging.info(f"Descargando actualización desde: {download_url}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(update_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        # Close progress window if it exists
        if not args.silent and 'progress_window' in locals():
            progress_window.destroy()
            
        # Install update
        return extract_and_replace(update_path, latest_version)
        
    except requests.RequestException as e:
        logging.error(f"Error al descargar la actualización: {e}")
        show_message("Error", f"Error al descargar la actualización:\n{e}", error=True)
        return False
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        show_message("Error", f"Error inesperado:\n{e}", error=True)
        return False
    finally:
        # Ensure UI is closed
        if not args.silent and 'progress_window' in locals():
            try:
                progress_window.destroy()
            except:
                pass

def create_desktop_shortcut():
    """Crea un acceso directo en el escritorio para la aplicación."""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "WoLlama.lnk")
        target = os.path.join(PROGRAM_PATH, EXECUTABLE_NAME)
        
        if os.path.exists(target):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = PROGRAM_PATH
            shortcut.IconLocation = target
            shortcut.save()
            logging.info(f"Acceso directo creado en: {shortcut_path}")
            return True
        else:
            logging.error(f"No se encontró el ejecutable para crear acceso directo: {target}")
            return False
    except Exception as e:
        logging.error(f"Error al crear acceso directo: {e}")
        return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='WoLlama Updater')
    parser.add_argument('--silent', action='store_true', help='Ejecutar en modo silencioso (sin interfaz gráfica)')
    parser.add_argument('--check-only', action='store_true', help='Solo verificar si hay actualizaciones, sin descargar')
    parser.add_argument('--no-restart', action='store_true', help='No reiniciar la aplicación después de actualizar')
    parser.add_argument('--allow-prerelease', action='store_true', 
                        help='Permitir actualizar a versiones pre-release incluso si la versión actual es estable')
    parser.add_argument('--create-shortcut', action='store_true',
                        help='Crear acceso directo en el escritorio')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logging.info("Iniciando WoLlama Updater")
    
    # Verificar si necesitamos permisos de administrador para actualizar en Program Files
    if not is_admin() and not args.check_only:
        logging.info("Solicitando permisos de administrador para actualizar")
        run_as_admin()
    
    try:
        # Crear acceso directo si se solicita
        if args.create_shortcut:
            if create_desktop_shortcut():
                show_message("Acceso directo", "Se ha creado un acceso directo en el escritorio.")
            else:
                show_message("Error", "No se pudo crear el acceso directo en el escritorio.", error=True)
                
        # Run the updater
        if download_update():
            if args.check_only:
                logging.info("Verificación completada, hay una actualización disponible")
            else:
                logging.info("Actualización completada exitosamente")
        else:
            logging.info("No se realizó ninguna actualización")
            
    except Exception as e:
        logging.error(f"Error crítico en el actualizador: {e}")
        if not args.silent:
            show_message("Error Crítico", f"Error en el actualizador:\n{e}", error=True)
    finally:
        # Ensure cleanup happens
        cleanup_temp_files()
        
        # Exit if we're not supposed to restart
        if not args.no_restart and getattr(sys, 'frozen', False):
            sys.exit(0)