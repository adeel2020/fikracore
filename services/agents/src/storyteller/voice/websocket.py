"""Realtime voice WebSocket endpoint (Phase 3C).

Exposes ``GET /ws/voice/{session_id}`` as a WebSocket. Audio arrives as raw
``pcm_s16le`` 16 kHz binary frames; control messages are JSON text frames (see
``protocol.py``). Replies stream as JSON control messages plus TTS audio as raw
``pcm_s16le`` 24 kHz binary frames.

Shared heavies (faster-whisper backend, Kokoro backend, gbrain-wired
``ConversationService``) are created once per process and reused across
connections; per-connection streaming wrappers + VAD iterator isolate each
session's streaming state so sessions never cross-talk. All adapters are wired
through ``Depends`` so tests can substitute fakes and never load models.
"""

from __future__ import annotations

import abc
import asyncio
import contextlib
import json
import logging
import threading

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..conversation.service import ConversationService, IncidentNotFound
from .config import get_voice_settings
from .protocol import (
    ErrorCode,
    INPUT_SAMPLE_RATE,
    MessageType,
    MAX_CONTROL_MESSAGE_BYTES,
    build_ready,
    decode_audio_event,
    decode_message,
    float32_to_pcm16,
    pcm16_to_float32,
    validate_audio_payload_size,
    validate_session_id,
)
from .realtime import RealtimeVoicePipeline
from .stt import (
    IncrementalWhisperSTT,
    STTAdapter,
    StreamingSTTAdapter,
    create_stt,
    create_streaming_stt,
)
from .tts import (
    ChunkedKokoroTTS,
    StreamingTTSAdapter,
    TTSAdapter,
    create_streaming_tts,
    create_tts,
)
from .vad import VADAdapter, create_vad

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported message types advertised in the ``ready`` envelope.
_MESSAGE_TYPES = [
    MessageType.START.value,
    MessageType.AUDIO.value,
    MessageType.TEXT.value,
    MessageType.STOP.value,
    MessageType.INTERRUPT.value,
]


class RealtimeVoiceAdapter(abc.ABC):
    """Thin, replaceable realtime *transport* adapter (spec: do not reinvent).

    This layer only moves audio and control messages between a client and the
    voice engine. It MUST NOT contain incident reasoning, session memory, VAD,
    STT, TTS, or conversation logic — those live in ``ConversationService`` and
    the Phase 3B adapters. The concrete implementation here uses FastAPI /
    starlette WebSocket (an existing library already used by this service); a
    LiveKit / aiortc transport could be swapped in by implementing the same
    five methods without touching the voice engine.
    """

    @abc.abstractmethod
    async def start_session(self) -> dict:
        """Accept the client and return the negotiated ``ready`` envelope."""

    @abc.abstractmethod
    async def receive(self) -> tuple[str, object]:
        """Return the next inbound message: ``("audio", bytes)``,
        ``("text", str)``, or ``("disconnect", code)``."""

    @abc.abstractmethod
    async def send_audio(self, audio: bytes) -> None:
        """Send a raw PCM output frame to the client."""

    @abc.abstractmethod
    async def send_message(self, envelope: dict) -> None:
        """Send a JSON control envelope to the client."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the transport and release resources."""


# ---------------------------------------------------------------------------
# Shared, lazily-created heavies (once per process).
# ---------------------------------------------------------------------------
_shared_adapters: dict[str, object] = {}


