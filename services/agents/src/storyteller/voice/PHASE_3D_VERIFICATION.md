# Phase 3D — Real ML Backend Integration & Production Hardening: Verification Report

Scope: connect the Phase 3C realtime voice architecture to *real* Silero VAD /
faster-whisper STT / Kokoro TTS backends, harden the live WebSocket path with
resource protections and latency observability, and prove it with real-ML tests.
No Phase 3C contract was rewritten — the 3C suites still pass unmodified.

## 1. What changed

| File | Change |
| --- | --- |
| `voice/config.py` (new) | `VoiceSettings(BaseSettings)` + cached `get_voice_settings()`. Env vars: `STT_MODEL=small`, `STT_DEVICE=cpu`, `STT_COMPUTE_TYPE=int8`, `STT_LANGUAGE`, `TTS_MODEL=hexgrad/Kokoro-82M`, `TTS_VOICE=af_heart`, `TTS_SPEED`, `TTS_DEVICE`, `VOICE_VAD_THRESHOLD`, `VOICE_VAD_MIN_SILENCE_MS`, `VOICE_VAD_SPEECH_PAD_MS`, `VOICE_MAX_UTTERANCE_SECONDS=30`, `VOICE_MAX_TURN_MS=120_000`, `VOICE_MAX_CONCURRENT_SESSIONS=16`, `VOICE_IDLE_TIMEOUT_S=900`, `VOICE_OUT_QUEUE_SIZE=256`. Loads `cwd/.env` then repo-root `shared/.env`. |
| `voice/realtime.py` | Added `max_turn_ms` / `max_utterance_samples` caps, utterance-cap guard in `accept_audio`, `_check_turn_deadline` (→ `Cancelled`), idle latency markers (`audio_received_ms`, `time_to_first_transcript_ms`, `time_to_first_audio_ms`, `total_turn_ms`), `_latency_anchor()` so text turns report sane `first_response_ms`/`tts_first_audio_ms`, and **fixed a real-ML livelock**: `_on_speech_start` no longer resets the Silero iterator (resetting right after a `start` made Silero re-detect the same speech as repeated starts). |
| `voice/websocket.py` | Handler wiring for 3D limits: acquire `_SessionLimiter` (reject `error` + close 1013 when at cap), pass `max_turn_ms` / `max_utterance_samples` into the pipeline, idle timeout around the receive loop (close on `TimeoutError`), pass `out_queue_size` → bounded per-connection `asyncio.Queue` with drop-on-full logging, limiter released in `finally`. |
| `pyproject.toml` | Registered `real_ml` pytest marker (single-line TOML-safe description). |
| `tests/ml/` (new) | Opt-in real-ML suite: `conftest.py` (gate, session fixtures, real-speech fixture), `test_real_vad.py`, `test_real_stt.py`, `test_real_tts.py`, `test_real_voice_e2e.py`. |

Dependencies: **unchanged**. No new packages — all three backends were already
declared in the voice extra (spec: no custom ML, thin adapters around established
libs; real backends were already lazy-imported in Phase 3B/3C).

## 2. Verification matrix (all green)

| Suite | Run | Result |
| --- | --- | --- |
| Phase 3C + prior suites (default `testpaths`) | `pytest agents/src/storyteller/tests` | **139 passed, 43 skipped** (21 real-ML tests collect and skip cleanly when `VOICE_REAL_ML` is unset) |
| Real ML suite | `VOICE_REAL_ML=1 pytest tests/ml` | **21 passed, 0 failed, 0 skipped** |
| Lint | `ruff check` on all touched dirs | pass |
| Format | `ruff format` on new files | applied |

Real-ML tests skipped *before* loading any model when disabled — default CI never
downloads weights or imports torch/CTranslate2 (spec: "Do not make normal CI
dependent on downloading large models").

### What the 21 real tests prove
- **VAD (6):** silence never fires; real Kokoro speech → exactly one `start`+`end`
  (`4608→47616` of the fixture); `speech_ranges` returns one valid range; reset
  clears streaming state; non-16k input raises `VADError`; two instances stay
  isolated (shared weights, per-instance `VADIterator`).
- **STT (4):** real speech transcribes non-empty; shared backend is stateless
  across calls; uninitialized backend raises `STTError`; incremental streamer
  partial→final; per-streamer buffer isolation over one shared backend.
- **TTS (6):** real synthesis → finite float32 audio ≤ 1.0 at 24 kHz with
  `duration > 0`; fresh lazy backend works; empty/whitespace text raises
  `TTSError`; uninitialized raises; sentence-chunked streaming returns audio per
  chunk and `None` for empty; `split_sentences` chunking for real streaming.
- **E2E (3):** text route → response + 24 kHz audio + done with sane latency
  markers; **real audio route** → real speech detected by real VAD, transcribed by
  real STT to non-empty text, answered by the injected `ConversationService`, spoken
  by real TTS, `done` emitted; **real barge-in** → real TTS interrupted by real
  speech, cancelled generation never emits `done`, task settles.

## 3. Measured latencies (macOS, CPU, single-threaded)

Real backends were verified working only with `KMP_DUPLICATE_LIB_OK=TRUE` and
`OMP_NUM_THREADS=1` (torch vs CTranslate2 OpenMP conflict). Linux/Docker unaffected.

| Step | Cold init | Steady state |
| --- | --- | --- |
| Silero VAD | 2.61 s (weights bundled in package) | per-512-sample classify ~1 ms |
| faster-whisper `Systran/faster-whisper-tiny`, int8, CPU | 6 s | transcribe 3.25 s speech ≈ 2.4–5.8 s |
| Kokoro-82M, `af_heart`, CPU | 39.2 s (first run incl. one-time spaCy `en_core_web_sm`) | synthesize 3.25 s speech ≈ 2.2 s |
| Full real audio turn (VAD→STT→conversation→TTS→done) | — | ≈ 50 s (dominated by CPU TTS of the 8-chunk answer; machine-dependent) |

Latency markers emitted per turn (`done.timings`): `stt_ms`, `conversation_ms`,
`first_response_ms`, `tts_ms`, `vad_ms`, `tts_first_audio_ms`, plus Phase 3D
`audio_received_ms`, `time_to_first_transcript_ms`, `time_to_first_audio_ms`,
`total_turn_ms` — measured, never fabricated.

## 4. Resource protections (live WebSocket path)

- Session cap: `VOICE_MAX_CONCURRENT_SESSIONS=16` via `_SessionLimiter` (reject 1013).
- Turn cap: `VOICE_MAX_TURN_MS=120s` → `_check_turn_deadline` cancels long turns.
- Utterance cap: `VOICE_MAX_UTTERANCE_SECONDS=30` → forced finalize on over-length speech.
- Idle timeout: `VOICE_IDLE_TIMEOUT_S=900` → close on silence.
- Backpressure: bounded per-connection out queue (drop-on-full + log, no head-of-line block).
- Shared model caches: weights/backends loaded once; per-connection streaming state
  isolated (verified by real VAD/STT isolation tests).

## 5. Limitations (honest)

- faster-whisper exposes no token-level incremental decoding; STT is *chunked*,
  not token-streaming (documented in `stt.py`).
- Kokoro is *sentence-chunked*, not phoneme-streaming; TTS is interruptible only
  between sentences (atomic per chunk).
- Real-ML tests are opt-in and slow (~3.5 min on this machine) — they gate on
  `VOICE_REAL_ML=1` and skip cleanly otherwise.
- Two-sentence speech fixtures can split into two utterances at mid-sentence
  pauses; the suite uses a single deterministic sentence for reproducibility.
