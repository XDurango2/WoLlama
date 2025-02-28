# config/setup.py
from cryptography.fernet import Fernet
import json
import os
import sys
from config.constants import APP_NAME, APP_VERSION

# Obtener la ruta donde se almacenará la configuración y clave
def get_user_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.environ["APPDATA"], "WoLlama")  # Para Windows
    return os.path.dirname(os.path.abspath(__file__))

global ADMIN_USER  # Declarar las variables globales
BASE_PATH = get_user_data_path()
CONFIG_FILE = os.path.join(BASE_PATH, "config.json")
KEY_FILE = os.path.join(BASE_PATH, "secret.key")
DEFAULT_ADMIN_USER = "FDM-Soporte"

# Crear el directorio si no existe
os.makedirs(BASE_PATH, exist_ok=True)

def generate_key():
    """Genera una clave secreta y la almacena en un archivo."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)

def load_key():
    """Carga la clave de cifrado desde el archivo."""
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

def encrypt_data(data, key):
    """Encripta datos con la clave dada."""
    cipher = Fernet(key)
    return cipher.encrypt(json.dumps(data).encode()).decode()

def decrypt_data(data, key):
    """Desencripta datos con la clave dada."""
    cipher = Fernet(key)
    return json.loads(cipher.decrypt(data.encode()).decode())

# Asegurar que la clave existe
generate_key()
fernet_key = load_key()

# Cargar configuración desde config.json
def reload_config():
    """Recarga la configuración y actualiza las variables globales."""
    global ADMIN_USER, FAVORITES, APP_VERSION, APP_NAME
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                encrypted_user = config.get("admin_user", "")
                app_version = config.get("app_version", APP_VERSION)  # Leer la versión desde el archivo
                app_name = config.get("app_name", APP_NAME)  # Leer el nombre de la app desde el archivo
                
                # Desencriptar los valores
                ADMIN_USER = decrypt_data(encrypted_user, fernet_key) if encrypted_user else DEFAULT_ADMIN_USER
        except (json.JSONDecodeError, Exception):
            ADMIN_USER = DEFAULT_ADMIN_USER
            APP_VERSION = APP_VERSION
            APP_NAME = APP_NAME

# Asegúrate de que las variables estén actualizadas al inicio
reload_config()
# Si el archivo config.json no existe, crea uno con los valores por defecto
if not os.path.exists(CONFIG_FILE):
    config = {
        "admin_user": encrypt_data(DEFAULT_ADMIN_USER, fernet_key),
        "app_version": APP_VERSION,
        "app_name": APP_NAME
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
