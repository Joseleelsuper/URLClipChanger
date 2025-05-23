"""Auto-restart functionality for the URL Clip Changer"""

import sys
import subprocess
import time
import os
from typing import Callable

# Asegurarse de que 'src' esté en el path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == 'src':
    sys.path.insert(0, os.path.dirname(current_dir))

try:
    from logger import logger
except ImportError:
    from src.logger import logger


def restart_program():
    """Restart the current program with a clean process, detached from current terminal."""

    logger.info("Restarting program...")
    
    # DETACHED_PROCESS flag (0x00000008) completely separates the new process from the 
    # parent console, preventing terminal interference
    DETACHED_PROCESS = 0x00000008
    
    # Check if we're running from a PyInstaller executable or as a Python script
    if getattr(sys, 'frozen', False):
        # We're running from a PyInstaller executable
        executable = sys.executable
        args = []
    else:
        # We're running as a Python script
        executable = sys.executable
        script = sys.argv[0]
        args = [script] + sys.argv[1:]
    
    # start_new_session=True helps in creating a separate session
    # We redirect stdout and stderr to NUL to avoid any terminal interference
    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(
            [executable] + args,
            creationflags=DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            start_new_session=True,
            stdout=devnull,
            stderr=devnull,
        )
    
    # Give the new process a moment to start before exiting this one
    time.sleep(0.5)
    sys.exit(0)


def run_with_auto_restart(main_func: Callable, max_restarts: int = 5):
    """Run main function with auto-restart capability.

    Args:
        main_func (Callable): The main function to run.
        max_restarts (int, optional): Maximum number of restarts allowed. Defaults to 5.
    """
    restart_count = 0

    while restart_count < max_restarts:
        try:
            logger.info(f"Starting program (attempt {restart_count + 1})")
            result = main_func()

            # If main_func returns True, it means restart was requested
            if result is True:
                restart_count += 1
                logger.info(f"Restart requested. Count: {restart_count}/{max_restarts}")
                time.sleep(2)  # Wait a bit before restarting
                continue
            else:
                # Normal exit
                break

        except KeyboardInterrupt:
            logger.info("Program interrupted by user")
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"Program crashed: {e}")
            logger.info(f"Auto-restarting... ({restart_count}/{max_restarts})")
            if restart_count < max_restarts:
                time.sleep(5)  # Wait before restart
            else:
                logger.error("Maximum restart attempts reached")
                break

    logger.info("Program ended")
