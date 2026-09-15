"""Realtime voice WebSocket protocol (Phase 3C).

Wire contract for the ``/ws/voice/{session_id}`` endpoint.

Audio format (documented, single conversion boundary)
-----------------------------------------------------
* Input: PCM 16-bit signed little-endian mono @ 16 kHz (``pcm_s16le``). Sent as
  raw binary WebSocket frames. Converted once to ``float32 [-1, 1]`` for the
  VAD/STT adapters.
* Output: PCM 16-bit signed little-endian mono @ 24 kHz (Kokoro's native rate).
  Sent as raw binary WebSocket frames. The only format conversion is the final
  ``float32 -> pcm_s16le`` at the wire.

Control messages are JSON text frames. Envelopes::

    {"type": "...", ...fields}

Client -> server:  ``start``, ``audio`` (JSON/base64 variant), ``text``,
                   ``stop``, ``interrupt``
Server -> client:  ``ready``, ``state``, ``transcript_partial``,
                   ``transcript``, ``response``, ``audio`` (JSON/base64
                   variant), ``error``, ``done``

Raw 24 kHz audio is the preferred output transport (binary frames, lower
overhead); the ``audio`` JSON envelope (base64) exists for the text-oriented
test client. ``start``/``text`` may carry an optional ``path_incident_id`` so
follow-up turns can omit it and reuse the session's active incident.
"""

from __future__ import annotations

import base64
import enum
import json
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Formats.
# ---------------------------------------------------------------------------
INPUT_SAMPLE_RATE = 16000  # VAD / STT native rate, 1 channel.
OUTPUT_SAMPLE_RATE = 24000  # Kokoro native rate, 1 channel.

INPUT_FORMAT = "pcm_s16le"
OUTPUT_FORMAT = "pcm_s16le"

# Protocol limits (bytes). Oversize frames -> protocol error, connection kept.
MAX_CONTROL_MESSAGE_BYTES = 1 << 20  # 1 MiB of JSON control.
MAX_AUDIO_CHUNK_BYTES = 1 << 20  # 1 MiB of PCM per frame.
MAX_SESSION_ID_LEN = 128


class MessageType(str, enum.Enum):
    """All frames understood by the voice endpoint."""

    # client -> server
    START = "start"
    AUDIO = "audio"
    TEXT = "text"
    STOP = "stop"
    INTERRUPT = "interrupt"
    # server -> client
    READY = "ready"
    STATE = "state"
    TRANSCRIPT_PARTIAL = "transcript_partial"
    TRANSCRIPT = "transcript"
    RESPONSE = "response"
    DONE = "done"
    # client <-> server
    ERROR = "error"


class ErrorCode(str, enum.Enum):
    """Machine-readable error codes for the ``error`` envelope."""

    INVALID_MESSAGE = "invalid_message"
    AUDIO_FORMAT_ERROR = "audio_format_error"
    STT_ERROR = "stt_error"
    TTS_ERROR = "tts_error"
    CONVERSATION_ERROR = "conversation_error"
    SESSION_ERROR = "session_error"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


