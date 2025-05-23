"""Auto-restart functionality for the URL Clip Changer"""

import sys
import subprocess
import time
from typing import Callable
from logger import logger


def restart_program():
    """Restart the current program with a clean process"""

    logger.info("Restarting program...")
    python = sys.executable
    script = sys.argv[0]

    subprocess.Popen(
        [python, script] + sys.argv[1:], 
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        start_new_session=True
    )
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
                logger.info(
                    f"Restart requested. Count: {restart_count}/{max_restarts}"
                )
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
