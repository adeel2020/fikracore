"""Text-to-speech (TTS) adapters.

Phase 3B: a thin adapter layer so the voice pipeline is model-agnostic. The
real backend is Kokoro (``kokoro``), imported lazily inside ``init()``.
Kokoro requires PyTorch; we pin ``torch<=2.2.1`` (see services/pyproject.toml
``voice`` extra) and ``transformers<5`` so the torch backend stays enabled.
The model loads its weights on ``init()`` (may download on first use).

Kokoro synthesizes 24 kHz mono float32 audio.
"""

from __future__ import annotations

import abc
import contextlib
import logging
import os
import threading

import httpx
import numpy as np

logger = logging.getLogger(__name__)

KOKORO_SAMPLE_RATE = 24000


class TTSError(Exception):
    """TTS backend unavailable or misused."""


class TTSResult:
    __slots__ = ("audio", "sample_rate", "text", "duration")

    def __init__(
        self,
        audio: np.ndarray,
        sample_rate: int,
        text: str,
        duration: float = 0.0,
    ) -> None:
        self.audio = audio
        self.sample_rate = sample_rate
        self.text = text
        self.duration = duration

    def __repr__(self) -> str:
        return f"TTSResult(audio={self.audio.shape}, sample_rate={self.sample_rate})"


class TTSAdapter(abc.ABC):
    sample_rate: int = KOKORO_SAMPLE_RATE

    @abc.abstractmethod
    def init(self) -> None:
        """Load the backend model. Idempotent; may download weights."""

    @abc.abstractmethod
    def synthesize(self, text: str) -> TTSResult:
        """Synthesize mono float32 audio for the given text."""


class KokoroTTS(TTSAdapter):
    """Kokoro backend. Configurable via TTS_* environment variables."""

    sample_rate = KOKORO_SAMPLE_RATE

    def __init__(
        self,
        *,
        model: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        device: str | None = None,
    ) -> None:
        self.model = model or os.environ.get("TTS_MODEL", "hexgrad/Kokoro-82M")
        self.voice = voice or os.environ.get("TTS_VOICE", "af_heart")
        self.speed = float(speed if speed is not None else os.environ.get("TTS_SPEED", "0.86"))
        self.device = device or os.environ.get("TTS_DEVICE", "cpu")
        self._pipeline = None
        # Serialize synthesis on the shared model. Kokoro's KModel is
        # ``torch.no_grad()`` and allocates fresh tensors per call, but torch CPU
        # parallelism is not documented as re-entrant, so concurrent sessions
        # share this one model through a single-worker lock (bounded
        # concurrency = 1). Generated audio still drains/sends concurrently via
        # the async out-queue; only model inference is serialized.
        self._lock = threading.Lock()

    def init(self) -> None:
        if self._pipeline is not None:
            return
        # Apply the process runtime config (torch intra-op threads) before the
        # model loads so the first inference benefits. Idempotent.
        from .runtime import configure_runtime  # noqa: PLC0415

        configure_runtime()
        try:
            from kokoro import KPipeline  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            raise TTSError(f"Kokoro is unavailable: {exc}") from exc
        logger.info(
            "loading kokoro model=%s voice=%s speed=%s device=%s",
            self.model,
            self.voice,
            self.speed,
            self.device,
        )
        self._pipeline = KPipeline(
            lang_code="a", repo_id=self.model, device=self.device
        )

    def synthesize(self, text: str) -> TTSResult:
        if self._pipeline is None:
            raise TTSError("TTS is not initialized (call init() first)")
        chunks: list[np.ndarray] = []
        for result in self._pipeline(text, voice=self.voice, speed=self.speed):
            if result.audio is None:
                continue
            audio = np.asarray(result.audio.detach().cpu().numpy(), dtype=np.float32)
            audio = np.ascontiguousarray(audio)
            chunks.append(audio)
        if not chunks:
            raise TTSError("Kokoro produced no audio for the given text")
        audio = np.concatenate(chunks)
        return TTSResult(
            audio=audio,
            sample_rate=self.sample_rate,
            text=text,
            duration=float(len(audio)) / float(self.sample_rate),
        )

    def synthesize(self, text: str) -> TTSResult:
        if self._pipeline is None:
            raise TTSError("TTS is not initialized (call init() first)")
        # Single-worker guard: serialize model inference across all sessions
        # sharing this backend (bounded concurrency = 1, model-safe).
        with self._lock:
            return self._synthesize_locked(text)

    def _synthesize_locked(self, text: str) -> TTSResult:
        chunks: list[np.ndarray] = []
        for result in self._pipeline(text, voice=self.voice, speed=self.speed):
            if result.audio is None:
                continue
            audio = np.asarray(result.audio.detach().cpu().numpy(), dtype=np.float32)
            audio = np.ascontiguousarray(audio)
            chunks.append(audio)
        if not chunks:
            raise TTSError("Kokoro produced no audio for the given text")
        audio = np.concatenate(chunks)
        return TTSResult(
            audio=audio,
            sample_rate=self.sample_rate,
            text=text,
            duration=float(len(audio)) / float(self.sample_rate),
        )

    def synthesize_stream(self, text: str):
        if self._pipeline is None:
            raise TTSError("TTS is not initialized (call init() first)")
        with self._lock:
            for result in self._pipeline(text, voice=self.voice, speed=self.speed):
                if result.audio is None:
                    continue
                audio = np.asarray(result.audio.detach().cpu().numpy(), dtype=np.float32)
                audio = np.ascontiguousarray(audio)
                if audio.size > 0:
                    yield TTSResult(
                        audio=audio,
                        sample_rate=self.sample_rate,
                        text=text,
                        duration=float(len(audio)) / float(self.sample_rate),
                    )


