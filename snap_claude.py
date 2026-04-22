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


_current_hotkey: str | None = None


def toggle_pause(
    paused_event: threading.Event,
    icon: pystray.Icon,
    icon_active: Image.Image,
    icon_paused: Image.Image,
) -> None:
    if paused_event.is_set():
        paused_event.clear()
        icon.icon = icon_active
        icon.title = "Snap Claude — Active"
    else:
        paused_event.set()
        icon.icon = icon_paused
        icon.title = "Snap Claude — Paused"
    icon.update_menu()


def register_hotkey(hotkey_str: str, callback) -> bool:
    global _current_hotkey
    try:
        if _current_hotkey:
            try:
                keyboard.remove_hotkey(_current_hotkey)
            except Exception:
                pass
            _current_hotkey = None
        keyboard.add_hotkey(hotkey_str, callback)
        _current_hotkey = hotkey_str
        return True
    except Exception:
        return False


_settings_open: bool = False


def open_settings(
    config: dict,
    paused_event: threading.Event,
    icon: pystray.Icon,
    icon_active: Image.Image,
    icon_paused: Image.Image,
) -> None:
    global _settings_open
    if _settings_open:
        return

    def run() -> None:
        global _settings_open, SAVE_DIR
        _settings_open = True
        win = tk.Tk()
        win.title("Snap Claude Settings")
        win.resizable(False, False)

        tk.Label(win, text="Save folder:").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        save_var = tk.StringVar(value=config["save_dir"])
        tk.Entry(win, textvariable=save_var, width=40).grid(row=1, column=0, padx=(8, 0), pady=(0, 4))

        def browse() -> None:
            path = filedialog.askdirectory(initialdir=config["save_dir"])
            if path:
                save_var.set(path)

        tk.Button(win, text="Browse", command=browse).grid(row=1, column=1, padx=(4, 8))

        tk.Label(win, text="Hotkey:").grid(row=2, column=0, sticky="w", padx=8, pady=(4, 2))
        hotkey_var = tk.StringVar(value=config["hotkey"])
        tk.Entry(win, textvariable=hotkey_var, width=40).grid(row=3, column=0, padx=(8, 0), pady=(0, 8))

        def on_save() -> None:
            global SAVE_DIR
            new_dir = save_var.get().strip()
            new_hotkey = hotkey_var.get().strip()
            if new_hotkey != config["hotkey"] or _current_hotkey is None:
                if not register_hotkey(
                    new_hotkey,
                    lambda: toggle_pause(paused_event, icon, icon_active, icon_paused),
                ):
                    messagebox.showerror(
                        "Invalid hotkey",
                        f"Could not register '{new_hotkey}'. Hotkey unchanged.",
                    )
                    return
            config["save_dir"] = new_dir
            config["hotkey"] = new_hotkey
            SAVE_DIR = Path(new_dir)
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            save_config(config)
            win.destroy()

        btn_frame = tk.Frame(win)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(0, 8))
        tk.Button(btn_frame, text="Save", command=on_save, width=10).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Cancel", command=win.destroy, width=10).pack(side="left", padx=4)

        win.mainloop()
        _settings_open = False

    threading.Thread(target=run, daemon=True).start()


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


def clipboard_watcher(stop_event: threading.Event, paused_event: threading.Event) -> None:
    last_hash: str | None = None
    while not stop_event.is_set():
        if not paused_event.is_set():
            try:
                img = get_clipboard_image()
                if img is not None:
                    h = image_hash(img)
                    if h != last_hash:
                        last_hash = h
                        path = save_image(img)
                        set_clipboard_text(str(path))
            except Exception as e:
                print(f"snap-claude error: {e}", file=sys.stderr)
        time.sleep(0.5)


def main() -> None:
    global SAVE_DIR
    config = load_config()
    SAVE_DIR = Path(config["save_dir"])
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    icon_active, icon_paused = load_icon_images()
    stop_event = threading.Event()
    paused_event = threading.Event()

    threading.Thread(
        target=clipboard_watcher,
        args=(stop_event, paused_event),
        daemon=True,
    ).start()

    icon_ref: list = [None]

    def on_toggle_hotkey() -> None:
        if icon_ref[0] is not None:
            toggle_pause(paused_event, icon_ref[0], icon_active, icon_paused)

    register_hotkey(config["hotkey"], on_toggle_hotkey)

    def on_exit(ic, item) -> None:
        stop_event.set()
        ic.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: "Resume" if paused_event.is_set() else "Pause",
            lambda ic, item: toggle_pause(paused_event, ic, icon_active, icon_paused),
        ),
        pystray.MenuItem("Open folder", lambda ic, item: open_folder()),
        pystray.MenuItem(
            "Settings",
            lambda ic, item: open_settings(config, paused_event, ic, icon_active, icon_paused),
        ),
        pystray.MenuItem("Exit", on_exit),
    )
    tray_icon = pystray.Icon("snap_claude", icon_active, "Snap Claude — Active", menu)
    icon_ref[0] = tray_icon
    tray_icon.run()


if __name__ == "__main__":
    main()
