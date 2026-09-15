"""Phase 3C tests — realtime voice pipeline internals.

Covers the WebSocket protocol helpers, cooperative cancellation, the streaming
STT/TTS adapters, and the ``RealtimeVoicePipeline`` (text and audio turns,
partials, barge-in, stale-generation filtering). All adapters are fakes — no ML
models or gbrain. Generic incidents (``incident-A``/``incident-B``) are used
alongside the AMF fixture; the pipeline itself is incident-agnostic.
"""

from __future__ import annotations

import asyncio
import threading
import time

import numpy as np
import pytest

from storyteller.conversation.service import ConversationService
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.voice.cancellation import (
    Cancelled,
    CancellationToken,
    GenerationCounter,
)
from storyteller.voice.protocol import (
    ErrorCode,
    MessageType,
    float32_to_pcm16,
    pcm16_to_float32,
    encode_message,
    decode_message,
    validate_session_id,
    validate_audio_payload_size,
    encode_audio_event,
    decode_audio_event,
    MAX_AUDIO_CHUNK_BYTES,
)
from storyteller.voice.realtime import RealtimeVoicePipeline
from storyteller.voice.stt import (
    FallbackStreamingSTT,
    STTAdapter,
    STTError,
    STTResult,
    StreamingSTTAdapter,
    IncrementalWhisperSTT,
)
from storyteller.voice.tts import (
    FallbackStreamingTTS,
    TTSAdapter,
    TTSResult,
    StreamingTTSAdapter,
    ChunkedKokoroTTS,
    split_sentences,
    TTSError,
)
from storyteller.voice.vad import VADAdapter, SpeechEvent

AMF = "mobile-core/incidents/amf-overload-2026-08-09"
INC_A = "mobile-core/incidents/incident-a"
INC_B = "mobile-core/incidents/incident-b"
SR = 16000
Z512 = np.zeros(512, dtype=np.float32)


# ---------------------------------------------------------------------------
# Shared fixtures (mirror test_voice.py).
# ---------------------------------------------------------------------------
class FakeKnowledge:
    def __init__(self) -> None:
        self.contexts = {AMF: _ctx(AMF), INC_A: _ctx(INC_A), INC_B: _ctx(INC_B)}

    def get_incident_context(self, incident_id: str) -> IncidentContext:
        return self.contexts.get(incident_id, IncidentContext())


