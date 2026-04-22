# snap-claude Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file Windows tray app that watches clipboard for images, saves them to `~/snap-claude/`, and replaces clipboard with the file path.

**Architecture:** One Python file (`snap_claude.py`) with a daemon thread polling the clipboard every 500ms via `PIL.ImageGrab.grabclipboard()`. When a new image is detected (deduplicated by MD5 hash), it saves the file and replaces clipboard with the path string. A `pystray` system tray icon on the main thread provides Open folder / Exit.

**Tech Stack:** Python 3.11+, Pillow (ImageGrab + Image), pywin32 (win32clipboard), pystray, PyInstaller

---

## File Structure

```
snap_claude/              ← project root (C:\Users\manhlinhfs\snap-claude)
├── snap_claude.py        ← entire app: helpers + clipboard + tray + main
├── requirements.txt      ← runtime + build deps
├── build.bat             ← PyInstaller one-liner
└── tests/
    ├── __init__.py
    └── test_snap_claude.py  ← unit tests for pure/mockable functions
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `build.bat`
- Create: `tests/__init__.py`
- Create: `snap_claude.py` (imports + constants only)

- [ ] **Step 1: Create `requirements.txt`**

```
Pillow>=10.0.0
pywin32>=306
pystray>=0.19.5
pyinstaller>=6.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Create `build.bat`**

```bat
@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name snap_claude snap_claude.py
echo.
echo Build complete. Run: dist\snap_claude.exe
pause
```

- [ ] **Step 3: Create `tests/__init__.py`** (empty file)

- [ ] **Step 4: Create `snap_claude.py` with skeleton**

```python
import hashlib
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import pystray
from PIL import Image, ImageDraw, ImageGrab
import win32clipboard
import win32con

SAVE_DIR = Path.home() / "snap-claude"
```

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: all packages install without error.

- [ ] **Step 6: Verify imports work**

Run: `python -c "import snap_claude; print('OK')"`
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git init
git add snap_claude.py requirements.txt build.bat tests/__init__.py
git commit -m "chore: project scaffolding"
```

---

### Task 2: Pure helper functions (TDD)

**Files:**
- Modify: `snap_claude.py` — add `get_save_path()`, `image_hash()`
- Create: `tests/test_snap_claude.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_snap_claude.py
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import win32con
from PIL import Image

import snap_claude


def make_img(color=(255, 0, 0), size=(10, 10)) -> Image.Image:
    return Image.new("RGB", size, color=color)


class TestGetSavePath:
    def test_uses_timestamp_format(self):
        dt = datetime(2026, 4, 22, 14, 30, 55)
        path = snap_claude.get_save_path(dt)
        assert path.name == "screenshot_20260422_143055.png"

    def test_parent_is_save_dir(self):
        path = snap_claude.get_save_path(datetime(2026, 1, 1, 0, 0, 0))
        assert path.parent == snap_claude.SAVE_DIR

    def test_defaults_to_now(self):
        path = snap_claude.get_save_path()
        assert path.name.startswith("screenshot_")
        assert path.suffix == ".png"


class TestImageHash:
    def test_same_image_returns_same_hash(self):
        img = make_img()
        assert snap_claude.image_hash(img) == snap_claude.image_hash(img)

    def test_different_images_return_different_hashes(self):
        img1 = make_img(color=(255, 0, 0))
        img2 = make_img(color=(0, 255, 0))
        assert snap_claude.image_hash(img1) != snap_claude.image_hash(img2)

    def test_returns_32_char_hex_string(self):
        h = snap_claude.image_hash(make_img())
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'get_save_path'`

- [ ] **Step 3: Implement `get_save_path` and `image_hash` in `snap_claude.py`**

Add after the `SAVE_DIR` line:

```python
def get_save_path(dt: datetime | None = None) -> Path:
    if dt is None:
        dt = datetime.now()
    return SAVE_DIR / f"screenshot_{dt.strftime('%Y%m%d_%H%M%S')}.png"