def _sample_rate_from_output_format(output_format: str) -> int:
    if output_format.startswith("pcm_"):
        with contextlib.suppress(ValueError, IndexError):
            return int(output_format.split("_", 1)[1])
    return KOKORO_SAMPLE_RATE


def _is_non_retryable_provider_error(exc: Exception) -> bool:
    """Provider auth/policy errors should fail fast instead of loading local TTS."""
    text = str(exc).lower()
    return any(
        token in text
        for token in ("401", "403", "unauthorized", "forbidden", "policy")
    )


class ElevenLabsTTS(TTSAdapter):
    """ElevenLabs TTS adapter returning raw PCM for the realtime voice socket."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        voice_id: str | None = None,
        model_id: str | None = None,
        output_format: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        self.model_id = model_id or os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.output_format = output_format or os.environ.get("ELEVENLABS_TTS_OUTPUT_FORMAT", "pcm_24000")
        self.timeout_s = float(timeout_s or os.environ.get("ELEVENLABS_TIMEOUT_S", "30"))
        self.sample_rate = _sample_rate_from_output_format(self.output_format)
        self._ready = False

    def init(self) -> None:
        if not self.api_key:
            raise TTSError("ElevenLabs TTS is not configured")
        self._ready = True

    def synthesize(self, text: str) -> TTSResult:
        if not self._ready:
            self.init()
        if not text or not text.strip():
            raise TTSError("ElevenLabs TTS requires non-empty text")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        params = {"output_format": self.output_format}
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.58,
                "similarity_boost": 0.78,
                "style": 0.16,
                "use_speaker_boost": True,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(
                    url,
                    params=params,
                    headers={
                        "xi-api-key": self.api_key or "",
                        "accept": "application/octet-stream",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            status = getattr(getattr(exc, "response", None), "status_code", None)
            suffix = f" ({status})" if status else ""
            raise TTSError(f"ElevenLabs TTS failed{suffix}") from exc
        pcm = np.frombuffer(response.content, dtype="<i2").astype(np.float32) / 32768.0
        if pcm.size == 0:
            raise TTSError("ElevenLabs produced no audio")
        audio = np.ascontiguousarray(pcm)
        return TTSResult(
            audio=audio,
            sample_rate=self.sample_rate,
            text=text,
            duration=float(len(audio)) / float(self.sample_rate or 1),
        )

    def synthesize_stream(self, text: str):
        if not self._ready:
            self.init()
        if not text or not text.strip():
            raise TTSError("ElevenLabs TTS requires non-empty text")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"
        params = {"output_format": self.output_format}
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.58,
                "similarity_boost": 0.78,
                "style": 0.16,
                "use_speaker_boost": True,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                with client.stream(
                    "POST",
                    url,
                    params=params,
                    headers={
                        "xi-api-key": self.api_key or "",
                        "accept": "application/octet-stream",
                        "content-type": "application/json",
                    },
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    leftover = b""
                    for raw_chunk in response.iter_bytes(chunk_size=4096):
                        if not raw_chunk:
                            continue
                        chunk_bytes = leftover + raw_chunk
                        if len(chunk_bytes) % 2 != 0:
                            leftover = chunk_bytes[-1:]
                            chunk_bytes = chunk_bytes[:-1]
                        else:
                            leftover = b""
                        if not chunk_bytes:
                            continue
                        pcm = np.frombuffer(chunk_bytes, dtype="<i2").astype(np.float32) / 32768.0
                        if pcm.size > 0:
                            yield TTSResult(
                                audio=np.ascontiguousarray(pcm),
                                sample_rate=self.sample_rate,
                                text=text,
                                duration=float(len(pcm)) / float(self.sample_rate or 1),
                            )
        except Exception as exc:  # noqa: BLE001
            resp = getattr(exc, "response", None)
            status = getattr(resp, "status_code", None)
            detail = ""
            if resp is not None:
                with contextlib.suppress(Exception):
                    detail = resp.read().decode("utf-8", errors="replace")
            suffix = f" ({status}: {detail})" if detail else (f" ({status})" if status else "")
            raise TTSError(f"ElevenLabs TTS streaming failed{suffix}") from exc


class StreamingTTSAdapter(abc.ABC):
    """Streaming/sentence-chunked TTS interface (Phase 3C).

    A response is synthesized piecewise so audio can start flowing before the
    whole answer is ready and so a turn can be stopped mid-way on barge-in.
    ``synthesize_chunk`` returns audio for one sentence (or ``None`` if the
    backend produced nothing); the caller chunks the answer text via
    :func:`split_sentences`.
    """

    @abc.abstractmethod
    def start(self, *, sample_rate: int) -> None:
        """Prepare for a new streamed response. Lazy-loads the backend."""

    @abc.abstractmethod
    def synthesize_chunk(self, text: str) -> TTSResult | None:
        """Synthesize one sentence chunk into audio (or ``None``)."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Release any per-response resources."""


