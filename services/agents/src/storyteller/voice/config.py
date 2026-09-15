"""Realtime voice configuration (Phase 3D).

Centralizes the voice stack's deployment-facing settings behind the same
``pydantic-settings`` pattern used elsewhere in the service (see
``rag/config.py`` and ``agenticaiops_shared/config.py``). Every field maps to
an environment variable by name (case-insensitive), so there is exactly one
configuration system and nothing is hard-coded:

    VOICE_STT_PROVIDER, STT_MODEL, STT_DEVICE, STT_COMPUTE_TYPE, STT_LANGUAGE,
    VOICE_TTS_PROVIDER, TTS_MODEL, TTS_VOICE, TTS_SPEED, TTS_DEVICE,
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL,
    ELEVENLABS_STT_MODEL, VOICE_TORCH_THREADS,
    VOICE_WARMUP,
    VOICE_VAD_THRESHOLD, VOICE_VAD_MIN_SILENCE_MS, VOICE_VAD_SPEECH_PAD_MS,
    VOICE_MAX_UTTERANCE_SECONDS, VOICE_MAX_TURN_MS,
    VOICE_MAX_CONCURRENT_SESSIONS, VOICE_IDLE_TIMEOUT_S, VOICE_OUT_QUEUE_SIZE

The adapters themselves still accept explicit constructor kwargs (and keep their
env-var fallbacks) so tests and direct use remain unchanged; the WebSocket
endpoint derives its adapter + resource settings from this object.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[5]


class VoiceSettings(BaseSettings):
    """Env-driven settings for the realtime voice stack."""

    model_config = SettingsConfigDict(
        env_file=(
            str(Path.cwd() / ".env"),
            str(_REPO_ROOT / "backend" / ".env"),
            str(_REPO_ROOT / "shared" / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- STT -------------------------------------------------------------
    voice_stt_provider: str = "auto"  # auto | local | elevenlabs
    stt_model: str = "small"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    stt_language: str | None = None

    # ---- TTS -------------------------------------------------------------
    voice_tts_provider: str = "auto"  # auto | local | elevenlabs
    tts_model: str = "hexgrad/Kokoro-82M"
    tts_voice: str = "af_heart"
    tts_speed: float = 0.86
    tts_device: str = "cpu"

    # ---- ElevenLabs primary provider ------------------------------------
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_stt_model: str = "scribe_v2"
    elevenlabs_timeout_s: float = 30.0
    elevenlabs_tts_output_format: str = "pcm_24000"

    # ---- Runtime / CPU threading (Phase 3E) --------------------------------
    # torch intra-op thread count for Kokoro inference. Applied via
    # ``torch.set_num_threads`` so it never requires ``OMP_NUM_THREADS > 1``
    # (which would deadlock CTranslate2/faster-whisper when both runtimes load).
    voice_torch_threads: int = 4
    # Eagerly load the shared VAD/STT/TTS backends on app startup so the first
    # real connection is not cold. Off by default because it holds model RAM in
    # the app process from boot; enable with VOICE_WARMUP=1 where desired.
    voice_warmup: bool = False

    # ---- VAD (Silero) -----------------------------------------------------
    voice_vad_threshold: float = 0.70
    voice_vad_min_silence_ms: int = 1500
    voice_vad_speech_pad_ms: int = 100
    voice_vad_energy_threshold: float = 0.01

    # ---- Resource protection ----------------------------------------------
    # Longest single utterance accepted (seconds of 16 kHz audio).
    voice_max_utterance_seconds: float = 30.0
    # Hard cap on one turn's total wall-clock time (ms), including TTS.
    voice_max_turn_ms: int = 120_000
    # Maximum concurrently active WebSocket voice sessions.
    voice_max_concurrent_sessions: int = 16
    # Close a voice connection after this many seconds of client inactivity.
    voice_idle_timeout_s: int = 900
    # Bounded sender queue (JSON + audio frames); a full queue drops audio.
    voice_out_queue_size: int = 256


@lru_cache(maxsize=1)
def get_voice_settings() -> VoiceSettings:
    """Return the process-wide voice settings (cached, env-read once)."""
    return VoiceSettings()


__all__ = ["VoiceSettings", "get_voice_settings"]
