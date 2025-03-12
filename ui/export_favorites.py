import json
import csv
from tkinter import messagebox, filedialog

class FavoritesExporter:
    def __init__(self, favorites_manager):
        self.favorites_manager = favorites_manager

    def export_favorites(self):
        """Permite al usuario elegir un archivo para guardar los favoritos en JSON o CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Archivos CSV", "*.csv")],
            title="Guardar favoritos"
        )

        if not file_path:
            return  # El usuario canceló

        if file_path.endswith(".json"):
            self._export_to_json(file_path)
        elif file_path.endswith(".csv"):
            self._export_to_csv(file_path)
        else:
            messagebox.showerror("Error", "Formato no soportado. Por favor, elija JSON o CSV.")

    def _export_to_json(self, file_path):
        """Exporta los favoritos a un archivo JSON."""
        favorites = self.favorites_manager.load_favorites()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"favorites": favorites}, f, indent=4)
            messagebox.showinfo("Exportación JSON", "Favoritos exportados correctamente en JSON.")
        except Exception as e:
            messagebox.showerror("Error de exportación", f"No se pudo exportar a JSON: {str(e)}")

    def _export_to_csv(self, file_path):
        """Exporta los favoritos a un archivo CSV."""
        favorites = self.favorites_manager.load_favorites()
        try:
            with open(file_path, "w", encoding="utf-8", newline='') as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(["Nombre", "IP", "MAC", "Notas"])  # Encabezados

                for device in favorites:
                    if isinstance(device, dict):
                        name = device.get('name', f"Dispositivo {device.get('ip', '')}")
                        ip = device.get('ip', '')
                        mac = device.get('mac', '')
                        notes = device.get('notes', '')
                        csv_writer.writerow([name, ip, mac, notes])

            messagebox.showinfo("Exportación CSV", "Favoritos exportados correctamente en CSV.")
        except Exception as e:
            messagebox.showerror("Error de exportación", f"No se pudo exportar a CSV: {str(e)}")