class _JarvisConversationBridge:
    """ConversationService-shaped bridge for MARK's general assistant brain."""

    def __init__(self) -> None:
        self._jarvis = None
        self._lock = threading.Lock()
        self._simulation_run_id: str | None = None
        self._simulation_context: dict | None = None

    def _get_jarvis(self):
        if self._jarvis is not None:
            return self._jarvis
        with self._lock:
            if self._jarvis is None:
                from assistant.mark import JARVIS  # noqa: PLC0415

                jarvis = JARVIS()
                asyncio.run(jarvis.initialize())
                self._jarvis = jarvis
        return self._jarvis

    def set_simulation_context(self, run_id: str | None) -> None:
        """Pre-load simulation story_context.json for the given run_id.

        When set, Mark's voice responses will be grounded in the active
        simulation's authentic operational context, enabling intelligent
        incident-aware conversation without the user needing to specify
        which incident they're asking about.
        """
        self._simulation_run_id = run_id
        self._simulation_context = None
        if not run_id:
            return
        try:
            from storyteller.knowledge.story_context_reader import StoryContextReader  # noqa: PLC0415

            reader = StoryContextReader()
            story_file = reader.resolve_story_file(run_id)
            if story_file:
                import json as _json  # noqa: PLC0415

                self._simulation_context = _json.loads(
                    story_file.read_text(encoding="utf-8")
                )
                logger.info(
                    "voice bridge loaded simulation context for %s (%s)",
                    run_id,
                    story_file,
                )
        except Exception:
            logger.debug("failed to load simulation context for %s", run_id, exc_info=True)

    def warm(self) -> None:
        """Load MARK once per process while the user is connecting/listening."""
        self._get_jarvis()

    def ask(
        self,
        *,
        path_incident_id: str | None,
        message: str,
        session_id: str,
    ) -> tuple[None, str, str, str | None]:
        jarvis = self._get_jarvis()
        # Enrich context with active simulation if available
        context: dict | None = None
        effective_incident = path_incident_id
        if self._simulation_context:
            sc = self._simulation_context
            context = {
                "path_incident_id": path_incident_id,
                "simulation_run_id": self._simulation_run_id,
                "simulation_summary": sc.get("executive_summary", ""),
                "simulation_stage": sc.get("stage", ""),
                "simulation_root_cause": sc.get("root_cause", {}),
                "simulation_severity": sc.get("severity", ""),
            }
            if not effective_incident:
                effective_incident = self._simulation_run_id
        elif path_incident_id:
            context = {"path_incident_id": path_incident_id}

        answer = asyncio.run(
            jarvis.process(message, session_id=session_id, context=context)
        )
        return None, "mark_general", answer, effective_incident


def _get_shared_stt_backend() -> STTAdapter:
    if "stt" not in _shared_adapters:
        s = get_voice_settings()
        _shared_adapters["stt"] = create_stt(
            provider="local",
            model=s.stt_model,
            device=s.stt_device,
            compute_type=s.stt_compute_type,
            language=s.stt_language,
        )
    return _shared_adapters["stt"]  # type: ignore[return-value]


def _get_shared_tts_backend() -> TTSAdapter:
    if "tts" not in _shared_adapters:
        s = get_voice_settings()
        _shared_adapters["tts"] = create_tts(
            provider="local",
            model=s.tts_model,
            voice=s.tts_voice,
            speed=s.tts_speed,
            device=s.tts_device,
        )
    return _shared_adapters["tts"]  # type: ignore[return-value]


def _make_conversation() -> ConversationService:
    from ..conversation.session import SessionStore  # noqa: PLC0415
    from ..knowledge.gbrain_client import GbrainClient  # noqa: PLC0415
    from ..knowledge.mobile_core_knowledge import MobileCoreKnowledge  # noqa: PLC0415

    return ConversationService(
        MobileCoreKnowledge(GbrainClient()), sessions=SessionStore()
    )


def _get_shared_conversation() -> ConversationService:
    if "conversation" not in _shared_adapters:
        _shared_adapters["conversation"] = _make_conversation()
    return _shared_adapters["conversation"]  # type: ignore[return-value]


def _get_shared_jarvis_conversation() -> _JarvisConversationBridge:
    if "jarvis_conversation" not in _shared_adapters:
        _shared_adapters["jarvis_conversation"] = _JarvisConversationBridge()
    return _shared_adapters["jarvis_conversation"]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Dependencies (overridable in tests).
# ---------------------------------------------------------------------------
def _conversation_dep() -> ConversationService:
    return _get_shared_conversation()


def _jarvis_conversation_dep() -> _JarvisConversationBridge:
    return _get_shared_jarvis_conversation()


