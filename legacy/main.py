import sys
import ctypes
import os

from auto_restart import restart_program, run_with_auto_restart
from config_loader import load_rules
from clipboard_watcher import ClipboardWatcher
from logger import logger

# Determinar si estamos ejecutando desde un ejecutable de PyInstaller o como script normal
FROZEN = getattr(sys, 'frozen', False)

# Establecer la ruta base correctamente según modo de ejecución
if FROZEN:
    # Ejecutando desde ejecutable PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
    # Asegurarse de que el directorio de trabajo actual sea el directorio del ejecutable
    os.chdir(BASE_DIR)
else:
    # Ejecutando como script Python
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'src':
        BASE_DIR = os.path.dirname(current_dir)
    else:
        BASE_DIR = current_dir
    
    sys.path.insert(0, BASE_DIR)
    
# Constants for hiding console window
SW_HIDE = 0
if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32")
    user32 = ctypes.WinDLL("user32")
    GetConsoleWindow = kernel32.GetConsoleWindow
    ShowWindow = user32.ShowWindow


def main():
    """Main function that can be restarted"""
    try:
        rules = load_rules()
        watcher = ClipboardWatcher(rules)
        restart_requested = watcher.run()
        if restart_requested:
            restart_program()

        return False
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        return True


def hide_console_window():
    """Hide the console window when running as an executable"""
    if sys.platform == "win32":
        console_window = GetConsoleWindow()
        if console_window:
            ShowWindow(console_window, SW_HIDE)
            logger.debug("Console window hidden")


if __name__ == "__main__":
    # Check if we should hide the console window
    # When running as a PyInstaller executable with --noconsole, this won't matter
    # But it helps when running from Python directly with pythonw.exe
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller executable
        hide_console_window()
    
    logger.info("URL Clip Changer starting...")
    run_with_auto_restart(main, max_restarts=5)
