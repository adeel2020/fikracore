"""Phase 3B integration tests — voice text route over the real AMF incident.

These exercise the end-to-end voice pipeline (text → ConversationService →
TTS) against the real gbrain context and are skipped when gbrain is
unavailable or locked.

The AMF incident is ONLY a fixture here — the pipeline itself is incident-
agnostic. No ML model weights are loaded: the VAD/STT/TTS adapters are fakes.
The Kokoro/faster-whisper/Silero backends are never initialized in this suite.
"""

from __future__ import annotations

import numpy as np
import pytest

from storyteller.conversation.service import ConversationService
from storyteller.voice.pipeline import VoicePipeline
from storyteller.voice.stt import STTAdapter, STTResult
from storyteller.voice.tts import TTSAdapter, TTSResult
from storyteller.voice.vad import VADAdapter

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
TTS_SR = 24000


class IntegrationVAD(VADAdapter):
    def init(self) -> None:
        pass

    def reset(self) -> None:
        pass

    def process(self, chunk: np.ndarray):
        return None

    def speech_ranges(self, audio: np.ndarray, sample_rate: int) -> list[tuple[int, int]]:
        return [(0, len(audio))]


class IntegrationSTT(STTAdapter):
    def __init__(self, transcript: str) -> None:
        self.transcript = transcript

    def init(self) -> None:
        pass

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        return STTResult(text=self.transcript, language="en", duration=1.0)


class IntegrationTTS(TTSAdapter):
    sample_rate = TTS_SR

    def init(self) -> None:
        pass

    def synthesize(self, text: str) -> TTSResult:
        audio = np.full(TTS_SR // 2, 0.001, dtype=np.float32)
        return TTSResult(audio=audio, sample_rate=self.sample_rate, text=text)


@pytest.fixture(scope="session")
def knowledge_or_skip(knowledge):
    if knowledge is None:
        pytest.skip("gbrain unavailable")
    return knowledge


@pytest.fixture()
def pipeline(knowledge_or_skip) -> VoicePipeline:
    conversation = ConversationService(knowledge_or_skip)
    return VoicePipeline(
        vad=IntegrationVAD(),
        stt=IntegrationSTT(transcript="why did it happen?"),
        tts=IntegrationTTS(),
        conversation=conversation,
        session_id="voice-amf-integration",
    )


def test_voice_text_route_amf(pipeline):
    result = pipeline.process_text("why did it happen?", path_incident_id=AMF)
    assert result.error is None
    assert result.incident_id == AMF
    assert result.intent == "why"
    assert "confirmed root cause" in result.answer.lower()
    assert result.audio is not None
    assert result.sample_rate == TTS_SR
    assert result.synthesized
    assert result.timings["conversation_ms"] >= 0
    assert result.timings["tts_ms"] >= 0


def test_voice_audio_route_amf(pipeline):
    audio = np.zeros(16000, dtype=np.float32)
    result = pipeline.process_audio(audio, sample_rate=16000, path_incident_id=AMF)
    assert result.error is None
    assert result.incident_id == AMF
    assert result.transcript == "why did it happen?"
    assert result.audio is not None
    # All four stages instrumented.
    assert result.timings["vad_ms"] >= 0
    assert result.timings["stt_ms"] >= 0
    assert result.timings["conversation_ms"] >= 0
    assert result.timings["tts_ms"] >= 0


def test_voice_session_followup_amf(pipeline):
    first = pipeline.process_text("what happened?", path_incident_id=AMF)
    assert first.incident_id == AMF
    # No incident in the path -> session active incident reused.
    follow = pipeline.process_text("why did it happen?")
    assert follow.incident_id == AMF
    assert follow.intent == "why"