class ChunkedKokoroTTS(StreamingTTSAdapter):
    """Kokoro backend, sentence-chunked.

    **Streaming limitation (documented):** Kokoro does not expose phoneme/token
    streaming across a TTS lifetime. This adapter chunks the *answer text* into
    sentences and synthesizes each independently (sentence-level streaming, not
    token-level). The ``backend`` (stateless per ``synthesize`` call) may be
    shared across connections.
    """

    sample_rate = KOKORO_SAMPLE_RATE

    def __init__(
        self,
        *,
        backend: TTSAdapter | None = None,
        **kwargs,
    ) -> None:
        self._backend = backend or KokoroTTS(**kwargs)
        self.sample_rate = KOKORO_SAMPLE_RATE
        self._started = False

    def start(self, *, sample_rate: int) -> None:
        self._backend.init()
        self.sample_rate = sample_rate or KOKORO_SAMPLE_RATE
        self._started = True

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        if not self._started:
            raise TTSError("synthesize_chunk called before start()")
        if not text or not text.strip():
            return None
        result = self._backend.synthesize(text)
        if result.audio is None or result.audio.size == 0:
            return None
        return result

    def synthesize_stream(self, text: str):
        if not self._started:
            raise TTSError("synthesize_stream called before start()")
        if not text or not text.strip():
            return
        if hasattr(self._backend, "synthesize_stream"):
            yield from self._backend.synthesize_stream(text)
        else:
            res = self.synthesize_chunk(text)
            if res is not None:
                yield res

    def stop(self) -> None:
        self._started = False


