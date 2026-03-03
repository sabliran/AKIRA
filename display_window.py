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
        layout.setSpacing(12)

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._img_label, stretch=3)

        self._txt_label = QLabel()
        self._txt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._txt_label.setWordWrap(True)
        layout.addWidget(self._txt_label, stretch=1)

    # ── Content ────────────────────────────────────────────────────────────

    def _refresh_content(self) -> None:
        mode = self.config["mode"]
        show_image = mode in ("image", "both")
        show_text = mode in ("text", "both")

        self._img_label.setVisible(show_image)
        self._txt_label.setVisible(show_text)

        if show_image:
            img_h = int((self.height() - 48) * (0.65 if mode == "both" else 1.0))
            pix = QPixmap(self.config["image_path"]) if self.config["image_path"] else QPixmap()
            if not pix.isNull():
                scaled = pix.scaled(
                    self.width() - 48, img_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._img_label.setPixmap(scaled)
                self._img_label.setStyleSheet("")
            else:
                self._img_label.setPixmap(QPixmap())
                self._img_label.setText("(no image set)")
                self._img_label.setStyleSheet(f"color: {self.config['text_color']};")

        if show_text:
            font = QFont()
            font.setPointSize(self.config["text_font_size"])
            self._txt_label.setFont(font)
            self._txt_label.setText(self.config["text"])
            self._txt_label.setStyleSheet(f"color: {self.config['text_color']};")

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
