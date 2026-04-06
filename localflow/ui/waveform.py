"""Real-time audio waveform bar visualization."""

from collections import deque

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget


class WaveformWidget(QWidget):
    """Displays a rolling waveform of audio levels as vertical bars."""

    BAR_WIDTH = 3
    BAR_GAP = 2
    MAX_BARS = 60
    COLOR_LOW = QColor("#89b4fa")
    COLOR_HIGH = QColor("#f38ba8")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._levels: deque[float] = deque(maxlen=self.MAX_BARS)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)

    def push_level(self, level: float):
        """Add a new audio level (0.0–1.0) and repaint."""
        self._levels.append(level)
        self.update()

    def clear(self):
        self._levels.clear()
        self.update()

    def sizeHint(self):
        return QSize(self.MAX_BARS * (self.BAR_WIDTH + self.BAR_GAP), 40)

    def paintEvent(self, event):
        if not self._levels:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        w = self.width()
        bar_step = self.BAR_WIDTH + self.BAR_GAP
        total_bars = min(len(self._levels), w // bar_step)

        # Draw bars right-aligned (newest on the right)
        start_x = w - total_bars * bar_step
        levels = list(self._levels)[-total_bars:]

        for i, level in enumerate(levels):
            x = start_x + i * bar_step
            bar_h = max(2, int(level * (h - 4)))
            y = (h - bar_h) // 2

            # Interpolate color based on level
            r = int(self.COLOR_LOW.red() + (self.COLOR_HIGH.red() - self.COLOR_LOW.red()) * level)
            g = int(self.COLOR_LOW.green() + (self.COLOR_HIGH.green() - self.COLOR_LOW.green()) * level)
            b = int(self.COLOR_LOW.blue() + (self.COLOR_HIGH.blue() - self.COLOR_LOW.blue()) * level)
            color = QColor(r, g, b)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(x, y, self.BAR_WIDTH, bar_h, 1, 1)

        p.end()
