from tkinter import filedialog
from tkinter import messagebox
import json
from .favorites_manager import FavoritesManager

def export_favorites(self):
    """ Exporta los favoritos en un archivo JSON encriptado """
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Archivos JSON", "*.json")],
        title="Guardar favoritos"
    )

    if not file_path:
        return  # El usuario canceló

    favorites = self.favorites_manager.load_favorites()

    with open(file_path, "w") as f:
        json.dump({"favorites": favorites}, f, indent=4)

    messagebox.showinfo("Exportación completa", "Favoritos exportados correctamente.")