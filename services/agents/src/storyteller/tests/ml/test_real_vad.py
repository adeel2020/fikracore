"""Real Silero VAD integration tests.

These exercise genuine neural VAD classification on real synthesised speech and
verify per-instance streaming-state isolation (each ``SileroVAD`` builds its own
``VADIterator`` over shared, cached model weights).
"""

from __future__ import annotations

import numpy as np
import pytest

from storyteller.voice.vad import SILERO_CHUNK_SAMPLES, SileroVAD, VADError

pytestmark = pytest.mark.real_ml


def _chunks(audio: np.ndarray, *, pad: bool = True) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    for i in range(0, len(audio), SILERO_CHUNK_SAMPLES):
        chunk = audio[i : i + SILERO_CHUNK_SAMPLES]
        if len(chunk) < SILERO_CHUNK_SAMPLES:
            if not pad:
                break
            chunk = np.pad(chunk, (0, SILERO_CHUNK_SAMPLES - len(chunk)))
        out.append(np.asarray(chunk, dtype=np.float32))
    return out


def _events(vad: SileroVAD, audio: np.ndarray) -> list[str]:
    kinds: list[str] = []
    for c in _chunks(audio):
        e = vad.process(c)
        if e is not None:
            kinds.append(e.kind)
    return kinds


def _silence(seconds: float = 1.0) -> np.ndarray:
    return np.zeros(int(seconds * 16000), dtype=np.float32)


def test_real_vad_silence_never_fires(real_vad):
    assert _events(real_vad, _silence(1.0)) == []


def test_real_vad_detects_real_speech(real_vad, real_speech_16k):
    kinds = _events(real_vad, real_speech_16k)
    assert "start" in kinds
    assert "end" in kinds
    assert kinds.index("start") < kinds.index("end")


def test_real_vad_speech_ranges(real_vad, real_speech_16k):
    ranges = real_vad.speech_ranges(real_speech_16k, 16000)
    assert len(ranges) == 1
    start, end = ranges[0]
    assert 0 <= start < end <= len(real_speech_16k)


def test_real_vad_reset_clears_streaming_state(real_vad, real_speech_16k):
    _events(real_vad, real_speech_16k)
    real_vad.reset()
    assert _events(real_vad, _silence(1.0)) == []


def test_real_vad_rejects_wrong_sample_rate(real_vad):
    with pytest.raises(VADError):
        real_vad.speech_ranges(np.zeros(16000, dtype=np.float32), 8000)


def test_real_vad_instances_are_isolated(real_tts, real_speech_16k):
    # A second instance shares the cached model weights but must keep its own
    # streaming iterator, so one connection's speech must not leak into another.
    other = SileroVAD()
    other.init()
    assert _events(other, _silence(1.0)) == []

    primary = SileroVAD()
    primary.init()
    assert "start" in _events(primary, real_speech_16k)
    assert _events(other, _silence(0.5)) == []
