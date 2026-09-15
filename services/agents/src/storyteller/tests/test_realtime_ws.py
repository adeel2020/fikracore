"""Phase 3C tests — the realtime WebSocket endpoint.

Drives the real ``/ws/voice/{session_id}`` route with FastAPI's ``TestClient``
(an existing library) while the heavy adapters are dependency-overridden with
fakes — no ML models, no gbrain. Covers connect/ready, text and audio turns,
barge-in over the wire, error handling, incident binding, and the browser page.
Generic incidents (``incident-A``/``incident-B``) are used; the endpoint itself
is incident-agnostic.
"""

from __future__ import annotations

import json
import threading
import time

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from storyteller.conversation.service import ConversationService
from storyteller.conversation.session import SessionStore
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact
from storyteller.voice.stt import STTResult, StreamingSTTAdapter
from storyteller.voice.tts import TTSResult, StreamingTTSAdapter
from storyteller.voice.vad import VADAdapter, SpeechEvent
from storyteller.voice import websocket as voice_ws

INC_A = "mobile-core/incidents/incident-a"
INC_B = "mobile-core/incidents/incident-b"
AMF = "mobile-core/incidents/amf-overload-2026-08-09"


class FakeKnowledge:
    def __init__(self) -> None:
        self.contexts = {INC_A: _ctx(INC_A), INC_B: _ctx(INC_B)}

    def get_incident_context(self, incident_id: str) -> IncidentContext:
        return self.contexts.get(incident_id, IncidentContext())


