#!/usr/bin/env bash
# install.sh — set up Akira on Linux (X11 / Wayland)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="akira"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "=== Akira — Installer ==="
echo

# ── 1. Python dependencies ─────────────────────────────────────────────────
echo "Installing Python dependencies (PyQt6, pynput, PyMuPDF)…"

install_pip() {
    pip3 install --user -q "$@" 2>/dev/null \
        || pip3 install --user -q --break-system-packages "$@" \
        || { echo "  pip3 failed for $*"; return 1; }
}

if command -v pip3 &>/dev/null; then
    install_pip PyQt6 pynput PyMuPDF
elif command -v pip &>/dev/null; then
    pip install --user -q PyQt6 pynput PyMuPDF 2>/dev/null \
        || pip install --user -q --break-system-packages PyQt6 pynput PyMuPDF
else
    if command -v dnf &>/dev/null; then
        echo "  pip not found — trying dnf…"
        sudo dnf install -y python3-pyqt6 python3-pynput 2>/dev/null \
            || { echo "  dnf failed. Install python3-pyqt6 and python3-pynput manually."; exit 1; }
    else
        echo "Error: pip not found. Install pip and re-run, or install PyQt6 and pynput manually."
        exit 1
    fi
fi
echo "Dependencies OK."
echo

# ── 2. Make script executable ─────────────────────────────────────────────
chmod +x "$SCRIPT_DIR/main.py"

# ── 3. Application .desktop entry ─────────────────────────────────────────
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Akira
Comment=Display an image or text with a global keyboard shortcut
Exec=/usr/bin/python3 $SCRIPT_DIR/main.py
Icon=akira
Type=Application
Categories=Utility;
Keywords=shortcut;image;text;overlay;display;
EOF
echo "App entry: $DESKTOP_DIR/$APP_NAME.desktop"

# ── 4. Autostart entry ────────────────────────────────────────────────────
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Akira
Comment=Start Akira on login
Exec=/usr/bin/python3 $SCRIPT_DIR/main.py
Type=Application
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
EOF
echo "Autostart entry: $AUTOSTART_DIR/$APP_NAME.desktop"

# ── Done ───────────────────────────────────────────────────────────────────
echo
echo "=== Installation complete! ==="
echo
echo "  Run now:          python3 $SCRIPT_DIR/main.py"
echo "  Or launch from:   your application menu → 'Akira'"
echo
echo "  Default shortcut: Ctrl+Shift+I"
echo "  Right-click the tray icon to open Settings or Quit."
echo
