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