def _vad_dep() -> VADAdapter:
    s = get_voice_settings()
    return create_vad(
        threshold=s.voice_vad_threshold,
        min_silence_duration_ms=s.voice_vad_min_silence_ms,
        speech_pad_ms=s.voice_vad_speech_pad_ms,
    )


def _stt_dep() -> StreamingSTTAdapter:
    s = get_voice_settings()
    return create_streaming_stt(
        provider=s.voice_stt_provider,
        local_backend=_get_shared_stt_backend(),
        model=s.stt_model,
        device=s.stt_device,
        compute_type=s.stt_compute_type,
        language=s.stt_language,
        elevenlabs_api_key=s.elevenlabs_api_key,
        elevenlabs_stt_model=s.elevenlabs_stt_model,
        elevenlabs_timeout_s=s.elevenlabs_timeout_s,
    )


def _tts_dep() -> StreamingTTSAdapter:
    s = get_voice_settings()
    return create_streaming_tts(
        provider=s.voice_tts_provider,
        local_backend=_get_shared_tts_backend(),
        model=s.tts_model,
        voice=s.tts_voice,
        speed=s.tts_speed,
        device=s.tts_device,
        elevenlabs_api_key=s.elevenlabs_api_key,
        elevenlabs_voice_id=s.elevenlabs_voice_id,
        elevenlabs_model=s.elevenlabs_model,
        elevenlabs_tts_output_format=s.elevenlabs_tts_output_format,
        elevenlabs_timeout_s=s.elevenlabs_timeout_s,
    )


# ---------------------------------------------------------------------------
# Concurrent-session limiter (resource protection, Phase 3D).
# ---------------------------------------------------------------------------
class _SessionLimiter:
    """Bounded active-connection counter shared across all voice sessions."""

    def __init__(self, limit: int) -> None:
        self.limit = max(1, int(limit))
        self.active = 0

    def acquire(self) -> bool:
        if self.active >= self.limit:
            return False
        self.active += 1
        return True

    def release(self) -> None:
        self.active = max(0, self.active - 1)


def _get_session_limiter() -> _SessionLimiter:
    if not hasattr(_get_session_limiter, "_limiter"):
        _get_session_limiter._limiter = _SessionLimiter(
            get_voice_settings().voice_max_concurrent_sessions
        )
    return _get_session_limiter._limiter


async def warm_voice_backends() -> None:
    """Eagerly load the shared model backends (opt-in, non-blocking).

    Called from the app startup lifecycle so the first real connection is not
    cold. Only loads models (no fixture inference); is trip-safe — any failure
    is logged and startup continues. Yes = ``VOICE_WARMUP=1``.
    """
    if not get_voice_settings().voice_warmup:
        return
    try:
        from . import runtime  # noqa: PLC0415

        runtime.configure_runtime()
        await asyncio.to_thread(_get_shared_stt_backend().init)
        await asyncio.to_thread(_get_shared_tts_backend().init)
        create_vad().init()
        logger.info("voice backends warmed up")
    except Exception as exc:  # noqa: BLE001 - optional warm-up must never break startup
        logger.warning("voice warm-up skipped: %s", exc)


