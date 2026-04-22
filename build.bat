@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name snap_claude snap_claude.py
echo.
echo Build complete. Run: dist\snap_claude.exe
pause
