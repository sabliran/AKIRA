"""Reading-line overlay — a thin horizontal guide that tracks the cursor.

Uses a full-screen transparent overlay so the window never needs to move.
The overlay captures mouse-move events (no input pass-through) so cursor
position is accurately reported by Qt for all apps, including native Wayland
windows where Xlib query_pointer() returns stale data.

Tradeoff: while the reading line is active, mouse clicks do not reach apps
beneath the overlay. Toggle off to interact normally.
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor


class ReadingLine(QWidget):
    """Full-screen transparent overlay that draws a line at the cursor's Y.

    The window never moves; only the painted content changes on each mouse
    move or timer tick.  Toggle with toggle() or set_active().
    """

    def __init__(self, config: dict):
        super().__init__()
        self.config = config.copy()
        self._active = False
        self._cx = 0
        self._cy = 0
        self._locked = False   # True = line stays at _locked_y even as cursor moves
        self._locked_y = 0
        self._setup_window()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60 fps — ensures first paint after show()

    # ── Setup ──────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._cover_screen()

    def _cover_screen(self) -> None:
        """Size the window to cover the full primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 3840, 2160)

    # ── Public API ─────────────────────────────────────────────────────────

    def toggle(self) -> None:
        self._active = not self._active
        if self._active:
            self._cover_screen()
            self.show()
            self.raise_()
        else:
            self._locked = False
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

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        self._cx = int(pos.x())
        if not self._locked:
            self._cy = int(pos.y())
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._locked = not self._locked
            if self._locked:
                self._locked_y = self._cy
        else:
            self._locked = False
            self.toggle()

    def _tick(self) -> None:
        if self._active:
            self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)

        # Erase the whole surface to fully transparent
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        thickness = max(self.config.get("rl_thickness", 2), 1)
        half_len = self.config.get("rl_length", 800) // 2
        color = QColor(self.config.get("rl_color", "#ff0000"))
        color.setAlpha(self.config.get("rl_opacity", 255))

        ly = self._locked_y if self._locked else self._cy

        painter.fillRect(
            self._cx - half_len, ly - thickness // 2,
            half_len * 2, thickness,
            color,
        )

        # When locked, draw small vertical tick marks at both ends as a visual cue
        if self._locked:
            tick_h = max(thickness * 5, 10)
            painter.fillRect(
                self._cx - half_len, ly - tick_h // 2,
                max(thickness, 2), tick_h,
                color,
            )
            painter.fillRect(
                self._cx + half_len - max(thickness, 2), ly - tick_h // 2,
                max(thickness, 2), tick_h,
                color,
            )
