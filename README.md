# SnapPath

<p align="center">
  <img src="logo.png" alt="SnapPath logo" width="96" height="96">
</p>

<p align="center">
  <b>Windows tray utility that turns clipboard screenshots into file paths.</b><br>
  <i>Tiện ích khay hệ thống Windows: biến ảnh chụp màn hình trong clipboard thành đường dẫn file.</i>
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#tiếng-việt">Tiếng Việt</a>
</p>

---

## English

### What is SnapPath?

Claude Code CLI, and many other terminal-based tools, cannot accept pasted images directly — they only accept **file paths**. SnapPath fixes that.

It runs quietly in the system tray, watches your clipboard, and the moment you copy a screenshot (e.g. with `Win+Shift+S` Snipping Tool), it:

1. Saves the image as a PNG to a folder you choose
2. Replaces the clipboard with the **file path** of that PNG
3. Lets you paste (`Ctrl+V`) the path anywhere — Claude Code, Notepad, a chat box

No more awkward "save as…" dialogs before every paste.

### Download

Grab the latest `snap_path.exe` from the [Releases](../../releases) page — it's a single self-contained executable, no Python install required.

### Usage

1. Double-click `snap_path.exe` — a tray icon appears in the bottom-right of the taskbar
2. Take screenshots as you normally would (Snipping Tool, `Win+Shift+S`, any tool that copies to clipboard)
3. Paste (`Ctrl+V`) wherever you want the path — it's already on the clipboard
4. Right-click the tray icon for options:
   - **Pause / Resume** — temporarily stop watching the clipboard
   - **Open folder** — open the save directory in Explorer
   - **Settings** — change the save folder or the pause/resume hotkey
   - **Exit** — quit the app

### Default hotkey

`Ctrl+Shift+X` toggles pause/resume globally. Change it any time from **Settings** in the tray menu.

### Configuration

| Setting      | Default                     | Description                            |
| ------------ | --------------------------- | -------------------------------------- |
| Save folder  | `%USERPROFILE%\snap-path`   | Where PNG files are saved              |
| Hotkey       | `ctrl+shift+x`              | Global pause/resume toggle             |

Config is stored at `%USERPROFILE%\snap-path\config.json` — edit from the Settings dialog, not by hand.

### Auto-start with Windows

1. Press `Win+R`, type `shell:startup`, press **Enter**
2. Copy a shortcut to `snap_path.exe` into the folder that opens

### Build from source

Requires **Python 3.11+** on Windows.

```bat
pip install -r requirements.txt
build.bat
```

Output: `dist\snap_path.exe` — a standalone ~19 MB Windows executable.

### Run the tests

```bat
pytest tests/ -v
```

### How it works

| Step | Component           | Detail                                                      |
| ---- | ------------------- | ----------------------------------------------------------- |
| 1    | Clipboard watcher   | Polls every 500 ms via `PIL.ImageGrab.grabclipboard()`       |
| 2    | Deduplication       | MD5 hash of the image, so the same screenshot isn't re-saved |
| 3    | Save                | PNG, filename `screenshot_YYYYMMDD_HHMMSS_ffffff.png`        |
| 4    | Replace clipboard   | `win32clipboard` writes the path as `CF_UNICODETEXT`         |
| 5    | Tray icon           | `pystray` on the main thread                                 |

Everything lives in a single file: [`snap_path.py`](snap_path.py).

### Tech stack