class FallbackTTS(TTSAdapter):
    """One-shot TTS with primary/fallback provider behavior."""

    def __init__(self, *, primary: TTSAdapter, fallback: TTSAdapter) -> None:
        self.primary = primary
        self.fallback = fallback
        self.sample_rate = getattr(primary, "sample_rate", KOKORO_SAMPLE_RATE)
        self.active_provider = "primary"

    def init(self) -> None:
        try:
            self.primary.init()
            self.active_provider = "primary"
            self.sample_rate = getattr(self.primary, "sample_rate", KOKORO_SAMPLE_RATE)
        except Exception as exc:  # noqa: BLE001
            logger.warning("primary TTS unavailable, using fallback: %s", exc)
            self.fallback.init()
            self.active_provider = "fallback"
            self.sample_rate = getattr(self.fallback, "sample_rate", KOKORO_SAMPLE_RATE)

    def synthesize(self, text: str) -> TTSResult:
        if self.active_provider == "fallback":
            self.fallback.init()
            return self.fallback.synthesize(text)
        try:
            self.primary.init()
            result = self.primary.synthesize(text)
            self.sample_rate = result.sample_rate
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("primary TTS failed, retrying response with fallback: %s", exc)
            self.active_provider = "fallback"
            self.fallback.init()
            result = self.fallback.synthesize(text)
            self.sample_rate = result.sample_rate
            return result


class FallbackStreamingTTS(StreamingTTSAdapter):
    """Response-level TTS fallback so a spoken answer keeps one voice/provider."""

    def __init__(self, *, primary: TTSAdapter, fallback: TTSAdapter) -> None:
        self.primary = primary
        self.fallback = fallback
        self.sample_rate = getattr(primary, "sample_rate", KOKORO_SAMPLE_RATE)
        self._started = False
        self.active_provider = "primary"

    def start(self, *, sample_rate: int) -> None:
        self.sample_rate = sample_rate or self.sample_rate
        self._started = True

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        if not self._started:
            raise TTSError("synthesize_chunk called before start()")
        if not text or not text.strip():
            return None
        if self.active_provider == "fallback":
            self.fallback.init()
            res = self.fallback.synthesize(text)
            self.sample_rate = res.sample_rate
            return res
        try:
            self.primary.init()
            res = self.primary.synthesize(text)
            self.active_provider = "primary"
            self.sample_rate = res.sample_rate
            return res
        except Exception as exc:  # noqa: BLE001
            if _is_non_retryable_provider_error(exc):
                raise
            logger.warning("primary TTS failed on chunk, switching to fallback: %s", exc)
            self.active_provider = "fallback"
            self.fallback.init()
            res = self.fallback.synthesize(text)
            self.sample_rate = res.sample_rate
            return res

    def synthesize_stream(self, text: str):
        if not self._started:
            raise TTSError("synthesize_stream called before start()")
        if not text or not text.strip():
            return
        if self.active_provider == "fallback":
            self.fallback.init()
            if hasattr(self.fallback, "synthesize_stream"):
                for chunk in self.fallback.synthesize_stream(text):
                    self.sample_rate = chunk.sample_rate
                    yield chunk
            else:
                res = self.fallback.synthesize(text)
                self.sample_rate = res.sample_rate
                yield res
            return
        try:
            self.primary.init()
            if hasattr(self.primary, "synthesize_stream"):
                for chunk in self.primary.synthesize_stream(text):
                    self.active_provider = "primary"
                    self.sample_rate = chunk.sample_rate
                    yield chunk
            else:
                res = self.primary.synthesize(text)
                self.active_provider = "primary"
                self.sample_rate = res.sample_rate
                yield res
        except Exception as exc:  # noqa: BLE001
            if _is_non_retryable_provider_error(exc):
                raise
            logger.warning("primary TTS streaming failed, switching to fallback: %s", exc)
            self.active_provider = "fallback"
            self.fallback.init()
            if hasattr(self.fallback, "synthesize_stream"):
                for chunk in self.fallback.synthesize_stream(text):
                    self.sample_rate = chunk.sample_rate
                    yield chunk
            else:
                res = self.fallback.synthesize(text)
                self.sample_rate = res.sample_rate
                yield res

    def synthesize_response_chunks(self, texts: list[str]) -> list[TTSResult]:
        clean = [text for text in texts if text and text.strip()]
        if not clean:
            return []
        chunks = []
        for text in clean:
            c = self.synthesize_chunk(text)
            if c is not None:
                chunks.append(c)
        return chunks

    def stop(self) -> None:
        self._started = False