def image_hash(img: Image.Image) -> str:
    return hashlib.md5(img.tobytes()).hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: 7 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add snap_claude.py tests/test_snap_claude.py
git commit -m "feat: add get_save_path and image_hash helpers"
```

---

### Task 3: Image saving (TDD)

**Files:**
- Modify: `snap_claude.py` — add `save_image()`
- Modify: `tests/test_snap_claude.py` — add `TestSaveImage`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_snap_claude.py`:

```python
class TestSaveImage:
    def test_saves_png_file_in_save_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_claude, "SAVE_DIR", tmp_path)
        path = snap_claude.save_image(make_img())
        assert path.exists()
        assert path.suffix == ".png"
        assert path.parent == tmp_path

    def test_saved_file_is_valid_image(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_claude, "SAVE_DIR", tmp_path)
        img = make_img(color=(0, 128, 255), size=(20, 20))
        path = snap_claude.save_image(img)
        loaded = Image.open(path)
        assert loaded.size == (20, 20)

    def test_creates_save_dir_if_missing(self, tmp_path, monkeypatch):
        new_dir = tmp_path / "new_subdir"
        monkeypatch.setattr(snap_claude, "SAVE_DIR", new_dir)
        assert not new_dir.exists()
        snap_claude.save_image(make_img())
        assert new_dir.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py::TestSaveImage -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'save_image'`

- [ ] **Step 3: Implement `save_image` in `snap_claude.py`**

```python
def save_image(img: Image.Image) -> Path:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    path = get_save_path()
    img.save(path, format="PNG")
    return path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: all 10 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add snap_claude.py tests/test_snap_claude.py
git commit -m "feat: add save_image"
```

---

### Task 4: Clipboard read/write (TDD)

**Files:**
- Modify: `snap_claude.py` — add `get_clipboard_image()`, `set_clipboard_text()`
- Modify: `tests/test_snap_claude.py` — add `TestGetClipboardImage`, `TestSetClipboardText`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_snap_claude.py`:

```python
class TestGetClipboardImage:
    def test_returns_image_when_clipboard_has_image(self):
        img = make_img()
        with patch("snap_claude.ImageGrab.grabclipboard", return_value=img):
            result = snap_claude.get_clipboard_image()
        assert result is img

    def test_returns_none_when_clipboard_has_file_list(self):
        with patch("snap_claude.ImageGrab.grabclipboard", return_value=["file.txt"]):
            result = snap_claude.get_clipboard_image()
        assert result is None

    def test_returns_none_when_clipboard_is_empty(self):
        with patch("snap_claude.ImageGrab.grabclipboard", return_value=None):
            result = snap_claude.get_clipboard_image()
        assert result is None

    def test_returns_none_on_exception(self):
        with patch("snap_claude.ImageGrab.grabclipboard", side_effect=OSError("fail")):
            result = snap_claude.get_clipboard_image()
        assert result is None


