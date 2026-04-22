# tests/test_snap_path.py
import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import win32con
from PIL import Image

import snap_path


def make_img(color=(255, 0, 0), size=(10, 10)) -> Image.Image:
    return Image.new("RGB", size, color=color)


class TestGetSavePath:
    def test_uses_timestamp_format(self):
        dt = datetime(2026, 4, 22, 14, 30, 55, 123456)
        path = snap_path.get_save_path(dt)
        assert path.name == "screenshot_20260422_143055_123456.png"

    def test_parent_is_save_dir(self):
        path = snap_path.get_save_path(datetime(2026, 1, 1, 0, 0, 0))
        assert path.parent == snap_path.SAVE_DIR

    def test_defaults_to_now(self):
        path = snap_path.get_save_path()
        assert path.name.startswith("screenshot_")
        assert path.suffix == ".png"


class TestImageHash:
    def test_same_image_returns_same_hash(self):
        img = make_img()
        assert snap_path.image_hash(img) == snap_path.image_hash(img)

    def test_different_images_return_different_hashes(self):
        img1 = make_img(color=(255, 0, 0))
        img2 = make_img(color=(0, 255, 0))
        assert snap_path.image_hash(img1) != snap_path.image_hash(img2)

    def test_returns_32_char_hex_string(self):
        h = snap_path.image_hash(make_img())
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)


class TestSaveImage:
    def test_saves_png_file_in_save_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_path, "SAVE_DIR", tmp_path)
        path = snap_path.save_image(make_img())
        assert path.exists()
        assert path.suffix == ".png"
        assert path.parent == tmp_path

    def test_saved_file_is_valid_image(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_path, "SAVE_DIR", tmp_path)
        img = make_img(color=(0, 128, 255), size=(20, 20))
        path = snap_path.save_image(img)
        loaded = Image.open(path)
        assert loaded.size == (20, 20)

    def test_creates_save_dir_if_missing(self, tmp_path, monkeypatch):
        new_dir = tmp_path / "new_subdir"
        monkeypatch.setattr(snap_path, "SAVE_DIR", new_dir)
        assert not new_dir.exists()
        snap_path.save_image(make_img())
        assert new_dir.exists()


class TestGetClipboardImage:
    def test_returns_image_when_clipboard_has_image(self):
        img = make_img()
        with patch("snap_path.ImageGrab.grabclipboard", return_value=img):
            result = snap_path.get_clipboard_image()
        assert result is img

    def test_returns_none_when_clipboard_has_file_list(self):
        with patch("snap_path.ImageGrab.grabclipboard", return_value=["file.txt"]):
            result = snap_path.get_clipboard_image()
        assert result is None

    def test_returns_none_when_clipboard_is_empty(self):
        with patch("snap_path.ImageGrab.grabclipboard", return_value=None):
            result = snap_path.get_clipboard_image()
        assert result is None

    def test_returns_none_on_exception(self):
        with patch("snap_path.ImageGrab.grabclipboard", side_effect=OSError("fail")):
            result = snap_path.get_clipboard_image()
        assert result is None


class TestSetClipboardText:
    def test_opens_and_closes_clipboard(self):
        with patch("snap_path.win32clipboard.OpenClipboard") as m_open, \
             patch("snap_path.win32clipboard.EmptyClipboard"), \
             patch("snap_path.win32clipboard.SetClipboardData"), \
             patch("snap_path.win32clipboard.CloseClipboard") as m_close:
            snap_path.set_clipboard_text("C:\\snap-path\\test.png")
        m_open.assert_called_once()
        m_close.assert_called_once()

    def test_sets_unicode_text(self):
        with patch("snap_path.win32clipboard.OpenClipboard"), \
             patch("snap_path.win32clipboard.EmptyClipboard"), \
             patch("snap_path.win32clipboard.SetClipboardData") as m_set, \
             patch("snap_path.win32clipboard.CloseClipboard"):
            snap_path.set_clipboard_text("C:\\snap-path\\test.png")
        m_set.assert_called_once_with(
            win32con.CF_UNICODETEXT, "C:\\snap-path\\test.png"
        )


