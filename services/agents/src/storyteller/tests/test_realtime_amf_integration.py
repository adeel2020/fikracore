"""Phase 3C integration tests — realtime voice over the real AMF incident.

Drive ``RealtimeVoicePipeline`` (streaming text + audio turns, follow-ups)
against the real gbrain context. Skipped when gbrain is unavailable or locked.

The AMF incident is ONLY a fixture here — the pipeline itself is incident-
agnostic. No ML model weights are loaded: VAD/STT/TTS adapters are fakes (the
Kokoro / faster-whisper / Silero backends are never initialized).
"""

from __future__ import annotations

import asyncio
import time

import numpy as np
import pytest

from storyteller.conversation.service import ConversationService
from storyteller.conversation.session import SessionStore
from storyteller.voice.realtime import RealtimeVoicePipeline
from storyteller.voice.stt import STTResult, StreamingSTTAdapter
from storyteller.voice.tts import TTSResult, StreamingTTSAdapter
from storyteller.voice.vad import VADAdapter, SpeechEvent

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
TTS_SR = 24000
Z512 = np.zeros(512, dtype=np.float32)


class IntegrationStreamingVAD(VADAdapter):
    """Emits start/end on a fixed frame schedule (5 process calls per turn)."""

    def __init__(self, *, start_at: int = 0, end_at: int = 4) -> None:
        self.start_at = start_at
        self.end_at = end_at
        self._calls = 0
        self._ready = False

    def init(self) -> None:
        self._ready = True

    def reset(self) -> None:
        pass

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        idx = self._calls
        self._calls += 1
        if idx == self.start_at:
            return SpeechEvent("start", 0)
        if idx == self.end_at:
            return SpeechEvent("end", 0)
        return None


class IntegrationStreamingSTT(StreamingSTTAdapter):
    def __init__(self, transcript: str = "why did it happen?") -> None:
        self.transcript = transcript

    def start(self, *, sample_rate: int) -> None:
        self._started = True

    def accept_audio(self, audio: np.ndarray) -> None:
        pass

    def get_partial(self) -> str:
        words = self.transcript.split()[:2]
        return " ".join(words)

    def finalize(self) -> STTResult:
        return STTResult(text=self.transcript, language="en", duration=1.0)

    def reset(self) -> None:
        self._started = False


class IntegrationStreamingTTS(StreamingTTSAdapter):
    sample_rate = TTS_SR

    def __init__(self) -> None:
        self.synth_calls = 0
        self._started = False

    def start(self, *, sample_rate: int) -> None:
        self._started = True

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        self.synth_calls += 1
        return TTSResult(
            audio=np.full(TTS_SR // 2, 0.001, dtype=np.float32),
            sample_rate=self.sample_rate,
            text=text,
        )

    def stop(self) -> None:
        self._started = False


class Recorder:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def emit(self, event: dict) -> None:
        self.events.append(dict(event))

    def of_type(self, kind: str) -> list[dict]:
        return [e for e in self.events if e.get("type") == kind]


@pytest.fixture(scope="session")
def knowledge_or_skip(knowledge):
    if knowledge is None:
        pytest.skip("gbrain unavailable")
    return knowledge


@pytest.fixture()
def pipeline(knowledge_or_skip) -> tuple[RealtimeVoicePipeline, Recorder]:
    conversation = ConversationService(
        knowledge_or_skip, sessions=SessionStore()
    )
    rec = Recorder()
    pipe = RealtimeVoicePipeline(
        vad=IntegrationStreamingVAD(),
        stt=IntegrationStreamingSTT(),
        tts=IntegrationStreamingTTS(),
        conversation=conversation,
        session_id="realtime-amf-integration",
        emit=rec.emit,
        partial_interval_ms=0,
    )
    return pipe, rec


async def _await_done(rec: Recorder, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if rec.of_type("done"):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("realtime pipeline never emitted a done event")


def _drive_until_done(
    pipe: RealtimeVoicePipeline, rec: Recorder, frames: int = 5, *, path_incident_id: str | None = None
) -> None:
    async def drive() -> None:
        if path_incident_id is not None:
            await pipe.begin_generation(path_incident_id=path_incident_id)
        for _ in range(frames):
            await pipe.accept_audio(Z512)
        await _await_done(rec)

    asyncio.run(drive())


def test_realtime_text_route_amf(pipeline):
    pipe, rec = pipeline
    asyncio.run(pipe.submit_text("why did it happen?", path_incident_id=AMF))
    responses = rec.of_type("response")
    dones = rec.of_type("done")
    assert responses and responses[0]["incident_id"] == AMF
    assert responses[0]["intent"] == "why"
    assert "confirmed root cause" in responses[0]["answer"].lower()
    assert rec.of_type("audio")
    timings = dones[0]["timings"]
    for key in ("conversation_ms", "reasoning_ms", "tts_ms", "total_ms"):
        assert timings[key] >= 0


def test_realtime_audio_route_amf(pipeline):
    pipe, rec = pipeline
    _drive_until_done(pipe, rec, path_incident_id=AMF)
    transcripts = rec.of_type("transcript")
    responses = rec.of_type("response")
    assert transcripts and transcripts[0]["text"] == "why did it happen?"
    assert responses and responses[0]["incident_id"] == AMF
    assert responses[0]["intent"] == "why"
    timings = rec.of_type("done")[0]["timings"]
    for key in ("stt_ms", "reasoning_ms", "llm_ms", "vad_ms"):
        assert timings[key] >= 0


def test_realtime_session_followup_amf(pipeline):
    pipe, rec = pipeline
    asyncio.run(pipe.submit_text("what happened?", path_incident_id=AMF))
    first = rec.of_type("response")[-1]
    assert first["incident_id"] == AMF
    # No incident in the path -> session active incident (AMF) reused.
    asyncio.run(pipe.submit_text("why did it happen?"))
    second = rec.of_type("response")[-1]
    assert second["incident_id"] == AMF
    assert second["intent"] == "why"


def test_realtime_amf_emits_audio_binary_and_timings(pipeline):
    pipe, rec = pipeline
    asyncio.run(pipe.submit_text("what was the impact?", path_incident_id=AMF))
    audios = rec.of_type("audio")
    assert audios
    for a in audios:
        assert a["sample_rate"] == TTS_SR
        assert a["generation_id"] == rec.of_type("done")[0]["generation_id"]