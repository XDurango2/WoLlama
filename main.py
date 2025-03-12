import sys
import time
from ui.main_window import MainWindow
from utils.logger import setup_logger
from config import setup
def main():
    if getattr(sys, 'frozen', False):
        import pyi_splash
        time.sleep(2)
    setup.reload_config()    
    setup_logger()
    root = MainWindow()
    
    if getattr(sys, 'frozen', False):
        pyi_splash.close()
        
    root.mainloop()

if __name__ == "__main__":
    main()