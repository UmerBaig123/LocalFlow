"""System tray icon with state-based icons generated via QPainter."""

from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def _make_icon(color: str, ring: bool = False) -> QIcon:
    """Generate a simple circular tray icon."""
    size = 64
    pix = QPixmap(QSize(size, size))
    pix.fill(QColor(0, 0, 0, 0))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if ring:
        p.setPen(QPen(QColor(color), 4))
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))
        p.drawEllipse(6, 6, size - 12, size - 12)
    else:
        p.setPen(QPen(QColor(color), 2))
        p.setBrush(QBrush(QColor(color)))
        p.drawEllipse(8, 8, size - 16, size - 16)
    p.end()
    return QIcon(pix)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with menu-driven interaction (GNOME compatible)."""

    toggle_popup = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icons = {
            "idle": _make_icon("#89b4fa"),
            "recording": _make_icon("#f38ba8", ring=True),
            "processing": _make_icon("#f9e2af"),
            "done": _make_icon("#a6e3a1"),
            "error": _make_icon("#f38ba8"),
        }
        self.setIcon(self._icons["idle"])
        self.setToolTip("LocalFlow")

        menu = QMenu()

        open_action = QAction("Open", menu)
        open_action.triggered.connect(self.toggle_popup.emit)
        menu.addAction(open_action)

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._on_quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        # Also support left-click toggle on DEs where it works
        self.activated.connect(self._on_activated)

    def set_state(self, state: str):
        icon = self._icons.get(state, self._icons["idle"])
        self.setIcon(icon)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_popup.emit()

    def _on_quit(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().quit()
