# snap-claude Toggle + Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pause/resume toggle (tray menu + `Ctrl+Shift+X` hotkey), icon/tooltip state changes, and a tkinter settings dialog to snap-claude.

**Architecture:** All changes are in the single `snap_claude.py` file. New state: `paused_event: threading.Event` passed to the watcher thread; `config: dict` loaded from `~/snap-claude/config.json` at startup. `keyboard` library handles the global hotkey. `tkinter` (stdlib) handles the settings dialog in a daemon thread.

**Tech Stack:** Python 3.11+, existing deps unchanged + `keyboard` (new)

---

## File Structure

```
snap_claude/
├── snap_claude.py          ← all changes here (~180 lines when done)
├── requirements.txt        ← add keyboard>=0.13.5
├── build.bat               ← add --add-data "logo.png;."
└── tests/
    └── test_snap_claude.py ← add 5 new test classes
```

---

### Task 1: Dependencies + resource_path + load_icon_images (TDD)

**Files:**
- Modify: `C:\Users\manhlinhfs\snap-claude\requirements.txt`
- Modify: `C:\Users\manhlinhfs\snap-claude\snap_claude.py` — add imports, `resource_path()`, `load_icon_images()`
- Modify: `C:\Users\manhlinhfs\snap-claude\tests\test_snap_claude.py` — add `TestResourcePath`, `TestLoadIconImages`

- [ ] **Step 1: Add `keyboard` to `requirements.txt`**

Final content of `C:\Users\manhlinhfs\snap-claude\requirements.txt`:
```
Pillow>=10.0.0
pywin32>=306
pystray>=0.19.5
pyinstaller>=6.0.0
pytest>=8.0.0
keyboard>=0.13.5
```

- [ ] **Step 2: Install keyboard**

Run from `C:\Users\manhlinhfs\snap-claude`:
```
pip install keyboard>=0.13.5
```
Expected: `Successfully installed keyboard-...`

- [ ] **Step 3: Add imports to `snap_claude.py`**

Replace the current import block (lines 1–11) with:
```python
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
```

- [ ] **Step 4: Write failing tests**

Add to the END of `C:\Users\manhlinhfs\snap-claude\tests\test_snap_claude.py`:

```python
class TestResourcePath:
    def test_returns_path_relative_to_script_without_meipass(self, monkeypatch):
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        result = snap_claude.resource_path("logo.png")
        assert result == Path(snap_claude.__file__).parent / "logo.png"

    def test_returns_path_under_meipass_when_set(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path))
        result = snap_claude.resource_path("logo.png")
        assert result == tmp_path / "logo.png"


class TestLoadIconImages:
    def test_returns_two_pil_images(self):
        active, paused = snap_claude.load_icon_images()
        assert isinstance(active, Image.Image)
        assert isinstance(paused, Image.Image)

    def test_both_icons_are_64x64(self):
        active, paused = snap_claude.load_icon_images()
        assert active.size == (64, 64)
        assert paused.size == (64, 64)

    def test_paused_is_visually_different_from_active(self):
        active, paused = snap_claude.load_icon_images()
        assert snap_claude.image_hash(active.convert("RGB")) != snap_claude.image_hash(paused.convert("RGB"))

    def test_falls_back_when_logo_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path))
        active, paused = snap_claude.load_icon_images()
        assert isinstance(active, Image.Image)
        assert active.size == (64, 64)
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py::TestResourcePath tests/test_snap_claude.py::TestLoadIconImages -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'resource_path'`

- [ ] **Step 6: Add `resource_path` and `load_icon_images` to `snap_claude.py`**

Insert after the `SAVE_DIR` line:

```python
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
```

- [ ] **Step 7: Run all tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: 19+ tests PASSED

- [ ] **Step 8: Commit**

```bash
git -C C:\Users\manhlinhfs\snap-claude add requirements.txt snap_claude.py tests/test_snap_claude.py
git -C C:\Users\manhlinhfs\snap-claude commit -m "feat: add resource_path and load_icon_images"
```

---

### Task 2: Config load/save (TDD)

**Files:**
- Modify: `C:\Users\manhlinhfs\snap-claude\snap_claude.py` — add `CONFIG_PATH`, `load_config()`, `save_config()`
- Modify: `C:\Users\manhlinhfs\snap-claude\tests\test_snap_claude.py` — add `TestLoadConfig`, `TestSaveConfig`

- [ ] **Step 1: Write failing tests**

Add to the END of `tests/test_snap_claude.py`:

