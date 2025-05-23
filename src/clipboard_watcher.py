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

from suffix_adder import add_suffix
from logger import logger


class ClipboardWatcher:
    BASE_CLASS_NAME = "ClipboardWatcher"
    CLASS_NAME = f"{BASE_CLASS_NAME}_{int(time.time())}_{os.getpid()}"

    def __init__(self, rules: List[Tuple[List[str], str]]):
        self.rules = rules
        self.ignore_next = False
        self.last_activity = time.time()
        self.is_running = True
        self.restart_flag = False
        self.clipboard_access_lock = threading.Lock()
        self.atom = None
        self.hwnd = None

        # Solo arrancar watchdog en desarrollo (no en EXE compilado)
        if not getattr(sys, "frozen", False):
            self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
            self.watchdog_thread.start()

        # Cleanup any existing windows, register ours, etc.
        self._cleanup_existing_windows()
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc  # type: ignore
        wc.lpszClassName = self.CLASS_NAME  # type: ignore
        try:
            logger.debug(f"Registering window class: {self.CLASS_NAME}")
            self.atom = win32gui.RegisterClass(wc)
            self.hwnd = win32gui.CreateWindow(
                self.atom, self.CLASS_NAME, 0, 0, 0, 0, 0, 0, 0, 0, None
            )
            self.WM_CLIPBOARDUPDATE = 0x031D
            ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)
        except Exception as e:
            logger.error(f"Failed to register window class: {e}")
            # Re-raise to be caught by main's exception handler
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
            except Exception:
                # Skip any windows that cause errors when getting class name
                pass
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

        while self.is_running:
            time.sleep(10)  # Check every 10 seconds
            if time.time() - self.last_activity > 30:  # 30 seconds without activity
                logger.warning("Possible deadlock detected, requesting restart...")
                self.restart_flag = True
                self.is_running = False
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
                logger.warning(f"Clipboard read attempt {attempt + 1} failed: {e}")
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
                logger.warning(f"Clipboard write attempt {attempt + 1} failed: {e}")
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
            # Log full traceback for debugging
            import traceback

            logger.error(
                f"Error handling clipboard change: {e}\n" + traceback.format_exc()
            )
            self.last_activity = time.time()

    def cleanup(self):
        """Clean up resources"""

        self.is_running = False
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
            # Pump messages until quit; restart_flag set by watchdog on deadlock
            win32gui.PumpMessages()
            # Return restart flag indicating whether auto-restart requested
            return self.restart_flag
        except Exception as e:
            logger.error(f"Message pump error: {e}")
            # On message pump error, signal restart
            return True
        finally:
            # Always clean up resources, regardless of restart state
            self.cleanup()