def _ctx(incident_id: str) -> IncidentContext:
    return IncidentContext(
        incident={"slug": incident_id, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
        timeline=[fact("symptom observed", relationship="timeline-entry")],
        symptoms=[fact("Generic symptom", relationship="has-symptom")],
        hypotheses=[fact(
            "Generic root cause hypothesis", relationship="has-hypothesis",
            confidence=0.8, extra={"status": "confirmed"},
        )],
        evidence=[fact("Generic evidence", relationship="supported-by")],
        remediations=[fact("Generic remediation", relationship="has-remediation")],
        recovery_events=[fact("Recovery observed", relationship="verified-by")],
    )


class FakeVAD(VADAdapter):
    def __init__(self, start_at: int = 0, end_at: int = 4) -> None:
        self.start_at = start_at
        self.end_at = end_at
        self.calls = 0

    def init(self) -> None:
        pass

    def reset(self) -> None:
        pass

    def process(self, chunk: np.ndarray) -> SpeechEvent | None:
        idx = self.calls
        self.calls += 1
        if idx == self.start_at:
            return SpeechEvent("start", 0)
        if idx == self.end_at:
            return SpeechEvent("end", 0)
        return None


class FakeSTT(StreamingSTTAdapter):
    def __init__(self, transcript: str = "why did it happen?", partial: str = "why did") -> None:
        self.transcript = transcript
        self.partial = partial
        self.started = False

    def start(self, *, sample_rate: int) -> None:
        self.started = True

    def accept_audio(self, audio: np.ndarray) -> None:
        if not self.started:
            raise RuntimeError("accept_audio called before start()")
        pass

    def get_partial(self) -> str:
        return self.partial

    def finalize(self) -> STTResult:
        return STTResult(text=self.transcript, language="en", duration=1.0)

    def reset(self) -> None:
        self.started = False


class FakeTTS(StreamingTTSAdapter):
    def __init__(self, gate: threading.Event | None = None) -> None:
        self.gate = gate
        self.entered = 0
        self._started = False

    def start(self, *, sample_rate: int) -> None:
        self._started = True

    def synthesize_chunk(self, text: str) -> TTSResult | None:
        self.entered += 1
        if self.gate is not None:
            self.gate.wait(timeout=5)
        return TTSResult(audio=np.full(240, 0.01, dtype=np.float32), sample_rate=24000, text=text)

    def stop(self) -> None:
        self._started = False


class FakeJarvisConversation:
    def ask(
        self,
        *,
        path_incident_id: str | None,
        message: str,
        session_id: str,
    ) -> tuple[None, str, str, str | None]:
        return None, "mark_general", f"MARK heard: {message}", path_incident_id


def make_app(*, stt=None, tts=None, vad=None, conversation=None) -> FastAPI:
    app = FastAPI()
    app.include_router(voice_ws.router)
    conv = conversation or ConversationService(FakeKnowledge(), sessions=SessionStore())
    stt_impl = stt or FakeSTT()
    tts_impl = tts or FakeTTS()
    vad_impl = vad or FakeVAD()
    app.dependency_overrides[voice_ws._conversation_dep] = lambda: conv
    app.dependency_overrides[voice_ws._stt_dep] = lambda: stt_impl
    app.dependency_overrides[voice_ws._tts_dep] = lambda: tts_impl
    app.dependency_overrides[voice_ws._vad_dep] = lambda: vad_impl
    app.dependency_overrides[voice_ws._jarvis_conversation_dep] = lambda: FakeJarvisConversation()
    return app


def next_json(ws) -> dict:
    msg = ws.receive()
    assert msg.get("type") == "websocket.send"
    return json.loads(msg["text"])


def recv_any(ws) -> tuple[str, object]:
    msg = ws.receive()
    if msg.get("type") != "websocket.send":
        return ("close", msg.get("code"))
    if msg.get("bytes") is not None:
        return ("bytes", msg["bytes"])
    return ("json", json.loads(msg["text"]))


def drain_until_done(ws) -> list:
    kinds: list[str] = []
    while True:
        kind, payload = recv_any(ws)
        if kind == "json":
            kinds.append(payload["type"])
            if payload["type"] == "done":
                return kinds
        else:
            kinds.append("audio-bytes")


def pcm16(samples: int) -> bytes:
    return np.zeros(samples, dtype=np.float32).astype("<i2").tobytes()


class TestVoiceSessionEndpoint:
    def test_bind_incident_to_session(self):
        client = TestClient(make_app())
        resp = client.post(f"/api/incidents/{INC_A}/voice-session", json={"session_id": "vs-1"})
        assert resp.status_code == 200
        assert resp.json()["incident_id"] == INC_A
        assert resp.json()["session_id"] == "vs-1"
        assert resp.json()["active"] is True

    def test_bind_unknown_incident_404(self):
        client = TestClient(make_app())
        resp = client.post(
            "/api/incidents/mobile-core/incidents/does-not-exist/voice-session",
            json={"session_id": "vs-2"},
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_bind_invalid_session_400(self):
        client = TestClient(make_app())
        resp = client.post(f"/api/incidents/{INC_A}/voice-session", json={"session_id": "bad id!"})
        assert resp.status_code == 400

    def test_bind_then_followup_uses_session(self):
        conversation = ConversationService(FakeKnowledge(), sessions=SessionStore())
        client = TestClient(make_app(conversation=conversation))
        client.post(f"/api/incidents/{INC_A}/voice-session", json={"session_id": "vs-follow"})
        # A WS turn for that session, message with no incident reference, must
        # resolve INC_A from the session's active incident.
        with client.websocket_connect("/ws/voice/vs-follow") as ws:
            next_json(ws)  # ready
            ws.send_text(json.dumps({"type": "text", "text": "why did it happen?"}))
            kinds = drain_until_done(ws)
            assert "response" in kinds


class TestWebSocketReady:
    def test_ready_envelope(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-ready") as ws:
            ready = next_json(ws)
            assert ready["type"] == "ready"
            assert ready["session_id"] == "ws-ready"
            assert ready["input"]["sample_rate"] == 16000
            assert ready["output"]["sample_rate"] == 24000
            assert "text" in ready["message_types"]

    def test_invalid_session_closes(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/user@host") as ws:
            err = next_json(ws)
            assert err["type"] == "error"
            assert err["code"] == "session_error"


class TestWebSocketTextTurn:
    def test_text_turn_streams_response_and_audio(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-text") as ws:
            ready = next_json(ws)
            assert ready["type"] == "ready"
            ws.send_text(json.dumps({"type": "text", "text": "why did it happen?", "path_incident_id": INC_A}))
            kinds = drain_until_done(ws)
            assert "transcript" in kinds
            assert "response" in kinds
            assert "audio" in kinds
            assert "audio-bytes" in kinds
            assert "done" in kinds

    def test_jarvis_voice_text_turn_does_not_require_incident_context(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/jarvis-voice/ws-mark") as ws:
            ready = next_json(ws)
            assert ready["type"] == "ready"
            ws.send_text(json.dumps({"type": "text", "text": "hello can you listen to me"}))
            kinds = drain_until_done(ws)
            assert "transcript" in kinds
            assert "response" in kinds
            assert "audio-bytes" in kinds
            assert "done" in kinds

    def test_text_turn_invalid_message(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-text") as ws:
            next_json(ws)
            ws.send_text(json.dumps({"type": "text"}))  # missing 'text'
            err = next_json(ws)
            assert err["type"] == "error"
            assert err["code"] == "invalid_message"

    def test_unknown_message_type(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-text") as ws:
            next_json(ws)
            ws.send_text(json.dumps({"type": "banana"}))
            err = next_json(ws)
            assert err["type"] == "error"
            assert err["code"] == "invalid_message"


class TestWebSocketAudioTurn:
    def test_audio_turn_full_flow(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-audio") as ws:
            next_json(ws)
            ws.send_text(json.dumps({"type": "start", "path_incident_id": INC_A}))
            # Each VAD process() consumes 512 samples; start@call0 + end@call4
            # needs 5 * 512 = 2560 samples (10 chunks of 256 samples).
            for _ in range(12):
                ws.send_bytes(pcm16(512))
            kinds = drain_until_done(ws)
            assert "transcript" in kinds
            assert "response" in kinds
            assert "audio-bytes" in kinds

    def test_audio_frames_before_explicit_start_do_not_crash(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/jarvis-voice/ws-mark-audio-race") as ws:
            next_json(ws)
            for _ in range(12):
                ws.send_bytes(pcm16(512))
            kinds = drain_until_done(ws)
            assert "transcript" in kinds
            assert "response" in kinds
            assert "done" in kinds

    def test_oversize_audio_chunk_rejected(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-audio") as ws:
            next_json(ws)
            ws.send_bytes(b"\x00" * (1024 * 1024 + 4))
            err = next_json(ws)
            assert err["type"] == "error"
            assert err["code"] == "audio_format_error"

    def test_json_audio_event_base64_path(self):
        client = TestClient(make_app())
        with client.websocket_connect("/ws/voice/ws-audio") as ws:
            next_json(ws)
            ws.send_text(json.dumps({"type": "start", "path_incident_id": INC_A}))
            import base64

            for _ in range(12):
                ws.send_text(json.dumps({
                    "type": "audio",
                    "data_base64": base64.b64encode(pcm16(512)).decode("ascii"),
                }))
            kinds = drain_until_done(ws)
            assert "response" in kinds


class TestWebSocketBargeIn:
    def test_interrupt_cancels_turn_and_keeps_connection(self):
        release = threading.Event()
        tts = FakeTTS(gate=release)
        client = TestClient(make_app(tts=tts))
        with client.websocket_connect("/ws/voice/ws-barge") as ws:
            next_json(ws)
            ws.send_text(json.dumps({"type": "start", "path_incident_id": INC_A}))
            for _ in range(12):
                ws.send_bytes(pcm16(512))
            # Wait until the TTS worker has entered (blocked on `release`).
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and tts.entered < 1:
                time.sleep(0.01)
            assert tts.entered >= 1
            # Interrupt, then release the worker so cancellation propagates.
            ws.send_text(json.dumps({"type": "interrupt"}))
            time.sleep(0.05)
            release.set()
            # The interrupted turn must NOT reach `done`; we expect a state change.
            seen_done = False
            seen_idle = False
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not seen_idle:
                kind, payload = recv_any(ws)
                if kind == "json":
                    if payload["type"] == "done":
                        seen_done = True
                    if payload["type"] == "state" and payload["state"] == "idle":
                        seen_idle = True
            assert seen_idle
            assert not seen_done
            # The connection is still usable: a follow-up text turn completes.
            ws.send_text(json.dumps({"type": "text", "text": "what is the status?", "path_incident_id": INC_B}))
            kinds = drain_until_done(ws)
            assert "done" in kinds


class TestBrowserPage:
    def test_voice_test_page_served(self):
        client = TestClient(make_app())
        resp = client.get("/voice-test")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "WebSocket" in resp.text
        assert "getUserMedia" in resp.text
