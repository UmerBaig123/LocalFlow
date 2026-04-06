"""Audio recorder using sounddevice — 16kHz mono float32."""

from collections.abc import Callable

import numpy as np
import sounddevice as sd

from localflow.config import AUDIO_SAMPLE_RATE


class Recorder:
    """Records audio into a numpy buffer via sounddevice callback."""

    def __init__(self):
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._level_callback: Callable[[float], None] | None = None

    def set_level_callback(self, cb: Callable[[float], None]):
        """Set a callback that receives RMS level (0.0–1.0) per audio chunk."""
        self._level_callback = cb

    def start(self):
        self._chunks.clear()
        self._stream = sd.InputStream(
            samplerate=AUDIO_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return the audio as a 1-D float32 array."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._chunks).flatten()

    def _callback(self, indata: np.ndarray, frames, time_info, status):
        self._chunks.append(indata.copy())
        if self._level_callback is not None:
            rms = float(np.sqrt(np.mean(indata ** 2)))
            # Clamp to 0–1 (rms of speech is typically 0.01–0.3)
            level = min(1.0, rms * 5.0)
            self._level_callback(level)
