import ctypes
import win32con
import win32clipboard
import win32gui
import pyperclip
import time
import threading
import os
import sys
from typing import Any, List, Optional, Tuple
import traceback
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__))

src_path = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.insert(0, src_path)

from core.services.url_processor import add_suffix  # noqa: E402
from infrastructure.logging.logger import logger  # noqa: E402

class ClipboardWatcher:
    """Watches the clipboard for changes and processes URLs."""

    BASE_CLASS_NAME = "ClipboardWatcher"
    CLASS_NAME = f"{BASE_CLASS_NAME}_{int(time.time())}_{os.getpid()}"

    def __init__(self, rules: List[Tuple[List[str], str]]):
        """Initialize the clipboard watcher.

        Args:
            rules: List of rules to apply to URLs
        """
        self.rules = rules
        self.check_interval = 1.0
        self.prev_clipboard = ""
        self.running = True
        self.hwnd = None
        self.hinst = None
        self.window_class_name = f"ClipboardWatcher_{uuid.uuid4().hex}"
        self.last_activity = time.time()
        self.restart_flag = False
        self.ignore_next = False
        # Add a lock for clipboard access to avoid threading issues
        self.clipboard_access_lock = threading.Lock()

        # Only start watchdog in development (not in EXE compiled)
        if not getattr(sys, "frozen", False):
            self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
            self.watchdog_thread.start()

        # Cleanup any existing windows, register ours, etc.
        self._cleanup_existing_windows()
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc  # type: ignore
        wc.lpszClassName = self.window_class_name  # type: ignore
        try:
            logger.debug(f"Registering window class: {self.window_class_name}")
            self.atom = win32gui.RegisterClass(wc)
            self.hwnd = win32gui.CreateWindow(
                self.atom, self.window_class_name, 0, 0, 0, 0, 0, 0, 0, 0, None
            )
            self.WM_CLIPBOARDUPDATE = 0x031D
            ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)
        except Exception as e:
            logger.error(f"Failed to register window class: {e}")
            raise

    def _cleanup_existing_windows(self):
        """Find and cleanup any existing instances of our window class"""

        def enum_windows_callback(hwnd, extra):
            try:
                class_name = win32gui.GetClassName(hwnd)
                if class_name.startswith(self.BASE_CLASS_NAME):  # type: ignore
                    try:
                        logger.debug(
                            f"Found existing window: {hwnd}, class: {class_name}, attempting to close"
                        )
                        win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    except Exception as e:
                        logger.debug(f"Error closing window {hwnd}: {e}")
            except Exception as e:
                logger.debug(f"Error enumerating windows: {e}")
            finally:
                return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            logger.debug(f"Error cleaning up existing windows: {e}")

    def wnd_proc(self, hwnd: Any, msg: Any, wparam: Any, lparam: Any) -> Any:
        """Window procedure to handle messages

        Args:
            hwnd (Any): Window handle
            msg (Any): Message identifier
            wparam (Any): Window message parameter
            lparam (Any): Window message parameter

        Returns:
            Any: Result of the message processing
        """
        if msg == self.WM_CLIPBOARDUPDATE:
            self.handle_clipboard_change()
            return 0
        elif msg == win32con.WM_DESTROY:
            ctypes.windll.user32.RemoveClipboardFormatListener(self.hwnd)
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _watchdog(self):
        """Watchdog timer to detect if the program gets stuck"""

        while self.running:
            time.sleep(10)  # Check every 10 seconds
            if time.time() - self.last_activity > 30:  # 30 seconds without activity
                logger.warning("Possible deadlock detected, requesting restart...")
                self.restart_flag = True
                self.running = False
                try:
                    win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
                except Exception as e:
                    logger.debug(f"Failed to post quit message: {e}")
                break

    def _safe_clipboard_get(self, max_retries: int = 3) -> Optional[str]:
        """Safely get clipboard data with retries

        Args:
            max_retries (int, optional): Maximum number of retries. Defaults to 3.

        Returns:
            Optional[str]: Clipboard text or None if failed.
        """
        for attempt in range(max_retries):
            try:
                with self.clipboard_access_lock:
                    win32clipboard.OpenClipboard()
                    try:
                        text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        return text
                    finally:
                        win32clipboard.CloseClipboard()
            except Exception as e:
                logger.debug(f"Clipboard read attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                else:
                    return None
        return None

    def _safe_clipboard_set(self, text: str, max_retries: int = 3) -> bool:
        """Safely set clipboard data with retries.

        Args:
            text (str): Text to set in the clipboard.
            max_retries (int, optional): Maximum number of retries. Defaults to 3.

        Returns:
            bool: True if successful, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                with self.clipboard_access_lock:
                    pyperclip.copy(text)
                    return True
            except Exception as e:
                logger.debug(f"Clipboard write attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1)
                else:
                    return False
        return False

    def handle_clipboard_change(self):
        """Handle clipboard change event."""
        self.last_activity = time.time()

        if self.ignore_next:
            self.ignore_next = False
            return

        try:
            text = self._safe_clipboard_get()
            if text is None:
                return

            if text.startswith(("http://", "https://")):
                new = add_suffix(text, self.rules)
                if new != text:
                    self.ignore_next = True
                    success = self._safe_clipboard_set(new)
                    if success:
                        logger.info(f"Clipboard updated: {new}")
                    else:
                        logger.error("Failed to update clipboard")
                        self.ignore_next = False

        except Exception as e:
            logger.error(
                f"Error handling clipboard change: {e}\n" + traceback.format_exc()
            )
            self.last_activity = time.time()

    def cleanup(self):
        """Clean up resources"""

        self.running = False
        try:
            if self.hwnd:
                ctypes.windll.user32.RemoveClipboardFormatListener(self.hwnd)
                win32gui.DestroyWindow(self.hwnd)
            logger.debug("Clipboard watcher resources cleaned up")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")

    def run(self):
        """Run the clipboard watcher"""

        try:
            logger.info("Clipboard watcher started")
            win32gui.PumpMessages()
            return self.restart_flag
        except Exception as e:
            logger.error(f"Message pump error: {e}")
            # On message pump error, signal restart
            return True
        finally:
            self.cleanup()

    def _create_window(self):
        """Create a hidden window to receive clipboard change messages."""
        try:
            # Use the instance-specific window class name
            logger.debug(f"Registering window class: {self.window_class_name}")

            # Check if the window class already exists using EnumWindows
            found_existing = [False]
            
            def check_class_name(hwnd, extra):
                try:
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name == self.window_class_name:
                        found_existing[0] = True
                except Exception:
                    pass
                return True
            
            win32gui.EnumWindows(check_class_name, None)
            
            if found_existing[0]:
                logger.debug(f"Window class already exists: {self.window_class_name}")
                # Generate a new unique name
                self.window_class_name = f"ClipboardWatcher_{uuid.uuid4().hex}"
                logger.debug(f"Generated new window class name: {self.window_class_name}")

            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self.wnd_proc  # type: ignore
            wc.lpszClassName = self.window_class_name  # type: ignore
            try:
                logger.debug(f"Registering window class: {self.window_class_name}")
                self.atom = win32gui.RegisterClass(wc)
                self.hwnd = win32gui.CreateWindow(
                    self.atom, self.window_class_name, 0, 0, 0, 0, 0, 0, 0, 0, None
                )
                self.WM_CLIPBOARDUPDATE = 0x031D
                ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)
            except Exception as e:
                logger.error(f"Failed to register window class: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to register window class: {e}")
            raise
