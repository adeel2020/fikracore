"""Real faster-whisper STT integration tests.

Verifies genuine transcription on real synthesised speech through both the raw
backend and the incremental/phased streamer used by the live pipeline. The heavy
backend is shared; only per-utterance buffer state is per-streamer.
"""

from __future__ import annotations

import numpy as np
import pytest

from storyteller.voice.stt import (
    FasterWhisperSTT,
    IncrementalWhisperSTT,
    STTError,
)

pytestmark = pytest.mark.real_ml


def test_real_stt_transcribes_real_speech(real_stt, real_speech_16k):
    result = real_stt.transcribe(real_speech_16k, 16000)
    assert result.text.strip() != ""
    assert result.duration >= 0


def test_real_stt_backend_can_be_reused_after_reset(real_stt, real_speech_16k):
    # A backend shared across utterances must stay stateless across calls.
    first = real_stt.transcribe(real_speech_16k, 16000)
    second = real_stt.transcribe(np.zeros(int(0.5 * 16000), dtype=np.float32), 16000)
    assert first.text.strip() != ""
    assert isinstance(second.text, str)


def test_real_stt_uninitialized_raises():
    backend = FasterWhisperSTT(model="Systran/faster-whisper-tiny")
    with pytest.raises(STTError):
        backend.transcribe(np.zeros(16000, dtype=np.float32), 16000)


def test_real_stt_incremental_finalizes(real_stt, real_speech_16k):
    streamer = IncrementalWhisperSTT(backend=real_stt, partial_interval_ms=0)
    streamer.start(sample_rate=16000)
    for c in _chunks(real_speech_16k):
        streamer.accept_audio(c)
    partial = streamer.get_partial()
    final = streamer.finalize()
    assert isinstance(partial, str)
    assert final.text.strip() != ""
    assert final.duration >= 0


def test_real_stt_utterance_isolation(real_stt, real_speech_16k):
    # Two streamers over one shared backend must not share running buffers.
    a = IncrementalWhisperSTT(backend=real_stt, partial_interval_ms=0)
    b = IncrementalWhisperSTT(backend=real_stt, partial_interval_ms=0)
    a.start(sample_rate=16000)
    b.start(sample_rate=16000)
    for c in _chunks(real_speech_16k):
        a.accept_audio(c)
    fa = a.finalize()
    fb = b.finalize()
    assert fa.text.strip() != ""
    assert fb.text in ("", " ")
    a.reset()
    b.reset()


def _chunks(audio: np.ndarray):
    out = []
    for i in range(0, len(audio), 16000):
        out.append(audio[i : i + 16000])
    return [c for c in out if c.size] or [audio]
