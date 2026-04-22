@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name snap_claude --add-data "logo.png;." snap_claude.py
echo.
echo Build complete. Run: dist\snap_claude.exe
pause
