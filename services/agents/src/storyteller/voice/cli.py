"""Local voice CLI.

Usage:

    python -m storyteller.voice.cli --text "why did it happen?"          # text-only
    python -m storyteller.voice.cli --incident mobile-core/incidents/amf-overload-2026-08-09
    python -m storyteller.voice.cli                                       # live mic loop

Audio devices (microphone in / speaker out) are only touched in live mic mode;
``--text`` needs no audio hardware. Model selection is via the same STT_*/TTS_*
environment variables as the library (see the module docstrings).
"""

from __future__ import annotations

import argparse
import json
import logging
import os

from .pipeline import VoicePipeline
from .stt import create_stt
from .tts import create_tts
from .vad import create_vad


def _configure_logging() -> None:
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _build_pipeline(args: argparse.Namespace) -> VoicePipeline:
    from ..conversation.service import ConversationService
    from ..conversation.session import SessionStore
    from ..knowledge.gbrain_client import GbrainClient
    from ..knowledge.mobile_core_knowledge import MobileCoreKnowledge

    vad = create_vad()
    stt = create_stt()
    tts = create_tts()
    knowledge = MobileCoreKnowledge(GbrainClient())
    conversation = ConversationService(knowledge, sessions=SessionStore())
    return VoicePipeline(
        vad=vad,
        stt=stt,
        tts=tts,
        conversation=conversation,
        session_id=args.session_id,
    )


def _print_result(result) -> None:
    out = {
        "transcript": result.transcript,
        "answer": result.answer,
        "intent": result.intent,
        "incident_id": result.incident_id,
        "timings_ms": result.timings,
        "audio_samples": None if result.audio is None else int(len(result.audio)),
        "sample_rate": result.sample_rate,
        "synthesized": result.synthesized,
        "error": result.error,
    }
    print(json.dumps(out, indent=2))


def run_text(args: argparse.Namespace) -> int:
    pipeline = _build_pipeline(args)
    result = pipeline.process_text(args.text, path_incident_id=args.incident)
    _print_result(result)
    if args.output and result.audio is not None:
        import soundfile as sf  # noqa: PLC0415

        sf.write(args.output, result.audio, result.sample_rate)
        print(f"Wrote audio to {args.output}")
    return 0 if result.error is None else 2


def run_mic(args: argparse.Namespace) -> int:
    import time

    import sounddevice as sd  # noqa: PLC0415

    pipeline = _build_pipeline(args)
    pipeline.vad.init()
    sample_rate = pipeline.vad.sample_rate
    chunk = 512

    print(f"Listening on mic at {sample_rate} Hz. Press Ctrl+C to exit.")
    buffer: list[float] = []
    recording = False

    def callback(indata, frames, time_info, status):  # noqa: ARG001
        nonlocal recording, buffer
        audio = indata[:, 0]
        for i in range(0, len(audio), chunk):
            piece = audio[i : i + chunk]
            event = pipeline.vad.process(piece)
            if event is not None:
                if event.kind == "start":
                    buffer = []
                    recording = True
                elif event.kind == "end" and recording:
                    recording = False
            if recording:
                buffer.extend(piece.tolist())

    import numpy as np  # noqa: PLC0415

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", callback=callback):
        try:
            while True:
                time.sleep(0.1)
                if not recording and buffer:
                    speech = np.asarray(buffer, dtype=np.float32)
                    buffer = []
                    result = pipeline.process_audio(speech, sample_rate=sample_rate)
                    _print_result(result)
                    if result.audio is not None and result.audio.size:
                        sd.play(result.audio, result.sample_rate)
                        sd.wait()
                    if args.output and result.audio is not None:
                        import soundfile as sf  # noqa: PLC0415

                        sf.write(args.output, result.audio, result.sample_rate)
                        print(f"Wrote audio to {args.output}")
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local voice storyteller")
    parser.add_argument("--text", help="text-only route (no microphone)")
    parser.add_argument("--incident", help="incident id/slug to resolve context")
    parser.add_argument("--session-id", default="voice-default", help="conversation session id")
    parser.add_argument("--output", help="write the TTS audio to a .wav file")
    args = parser.parse_args(argv)

    _configure_logging()
    if args.text:
        return run_text(args)
    return run_mic(args)


if __name__ == "__main__":
    raise SystemExit(main())