def _ctx(incident_id: str) -> IncidentContext:
    return IncidentContext(
        incident={"slug": incident_id, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
        timeline=[fact("symptom observed", relationship="timeline-entry")],
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


class FakeStreamingVAD(VADAdapter):
    """Emits start/end on a fixed frame schedule (frame indices are 0-based)."""

    def __init__(self, *, start_at: int = 0, end_at: int = 4) -> None:
        self.start_at = start_at
        self.end_at = end_at
        self.process_calls = 0
        self.reset_calls = 0
        self.init_calls = 0
        self._ready = False

    def init(self) -> None:
        if not self._ready:
            self._ready = True
            self.init_calls += 1

    def reset(self) -> None:
        self.reset_calls += 1

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        idx = self.process_calls
        self.process_calls += 1
        if idx == self.start_at:
            return SpeechEvent("start", 0)
        if idx == self.end_at:
            return SpeechEvent("end", 0)
        return None


class FakeStreamingSTT(StreamingSTTAdapter):
    def __init__(
        self,
        transcript: str = "why did it happen?",
        partial: str = "why did",
        *,
        fail_finalize: bool = False,
    ) -> None:
        self.transcript = transcript
        self.partial = partial
        self.fail_finalize = fail_finalize
        self.started = False
        self.buffer: list[np.ndarray] = []
        self.accept_calls = 0
        self.partial_calls = 0
        self.finalize_calls = 0
        self.reset_calls = 0

    def start(self, *, sample_rate: int) -> None:
        self.started = True
        self.buffer = []

    def accept_audio(self, audio: np.ndarray) -> None:
        if not self.started:
            raise STTError("accept_audio called before start()")
        self.accept_calls += 1
        self.buffer.append(np.asarray(audio, dtype=np.float32))

    def get_partial(self) -> str:
        self.partial_calls += 1
        return self.partial

    def finalize(self) -> STTResult:
        self.finalize_calls += 1
        if self.fail_finalize:
            raise STTError("fake STT finalize failure")
        return STTResult(text=self.transcript, language="en", duration=1.0)

    def reset(self) -> None:
        self.reset_calls += 1
        self.started = False
        self.buffer = []


class FakeOneShotSTT(STTAdapter):
    def __init__(self, transcript: str = "primary transcript", *, fail: bool = False) -> None:
        self.transcript = transcript
        self.fail = fail
        self.init_calls = 0
        self.transcribe_calls = 0

    def init(self) -> None:
        self.init_calls += 1
        if self.fail:
            raise STTError("fake one-shot STT failure")

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        self.transcribe_calls += 1
        if self.fail:
            raise STTError("fake one-shot STT failure")
        return STTResult(text=self.transcript, language="en", duration=len(audio) / sample_rate)


class FakeStreamingTTS(StreamingTTSAdapter):
    sample_rate = 24000

    def __init__(self, *, fail: bool = False, silence: bool = False) -> None:
        self.fail = fail
        self.silence = silence
        self.start_calls = 0
        self.stop_calls = 0
        self.synth_calls = 0
        self.last_text = None
        self._started = False

    def start(self, *, sample_rate: int) -> None:
        self.start_calls += 1
        self._started = True

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        self.synth_calls += 1
        if not self._started:
            raise TTSError("fake TTS not started")
        self.last_text = text
        if self.fail:
            raise TTSError("fake TTS failure")
        audio = np.zeros(480, dtype=np.float32) if self.silence else np.full(480, 0.01, dtype=np.float32)
        return TTSResult(audio=audio, sample_rate=self.sample_rate, text=text)

    def stop(self) -> None:
        self.stop_calls += 1
        self._started = False


class FakeOneShotTTS(TTSAdapter):
    sample_rate = 24000

    def __init__(self, label: str, *, fail: bool = False) -> None:
        self.label = label
        self.fail = fail
        self.init_calls = 0
        self.synth_calls = 0
        self.texts: list[str] = []

    def init(self) -> None:
        self.init_calls += 1
        if self.fail:
            raise TTSError(f"{self.label} failed")

    def synthesize(self, text: str) -> TTSResult:
        self.synth_calls += 1
        self.texts.append(text)
        if self.fail:
            raise TTSError(f"{self.label} failed")
        level = 0.02 if self.label == "primary" else 0.01
        audio = np.full(160, level, dtype=np.float32)
        return TTSResult(audio=audio, sample_rate=self.sample_rate, text=f"{self.label}:{text}")


class Recorder:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def emit(self, event: dict) -> None:
        self.events.append(dict(event))

    def of_type(self, kind: str) -> list[dict]:
        return [e for e in self.events if e.get("type") == kind]


def build_pipeline(*, stt=None, tts=None, vad=None, conversation=None, **kw) -> tuple:
    rec = Recorder()
    pipe = RealtimeVoicePipeline(
        vad=vad or FakeStreamingVAD(),
        stt=stt or FakeStreamingSTT(),
        tts=tts or FakeStreamingTTS(),
        conversation=conversation or make_conversation(),
        emit=rec.emit,
        partial_interval_ms=0,
        **kw,
    )
    return pipe, rec


def test_mark_voice_preserves_presentation_and_curated_speech():
    from assistant.mark.response import MarkResponse

    class MarkConversation:
        def ask(self, **kwargs):
            return None, "mark_general", MarkResponse("# Full technical answer", spoken_reply="Service is recovering.", presentation={
                "narrative": {"incident_id": "incident-a"},
                "visual_explanation": {"widgets": [{"id": "impact"}]},
            }), "incident-a"

    async def run():
        pipe, rec = build_pipeline(conversation=MarkConversation())
        await pipe.submit_text("Tell the incident story")
        response = rec.of_type("response")[0]
        assert response["answer"] == "# Full technical answer"
        assert response["spoken_answer"] == "Service is recovering."
        assert response["visual_explanation"]["widgets"][0]["id"] == "impact"
        await pipe.interrupt()
        assert rec.of_type("interrupted")[-1]["generation_id"] == response["generation_id"]

    asyncio.run(run())


async def _await_done(rec: Recorder, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if rec.of_type("done"):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("pipeline never emitted a done event")


async def _drive_until_done(pipe, rec, *, frames: int = 5) -> None:
    for _ in range(frames):
        await pipe.accept_audio(Z512)
    await _await_done(rec)


async def _await_true(pred, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pred():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met in time")


# ---------------------------------------------------------------------------
# Protocol tests.
# ---------------------------------------------------------------------------
class TestProtocol:
    def test_pcm_round_trip(self):
        audio = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        data = float32_to_pcm16(audio)
        assert isinstance(data, bytes)
        back = pcm16_to_float32(data)
        np.testing.assert_allclose(back, audio, atol=2.0 / 32767.0)

    def test_audio_event_base64_round_trip(self):
        audio = np.full(64, 0.25, dtype=np.float32)
        env = encode_audio_event(generation_id=7, audio=audio)
        assert env["type"] == MessageType.AUDIO.value
        assert env["generation_id"] == 7
        np.testing.assert_allclose(decode_audio_event(env), audio, atol=2.0 / 32767.0)

    def test_control_message_round_trip(self):
        raw = encode_message(MessageType.TEXT.value, text="hello", path_incident_id=INC_A)
        env = decode_message(raw)
        assert env["type"] == MessageType.TEXT.value
        assert env["text"] == "hello"
        assert env["path_incident_id"] == INC_A

    def test_decode_message_rejects_bad_json(self):
        with pytest.raises(ValueError):
            decode_message("{not json")
        with pytest.raises(ValueError):
            decode_message("[1, 2]")
        with pytest.raises(ValueError):
            decode_message('{"no_type": true}')

    def test_audio_size_validation(self):
        validate_audio_payload_size(b"\x00\x00" * 8)
        with pytest.raises(ValueError):
            validate_audio_payload_size(b"")
        with pytest.raises(ValueError):
            validate_audio_payload_size(b"\x00" * (MAX_AUDIO_CHUNK_BYTES + 1))

    def test_session_id_validation(self):
        assert validate_session_id("voice-test") is None
        assert validate_session_id("incident-a_1") is None
        assert validate_session_id("") is not None
        assert validate_session_id("bad id!") is not None
        assert validate_session_id("x" * 129) is not None

    def test_error_codes(self):
        assert ErrorCode.CANCELLED.value == "cancelled"
        assert ErrorCode.CONVERSATION_ERROR.value == "conversation_error"


# ---------------------------------------------------------------------------
# Cancellation tests.
# ---------------------------------------------------------------------------
class TestCancellation:
    def test_token_cancel_and_check(self):
        tok = CancellationToken()
        assert not tok.cancelled
        tok.cancel()
        assert tok.cancelled
        with pytest.raises(Cancelled):
            tok.check()
        tok.cancel()  # idempotent
        assert tok.cancelled

    def test_generation_counter_monotonic(self):
        counter = GenerationCounter()
        g1 = counter.next()
        g2 = counter.next()
        assert g1.id < g2.id
        assert g1.token is not g2.token
        assert not g1.cancelled
        g1.cancel()
        assert g1.cancelled
        assert not g2.cancelled


# ---------------------------------------------------------------------------
# Streaming STT/TTS adapter tests.
# ---------------------------------------------------------------------------
class Backend:
    """A fake single-shot STTAdapter used to back IncrementalWhisperSTT."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.init_calls = 0
        self.calls: list[int] = []

    def init(self) -> None:
        self.init_calls += 1

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        self.calls.append(len(audio))
        return STTResult(text=self.text, language="en", duration=len(audio) / sample_rate)


class TestIncrementalWhisperSTT:
    def test_buffers_and_finalizes(self):
        backend = Backend("hello world")
        stt = IncrementalWhisperSTT(
            backend=backend, partial_interval_ms=0, min_partial_seconds=0.0
        )
        stt.start(sample_rate=SR)
        assert backend.init_calls == 1
        stt.accept_audio(np.zeros(3200, dtype=np.float32))
        partial = stt.get_partial()
        assert partial == "hello world"
        result = stt.finalize()
        assert result.text == "hello world"
        # finalize resets the utterance.
        with pytest.raises(STTError):
            stt.finalize()

    def test_partial_throttled_by_interval(self):
        backend = Backend("throttled")
        stt = IncrementalWhisperSTT(
            backend=backend, partial_interval_ms=10000, min_partial_seconds=0.0
        )
        stt.start(sample_rate=SR)
        stt.accept_audio(np.zeros(3200, dtype=np.float32))
        # The interval is 10 s -> 160000 new samples required before the next
        # transcription, so no partial is emitted yet.
        assert stt.get_partial() == ""
        stt.finalize()

    def test_reset_drops_buffer(self):
        backend = Backend("reset me")
        stt = IncrementalWhisperSTT(backend=backend)
        stt.start(sample_rate=SR)
        stt.accept_audio(np.zeros(3200, dtype=np.float32))
        stt.reset()
        assert not stt._started
        # finalize() after reset requires a fresh start().
        with pytest.raises(STTError):
            stt.finalize()


class FakeTTSPipeline:
    """A fake single-shot TTSAdapter backing ChunkedKokoroTTS."""

    sample_rate = 24000

    def __init__(self) -> None:
        self.init_calls = 0
        self.calls: list[str] = []

    def init(self) -> None:
        self.init_calls += 1

    def synthesize(self, text: str) -> TTSResult:
        self.calls.append(text)
        return TTSResult(audio=np.full(480, 0.01, dtype=np.float32), sample_rate=24000, text=text)


class TestChunkedKokoroTTS:
    def test_synthesize_chunk_delegates(self):
        backend = FakeTTSPipeline()
        tts = ChunkedKokoroTTS(backend=backend)
        tts.start(sample_rate=24000)
        assert backend.init_calls == 1
        result = tts.synthesize_chunk("hello there")
        assert result is not None
        assert backend.calls == ["hello there"]
        assert result.sample_rate == 24000
        tts.stop()

    def test_empty_chunk_returns_none(self):
        tts = ChunkedKokoroTTS(backend=FakeTTSPipeline())
        tts.start(sample_rate=24000)
        assert tts.synthesize_chunk("   ") is None
        tts.stop()

    def test_before_start_raises(self):
        tts = ChunkedKokoroTTS(backend=FakeTTSPipeline())
        from storyteller.voice.tts import TTSError

        with pytest.raises(TTSError):
            tts.synthesize_chunk("x")


class TestProviderFallbacks:
    def test_streaming_stt_uses_primary_final_transcript(self):
        primary = FakeOneShotSTT("elevenlabs transcript")
        fallback = FakeStreamingSTT(transcript="local transcript", partial="local partial")
        stt = FallbackStreamingSTT(primary=primary, fallback=fallback)

        stt.start(sample_rate=SR)
        stt.accept_audio(np.ones(320, dtype=np.float32))

        assert stt.get_partial() == ""
        result = stt.finalize()

        assert result.text == "elevenlabs transcript"
        assert primary.transcribe_calls == 1
        assert fallback.started is False
        assert fallback.finalize_calls == 0

    def test_streaming_stt_can_enable_local_partials_explicitly(self):
        primary = FakeOneShotSTT("elevenlabs transcript")
        fallback = FakeStreamingSTT(transcript="local transcript", partial="local partial")
        stt = FallbackStreamingSTT(
            primary=primary,
            fallback=fallback,
            enable_fallback_partials=True,
        )

        stt.start(sample_rate=SR)
        stt.accept_audio(np.ones(320, dtype=np.float32))

        assert stt.get_partial() == "local partial"

    def test_streaming_stt_retries_same_utterance_with_fallback(self):
        primary = FakeOneShotSTT(fail=True)
        fallback = FakeStreamingSTT(transcript="local transcript")
        stt = FallbackStreamingSTT(primary=primary, fallback=fallback)

        stt.start(sample_rate=SR)
        stt.accept_audio(np.ones(320, dtype=np.float32))
        result = stt.finalize()

        assert result.text == "local transcript"
        assert stt.active_provider == "fallback"
        assert fallback.finalize_calls == 1
        assert fallback.accept_calls == 1

    def test_streaming_tts_retries_full_response_with_fallback(self):
        primary = FakeOneShotTTS("primary", fail=True)
        fallback = FakeOneShotTTS("fallback")
        tts = FallbackStreamingTTS(primary=primary, fallback=fallback)

        tts.start(sample_rate=24000)
        chunks = tts.synthesize_response_chunks(["hello.", "world."])

        assert [chunk.text for chunk in chunks] == ["fallback:hello.", "fallback:world."]
        assert tts.active_provider == "fallback"
        assert primary.synth_calls == 0
        assert fallback.synth_calls == 2

    def test_realtime_pipeline_uses_response_level_tts_chunks(self):
        primary = FakeOneShotTTS("primary")
        fallback = FakeOneShotTTS("fallback")
        tts = FallbackStreamingTTS(primary=primary, fallback=fallback)
        pipe, rec = build_pipeline(tts=tts)

        asyncio.run(pipe.submit_text("tell me the incident story", path_incident_id=INC_A))

        assert rec.of_type("audio")
        assert tts.active_provider == "primary"
        assert primary.synth_calls >= 1
        assert fallback.synth_calls == 0


class TestSplitSentences:
    def test_splits_on_boundaries(self):
        chunks = split_sentences("One. Two? Three!")
        assert chunks == ["One.", "Two?", "Three!"]

    def test_hard_wrap_long_sentence(self):
        long = "x" * 600
        chunks = split_sentences(long, max_chars=400)
        assert len(chunks) >= 2
        assert all(len(c) <= 401 for c in chunks)

    def test_empty(self):
        assert split_sentences("") == []
        assert split_sentences("   ") == []


# ---------------------------------------------------------------------------
# RealtimeVoicePipeline tests.
# ---------------------------------------------------------------------------
class TestRealtimeText:
    def test_text_turn_full_flow(self):
        pipe, rec = build_pipeline()
        asyncio.run(pipe.submit_text("why did it happen?", path_incident_id=INC_A))
        transcripts = rec.of_type("transcript")
        responses = rec.of_type("response")
        audios = rec.of_type("audio")
        dones = rec.of_type("done")
        assert transcripts and transcripts[0]["text"] == "why did it happen?"
        assert responses and responses[0]["answer"]
        assert responses[0]["incident_id"] == INC_A
        assert responses[0]["intent"] == "why"
        assert audios
        for a in audios:
            assert a["generation_id"] == dones[0]["generation_id"]
            assert a["sample_rate"] == 24000
        timings = dones[0]["timings"]
        for key in ("conversation_ms", "first_response_ms", "tts_first_audio_ms", "tts_ms", "total_ms"):
            assert timings[key] >= 0

    def test_text_turn_followup_uses_session(self):
        pipe, rec = build_pipeline()
        asyncio.run(pipe.submit_text("what happened?", path_incident_id=INC_A))
        asyncio.run(pipe.submit_text("why did it happen?"))
        responses = rec.of_type("response")
        assert responses[1]["incident_id"] == INC_A
        assert responses[1]["intent"] == "why"

    def test_text_turn_no_context_errors(self):
        pipe, rec = build_pipeline()
        asyncio.run(pipe.submit_text("why did it happen?"))
        errors = rec.of_type("error")
        dones = rec.of_type("done")
        assert errors and errors[0]["code"] == ErrorCode.CONVERSATION_ERROR.value
        assert dones

    def test_text_turn_generic_incidents(self):
        for incident in (INC_A, INC_B):
            pipe, rec = build_pipeline()
            asyncio.run(pipe.submit_text("what is the status?", path_incident_id=incident))
            response = rec.of_type("response")
            assert response and response[0]["incident_id"] == incident

    def test_tts_failure_emits_tts_error(self):
        pipe, rec = build_pipeline(tts=FakeStreamingTTS(fail=True))
        asyncio.run(pipe.submit_text("what happened?", path_incident_id=INC_A))
        errors = rec.of_type("error")
        dones = rec.of_type("done")
        assert errors and errors[0]["code"] == ErrorCode.TTS_ERROR.value
        assert dones


class TestRealtimeAudio:
    def test_audio_turn_full_flow(self):
        pipe, rec = build_pipeline(path_incident_id=INC_A)
        asyncio.run(_drive_until_done(pipe, rec))
        transcripts = rec.of_type("transcript")
        responses = rec.of_type("response")
        dones = rec.of_type("done")
        assert transcripts and transcripts[0]["text"] == "why did it happen?"
        assert responses and responses[0]["incident_id"] == INC_A
        assert responses[0]["intent"] == "why"
        timings = dones[0]["timings"]
        assert "stt_final_ms" in timings
        assert "reasoning_ms" in timings
        assert "llm_ms" in timings

    def test_audio_turn_no_speech_no_turn(self):
        pipe, rec = build_pipeline(vad=FakeStreamingVAD(start_at=999, end_at=9999))
        asyncio.run(self._drive(pipe))
        assert rec.of_type("transcript") == []

    @staticmethod
    async def _drive(pipe, frames: int = 5) -> None:
        for _ in range(frames):
            await pipe.accept_audio(Z512)

    def test_audio_turn_emits_partial(self):
        pipe, rec = build_pipeline(path_incident_id=INC_A)
        asyncio.run(_drive_until_done(pipe, rec))
        partials = rec.of_type("transcript_partial")
        assert partials and partials[0]["text"] == "why did"

    def test_audio_turn_stt_failure(self):
        pipe, rec = build_pipeline(stt=FakeStreamingSTT(fail_finalize=True))
        asyncio.run(_drive_until_done(pipe, rec))
        errors = rec.of_type("error")
        assert errors and errors[0]["code"] == ErrorCode.STT_ERROR.value


class TestRealtimeBargeIn:
    def test_interrupt_stops_tts_and_emits_no_done(self):
        release = threading.Event()

        class GatedTTS(FakeStreamingTTS):
            def __init__(self, release):
                super().__init__()
                self.release = release
                self.entered = 0

            def synthesize_chunk(self, text):
                self.entered += 1  # thread entered TTS, now blocked on release
                self.release.wait(timeout=5)
                return super().synthesize_chunk(text)

        tts = GatedTTS(release)
        pipe, rec = build_pipeline(tts=tts, path_incident_id=INC_A)
        asyncio.run(self._barge(pipe, rec, tts, release))
        # The cancelled turn must not emit done or response audio after barge.
        assert rec.of_type("done") == []
        assert tts.stop_calls >= 1
        assert pipe.session.connection_state == "idle"

    @staticmethod
    async def _barge(pipe, rec, tts, release) -> None:
        # Start an audio turn; it reaches TTS (thread entered, blocked on release).
        for _ in range(5):
            await pipe.accept_audio(Z512)
        await _await_true(
            lambda: tts.entered >= 1 and pipe.session.connection_state == "speaking"
        )
        # Barge-in while speaking.
        interrupt_task = asyncio.create_task(
            pipe.interrupt(barged_at=time.perf_counter())
        )
        await asyncio.sleep(0.02)
        release.set()
        await interrupt_task
        # Timings recorded the barge-in -> tts-stopped latency.
        gen = pipe._current_generation
        assert gen is None or gen.timings.get("barge_in_to_tts_stopped_ms") is not None

    def test_stale_generation_ids_change_per_turn(self):
        pipe, rec = build_pipeline()
        asyncio.run(pipe.submit_text("first?", path_incident_id=INC_A))
        first_done = rec.of_type("done")[0]["generation_id"]
        asyncio.run(pipe.submit_text("second?", path_incident_id=INC_A))
        second_done = rec.of_type("done")[-1]["generation_id"]
        assert second_done > first_done