_SENTENCE_END = (".", "!", "?", "\n")


def split_sentences(text: str, *, max_chars: int = 400) -> list[str]:
    """Split answer text into TTS-sized sentence chunks.

    Splits on sentence boundaries (``.``/``!``/``?``) and newlines, then
    hard-wraps any sentence longer than ``max_chars`` so an extremely long
    sentence is synthesized in pieces rather than one giant call. Whitespace is
    trimmed and empty chunks are dropped.
    """
    import re  # noqa: PLC0415

    if not text:
        return []
    chunks: list[str] = []
    for part in re.split(r"(?<=[.!?])\s*", text.strip()):
        for segment in part.split("\n"):
            segment = segment.strip()
            if not segment:
                continue
            while len(segment) > max_chars:
                chunks.append(segment[:max_chars].rstrip())
                segment = segment[max_chars:].strip()
            if segment:
                chunks.append(segment)
    return chunks


def _provider(provider: str | None, env_name: str) -> str:
    return (provider or os.environ.get(env_name) or "auto").strip().lower()


def create_tts(**kwargs) -> TTSAdapter:
    """Factory; uses ElevenLabs when configured and falls back to Kokoro."""
    provider = _provider(kwargs.pop("provider", None), "VOICE_TTS_PROVIDER")
    api_key = kwargs.pop("elevenlabs_api_key", None) or os.environ.get("ELEVENLABS_API_KEY")
    voice_id = kwargs.pop("elevenlabs_voice_id", None)
    model_id = kwargs.pop("elevenlabs_model", None)
    output_format = kwargs.pop("elevenlabs_tts_output_format", None)
    timeout_s = kwargs.pop("elevenlabs_timeout_s", None)
    if provider in {"elevenlabs", "auto"} and api_key:
        return FallbackTTS(
            primary=ElevenLabsTTS(
                api_key=api_key,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                timeout_s=timeout_s,
            ),
            fallback=KokoroTTS(**kwargs),
        )
    if provider == "elevenlabs":
        raise TTSError("VOICE_TTS_PROVIDER=elevenlabs requires ELEVENLABS_API_KEY")
    return KokoroTTS(**kwargs)


def create_streaming_tts(**kwargs) -> StreamingTTSAdapter:
    """Factory for realtime TTS with response-level ElevenLabs fallback."""
    provider = _provider(kwargs.pop("provider", None), "VOICE_TTS_PROVIDER")
    api_key = kwargs.pop("elevenlabs_api_key", None) or os.environ.get("ELEVENLABS_API_KEY")
    voice_id = kwargs.pop("elevenlabs_voice_id", None)
    model_id = kwargs.pop("elevenlabs_model", None)
    output_format = kwargs.pop("elevenlabs_tts_output_format", None)
    timeout_s = kwargs.pop("elevenlabs_timeout_s", None)
    local_backend = kwargs.pop("local_backend", None)
    if provider in {"elevenlabs", "auto"} and api_key:
        return FallbackStreamingTTS(
            primary=ElevenLabsTTS(
                api_key=api_key,
                voice_id=voice_id,
                model_id=model_id,
                output_format=output_format,
                timeout_s=timeout_s,
            ),
            fallback=local_backend or KokoroTTS(**kwargs),
        )
    if provider == "elevenlabs":
        raise TTSError("VOICE_TTS_PROVIDER=elevenlabs requires ELEVENLABS_API_KEY")
    return ChunkedKokoroTTS(backend=local_backend, **kwargs)


__all__ = [
    "ChunkedKokoroTTS",
    "ElevenLabsTTS",
    "FallbackTTS",
    "FallbackStreamingTTS",
    "KOKORO_SAMPLE_RATE",
    "KokoroTTS",
    "StreamingTTSAdapter",
    "TTSAdapter",
    "TTSError",
    "TTSResult",
    "create_streaming_tts",
    "create_tts",
    "split_sentences",
]