```python
class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", tmp_path / "config.json")
        config = snap_claude.load_config()
        assert config["hotkey"] == "ctrl+shift+x"
        assert "save_dir" in config

    def test_reads_values_from_file(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"save_dir": "C:/custom", "hotkey": "ctrl+alt+z"}', encoding="utf-8")
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", cfg_path)
        config = snap_claude.load_config()
        assert config["save_dir"] == "C:/custom"
        assert config["hotkey"] == "ctrl+alt+z"

    def test_merges_defaults_for_missing_keys(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"hotkey": "ctrl+alt+z"}', encoding="utf-8")
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", cfg_path)
        config = snap_claude.load_config()
        assert "save_dir" in config
        assert config["hotkey"] == "ctrl+alt+z"

    def test_returns_defaults_on_malformed_json(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text("not json!!!!", encoding="utf-8")
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", cfg_path)
        config = snap_claude.load_config()
        assert config["hotkey"] == "ctrl+shift+x"


class TestSaveConfig:
    def test_writes_correct_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", tmp_path / "config.json")
        snap_claude.save_config({"save_dir": "C:/test", "hotkey": "ctrl+alt+z"})
        data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert data["save_dir"] == "C:/test"
        assert data["hotkey"] == "ctrl+alt+z"

    def test_creates_parent_dir_if_missing(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "sub" / "config.json"
        monkeypatch.setattr(snap_claude, "CONFIG_PATH", cfg_path)
        snap_claude.save_config({"save_dir": "C:/test", "hotkey": "ctrl+alt+z"})
        assert cfg_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py::TestLoadConfig tests/test_snap_claude.py::TestSaveConfig -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'load_config'`

- [ ] **Step 3: Add `CONFIG_PATH`, `load_config`, `save_config` to `snap_claude.py`**

Add after the `SAVE_DIR` line (before `resource_path`):

```python
CONFIG_PATH = Path.home() / "snap-claude" / "config.json"
```

Add after `load_icon_images`:

