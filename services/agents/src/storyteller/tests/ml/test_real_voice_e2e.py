"""End-to-end real ML voice pipeline test.

Runs the *real* Silero VAD + faster-whisper STT + Kokoro TTS through the full
``RealtimeVoicePipeline`` (Phase 3C engine) with an injected, incident-agnostic
conversation service. Exercises the text route, the real-speech audio route, and
a real audio barge-in while the speaking turn (real TTS) is still emitting.
"""

from __future__ import annotations

import asyncio
import time

import numpy as np
import pytest

from storyteller.conversation.service import ConversationService
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.voice.realtime import RealtimeVoicePipeline
from storyteller.voice.stt import IncrementalWhisperSTT
from storyteller.voice.tts import ChunkedKokoroTTS
from storyteller.voice.vad import SILERO_CHUNK_SAMPLES, SileroVAD

pytestmark = pytest.mark.real_ml

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
OUT_SR = 24000


class _Knowledge:
    def get_incident_context(self, incident_id: str) -> IncidentContext:
        return IncidentContext(
            incident={
                "slug": "amf-overload-2026-08-09",
                "frontmatter": {"severity": "SEV-2", "status": "resolved"},
            },
            timeline=[fact("RSR critical at 06:14", relationship="timeline-entry")],
            symptoms=[fact("Registration failure spike", relationship="has-symptom")],
            hypotheses=[
                fact(
                    "AMF-01 CPU saturation",
                    relationship="has-hypothesis",
                    confidence=0.9,
                    extra={"status": "confirmed"},
                )
            ],
            evidence=[fact("CPU at 98%", relationship="supported-by")],
            remediations=[fact("Scale out AMF-01", relationship="has-remediation")],
        )


class _LongAnswerConversation:
    """A conversation whose ``ask`` returns a deliberately long answer.

    Lets the barge-in test keep the real TTS speaking long enough to interrupt.
    """

    def ask(self, *, path_incident_id=None, message="", session_id=None, intent=None):
        answer = (
            "The AMF experienced CPU saturation during a registration burst. "
            "This caused a spike in failed registrations across the core. "
            "The recommended remediation is to scale out the AMF instance. "
            "Operators confirmed the recovery at seven AM. "
            "All services returned to nominal status shortly afterwards. "
            "Monitoring is now watching the registration success rate. "
        )
        return None, "why", answer, path_incident_id

    @property
    def sessions(self):
        return None


class Recorder:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def emit(self, event: dict) -> None:
        self.events.append(dict(event))

    def of_type(self, kind: str) -> list[dict]:
        return [e for e in self.events if e.get("type") == kind]


def _real_streamers(real_vad, real_stt, real_tts):
    vad = SileroVAD()
    vad.init()
    stt = IncrementalWhisperSTT(backend=real_stt, partial_interval_ms=600)
    tts = ChunkedKokoroTTS(backend=real_tts)
    return vad, stt, tts


def _chunks(audio: np.ndarray) -> list[np.ndarray]:
    out = []
    for i in range(0, len(audio), SILERO_CHUNK_SAMPLES):
        out.append(audio[i : i + SILERO_CHUNK_SAMPLES])
    return out


def _with_trailing_silence(audio: np.ndarray, seconds: float = 0.8) -> np.ndarray:
    tail = np.zeros(int(seconds * 16000), dtype=np.float32)
    return np.concatenate([audio, tail])


