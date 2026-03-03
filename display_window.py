from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, QPainterPath, QIcon, QImage

try:
    import fitz  # PyMuPDF
    _FITZ_AVAILABLE = True
except ImportError:
    _FITZ_AVAILABLE = False


class DisplayWindow(QWidget):
    """Frameless, always-on-top overlay that shows an image or text.

    Dismissed by pressing Escape or clicking anywhere on the window.
    Toggled by calling toggle().
    """

    def __init__(self, config: dict, icon: QIcon | None = None):
        super().__init__()
        self.config = config.copy()
        self._pdf_doc = None
        self._pdf_path_loaded = ""
        self._pdf_page_idx = 0
        self._pdf_scroll_accum = 0
        self._setup_window()
        self._build_ui()
        self._refresh_content()
        if icon:
            self.setWindowIcon(icon)

    # ── Setup ──────────────────────────────────────────────────────────────

    def _window_size(self) -> tuple[int, int]:
        if self.config.get("mode") == "pdf":
            return (self.config.get("pdf_window_width", 900),
                    self.config.get("pdf_window_height", 700))
        return self.config["window_width"], self.config["window_height"]

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        w, h = self._window_size()
        self.resize(w, h)
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
        show_pdf = mode == "pdf"

        self._img_label.setVisible(show_image or show_pdf)
        self._txt_label.setVisible(show_text or show_pdf)

        if show_pdf:
            self._render_pdf_page()
            return

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

    def _render_pdf_page(self) -> None:
        if not _FITZ_AVAILABLE:
            self._img_label.setText("PyMuPDF not installed.\nRun: pip install PyMuPDF")
            self._img_label.setStyleSheet(f"color: {self.config['text_color']};")
            self._txt_label.setText("")
            return

        path = self.config.get("pdf_path", "")
        if not path:
            self._img_label.setPixmap(QPixmap())
            self._img_label.setText("(no PDF set)")
            self._img_label.setStyleSheet(f"color: {self.config['text_color']};")
            self._txt_label.setText("")
            return

        if path != self._pdf_path_loaded:
            try:
                self._pdf_doc = fitz.open(path)
                self._pdf_path_loaded = path
                self._pdf_page_idx = 0
            except Exception as e:
                self._img_label.setText(f"Error loading PDF:\n{e}")
                self._img_label.setStyleSheet(f"color: {self.config['text_color']};")
                self._txt_label.setText("")
                return

        total = len(self._pdf_doc)
        self._pdf_page_idx = max(0, min(self._pdf_page_idx, total - 1))
        page = self._pdf_doc.load_page(self._pdf_page_idx)

        available_w = self.config.get("pdf_window_width", 900) - 48
        available_h = self.config.get("pdf_window_height", 700) - 72

        # Compute scale so the page renders at exactly the display resolution
        # (no upscaling later = sharp result). pdf_scale multiplies this for
        # extra quality (2× = super-sampled, then scaled down).
        rect = page.rect
        fit_scale = min(available_w / rect.width, available_h / rect.height)
        quality = max(0.5, float(self.config.get("pdf_scale", 1.0)))
        render_scale = fit_scale * quality

        mat = fitz.Matrix(render_scale, render_scale)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format.Format_RGB888)
        qt_pix = QPixmap.fromImage(img)

        # Only scale down if quality > 1 (super-sampled); at 1× the pixmap
        # already matches the display area exactly.
        if quality > 1.0:
            qt_pix = qt_pix.scaled(
                available_w, available_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self._img_label.setPixmap(qt_pix)
        self._img_label.setStyleSheet("")

        font = QFont()
        font.setPointSize(11)
        self._txt_label.setFont(font)
        self._txt_label.setText(f"Page {self._pdf_page_idx + 1} / {total}  •  scroll to navigate")
        self._txt_label.setStyleSheet(f"color: {self.config['text_color']};")

    # ── Public API ─────────────────────────────────────────────────────────

    def toggle(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self._refresh_content()
            self._center_on_screen()
            self.show()
            self.raise_()
            self.activateWindow()

    def update_config(self, config: dict) -> None:
        self.config = config.copy()
        w, h = self._window_size()
        self.resize(w, h)
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

    def wheelEvent(self, event) -> None:
        if self.config.get("mode") == "pdf" and self._pdf_doc:
            self._pdf_scroll_accum += event.angleDelta().y()
            # Require a full wheel click (120 units) before turning the page.
            # Remainder is discarded so a fast scroll can't carry into the next page.
            if self._pdf_scroll_accum <= -120:
                self._pdf_scroll_accum = 0
                self._pdf_page_idx = min(self._pdf_page_idx + 1, len(self._pdf_doc) - 1)
                self._render_pdf_page()
            elif self._pdf_scroll_accum >= 120:
                self._pdf_scroll_accum = 0
                self._pdf_page_idx = max(self._pdf_page_idx - 1, 0)
                self._render_pdf_page()
            event.accept()
