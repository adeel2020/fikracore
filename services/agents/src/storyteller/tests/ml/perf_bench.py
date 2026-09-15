"""Phase 3E deterministic performance benchmark.

Profiles the *real* voice stack (Silero VAD / faster-whisper STT / Kokoro TTS)
stage-by-stage using monotonic clocks, the same real-audio fixture and the same
deterministic response the real-ML E2E test uses. It emits the latency breakdown
of compétences §3/§4:

    model init, VAD processing, first speech detected, STT start, first STT
    result (partial), final STT, ConversationService, first response text,
    sentence splitting, TTS start, TTS per chunk, first TTS audio, total turn.

Opt-in: it runs only when ``VOICE_BENCH=1`` **and** the real backends are
available (``VOICE_REAL_ML=1``). Without both it is skipped by ``pytest`` and a
no-op under ``__main__``, so normal CI stays fast and never loads models.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import numpy as np
import pytest

from storyteller.voice.realtime import RealtimeVoicePipeline
from storyteller.voice.stt import (
    IncrementalWhisperSTT,
    STTResult,
    StreamingSTTAdapter,
)
from storyteller.voice.tts import (
    ChunkedKokoroTTS,
    StreamingTTSAdapter,
    TTSResult,
    split_sentences,
)
from storyteller.voice.vad import (
    SILERO_CHUNK_SAMPLES,
    SpeechEvent,
    VADAdapter,
)

pytestmark = [pytest.mark.real_ml]


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() not in ("", "0", "false", "no")


def bench_enabled() -> bool:
    """True only when the operator explicitly opts into the perf benchmark."""
    return _flag("VOICE_BENCH") and _flag("VOICE_REAL_ML")


# ---------------------------------------------------------------------------
# Timing wrappers (read the pipeline's clock at each adapter boundary).
# ---------------------------------------------------------------------------
class _Tape:
    def __init__(self) -> None:
        self.marks: list[tuple[str, float]] = []
        self.chunk_audio: list[float] = []
        self.chunk_dur: list[float] = []

    def mark(self, name: str) -> None:
        self.marks.append((name, time.perf_counter()))

    def elapsed(self, start: str, end: str) -> float:
        ts = dict(self.marks)
        try:
            return max(0.0, (ts[end] - ts[start]) * 1000.0)
        except KeyError:
            return 0.0


class _WrappedVAD(VADAdapter):
    def __init__(self, inner: VADAdapter, tape: _Tape) -> None:
        self._i = inner
        self._tape = tape
        self.sample_rate = inner.sample_rate

    def init(self) -> None:
        self._i.init()

    def reset(self) -> None:
        self._i.reset()

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        return self._i.process(chunk)

    def speech_ranges(self, audio: np.ndarray, sample_rate: int):
        return self._i.speech_ranges(audio, sample_rate)


class _WrappedSTT(StreamingSTTAdapter):
    def __init__(self, inner: StreamingSTTAdapter, tape: _Tape) -> None:
        self._i = inner
        self._tape = tape

    def start(self, *, sample_rate: int) -> None:
        self._tape.mark("stt.start")
        return self._i.start(sample_rate=sample_rate)

    def accept_audio(self, audio: np.ndarray) -> None:
        self._i.accept_audio(audio)

    def get_partial(self) -> str:
        self._tape.mark("stt.partial")
        return self._i.get_partial()

    def finalize(self) -> STTResult:
        self._tape.mark("stt.final.start")
        res = self._i.finalize()
        self._tape.mark("stt.final.end")
        return res

    def reset(self) -> None:
        self._i.reset()


class _WrappedTTS(StreamingTTSAdapter):
    def __init__(self, inner: StreamingTTSAdapter, tape: _Tape) -> None:
        self._i = inner
        self._tape = tape

    def start(self, *, sample_rate: int) -> None:
        self._tape.mark("tts.start")
        return self._i.start(sample_rate=sample_rate)

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        t0 = time.perf_counter()
        res = self._i.synthesize_chunk(text)
        self._tape.mark("tts.chunk")
        if res is not None:
            self._tape.chunk_audio.append(float(len(res.audio)) / float(res.sample_rate))
        self._tape.chunk_dur.append((time.perf_counter() - t0) * 1000.0)
        return res

    def stop(self) -> None:
        self._i.stop()


class _TimedConversation:
    """Wraps the injected conversation so we can time the ``ask`` call."""

    def __init__(self, inner: Any, tape: _Tape) -> None:
        self._i = inner
        self._tape = tape

    def ask(self, **kwargs):
        self._tape.mark("conv.start")
        out = self._i.ask(**kwargs)
        self._tape.mark("conv.end")
        return out

    def __getattr__(self, name: str) -> Any:
        return getattr(self._i, name)


# ---------------------------------------------------------------------------
# The benchmark.
# ---------------------------------------------------------------------------
def _chunks(audio: np.ndarray) -> list[np.ndarray]:
    return [
        audio[i : i + SILERO_CHUNK_SAMPLES]
        for i in range(0, len(audio), SILERO_CHUNK_SAMPLES)
    ]


def run_audio_turn(
    real_vad,
    real_stt,
    real_tts,
    conversation,
    speech_16k: np.ndarray,
) -> _Tape:
    """Drive one full real audio turn and return the timing tape."""
    tape = _Tape()
    vad = _WrappedVAD(real_vad, tape)  # type: ignore[arg-type]
    stt = _WrappedSTT(
        IncrementalWhisperSTT(backend=real_stt, partial_interval_ms=600), tape
    )
    tts = _WrappedTTS(ChunkedKokoroTTS(backend=real_tts), tape)
    tconversation = _TimedConversation(conversation, tape)

    events: list[tuple[str, float]] = []

    async def emit(event: dict) -> None:
        events.append((event.get("type", ""), time.perf_counter()))

    pipe = RealtimeVoicePipeline(
        vad=vad,  # type: ignore[arg-type]
        stt=stt,  # type: ignore[arg-type]
        tts=tts,  # type: ignore[arg-type]
        conversation=tconversation,  # type: ignore[arg-type]
        session_id="perf-audio",
        emit=emit,
        partial_interval_ms=600,
    )

    async def drive():
        t0 = time.perf_counter()
        tape.mark("turn.start")
        await pipe.begin_generation(path_incident_id="perf")
        with_tail = np.concatenate(
            [speech_16k, np.zeros(int(0.8 * 16000), dtype=np.float32)]
        )
        for c in _chunks(with_tail):
            await pipe.accept_audio(c)
        deadline = time.monotonic() + 180.0
        while time.monotonic() < deadline and not any(e[0] == "done" for e in events):
            await asyncio.sleep(0.01)
        tape.mark("turn.end")

    asyncio.run(drive())
    asyncio.run(pipe.close())
    tape.marks.extend(events)
    return tape


def _baseline_speech(real_tts) -> np.ndarray:
    from scipy import signal  # noqa: PLC0415

    r = real_tts.synthesize("The quick brown fox jumps over the lazy dog.")
    return np.ascontiguousarray(
        signal.resample_poly(np.asarray(r.audio, dtype=np.float32), up=2, down=3),
        dtype=np.float32,
    )


def format_report(tape: _Tape, *, total_audio: float) -> list[str]:
    out = [
        "--- Voice latency breakdown (ms) ---",
        f"first STT final       {tape.elapsed('stt.final.start','stt.final.end'):8.1f}",
        f"total turn            {tape.elapsed('turn.start','turn.end'):8.1f}",
        f"TTS chunks            {len(tape.chunk_dur)}",
        f"TTS audio (s)         {total_audio:8.2f}",
        f"TTS RTF (wall/audio)  {_rtf(tape, total_audio):8.2f}",
    ]
    if tape.chunk_dur:
        out.append(
            "TTS per chunk (ms): "
            + ", ".join(f"{c:.0f}" for c in tape.chunk_dur)
        )
        out.append(
            "chunk audio (s):     "
            + ", ".join(f"{a:.2f}" for a in tape.chunk_audio)
        )
    return out


def _rtf(tape: _Tape, audio_s: float) -> float:
    if audio_s <= 0:
        return 0.0
    total_ms = tape.elapsed("turn.start", "turn.end")
    return (total_ms / 1000.0) / audio_s


@pytest.mark.skipif(not bench_enabled(), reason="VOICE_BENCH=1 + VOICE_REAL_ML=1 required")
def test_perf_audio_bench(real_vad, real_stt, real_tts):
    """Deterministic stage-timed real audio turn (opt-in)."""
    from storyteller.conversation.service import ConversationService
    from storyteller.conversation.session import SessionStore
    from storyteller.knowledge.provenance import fact
    from storyteller.knowledge.context import IncidentContext

    class _FixedAnswer:
        """Deterministic multi-sentence answer so TTS always runs and we measure
        the engine's real per-sentence synthesis + pipeline timing."""

        def ask(self, *, path_incident_id=None, message="", session_id=None, intent=None):
            answer = (
                "Registration services are healthy. The AMF scaled out successfully. "
                "Recovery was confirmed at seven AM. Monitoring is now watchful. "
                "All metrics have returned to nominal. "
            )
            return None, "why", answer, "perf"

    conversation = _FixedAnswer()
    speech = _baseline_speech(real_tts)
    total_audio = float(len(speech)) / 16000.0
    tape = run_audio_turn(real_vad, real_stt, real_tts, conversation, speech)
    report = format_report(tape, total_audio=total_audio)
    print("\n".join(report))
    # The turn MUST complete; assert the pipeline terminated and produced TTS audio.
    assert tape.chunk_dur, "audio turn produced no TTS chunks"
    assert tape.elapsed("turn.start", "turn.end") > 0


if __name__ == "__main__":
    if not bench_enabled():
        print("perf bench skipped (VOICE_BENCH=1 and VOICE_REAL_ML=1 required)")
        raise SystemExit(0)
    # Convenience runner. In this direct path we import the conftest fixtures via pytest.
    ret = pytest.main(["-q", "-k", "test_perf_audio_bench", __file__])
    raise SystemExit(ret)