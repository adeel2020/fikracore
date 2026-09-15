"""Speech-to-text (STT) adapters.

Phase 3B: a thin adapter layer so the voice pipeline is model-agnostic. The
real backend is faster-whisper (CTranslate2 runtime — no PyTorch), imported
lazily inside ``init()``. The model loads its weights on ``init()`` (may
download on first use).
"""

from __future__ import annotations

import abc
import io
import logging
import os
import wave

import httpx
import numpy as np

logger = logging.getLogger(__name__)


class STTError(Exception):
    """STT backend unavailable or misused."""


class STTResult:
    __slots__ = ("text", "language", "duration", "segments")

    def __init__(
        self,
        text: str,
        language: str | None = None,
        duration: float = 0.0,
        segments: list[dict] | None = None,
    ) -> None:
        self.text = text
        self.language = language
        self.duration = duration
        self.segments = segments or []

    def __repr__(self) -> str:
        return f"STTResult(text={self.text!r}, language={self.language!r})"


def _is_non_retryable_provider_error(exc: Exception) -> bool:
    """Provider auth/policy errors should fail fast instead of loading local STT."""
    text = str(exc).lower()
    return any(
        token in text
        for token in ("401", "403", "unauthorized", "forbidden", "policy")
    )


class STTAdapter(abc.ABC):
    @abc.abstractmethod
    def init(self) -> None:
        """Load the backend model. Idempotent; may download weights."""

    @abc.abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        """Transcribe mono audio (float32 in [-1, 1]) to text."""


class FasterWhisperSTT(STTAdapter):
    """faster-whisper backend. Configurable via STT_* environment variables."""

    def __init__(
        self,
        *,
        model: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        language: str | None = None,
    ) -> None:
        self.model = model or os.environ.get("STT_MODEL", "small")
        self.device = device or os.environ.get("STT_DEVICE", "cpu")
        self.compute_type = compute_type or os.environ.get("STT_COMPUTE_TYPE", "int8")
        self.language = language or os.environ.get("STT_LANGUAGE") or None
        self._model_obj = None

    def init(self) -> None:
        if self._model_obj is not None:
            return
        try:
            from faster_whisper import WhisperModel  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            raise STTError(f"faster-whisper is unavailable: {exc}") from exc
        logger.info(
            "loading faster-whisper model=%s device=%s compute_type=%s",
            self.model,
            self.device,
            self.compute_type,
        )
        self._model_obj = WhisperModel(
            self.model, device=self.device, compute_type=self.compute_type
        )

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        if self._model_obj is None:
            raise STTError("STT is not initialized (call init() first)")
        audio = np.asarray(audio, dtype=np.float32)
        segments_iter, info = self._model_obj.transcribe(
            audio,
            language=self.language,
            vad_filter=False,
            beam_size=1,
        )
        text = " ".join(s.text.strip() for s in segments_iter if s.text and s.text.strip())
        return STTResult(
            text=text,
            language=info.language,
            duration=float(getattr(info, "duration", 0.0) or 0.0),
        )