- Python 3.11+
- [Pillow](https://pypi.org/project/Pillow/) — image handling
- [pywin32](https://pypi.org/project/pywin32/) — clipboard & Win32 APIs
- [pystray](https://pypi.org/project/pystray/) — system tray icon
- [keyboard](https://pypi.org/project/keyboard/) — global hotkey
- [PyInstaller](https://pypi.org/project/pyinstaller/) — single-file packaging

### License

MIT — see [LICENSE](LICENSE) if present, otherwise: do what you want, no warranty.

---

## Tiếng Việt

### SnapPath là gì?

Claude Code CLI và nhiều công cụ dòng lệnh khác **không chấp nhận paste trực tiếp hình ảnh** — chúng chỉ nhận **đường dẫn file**. SnapPath giải quyết vấn đề đó.

App chạy im lặng dưới khay hệ thống, theo dõi clipboard. Mỗi khi bạn chụp ảnh màn hình (ví dụ `Win+Shift+S`), SnapPath sẽ:

1. Lưu ảnh thành file PNG vào thư mục bạn chọn
2. Thay nội dung clipboard bằng **đường dẫn** tới file PNG đó
3. Bạn dán (`Ctrl+V`) đường dẫn vào bất cứ đâu — Claude Code, Notepad, khung chat…

Không cần phải "Save as…" thủ công trước mỗi lần paste nữa.

### Tải về

Lấy `snap_path.exe` mới nhất tại mục [Releases](../../releases) — file `.exe` đơn, chạy ngay, không cần cài Python.

### Cách dùng

1. Chạy `snap_path.exe` — biểu tượng xuất hiện dưới khay hệ thống (góc phải taskbar)
2. Chụp màn hình như bình thường (Snipping Tool, `Win+Shift+S`, hoặc công cụ nào cũng được miễn là copy được vào clipboard)
3. Dán (`Ctrl+V`) vào nơi cần — đường dẫn đã sẵn trong clipboard
4. Chuột phải vào biểu tượng để:
   - **Pause / Resume** — tạm dừng / tiếp tục theo dõi clipboard
   - **Open folder** — mở thư mục lưu ảnh bằng Explorer
   - **Settings** — đổi thư mục lưu hoặc đổi phím tắt pause/resume
   - **Exit** — thoát app

### Phím tắt mặc định

`Ctrl+Shift+X` bật/tắt chế độ pause toàn hệ thống. Có thể đổi bất cứ lúc nào trong **Settings**.

### Cấu hình

| Mục          | Mặc định                    | Giải thích                                      |
| ------------ | --------------------------- | ----------------------------------------------- |
| Save folder  | `%USERPROFILE%\snap-path`   | Nơi lưu các file PNG                            |
| Hotkey       | `ctrl+shift+x`              | Phím tắt toàn hệ thống để pause/resume           |

Config lưu tại `%USERPROFILE%\snap-path\config.json` — sửa qua hộp thoại Settings, đừng sửa tay.

### Tự chạy cùng Windows

1. Nhấn `Win+R`, gõ `shell:startup`, rồi **Enter**
2. Copy shortcut của `snap_path.exe` vào thư mục vừa mở

### Build từ source

Yêu cầu **Python 3.11+** trên Windows.

```bat
pip install -r requirements.txt
build.bat
```

Kết quả: `dist\snap_path.exe` — 1 file `.exe` khoảng 19 MB, tự chứa đủ dependencies.

### Chạy test

```bat
pytest tests/ -v
```

### Nguyên lý hoạt động

| Bước | Thành phần           | Chi tiết                                                           |
| ---- | -------------------- | ------------------------------------------------------------------ |
| 1    | Clipboard watcher    | Poll mỗi 500 ms qua `PIL.ImageGrab.grabclipboard()`                |
| 2    | Chống trùng          | Hash MD5 nội dung ảnh — ảnh giống hệt không bị lưu lại             |
| 3    | Lưu file             | Định dạng PNG, tên `screenshot_YYYYMMDD_HHMMSS_ffffff.png`         |
| 4    | Ghi clipboard        | Dùng `win32clipboard` ghi đường dẫn kiểu `CF_UNICODETEXT`          |
| 5    | Tray icon            | Dùng `pystray` ở main thread                                       |

Toàn bộ logic nằm gọn trong 1 file: [`snap_path.py`](snap_path.py).

### Công nghệ

- Python 3.11+
- [Pillow](https://pypi.org/project/Pillow/) — xử lý ảnh
- [pywin32](https://pypi.org/project/pywin32/) — clipboard & Win32 API
- [pystray](https://pypi.org/project/pystray/) — icon khay hệ thống
- [keyboard](https://pypi.org/project/keyboard/) — phím tắt toàn hệ thống
- [PyInstaller](https://pypi.org/project/pyinstaller/) — đóng gói thành 1 file `.exe`

### Giấy phép

MIT — xem file [LICENSE](LICENSE) nếu có, nếu không thì: dùng tự do, không bảo hành gì cả.
