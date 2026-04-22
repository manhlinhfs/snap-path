@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name snap_path --add-data "logo.png;." snap_path.py
echo.
echo Build complete. Run: dist\snap_path.exe
pause