class TestResourcePath:
    def test_returns_path_relative_to_script_without_meipass(self, monkeypatch):
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        result = snap_path.resource_path("logo.png")
        assert result == Path(snap_path.__file__).parent / "logo.png"

    def test_returns_path_under_meipass_when_set(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        result = snap_path.resource_path("logo.png")
        assert result == tmp_path / "logo.png"


class TestLoadIconImages:
    def test_returns_two_pil_images(self):
        active, paused = snap_path.load_icon_images()
        assert isinstance(active, Image.Image)
        assert isinstance(paused, Image.Image)

    def test_both_icons_are_64x64(self):
        active, paused = snap_path.load_icon_images()
        assert active.size == (64, 64)
        assert paused.size == (64, 64)

    def test_paused_is_visually_different_from_active(self):
        active, paused = snap_path.load_icon_images()
        assert snap_path.image_hash(active.convert("RGB")) != snap_path.image_hash(paused.convert("RGB"))

    def test_falls_back_when_logo_missing(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        active, paused = snap_path.load_icon_images()
        assert isinstance(active, Image.Image)
        assert active.size == (64, 64)


class TestLoadConfig:
    def test_returns_defaults_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_path, "CONFIG_PATH", tmp_path / "config.json")
        config = snap_path.load_config()
        assert config["hotkey"] == "ctrl+shift+x"
        assert "save_dir" in config

    def test_reads_values_from_file(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"save_dir": "C:/custom", "hotkey": "ctrl+alt+z"}', encoding="utf-8")
        monkeypatch.setattr(snap_path, "CONFIG_PATH", cfg_path)
        config = snap_path.load_config()
        assert config["save_dir"] == "C:/custom"
        assert config["hotkey"] == "ctrl+alt+z"

    def test_merges_defaults_for_missing_keys(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text('{"hotkey": "ctrl+alt+z"}', encoding="utf-8")
        monkeypatch.setattr(snap_path, "CONFIG_PATH", cfg_path)
        config = snap_path.load_config()
        assert "save_dir" in config
        assert config["hotkey"] == "ctrl+alt+z"

    def test_returns_defaults_on_malformed_json(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text("not json!!!!", encoding="utf-8")
        monkeypatch.setattr(snap_path, "CONFIG_PATH", cfg_path)
        config = snap_path.load_config()
        assert config["hotkey"] == "ctrl+shift+x"


class TestSaveConfig:
    def test_writes_correct_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(snap_path, "CONFIG_PATH", tmp_path / "config.json")
        snap_path.save_config({"save_dir": "C:/test", "hotkey": "ctrl+alt+z"})
        data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert data["save_dir"] == "C:/test"
        assert data["hotkey"] == "ctrl+alt+z"

    def test_creates_parent_dir_if_missing(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "sub" / "config.json"
        monkeypatch.setattr(snap_path, "CONFIG_PATH", cfg_path)
        snap_path.save_config({"save_dir": "C:/test", "hotkey": "ctrl+alt+z"})
        assert cfg_path.exists()


class TestTogglePause:
    def test_sets_paused_event_when_active(self):
        paused_event = threading.Event()
        icon = MagicMock()
        snap_path.toggle_pause(paused_event, icon, make_img(), make_img())
        assert paused_event.is_set()

    def test_clears_paused_event_when_paused(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        snap_path.toggle_pause(paused_event, icon, make_img(), make_img())
        assert not paused_event.is_set()

    def test_sets_icon_to_paused_image(self):
        paused_event = threading.Event()
        icon = MagicMock()
        active_img = make_img(color=(0, 0, 255))
        paused_img = make_img(color=(128, 128, 128))
        snap_path.toggle_pause(paused_event, icon, active_img, paused_img)
        assert icon.icon is paused_img

    def test_sets_icon_to_active_image_on_resume(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        active_img = make_img(color=(0, 0, 255))
        paused_img = make_img(color=(128, 128, 128))
        snap_path.toggle_pause(paused_event, icon, active_img, paused_img)
        assert icon.icon is active_img

    def test_sets_title_to_paused(self):
        paused_event = threading.Event()
        icon = MagicMock()
        snap_path.toggle_pause(paused_event, icon, make_img(), make_img())
        assert icon.title == "SnapPath — Paused"

    def test_sets_title_to_active_on_resume(self):
        paused_event = threading.Event()
        paused_event.set()
        icon = MagicMock()
        snap_path.toggle_pause(paused_event, icon, make_img(), make_img())
        assert icon.title == "SnapPath — Active"


class TestRegisterHotkey:
    def test_returns_true_on_success(self, monkeypatch):
        monkeypatch.setattr(snap_path, "_current_hotkey", None)
        with patch("snap_path.keyboard.add_hotkey"), \
             patch("snap_path.keyboard.remove_hotkey"):
            result = snap_path.register_hotkey("ctrl+shift+x", lambda: None)
        assert result is True

    def test_returns_false_on_invalid_hotkey(self, monkeypatch):
        monkeypatch.setattr(snap_path, "_current_hotkey", None)
        with patch("snap_path.keyboard.add_hotkey", side_effect=ValueError("bad")):
            result = snap_path.register_hotkey("!!!bad!!!", lambda: None)
        assert result is False

    def test_removes_previous_hotkey_before_registering(self, monkeypatch):
        monkeypatch.setattr(snap_path, "_current_hotkey", "ctrl+shift+x")
        with patch("snap_path.keyboard.remove_hotkey") as mock_remove, \
             patch("snap_path.keyboard.add_hotkey"):
            snap_path.register_hotkey("ctrl+shift+z", lambda: None)
        mock_remove.assert_called_once_with("ctrl+shift+x")
