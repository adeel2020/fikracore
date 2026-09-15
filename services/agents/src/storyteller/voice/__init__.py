"""Phase 3B + 3C — local and realtime voice.

Phase 3B (sequential): audio → VAD (Silero) → STT (faster-whisper) →
ConversationService → TTS (Kokoro) → audio.

Phase 3C (realtime, *new*): a WebSocket conversational interface
(``voice/websocket.py``) that streams audio incrementally through VAD →
incremental STT → ConversationService → sentence-chunked TTS with barge-in,
cooperative generation cancellation, stale-audio prevention, and latency
instrumentation.

Incident-agnostic: the pipeline never hard-codes an incident; it forwards an
optional ``path_incident_id`` to Phase 3A. Adapters are lazily initialized so
importing this package does not load any ML model.
"""

from . import realtime, websocket  # noqa: F401  (re-exported for programmatic use)
from .cancellation import Cancelled, CancellationToken, Generation, GenerationCounter
from .pipeline import DEFAULT_SAMPLE_RATE, VoicePipeline, VoiceResult
from .protocol import (
    ErrorCode,
    INPUT_FORMAT,
    INPUT_SAMPLE_RATE,
    MessageType,
    OUTPUT_FORMAT,
    OUTPUT_SAMPLE_RATE,
    build_ready,
    decode_message,
    encode_message,
    float32_to_pcm16,
    pcm16_to_float32,
    validate_session_id,
)
from .realtime import RealtimeVoicePipeline, RealtimeVoiceSession
from .session import VoiceSession
from .stt import (
    ElevenLabsSTT,
    FallbackSTT,
    FallbackStreamingSTT,
    STTAdapter,
    STTError,
    STTResult,
    StreamingSTTAdapter,
    create_stt,
    create_streaming_stt,
)
from .tts import (
    ElevenLabsTTS,
    FallbackTTS,
    FallbackStreamingTTS,
    KOKORO_SAMPLE_RATE,
    StreamingTTSAdapter,
    TTSAdapter,
    TTSError,
    TTSResult,
    create_streaming_tts,
    create_tts,
    split_sentences,
)
from .vad import (
    SILERO_CHUNK_SAMPLES,
    VAD_SAMPLE_RATE,
    VADAdapter,
    VADError,
    SileroVAD,
    SpeechEvent,
    create_vad,
)

__all__ = [
    "Cancelled",
    "CancellationToken",
    "DEFAULT_SAMPLE_RATE",
    "ElevenLabsSTT",
    "ElevenLabsTTS",
    "ErrorCode",
    "FallbackSTT",
    "FallbackStreamingSTT",
    "FallbackTTS",
    "FallbackStreamingTTS",
    "Generation",
    "GenerationCounter",
    "INPUT_FORMAT",
    "INPUT_SAMPLE_RATE",
    "KOKORO_SAMPLE_RATE",
    "MessageType",
    "OUTPUT_FORMAT",
    "OUTPUT_SAMPLE_RATE",
    "RealtimeVoicePipeline",
    "RealtimeVoiceSession",
    "SILERO_CHUNK_SAMPLES",
    "STTAdapter",
    "STTError",
    "STTResult",
    "SileroVAD",
    "SpeechEvent",
    "StreamingSTTAdapter",
    "StreamingTTSAdapter",
    "TTSAdapter",
    "TTSError",
    "TTSResult",
    "VAD_SAMPLE_RATE",
    "VADAdapter",
    "VADError",
    "VoicePipeline",
    "VoiceResult",
    "VoiceSession",
    "build_ready",
    "create_stt",
    "create_streaming_stt",
    "create_streaming_tts",
    "create_tts",
    "create_vad",
    "decode_message",
    "encode_message",
    "float32_to_pcm16",
    "pcm16_to_float32",
    "realtime",
    "split_sentences",
    "validate_session_id",
    "websocket",
]