class TestSetClipboardText:
    def test_opens_and_closes_clipboard(self):
        with patch("snap_claude.win32clipboard.OpenClipboard") as m_open, \
             patch("snap_claude.win32clipboard.EmptyClipboard"), \
             patch("snap_claude.win32clipboard.SetClipboardData"), \
             patch("snap_claude.win32clipboard.CloseClipboard") as m_close:
            snap_claude.set_clipboard_text("C:\\snap-claude\\test.png")
        m_open.assert_called_once()
        m_close.assert_called_once()

    def test_sets_unicode_text(self):
        with patch("snap_claude.win32clipboard.OpenClipboard"), \
             patch("snap_claude.win32clipboard.EmptyClipboard"), \
             patch("snap_claude.win32clipboard.SetClipboardData") as m_set, \
             patch("snap_claude.win32clipboard.CloseClipboard"):
            snap_claude.set_clipboard_text("C:\\snap-claude\\test.png")
        m_set.assert_called_once_with(
            win32con.CF_UNICODETEXT, "C:\\snap-claude\\test.png"
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_snap_claude.py::TestGetClipboardImage tests/test_snap_claude.py::TestSetClipboardText -v`
Expected: `AttributeError: module 'snap_claude' has no attribute 'get_clipboard_image'`

- [ ] **Step 3: Implement `get_clipboard_image` and `set_clipboard_text` in `snap_claude.py`**

```python
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
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `pytest tests/test_snap_claude.py -v`
Expected: all 16 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add snap_claude.py tests/test_snap_claude.py
git commit -m "feat: add clipboard read/write functions"
```

---

### Task 5: Tray icon, watcher loop, and main

**Files:**
- Modify: `snap_claude.py` — add `make_tray_icon_image()`, `open_folder()`, `clipboard_watcher()`, `main()`

No unit tests for this task — tray and subprocess calls require manual verification.

- [ ] **Step 1: Add `make_tray_icon_image` and `open_folder`**

Append to `snap_claude.py`:

```python
def make_tray_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), color=(0, 120, 212))
    draw = ImageDraw.Draw(img)
    draw.ellipse([14, 14, 50, 50], fill=(255, 255, 255))
    draw.ellipse([24, 24, 40, 40], fill=(0, 120, 212))
    return img


def open_folder() -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["explorer", str(SAVE_DIR)])
```

- [ ] **Step 2: Add `clipboard_watcher`**

```python
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
        except Exception:
            pass
        time.sleep(0.5)
```

- [ ] **Step 3: Add `main`**

```python
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
```

- [ ] **Step 4: Manual test — run the app**

Run: `python snap_claude.py`
Expected:
- A blue circle icon appears in the system tray (bottom-right taskbar)
- Tooltip shows "Snap Claude — Active" on hover
- Right-click shows "Open folder" and "Exit"

- [ ] **Step 5: Manual test — screenshot flow**

1. Press `Win+Shift+S` to open Snipping Tool, draw a selection
2. Immediately open Notepad and press `Ctrl+V`
3. Expected: a file path like `C:\Users\manhlinhfs\snap-claude\screenshot_20260422_143055.png` is pasted (not the image)
4. In Claude Code CLI, type that path — Claude should be able to `Read` the image

- [ ] **Step 6: Manual test — Open folder**

Right-click tray icon → "Open folder"
Expected: Windows Explorer opens `C:\Users\manhlinhfs\snap-claude\` showing the saved PNG files.

- [ ] **Step 7: Manual test — Exit**

Right-click tray icon → "Exit"
Expected: icon disappears from tray, app terminates.

- [ ] **Step 8: Commit**

```bash
git add snap_claude.py
git commit -m "feat: add tray icon, clipboard watcher, and main"
```

---

### Task 6: Build single `.exe`

**Files:**
- No code changes

- [ ] **Step 1: Run build script**

Run: `build.bat`
Expected: PyInstaller output ends with `Successfully built snap_claude.exe`, file appears at `dist\snap_claude.exe`.

- [ ] **Step 2: Verify exe runs**

Double-click `dist\snap_claude.exe`
Expected: tray icon appears, same behavior as `python snap_claude.py`.

- [ ] **Step 3: Test screenshot flow with the exe**

Repeat Task 5 Step 5 but with the exe running instead of the Python script.
Expected: identical behavior.

- [ ] **Step 4: Commit**

```bash
git add build.bat
git commit -m "chore: add build script, produce snap_claude.exe"
```

---

## Usage After Build

1. Copy `dist\snap_claude.exe` to any location (e.g., `C:\Users\manhlinhfs\snap-claude\`)
2. Double-click to run — tray icon appears
3. Take screenshots with Snipping Tool (`Win+Shift+S`)
4. Paste (`Ctrl+V`) in Claude Code CLI — the file path is ready to use
5. Claude reads the image via its `Read` tool

**Optional auto-start:** Press `Win+R` → `shell:startup` → paste a shortcut to `snap_claude.exe` there.
