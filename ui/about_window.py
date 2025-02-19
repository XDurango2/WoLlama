# gui/about_window.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import logging
from config.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION

class AboutWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"Acerca de {APP_NAME}")
        self.geometry("600x400")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self.center_window()
        self.create_widgets()
        
    def center_window(self):
        self.update_idletasks()
        width, height = 300, 400  # Tamaño fijo para evitar problemas
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def load_logo(self):
        try:
            if os.path.exists("wollama.png"):
                image = Image.open("wollama.png")
                image = image.resize((90, 150), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
        except Exception as e:
            logging.error(f"Error loading logo: {e}")
        return None
        
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Cargar logo
        logo_image = self.load_logo()
        if logo_image:
            logo_label = ttk.Label(content_frame, image=logo_image)
            logo_label.image = logo_image
            logo_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="e")  # Logo en la derecha

        # Información a la izquierda
        title_label = ttk.Label(content_frame, text=APP_NAME, font=("Helvetica", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w")

        version_label = ttk.Label(content_frame, text=f"Versión {APP_VERSION}", font=("Helvetica", 10))
        version_label.grid(row=1, column=0, sticky="w")

        desc_label = ttk.Label(content_frame, text=APP_DESCRIPTION, wraplength=250, justify="left")
        desc_label.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        # Botón de cierre (Cambiado a grid)
        close_button = ttk.Button(main_frame, text="Cerrar", command=self.destroy)
        close_button.grid(row=1, column=0, columnspan=2, pady=10)  # ← Cambio de pack() a grid()