```python
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
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: 25+ tests PASSED

- [ ] **Step 5: Commit**

```bash
git -C C:\Users\manhlinhfs\snap-claude add snap_claude.py tests/test_snap_claude.py
git -C C:\Users\manhlinhfs\snap-claude commit -m "feat: add load_config and save_config"
```

---

### Task 3: toggle_pause + register_hotkey (TDD)

**Files:**
- Modify: `C:\Users\manhlinhfs\snap-claude\snap_claude.py` — add `_current_hotkey`, `toggle_pause()`, `register_hotkey()`
- Modify: `C:\Users\manhlinhfs\snap-claude\tests\test_snap_claude.py` — add `TestTogglePause`, `TestRegisterHotkey`

- [ ] **Step 1: Add missing import to test file**

Open `C:\Users\manhlinhfs\snap-claude\tests\test_snap_claude.py` and add `import threading` to the imports block at the top (after `import pytest`):

```python
import threading
```

- [ ] **Step 2: Write failing tests**

Add to the END of `tests/test_snap_claude.py`:

```python
class TestTogglePause:
    def test_sets_paused_event_when_active(self):
        paused_event = threading.Event()
        icon = MagicMock()
        snap_claude.toggle_pause(paused_event, icon, make_img(), make_img())
        assert paused_event.is_set()

    def test_clears_paused_event_when_paused(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        snap_claude.toggle_pause(paused_event, icon, make_img(), make_img())
        assert not paused_event.is_set()

    def test_sets_icon_to_paused_image(self):
        paused_event = threading.Event()
        icon = MagicMock()
        active_img = make_img(color=(0, 0, 255))
        paused_img = make_img(color=(128, 128, 128))
        snap_claude.toggle_pause(paused_event, icon, active_img, paused_img)
        assert icon.icon is paused_img

    def test_sets_icon_to_active_image_on_resume(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        active_img = make_img(color=(0, 0, 255))
        paused_img = make_img(color=(128, 128, 128))
        snap_claude.toggle_pause(paused_event, icon, active_img, paused_img)
        assert icon.icon is active_img

    def test_sets_title_to_paused(self):
        paused_event = threading.Event()
        icon = MagicMock()
        snap_claude.toggle_pause(paused_event, icon, make_img(), make_img())
        assert icon.title == "Snap Claude — Paused"

    def test_sets_title_to_active_on_resume(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        snap_claude.toggle_pause(paused_event, icon, make_img(), make_img())
        assert icon.title == "Snap Claude — Active"


class TestRegisterHotkey:
    def test_returns_true_on_success(self, monkeypatch):
        monkeypatch.setattr(snap_claude, "_current_hotkey", None)
        with patch("snap_claude.keyboard.add_hotkey"), \
             patch("snap_claude.keyboard.remove_hotkey"):
            result = snap_claude.register_hotkey("ctrl+shift+x", lambda: None)
        assert result is True

    def test_returns_false_on_invalid_hotkey(self, monkeypatch):
        monkeypatch.setattr(snap_claude, "_current_hotkey", None)
        with patch("snap_claude.keyboard.add_hotkey", side_effect=ValueError("bad")):
            result = snap_claude.register_hotkey("!!!bad!!!", lambda: None)
        assert result is False

    def test_removes_previous_hotkey_before_registering(self, monkeypatch):
        monkeypatch.setattr(snap_claude, "_current_hotkey", "ctrl+shift+x")
        with patch("snap_claude.keyboard.remove_hotkey") as mock_remove, \
             patch("snap_claude.keyboard.add_hotkey"):
            snap_claude.register_hotkey("ctrl+shift+z", lambda: None)
        mock_remove.assert_called_once_with("ctrl+shift+x")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py::TestTogglePause tests/test_snap_claude.py::TestRegisterHotkey -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'toggle_pause'`

- [ ] **Step 4: Add `_current_hotkey`, `toggle_pause`, `register_hotkey` to `snap_claude.py`**

Add after `save_config`:

```python
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
```

- [ ] **Step 5: Run all tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: 34+ tests PASSED

- [ ] **Step 6: Commit**

```bash
git -C C:\Users\manhlinhfs\snap-claude add snap_claude.py tests/test_snap_claude.py
git -C C:\Users\manhlinhfs\snap-claude commit -m "feat: add toggle_pause and register_hotkey"
```

---

### Task 4: Settings dialog + update clipboard_watcher + main

**Files:**
- Modify: `C:\Users\manhlinhfs\snap-claude\snap_claude.py` — add `_settings_open`, `open_settings()`, update `clipboard_watcher()`, rewrite `main()`

No new unit tests — tkinter UI and main() wiring require manual verification.

- [ ] **Step 1: Add `_settings_open` global and `open_settings` function**

Add after `register_hotkey`:

```python
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
            if new_hotkey != config["hotkey"]:
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
```

- [ ] **Step 2: Update `clipboard_watcher` to accept `paused_event`**

Replace the existing `clipboard_watcher` function with:

```python
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
```

- [ ] **Step 3: Rewrite `main`**

Replace the existing `main` function with:

```python
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
```

- [ ] **Step 4: Run all existing tests to verify nothing broke**

Run: `pytest tests/test_snap_claude.py -v`
Expected: all tests PASSED (no regressions)

- [ ] **Step 5: Manual test — run the app**

Run: `python C:\Users\manhlinhfs\snap-claude\snap_claude.py`
Expected:
- Tray icon appears (logo.png, full color)
- Tooltip: "Snap Claude — Active"
- Right-click menu shows: Pause / Open folder / Settings / Exit

- [ ] **Step 6: Manual test — toggle via menu**

Right-click → "Pause"
Expected:
- Menu item changes to "Resume"
- Icon goes grayscale
- Tooltip: "Snap Claude — Paused"
- Taking a screenshot and pasting → image pastes (not a path), confirming watcher is paused

Right-click → "Resume"
Expected: icon returns to color, tooltip "Snap Claude — Active", screenshots capture normally again

- [ ] **Step 7: Manual test — toggle via hotkey**

Press `Ctrl+Shift+X`
Expected: same toggle behavior as menu

- [ ] **Step 8: Manual test — Settings dialog**

Right-click → "Settings"
Expected:
- Small window with "Save folder" field (current path), Browse button, "Hotkey" field (`ctrl+shift+x`), Save/Cancel
- Click Browse → folder picker opens
- Change hotkey to `ctrl+shift+z`, click Save → old hotkey stops working, new hotkey `Ctrl+Shift+Z` toggles app
- Re-open Settings, change hotkey back to `ctrl+shift+x`, Save

- [ ] **Step 9: Manual test — double-open guard**

Right-click → "Settings" twice quickly
Expected: only one Settings window opens

- [ ] **Step 10: Commit**

```bash
git -C C:\Users\manhlinhfs\snap-claude add snap_claude.py
git -C C:\Users\manhlinhfs\snap-claude commit -m "feat: add settings dialog, toggle, update main"
```

---

### Task 5: Update build.bat and rebuild exe

**Files:**
- Modify: `C:\Users\manhlinhfs\snap-claude\build.bat`

- [ ] **Step 1: Update `build.bat`**

Replace content of `C:\Users\manhlinhfs\snap-claude\build.bat` with:

```bat
@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name snap_claude --add-data "logo.png;." snap_claude.py
echo.
echo Build complete. Run: dist\snap_claude.exe
pause
```

- [ ] **Step 2: Run build**

Run: `C:\Users\manhlinhfs\snap-claude\build.bat`
Expected: `dist\snap_claude.exe` created successfully.

- [ ] **Step 3: Manual test — verify exe uses logo**

Double-click `dist\snap_claude.exe`
Expected: tray icon shows the logo.png icon (not the blue circle fallback), all features work.

- [ ] **Step 4: Commit**

```bash
git -C C:\Users\manhlinhfs\snap-claude add build.bat
git -C C:\Users\manhlinhfs\snap-claude commit -m "chore: update build.bat with logo and keyboard dep"
```
