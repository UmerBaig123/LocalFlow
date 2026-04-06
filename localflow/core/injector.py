"""Text injection — copy to clipboard and paste as plain text."""

import subprocess
import time

from PyQt6.QtWidgets import QApplication


class Injector:
    def inject(self, text: str):
        QApplication.clipboard().setText(text)
        time.sleep(0.05)
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", "ctrl+shift+v"],
            check=True, timeout=5,
        )