class _Connection(RealtimeVoiceAdapter):
    """Per-connection FastAPI WebSocket transport (implements the adapter)."""

    def __init__(self, websocket: WebSocket, session_id: str, *, out_queue_size: int = 256) -> None:
        self.ws = websocket
        self.session_id = session_id
        self.pipeline: RealtimeVoicePipeline | None = None
        self._out: asyncio.Queue[tuple[str, object]] = asyncio.Queue(
            maxsize=max(8, int(out_queue_size))
        )
        self._closed = False

    # -- RealtimeVoiceAdapter: transport only ---------------------------------
    async def start_session(self) -> dict:
        await self.ws.accept()
        ready = build_ready(self.session_id, _MESSAGE_TYPES)
        await self._out.put(("json", ready))
        return ready

    async def receive(self) -> tuple[str, object]:
        message = await self.ws.receive()
        mtype = message.get("type")
        if mtype == "websocket.disconnect":
            return ("disconnect", message.get("code"))
        if message.get("bytes") is not None:
            return ("audio", bytes(message["bytes"]))
        return ("text", message.get("text") or "")

    async def send_audio(self, audio: bytes) -> None:
        await self._enqueue(("binary", audio), audio=True)

    async def send_message(self, envelope: dict) -> None:
        await self._enqueue(("json", envelope))

    async def _enqueue(self, item: tuple[str, object], *, audio: bool = False) -> None:
        """Bound the sender queue (resource protection). When a slow client fills
        the queue, audio frames are dropped (loss-tolerant); control messages are
        dropped too rather than letting the queue grow without bound."""
        try:
            self._out.put_nowait(item)
        except asyncio.QueueFull:
            if not audio:
                logger.warning(
                    "voice sender queue full; dropping control frame session=%s",
                    self.session_id,
                )

    async def close(self) -> None:
        self._closed = True

    # -- pipeline emit callback (routes engine events onto the transport) -----
    async def emit(self, event: dict) -> None:
        if event.get("type") == MessageType.AUDIO.value:
            audio = event.pop("audio")
            sr = event.get("sample_rate")
            meta = {
                "type": MessageType.AUDIO.value,
                "generation_id": event.get("generation_id"),
                "format": "pcm_s16le",
                "sample_rate": sr,
                "channels": 1,
            }
            await self.send_message(meta)
            await self.send_audio(float32_to_pcm16(audio))
        else:
            await self.send_message(event)

    async def send_error(self, code: ErrorCode, message: str) -> None:
        gen = self.pipeline._current_generation if self.pipeline else None
        await self.send_message(
            {
                "type": MessageType.ERROR.value,
                "generation_id": gen.id if gen else None,
                "code": code.value,
                "message": message,
            }
        )

    # -- sender task (drains the out-queue to the socket) ---------------------
    async def _sender(self) -> None:
        while True:
            kind, payload = await self._out.get()
            if kind is None:
                break
            try:
                if kind == "binary":
                    await self.ws.send_bytes(bytes(payload))  # type: ignore[arg-type]
                else:
                    await self.ws.send_text(json.dumps(payload))
            except Exception:  # noqa: BLE001 - socket closed mid-send
                break

    # -- inbound dispatch -----------------------------------------------------
    async def _handle_audio(self, data: bytes) -> None:
        if self.pipeline is None:
            return
        try:
            validate_audio_payload_size(data)
            audio = pcm16_to_float32(data)
        except ValueError as exc:
            await self.send_error(ErrorCode.AUDIO_FORMAT_ERROR, str(exc))
            return
        try:
            await self.pipeline.accept_audio(audio)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to process audio frame session=%s: %s", self.session_id, exc)
            await self.send_error(ErrorCode.AUDIO_FORMAT_ERROR, str(exc))

    async def _handle_text(self, text: str) -> None:
        if len(text) > MAX_CONTROL_MESSAGE_BYTES:
            await self.send_error(ErrorCode.INVALID_MESSAGE, "control message too large")
            return
        try:
            env = decode_message(text)
        except ValueError as exc:
            await self.send_error(ErrorCode.INVALID_MESSAGE, str(exc))
            return
        if self.pipeline is None:
            return
        try:
            mtype = env.get("type")
            if mtype == MessageType.START.value:
                await self.pipeline.begin_generation(
                    path_incident_id=env.get("path_incident_id")
                )
            elif mtype == MessageType.TEXT.value:
                body = env.get("text")
                if not isinstance(body, str) or not body.strip():
                    await self.send_error(
                        ErrorCode.INVALID_MESSAGE, "text message requires non-empty 'text'"
                    )
                    return
                await self.pipeline.submit_text(
                    body, path_incident_id=env.get("path_incident_id")
                )
            elif mtype in (MessageType.INTERRUPT.value, MessageType.STOP.value):
                await self.pipeline.interrupt()
            elif mtype == MessageType.AUDIO.value:
                try:
                    audio = decode_audio_event(env)
                except ValueError as exc:
                    await self.send_error(ErrorCode.AUDIO_FORMAT_ERROR, str(exc))
                    return
                await self.pipeline.accept_audio(audio)
            else:
                await self.send_error(ErrorCode.INVALID_MESSAGE, f"unknown message type '{mtype}'")
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to process text frame session=%s: %s", self.session_id, exc)
            await self.send_error(ErrorCode.INVALID_MESSAGE, str(exc))


