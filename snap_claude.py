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
