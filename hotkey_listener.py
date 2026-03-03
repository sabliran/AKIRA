"""
Global hotkey listener via pynput (X11/XWayland).

Sets DISPLAY=:0 so pynput can connect to XWayland even when the
environment variable is not inherited (e.g. launched from a Flatpak terminal).
"""

import os
import threading

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

# Ensure pynput can reach XWayland
os.environ.setdefault('DISPLAY', ':0')


class HotkeyListener(QObject):
    """Listens for a global X11 keyboard shortcut and emits triggered().

    Runs pynput in its own daemon thread; the signal is automatically
    delivered to the Qt main thread via queued connection.
    """

    triggered = pyqtSignal()

    def __init__(self, shortcut: str):
        super().__init__()
        self._shortcut = shortcut
        self._hotkeys: keyboard.GlobalHotKeys | None = None

    # ── Public API ─────────────────────────────────────────────────────────

    def start(self) -> None:
        try:
            self._hotkeys = keyboard.GlobalHotKeys(
                {self._shortcut: self._on_triggered}
            )
            self._hotkeys.start()
        except Exception as exc:
            print(f'[HotkeyListener] Could not register {self._shortcut!r}: {exc}')

    def stop(self) -> None:
        if self._hotkeys:
            self._hotkeys.stop()
            self._hotkeys = None

    def update_shortcut(self, shortcut: str) -> None:
        self.stop()
        self._shortcut = shortcut
        self.start()

    # ── Internal ───────────────────────────────────────────────────────────

    def _on_triggered(self) -> None:
        # Called from pynput's thread; Qt routes it to the main thread.
        self.triggered.emit()
