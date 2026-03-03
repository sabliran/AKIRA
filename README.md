# Akira
![image](https://github.com/sabliran/AKIRA/blob/main/unnamed.jpg)
A custom Linux multipurpose tray application that shows a floating overlay (image, text, or both) anywhere on the desktop when a global keyboard shortcut is pressed.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4%2B-green)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

## Features
- **Multifunctional software** - designed to suit my needs.
- **Global hotkey** — trigger from any application (default: `Ctrl+Shift+I`)
- **Image, text, or both** — display a custom image, styled text, or both stacked together
- **System tray** — lives quietly in the tray; left-click or use the shortcut to toggle
- **Customizable appearance** — background color, opacity, text font/size/color, window size
- **Custom tray icon** — use any image as the tray & app-menu icon
- **Settings GUI** — change everything at runtime without restarting
- **Persistent config** — settings saved to `~/.config/akira/config.json`

## Requirements

- Linux with X11 or XWayland (works on KDE Plasma Wayland via XWayland)
- Python 3.10+
- PyQt6 ≥ 6.4
- pynput ≥ 1.7.6

## Installation

```bash
git clone https://github.com/sabliran/shortcut-display.git
cd shortcut-display
bash install.sh
```

`install.sh` installs Python dependencies, creates a `.desktop` entry for your app launcher, and sets up autostart on login.

## Running manually

```bash
python3 main.py
```

> **Flatpak / sandboxed terminal users:** use `flatpak-spawn --host python3 main.py`

## Usage

1. The app icon appears in your system tray after launch.
2. Press **Ctrl+Shift+I** (or your configured shortcut) to show/hide the overlay.
3. **Right-click** the tray icon → **Settings…** to configure:
   - **Content tab** — choose image, text, or image + text mode
   - **Appearance tab** — colors, opacity, window size, custom tray icon
   - **Shortcut tab** — record a new global shortcut

## File structure

```
main.py              # Entry point: tray icon, wires listener → display window
config_manager.py    # load() / save() — config persistence
hotkey_listener.py   # QObject wrapping pynput.keyboard.GlobalHotKeys
display_window.py    # Frameless always-on-top Qt overlay
settings_window.py   # Tabbed settings dialog
requirements.txt     # Python dependencies
install.sh           # Installer script
```

## License

MIT
