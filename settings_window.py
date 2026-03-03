from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QTextEdit, QSpinBox,
    QSlider, QFileDialog, QColorDialog, QDialogButtonBox,
    QCheckBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


# ── Shortcut helpers ───────────────────────────────────────────────────────

_PYNPUT_TO_HUMAN = {
    "<ctrl>": "Ctrl",
    "<shift>": "Shift",
    "<alt>": "Alt",
    "<super>": "Super",
    "<cmd>": "Super",
}


def pynput_to_human(shortcut: str) -> str:
    """'<ctrl>+<shift>+i'  →  'Ctrl+Shift+I'"""
    return "+".join(
        _PYNPUT_TO_HUMAN.get(p, p.upper()) for p in shortcut.split("+")
    )


def qt_event_to_pynput(event) -> str | None:
    """Convert a Qt key-press event to a pynput hotkey string, or None if invalid."""
    mods = event.modifiers()
    key = event.key()

    # Ignore pure modifier key presses
    pure_mod_keys = {
        Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
        Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R, Qt.Key.Key_AltGr,
    }
    if key in pure_mod_keys:
        return None

    parts: list[str] = []
    if mods & Qt.KeyboardModifier.ControlModifier:
        parts.append("<ctrl>")
    if mods & Qt.KeyboardModifier.AltModifier:
        parts.append("<alt>")
    if mods & Qt.KeyboardModifier.ShiftModifier:
        parts.append("<shift>")
    if mods & Qt.KeyboardModifier.MetaModifier:
        parts.append("<super>")

    if not parts:   # Require at least one modifier
        return None

    _SPECIAL = {
        Qt.Key.Key_F1: "<f1>",   Qt.Key.Key_F2: "<f2>",   Qt.Key.Key_F3: "<f3>",
        Qt.Key.Key_F4: "<f4>",   Qt.Key.Key_F5: "<f5>",   Qt.Key.Key_F6: "<f6>",
        Qt.Key.Key_F7: "<f7>",   Qt.Key.Key_F8: "<f8>",   Qt.Key.Key_F9: "<f9>",
        Qt.Key.Key_F10: "<f10>", Qt.Key.Key_F11: "<f11>", Qt.Key.Key_F12: "<f12>",
        Qt.Key.Key_Tab: "<tab>",         Qt.Key.Key_Space: "<space>",
        Qt.Key.Key_Return: "<enter>",    Qt.Key.Key_Backspace: "<backspace>",
        Qt.Key.Key_Delete: "<delete>",   Qt.Key.Key_Escape: "<esc>",
        Qt.Key.Key_Home: "<home>",       Qt.Key.Key_End: "<end>",
        Qt.Key.Key_PageUp: "<page_up>",  Qt.Key.Key_PageDown: "<page_down>",
        Qt.Key.Key_Up: "<up>",           Qt.Key.Key_Down: "<down>",
        Qt.Key.Key_Left: "<left>",       Qt.Key.Key_Right: "<right>",
    }

    if key in _SPECIAL:
        parts.append(_SPECIAL[key])
    elif 32 <= key <= 126:
        parts.append(chr(key).lower())
    else:
        return None

    return "+".join(parts)


# ── Color button ───────────────────────────────────────────────────────────

class ColorButton(QPushButton):
    color_changed = pyqtSignal(str)

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 28)
        self.set_color(color)
        self.clicked.connect(self._pick)

    def set_color(self, hex_color: str) -> None:
        self._color = hex_color
        self.setStyleSheet(
            f"background-color:{hex_color}; border:1px solid #666; border-radius:4px;"
        )

    def get_color(self) -> str:
        return self._color

    def _pick(self) -> None:
        c = QColorDialog.getColor(QColor(self._color), self, "Pick Color")
        if c.isValid():
            self.set_color(c.name())
            self.color_changed.emit(c.name())


# ── Shortcut recorder dialog ───────────────────────────────────────────────

