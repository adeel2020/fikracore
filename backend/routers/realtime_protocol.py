"""Custom OpenAI Realtime protocol WebSocket server.

Replaces HF speech-to-speech subprocess. Uses existing local components:
  - Whisper Tiny (transformers) for STT
  - Kokoro (local) for TTS
  - run_storyteller() for the CrewAI agent

Speaks the standard OpenAI Realtime protocol on the wire so the frontend
WebSocketContext.tsx (Realtime protocol client) connects without changes.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import uuid
from typing import Any, Optional

import numpy as np
import torch
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Singletons (lazy-loaded, thread-safe)
# ---------------------------------------------------------------------------
# --- Whisper Tiny (local) ---
_whisper_processor: Any = None
_whisper_model: Any = None
_whisper_lock = asyncio.Lock()

# --- Kokoro globals ---
_kokoro_pipe: Any = None
_kokoro_lock = asyncio.Lock()

TARGET_SAMPLE_RATE = 24000  # Kokoro native rate; Realtime protocol default
MAX_AUDIO_SAMPLES = 480000  # 30 s


async def warmup_models() -> None:
    """Pre-load Whisper Tiny + Kokoro on server start."""
    logger.info("Warming up Whisper Tiny …")
    await _get_whisper()
    logger.info("Warming up Kokoro TTS …")
    await _get_kokoro()
    phonemizer_log = logging.getLogger("phonemizer")
    phonemizer_log.setLevel(logging.ERROR)
    phonemizer_log.propagate = False
    logger.info("All models ready")


async def _get_whisper():
    global _whisper_processor, _whisper_model
    if _whisper_model is not None:
        return _whisper_processor, _whisper_model
    async with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_processor, _whisper_model
        loop = asyncio.get_event_loop()

        def _load():
            global _whisper_processor, _whisper_model
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            logger.info("Loading Whisper Tiny ...")
            _whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
            _whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en")
            _whisper_model.config.forced_decoder_ids = None
            logger.info("Whisper Tiny ready")
            return _whisper_processor, _whisper_model

        return await loop.run_in_executor(None, _load)


async def _get_kokoro():
    global _kokoro_pipe
    if _kokoro_pipe is not None:
        return _kokoro_pipe
    async with _kokoro_lock:
        if _kokoro_pipe is not None:
            return _kokoro_pipe
        loop = asyncio.get_event_loop()

        def _load():
            global _kokoro_pipe
            from kokoro import KPipeline
            logger.info("Loading Kokoro TTS …")
            pipe = KPipeline(lang_code="a")
            _kokoro_pipe = pipe
            logger.info("Kokoro ready")
            return pipe

        return await loop.run_in_executor(None, _load)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gen_id(prefix: str = "evt") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _build_session(session_id: str) -> dict:
    return {
        "id": session_id,
        "model": "noc-storyteller",
        "modalities": ["text", "audio"],
        "instructions": "",
        "voice": "af_heart",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "input_audio_transcription": {"model": "whisper-1"},
        "turn_detection": None,
        "tools": [],
        "tool_choice": "auto",
        "temperature": 0.8,
        "max_output_tokens": 2048,
    }


async def _send(ws: WebSocket, msg: dict) -> None:
    await ws.send_json(msg)


# ---------------------------------------------------------------------------
# Conversation state (per-connection)
# ---------------------------------------------------------------------------

class ConnState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.config = _build_session(session_id)
        self.history: list[dict] = []
        self.in_response = False
        self.response_id: str | None = None
        self.item_id: str | None = None
        self.content_index = 0
        self.cancel_event = asyncio.Event()

    def next_item_id(self) -> str:
        self.item_id = _gen_id("item")
        return self.item_id

    def next_response_id(self) -> str:
        self.response_id = _gen_id("resp")
        return self.response_id

    def next_content_index(self) -> int:
        idx = self.content_index
        self.content_index += 1
        return idx


# ---------------------------------------------------------------------------
# Audio processing pipeline
# ---------------------------------------------------------------------------

async def _transcribe(audio_bytes: bytes) -> str | None:
    processor, model = await _get_whisper()
    loop = asyncio.get_event_loop()
    logger.info("Transcribing %d PCM16 bytes via Whisper Tiny", len(audio_bytes))

    def _run():
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        inputs = processor(
            audio_np,
            sampling_rate=16000,
            return_tensors="pt",
        )
        with torch.no_grad():
            generated_ids = model.generate(inputs.input_features)
        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return transcript if transcript else ""

    result = await loop.run_in_executor(None, _run)
    logger.info("Transcript: '%s' (%d chars)", result, len(result))
    return result if len(result) >= 1 else None


async def _synthesize(text: str, voice: str = "af_heart") -> tuple[np.ndarray | None, list[dict]]:
    """Run Kokoro TTS, return (audio_float32_24khz, word_timings)."""
    kokoro = await _get_kokoro()
    loop = asyncio.get_event_loop()

    def _run():
        segments = []
        timings = []
        offset = 0.0
        gen = kokoro(text, voice=voice, speed=1, split_pattern=None)
        for result in gen:
            audio = result.audio.cpu().numpy()
            tokens = result.tokens
            for token in tokens:
                if token.start_ts is not None and token.end_ts is not None:
                    timings.append({
                        "word": token.text,
                        "start_time": (token.start_ts + offset) * 1000,
                        "end_time": (token.end_ts + offset) * 1000,
                    })
            segments.append(audio)
            if len(audio):
                offset += len(audio) / TARGET_SAMPLE_RATE
        if not segments:
            return None, []
        return np.concatenate(segments), timings

    return await loop.run_in_executor(None, _run)


async def _process_utterance(
    ws: WebSocket,
    audio_bytes: bytes,
    state: ConnState,
) -> None:
    """STT → agent → TTS → stream response events."""
    if state.in_response:
        logger.warning("Already in response, dropping utterance")
        return

    # --- speech_started / speech_stopped (only with server VAD) ---
    item_id = state.next_item_id()
    if state.config.get("turn_detection"):
        await _send(ws, {
            "type": "input_audio_buffer.speech_started",
            "event_id": _gen_id(),
            "audio_start_ms": 0,
            "item_id": item_id,
        })
        # Small delay so the frontend receives speech_started before transcription
        await asyncio.sleep(0.05)
        await _send(ws, {
            "type": "input_audio_buffer.speech_stopped",
            "event_id": _gen_id(),
            "audio_end_ms": _now_ms(),
            "item_id": item_id,
        })

    # --- STT ---
    transcript = await _transcribe(audio_bytes)
    if not transcript:
        logger.info("No transcription, skipping response")
        return
    logger.info("Transcript: %s", transcript)

    await _send(ws, {
        "type": "conversation.item.created",
        "event_id": _gen_id(),
        "item": {
            "id": item_id,
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": transcript}],
        },
    })
    await _send(ws, {
        "type": "conversation.item.input_audio_transcription.completed",
        "event_id": _gen_id(),
        "item_id": item_id,
        "content_index": 0,
        "transcript": transcript,
    })

    # --- Agent ---
    from backend.datastory.crewai_storyteller import run_storyteller

    response = await asyncio.get_event_loop().run_in_executor(
        None, run_storyteller, transcript, state.history
    )
    state.history.append({"q": transcript, "a": response})
    if len(state.history) > 10:
        state.history[:] = state.history[-10:]
    logger.info("Agent: %.120s", response)

    tts_voice = state.config.get("voice", "af_heart")
    audio, word_timings = await _synthesize(response, voice=tts_voice)
    if audio is None or len(audio) == 0:
        return

    audio_int16 = (audio * 32767).astype(np.int16).tobytes()
    resp_id = state.next_response_id()
    out_item_id = _gen_id("item")
    state.in_response = True

    # response.created
    await _send(ws, {
        "type": "response.created",
        "event_id": _gen_id(),
        "response": {
            "id": resp_id,
            "object": "realtime.response",
            "status": "in_progress",
            "status_details": None,
            "output": [],
            "usage": None,
        },
    })

    CHUNK_SIZE = 3200  # 100 ms at 24 kHz / 16-bit
    # Stream audio chunks
    for offset in range(0, len(audio_int16), CHUNK_SIZE):
        if state.cancel_event.is_set():
            logger.info("Response cancelled mid-stream")
            break
        chunk = audio_int16[offset : offset + CHUNK_SIZE]
        b64 = base64.b64encode(chunk).decode("ascii")
        await _send(ws, {
            "type": "response.output_audio.delta",
            "event_id": _gen_id(),
            "response_id": resp_id,
            "item_id": out_item_id,
            "output_index": 0,
            "content_index": state.next_content_index(),
            "delta": b64,
            "sample_rate": TARGET_SAMPLE_RATE,
        })
        await asyncio.sleep(0.01)  # yield to event loop

    if not state.cancel_event.is_set():
        # audio.done
        await _send(ws, {
            "type": "response.output_audio.done",
            "event_id": _gen_id(),
            "response_id": resp_id,
            "item_id": out_item_id,
            "output_index": 0,
            "content_index": state.content_index,
        })

        # transcript.done (includes word_timings for lip-sync)
        await _send(ws, {
            "type": "response.output_audio_transcript.done",
            "event_id": _gen_id(),
            "response_id": resp_id,
            "item_id": out_item_id,
            "output_index": 0,
            "content_index": state.content_index,
            "transcript": response,
            "word_timings": word_timings,
        })

        # response.done
        await _send(ws, {
            "type": "response.done",
            "event_id": _gen_id(),
            "response": {
                "id": resp_id,
                "object": "realtime.response",
                "status": "completed",
                "status_details": None,
                "output": [
                    {
                        "id": out_item_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {"type": "audio", "transcript": response},
                        ],
                    }
                ],
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                },
            },
        })

    state.in_response = False
    state.cancel_event.clear()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/v1/realtime")
async def realtime_websocket(ws: WebSocket):
    await ws.accept()
    session_id = _gen_id("sess")
    state = ConnState(session_id)

    logger.info("Realtime client connected (session=%s)", session_id)

    # session.created
    await _send(ws, {
        "type": "session.created",
        "event_id": _gen_id(),
        "session": dict(state.config),
    })

    try:
        async def _run_utterance(audio: bytes):
            try:
                await _process_utterance(ws, audio, state)
            except Exception:
                logger.exception("Utterance failed")
                state.in_response = False
                state.cancel_event.clear()

        pending_utterance: asyncio.Task | None = None
        audio_buffer = bytearray()

        while True:
            raw = await ws.receive_json()
            t = raw.get("type")

            if t == "session.update":
                session = raw.get("session", {})
                for key in ("instructions", "turn_detection", "tools", "voice",
                            "input_audio_format", "output_audio_format"):
                    if key in session:
                        state.config[key] = session[key]
                await _send(ws, {
                    "type": "session.updated",
                    "event_id": _gen_id(),
                })

            elif t == "input_audio_buffer.append":
                b64 = raw.get("audio", "")
                try:
                    audio_buffer.extend(base64.b64decode(b64))
                except Exception as exc:
                    logger.warning("Audio decode error: %s", exc)

            elif t == "input_audio_buffer.commit":
                if len(audio_buffer) == 0:
                    logger.warning("commit with empty buffer")
                    continue
                audio_bytes = bytes(audio_buffer)
                audio_buffer.clear()
                # Cancel previous in-flight utterance
                if pending_utterance and not pending_utterance.done():
                    pending_utterance.cancel()
                    try:
                        await pending_utterance
                    except (asyncio.CancelledError, Exception):
                        pass
                    state.cancel_event.set()
                    state.in_response = False
                pending_utterance = asyncio.create_task(
                    _run_utterance(audio_bytes)
                )

            elif t == "response.create":
                if len(audio_buffer) > 0:
                    audio_bytes = bytes(audio_buffer)
                    audio_buffer.clear()
                    if pending_utterance and not pending_utterance.done():
                        pending_utterance.cancel()
                        try:
                            await pending_utterance
                        except (asyncio.CancelledError, Exception):
                            pass
                    pending_utterance = asyncio.create_task(
                        _run_utterance(audio_bytes)
                    )
                elif not state.in_response:
                    # No audio, just run the agent with the last context
                    if state.history:
                        last_q = state.history[-1].get("q", "")
                        pending_utterance = asyncio.create_task(
                            _run_utterance(b"")
                        )

            elif t == "response.cancel":
                state.cancel_event.set()
                if pending_utterance and not pending_utterance.done():
                    pending_utterance.cancel()
                    try:
                        await pending_utterance
                    except (asyncio.CancelledError, Exception):
                        pass
                state.in_response = False
                await _send(ws, {
                    "type": "response.done",
                    "event_id": _gen_id(),
                    "response": {
                        "id": state.response_id or _gen_id("resp"),
                        "object": "realtime.response",
                        "status": "cancelled",
                        "status_details": {"reason": "client_cancelled"},
                        "output": [],
                        "usage": None,
                    },
                })

            elif t == "conversation.item.create":
                item = raw.get("item", {})
                role = item.get("role")
                content = item.get("content", [])
                if role == "user" and content:
                    text = " ".join(
                        p.get("text", "") for p in content if p.get("type") == "input_text"
                    )
                    if text.strip():
                        state.history.append({"q": text.strip(), "a": ""})

            else:
                logger.debug("Unhandled event type: %s", t)

    except WebSocketDisconnect:
        logger.info("Realtime client disconnected (session=%s)", session_id)
    except Exception as exc:
        logger.exception("Realtime websocket error: %s", exc)
    finally:
        # Cancel any in-flight utterance
        if pending_utterance and not pending_utterance.done():
            pending_utterance.cancel()
            try:
                await pending_utterance
            except (asyncio.CancelledError, Exception):
                pass
