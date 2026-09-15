"""Phase 3B tests — local voice pipeline.

Tests use fake VAD/STT/TTS adapters (no ML model downloads, no gbrain).
The pipeline is incident-agnostic: it exercises generic incidents in addition
to the AMF fixture, and never hard-codes incident ids.

The heavy backends (Silero / faster-whisper / Kokoro) are imported lazily
inside ``init()``, so importing this module and the ``storyteller.voice``
package does not require PyTorch or any model weights.
"""

from __future__ import annotations

import numpy as np
import pytest

from storyteller.conversation.service import ConversationService
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.voice.pipeline import VoicePipeline, VoiceResult
from storyteller.voice.session import VoiceSession
from storyteller.voice.stt import STTAdapter, STTError, STTResult, create_stt
from storyteller.voice.tts import TTSAdapter, TTSError, TTSResult, create_tts
from storyteller.voice.vad import VADAdapter, VADError, SpeechEvent, create_vad

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
INC_A = "mobile-core/incidents/incident-a"
INC_B = "mobile-core/incidents/incident-b"

SR = 16000
TTS_SR = 24000


class FakeKnowledge:
    """Canned contexts keyed by incident id (generic incidents, not AMF-only)."""

    def __init__(self) -> None:
        self.contexts = {
            AMF: _amf_context(),
            INC_A: _generic_context(INC_A, "SEV-2", "resolved"),
            INC_B: _generic_context(INC_B, "SEV-3", "open"),
        }

    def get_incident_context(self, incident_id: str) -> IncidentContext:
        return self.contexts.get(incident_id, IncidentContext())


