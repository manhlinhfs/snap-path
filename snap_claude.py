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


def get_save_path(dt: datetime | None = None) -> Path:
    if dt is None:
        dt = datetime.now()
    return SAVE_DIR / f"screenshot_{dt.strftime('%Y%m%d_%H%M%S')}.png"


def image_hash(img: Image.Image) -> str:
    return hashlib.md5(img.tobytes()).hexdigest()