# ---------------------------------------------------------------------------
# PCM codec. s16le <-> float32.
# ---------------------------------------------------------------------------
def pcm16_to_float32(data: bytes) -> np.ndarray:
    """Decode raw s16le bytes into mono ``float32 [-1, 1]``."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise ValueError("audio payload must be bytes")
    i16 = np.frombuffer(data, dtype="<i2")
    return i16.astype(np.float32) / 32768.0


def float32_to_pcm16(audio: np.ndarray) -> bytes:
    """Encode mono ``float32 [-1, 1]`` audio into raw s16le bytes."""
    arr = np.asarray(audio, dtype=np.float32)
    clipped = np.clip(arr, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


def validate_audio_payload_size(payload: bytes) -> None:
    """Raise ``ValueError`` if the frame is empty or over the size limit."""
    if not payload:
        raise ValueError("empty audio payload")
    if len(payload) > MAX_AUDIO_CHUNK_BYTES:
        raise ValueError(f"audio chunk too large ({len(payload)} > {MAX_AUDIO_CHUNK_BYTES})")


# ---------------------------------------------------------------------------
# JSON envelopes.
# ---------------------------------------------------------------------------
def encode_message(msg_type: MessageType | str, **fields: Any) -> str:
    """Serialize a JSON control envelope (``audio`` uses base64 payload)."""
    envelope: dict[str, Any] = {"type": str(msg_type)}
    envelope.update(fields)
    return json.dumps(envelope, separators=(",", ":"))


def decode_message(raw: str) -> dict[str, Any]:
    """Decode a JSON text frame. Raises ``ValueError`` on bad JSON."""
    try:
        envelope = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"malformed JSON message: {exc}") from exc
    if not isinstance(envelope, dict):
        raise ValueError("message must be a JSON object")
    if "type" not in envelope or not isinstance(envelope["type"], str):
        raise ValueError("message missing a string 'type' field")
    return envelope


def encode_audio_event(
    *,
    generation_id: int | None,
    audio: np.ndarray,
    sample_rate: int = OUTPUT_SAMPLE_RATE,
) -> dict[str, Any]:
    """JSON/base64 ``audio`` envelope (for text-oriented consumers)."""
    return {
        "type": MessageType.AUDIO.value,
        "generation_id": generation_id,
        "format": OUTPUT_FORMAT,
        "sample_rate": sample_rate,
        "channels": 1,
        "data_base64": base64.b64encode(float32_to_pcm16(audio)).decode("ascii"),
    }


def decode_audio_event(envelope: dict[str, Any]) -> np.ndarray:
    """Decode the JSON/base64 ``audio`` envelope back to float32 audio."""
    payload = envelope.get("data_base64")
    if not isinstance(payload, str):
        raise ValueError("audio envelope missing 'data_base64'")
    try:
        raw = base64.b64decode(payload)
    except (ValueError, TypeError) as exc:
        raise ValueError("audio envelope has malformed base64") from exc
    return pcm16_to_float32(raw)


def build_ready(session_id: str, message_types: list[str]) -> dict[str, Any]:
    """Server greeting: negotiated formats, limits, supported message types."""
    return {
        "type": MessageType.READY.value,
        "session_id": session_id,
        "input": {"format": INPUT_FORMAT, "sample_rate": INPUT_SAMPLE_RATE, "channels": 1},
        "output": {"format": OUTPUT_FORMAT, "sample_rate": OUTPUT_SAMPLE_RATE, "channels": 1},
        "max_message_bytes": MAX_CONTROL_MESSAGE_BYTES,
        "max_audio_chunk_bytes": MAX_AUDIO_CHUNK_BYTES,
        "message_types": message_types,
    }


def validate_session_id(session_id: str) -> str | None:
    """Return ``None`` if valid, otherwise the reason it is invalid."""
    if not session_id:
        return "session_id must not be empty"
    if len(session_id) > MAX_SESSION_ID_LEN:
        return f"session_id too long (>{MAX_SESSION_ID_LEN})"
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(ch not in allowed for ch in session_id):
        return "session_id contains disallowed characters"
    return None


__all__ = [
    "ErrorCode",
    "INPUT_FORMAT",
    "INPUT_SAMPLE_RATE",
    "MAX_AUDIO_CHUNK_BYTES",
    "MAX_CONTROL_MESSAGE_BYTES",
    "MAX_SESSION_ID_LEN",
    "MessageType",
    "OUTPUT_FORMAT",
    "OUTPUT_SAMPLE_RATE",
    "build_ready",
    "decode_audio_event",
    "decode_message",
    "encode_audio_event",
    "encode_message",
    "float32_to_pcm16",
    "pcm16_to_float32",
    "validate_audio_payload_size",
    "validate_session_id",
]