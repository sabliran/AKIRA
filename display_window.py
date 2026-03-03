from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, QPainterPath, QIcon


class DisplayWindow(QWidget):
    """Frameless, always-on-top overlay that shows an image or text.

    Dismissed by pressing Escape or clicking anywhere on the window.
    Toggled by calling toggle().
    """

    def __init__(self, config: dict, icon: QIcon | None = None):
        super().__init__()
        self.config = config.copy()
        self._setup_window()
        self._build_ui()
        self._refresh_content()
        if icon:
            self.setWindowIcon(icon)

    # ── Setup ──────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(self.config["window_width"], self.config["window_height"])
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        geo = self.screen().geometry()
        self.move(
            (geo.width() - self.width()) // 2,
            (geo.height() - self.height()) // 2,
        )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

    # ── Content ────────────────────────────────────────────────────────────

    def _refresh_content(self) -> None:
        if self.config["mode"] == "image" and self.config["image_path"]:
            pix = QPixmap(self.config["image_path"])
            if not pix.isNull():
                scaled = pix.scaled(
                    self.width() - 48,
                    self.height() - 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.label.setPixmap(scaled)
                self.label.setStyleSheet("")
                return

        # Text mode (or image failed to load)
        self.label.setPixmap(QPixmap())
        font = QFont()
        font.setPointSize(self.config["text_font_size"])
        self.label.setFont(font)
        self.label.setText(
            self.config["text"] if self.config["mode"] == "text" else "(no image set)"
        )
        self.label.setStyleSheet(f"color: {self.config['text_color']};")

    # ── Public API ─────────────────────────────────────────────────────────

    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self._center_on_screen()
            self.show()
            self.raise_()
            self.activateWindow()

    def update_config(self, config: dict) -> None:
        self.config = config.copy()
        self.resize(config["window_width"], config["window_height"])
        self._center_on_screen()
        self._refresh_content()
        self.update()

    # ── Qt overrides ───────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.config["background_color"])
        color.setAlpha(self.config["background_opacity"])
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.drawPath(path)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.hide()

    def mousePressEvent(self, _event) -> None:
        self.hide()