class _ShortcutRecorder(QDialog):
    def __init__(self, current: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Shortcut")
        self.setModal(True)
        self.setFixedSize(380, 170)
        self._result = current
        self._recording = False

        layout = QVBoxLayout(self)

        info = QLabel(
            "Click the button, then press your key combination.\n"
            "At least one modifier key (Ctrl / Alt / Shift) is required."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        self._btn = QPushButton(f"Current: {pynput_to_human(current)}")
        self._btn.setCheckable(True)
        self._btn.setMinimumHeight(36)
        self._btn.clicked.connect(self._start_recording)
        layout.addWidget(self._btn)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _start_recording(self, checked: bool) -> None:
        if checked:
            self._recording = True
            self._btn.setText("Press a key combination…")
            self.grabKeyboard()

    def keyPressEvent(self, event) -> None:
        if not self._recording:
            super().keyPressEvent(event)
            return
        result = qt_event_to_pynput(event)
        if result:
            self._result = result
            self._btn.setChecked(False)
            self._btn.setText(f"Captured: {pynput_to_human(result)}")
            self._recording = False
            self.releaseKeyboard()
        event.accept()

    def get_shortcut(self) -> str:
        return self._result


# ── Main settings window ───────────────────────────────────────────────────

class SettingsWindow(QDialog):
    """Settings dialog with three tabs: Content, Appearance, Shortcut."""

    saved = pyqtSignal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Akira — Settings")
        self.setMinimumWidth(520)
        self._config = config.copy()
        self._current_shortcut = config["shortcut"]
        self._rl_current_shortcut = config.get("rl_shortcut", "<ctrl>+<shift>+l")
        self._build_ui()
        self._load_values()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_content_tab(), "Content")
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        tabs.addTab(self._build_shortcut_tab(), "Shortcut")
        tabs.addTab(self._build_reading_line_tab(), "Reading Line")
        root.addWidget(tabs)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _build_content_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Mode radio buttons
        mode_box = QGroupBox("Display mode")
        mode_layout = QHBoxLayout(mode_box)
        self._rb_image = QRadioButton("Image")
        self._rb_text = QRadioButton("Text")
        self._rb_both = QRadioButton("Image + Text")
        self._rb_pdf = QRadioButton("PDF")
        bg = QButtonGroup(self)
        bg.addButton(self._rb_image)
        bg.addButton(self._rb_text)
        bg.addButton(self._rb_both)
        bg.addButton(self._rb_pdf)
        mode_layout.addWidget(self._rb_image)
        mode_layout.addWidget(self._rb_text)
        mode_layout.addWidget(self._rb_both)
        mode_layout.addWidget(self._rb_pdf)
        mode_layout.addStretch()
        layout.addWidget(mode_box)

        # Image path
        self._image_box = QGroupBox("Image file")
        img_layout = QHBoxLayout(self._image_box)
        self._image_path = QLineEdit()
        self._image_path.setPlaceholderText("Path to image file…")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_image)
        img_layout.addWidget(self._image_path)
        img_layout.addWidget(browse_btn)
        layout.addWidget(self._image_box)

        # Text content
        self._text_box = QGroupBox("Text content")
        txt_layout = QVBoxLayout(self._text_box)
        self._text_edit = QTextEdit()
        self._text_edit.setMaximumHeight(120)
        self._text_edit.setPlaceholderText("Enter the text to display…")
        txt_layout.addWidget(self._text_edit)
        layout.addWidget(self._text_box)

        # PDF file
        self._pdf_box = QGroupBox("PDF file")
        pdf_layout = QFormLayout(self._pdf_box)
        pdf_path_row = QWidget()
        pdf_path_layout = QHBoxLayout(pdf_path_row)
        pdf_path_layout.setContentsMargins(0, 0, 0, 0)
        self._pdf_path = QLineEdit()
        self._pdf_path.setPlaceholderText("Path to PDF file…")
        pdf_browse_btn = QPushButton("Browse…")
        pdf_browse_btn.clicked.connect(self._browse_pdf)
        pdf_path_layout.addWidget(self._pdf_path)
        pdf_path_layout.addWidget(pdf_browse_btn)
        pdf_layout.addRow("File:", pdf_path_row)

        self._pdf_scale = QDoubleSpinBox()
        self._pdf_scale.setRange(0.5, 4.0)
        self._pdf_scale.setSingleStep(0.25)
        self._pdf_scale.setDecimals(2)
        self._pdf_scale.setSuffix("×")
        pdf_layout.addRow("Render scale:", self._pdf_scale)
        layout.addWidget(self._pdf_box)

        layout.addStretch()

        self._rb_image.toggled.connect(self._on_mode_toggle)
        self._rb_text.toggled.connect(self._on_mode_toggle)
        self._rb_both.toggled.connect(self._on_mode_toggle)
        self._rb_pdf.toggled.connect(self._on_mode_toggle)
        return w

    def _build_appearance_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(14)
        form.setContentsMargins(16, 16, 16, 16)

        # Background color
        self._bg_color = ColorButton(self._config["background_color"])
        form.addRow("Background color:", self._bg_color)

        # Opacity slider
        opacity_row = QWidget()
        op_layout = QHBoxLayout(opacity_row)
        op_layout.setContentsMargins(0, 0, 0, 0)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 255)
        self._opacity_label = QLabel()
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{int(v / 255 * 100)}%")
        )
        op_layout.addWidget(self._opacity_slider)
        op_layout.addWidget(self._opacity_label)
        form.addRow("Background opacity:", opacity_row)

        # Text color
        self._text_color = ColorButton(self._config["text_color"])
        form.addRow("Text color:", self._text_color)

        # Font size
        self._font_size = QSpinBox()
        self._font_size.setRange(8, 200)
        self._font_size.setSuffix(" pt")
        form.addRow("Font size:", self._font_size)

        # Window size
        size_row = QWidget()
        size_layout = QHBoxLayout(size_row)
        size_layout.setContentsMargins(0, 0, 0, 0)
        self._win_width = QSpinBox()
        self._win_width.setRange(200, 3840)
        self._win_width.setSuffix(" px")
        self._win_height = QSpinBox()
        self._win_height.setRange(100, 2160)
        self._win_height.setSuffix(" px")
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(self._win_width)
        size_layout.addWidget(QLabel("  H:"))
        size_layout.addWidget(self._win_height)
        size_layout.addStretch()
        form.addRow("Window size:", size_row)

        # Tray icon
        tray_row = QWidget()
        tray_layout = QHBoxLayout(tray_row)
        tray_layout.setContentsMargins(0, 0, 0, 0)
        self._tray_icon_path = QLineEdit()
        self._tray_icon_path.setPlaceholderText("Leave empty for default icon…")
        tray_browse = QPushButton("Browse…")
        tray_browse.clicked.connect(self._browse_tray_icon)
        tray_layout.addWidget(self._tray_icon_path)
        tray_layout.addWidget(tray_browse)
        form.addRow("Tray icon:", tray_row)

        return w

    def _build_shortcut_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        box = QGroupBox("Global keyboard shortcut")
        box_layout = QHBoxLayout(box)
        self._shortcut_label = QLabel()
        self._shortcut_label.setStyleSheet(
            "font-size:16px; font-weight:bold; padding:4px 14px;"
            "background:#2b2b2b; border-radius:6px; border:1px solid #555;"
        )
        change_btn = QPushButton("Change…")
        change_btn.clicked.connect(self._record_shortcut)
        box_layout.addWidget(self._shortcut_label)
        box_layout.addStretch()
        box_layout.addWidget(change_btn)
        layout.addWidget(box)

        note = QLabel(
            "Uses X11 global hotkeys (via pynput / Xlib).\n"
            "Avoid combinations already claimed by your desktop environment."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(note)
        layout.addStretch()
        return w

    def _build_reading_line_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self._rl_active = QCheckBox("Show reading line (horizontal guide that follows the cursor)")
        layout.addWidget(self._rl_active)

        # Appearance group
        appearance_box = QGroupBox("Line appearance")
        form = QFormLayout(appearance_box)
        form.setSpacing(12)

        self._rl_color = ColorButton(self._config.get("rl_color", "#ff0000"))
        form.addRow("Color:", self._rl_color)

        rl_opacity_row = QWidget()
        rl_op_layout = QHBoxLayout(rl_opacity_row)
        rl_op_layout.setContentsMargins(0, 0, 0, 0)
        self._rl_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._rl_opacity_slider.setRange(0, 255)
        self._rl_opacity_label = QLabel()
        self._rl_opacity_slider.valueChanged.connect(
            lambda v: self._rl_opacity_label.setText(f"{int(v / 255 * 100)}%")
        )
        rl_op_layout.addWidget(self._rl_opacity_slider)
        rl_op_layout.addWidget(self._rl_opacity_label)
        form.addRow("Opacity:", rl_opacity_row)

        rl_thickness_row = QWidget()
        rl_th_layout = QHBoxLayout(rl_thickness_row)
        rl_th_layout.setContentsMargins(0, 0, 0, 0)
        self._rl_thickness = QSlider(Qt.Orientation.Horizontal)
        self._rl_thickness.setRange(1, 20)
        self._rl_thickness_label = QLabel()
        self._rl_thickness.valueChanged.connect(
            lambda v: self._rl_thickness_label.setText(f"{v} px")
        )
        rl_th_layout.addWidget(self._rl_thickness)
        rl_th_layout.addWidget(self._rl_thickness_label)
        form.addRow("Thickness:", rl_thickness_row)

        self._rl_length = QSpinBox()
        self._rl_length.setRange(100, 3840)
        self._rl_length.setSuffix(" px")
        form.addRow("Length:", self._rl_length)

        layout.addWidget(appearance_box)

        # Shortcut group
        sc_box = QGroupBox("Toggle shortcut")
        sc_layout = QHBoxLayout(sc_box)
        self._rl_shortcut_label = QLabel()
        self._rl_shortcut_label.setStyleSheet(
            "font-size:16px; font-weight:bold; padding:4px 14px;"
            "background:#2b2b2b; border-radius:6px; border:1px solid #555;"
        )
        rl_change_btn = QPushButton("Change…")
        rl_change_btn.clicked.connect(self._record_rl_shortcut)
        sc_layout.addWidget(self._rl_shortcut_label)
        sc_layout.addStretch()
        sc_layout.addWidget(rl_change_btn)
        layout.addWidget(sc_box)

        layout.addStretch()
        return w

    # ── Internal helpers ───────────────────────────────────────────────────

    def _load_values(self) -> None:
        c = self._config

        if c["mode"] == "both":
            self._rb_both.setChecked(True)
        elif c["mode"] == "text":
            self._rb_text.setChecked(True)
        elif c["mode"] == "pdf":
            self._rb_pdf.setChecked(True)
        else:
            self._rb_image.setChecked(True)
        self._on_mode_toggle()

        self._image_path.setText(c["image_path"])
        self._text_edit.setPlainText(c["text"])
        self._pdf_path.setText(c.get("pdf_path", ""))
        self._pdf_scale.setValue(c.get("pdf_scale", 1.0))

        self._bg_color.set_color(c["background_color"])
        self._opacity_slider.setValue(c["background_opacity"])
        self._text_color.set_color(c["text_color"])
        self._font_size.setValue(c["text_font_size"])
        self._win_width.setValue(c["window_width"])
        self._win_height.setValue(c["window_height"])
        self._tray_icon_path.setText(c.get("tray_icon_path", ""))

        self._shortcut_label.setText(pynput_to_human(c["shortcut"]))

        self._rl_active.setChecked(c.get("rl_active", False))
        self._rl_color.set_color(c.get("rl_color", "#ff0000"))
        self._rl_opacity_slider.setValue(c.get("rl_opacity", 255))
        self._rl_thickness.setValue(c.get("rl_thickness", 2))
        self._rl_length.setValue(c.get("rl_length", 800))
        self._rl_shortcut_label.setText(pynput_to_human(c.get("rl_shortcut", "<ctrl>+<shift>+l")))

    def _on_mode_toggle(self) -> None:
        self._image_box.setVisible(self._rb_image.isChecked() or self._rb_both.isChecked())
        self._text_box.setVisible(self._rb_text.isChecked() or self._rb_both.isChecked())
        self._pdf_box.setVisible(self._rb_pdf.isChecked())

    def _browse_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.svg *.tiff)",
        )
        if path:
            self._image_path.setText(path)

    def _browse_tray_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Tray Icon", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.svg *.ico)",
        )
        if path:
            self._tray_icon_path.setText(path)

    def _browse_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF", "",
            "PDF files (*.pdf)",
        )
        if path:
            self._pdf_path.setText(path)

    def _record_shortcut(self) -> None:
        dlg = _ShortcutRecorder(self._current_shortcut, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._current_shortcut = dlg.get_shortcut()
            self._shortcut_label.setText(pynput_to_human(self._current_shortcut))

    def _record_rl_shortcut(self) -> None:
        dlg = _ShortcutRecorder(self._rl_current_shortcut, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._rl_current_shortcut = dlg.get_shortcut()
            self._rl_shortcut_label.setText(pynput_to_human(self._rl_current_shortcut))

    def _save(self) -> None:
        if self._rb_both.isChecked():
            mode = "both"
        elif self._rb_text.isChecked():
            mode = "text"
        elif self._rb_pdf.isChecked():
            mode = "pdf"
        else:
            mode = "image"
        new_config = {
            "mode": mode,
            "image_path": self._image_path.text().strip(),
            "pdf_path": self._pdf_path.text().strip(),
            "pdf_scale": self._pdf_scale.value(),
            "text": self._text_edit.toPlainText(),
            "text_font_size": self._font_size.value(),
            "text_color": self._text_color.get_color(),
            "background_color": self._bg_color.get_color(),
            "background_opacity": self._opacity_slider.value(),
            "shortcut": self._current_shortcut,
            "window_width": self._win_width.value(),
            "window_height": self._win_height.value(),
            "tray_icon_path": self._tray_icon_path.text().strip(),
            "rl_active": self._rl_active.isChecked(),
            "rl_color": self._rl_color.get_color(),
            "rl_opacity": self._rl_opacity_slider.value(),
            "rl_thickness": self._rl_thickness.value(),
            "rl_length": self._rl_length.value(),
            "rl_shortcut": self._rl_current_shortcut,
        }
        self.saved.emit(new_config)
        self.accept()
