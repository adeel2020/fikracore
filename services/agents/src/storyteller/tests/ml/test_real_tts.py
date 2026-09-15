"""Real Kokoro TTS integration tests.

Verifies genuine synthesis (audio bytes at 24 kHz), graceful empty-text
handling, and the sentence-chunked streamer used by the live pipeline.
"""

from __future__ import annotations

import numpy as np
import pytest

from storyteller.voice.tts import (
    KOKORO_SAMPLE_RATE,
    ChunkedKokoroTTS,
    KokoroTTS,
    TTSError,
    split_sentences,
)

pytestmark = pytest.mark.real_ml


def test_real_tts_synthesizes_known_text(real_tts):
    r = real_tts.synthesize("The quick brown fox jumps over the lazy dog.")
    assert r.audio is not None and r.audio.size > 0
    assert r.audio.dtype == np.float32
    assert r.sample_rate == KOKORO_SAMPLE_RATE
    assert r.duration > 0
    assert np.isfinite(r.audio).all()
    assert np.max(np.abs(r.audio)) <= 1.0 + 1e-3


def test_real_tts_raw_first_use_is_lazy(real_tts, real_speech_16k):
    # A brand new backend must also load lazily and work.
    fresh = KokoroTTS(voice="af_heart", device="cpu")
    fresh.init()
    r = fresh.synthesize("Hello world.")
    assert r.audio.size > 0


def test_real_tts_empty_text_raises(real_tts):
    with pytest.raises(TTSError):
        real_tts.synthesize("")
    with pytest.raises(TTSError):
        real_tts.synthesize("   ")


def test_real_tts_uninitialized_raises():
    backend = KokoroTTS()
    with pytest.raises(TTSError):
        backend.synthesize("hello")


def test_real_tts_chunked_streaming(real_tts):
    streamer = ChunkedKokoroTTS(backend=real_tts)
    streamer.start(sample_rate=KOKORO_SAMPLE_RATE)

    answer = "Registration services are healthy. The AMF scaled out at seven AM and recovered fully."
    chunks = split_sentences(answer)
    assert len(chunks) >= 2

    produced = []
    for chunk in chunks:
        r = streamer.synthesize_chunk(chunk)
        assert r is not None and r.audio.size > 0
        produced.append(r.audio)
    streamer.stop()
    sounds = np.concatenate(produced)
    assert sounds.size > 0


def test_real_tts_chunked_empty_returns_none(real_tts):
    streamer = ChunkedKokoroTTS(backend=real_tts)
    streamer.start(sample_rate=KOKORO_SAMPLE_RATE)
    assert streamer.synthesize_chunk("") is None
    assert streamer.synthesize_chunk("   ") is None
    streamer.stop()


def test_real_tts_split_sentences_for_real_streaming():
    text = "One sentence. Two sentences! Three?\nFour."
    chunks = split_sentences(text)
    assert any("One" in c for c in chunks)
    assert any("Two" in c for c in chunks)
    assert any("Three" in c for c in chunks)
    assert any("Four" in c for c in chunks)
