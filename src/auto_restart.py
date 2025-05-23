"""Auto-restart functionality for the URL Clip Changer"""

import sys
import subprocess
import time
import os
from typing import Callable

from logger import logger


def restart_program():
    """Restart the current program with a clean process, detached from current terminal."""
    logger.info("Restarting program.")

    # Determine restart command: use original EXE path when frozen to avoid temp _MEI folder
    if getattr(sys, "frozen", False):
        exe_path = os.path.abspath(sys.argv[0])
        cmd = [exe_path] + sys.argv[1:]
        cwd = os.path.dirname(exe_path)
    else:
        exe = sys.executable
        script = os.path.abspath(sys.argv[0])
        cmd = [exe, script] + sys.argv[1:]
        cwd = None

    # Launch new process with its own temp folder (PyInstaller reset) so the old one can cleanup
    with open(os.devnull, "w") as devnull:
        env = os.environ.copy()
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        popen_kwargs = {
            "stdout": devnull,
            "stderr": devnull,
            "close_fds": True,
            "env": env,
        }
        if cwd:
            popen_kwargs["cwd"] = cwd
        subprocess.Popen(cmd, **popen_kwargs)

    # Give the new process a moment to start before exiting this one
    time.sleep(0.5)
    sys.exit(0)


def run_with_auto_restart(main_func: Callable, max_restarts: int = 5):
    """Run main function with auto-restart capability."""
    restart_count = 0

    while restart_count < max_restarts:
        try:
            logger.info(f"Starting program (attempt {restart_count + 1})")
            result = main_func()
            if result:
                restart_count += 1
                logger.info(f"Restart requested. Count: {restart_count}/{max_restarts}")
                time.sleep(2)
                continue
            break
        except KeyboardInterrupt:
            logger.info("Program interrupted by user")
            break
        except Exception as e:
            restart_count += 1
            logger.error(f"Program crashed: {e}")
            if restart_count < max_restarts:
                logger.info(f"Auto-restarting... ({restart_count}/{max_restarts})")
                time.sleep(5)
            else:
                logger.error("Maximum restart attempts reached")
                break

    logger.info("Program ended")