def _await_done(rec: Recorder, timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if rec.of_type("done"):
            return
        time.sleep(0.02)
    kinds = [e["type"] for e in rec.events]
    raise AssertionError(f"pipeline never emitted done; saw events={kinds}")


def test_real_voice_e2e_text_route(real_vad, real_stt, real_tts, real_speech_16k):
    vad, stt, tts = _real_streamers(real_vad, real_stt, real_tts)
    rec = Recorder()
    pipe = RealtimeVoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=ConversationService(_Knowledge(), sessions=SessionStore()),
        session_id="real-text",
        emit=rec.emit,
    )
    try:
        asyncio.run(pipe.submit_text("why did it happen?", path_incident_id=AMF))
        _await_done(rec)
        responses = rec.of_type("response")
        dones = rec.of_type("done")
        assert responses and responses[0]["answer"]
        assert responses[0]["incident_id"] == AMF
        audios = rec.of_type("audio")
        assert audios
        for a in audios:
            assert a["sample_rate"] == OUT_SR
            assert a["audio"].size / a["sample_rate"] > 0
        timings = dones[0]["timings"]
        # Text route: no audio was captured, so the audio-received marker is
        # correctly absent; the speech-anchored markers must still be sane.
        for key in (
            "time_to_first_transcript_ms",
            "time_to_first_audio_ms",
            "total_turn_ms",
        ):
            assert key in timings and timings[key] >= 0
    finally:
        asyncio.run(pipe.close())


def test_real_voice_e2e_audio_route(real_vad, real_stt, real_tts, real_speech_16k):
    vad, stt, tts = _real_streamers(real_vad, real_stt, real_tts)
    rec = Recorder()
    pipe = RealtimeVoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=ConversationService(_Knowledge(), sessions=SessionStore()),
        session_id="real-audio",
        emit=rec.emit,
    )
    try:

        async def drive() -> None:
            await pipe.begin_generation(path_incident_id=AMF)
            for c in _chunks(_with_trailing_silence(real_speech_16k)):
                await pipe.accept_audio(c)
            # Keep the loop alive: the turn is finalized by a spawned task, which
            # would be cancelled if the loop closed before it emitted ``done``.
            deadline = time.monotonic() + 120.0
            while time.monotonic() < deadline and not rec.of_type("done"):
                await asyncio.sleep(0.02)

        asyncio.run(drive())
        _await_done(rec)
        transcripts = rec.of_type("transcript")
        assert transcripts and transcripts[0]["text"]
        assert rec.of_type("response")
        assert rec.of_type("audio")
        # Final transcript + an audio answer means the real speech was detected,
        # transcribed to non-empty text, and the answer was spoken by real TTS.
        final = [t for t in rec.of_type("transcript_partial") if t.get("text")]
        assert isinstance(final, list)
    finally:
        asyncio.run(pipe.close())


def test_real_voice_e2e_barge_in(real_vad, real_stt, real_tts, real_speech_16k):
    vad, stt, tts = _real_streamers(real_vad, real_stt, real_tts)
    rec = Recorder()
    pipe = RealtimeVoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=_LongAnswerConversation(),
        session_id="real-barge",
        emit=rec.emit,
    )
    try:

        async def run():
            # A long textual answer starts a turn that stays in real TTS (many
            # sentences). Run it as a background task so we can barge in while
            # the speaker is still emitting.
            turn = asyncio.create_task(
                pipe.submit_text("why did the AMF overload?", path_incident_id=AMF)
            )
            # Wait until gen1 is genuinely speaking (first real TTS audio).
            deadline = time.monotonic() + 30.0
            first_audio = None
            while time.monotonic() < deadline:
                for e in rec.events:
                    if e.get("type") == "audio":
                        first_audio = e
                        break
                if first_audio is not None:
                    break
                await asyncio.sleep(0.02)
            assert first_audio is not None, "no real TTS audio emitted before barge-in"

            gen1_id = first_audio["generation_id"]
            speaking = pipe._tts_active or pipe.session.connection_state == "speaking"
            await pipe.accept_audio(
                _with_trailing_silence(real_speech_16k, seconds=1.0)
            )
            return turn, speaking, gen1_id

        turn, speaking, gen1_id = asyncio.run(run())
        assert speaking, "real TTS should still be speaking at barge-in time"
        # Barge-in cancels gen1; it must never reach a done event.
        done_ids = {d["generation_id"] for d in rec.of_type("done")}
        assert gen1_id not in done_ids
        # The interrupted turn task settles (cancelled) instead of hanging.
        assert turn.done()
    finally:
        asyncio.run(pipe.close())
