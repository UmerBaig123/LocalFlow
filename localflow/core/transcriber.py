"""Faster-whisper GPU transcription."""

import numpy as np
from faster_whisper import WhisperModel

from localflow.config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE


class Transcriber:
    """Loads faster-whisper model on first use and transcribes audio arrays."""

    def __init__(self):
        self._model: WhisperModel | None = None

    def _ensure_model(self):
        if self._model is None:
            self._model = WhisperModel(
                WHISPER_MODEL,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
            )

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a 16kHz float32 audio array to text."""
        self._ensure_model()
        segments, _info = self._model.transcribe(
            audio,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
            # Don't let previous segments influence the next — prevents runaway completions
            condition_on_previous_text=False,
            # Filter out hallucinated segments during silence
            no_speech_threshold=0.6,
            hallucination_silence_threshold=2.0,
            # Suppress common hallucination tokens (thanks, subscribe, etc.)
            suppress_blank=True,
        )
        # Drop low-confidence segments
        parts = []
        for seg in segments:
            if seg.no_speech_prob < 0.7:
                parts.append(seg.text.strip())
        return " ".join(parts).strip()
