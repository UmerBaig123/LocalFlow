"""Main application: QApplication + tray + popup + pipeline wiring."""

import sys

from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
from PyQt6.QtWidgets import QApplication

from localflow.core.recorder import Recorder
from localflow.core.transcriber import Transcriber
from localflow.core.injector import Injector
from localflow.pipeline import PipelineWorker
from localflow.ui.tray import TrayIcon
from localflow.ui.popup import PopupWindow

class LocalFlowApp:
    """Wires UI to the record → transcribe → refine → inject pipeline."""

    def __init__(self, qapp: QApplication):
        self._qapp = qapp
        self._recorder = Recorder()
        self._transcriber = Transcriber()
        self._injector = Injector()
        self._worker: PipelineWorker | None = None
        self._recording = False
        self._refined_buf = ""

        # Audio level callback (called from sounddevice thread → marshal to main)
        self._recorder.set_level_callback(self._on_audio_level)

        # UI
        self._tray = TrayIcon()
        self._popup = PopupWindow()

        # Connections
        self._tray.toggle_popup.connect(self._popup.toggle)
        self._popup.record_clicked.connect(self._on_record_toggle)
        self._popup.cancel_clicked.connect(self._on_cancel)

        self._tray.show()

    def _on_audio_level(self, level: float):
        """Called from the sounddevice thread — invoke on main thread."""
        QMetaObject.invokeMethod(
            self._popup, "push_audio_level",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(float, level),
        )

    # --- Record toggle ---

    def _on_record_toggle(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._recording = True
        self._refined_buf = ""
        self._popup.set_recording(True)
        self._popup.set_status("Recording...")
        self._popup.set_preview("")
        self._tray.set_state("recording")
        self._recorder.start()

    def _stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        self._popup.set_recording(False)
        self._popup.set_status("Processing...")
        self._tray.set_state("processing")
        audio = self._recorder.stop()

        if audio.size == 0:
            self._popup.set_status("No audio captured.")
            self._tray.set_state("idle")
            return

        mode = self._popup.current_mode()
        self._worker = PipelineWorker(audio, self._transcriber, mode)
        self._worker.status_changed.connect(self._popup.set_status)
        self._worker.transcription_ready.connect(self._on_transcription)
        self._worker.refine_token.connect(self._on_refine_token)
        self._worker.finished_text.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    # --- Pipeline callbacks ---

    def _on_transcription(self, raw: str):
        self._popup.set_preview(raw)
        mode = self._popup.current_mode()
        self._popup.set_status("Responding..." if mode == "interact" else "Refining...")

    def _on_refine_token(self, token: str):
        self._refined_buf += token
        self._popup.set_preview(self._refined_buf)

    def _on_finished(self, text: str):
        self._popup.set_status("Done — copied!")
        self._tray.set_state("idle")
        self._injector.inject(text)

    def _on_cancel(self):
        if not self._recording:
            return
        self._recording = False
        self._recorder.stop()  # discard audio
        self._popup.set_recording(False)
        self._popup.set_status("Ready — click to record")
        self._tray.set_state("idle")

    def _on_error(self, msg: str):
        self._popup.set_status(f"Error: {msg}")
        self._popup.set_preview("")
        self._tray.set_state("error")


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _flow = LocalFlowApp(app)  # prevent GC
    return app.exec()