def _amf_context() -> IncidentContext:
    return IncidentContext(
        incident={"slug": AMF, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
        timeline=[fact("2026-08-09T06:14:00Z RSR critical", relationship="timeline-entry")],
        services=[fact("UE Registration Service", relationship="affects")],
        network_functions=[fact("AMF-01", relationship="involves")],
        kpis=[fact("Registration Success Rate (RSR)", relationship="measures")],
        kpi_events=[fact(
            "RSR critical breach at 06:14", relationship="detected-by",
            extra={"value": 94.7, "event_type": "alarm", "threshold": "critical"},
        )],
        symptoms=[fact("Spike in UE registration failures", relationship="has-symptom")],
        hypotheses=[fact(
            "AMF-01 CPU saturation from registration signaling burst",
            relationship="has-hypothesis",
            confidence=0.92,
            extra={"status": "confirmed",
                   "explains": ["mobile-core/symptoms/registration-failure-spike"]},
        )],
        evidence=[fact(
            "AMF-01 CPU utilization pegged at 98%", relationship="supported-by",
            extra={"hypothesis_slug": "mobile-core/hypotheses/amf-cpu-saturation"},
        )],
        remediations=[fact("Scale out AMF-01", relationship="has-remediation")],
        recovery_events=[fact("RSR recovery at 07:05", relationship="verified-by")],
    )


def _generic_context(incident_id: str, severity: str, status: str) -> IncidentContext:
    return IncidentContext(
        incident={"slug": incident_id, "frontmatter": {"severity": severity, "status": status}},
        timeline=[fact("symptom observed", relationship="timeline-entry")],
        services=[fact("Generic Service", relationship="affects")],
        network_functions=[fact("Generic NF", relationship="involves")],
        symptoms=[fact("Generic symptom", relationship="has-symptom")],
        hypotheses=[fact(
            "Generic root cause hypothesis", relationship="has-hypothesis",
            confidence=0.8, extra={"status": "confirmed"},
        )],
        evidence=[fact("Generic evidence", relationship="supported-by")],
        remediations=[fact("Generic remediation", relationship="has-remediation")],
        recovery_events=[fact("Recovery observed", relationship="verified-by")],
    )


def make_conversation() -> ConversationService:
    return ConversationService(FakeKnowledge(), sessions=SessionStore())


# ---------------------------------------------------------------------------
# Fakes.
# ---------------------------------------------------------------------------
class FakeVAD(VADAdapter):
    def __init__(self, *, ranges: list[tuple[int, int]] | None = None,
                 fail_init: bool = False, fail_process: bool = False) -> None:
        self.ranges = ranges or []
        self.fail_init = fail_init
        self.fail_process = fail_process
        self.init_calls = 0
        self.reset_calls = 0
        self.process_calls = 0
        self._initialized = False

    def init(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.init_calls += 1
        if self.fail_init:
            raise VADError("fake VAD init failure")

    def reset(self) -> None:
        self.reset_calls += 1

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        self.process_calls += 1
        if self.fail_process:
            raise VADError("fake VAD process failure")
        return None

    def speech_ranges(self, audio: np.ndarray, sample_rate: int) -> list[tuple[int, int]]:
        return list(self.ranges)


class FakeSTT(STTAdapter):
    def __init__(self, *, transcript: str = "what happened?",
                 fail_init: bool = False, fail_transcribe: bool = False) -> None:
        self.transcript = transcript
        self.fail_init = fail_init
        self.fail_transcribe = fail_transcribe
        self.init_calls = 0
        self.last_audio = None
        self.last_sample_rate = None
        self._initialized = False

    def init(self) -> None:
        if self._initialized:
            return
        self.init_calls += 1
        self._initialized = True
        if self.fail_init:
            raise STTError("fake STT init failure")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        if not self._initialized:
            raise STTError("fake STT not initialized")
        if self.fail_transcribe:
            raise STTError("fake STT transcribe failure")
        self.last_audio = audio
        self.last_sample_rate = sample_rate
        return STTResult(text=self.transcript, language="en", duration=1.0)


class FakeTTS(TTSAdapter):
    sample_rate = TTS_SR

    def __init__(self, *, fail_init: bool = False, fail_synth: bool = False,
                 silence: bool = False) -> None:
        self.fail_init = fail_init
        self.fail_synth = fail_synth
        self.silence = silence
        self.init_calls = 0
        self.last_text = None
        self._initialized = False

    def init(self) -> None:
        if self._initialized:
            return
        self.init_calls += 1
        self._initialized = True
        if self.fail_init:
            raise TTSError("fake TTS init failure")

    def synthesize(self, text: str) -> TTSResult:
        if not self._initialized:
            raise TTSError("fake TTS not initialized")
        if self.fail_synth:
            raise TTSError("fake TTS synth failure")
        self.last_text = text
        audio = np.zeros(2400, dtype=np.float32) if self.silence else np.random.rand(2400).astype(np.float32)
        return TTSResult(audio=audio, sample_rate=self.sample_rate, text=text)


@pytest.fixture()
def pipeline_factory():
    def build(*, vad: VADAdapter | None = None, stt: STTAdapter | None = None,
              tts: TTSAdapter | None = None,
              conversation: ConversationService | None = None) -> VoicePipeline:
        return VoicePipeline(
            vad=vad or FakeVAD(ranges=[(0, SR)]),
            stt=stt or FakeSTT(),
            tts=tts or FakeTTS(),
            conversation=conversation or make_conversation(),
            session_id="voice-test",
        )
    return build


# ---------------------------------------------------------------------------
# VAD adapter tests.
# ---------------------------------------------------------------------------
class TestVADAdapter:
    def test_speech_ranges_default_merges_events(self):
        class EventVAD(VADAdapter):
            def __init__(self):
                self.queue = [SpeechEvent("start", 1600), SpeechEvent("end", 3200)]
                self.reset_calls = 0

            def init(self):
                pass

            def reset(self):
                self.reset_calls += 1

            def process(self, chunk):
                return self.queue.pop(0) if self.queue else None

        audio = np.zeros(4800, dtype=np.float32)
        vad = EventVAD()
        ranges = vad.speech_ranges(audio, SR)
        assert ranges == [(1600, 3200)]
        # reset is called before and after feeding.
        assert vad.reset_calls >= 2

    def test_speech_ranges_rejects_wrong_sample_rate(self):
        class DefaultVAD(VADAdapter):
            def init(self):
                pass

            def reset(self):
                pass

            def process(self, chunk):
                return None

        vad = DefaultVAD()
        with pytest.raises(VADError):
            vad.speech_ranges(np.zeros(100, dtype=np.float32), 8000)

    def test_create_vad_returns_silero_adapter(self):
        assert isinstance(create_vad(), VADAdapter)
        assert create_vad().sample_rate == 16000


# ---------------------------------------------------------------------------
# STT adapter tests.
# ---------------------------------------------------------------------------
class TestSTTAdapter:
    def test_fake_adapter_round_trip(self):
        stt = FakeSTT(transcript="hello there")
        stt.init()
        result = stt.transcribe(np.zeros(100, dtype=np.float32), SR)
        assert result.text == "hello there"
        assert result.language == "en"

    def test_transcribe_before_init_raises(self, pipeline_factory):
        stt = FakeSTT()
        with pytest.raises(STTError):
            stt.transcribe(np.zeros(100, dtype=np.float32), SR)

    def test_create_stt_returns_adapter(self):
        assert isinstance(create_stt(), STTAdapter)


# ---------------------------------------------------------------------------
# TTS adapter tests.
# ---------------------------------------------------------------------------
class TestTTSAdapter:
    def test_fake_adapter_synthesizes_audio(self):
        tts = FakeTTS()
        tts.init()
        result = tts.synthesize("hello")
        assert isinstance(result.audio, np.ndarray)
        assert result.sample_rate == TTS_SR

    def test_synthesize_before_init_raises(self):
        tts = FakeTTS()
        with pytest.raises(TTSError):
            tts.synthesize("hello")

    def test_create_tts_returns_adapter(self):
        assert isinstance(create_tts(), TTSAdapter)


# ---------------------------------------------------------------------------
# VoiceSession tests.
# ---------------------------------------------------------------------------
class TestVoiceSession:
    def test_active_incident_shared_with_conversation(self):
        conversation = make_conversation()
        session = VoiceSession(conversation=conversation, session_id="sess-1")
        assert session.active_incident_id is None
        conversation.sessions.set_active_incident("sess-1", INC_A)
        assert session.active_incident_id == INC_A

    def test_remember_records_last_turn(self):
        conversation = make_conversation()
        session = VoiceSession(conversation=conversation, session_id="sess-1")
        session.remember(transcript="what happened?", answer="a", intent="story", incident_id=INC_A)
        assert session.last_transcript == "what happened?"
        assert session.last_answer == "a"
        assert session.last_intent == "story"
        assert session.last_incident_id == INC_A


# ---------------------------------------------------------------------------
# VoicePipeline tests.
# ---------------------------------------------------------------------------
class TestVoicePipelineText:
    def test_text_route_returns_answer_and_audio(self, pipeline_factory):
        pipeline = pipeline_factory()
        result = pipeline.process_text("what happened?", path_incident_id=INC_A)
        assert isinstance(result, VoiceResult)
        assert result.incident_id == INC_A
        assert result.answer
        assert result.intent == "story"
        assert result.audio is not None
        assert result.sample_rate == TTS_SR
        assert result.synthesized
        assert result.error is None
        # Latency instrumentation present.
        assert result.timings["conversation_ms"] >= 0
        assert result.timings["tts_ms"] >= 0
        assert result.timings["vad_ms"] == 0
        assert result.timings["stt_ms"] == 0
        assert result.timings["total_ms"] > 0

    def test_text_route_followup_uses_session(self, pipeline_factory):
        pipeline = pipeline_factory()
        pipeline.process_text("what happened?", path_incident_id=INC_A)
        # No incident in path -> session active incident must be reused.
        result = pipeline.process_text("why did it happen?")
        assert result.incident_id == INC_A
        assert result.intent == "why"

    def test_text_route_no_context_errors_gracefully(self, pipeline_factory):
        pipeline = pipeline_factory()
        result = pipeline.process_text("why did it happen?")
        assert result.error is not None
        assert "conversation error" in result.error
        assert result.audio is None

    def test_text_route_generic_incidents(self, pipeline_factory):
        pipeline = pipeline_factory()
        for incident in (INC_A, INC_B):
            result = pipeline.process_text("what is the status?", path_incident_id=incident)
            assert result.incident_id == incident
            assert result.answer
            assert result.error is None


class TestVoicePipelineAudio:
    def test_audio_route_runs_full_chain(self, pipeline_factory):
        audio = np.random.rand(SR).astype(np.float32)
        pipeline = pipeline_factory()
        result = pipeline.process_audio(audio, sample_rate=SR, path_incident_id=INC_B)
        assert result.transcript == "what happened?"
        assert result.incident_id == INC_B
        assert result.audio is not None
        assert result.synthesized
        assert result.error is None
        # All four stages instrumented.
        assert result.timings["vad_ms"] >= 0
        assert result.timings["stt_ms"] >= 0
        assert result.timings["conversation_ms"] >= 0
        assert result.timings["tts_ms"] >= 0
        assert result.timings["total_ms"] > 0
        assert result.timings["total_ms"] == pytest.approx(
            result.timings["vad_ms"] + result.timings["stt_ms"]
            + result.timings["conversation_ms"] + result.timings["tts_ms"]
        )

    def test_audio_route_no_speech(self, pipeline_factory):
        pipeline = pipeline_factory(vad=FakeVAD(ranges=[]))
        result = pipeline.process_audio(np.zeros(SR, dtype=np.float32), sample_rate=SR)
        assert result.error == "no speech detected"
        assert result.transcript == ""
        assert result.audio is None

    def test_audio_route_empty_transcript(self, pipeline_factory):
        pipeline = pipeline_factory(stt=FakeSTT(transcript="   "))
        result = pipeline.process_audio(np.random.rand(SR).astype(np.float32), sample_rate=SR)
        assert result.error == "empty transcript"
        assert result.answer == "I could not understand the audio."

    def test_audio_route_bad_sample_rate(self, pipeline_factory):
        pipeline = pipeline_factory()
        result = pipeline.process_audio(np.zeros(8000, dtype=np.float32), sample_rate=8000)
        assert "unsupported sample rate" in result.error

    def test_audio_route_vad_init_failure(self, pipeline_factory):
        pipeline = pipeline_factory(vad=FakeVAD(fail_init=True))
        result = pipeline.process_audio(np.zeros(SR, dtype=np.float32), sample_rate=SR)
        assert "VAD error" in result.error
        assert result.audio is None

    def test_audio_route_stt_failure(self, pipeline_factory):
        pipeline = pipeline_factory(stt=FakeSTT(fail_transcribe=True))
        result = pipeline.process_audio(np.random.rand(SR).astype(np.float32), sample_rate=SR)
        assert "STT error" in result.error

    def test_audio_route_tts_failure_still_returns_answer(self, pipeline_factory):
        pipeline = pipeline_factory(tts=FakeTTS(fail_synth=True))
        result = pipeline.process_audio(np.random.rand(SR).astype(np.float32),
                                        sample_rate=SR, path_incident_id=INC_A)
        assert "TTS error" in result.error
        assert result.answer  # deterministic answer still present
        assert result.audio is None


class TestVoicePipelineInitIsLazy:
    def test_construction_does_not_init_backends(self, pipeline_factory):
        vad, stt, tts = FakeVAD(), FakeSTT(), FakeTTS()
        VoicePipeline(
            vad=vad, stt=stt, tts=tts, conversation=make_conversation()
        )
        assert vad.init_calls == 0
        assert stt.init_calls == 0
        assert tts.init_calls == 0

    def test_init_called_once_on_first_use(self, pipeline_factory):
        vad = FakeVAD(ranges=[(0, SR)])
        stt = FakeSTT()
        tts = FakeTTS()
        pipeline = VoicePipeline(
            vad=vad, stt=stt, tts=tts, conversation=make_conversation()
        )
        pipeline.process_audio(np.random.rand(SR).astype(np.float32), sample_rate=SR,
                               path_incident_id=INC_A)
        assert vad.init_calls == 1
        assert stt.init_calls == 1
        assert tts.init_calls == 1
        pipeline.process_audio(np.random.rand(SR).astype(np.float32), sample_rate=SR,
                               path_incident_id=INC_A)
        assert vad.init_calls == 1
        assert stt.init_calls == 1
        assert tts.init_calls == 1
