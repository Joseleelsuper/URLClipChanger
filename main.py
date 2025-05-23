import json
from pathlib import Path
import ctypes
import win32con
import win32clipboard
import win32gui
import pyperclip
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import List, Tuple, Dict, Any

# Load rules from an external JSON file
rules_path = Path(__file__).parent / "rules.json"

# Try to load rules.json first, then any json in the directory
if rules_path.exists():
    json_path = rules_path
else:
    # Search for any JSON file in the directory
    json_files = list(Path(__file__).parent.glob("*.json"))
    if json_files:
        json_path = json_files[0]
    else:
        raise FileNotFoundError("No rules JSON file found")

with open(json_path, "r", encoding="utf-8") as f:
    rules_json = json.load(f)
RULES: List[Tuple[List[str], str]] = [
    (rule["domains"], rule["suffix"]) for rule in rules_json
]


def add_suffix(url: str) -> str:
    parsed: Any = urlparse(url)
    host: str = parsed.netloc.lower()
    domains: List[str]
    suffix: str
    for domains, suffix in RULES:
        if any(d in host for d in domains):
            # 1) If the suffix is a full URL, return it as is
            if suffix.startswith(("http://", "https://")):
                return suffix
            # 2) If it starts with "/", add it to the path
            if suffix.startswith("/"):
                new_path: str = parsed.path.rstrip("/") + suffix
                return urlunparse(parsed._replace(path=new_path))
            # 3) If it starts with "?", merge with query params
            if suffix.startswith("?"):
                qs: Dict[str, List[str]] = parse_qs(parsed.query)
                p: str
                for p in suffix.lstrip("?").split("&"):
                    if "=" in p:
                        k, v = p.split("=", 1)
                        qs[k] = [v]
                new_q: str = urlencode(qs, doseq=True)
                return urlunparse(parsed._replace(query=new_q))
            # 4) Fallback: concatenate as is
            return url.rstrip("/") + suffix
    return url  # domain not recognized


class ClipboardWatcher:
    def __init__(self) -> None:
        self.ignore_next: bool = False
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc  # type: ignore
        wc.lpszClassName = "ClipboardWatcher"  # type: ignore
        self.class_atom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindow(
            "ClipboardWatcher", "Clipboard Watcher", 0, 0, 0, 0, 0, 0, 0, 0, None
        )
        global WM_CLIPBOARDUPDATE
        WM_CLIPBOARDUPDATE = 0x031D
        ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)

    def wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_CLIPBOARDUPDATE:
            self.handle_clipboard_change()
            return 0
        elif msg == win32con.WM_DESTROY:
            ctypes.windll.user32.RemoveClipboardFormatListener(self.hwnd)
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def handle_clipboard_change(self) -> None:
        if self.ignore_next:
            self.ignore_next = False
            return
        try:
            win32clipboard.OpenClipboard()
            data: str = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception:
            return
        if data.startswith(("http://", "https://")):
            new_url: str = add_suffix(data)
            if new_url != data:
                self.ignore_next = True
                pyperclip.copy(new_url)

    def run(self) -> None:
        win32gui.PumpMessages()


if __name__ == "__main__":
    # Requires: pip install pywin32 pyperclip
    watcher: ClipboardWatcher = ClipboardWatcher()
    watcher.run()
