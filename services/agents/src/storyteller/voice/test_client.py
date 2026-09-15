"""Minimal realtime voice client for the ``/ws/voice/{session_id}`` endpoint.

Primary path is **text mode** (no microphone): connect, send a ``text`` message,
and print the streamed transcript / response / audio-chunk summary. Optional
mic (``--mic``) or file (``--audio FILE.wav``) modes stream PCM for testing the
audio path. The client is intentionally dependency-light (only ``websockets`` +
``numpy`` are required for text mode).

Usage::

    python -m storyteller.voice.test_client --ws ws://127.0.0.1:8001 \
        --session voice-test --text "why did it happen?" \
        --incident mobile-core/incidents/amf-overload-2026-08-09
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import numpy as np

from .protocol import (
    INPUT_SAMPLE_RATE,
    MessageType,
    decode_message,
    encode_message,
)


def _syllable(kind: str, payload: dict) -> str:
    if kind == "transcript_partial" or kind == "transcript":
        return f"[{kind}] {payload.get('text', '')}"
    if kind == "response":
        return f"[response intent={payload.get('intent')} incident={payload.get('incident_id')}] {payload.get('answer', '')}"
    if kind == "audio":
        return f"[audio gen={payload.get('generation_id')} sr={payload.get('sample_rate')}] chunk"
    if kind == "done":
        return f"[done gen={payload.get('generation_id')} timings={payload.get('timings')}]"
    if kind == "error":
        return f"[error {payload.get('code')}] {payload.get('message')}"
    if kind == "state":
        return f"[state] {payload.get('state')}"
    return f"[{kind}] {payload}"


async def _drain_until_done(ws, audio_out: list[np.ndarray]) -> None:
    """Receive events until the server sends ``done`` for a turn."""
    while True:
        msg = await ws.recv()
        if isinstance(msg, (bytes, bytearray)):
            audio_out.append(np.frombuffer(bytes(msg), dtype="<i2"))
            print("[audio-bytes] chunk", file=sys.stderr)
            continue
        payload = decode_message(msg)
        kind = payload.get("type")
        print(_syllable(kind, payload))
        if kind == MessageType.DONE.value:
            return
        if kind == MessageType.ERROR.value:
            raise SystemExit(f"server error: {payload.get('message')}")


async def run_text(
    ws_uri: str, session_id: str, text: str, incident_id: str | None
) -> None:
    import websockets  # noqa: PLC0415

    async with websockets.connect(f"{ws_uri}/ws/voice/{session_id}") as ws:
        ready = decode_message(await ws.recv())
        print(f"[ready] {ready.get('session_id')}")
        await ws.send(encode_message(MessageType.TEXT.value, text=text, path_incident_id=incident_id))
        await _drain_until_done(ws, [])


async def run_audio(
    ws_uri: str, session_id: str, audio: np.ndarray, incident_id: str | None, chunk: int = 3200
) -> None:
    import websockets  # noqa: PLC0415

    pcm = (np.clip(audio, -1, 1) * 32767.0).astype("<i2").tobytes()
    async with websockets.connect(f"{ws_uri}/ws/voice/{session_id}") as ws:
        ready = decode_message(await ws.recv())
        print(f"[ready] {ready.get('session_id')}")
        await ws.send(
            encode_message(MessageType.START.value, path_incident_id=incident_id)
        )
        emitted: list[np.ndarray] = []
        for i in range(0, len(pcm), chunk * 2):
            await ws.send(pcm[i : i + chunk * 2])
        await ws.send(encode_message(MessageType.STOP.value))
        await _drain_until_done(ws, emitted)
        print(f"[audio] received {sum(a.size for a in emitted)} output samples")


def _load_wav(path: str, sample_rate: int = INPUT_SAMPLE_RATE) -> np.ndarray:
    import soundfile as sf  # noqa: PLC0415

    data, sr = sf.read(path, dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data[:, 0]
    if sr != sample_rate:
        import scipy.signal  # noqa: PLC0415

        ratio = sample_rate / sr
        data = scipy.signal.resample_poly(data, int(round(ratio * 1000)), 1000)
    return np.asarray(data, dtype=np.float32)


async def run_mic(ws_uri: str, session_id: str, incident_id: str | None) -> None:
    import websockets  # noqa: PLC0415
    import sounddevice as sd  # noqa: PLC0415

    emitted: list[np.ndarray] = []
    send_queue: asyncio.Queue[bytes] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def callback(indata, frames, time_info, status):  # noqa: ARG001
        try:
            loop.call_soon_threadsafe(
                send_queue.put_nowait,
                (np.clip(indata[:, 0], -1, 1) * 32767).astype("<i2").tobytes(),
            )
        except RuntimeError:  # loop is closed
            pass

    async with websockets.connect(f"{ws_uri}/ws/voice/{session_id}") as ws:
        ready = decode_message(await ws.recv())
        print(f"[ready] {ready.get('session_id')}")
        await ws.send(encode_message(MessageType.START.value, path_incident_id=incident_id))
        done_drain = asyncio.create_task(_drain_until_done(ws, emitted))

        async def feed() -> None:
            while True:
                chunk = await send_queue.get()
                await ws.send(chunk)

        feeder = asyncio.create_task(feed())
        try:
            with sd.InputStream(
                samplerate=INPUT_SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=1600,
                callback=callback,
            ):
                print(f"Listening on mic at {INPUT_SAMPLE_RATE} Hz. Ctrl+C to stop.")
                while True:
                    await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            pass
        await ws.send(encode_message(MessageType.STOP.value))
        await done_drain
        feeder.cancel()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Realtime voice test client")
    parser.add_argument("--ws", default="ws://127.0.0.1:8001", help="WebSocket base")
    parser.add_argument("--session", default="voice-client")
    parser.add_argument("--incident", help="incident id/slug to resolve context")
    parser.add_argument("--text", help="text mode: send this message")
    parser.add_argument("--audio", help="audio mode: read this .wav file")
    parser.add_argument("--mic", action="store_true", help="audio mode: live microphone")
    parser.add_argument("--chunk", type=int, default=3200, help="audio chunk samples")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    base = args.ws.rstrip("/")
    if args.text:
        asyncio.run(run_text(base, args.session, args.text, args.incident))
    elif args.audio:
        audio = _load_wav(args.audio)
        asyncio.run(run_audio(base, args.session, audio, args.incident, args.chunk))
    elif args.mic:
        asyncio.run(run_mic(base, args.session, args.incident))
    else:
        parser.error("provide --text, --audio, or --mic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())