"""Local voice pipeline: audio → VAD → STT → ConversationService → TTS → audio.

Phase 3B. The pipeline is incident-agnostic: it only passes an optional
``path_incident_id`` through to the Phase 3A conversation service and never
hard-codes any incident, KPI, or network function.

Latency instrumentation (milliseconds) is recorded for every stage:
``vad_ms``, ``stt_ms``, ``conversation_ms``, ``tts_ms`` and ``total_ms``.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from ..conversation.service import (
    ConversationError,
    ConversationService,
    IncidentContextRequired,
    IncidentNotFound,
)
from .session import VoiceSession
from .stt import STTAdapter, STTError
from .tts import TTSAdapter, TTSError
from .vad import VADAdapter, VADError

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 16000


class VoiceResult:
    """Result of a single voice turn (audio route or text route)."""

    __slots__ = (
        "transcript",
        "answer",
        "intent",
        "incident_id",
        "audio",
        "sample_rate",
        "timings",
        "error",
        "synthesized",
    )

    def __init__(
        self,
        *,
        transcript: str,
        answer: str,
        intent: str | None,
        incident_id: str | None,
        audio: np.ndarray | None,
        sample_rate: int | None,
        timings: dict[str, float],
        error: str | None = None,
        synthesized: bool = False,
    ) -> None:
        self.transcript = transcript
        self.answer = answer
        self.intent = intent
        self.incident_id = incident_id
        self.audio = audio
        self.sample_rate = sample_rate
        self.timings = timings
        self.error = error
        self.synthesized = synthesized

    def to_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript,
            "answer": self.answer,
            "intent": self.intent,
            "incident_id": self.incident_id,
            "audio": None if self.audio is None else self.audio.tolist(),
            "sample_rate": self.sample_rate,
            "timings": self.timings,
            "error": self.error,
            "synthesized": self.synthesized,
        }


class VoicePipeline:
    """Sequential local voice pipeline.

    All heavy backends (VAD/STT/TTS) are lazily initialized on first use so the
    pipeline can be constructed without downloading models. Backends are
    replaceable adapters, so tests inject fakes.
    """

    def __init__(
        self,
        *,
        vad: VADAdapter,
        stt: STTAdapter,
        tts: TTSAdapter,
        conversation: ConversationService,
        session_id: str = "voice-default",
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> None:
        self.vad = vad
        self.stt = stt
        self.tts = tts
        self.conversation = conversation
        self.session = VoiceSession(conversation=conversation, session_id=session_id)
        self.sample_rate = sample_rate

    # ------------------------------------------------------------------
    # Audio route: audio → VAD → STT → conversation → TTS → audio.
    # ------------------------------------------------------------------
    def process_audio(
        self,
        audio: np.ndarray,
        *,
        sample_rate: int | None = None,
        path_incident_id: str | None = None,
    ) -> VoiceResult:
        timings = _empty_timings()
        error: str | None = None

        sr = sample_rate or self.sample_rate
        if sr != self.sample_rate:
            return VoiceResult(
                transcript="",
                answer="Audio sample rate is not supported.",
                intent=None,
                incident_id=None,
                audio=None,
                sample_rate=None,
                timings=timings,
                error=f"unsupported sample rate {sr}; expected {self.sample_rate}",
            )

        # VAD
        t0 = time.perf_counter()
        try:
            self.vad.init()
            ranges = self.vad.speech_ranges(audio, sr)
        except VADError as exc:
            error = f"VAD error: {exc}"
            return self._result(
                transcript="",
                answer=error,
                intent=None,
                incident_id=None,
                audio=None,
                timings=timings,
                error=error,
            )
        timings["vad_ms"] = (time.perf_counter() - t0) * 1000.0

        if not ranges:
            return self._result(
                transcript="",
                answer="No speech detected.",
                intent=None,
                incident_id=None,
                audio=None,
                timings=timings,
                error="no speech detected",
            )

        speech = _extract_speech(audio, ranges)

        # STT
        t0 = time.perf_counter()
        try:
            self.stt.init()
            stt_result = self.stt.transcribe(speech, sr)
            transcript = stt_result.text.strip()
        except STTError as exc:
            error = f"STT error: {exc}"
            return self._result(
                transcript="",
                answer=error,
                intent=None,
                incident_id=None,
                audio=None,
                timings=timings,
                error=error,
            )
        timings["stt_ms"] = (time.perf_counter() - t0) * 1000.0

        if not transcript:
            return self._result(
                transcript="",
                answer="I could not understand the audio.",
                intent=None,
                incident_id=None,
                audio=None,
                timings=timings,
                error="empty transcript",
            )

        # Conversation
        t0 = time.perf_counter()
        try:
            story, intent, answer, resolved_id = self.conversation.ask(
                path_incident_id=path_incident_id,
                message=transcript,
                session_id=self.session.session_id,
            )
            incident_id = resolved_id
        except (IncidentContextRequired, IncidentNotFound, ConversationError) as exc:
            error = f"conversation error: {exc}"
            return self._result(
                transcript=transcript,
                answer=error,
                intent=None,
                incident_id=self.session.active_incident_id,
                audio=None,
                timings=timings,
                error=error,
            )
        timings["conversation_ms"] = (time.perf_counter() - t0) * 1000.0

        # TTS
        t0 = time.perf_counter()
        try:
            self.tts.init()
            tts_result = self.tts.synthesize(answer)
            audio_out = tts_result.audio
            out_sr = tts_result.sample_rate
        except TTSError as exc:
            error = f"TTS error: {exc}"
            return self._result(
                transcript=transcript,
                answer=answer,
                intent=intent,
                incident_id=incident_id,
                audio=None,
                timings=timings,
                error=error,
            )
        timings["tts_ms"] = (time.perf_counter() - t0) * 1000.0

        timings["total_ms"] = sum(
            timings[k] for k in ("vad_ms", "stt_ms", "conversation_ms", "tts_ms")
        )
        self.session.remember(
            transcript=transcript,
            answer=answer,
            intent=intent,
            incident_id=incident_id,
        )
        return VoiceResult(
            transcript=transcript,
            answer=answer,
            intent=intent,
            incident_id=incident_id,
            audio=audio_out,
            sample_rate=out_sr,
            timings=timings,
            synthesized=True,
        )

    # ------------------------------------------------------------------
    # Text route: text → ConversationService → TTS → audio.
    # Used by the CLI ``--text`` mode and by integration tests (no mic).
    # ------------------------------------------------------------------
    def process_text(
        self,
        text: str,
        *,
        path_incident_id: str | None = None,
    ) -> VoiceResult:
        timings = _empty_timings()
        error: str | None = None

        try:
            story, intent, answer, resolved_id = self.conversation.ask(
                path_incident_id=path_incident_id,
                message=text,
                session_id=self.session.session_id,
            )
            incident_id = resolved_id
        except (IncidentContextRequired, IncidentNotFound, ConversationError) as exc:
            error = f"conversation error: {exc}"
            return self._result(
                transcript=text,
                answer=error,
                intent=None,
                incident_id=self.session.active_incident_id,
                audio=None,
                timings=timings,
                error=error,
            )

        # TTS
        t0 = time.perf_counter()
        try:
            self.tts.init()
            tts_result = self.tts.synthesize(answer)
            audio_out = tts_result.audio
            out_sr = tts_result.sample_rate
        except TTSError as exc:
            error = f"TTS error: {exc}"
            return self._result(
                transcript=text,
                answer=answer,
                intent=intent,
                incident_id=incident_id,
                audio=None,
                timings=timings,
                error=error,
            )
        timings["tts_ms"] = (time.perf_counter() - t0) * 1000.0
        timings["total_ms"] = timings["tts_ms"]

        self.session.remember(
            transcript=text,
            answer=answer,
            intent=intent,
            incident_id=incident_id,
        )
        return VoiceResult(
            transcript=text,
            answer=answer,
            intent=intent,
            incident_id=incident_id,
            audio=audio_out,
            sample_rate=out_sr,
            timings=timings,
            synthesized=True,
        )

    # ------------------------------------------------------------------
    # Helpers.
    # ------------------------------------------------------------------
    def _result(
        self,
        *,
        transcript: str,
        answer: str,
        intent: str | None,
        incident_id: str | None,
        audio: np.ndarray | None,
        timings: dict[str, float],
        error: str | None,
    ) -> VoiceResult:
        timings["total_ms"] = sum(
            timings[k] for k in ("vad_ms", "stt_ms", "conversation_ms", "tts_ms")
        )
        return VoiceResult(
            transcript=transcript,
            answer=answer,
            intent=intent,
            incident_id=incident_id,
            audio=audio,
            sample_rate=None if audio is None else self.tts.sample_rate,
            timings=timings,
            error=error,
        )


def _empty_timings() -> dict[str, float]:
    return {
        "vad_ms": 0.0,
        "stt_ms": 0.0,
        "conversation_ms": 0.0,
        "tts_ms": 0.0,
        "total_ms": 0.0,
    }


def _extract_speech(audio: np.ndarray, ranges: list[tuple[int, int]]) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)
    if len(ranges) == 1:
        start, end = ranges[0]
        return audio[start:end]
    return np.concatenate([audio[start:end] for start, end in ranges])


__all__ = ["DEFAULT_SAMPLE_RATE", "VoicePipeline", "VoiceResult"]
