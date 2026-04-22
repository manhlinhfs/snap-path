import hashlib
import json
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import keyboard
import pystray
from PIL import Image, ImageDraw, ImageGrab
import win32clipboard
import win32con

SAVE_DIR = Path.home() / "snap-claude"
CONFIG_PATH = Path.home() / "snap-claude" / "config.json"


def resource_path(filename: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", None) or Path(__file__).parent)
    return base / filename


def load_icon_images() -> tuple[Image.Image, Image.Image]:
    path = resource_path("logo.png")
    if path.exists():
        img = Image.open(path).convert("RGBA").resize((64, 64), Image.LANCZOS)
    else:
        img = make_tray_icon_image().convert("RGBA")
    paused = img.convert("LA").convert("RGBA")
    return img, paused


def load_config() -> dict:
    defaults = {
        "save_dir": str(Path.home() / "snap-claude"),
        "hotkey": "ctrl+shift+x",
    }
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {**defaults, **data}
    except Exception:
        return defaults.copy()


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def get_save_path(dt: datetime | None = None) -> Path:
    if dt is None:
        dt = datetime.now()
    return SAVE_DIR / f"screenshot_{dt.strftime('%Y%m%d_%H%M%S_%f')}.png"


def image_hash(img: Image.Image) -> str:
    return hashlib.md5(img.tobytes()).hexdigest()


def save_image(img: Image.Image) -> Path:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = get_save_path()
    img.save(path, format="PNG")
    return path


def get_clipboard_image() -> Image.Image | None:
    try:
        result = ImageGrab.grabclipboard()
        return result if isinstance(result, Image.Image) else None
    except Exception:
        return None


def set_clipboard_text(text: str) -> None:
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def make_tray_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), color=(0, 120, 212))
    draw = ImageDraw.Draw(img)
    draw.ellipse([14, 14, 50, 50], fill=(255, 255, 255))
    draw.ellipse([24, 24, 40, 40], fill=(0, 120, 212))
    return img


def open_folder() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["explorer", str(SAVE_DIR)])


def clipboard_watcher(stop_event: threading.Event) -> None:
    last_hash: str | None = None
    while not stop_event.is_set():
        try:
            img = get_clipboard_image()
            if img is not None:
                h = image_hash(img)
                if h != last_hash:
                    last_hash = h
                    path = save_image(img)
                    set_clipboard_text(str(path))
        except Exception as e:
            print(f"snap-claude error: {e}", file=__import__('sys').stderr)
        time.sleep(0.5)


def main() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    stop_event = threading.Event()

    threading.Thread(
        target=clipboard_watcher,
        args=(stop_event,),
        daemon=True,
    ).start()

    def on_exit(icon, item):
        stop_event.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open folder", lambda icon, item: open_folder()),
        pystray.MenuItem("Exit", on_exit),
    )
    icon = pystray.Icon(
        "snap_claude", make_tray_icon_image(), "Snap Claude — Active", menu
    )
    icon.run()


if __name__ == "__main__":
    main()
