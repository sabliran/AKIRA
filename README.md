# This is my cat; Akira!!

![image](https://raw.githubusercontent.com/sabliran/AKIRA/refs/heads/main/unnamed.jpg)


(vibe coded only)
A custom Linux multipurpose tray application that shows a floating overlay (image, text, PDF, or both) anywhere on the desktop when a global keyboard shortcut is pressed.





![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

## Features
- **Multifunctional software** — designed to suit my needs.
- **Global hotkeys** — trigger from any application; all shortcuts are configurable
- **Image, text, or both** — display a custom image, styled text, or both stacked together
- **PDF viewer** — display any PDF page in the overlay; scroll wheel navigates pages; configurable render quality
- **Reading line** — a horizontal guide that follows the cursor; two modes: thin colored line or full-screen dimmer with a transparent reading slot
- **Screen dimmer** — dims the entire screen except a transparent slot at the cursor's Y position, helping focus while reading
- **System tray** — lives quietly in the tray; left-click or use the shortcut to toggle
- **Customizable appearance** — background color, opacity, text font/size/color, window size
- **Custom tray icon** — use any image as the tray & app-menu icon
- **Settings GUI** — open with `Ctrl+Shift+S` or from the tray menu; change everything at runtime without restarting
- **Single instance** — launching a second copy exits immediately
- **Persistent config** — settings saved to `~/.config/akira/config.json`

## Requirements

- Linux with X11 or XWayland (works on KDE Plasma Wayland via XWayland)
- Python 3.10+
- PyQt6 ≥ 6.4
- pynput ≥ 1.7.6
- PyMuPDF ≥ 1.23 (for PDF mode)

## Installation

```bash
git clone https://github.com/sabliran/AKIRA.git
cd AKIRA
bash install.sh
```

`install.sh` installs Python dependencies (PyQt6, pynput, PyMuPDF), creates a `.desktop` entry for your app launcher, and sets up autostart on login.

## Running manually

```bash
python3 main.py
```

> **Flatpak / sandboxed terminal users:** use `flatpak-spawn --host python3 main.py`

## Usage

1. The app icon appears in your system tray after launch.
2. Press **Ctrl+Shift+I** (or your configured shortcut) to show/hide the overlay.
3. **Right-click** the tray icon → **Settings…** (or press `Ctrl+Shift+S`) to configure:
   - **Content tab** — choose Image, Text, Image + Text, or PDF mode
   - **Appearance tab** — colors, opacity, window size, custom tray icon
   - **Shortcut tab** — record global shortcuts for the overlay and for opening Settings
   - **Reading Line tab** — enable/configure the reading line guide

### PDF mode

- Select a PDF file in Settings → Content → PDF
- Scroll up/down on the overlay to navigate pages
- Increase **Render scale** (default `1.00×`) for sharper text on high-DPI screens

### Reading line

- Toggle with **Ctrl+Shift+L** (configurable)
- Press **Escape** to turn it off from anywhere
- **Right-click** the overlay to lock the line at the current Y position (unlocks on right-click again or left-click)
- **Left-click** the overlay to turn the reading line off
- Two modes selectable in Settings:
  - **Line** — thin colored horizontal line following the cursor
  - **Screen dimmer** — dims the whole screen; a transparent slot shows the text at cursor height
- Enable **Cycle through modes** to step through off → line → dimmer → off with one shortcut
- Customise color, opacity, and thickness (line mode) or dimmer color, opacity, and slot height (screen dimmer mode)

## File structure

```
main.py              # Entry point: tray icon, wires listener → display window
config_manager.py    # load() / save() — config persistence
hotkey_listener.py   # QObject wrapping pynput.keyboard.GlobalHotKeys
display_window.py    # Frameless always-on-top Qt overlay (image / text / PDF)
reading_line.py      # Full-screen transparent overlay for the reading line
settings_window.py   # Tabbed settings dialog
requirements.txt     # Python dependencies
install.sh           # Installer script
```

## License

MIT
