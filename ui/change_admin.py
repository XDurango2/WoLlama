import tkinter as tk
from tkinter import messagebox
import os, json
from config.setup import encrypt_data, fernet_key,CONFIG_FILE,reload_config,ADMIN_USER
def change_admin_user(self):
    """ Abre una ventana para cambiar el usuario administrador """
    def save_user():
        new_user = user_entry.get().strip()
        if new_user:
            # Encriptar el nuevo usuario antes de guardarlo en el archivo
            encrypted_user = encrypt_data(new_user, fernet_key)

            # Guardar en config.json
            config = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    pass

            # Actualizar el usuario administrador en el archivo
            config["admin_user"] = encrypted_user
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)

            # Recargar la configuración para actualizar ADMIN_USER en memoria
            reload_config()  # Esto actualiza la variable ADMIN_USER con el valor desencriptado

            # Verificar que el valor se haya actualizado en memoria
            #print(f"Nuevo usuario administrador en memoria: {ADMIN_USER}")  # Esto debería mostrar el nuevo valor desencriptado

            # Mostrar mensaje de éxito
            messagebox.showinfo("Cambio de usuario", "Usuario cambiado correctamente. \nReinicia la aplicación para aplicar los cambios.")
            user_window.destroy()


    user_window = tk.Toplevel(self)
    user_window.title("Cambiar Usuario")
    user_window.geometry("300x150")

    tk.Label(user_window, text="Nuevo usuario administrador:").pack(pady=10)
    user_entry = tk.Entry(user_window)
    user_entry.pack(pady=5)

    save_button = tk.Button(user_window, text="Guardar", command=save_user)
    save_button.pack(pady=10)
