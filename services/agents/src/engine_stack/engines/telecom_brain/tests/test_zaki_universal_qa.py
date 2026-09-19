"""Comprehensive tests for Zaki Universal AI Copilot & Knowledge Graph Reasoning."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.investigation.contracts import ZakiContextContract

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _chat(query: str, payload: dict | None = None) -> dict:
    body = {"query": query, "scenario_id": "SCN-001", "run_id": "RUN-TEST-001", **(payload or {})}
    res = client.post("/api/v1/fikracore/zaki/chat", json=body)
    assert res.status_code == 200
    return res.json()


def test_zaki_curated_story_generation():
    """Test Zaki generates an end-to-end curated incident story with multi-perspective sections."""
    data = _chat("Generate a curated incident story for this run", {"response_level": "engineer"})
    resp = data["response"]["response"]
    assert "Curated Incident Investigation Story" in resp or "Incident Genesis" in resp
    assert "Causal Propagation" in resp
    assert "Remediation" in resp


def test_zaki_curated_story_executive_level():
    """Test Zaki produces concise executive summaries when response_level=executive."""
    data = _chat("Give me the incident story for leadership", {"response_level": "executive"})
    resp = data["response"]["response"]
    assert "Executive" in resp
    assert "throughput" in resp.lower() or "subscribers" in resp.lower()


def test_zaki_what_if_resilience_analysis():
    """Test Zaki answers counterfactual what-if questions evaluating redundancy and failover."""
    data = _chat("What if PE-RTR-21 experiences complete link severance?")
    resp = data["response"]["response"]
    assert "What-If" in resp or "Resilience" in resp
    assert "redundancy" in resp.lower() or "failover" in resp.lower() or "capacity" in resp.lower()


def test_zaki_what_if_premature_failover_risk():
    """Test Zaki warns against premature traffic rerouting before root cause validation."""
    data = _chat("What if we reroute traffic right now before validation?")
    resp = data["response"]["response"]
    assert "Hazard" in resp or "Risk" in resp or "Premature" in resp
    assert "uncertainty" in resp.lower() or "misidentif" in resp.lower() or "secondary" in resp.lower()


def test_zaki_digital_twin_spatial_grounding():
    """Test Zaki provides exact spatial guidance on how to navigate the 3D Knowledge Graph."""
    data = _chat("How do I visualize this incident on the digital twin knowledge graph?")
    resp = data["response"]["response"]
    assert "Digital Twin" in resp or "Knowledge Graph" in resp
    assert "Beacon" in resp or "Conduit" in resp or "Blast Radius" in resp


def test_zaki_causal_why_evidence_necessity():
    """Test Zaki explains the exact causal rationale for why diagnostic probes are required."""
    data = _chat("Why do we need PE-RTR-21 health stats evidence right now?")
    resp = data["response"]["response"]
    assert "Causal" in resp or "Diagnostic" in resp or "Evidence" in resp
    assert "probe" in resp.lower() or "competing" in resp.lower() or "interface" in resp.lower()


def test_zaki_stage_briefing_and_next_steps():
    """Test Zaki explains the current stage status and recommends exact next steps."""
    data = _chat("What should I do right now and what is the current stage briefing?")
    resp = data["response"]["response"]
    assert "Stage" in resp or "Status" in resp
    assert "Recommended Next Action" in resp or "Next" in resp


def test_zaki_comparative_hypothesis_evaluation():
    """Test Zaki compares competing hypotheses dynamically with confidence scores."""
    data = _chat("Compare the competing hypotheses and explain why Rank 1 is preferred.")
    resp = data["response"]["response"]
    assert "Hypothesis" in resp or "Comparative" in resp or "Rank" in resp


def test_zaki_llm_system_prompt_builder():
    """Test that the LLM agent prompt builder assembles complete operational state with 0% truth leakage."""
    bridge = ZakiBridge()
    ctx = ZakiContextContract(
        active_scenario="SCN-001",
        active_stage="H1",
        active_presentation_mode="INVESTIGATION",
        current_presentation_step=5,
        visible_evidence=[{"category": "alarm", "title": "N3 Path Degradation", "severity": "critical"}],
        visible_topology={"domains": [{"name": "IP Transport"}, {"name": "5G Core"}]},
        current_hypotheses=[{"display_name": "PE-RTR-21 Backhaul Fault", "confidence": 92.5, "status": "LEADING"}],
        current_terminal_state="MODEL_INSUFFICIENT",
        knowledge_gap_state={"gaps": [{"label": "Router physical interface counter telemetry"}]},
        next_best_evidence=[{"display_name": "Inspect PE-RTR-21 CRC counters", "status": "READY"}],
        candidate_knowledge=[],
        validation_status="PENDING",
        human_readable_display_names={},
        learning_state=None,
        resilience_state=None,
    )
    ui_ctx = {
        "simulation_state": {
            "scenario": {"display_name": "Transport N3 Degradation Cascades into Mobile Data Failure"},
            "impact": {"throughput_impact_pct": 42, "affected_users": 18500},
            "recovery": {"action": "Isolate degraded path on PE-RTR-21 and reroute N3 user plane"},
        }
    }
    prompt = bridge._build_llm_system_prompt(ctx, ui_ctx, "the transport boundary")
    assert "Mark / Zaki" in prompt
    assert "SCN-001" in prompt
    assert "PE-RTR-21 Backhaul Fault" in prompt
    assert "Inspect PE-RTR-21 CRC counters" in prompt
    assert "truth-blind" in prompt.lower()
    assert "18,500" in prompt or "18500" in prompt
