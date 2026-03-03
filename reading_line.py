"""Reading-line overlay — a thin horizontal guide that tracks the cursor.

Uses a full-screen transparent overlay so the window never needs to move.
The line is painted at the cursor's Y position on every repaint tick.
Cursor position is read via Xlib (python-xlib, already required by pynput)
because QCursor.pos() doesn't give the global position on Wayland.
"""

import os

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor


class ReadingLine(QWidget):
    """Full-screen transparent overlay that draws a line at the cursor's Y.

    The window never moves; only the painted content changes each frame.
    Toggle with toggle() or set_active().
    """

    def __init__(self, config: dict):
        super().__init__()
        self.config = config.copy()
        self._active = False
        self._xdpy = None
        self._xroot = None
        self._init_xdisplay()
        self._setup_window()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60 fps

    # ── Setup ──────────────────────────────────────────────────────────────

    def _init_xdisplay(self) -> None:
        """Open an Xlib connection to query the global cursor position."""
        try:
            from Xlib import display as xdisplay
            self._xdpy = xdisplay.Display(os.environ.get('DISPLAY', ':0'))
            self._xroot = self._xdpy.screen().root
        except Exception as exc:
            print(f'[ReadingLine] Xlib unavailable, falling back to QCursor: {exc}')

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._cover_screen()

    def _cover_screen(self) -> None:
        """Size the window to cover the full primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 3840, 2160)

    # ── Cursor tracking ────────────────────────────────────────────────────

    def _cursor_pos(self) -> tuple[int, int]:
        """Global cursor position via Xlib; falls back to QCursor."""
        if self._xroot is not None:
            try:
                ptr = self._xroot.query_pointer()
                return ptr.root_x, ptr.root_y
            except Exception:
                pass
        pos = QApplication.primaryScreen().cursor().pos() if QApplication.primaryScreen() else None
        if pos:
            return pos.x(), pos.y()
        return 0, 0

    def _tick(self) -> None:
        if self._active:
            self.update()

    # ── Public API ─────────────────────────────────────────────────────────

    def toggle(self) -> None:
        self._active = not self._active
        if self._active:
            self._cover_screen()
            self.show()
            self.raise_()
        else:
            self.hide()

    @property
    def active(self) -> bool:
        return self._active

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self.toggle()

    def update_config(self, config: dict) -> None:
        self.config = config.copy()
        if self._active:
            self.update()

    # ── Qt overrides ───────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)

        # Erase the whole surface to fully transparent
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        # Convert global cursor coords to window-local coords
        cx, cy = self._cursor_pos()
        screen = QApplication.primaryScreen()
        off = screen.geometry().topLeft() if screen else QPoint(0, 0)
        lx = cx - off.x()
        ly = cy - off.y()

        thickness = max(self.config.get("rl_thickness", 2), 1)
        half_len = self.config.get("rl_length", 800) // 2
        color = QColor(self.config.get("rl_color", "#ff0000"))

        painter.fillRect(lx - half_len, ly - thickness // 2, half_len * 2, thickness, color)
