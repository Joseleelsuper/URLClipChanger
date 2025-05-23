import sys
import ctypes
import os

# Asegurarse de que 'src' esté en el path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == 'src':
    sys.path.insert(0, os.path.dirname(current_dir))
else:
    # Si estamos ejecutando desde el ejecutable compilado, añadir el directorio actual
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Constants for hiding console window
SW_HIDE = 0
if sys.platform == "win32":
    kernel32 = ctypes.WinDLL("kernel32")
    user32 = ctypes.WinDLL("user32")
    GetConsoleWindow = kernel32.GetConsoleWindow
    ShowWindow = user32.ShowWindow

# Ahora podemos importar nuestros módulos
try:
    # Intentar importar directamente (cuando se ejecuta desde src)
    from auto_restart import restart_program, run_with_auto_restart
    from config_loader import load_rules
    from clipboard_watcher import ClipboardWatcher
    from logger import logger
except ImportError:
    # Si falla, intentar importar con el prefijo 'src.' (cuando se ejecuta desde la raíz)
    from src.auto_restart import restart_program, run_with_auto_restart
    from src.config_loader import load_rules
    from src.clipboard_watcher import ClipboardWatcher
    from src.logger import logger


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