class VoiceSessionRequest(BaseModel):
    """Body for the incident-to-session binding endpoint."""

    session_id: str = Field(..., min_length=1, max_length=128)


@router.post("/api/incidents/{incident_id:path}/voice-session")
async def bind_voice_session(
    incident_id: str,
    req: VoiceSessionRequest,
    conversation: ConversationService = Depends(_conversation_dep),
) -> dict:
    """Explicitly bind an incident to a ``session_id`` (spec: incident selection).

    This reuses the existing Phase 3A ``SessionStore`` — the same store the
    WebSocket turns read from, so a follow-up question in that session resolves
    the incident without repeating its id. The incident must exist in gbrain;
    there is no guessing and no separate incident cache.
    """
    reason = validate_session_id(req.session_id)
    if reason is not None:
        raise HTTPException(status_code=400, detail=reason)
    if not incident_id:
        raise HTTPException(status_code=400, detail="incident id is required")
    try:
        conversation.get_context(incident_id)
    except IncidentNotFound as exc:
        raise HTTPException(
            status_code=404, detail=f"Incident '{incident_id}' was not found in the knowledge graph."
        ) from exc
    conversation.sessions.set_active_incident(req.session_id, incident_id)
    return {
        "session_id": req.session_id,
        "incident_id": incident_id,
        "active": True,
        "note": "incident bound to session; follow-up questions need not repeat the id",
    }


@router.get("/voice-test")
async def voice_test_page() -> HTMLResponse:
    """Minimal browser test client (spec #14): mic, transcript, playback,
    interrupt. Uses the browser's ``getUserMedia`` for capture and streams raw
    PCM over the WebSocket — no custom WebRTC protocol is implemented."""
    from pathlib import Path  # noqa: PLC0415

    page = Path(__file__).parent / "static" / "voice_test.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))


@router.websocket("/ws/voice/{session_id}")
async def voice_ws(
    websocket: WebSocket,
    session_id: str,
    conversation: ConversationService = Depends(_conversation_dep),
    vad: VADAdapter = Depends(_vad_dep, use_cache=False),
    stt: StreamingSTTAdapter = Depends(_stt_dep, use_cache=False),
    tts: StreamingTTSAdapter = Depends(_tts_dep, use_cache=False),
) -> None:
    reason = validate_session_id(session_id)
    if reason is not None:
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "type": MessageType.ERROR.value,
                    "code": ErrorCode.SESSION_ERROR.value,
                    "message": reason,
                }
            )
        )
        await websocket.close(code=1008)
        return

    # Resource protection: refuse new sessions past the configured cap.
    limiter = _get_session_limiter()
    if not limiter.acquire():
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "type": MessageType.ERROR.value,
                    "code": ErrorCode.SESSION_ERROR.value,
                    "message": "too many concurrent voice sessions",
                }
            )
        )
        await websocket.close(code=1013)
        return

    settings = get_voice_settings()
    conn = _Connection(
        websocket, session_id, out_queue_size=settings.voice_out_queue_size
    )
    conn.pipeline = RealtimeVoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=conversation,
        session_id=session_id,
        emit=conn.emit,
        max_turn_ms=settings.voice_max_turn_ms,
        max_utterance_samples=int(
            settings.voice_max_utterance_seconds * INPUT_SAMPLE_RATE
        ),
    )
    await conn.start_session()
    sender = asyncio.create_task(conn._sender())

    try:
        while True:
            try:
                kind, payload = await asyncio.wait_for(
                    conn.receive(), timeout=settings.voice_idle_timeout_s
                )
            except asyncio.TimeoutError:
                logger.info("voice websocket idle timeout: %s", session_id)
                break
            if kind == "disconnect":
                break
            if kind == "audio":
                await conn._handle_audio(payload)  # type: ignore[arg-type]
            else:
                await conn._handle_text(payload)  # type: ignore[arg-type]
    except WebSocketDisconnect:
        logger.info("voice websocket disconnected: %s", session_id)
    finally:
        await conn.pipeline.close()
        conn._closed = True
        await conn._out.put((None, None))
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender
        await conn.close()
        limiter.release()


