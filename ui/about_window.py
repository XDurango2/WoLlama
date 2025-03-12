# gui/about_window.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import logging
from config.constants import APP_NAME, APP_VERSION, APP_DESCRIPTION

class AboutWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Acerca de")
        self.geometry("400x300")
        self.create_widgets()

    def load_logo(self):
        path="wollama.png"
        try:
            image = Image.open(path)
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
            logo_label.image = logo_image  # Guardar una referencia para evitar que se recoja basura
            logo_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="e")  # Logo en la derecha
        else:
            # Si no se puede cargar la imagen, mostrar un texto alternativo
            logo_label = ttk.Label(content_frame, text="Logo no disponible")
            logo_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="e")

        # Información a la izquierda
        title_label = ttk.Label(content_frame, text=APP_NAME, font=("Helvetica", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w")

        version_label = ttk.Label(content_frame, text=f"Versión {APP_VERSION}", font=("Helvetica", 10))
        version_label.grid(row=1, column=0, sticky="w")

        desc_label = ttk.Label(content_frame, text=APP_DESCRIPTION, wraplength=250, justify="left")
        desc_label.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    about_window = AboutWindow(root)
    root.mainloop()