# SnapPath

A lightweight Windows tray utility that watches your clipboard for screenshots and replaces each image with its saved file path — so you can paste the path directly into tools that accept file references instead of raw images (e.g. Claude Code CLI).

## How it works

1. Take a screenshot with Snipping Tool (`Win+Shift+S`) or any other tool that copies to clipboard
2. SnapPath detects the new image, saves it as a PNG to your configured folder
3. The clipboard is automatically replaced with the file path (e.g. `C:\Users\you\snap-path\screenshot_20260422_143055_123456.png`)
4. Paste (`Ctrl+V`) the path anywhere — Claude Code CLI, Notepad, a chat box

## Download

Grab the latest `snap_path.exe` from [Releases](../../releases).

No Python required — it's a single self-contained executable.

## Usage

1. Double-click `snap_path.exe` — a tray icon appears in the system tray
2. Take screenshots normally; the clipboard is handled automatically
3. Right-click the tray icon for options:
   - **Pause / Resume** — temporarily stop watching the clipboard
   - **Open folder** — open the save directory in Explorer
   - **Settings** — change the save folder or hotkey
   - **Exit** — quit the app

## Hotkey

Default: `Ctrl+Shift+X` — toggles pause/resume.  
Change it any time from **Settings** in the tray menu.

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Save folder | `%USERPROFILE%\snap-path` | Where PNG files are saved |
| Hotkey | `ctrl+shift+x` | Global pause/resume toggle |

Config is stored at `%USERPROFILE%\snap-path\config.json`.

## Auto-start with Windows

Press `Win+R`, type `shell:startup`, press Enter.  
Copy a shortcut to `snap_path.exe` into that folder.

## Build from source

Requirements: Python 3.11+

```bat
pip install -r requirements.txt
build.bat
```

Output: `dist\snap_path.exe`

## Run tests

```bat
pytest tests/ -v
```

## License

MIT
