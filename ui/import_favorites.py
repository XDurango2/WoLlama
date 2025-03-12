import json
import csv
from tkinter import messagebox
from config.setup import fernet_key, encrypt_data

def import_favorites(main_window, file_path):
    try:
        new_favorites = []

        if file_path.endswith('.json'):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                new_favorites = data.get("favorites", [])
        
        elif file_path.endswith('.csv'):
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                # Convertir claves a minúsculas para evitar errores con "MAC" vs "mac"
                new_favorites = [
                    {k.lower(): v for k, v in row.items()} 
                    for row in reader
                ]
        else:
            messagebox.showerror("Error", "Tipo de archivo no soportado.")
            return
        
        if not new_favorites:
            messagebox.showerror("Error", "El archivo no contiene favoritos válidos.")
            return

        # Obtener la lista actual de favoritos
        current_favorites = main_window.favorites_manager.favorite_devices

        # Contador de dispositivos añadidos
        added_count = 0

        for new_device in new_favorites:
            # Obtener la dirección MAC si existe
            mac_address = new_device.get("mac", "").strip()

            # Si no tiene MAC (por ejemplo, localhost), generar un identificador único con la IP
            if not mac_address:
                mac_address = f"NO-MAC-{new_device.get('ip', 'UNKNOWN')}"

            # Comprobar si el dispositivo ya existe en la lista actual por MAC
            if not any(device.get("mac", "").strip() == mac_address for device in current_favorites):
                new_device["mac"] = mac_address  # Asegurar que tenga MAC
                current_favorites.append(new_device)
                added_count += 1

        # Actualizar la lista de favoritos
        main_window.favorites_manager.favorite_devices = current_favorites
        main_window.favorites_manager.save_favorites()

        # Actualizar la interfaz
        main_window.filter_devices()

        # Mostrar mensaje de confirmación
        if added_count > 0:
            messagebox.showinfo("Importación completa", 
                               f"Se agregaron {added_count} nuevos favoritos correctamente.")
        else:
            messagebox.showinfo("Importación completa", 
                               "No se agregaron nuevos favoritos. Todos ya existían en la lista.")

    except (json.JSONDecodeError, csv.Error, Exception) as e:
        messagebox.showerror("Error", f"No se pudo importar: {str(e)}")
