#!/usr/bin/env python3
"""Shortcut Display — show an image or text anywhere with a global hotkey."""

import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

import config_manager
from display_window import DisplayWindow
from settings_window import SettingsWindow
from hotkey_listener import HotkeyListener


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
    app.setApplicationName("Shortcut Display")
    app.setQuitOnLastWindowClosed(False)   # Keep running when all windows close

    config = config_manager.load()

    tray_icon = _make_tray_icon(config.get("tray_icon_path", ""))
    app.setWindowIcon(tray_icon)
    display_win = DisplayWindow(config, icon=tray_icon)

    listener = HotkeyListener(config["shortcut"])
    listener.triggered.connect(display_win.toggle)
    listener.start()

    settings_win: SettingsWindow | None = None

    def open_settings() -> None:
        nonlocal settings_win, config
        if settings_win and settings_win.isVisible():
            settings_win.raise_()
            settings_win.activateWindow()
            return

        settings_win = SettingsWindow(config)

        def on_saved(new_cfg: dict) -> None:
            nonlocal config
            config = new_cfg
            config_manager.save(config)
            display_win.update_config(config)
            listener.update_shortcut(config["shortcut"])
            new_icon = _make_tray_icon(config.get("tray_icon_path", ""))
            app.setWindowIcon(new_icon)
            tray.setIcon(new_icon)
            display_win.setWindowIcon(new_icon)

        settings_win.saved.connect(on_saved)
        settings_win.show()

    # ── System tray ────────────────────────────────────────────────────────
    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip("Shortcut Display")

    menu = QMenu()
    menu.addAction("Show / Hide").triggered.connect(display_win.toggle)
    menu.addAction("Settings…").triggered.connect(open_settings)
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
