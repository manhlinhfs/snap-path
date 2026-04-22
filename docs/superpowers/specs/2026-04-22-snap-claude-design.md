# snap-claude — Design Spec
Date: 2026-04-22

## Problem
Claude Code CLI cannot accept pasted images directly. Users need a way to reference screenshots as file paths that Claude can read via its `Read` tool.

## Solution
A lightweight Windows background app that watches the clipboard. When the user takes a screenshot with Snipping Tool (which puts image data on the clipboard), the app saves the image to a local folder and replaces the clipboard content with the file path. The user then pastes the path into Claude Code CLI.

## Architecture

Single Python file (`snap_claude.py`), compiled to `snap_claude.exe` via PyInstaller.

### Components

**1. Clipboard Watcher**
- Polls clipboard every 500ms using `win32clipboard`
- Detects when clipboard format changes to image (CF_DIB or CF_BITMAP)
- Deduplicates: tracks last saved image hash to avoid saving the same image twice
- On new image detected → triggers Image Saver

**2. Image Saver**
- Saves image to `C:\Users\<user>\snap-claude\` as `screenshot_YYYYMMDD_HHMMSS.png`
- Uses `Pillow` to convert clipboard bitmap to PNG
- Returns the saved file path

**3. Clipboard Replacer**
- Replaces clipboard content with the file path string (plain text)
- Uses `win32clipboard` to write CF_UNICODETEXT

**4. System Tray Icon**
- Built with `pystray` + `Pillow` (generates a simple icon programmatically)
- Shows tooltip: "Snap Claude — Active"
- Right-click menu:
  - `Open folder` — opens `snap-claude/` in Explorer
  - `Exit` — stops the app

### Threading Model
- Main thread: `pystray` system tray (blocks)
- Daemon thread: clipboard watcher loop

## File Naming
`screenshot_YYYYMMDD_HHMMSS.png` — timestamp-based, no collisions for human-speed usage.

## Storage
All screenshots saved to `C:\Users\<user>\snap-claude\`. No automatic cleanup (user manages manually via "Open folder").

## Dependencies
- `Pillow` — image handling
- `pywin32` (`win32clipboard`, `win32con`) — clipboard access
- `pystray` — system tray

## Packaging
`pyinstaller --onefile --windowed --name snap_claude snap_claude.py`
Produces a single `snap_claude.exe`, no install required.

## Error Handling
- If save fails (disk full, permissions): show Windows balloon notification via tray, skip (don't crash)
- If clipboard read fails: log to stderr, continue polling

## Out of Scope
- Auto-start with Windows (user can add shortcut to Startup folder manually)
- Image compression or resizing
- Upload to cloud
- Hotkey customization
