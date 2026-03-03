import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "akira"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "mode": "image",          # "image" or "text"
    "image_path": "",
    "tray_icon_path": "",     # custom tray icon (empty = built-in "SD" icon)
    "text": "Your text here",
    "text_font_size": 72,
    "text_color": "#ffffff",
    "background_color": "#1a1a2e",
    "background_opacity": 220,   # 0-255
    "shortcut": "<ctrl>+<shift>+i",
    "window_width": 800,
    "window_height": 600,
    # Reading-line feature
    "rl_active": False,
    "rl_color": "#ff0000",
    "rl_thickness": 2,
    "rl_length": 800,
    "rl_shortcut": "<ctrl>+<shift>+l",
}


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                saved = json.load(f)
            return {**DEFAULTS, **saved}
        except Exception:
            pass
    return DEFAULTS.copy()


def save(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
