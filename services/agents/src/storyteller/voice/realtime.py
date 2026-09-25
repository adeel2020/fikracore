"""Realtime conversational voice pipeline (Phase 3C).

Pushes streaming audio through VAD -> incremental STT -> ConversationService ->
sentence-chunked TTS while supporting barge-in (new speech cancels the in-flight
reply), per-turn cooperative cancellation, stale-audio prevention via
monotonic generation ids, and end-to-end latency instrumentation.

Voice is ONLY an interface to the existing ``ConversationService``: there is no
second reasoning engine, incident memory, gbrain client, or AMF-specific code
here. Generic incidents (``incident-A``/``incident-B``) flow through unchanged.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import threading
import time

import numpy as np

from ..conversation.service import (
    ConversationError,
    ConversationService,
    IncidentContextRequired,
    IncidentNotFound,
)
from .cancellation import Cancelled, Generation, GenerationCounter
from .protocol import ErrorCode, INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE
from .session import VoiceSession
from .stt import StreamingSTTAdapter
from .tts import StreamingTTSAdapter, split_sentences
from .vad import VADAdapter, SILERO_CHUNK_SAMPLES

logger = logging.getLogger(__name__)


class RealtimeVoiceSession(VoiceSession):
    """Voice session plus per-connection realtime state (mirrors ``VoiceSession``)."""

    active_generation_id: int | None = None
    active_tts_id: int | None = None
    connection_state: str = "idle"  # idle | listening | processing | speaking


class RealtimeVoicePipeline:
    """Streaming turn engine.

    All heavy ML work (STT transcribe, conversation, TTS synth) is offloaded to
    worker threads and gated by a cooperative :class:`CancellationToken`, so a
    barge-in cancels the in-flight reply without leaking state. Adapters are
    injected so tests use fakes with no model downloads.
    """

    def __init__(
        self,
        *,
        vad: VADAdapter,
        stt: StreamingSTTAdapter,
        tts: StreamingTTSAdapter,
        conversation: ConversationService,
        session_id: str = "realtime-default",
        path_incident_id: str | None = None,
        emit=None,
        partial_interval_ms: int = 600,
        max_turn_ms: int | None = None,
        max_utterance_samples: int | None = None,
    ) -> None:
        self.vad = vad
        self.stt = stt
        self.tts = tts
        self.conversation = conversation
        self.session_id = session_id
        self.session = RealtimeVoiceSession(
            conversation=conversation, session_id=session_id
        )
        self._path_incident_id = path_incident_id
        self._partial_interval_ms = partial_interval_ms
        self._emit = emit or self._noop_emit

        # Resource protection (Phase 3D). ``None`` disables the guard.
        self._max_turn_ms = max_turn_ms
        self._max_utterance_samples = max_utterance_samples

        self._generations = GenerationCounter()
        self._current_generation: Generation | None = None
        self._turn_task: asyncio.Task | None = None

        # Streaming state (per connection).
        self._speech_active = False
        self._processing = False
        self._tts_active = False
        self._vad_ready = False
        self._stt_started = False
        self._vad_buf: np.ndarray | None = None
        self._speech_start_at: float = 0.0
        self._speech_end_at: float = 0.0
        self._speech_samples = 0
        self._last_partial_at: float = 0.0
        self._vad_ms: float = 0.0

        # Latency markers (Phase 3D) — absolute perf_counter times, reset per
        # generation. Only set when the corresponding event actually happens.
        self._audio_received_at: float | None = None
        self._transcript_at: float | None = None
        self._first_audio_at: float | None = None

    # ------------------------------------------------------------------
    # Externally driven entry points.
    # ------------------------------------------------------------------
    async def begin_generation(
        self, *, path_incident_id: str | None = None
    ) -> Generation:
        """Explicitly start a fresh turn (client ``start`` message / text)."""
        await self.interrupt()
        if path_incident_id is not None:
            self._path_incident_id = path_incident_id
        self._ensure_vad()
        gen = self._generations.next()
        self._current_generation = gen
        self.session.active_generation_id = gen.id
        self.stt.start(sample_rate=INPUT_SAMPLE_RATE)
        self._stt_started = True
        self._speech_start_at = time.perf_counter()
        self._reset_markers()
        return gen

    async def submit_text(self, text: str, *, path_incident_id: str | None = None) -> None:
        """Drive a full text turn: transcript -> answer -> TTS -> done."""
        gen = await self.begin_generation(path_incident_id=path_incident_id)
        await self._emit_state("processing")
        await self.emit_generation(gen, "transcript", text=text)
        self._transcript_at = time.perf_counter()
        try:
            await self._answer(gen, text)
        except Cancelled:
            return

    async def accept_audio(self, audio: np.ndarray) -> None:
        """Feed one PCM float32 frame (mono 16 kHz). Drives VAD/STT/barge-in."""
        self._ensure_vad()
        audio = np.asarray(audio, dtype=np.float32)
        # Resource protection: cap the accepted utterance length. Once the cap
        # is reached, force the current utterance to end (final STT -> answer).
        if self._speech_active and self._max_utterance_samples is not None:
            if self._speech_samples >= self._max_utterance_samples:
                gen = self._current_generation
                if gen is not None and not self._processing:
                    self._speech_active = False
                    self._speech_end_at = time.perf_counter()
                    self._spawn(self._process_audio_turn(gen))
                return
            self._speech_samples += len(audio)
        events = self._feed_vad(audio)
        for event in events:
            if event.kind == "start":
                await self._on_speech_start()
            elif event.kind == "end" and self._speech_active:
                self._speech_active = False
                gen = self._current_generation
                if gen is not None:
                    self._speech_end_at = time.perf_counter()
                    self._spawn(self._process_audio_turn(gen))
        if self._speech_active and self._current_generation is not None:
            if self._audio_received_at is None:
                self._audio_received_at = time.perf_counter()
            if not self._stt_started:
                self.stt.start(sample_rate=INPUT_SAMPLE_RATE)
                self._stt_started = True
            self.stt.accept_audio(audio)
            await self._maybe_partial()

    async def interrupt(self, *, barged_at: float | None = None) -> None:
        """Cancel the active turn (barge-in, client ``interrupt``, disconnect)."""
        gen = self._current_generation
        if gen is not None:
            await self._emit({"type": "interrupted", "generation_id": gen.id})
            if barged_at is not None:
                gen.timings["barge_in_to_tts_stopped_ms"] = max(
                    0.0, (time.perf_counter() - barged_at) * 1000.0
                )
            gen.cancel()
            logger.info(
                "voice turn interrupted session=%s generation=%d interrupted=%s",
                self.session_id,
                gen.id,
                True,
            )
        self._tts_active = False
        self._processing = False
        self._speech_active = False
        self.session.active_tts_id = None
        self.tts.stop()
        task, self._turn_task = self._turn_task, None
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self.stt.reset()
        self._stt_started = False
        self.vad.reset()
        self._vad_buf = None
        await self._emit_state("idle")

    async def close(self) -> None:
        """Full teardown on disconnect."""
        await self.interrupt()

    async def emit_generation(self, gen: Generation, kind: str, **fields) -> None:
        """Emit an event tagged with the generation (for stale-audio filtering)."""
        fields.setdefault("generation_id", gen.id)
        if kind == "transcript_partial":
            gen.meta["last_partial"] = fields.get("text", "")
        await self._emit({"type": kind, **fields})

    # ------------------------------------------------------------------
    # Internals: VAD feed.
    # ------------------------------------------------------------------
    def _ensure_vad(self) -> None:
        if not self._vad_ready:
            self.vad.init()
            self._vad_ready = True

    def _feed_vad(self, chunk: np.ndarray) -> list:
        if self._vad_buf is None:
            self._vad_buf = np.zeros(0, dtype=np.float32)
        self._vad_buf = np.concatenate([self._vad_buf, chunk])
        events: list = []
        while len(self._vad_buf) >= SILERO_CHUNK_SAMPLES:
            piece = self._vad_buf[:SILERO_CHUNK_SAMPLES]
            self._vad_buf = self._vad_buf[SILERO_CHUNK_SAMPLES:]
            t0 = time.perf_counter()
            event = self.vad.process(piece)
            self._vad_ms += (time.perf_counter() - t0) * 1000.0
            if event is not None:
                events.append(event)
        return events

    async def _on_speech_start(self) -> None:
        if self._tts_active or self._processing:
            await self.interrupt(barged_at=time.perf_counter())
        self._ensure_vad()
        gen = self._generations.next()
        self._current_generation = gen
        self.session.active_generation_id = gen.id
        self._speech_active = True
        self._speech_start_at = time.perf_counter()
        self._speech_samples = 0
        self._last_partial_at = 0.0
        self._reset_markers()
        # Do NOT reset the VAD iterator here: Silero needs its streaming state
        # to stay intact after emitting ``start`` so it can later emit the
        # matching ``end``. Resetting here made a real Silero VAD re-detect the
        # same speech as repeated ``start`` events (a livelock on real audio).
        self.stt.start(sample_rate=INPUT_SAMPLE_RATE)
        self._stt_started = True
        await self._emit_state("listening")

    async def _maybe_partial(self) -> None:
        gen = self._current_generation
        if gen is None:
            return
        now = time.perf_counter()
        if now - self._last_partial_at < self._partial_interval_ms / 1000.0:
            return
        self._last_partial_at = now
        try:
            text = (await asyncio.to_thread(self.stt.get_partial)).strip()
        except Exception:  # noqa: BLE001 - partials are best-effort
            return
        if text and text != gen.meta.get("last_partial"):
            gen.timings["stt_first_partial_ms"] = (
                max(0.0, now - self._speech_start_at) * 1000.0
            )
            await self.emit_generation(gen, "transcript_partial", text=text)

    # ------------------------------------------------------------------
    # Internals: audio turn (STT finalize -> conversation -> TTS).
    # ------------------------------------------------------------------
    async def _process_audio_turn(self, gen: Generation) -> None:
        self._processing = True
        await self._emit_state("processing")
        try:
            gen.check()
            stt_result = await asyncio.to_thread(self.stt.finalize)
            self._stt_started = False
            gen.check()
            gen.timings["stt_final_ms"] = (
                max(0.0, time.perf_counter() - self._speech_end_at) * 1000.0
            )
            transcript = stt_result.text.strip()
            if not transcript:
                await self.emit_generation(gen, "transcript", text="")
                self._transcript_at = time.perf_counter()
                await self._finish_done(gen)
                return
            await self.emit_generation(gen, "transcript", text=transcript)
            self._transcript_at = time.perf_counter()
            await self._answer(gen, transcript)
        except Cancelled:
            return
        except asyncio.CancelledError:
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("audio turn failed: %s", exc)
            await self._fail(gen, ErrorCode.STT_ERROR, str(exc))
        finally:
            self._processing = False

    def _latency_anchor(self) -> float:
        """Anchor latency deltas: end of speech (audio turns) or turn start (text turns).

        ``_speech_end_at`` is 0.0 for pure text turns (no speech was ever
        captured), so fall back to the turn start to avoid fabricated multi-hour
        ``first_response_ms``/``tts_first_audio_ms`` values.
        """
        return self._speech_end_at or self._speech_start_at

    async def _answer(self, gen: Generation, transcript: str) -> None:
        gen.check()
        t0 = time.perf_counter()
        try:
            story, intent, answer, resolved_id = await asyncio.to_thread(
                self.conversation.ask,
                path_incident_id=self._path_incident_id,
                message=transcript,
                session_id=self.session_id,
            )
        except (IncidentContextRequired, IncidentNotFound, ConversationError) as exc:
            await self._fail(gen, ErrorCode.CONVERSATION_ERROR, str(exc))
            return
        gen.timings["conversation_ms"] = (time.perf_counter() - t0) * 1000.0
        gen.timings["first_response_ms"] = (
            max(0.0, time.perf_counter() - self._latency_anchor()) * 1000.0
        )
        gen.meta["intent"] = intent
        gen.meta["incident_id"] = resolved_id
        self._check_turn_deadline(gen)

        from ..conversation.intents import render_spoken_answer, curate_spoken_text
        if story is not None:
            spoken_answer = render_spoken_answer(intent, story)
        else:
            spoken_answer = getattr(answer, "spoken_reply", None) or curate_spoken_text(answer)

        presentation = getattr(answer, "presentation", {})
        if story is not None:
            from engine_stack.engines.telecom_brain.services.narrative import narrative_from_story
            from engine_stack.engines.telecom_brain.services.visual_explanation import VisualExplanationService
            narrative = narrative_from_story(story, intent=intent, written_story=answer)
            presentation = {
                "narrative": narrative.model_dump(mode="json"),
                "visual_explanation": VisualExplanationService().build(narrative).model_dump(mode="json"),
            }

        await self.emit_generation(
            gen,
            "response",
            answer=answer,
            spoken_answer=spoken_answer,
            intent=intent,
            incident_id=resolved_id,
            **presentation,
        )
        await self._emit_tts(gen, spoken_answer)

    async def _stream_tts_chunks(self, sentence: str):
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        done = object()

        def _worker():
            try:
                for chunk in self.tts.synthesize_stream(sentence):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, done)

        threading.Thread(target=_worker, daemon=True).start()

        while True:
            item = await queue.get()
            if item is done:
                break
            if isinstance(item, Exception):
                raise item
            yield item

    async def _emit_tts(self, gen: Generation, answer: str) -> None:
        self._tts_active = True
        self.session.active_tts_id = gen.id
        await self._emit_state("speaking")
        t0 = time.perf_counter()
        emitted = False
        try:
            self.tts.start(sample_rate=OUTPUT_SAMPLE_RATE)
            sentences = split_sentences(answer)
            has_stream = hasattr(self.tts, "synthesize_stream")
            for beat_idx, sentence in enumerate(sentences):
                self._check_turn_deadline(gen)
                gen.check()
                cue = self._derive_visual_cue(sentence)
                await self.emit_generation(
                    gen, "beat_start", beat_id=beat_idx, text=sentence, cue=cue
                )
                if has_stream:
                    async for chunk in self._stream_tts_chunks(sentence):
                        self._check_turn_deadline(gen)
                        gen.check()
                        if chunk is None or chunk.audio is None or chunk.audio.size == 0:
                            continue
                        if not emitted:
                            gen.timings["tts_first_audio_ms"] = (
                                max(0.0, time.perf_counter() - self._latency_anchor()) * 1000.0
                            )
                            self._first_audio_at = time.perf_counter()
                            emitted = True
                        out_rate = chunk.sample_rate or OUTPUT_SAMPLE_RATE
                        await self.emit_generation(
                            gen, "audio", audio=chunk.audio, sample_rate=out_rate
                        )
                else:
                    chunk = await asyncio.to_thread(self.tts.synthesize_chunk, sentence)
                    gen.check()
                    if chunk is None or chunk.audio is None or chunk.audio.size == 0:
                        continue
                    if not emitted:
                        gen.timings["tts_first_audio_ms"] = (
                            max(0.0, time.perf_counter() - self._latency_anchor()) * 1000.0
                        )
                        self._first_audio_at = time.perf_counter()
                        emitted = True
                    out_rate = chunk.sample_rate or OUTPUT_SAMPLE_RATE
                    await self.emit_generation(
                        gen, "audio", audio=chunk.audio, sample_rate=out_rate
                    )
                await self.emit_generation(gen, "beat_end", beat_id=beat_idx)
            self.tts.stop()
            gen.timings["tts_ms"] = (time.perf_counter() - t0) * 1000.0
            await self._finish_done(gen)
        except Cancelled:
            self.tts.stop()
            return
        except asyncio.CancelledError:
            self.tts.stop()
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("tts turn failed: %s", exc)
            with contextlib.suppress(Exception):
                self.tts.stop()
            await self._fail(gen, ErrorCode.TTS_ERROR, str(exc))
        finally:
            self._tts_active = False
            self.session.active_tts_id = None
            await self._emit_state("idle")

    async def _finish_done(self, gen: Generation) -> None:
        self._finalize_timings(gen)
        await self.emit_generation(gen, "done", timings=dict(gen.timings))

    async def _fail(self, gen: Generation, code: ErrorCode, message: str) -> None:
        await self._emit(
            {
                "type": "error",
                "generation_id": gen.id,
                "code": code.value,
                "message": message,
            }
        )
        self._finalize_timings(gen)
        await self.emit_generation(gen, "done", timings=dict(gen.timings))

    def _finalize_timings(self, gen: Generation) -> None:
        """Normalize timing keys to the observability vocabulary (spec: #15).

        ``reasoning_ms`` == conversation/reasoning pipeline time; ``llm_ms`` is
        0.0 because answers are deterministic (the optional LLM is not invoked
        in the voice path). ``stt_ms`` aliases the final transcription latency.

        Phase 3D adds the latency markers captured along the real voice path
        (all deltas from the turn's speech-start anchor, monotonic clock).
        """
        conversation_ms = gen.timings.get("conversation_ms", 0.0)
        gen.timings.setdefault("stt_ms", gen.timings.get("stt_final_ms", 0.0))
        gen.timings["reasoning_ms"] = conversation_ms
        gen.timings.setdefault("llm_ms", 0.0)
        gen.timings["vad_ms"] = self._vad_ms
        gen.timings["total_ms"] = (
            max(0.0, time.perf_counter() - self._speech_start_at) * 1000.0
        )
        # --- Phase 3D latency markers (measured, never fabricated) ---------
        anchor = self._speech_start_at
        if self._audio_received_at is not None:
            gen.timings.setdefault(
                "audio_received_ms", max(0.0, (self._audio_received_at - anchor) * 1000.0)
            )
        if self._transcript_at is not None:
            gen.timings.setdefault(
                "time_to_first_transcript_ms",
                max(0.0, (self._transcript_at - anchor) * 1000.0),
            )
        if self._first_audio_at is not None:
            gen.timings.setdefault(
                "time_to_first_audio_ms", max(0.0, (self._first_audio_at - anchor) * 1000.0)
            )
        gen.timings["total_turn_ms"] = gen.timings["total_ms"]
        logger.info(
            "voice turn done session=%s generation=%d intent=%s incident=%s "
            "interrupted=%s timings=%s",
            self.session_id,
            gen.id,
            gen.meta.get("intent"),
            gen.meta.get("incident_id"),
            gen.cancelled,
            gen.timings,
        )

    async def _emit_state(self, state: str) -> None:
        self.session.connection_state = state
        await self._emit({"type": "state", "state": state})

    # ------------------------------------------------------------------
    # Spawn helper (keeps a handle for cancellation) + no-op emit.
    # ------------------------------------------------------------------
    def _spawn(self, coro) -> None:
        self._turn_task = asyncio.create_task(coro)

    def _check_turn_deadline(self, gen: Generation) -> None:
        """Abort a turn that exceeds ``max_turn_ms`` (resource protection).

        Raises :class:`Cancelled` (cooperative, consistent with barge-in) so the
        existing cancellation paths stop STT/TTS work and discard stale audio.
        """
        if self._max_turn_ms is None:
            return
        if (time.perf_counter() - self._speech_start_at) * 1000.0 > self._max_turn_ms:
            gen.cancel()
            raise Cancelled

    def _reset_markers(self) -> None:
        self._audio_received_at = None
        self._transcript_at = None
        self._first_audio_at = None

    @staticmethod
    def _derive_visual_cue(sentence: str) -> dict[str, Any]:
        """Derive synchronous visual cue action for this sentence (Narrative Beat)."""
        lower = sentence.lower()
        for ent in ("pe-rtr-21", "rtr-21", "upf-003", "upf", "amf", "smf", "ticket"):
            if ent in lower:
                return {"type": "HIGHLIGHT_NODE", "target": ent.upper()}
        if "confidence" in lower or "%" in lower or "percent" in lower:
            return {"type": "DIAL_CONFIDENCE"}
        if "recovery" in lower or "mitigat" in lower or "remediat" in lower or "restor" in lower:
            return {"type": "SHOW_RECOVERY"}
        return {"type": "GENERAL_NARRATION"}

    @staticmethod
    async def _noop_emit(_event: dict) -> None:
        return None


__all__ = ["RealtimeVoicePipeline", "RealtimeVoiceSession"]
