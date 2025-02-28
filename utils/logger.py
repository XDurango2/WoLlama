import logging
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class TextHandler(logging.Handler):
    """Manejador para enviar logs a un widget de Tkinter."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

def setup_logger(text_widget=None):
    """Configura el logger para escribir en archivo y opcionalmente en la interfaz."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Establecer nivel de logging

    # Configurar logging en archivo
    file_handler = logging.FileHandler('WoLlama_control.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Si se pasa un widget de texto, agregar un handler para la interfaz
    if text_widget:
        gui_handler = TextHandler(text_widget)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(gui_handler)

def log_action(action, target, status, error=None):
    """Registra una acción en el log."""
    message = f"Action: {action}, Target: {target}, Status: {status}"
    if error:
        logging.error(f"{message}, Error: {error}")
    else:
        logging.info(message)

def create_logging_window():
    """Crea una ventana de Tkinter para mostrar los logs en tiempo real."""
    root = tk.Tk()
    root.title("Logging Window")

    st = ScrolledText(root, state='disabled', width=80, height=20)
    st.pack(fill=tk.BOTH, expand=True)

    setup_logger(st)  # Configurar logger para escribir en el widget

    def on_closing():
        logging.shutdown()  # Asegura que los logs se cierren correctamente
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)

    return root

# Configurar logger sin abrir la ventana de GUI (para guardar en archivo)
setup_logger()

if __name__ == "__main__":
    root = create_logging_window()
    log_action("Start", "System", "Success")
    root.mainloop()
