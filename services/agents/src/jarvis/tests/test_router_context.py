from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import jarvis.router as jarvis_api


app = FastAPI()
app.include_router(jarvis_api.router)
client = TestClient(app)


class FakeJarvis:
    def __init__(self) -> None:
        self.session = SimpleNamespace(active_incident_id=None)
        self.session_store = SimpleNamespace(get=lambda _session_id: self.session)
        self.received_context = None

    async def process(self, message, session_id=None, context=None):
        self.received_context = context
        if context and context.get("incident_id"):
            self.session.active_incident_id = context["incident_id"]
        return "Incident story grounded in the selected incident."


def test_process_binds_incident_id_to_session_context(monkeypatch):
    jarvis = FakeJarvis()

    async def get_jarvis():
        return jarvis

    monkeypatch.setattr(jarvis_api, "_get_jarvis", get_jarvis)

    response = client.post(
        "/api/jarvis/process",
        json={
            "session_id": "zaki-context-test",
            "message": "Tell me the story.",
            "incident_id": "mobile-core/incidents/amf-overload-2026-08-09",
        },
    )

    assert response.status_code == 200
    assert jarvis.received_context["incident_id"] == "mobile-core/incidents/amf-overload-2026-08-09"
    assert response.json()["incident_id"] == "mobile-core/incidents/amf-overload-2026-08-09"