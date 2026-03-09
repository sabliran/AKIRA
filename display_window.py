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
        layout.setSpacing(8)

        self._img_labels = []
        for _ in range(4):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl, stretch=1)
            self._img_labels.append(lbl)

        self._txt_label = QLabel()
        self._txt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._txt_label.setWordWrap(True)
        layout.addWidget(self._txt_label, stretch=0)

    # ── Content ────────────────────────────────────────────────────────────

    def _refresh_content(self) -> None:
        mode = self.config["mode"]
        show_image = mode in ("image", "both")
        show_text = mode in ("text", "both")
        show_pdf = mode == "pdf"

        for lbl in self._img_labels:
            lbl.setVisible(show_image or show_pdf)
        self._txt_label.setVisible(show_text or show_pdf)

        if show_pdf:
            # Only the first label is used for PDF
            for lbl in self._img_labels[1:]:
                lbl.setVisible(False)
            self._render_pdf_page()
            return

        if show_image:
            img_paths = [
                self.config.get("image_path", ""),
                self.config.get("image_path_2", ""),
                self.config.get("image_path_3", ""),
                self.config.get("image_path_4", ""),
            ]
            # Count how many slots have a valid path
            visible_count = sum(1 for p in img_paths if p)
            if visible_count == 0:
                visible_count = 1  # show placeholder in first slot

            slot_h = max(1, (self.height() - 48 - 8 * 3) // 4)

            for lbl, path in zip(self._img_labels, img_paths):
                if path:
                    pix = QPixmap(path)
                    if not pix.isNull():
                        scaled = pix.scaled(
                            self.width() - 48, slot_h,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        lbl.setPixmap(scaled)
                        lbl.setText("")
                        lbl.setStyleSheet("")
                        lbl.setVisible(True)
                    else:
                        lbl.setPixmap(QPixmap())
                        lbl.setText("(invalid image)")
                        lbl.setStyleSheet(f"color: {self.config['text_color']};")
                        lbl.setVisible(True)
                else:
                    lbl.setPixmap(QPixmap())
                    lbl.setText("")
                    lbl.setStyleSheet("")
                    lbl.setVisible(False)

            # Show placeholder in first slot if nothing is set
            if visible_count == 1 and not img_paths[0]:
                self._img_labels[0].setText("(no image set)")
                self._img_labels[0].setStyleSheet(f"color: {self.config['text_color']};")
                self._img_labels[0].setVisible(True)

        if show_text:
            font = QFont()
            font.setPointSize(self.config["text_font_size"])
            self._txt_label.setFont(font)
            self._txt_label.setText(self.config["text"])
            self._txt_label.setStyleSheet(f"color: {self.config['text_color']};")

    def _render_pdf_page(self) -> None:
        lbl = self._img_labels[0]
        if not _FITZ_AVAILABLE:
            lbl.setText("PyMuPDF not installed.\nRun: pip install PyMuPDF")
            lbl.setStyleSheet(f"color: {self.config['text_color']};")
            self._txt_label.setText("")
            return

        path = self.config.get("pdf_path", "")
        if not path:
            lbl.setPixmap(QPixmap())
            lbl.setText("(no PDF set)")
            lbl.setStyleSheet(f"color: {self.config['text_color']};")
            self._txt_label.setText("")
            return

        if path != self._pdf_path_loaded:
            try:
                self._pdf_doc = fitz.open(path)
                self._pdf_path_loaded = path
                self._pdf_page_idx = 0
            except Exception as e:
                lbl.setText(f"Error loading PDF:\n{e}")
                lbl.setStyleSheet(f"color: {self.config['text_color']};")
                self._txt_label.setText("")
                return

        total = len(self._pdf_doc)
        self._pdf_page_idx = max(0, min(self._pdf_page_idx, total - 1))
        page = self._pdf_doc.load_page(self._pdf_page_idx)

        available_w = self.config.get("pdf_window_width", 900) - 48
        available_h = self.config.get("pdf_window_height", 700) - 72

        rect = page.rect
        fit_scale = min(available_w / rect.width, available_h / rect.height)
        quality = max(0.5, float(self.config.get("pdf_scale", 1.0)))
        render_scale = fit_scale * quality

        mat = fitz.Matrix(render_scale, render_scale)
        pix = page.get_pixmap(matrix=mat)

        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format.Format_RGB888)
        qt_pix = QPixmap.fromImage(img)

        if quality > 1.0:
            qt_pix = qt_pix.scaled(
                available_w, available_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        lbl.setPixmap(qt_pix)
        lbl.setStyleSheet("")

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
