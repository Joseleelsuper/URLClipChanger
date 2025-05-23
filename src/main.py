from auto_restart import restart_program
from config_loader import load_rules
from clipboard_watcher import ClipboardWatcher
from auto_restart import run_with_auto_restart
from logger import logger


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


if __name__ == "__main__":
    logger.info("URL Clip Changer starting...")
    run_with_auto_restart(main, max_restarts=5)