@router.websocket("/ws/jarvis-voice/{session_id}")
async def jarvis_voice_ws(
    websocket: WebSocket,
    session_id: str,
    run_id: str | None = None,
    conversation: _JarvisConversationBridge = Depends(_jarvis_conversation_dep),
    vad: VADAdapter = Depends(_vad_dep, use_cache=False),
    stt: StreamingSTTAdapter = Depends(_stt_dep, use_cache=False),
    tts: StreamingTTSAdapter = Depends(_tts_dep, use_cache=False),
) -> None:
    reason = validate_session_id(session_id)
    if reason is not None:
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "type": MessageType.ERROR.value,
                    "code": ErrorCode.SESSION_ERROR.value,
                    "message": reason,
                }
            )
        )
        await websocket.close(code=1008)
        return

    limiter = _get_session_limiter()
    if not limiter.acquire():
        await websocket.accept()
        await websocket.send_text(
            json.dumps(
                {
                    "type": MessageType.ERROR.value,
                    "code": ErrorCode.SESSION_ERROR.value,
                    "message": "too many concurrent voice sessions",
                }
            )
        )
        await websocket.close(code=1013)
        return

    settings = get_voice_settings()

    # Pre-load simulation context if a run_id was provided
    if run_id and hasattr(conversation, "set_simulation_context"):
        try:
            conversation.set_simulation_context(run_id)
        except Exception:
            logger.debug("failed to set simulation context for voice: %s", run_id, exc_info=True)

    conn = _Connection(
        websocket, session_id, out_queue_size=settings.voice_out_queue_size
    )
    conn.pipeline = RealtimeVoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=conversation,  # type: ignore[arg-type]
        session_id=session_id,
        emit=conn.emit,
        max_turn_ms=settings.voice_max_turn_ms,
        max_utterance_samples=int(
            settings.voice_max_utterance_seconds * INPUT_SAMPLE_RATE
        ),
    )
    await conn.start_session()
    sender = asyncio.create_task(conn._sender())
    warm = getattr(conversation, "warm", None)
    warm_task = (
        asyncio.create_task(asyncio.to_thread(warm)) if callable(warm) else None
    )

    try:
        while True:
            try:
                kind, payload = await asyncio.wait_for(
                    conn.receive(), timeout=settings.voice_idle_timeout_s
                )
            except asyncio.TimeoutError:
                logger.info("jarvis voice websocket idle timeout: %s", session_id)
                break
            if kind == "disconnect":
                break
            if kind == "audio":
                await conn._handle_audio(payload)  # type: ignore[arg-type]
            else:
                await conn._handle_text(payload)  # type: ignore[arg-type]
    except WebSocketDisconnect:
        logger.info("jarvis voice websocket disconnected: %s", session_id)
    finally:
        await conn.pipeline.close()
        if warm_task is not None:
            if not warm_task.done():
                warm_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await warm_task
            else:
                with contextlib.suppress(Exception):
                    warm_task.result()
        conn._closed = True
        await conn._out.put((None, None))
        sender.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sender
        await conn.close()
        limiter.release()


__all__ = [
    "ChunkedKokoroTTS",
    "IncrementalWhisperSTT",
    "RealtimeVoiceAdapter",
    "RealtimeVoicePipeline",
    "VoiceSessionRequest",
    "bind_voice_session",
    "router",
    "_conversation_dep",
    "_jarvis_conversation_dep",
    "_stt_dep",
    "_tts_dep",
    "_vad_dep",
]
