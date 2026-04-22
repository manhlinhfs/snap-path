# snap-claude Toggle + Config — Design Spec
Date: 2026-04-22

## Overview
Add pause/resume toggle (tray menu + global hotkey) and a settings dialog to snap-claude. Users can pause the clipboard watcher, change the save directory, and change the hotkey — all from the tray icon without editing files.

## New Features

### 1. Pause/Resume Toggle
- Tray menu item: **"Pause"** when active, **"Resume"** when paused
- Global hotkey (default `ctrl+shift+x`) triggers the same toggle
- When paused: clipboard watcher skips processing but thread stays alive
- When resumed: watcher processes clipboard normally

### 2. Icon States
- **Active:** `logo.png` loaded and resized to 64×64 (full color)
- **Paused:** same image converted to grayscale
- Both icons pre-generated at startup
- Icon updated via `icon.icon = <new_image>` on toggle

### 3. Tooltip States
- Active: `"Snap Claude — Active"`
- Paused: `"Snap Claude — Paused"`
- Updated via `icon.title = <new_title>` on toggle

### 4. Tray Menu (updated)
```
● Pause / Resume    ← toggles label
  Open folder
  Settings
  Exit
```

### 5. Settings Dialog
Built with **tkinter** (Python built-in, no extra deps).

Fields:
- **Save folder** — text entry + "Browse" button (opens folder picker)
- **Hotkey** — text entry, free-form string (e.g. `ctrl+shift+x`)

Buttons: **Save**, **Cancel**

Behavior on Save:
- Write new values to `config.json`
- Update `SAVE_DIR` in memory immediately
- Unregister old hotkey, register new hotkey — no restart needed
- If hotkey registration fails (invalid string): show tkinter messagebox error, keep old hotkey

Only one Settings window at a time (guard against double-open).

### 6. Config File
Location: **always** `~/snap-claude/config.json` — fixed, independent of `save_dir`. This ensures config is never lost when the user changes the save directory.

Default content created on first run:
```json
{
  "save_dir": "C:/Users/<user>/snap-claude",
  "hotkey": "ctrl+shift+x"
}
```

Loaded at startup. If file missing or malformed: use defaults silently.

## Implementation Changes to `snap_claude.py`

### New state (in `main`)
```python
paused_event = threading.Event()   # set = paused, clear = active
config: dict                        # loaded from config.json
icon_active: Image.Image            # logo full color, 64x64
icon_paused: Image.Image            # logo grayscale, 64x64
```

### `clipboard_watcher` change
Add `paused_event` parameter. Inside loop:
```python
if paused_event.is_set():
    time.sleep(0.5)
    continue
```

### New functions
- `load_config() -> dict` — read config.json, return dict with defaults for missing keys
- `save_config(config: dict) -> None` — write config.json
- `load_icon_images() -> tuple[Image.Image, Image.Image]` — returns (active, paused) images from logo.png
- `resource_path(filename: str) -> Path` — finds logo.png whether running as script or PyInstaller exe
- `toggle_pause(paused_event, icon, icon_active, icon_paused, menu_ref)` — flips paused_event, updates icon + tooltip + menu label
- `open_settings(config, paused_event, icon, ...)` — opens tkinter settings dialog, applies changes on Save
- `register_hotkey(hotkey_str, callback) -> bool` — calls `keyboard.add_hotkey`, returns True on success

### `make_tray_icon_image` removed
Replaced by `load_icon_images()` which loads `logo.png`.

## Dependencies
- `keyboard` (new): `pip install keyboard` — global hotkey registration
- `tkinter`: built into Python, no install needed
- All existing deps unchanged

## `build.bat` change
Add `--add-data "logo.png;."` to PyInstaller command:
```bat
pyinstaller --onefile --windowed --name snap_claude --add-data "logo.png;." snap_claude.py
```

## Error Handling
- `logo.png` missing: fall back to programmatically generated icon (existing `make_tray_icon_image` logic)
- Config malformed JSON: use defaults, overwrite with defaults on next Save
- Invalid hotkey string: show messagebox in Settings dialog, keep old hotkey
- Settings dialog already open: bring existing window to front (don't open second)

## Out of Scope
- Auto-start with Windows
- Multiple profiles / multiple hotkeys
- Hotkey capture UI (user types the key combo to record it)
