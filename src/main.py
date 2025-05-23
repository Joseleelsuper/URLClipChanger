from config_loader import load_rules
from clipboard_watcher import ClipboardWatcher
from auto_restart import run_with_auto_restart
from logger import logger


def main():
    """Main function that can be restarted"""
    try:
        rules = load_rules()
        watcher = ClipboardWatcher(rules)
        restart_requested = watcher.run()  # Returns True if restart requested
        
        # If restart is requested, use the restart_program function
        # which creates a completely new process
        if restart_requested:
            from auto_restart import restart_program
            restart_program()
            # This won't return
        
        return False  # No restart needed
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        return True  # Request restart via the normal auto_restart mechanism


if __name__ == '__main__':
    logger.info("URL Clip Changer starting...")
    run_with_auto_restart(main, max_restarts=5)