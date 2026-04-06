"""Frameless floating popup — the main LocalFlow UI."""

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QPoint
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTextEdit, QSizePolicy, QComboBox,
)

from localflow.config import MODE_PROMPTS, REFINE_MODE
from localflow.ui.styles import POPUP_STYLE
from localflow.ui.waveform import WaveformWidget


class PopupWindow(QWidget):
    """Floating popup toggled by the tray icon."""

    record_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(420)
        self.setStyleSheet(POPUP_STYLE)

        self._recording = False
        self._drag_pos: QPoint | None = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._frame = QFrame()
        self._frame.setObjectName("MainFrame")
        outer.addWidget(self._frame)

        root = QVBoxLayout(self._frame)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)

        # -- Top bar: minimize button right-aligned --
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)
        top_bar.addStretch()

        self._minimize_btn = QPushButton("\u2212")  # −
        self._minimize_btn.setObjectName("MinimizeButton")
        self._minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._minimize_btn.setToolTip("Minimize to tray")
        self._minimize_btn.clicked.connect(self.hide)
        top_bar.addWidget(self._minimize_btn)

        root.addLayout(top_bar)

        # -- Header row: title/status left, record button right --
        header = QHBoxLayout()
        header.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        self._title = QLabel("LocalFlow")
        self._title.setObjectName("TitleLabel")
        title_col.addWidget(self._title)

        self._status = QLabel("Ready — click to record")
        self._status.setObjectName("StatusLabel")
        title_col.addWidget(self._status)

        # Mode dropdown
        self._mode_combo = QComboBox()
        self._mode_combo.setObjectName("ModeCombo")
        for mode in MODE_PROMPTS:
            self._mode_combo.addItem(mode.capitalize(), mode)
        idx = self._mode_combo.findData(REFINE_MODE)
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        title_col.addWidget(self._mode_combo)

        header.addLayout(title_col, stretch=1)

        self._cancel_btn = QPushButton("\u2715")  # ✕
        self._cancel_btn.setObjectName("CancelButton")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setToolTip("Cancel recording")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        header.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._rec_btn = QPushButton("\u25cf")  # ●
        self._rec_btn.setObjectName("RecordButton")
        self._rec_btn.setProperty("recording", False)
        self._rec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rec_btn.clicked.connect(self._on_record)
        header.addWidget(self._rec_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # -- Waveform (visible during recording) --
        self._waveform = WaveformWidget()
        self._waveform.setVisible(False)
        root.addWidget(self._waveform)

        # -- Preview area --
        self._preview = QTextEdit()
        self._preview.setObjectName("PreviewText")
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("Transcription will appear here...")
        self._preview.setMinimumHeight(100)
        self._preview.setMaximumHeight(200)
        self._preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        root.addWidget(self._preview)

        # -- Hint --
        self._hint = QLabel("Drag to move")
        self._hint.setObjectName("HintLabel")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._hint)

    # --- Public API ---

    def set_status(self, text: str):
        self._status.setText(text)

    def set_preview(self, text: str):
        self._preview.setPlainText(text)
        sb = self._preview.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(float)
    def push_audio_level(self, level: float):
        self._waveform.push_level(level)

    def set_recording(self, active: bool):
        self._recording = active
        self._rec_btn.setProperty("recording", active)
        self._rec_btn.setText("\u25a0" if active else "\u25cf")  # ■ or ●
        self._rec_btn.style().unpolish(self._rec_btn)
        self._rec_btn.style().polish(self._rec_btn)
        self._cancel_btn.setVisible(active)
        self._waveform.setVisible(active)
        if not active:
            self._waveform.clear()

    def current_mode(self) -> str:
        return self._mode_combo.currentData()

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self._position_near_cursor()
            self.show()

    # --- Internal ---

    def _on_record(self):
        self.record_clicked.emit()

    def _on_cancel(self):
        self.cancel_clicked.emit()

    def _on_mode_changed(self):
        self.mode_changed.emit(self._mode_combo.currentData())

    def _position_near_cursor(self):
        cursor = QCursor.pos()
        screen = self.screen().availableGeometry()
        x = cursor.x() - self.width() // 2
        y = cursor.y() + 20
        x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
        y = max(screen.top() + 8, min(y, screen.bottom() - 350))
        self.move(x, y)

    # --- Drag ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
