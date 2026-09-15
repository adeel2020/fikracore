"""Voice Activity Detection (VAD) adapters.

Phase 3B: a thin, replaceable adapter layer so the voice pipeline is
model-agnostic and tests can substitute fakes. The real backend is Silero VAD
(``silero_vad``), imported lazily inside ``init()`` so the module loads without
the ML stack installed.

Backends load their model assets on ``init()`` (never at import time) and may
download weights on first use.
"""

from __future__ import annotations

import abc
import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

VAD_SAMPLE_RATE = 16000

# Silero VAD expects chunks that are multiples of 512 samples at 16 kHz.
SILERO_CHUNK_SAMPLES = 512

# A single utterance reported by the streaming VAD.
class SpeechEvent:
    __slots__ = ("kind", "sample")

    def __init__(self, kind: str, sample: int) -> None:
        self.kind = kind  # "start" | "end"
        self.sample = int(sample)

    def __repr__(self) -> str:
        return f"SpeechEvent({self.kind!r}, {self.sample})"


# Shared Silero model weights (loaded once, keyed by onnx flag). Each
# ``SileroVAD`` instance builds its own ``VADIterator`` over the shared model so
# per-connection streaming state stays isolated without re-downloading weights.
_silero_model_cache: dict[bool, Any] = {}


def _load_silero_model(onnx: bool):
    if onnx not in _silero_model_cache:
        try:
            import silero_vad  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            raise VADError(f"Silero VAD is unavailable: {exc}") from exc
        _silero_model_cache[onnx] = silero_vad.load_silero_vad(onnx=onnx)
    return _silero_model_cache[onnx]


class VADError(Exception):
    """VAD backend unavailable or misused."""


class VADAdapter(abc.ABC):
    """Streaming VAD interface. Feed 16 kHz mono float32 chunks."""

    sample_rate: int = VAD_SAMPLE_RATE

    @abc.abstractmethod
    def init(self) -> None:
        """Load the backend model. Idempotent; may download assets."""

    @abc.abstractmethod
    def reset(self) -> None:
        """Clear streaming state between utterances."""

    @abc.abstractmethod
    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        """Classify one chunk; return a start/end event or None."""

    def speech_ranges(self, audio: np.ndarray, sample_rate: int) -> list[tuple[int, int]]:
        """Merge streaming events into ``(start_sample, end_sample)`` ranges.

        Default implementation drives the streaming interface with fixed-size
        chunks. Override for whole-buffer backends.
        """
        if sample_rate != self.sample_rate:
            raise VADError(
                f"VAD requires {self.sample_rate} Hz audio, got {sample_rate} Hz"
            )
        audio = np.asarray(audio, dtype=np.float32)
        self.reset()
        ranges: list[tuple[int, int]] = []
        cur_start: int | None = None
        for i in range(0, len(audio), SILERO_CHUNK_SAMPLES):
            chunk = audio[i : i + SILERO_CHUNK_SAMPLES]
            if len(chunk) < SILERO_CHUNK_SAMPLES:
                chunk = np.pad(chunk, (0, SILERO_CHUNK_SAMPLES - len(chunk)))
            event = self.process(chunk)
            if event is None:
                continue
            if event.kind == "start" and cur_start is None:
                cur_start = max(0, min(event.sample, len(audio)))
            elif event.kind == "end" and cur_start is not None:
                end = min(max(cur_start, event.sample), len(audio))
                ranges.append((cur_start, end))
                cur_start = None
        if cur_start is not None:
            ranges.append((cur_start, len(audio)))
        self.reset()
        return ranges


class SileroVAD(VADAdapter):
    """Silero VAD backend (streaming iterator over 16 kHz chunks)."""

    def __init__(
        self,
        *,
        threshold: float | None = None,
        min_silence_duration_ms: int | None = None,
        speech_pad_ms: int | None = None,
        onnx: bool = False,
    ) -> None:
        self.threshold = (
            threshold if threshold is not None else _env_float("VOICE_VAD_THRESHOLD", 0.5)
        )
        self.min_silence_duration_ms = (
            min_silence_duration_ms
            if min_silence_duration_ms is not None
            else _env_int("VOICE_VAD_MIN_SILENCE_MS", 100)
        )
        self.speech_pad_ms = (
            speech_pad_ms if speech_pad_ms is not None else _env_int("VOICE_VAD_SPEECH_PAD_MS", 60)
        )
        self.energy_threshold = _env_float("VOICE_VAD_ENERGY_THRESHOLD", 0.01)
        self.onnx = onnx
        self._model = None
        self._iterator = None

    def init(self) -> None:
        if self._iterator is not None:
            return
        try:
            from silero_vad import VADIterator  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            raise VADError(f"Silero VAD is unavailable: {exc}") from exc
        # Shared weights (cached), per-instance iterator (isolated state).
        self._model = _load_silero_model(onnx=self.onnx)
        self._iterator = VADIterator(
            self._model,
            threshold=self.threshold,
            sampling_rate=self.sample_rate,
            min_silence_duration_ms=self.min_silence_duration_ms,
            speech_pad_ms=self.speech_pad_ms,
        )

    def reset(self) -> None:
        if self._iterator is not None:
            self._iterator.reset_states()

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        if self._iterator is None:
            raise VADError("VAD is not initialized (call init() first)")
        arr = np.asarray(chunk, dtype=np.float32)
        if self.energy_threshold > 0 and arr.size > 0:
            rms = float(np.sqrt(np.mean(arr**2)))
            if rms < self.energy_threshold:
                arr = np.zeros_like(arr)
        result = self._iterator(arr)
        if not result:
            return None
        if "start" in result:
            return SpeechEvent("start", int(result["start"]))
        if "end" in result:
            return SpeechEvent("end", int(result["end"]))
        return None


def create_vad(**kwargs) -> VADAdapter:
    """Factory; override by passing a ``VADAdapter``-compatible backend."""
    return SileroVAD(**kwargs)


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return float(raw)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    return int(raw)


__all__ = [
    "SILERO_CHUNK_SAMPLES",
    "VAD_SAMPLE_RATE",
    "VADAdapter",
    "VADError",
    "SileroVAD",
    "SpeechEvent",
    "create_vad",
]