def _float32_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    arr = np.asarray(audio, dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    pcm = (np.clip(arr, -1.0, 1.0) * 32767.0).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(int(sample_rate))
        wav.writeframes(pcm.tobytes())
    return buf.getvalue()


class ElevenLabsSTT(STTAdapter):
    """ElevenLabs speech-to-text adapter for final utterance transcription."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_id: str | None = None,
        language: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.model_id = model_id or os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v2")
        self.language = language or os.environ.get("STT_LANGUAGE") or None
        self.timeout_s = float(timeout_s or os.environ.get("ELEVENLABS_TIMEOUT_S", "30"))
        self._ready = False

    def init(self) -> None:
        if not self.api_key:
            raise STTError("ElevenLabs STT is not configured")
        self._ready = True

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        if not self._ready:
            self.init()
        duration = float(len(audio)) / float(sample_rate or 1)
        if len(audio) == 0 or duration < 0.3:
            return STTResult(text="", language=self.language, duration=duration)
        wav_bytes = _float32_to_wav_bytes(audio, sample_rate)
        data = {"model_id": self.model_id}
        if self.language:
            data["language_code"] = self.language
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": self.api_key or ""},
                    data=data,
                    files={"file": ("speech.wav", wav_bytes, "audio/wav")},
                )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            resp = getattr(exc, "response", None)
            status = getattr(resp, "status_code", None)
            detail = getattr(resp, "text", "")
            suffix = f" ({status}: {detail})" if detail else (f" ({status})" if status else "")
            raise STTError(f"ElevenLabs STT failed{suffix}") from exc
        text = str(payload.get("text") or "").strip()
        duration = float(len(audio)) / float(sample_rate or 1)
        return STTResult(text=text, language=self.language, duration=duration)


class FallbackSTT(STTAdapter):
    """One-shot STT with primary/fallback provider behavior."""

    def __init__(self, *, primary: STTAdapter, fallback: STTAdapter) -> None:
        self.primary = primary
        self.fallback = fallback
        self.active_provider = "primary"

    def init(self) -> None:
        try:
            self.primary.init()
            self.active_provider = "primary"
        except Exception as exc:  # noqa: BLE001
            logger.warning("primary STT unavailable, using fallback: %s", exc)
            self.fallback.init()
            self.active_provider = "fallback"

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> STTResult:
        if self.active_provider == "fallback":
            self.fallback.init()
            return self.fallback.transcribe(audio, sample_rate)
        try:
            self.primary.init()
            return self.primary.transcribe(audio, sample_rate)
        except Exception as exc:  # noqa: BLE001
            if _is_non_retryable_provider_error(exc):
                raise
            logger.warning("primary STT failed, retrying utterance with fallback: %s", exc)
            self.active_provider = "fallback"
            self.fallback.init()
            return self.fallback.transcribe(audio, sample_rate)


class StreamingSTTAdapter(abc.ABC):
    """Streaming/incremental STT interface (Phase 3C).

    A long-lived conversation feeds audio incrementally and receives partial
    (running) transcripts plus a single final transcript at utterance end. State
    is bounded by ``start``/``finalize``/``reset`` so a streamer can be reused
    across utterances. The heavy model object is shared; only the per-utterance
    buffer lives on the instance.
    """

    @abc.abstractmethod
    def start(self, *, sample_rate: int) -> None:
        """Begin a new utterance. Lazy-loads the backend on first use."""

    @abc.abstractmethod
    def accept_audio(self, audio: np.ndarray) -> None:
        """Append mono float32 audio to the running utterance."""

    @abc.abstractmethod
    def get_partial(self) -> str:
        """Return the best current (partial) transcript for the utterance."""

    @abc.abstractmethod
    def finalize(self) -> STTResult:
        """Transcribe the complete utterance; resets the buffer."""

    @abc.abstractmethod
    def reset(self) -> None:
        """Drop any in-progress utterance state (called between turns)."""


class IncrementalWhisperSTT(StreamingSTTAdapter):
    """Chunked/segment STT over a shared faster-whisper backend.

    **Streaming limitation (documented):** faster-whisper does not expose true
    token-level incremental decoding. This adapter performs *chunked/segment*
    inference: partials are produced by re-transcribing the accumulated buffer
    at most every ``partial_interval_ms`` of new audio, and the final transcript
    is a single transcription of the whole utterance. It is NOT token-streaming.

    The ``backend`` (a stateless-per-call ``STTAdapter``) may be shared across
    connections; the running buffer is per-instance so utterances stay isolated.
    """

    def __init__(
        self,
        *,
        backend: STTAdapter | None = None,
        sample_rate: int = 16000,
        partial_interval_ms: int = 600,
        min_partial_seconds: float = 0.4,
        **kwargs,
    ) -> None:
        self._backend = backend or FasterWhisperSTT(**kwargs)
        self.sample_rate = sample_rate
        self.partial_interval_ms = partial_interval_ms
        self._min_partial_samples = int(min_partial_seconds * sample_rate)
        self._buffers: list[np.ndarray] = []
        self._last_partial: str = ""
        self._partial_span = 0
        self._started = False

    # -- lifecycle ---------------------------------------------------------
    def start(self, *, sample_rate: int) -> None:
        self._backend.init()
        self.sample_rate = sample_rate
        self._min_partial_samples = int((self.partial_interval_ms / 1000.0) * sample_rate)
        self._buffers = []
        self._last_partial = ""
        self._partial_span = 0
        self._started = True

    def reset(self) -> None:
        self._buffers = []
        self._last_partial = ""
        self._partial_span = 0
        self._started = False

    # -- data --------------------------------------------------------------
    def accept_audio(self, audio: np.ndarray) -> None:
        if not self._started:
            self.start(sample_rate=self.sample_rate or 16000)
        arr = np.asarray(audio, dtype=np.float32)
        self._buffers.append(arr)

    def _total(self) -> int:
        return sum(len(b) for b in self._buffers)

    def get_partial(self) -> str:
        if not self._started:
            return ""
        total = self._total()
        if total - self._partial_span >= self._min_partial_samples:
            buf = self._snapshot()
            if len(buf) >= self._min_partial_samples:
                result = self._backend.transcribe(buf, self.sample_rate)
                self._last_partial = result.text.strip()
                self._partial_span = total
        return self._last_partial

    def finalize(self) -> STTResult:
        if not self._started:
            raise STTError("finalize called before start()")
        buf = self._snapshot()
        self.reset()
        if len(buf) == 0:
            result = STTResult(text="", language=None, duration=0.0)
        else:
            result = self._backend.transcribe(buf, self.sample_rate)
            result = STTResult(
                text=result.text.strip(),
                language=result.language,
                duration=result.duration,
            )
        return result

    def _snapshot(self) -> np.ndarray:
        if not self._buffers:
            return np.zeros(0, dtype=np.float32)
        if len(self._buffers) == 1:
            return self._buffers[0]
        return np.concatenate(self._buffers)


class FallbackStreamingSTT(StreamingSTTAdapter):
    """Final STT through primary provider with lazy local fallback."""

    def __init__(
        self,
        *,
        primary: STTAdapter,
        fallback: StreamingSTTAdapter,
        enable_fallback_partials: bool = False,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.enable_fallback_partials = enable_fallback_partials
        self.sample_rate = 16000
        self._buffers: list[np.ndarray] = []
        self._started = False
        self._fallback_ready = False
        self.active_provider = "primary"

    def start(self, *, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self._buffers = []
        self._started = True
        self._fallback_ready = False
        if self.enable_fallback_partials:
            self._start_fallback()

    def accept_audio(self, audio: np.ndarray) -> None:
        if not self._started:
            self.start(sample_rate=self.sample_rate or 16000)
        arr = np.asarray(audio, dtype=np.float32)
        self._buffers.append(arr)
        if self._fallback_ready:
            if not getattr(self.fallback, "_started", False):
                self.fallback.start(sample_rate=self.sample_rate)
            self.fallback.accept_audio(arr)

    def get_partial(self) -> str:
        if not self._fallback_ready:
            return ""
        return self.fallback.get_partial()

    def finalize(self) -> STTResult:
        if not self._started:
            raise STTError("finalize called before start()")
        audio = self._snapshot()
        buffered_chunks = list(self._buffers)
        self.reset()
        try:
            self.primary.init()
            result = self.primary.transcribe(audio, self.sample_rate)
            self.active_provider = "primary"
            return STTResult(
                text=result.text.strip(),
                language=result.language,
                duration=result.duration,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("primary STT failed, retrying utterance with fallback: %s", exc)
            self.active_provider = "fallback"
            if not self._fallback_ready:
                self._start_fallback()
                for chunk in buffered_chunks:
                    self.fallback.accept_audio(chunk)
            return self.fallback.finalize()

    def reset(self) -> None:
        self._buffers = []
        self._started = False
        if self._fallback_ready:
            self.fallback.reset()
        self._fallback_ready = False

    def _snapshot(self) -> np.ndarray:
        if not self._buffers:
            return np.zeros(0, dtype=np.float32)
        if len(self._buffers) == 1:
            return self._buffers[0]
        return np.concatenate(self._buffers)

    def _start_fallback(self) -> None:
        try:
            self.fallback.start(sample_rate=self.sample_rate)
            self._fallback_ready = True
        except Exception as exc:  # noqa: BLE001
            self._fallback_ready = False
            raise STTError("fallback STT is unavailable") from exc


def _provider(provider: str | None, env_name: str) -> str:
    return (provider or os.environ.get(env_name) or "auto").strip().lower()


def create_stt(**kwargs) -> STTAdapter:
    """Factory; uses ElevenLabs when configured and falls back to faster-whisper."""
    provider = _provider(kwargs.pop("provider", None), "VOICE_STT_PROVIDER")
    api_key = kwargs.pop("elevenlabs_api_key", None) or os.environ.get("ELEVENLABS_API_KEY")
    elevenlabs_stt_model = kwargs.pop("elevenlabs_stt_model", None)
    elevenlabs_timeout_s = kwargs.pop("elevenlabs_timeout_s", None)
    if provider in {"elevenlabs", "auto"} and api_key:
        fallback = FasterWhisperSTT(**kwargs)
        primary = ElevenLabsSTT(
            api_key=api_key,
            model_id=elevenlabs_stt_model,
            language=kwargs.get("language"),
            timeout_s=elevenlabs_timeout_s,
        )
        return FallbackSTT(primary=primary, fallback=fallback)
    if provider == "elevenlabs":
        raise STTError("VOICE_STT_PROVIDER=elevenlabs requires ELEVENLABS_API_KEY")
    return FasterWhisperSTT(**kwargs)


def create_streaming_stt(**kwargs) -> StreamingSTTAdapter:
    """Factory for realtime STT with ElevenLabs final transcript fallback."""
    provider = _provider(kwargs.pop("provider", None), "VOICE_STT_PROVIDER")
    api_key = kwargs.pop("elevenlabs_api_key", None) or os.environ.get("ELEVENLABS_API_KEY")
    elevenlabs_stt_model = kwargs.pop("elevenlabs_stt_model", None)
    elevenlabs_timeout_s = kwargs.pop("elevenlabs_timeout_s", None)
    local_backend = kwargs.pop("local_backend", None)
    if provider in {"elevenlabs", "auto"} and api_key:
        fallback = IncrementalWhisperSTT(
            backend=local_backend or FasterWhisperSTT(**kwargs)
        )
        primary = ElevenLabsSTT(
            api_key=api_key,
            model_id=elevenlabs_stt_model,
            language=kwargs.get("language"),
            timeout_s=elevenlabs_timeout_s,
        )
        return FallbackStreamingSTT(primary=primary, fallback=fallback)
    if provider == "elevenlabs":
        raise STTError("VOICE_STT_PROVIDER=elevenlabs requires ELEVENLABS_API_KEY")
    return IncrementalWhisperSTT(backend=local_backend, **kwargs)


__all__ = [
    "FasterWhisperSTT",
    "ElevenLabsSTT",
    "FallbackSTT",
    "FallbackStreamingSTT",
    "IncrementalWhisperSTT",
    "STTAdapter",
    "STTError",
    "STTResult",
    "StreamingSTTAdapter",
    "create_stt",
    "create_streaming_stt",
]
