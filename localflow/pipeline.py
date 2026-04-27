"""Pipeline worker: transcribe → refine → signal completion.

Runs in a QThread so the UI stays responsive.
"""

import re

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

_FENCE_RE = re.compile(r"^```\w*\n?", re.MULTILINE)

from localflow.core.transcriber import Transcriber
from localflow.core.refiner import Refiner


class PipelineWorker(QThread):
    """Processes recorded audio through transcription and refinement."""

    status_changed = pyqtSignal(str)
    transcription_ready = pyqtSignal(str)
    refine_token = pyqtSignal(str)
    finished_text = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio: np.ndarray, transcriber: Transcriber, mode: str, parent=None):
        super().__init__(parent)
        self._audio = audio
        self._transcriber = transcriber
        self._refiner = Refiner()
        self._mode = mode

    def run(self):
        try:
            self.status_changed.emit("Transcribing...")
            raw = self._transcriber.transcribe(self._audio)
            if not raw:
                self.error.emit("No speech detected.")
                return
            self.transcription_ready.emit(raw)

            if self._mode == "transcript":
                self.finished_text.emit(raw)
                return

            self.status_changed.emit("Responding..." if self._mode in {"interact", "fitness", "todo"} else "Refining...")
            refined_parts: list[str] = []
            for token in self._refiner.refine_stream(raw, self._mode, status_callback=self.status_changed.emit):
                refined_parts.append(token)
                self.refine_token.emit(token)
            refined = "".join(refined_parts).strip()
            if not refined:
                refined = raw
            if self._mode == "code":
                refined = _FENCE_RE.sub("", refined).strip()
            self.finished_text.emit(refined)

        except Exception as e:
            self.error.emit(str(e))
