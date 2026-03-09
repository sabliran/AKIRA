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
from PyQt6.QtGui import QPainter, QColor, QCursor


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
        self._cycle_mode: str | None = None   # overrides config["rl_mode"] while cycling
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

    def _effective_mode(self) -> str:
        """Return the active display mode, respecting any cycle override."""
        if self._cycle_mode is not None:
            return self._cycle_mode
        return self.config.get("rl_mode", "line")

    def toggle(self) -> None:
        if self.config.get("rl_cycle_modes", False):
            self._cycle()
            return
        self._active = not self._active
        if self._active:
            self._cycle_mode = None
            self._cover_screen()
            self._update_mouse_transparency()
            self.show()
            self.raise_()
        else:
            self._set_locked(False)
            self.hide()

    def _cycle(self) -> None:
        """Cycle through: off → line → block → off."""
        if not self._active:
            self._cycle_mode = "line"
            self._active = True
            self._cover_screen()
            self._update_mouse_transparency()
            self.show()
            self.raise_()
        elif self._cycle_mode == "line":
            self._cycle_mode = "block"
            self._update_mouse_transparency()
            self.update()
        else:
            self._cycle_mode = None
            self._set_locked(False)
            self._active = False
            self.hide()

    @property
    def active(self) -> bool:
        return self._active

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self.toggle()

    def update_config(self, config: dict) -> None:
        self.config = config.copy()
        self._cycle_mode = None   # reset cycle state on config change
        if self._active:
            self._update_mouse_transparency()
            self.update()

    # ── Internal ───────────────────────────────────────────────────────────

    def _set_locked(self, locked: bool) -> None:
        self._locked = locked
        self._update_mouse_transparency()

    def _update_mouse_transparency(self) -> None:
        """Transparent to mouse input when locked or in block mode.

        Block mode tracks cursor via QCursor.pos() on each timer tick so it
        doesn't need mouseMoveEvent; scroll/clicks pass through freely.
        Exception: when rl_scroll_resize is enabled, the overlay stays
        interactive so Ctrl+scroll wheel events reach this widget.
        """
        block = self._effective_mode() == "block"
        scroll_active = (self.config.get("rl_scroll_resize", False)
                         or self.config.get("rl_scroll_opacity", False))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                          self._locked or (block and not scroll_active))

    # ── Qt overrides ───────────────────────────────────────────────────────

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        self._cx = int(pos.x())
        if not self._locked:
            self._cy = int(pos.y())
        self.update()

    def wheelEvent(self, event) -> None:
        mods = event.modifiers()
        ctrl  = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        block = self._effective_mode() == "block"
        delta = event.angleDelta().y()

        if (block and ctrl and shift and self.config.get("rl_scroll_opacity", False)):
            step = max(2, abs(delta) // 10)
            current = self.config.get("rl_block_opacity", 180)
            self.config["rl_block_opacity"] = (
                max(current - step, 0) if delta > 0 else min(current + step, 255)
            )
            self.update()
            event.accept()
        elif (block and ctrl and not shift and self.config.get("rl_scroll_resize", False)):
            step = max(2, abs(delta) // 10)
            current = self.config.get("rl_slot_height", 40)
            self.config["rl_slot_height"] = (
                min(current + step, 400) if delta > 0 else max(current - step, 4)
            )
            self.update()
            event.accept()
        else:
            event.ignore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            if self._locked:
                self._set_locked(False)
            else:
                self._locked_y = self._cy
                self._set_locked(True)
        else:
            self._set_locked(False)
            self.toggle()

    def _tick(self) -> None:
        if self._active:
            if not self._locked and self._effective_mode() == "block":
                self._cy = QCursor.pos().y()
            self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)

        ly = self._locked_y if self._locked else self._cy

        if self._effective_mode() == "block":
            color = QColor(self.config.get("rl_block_color", "#000000"))
            color.setAlpha(self.config.get("rl_block_opacity", 180))
            # Cover entire screen with overlay color
            painter.fillRect(self.rect(), color)
            # Punch a transparent reading slot at the cursor's Y
            slot_h = max(self.config.get("rl_slot_height", 40), 4)
            painter.fillRect(0, ly - slot_h // 2, self.width(), slot_h,
                             Qt.GlobalColor.transparent)
        else:
            color = QColor(self.config.get("rl_color", "#ff0000"))
            color.setAlpha(self.config.get("rl_opacity", 255))
            # Original line mode: transparent background, colored line
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
            thickness = max(self.config.get("rl_thickness", 2), 1)
            half_len = 3799 // 2
            painter.fillRect(
                self._cx - half_len, ly - thickness // 2,
                half_len * 2, thickness,
                color,
            )
            # When locked, draw small vertical tick marks at both ends
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
