import logging
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from datetime import datetime

class TextHandler(logging.Handler):
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
    logger = logging.getLogger()
    if not logger.handlers:  # Evita añadir múltiples handlers
        logging.basicConfig(
            filename='remote_control.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    if text_widget:
        handler = TextHandler(text_widget)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

def log_action(action, target, status):
    logging.info(f"Action: {action}, Target: {target}, Status: {status}")

def create_logging_window():
    root = tk.Tk()
    root.title("Logging Window")

    st = ScrolledText(root, state='disabled', width=80, height=20)
    st.pack(fill=tk.BOTH, expand=True)

    setup_logger(st)

    # Cerrar correctamente el logger al cerrar la ventana
    def on_closing():
        logging.shutdown()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)

    return root

if __name__ == "__main__":
    root = create_logging_window()
    log_action("Start", "System", "Success")
    root.mainloop()
