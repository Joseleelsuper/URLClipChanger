"""GUI entry point for URL Clip Changer."""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, src_path)

from infrastructure.logging.logger import logger # noqa: E402
from infrastructure.ui.gui_app import start_gui  # noqa: E402


def main():
    """Main function for the GUI application."""
    try:
        logger.info("Starting URL Clip Changer GUI")
        start_gui()
        return False  # No restart needed
    except Exception as e:
        logger.error(f"Error in GUI main: {e}")
        return True  # Request restart


if __name__ == "__main__":
    main()
