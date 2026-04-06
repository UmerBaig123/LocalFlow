#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

echo "=== LocalFlow Setup ==="

# System dependencies
echo "[1/4] Installing system dependencies..."
if command -v apt-get &>/dev/null; then
    if dpkg -l libportaudio2 &>/dev/null && which xdotool &>/dev/null; then
        echo "  System deps already installed"
    else
        sudo apt-get update -qq
        sudo apt-get install -y -qq libportaudio2 xdotool
    fi
else
    echo "  Not a Debian/Ubuntu system — install portaudio and xdotool manually"
fi

# Bundled portaudio fallback (if system lib missing)
echo "[2/4] Checking portaudio..."
if ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    if [ -f "$LIB_DIR/libportaudio.so.2" ]; then
        echo "  Using bundled portaudio in lib/"
    else
        echo "  Downloading portaudio .deb and extracting..."
        mkdir -p "$LIB_DIR"
        TMP=$(mktemp -d)
        apt-get download libportaudio2 -o Dir::Cache::archives="$TMP" 2>/dev/null || \
            (cd "$TMP" && apt-get download libportaudio2)
        dpkg-deb -x "$TMP"/libportaudio2*.deb "$TMP/extracted"
        cp "$TMP"/extracted/usr/lib/*/libportaudio.so.* "$LIB_DIR/"
        cd "$LIB_DIR" && ln -sf libportaudio.so.2.* libportaudio.so.2 && ln -sf libportaudio.so.2 libportaudio.so
        rm -rf "$TMP"
        echo "  Extracted portaudio to $LIB_DIR"
    fi
fi

# Python dependencies
echo "[3/4] Installing Python packages..."
pip install PyQt6 sounddevice faster-whisper httpx numpy python-dotenv

# Verify
echo "[4/4] Verifying installation..."
export LD_LIBRARY_PATH="$LIB_DIR:${LD_LIBRARY_PATH:-}"
python -c "
import sounddevice, faster_whisper, httpx, numpy, dotenv
from PyQt6.QtWidgets import QApplication
print('All dependencies OK')
"

echo ""
echo "=== Setup complete! ==="
echo "Run with: python -m localflow"
