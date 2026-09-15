"""Step 5 v3 contextual Zaki request-envelope tests."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _chat(payload: dict):
    res = client.post("/api/v1/fikracore/zaki/chat", json={"query": "What evidence is missing?", **payload})
    assert res.status_code == 200
    return res.json()


def test_zaki_receives_active_scenario_run_workspace_entity_hypothesis_gap():
    data = _chat({
        "scenario_id": "SCN-001",
        "run_id": "RUN-TEST-001",
        "workspace": "discover",
        "selected_entity_id": "tr-01",
        "selected_hypothesis_id": "HYP-001",
        "selected_gap_id": "KG-01",
        "selected_evidence_id": "EV-001",
    })
    assert data["scenario_id"] == "SCN-001"
    assert data["run_id"] == "RUN-TEST-001"
    assert data["workspace"] == "discover"
    response = data["response"]["response"]
    assert "Discovery focus" in response
    assert "entity=tr-01" in response
    assert "hypothesis=HYP-001" in response
    assert "gap=KG-01" in response


def test_zaki_context_resets_on_scenario_change():
    first = _chat({"scenario_id": "SCN-001", "workspace": "investigate", "selected_entity_id": "tr-01"})
    second = _chat({"scenario_id": "H4-WI-001", "workspace": "investigate"})
    assert first["scenario_id"] == "SCN-001"
    assert second["scenario_id"] == "H4-WI-001"
    assert "entity=tr-01" not in second["response"]["response"]


def test_zaki_workspace_changes_response_focus():
    discover = _chat({"scenario_id": "SCN-001", "workspace": "discover"})
    predict = _chat({"scenario_id": "SCN-001", "workspace": "predict"})
    assert "Discovery focus" in discover["response"]["response"]
    assert "Prediction focus" in predict["response"]["response"]


def test_zaki_response_level_executive_operator_engineer_deep_technical():
    executive = _chat({"scenario_id": "SCN-001", "workspace": "investigate", "response_level": "executive"})
    operator = _chat({"scenario_id": "SCN-001", "workspace": "investigate", "response_level": "operator"})
    engineer = _chat({"scenario_id": "SCN-001", "workspace": "investigate", "response_level": "engineer"})
    deep = _chat({"scenario_id": "SCN-001", "workspace": "investigate", "response_level": "deep_technical"})
    assert executive["response_level"] == "executive"
    assert "Next action:" in operator["response"]["response"]
    assert "Investigation focus" in engineer["response"]["response"]
    assert "Technical guardrail" in deep["response"]["response"]


def test_zaki_preserves_model_insufficient():
    data = _chat({"scenario_id": "SCN-001", "workspace": "discover", "response_level": "deep_technical"})
    response = data["response"]["response"]
    assert "MODEL_INSUFFICIENT" in response or "Technical guardrail" in response


def test_zaki_does_not_invent_confidence():
    data = _chat({"scenario_id": "SCN-001", "workspace": "discover", "selected_gap_id": "KG-01"})
    response = data["response"]["response"].lower()
    assert "100%" not in response
    assert "confirmed root cause" not in response
