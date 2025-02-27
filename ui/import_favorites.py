import json
from tkinter import filedialog, messagebox
from config.setup import decrypt_data, fernet_key
def import_favorites(self):
    """ Importa favoritos desde un archivo JSON encriptado """
    file_path = filedialog.askopenfilename(
        filetypes=[("Archivos JSON", "*.json")],
        title="Cargar favoritos"
    )

    if not file_path:
        return  # El usuario canceló

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            encrypted_favorites = data.get("favorites", "")

            if encrypted_favorites:
                favorites_list = decrypt_data(encrypted_favorites, fernet_key)
                self.favorites_manager.favorite_devices = favorites_list
                self.save_favorites()
                messagebox.showinfo("Importación completa", "Favoritos importados correctamente.")
            else:
                messagebox.showerror("Error", "El archivo no contiene favoritos válidos.")

    except (json.JSONDecodeError, Exception) as e:
        messagebox.showerror("Error", f"No se pudo importar: {str(e)}")
