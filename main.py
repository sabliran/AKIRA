#!/usr/bin/env python3
"""Akira — show an image or text anywhere with a global hotkey."""

import os
import sys
from pathlib import Path

# Force X11/XWayland backend so window positioning (move/setGeometry) works
# reliably on KDE Plasma Wayland.  XWayland is required anyway (pynput hotkeys).
os.environ.setdefault('DISPLAY', ':0')
os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

_APP_ICON_PATH = (
    Path.home() / ".local" / "share" / "icons"
    / "hicolor" / "256x256" / "apps" / "akira.png"
)


def _export_app_icon(icon: QIcon) -> None:
    """Write the current icon as a PNG so the app-menu entry picks it up."""
    _APP_ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    icon.pixmap(256, 256).save(str(_APP_ICON_PATH))

import config_manager
from display_window import DisplayWindow
from settings_window import SettingsWindow
from hotkey_listener import HotkeyListener
from reading_line import ReadingLine


def _make_tray_icon(path: str = "") -> QIcon:
    """Return a tray icon: load from path if given, otherwise draw the default."""
    if path:
        pix = QPixmap(path)
        if not pix.isNull():
            return QIcon(pix)   # keep full resolution; Qt scales per context
    # Default: blue rounded square with "SD"
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#4a90e2"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 14, 14)
    p.setPen(QColor("white"))
    font = p.font()
    font.setPixelSize(26)
    font.setBold(True)
    p.setFont(font)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "SD")
    p.end()
    return QIcon(pix)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Akira")
    app.setQuitOnLastWindowClosed(False)   # Keep running when all windows close

    config = config_manager.load()

    tray_icon = _make_tray_icon(config.get("tray_icon_path", ""))
    _export_app_icon(tray_icon)
    app.setWindowIcon(tray_icon)
    display_win = DisplayWindow(config, icon=tray_icon)

    listener = HotkeyListener(config["shortcut"])
    listener.triggered.connect(display_win.toggle)
    listener.start()

    rl = ReadingLine(config)
    rl.set_active(config.get("rl_active", False))
    rl_listener = HotkeyListener(config.get("rl_shortcut", "<ctrl>+<shift>+l"))
    rl_listener.triggered.connect(rl.toggle)
    rl_listener.start()

    settings_win: SettingsWindow | None = None

    def open_settings() -> None:
        nonlocal settings_win, config
        if settings_win and settings_win.isVisible():
            settings_win.raise_()
            settings_win.activateWindow()
            return

        # Reflect current runtime state of the reading line in the dialog
        live_config = {**config, "rl_active": rl.active}
        settings_win = SettingsWindow(live_config)

        def on_saved(new_cfg: dict) -> None:
            nonlocal config
            config = new_cfg
            config_manager.save(config)
            display_win.update_config(config)
            listener.update_shortcut(config["shortcut"])
            rl.update_config(config)
            rl.set_active(config.get("rl_active", False))
            rl_listener.update_shortcut(config["rl_shortcut"])
            new_icon = _make_tray_icon(config.get("tray_icon_path", ""))
            _export_app_icon(new_icon)
            app.setWindowIcon(new_icon)
            tray.setIcon(new_icon)
            display_win.setWindowIcon(new_icon)

        settings_win.saved.connect(on_saved)
        settings_win.show()

    # ── System tray ────────────────────────────────────────────────────────
    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip("Akira")

    def restart() -> None:
        os.execv(sys.executable, [sys.executable] + sys.argv)

    menu = QMenu()
    menu.addAction("Show / Hide").triggered.connect(display_win.toggle)
    menu.addAction("Settings…").triggered.connect(open_settings)
    menu.addAction("Restart").triggered.connect(restart)
    menu.addSeparator()
    menu.addAction("Quit").triggered.connect(app.quit)
    tray.setContextMenu(menu)

    # Left-click on tray icon toggles the display
    tray.activated.connect(
        lambda reason: display_win.toggle()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )

    tray.show()

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("Warning: no system tray found — opening Settings instead.")
        open_settings()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
