import tkinter as tk
from tkinter import messagebox
import os, json
from config.setup import encrypt_data, fernet_key,CONFIG_FILE
def change_admin_user(self):
    """ Abre una ventana para cambiar el usuario administrador """
    def save_user():
        new_user = user_entry.get().strip()
        if new_user:
            # Encriptar el usuario
            encrypted_user = encrypt_data(new_user, fernet_key)

            # Guardar en config.json
            config = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    pass

            config["admin_user"] = encrypted_user
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)

            messagebox.showinfo("Cambio de usuario", "Usuario cambiado correctamente.")
            user_window.destroy()

    user_window = tk.Toplevel(self)
    user_window.title("Cambiar Usuario")
    user_window.geometry("300x150")

    tk.Label(user_window, text="Nuevo usuario administrador:").pack(pady=10)
    user_entry = tk.Entry(user_window)
    user_entry.pack(pady=5)

    save_button = tk.Button(user_window, text="Guardar", command=save_user)
    save_button.pack(pady=10)
