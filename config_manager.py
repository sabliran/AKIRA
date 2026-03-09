import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "akira"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "mode": "image",          # "image", "text", "both", or "pdf"
    "image_path": "",
    "image_path_2": "",
    "image_path_3": "",
    "image_path_4": "",
    "pdf_path": "",
    "pdf_scale": 1.0,         # rendering scale for PDF pages
    "pdf_window_width": 900,
    "pdf_window_height": 700,
    "tray_icon_path": "",     # custom tray icon (empty = built-in "SD" icon)
    "text": "Your text here",
    "text_font_size": 72,
    "text_color": "#ffffff",
    "background_color": "#1a1a2e",
    "background_opacity": 220,   # 0-255
    "shortcut": "<ctrl>+<shift>+i",
    "settings_shortcut": "<ctrl>+<shift>+s",
    "window_width": 800,
    "window_height": 600,
    # Reading-line feature
    "rl_active": False,
    "rl_cycle_modes": False,     # True = shortcut cycles off→line→block→off
    "rl_mode": "line",           # "line" or "block"
    "rl_color": "#ff0000",
    "rl_opacity": 255,           # 0-255
    "rl_thickness": 2,
    "rl_block_color": "#000000",
    "rl_block_opacity": 180,     # 0-255
    "rl_slot_height": 40,        # px — transparent reading slot height in block mode
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
