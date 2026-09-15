"""Test suite for Zaki 2.0 Contextual Copilot Interactions (§44).

Covers all 13 backend tests:
1. test_zaki_v2_selected_context_scoped_to_active_run
2. test_zaki_v2_selected_context_scoped_to_revision
3. test_zaki_v2_hypothesis_explanation_grounded
4. test_zaki_v2_pathway_explanation_grounded
5. test_zaki_v2_connection_explanation_grounded
6. test_zaki_v2_gap_explanation_grounded
7. test_zaki_v2_domain_explanation_uses_authoritative_attribution
8. test_zaki_v2_conflict_response
9. test_zaki_v2_replay_no_lookahead
10. test_zaki_v2_response_level
11. test_zaki_v2_structured_entities
12. test_zaki_v2_no_raw_html
13. test_zaki_v2_suggested_actions_governed
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import simulation_manager

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_zaki_v2_selected_context_scoped_to_active_run():
    """Test 1: Zaki response is scoped to the active run."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What is the status of this run?",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "STAGE",
                "context_id": "STAGE-1",
                "display_name": "Trigger Stage",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == run.run_id
    z2 = data.get("zaki_v2", {})
    assert z2.get("run_id") == run.run_id
    assert z2.get("selected_context", {}).get("context_type") == "STAGE"


def test_zaki_v2_selected_context_scoped_to_revision():
    """Test 2: Zaki validates revision boundaries (stale revision rejected)."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.snapshot_version = 5

    # Request with stale revision 3 < 5 should return 409
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain current state",
            "run_id": run.run_id,
            "revision": 3,
        },
    )
    assert res.status_code == 409
    assert "STALE_REVISION" in res.json()["detail"]


def test_zaki_v2_hypothesis_explanation_grounded():
    """Test 3: Selected hypothesis is grounded in live simulation state."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Why is this hypothesis leading?",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "HYPOTHESIS",
                "context_id": "HYP-001",
                "display_name": "H1 — Core Transport Failure",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "h1" in data["answer"].lower() or "hypothesis" in data["answer"].lower()
    assert data["grounded_in"].get("grounded_in_simulation") is True
    z2 = data.get("zaki_v2", {})
    assert len(z2.get("sections", [])) >= 2


def test_zaki_v2_pathway_explanation_grounded():
    """Test 4: Selected pathway is grounded in live simulation state."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain why this pathway is active",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "PATHWAY",
                "context_id": "PATH-SERVICE-DEPENDENCY",
                "display_name": "Service Dependency",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "service dependency" in data["answer"].lower()
    assert "PATH-SERVICE-DEPENDENCY" in data["grounded_in"].get("pathway_ids", [])
    assert data["grounded_in"].get("internet_access") is False


def test_zaki_v2_connection_explanation_grounded():
    """Test 5: Selected connection between evidence and pathway is explained."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain this connection",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "CONNECTION",
                "context_id": "CONN-001",
                "display_name": "BGP Alarm → Service Dependency",
                "metadata": {
                    "source": "BGP Alarm",
                    "target": "Service Dependency",
                    "reason": "BGP failure directly impairs service routing",
                },
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["grounded_in"].get("grounded_in_simulation") is True


def test_zaki_v2_gap_explanation_grounded():
    """Test 6: Selected knowledge gap is explained with blocking reasons."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What does this knowledge gap block?",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "KNOWLEDGE_GAP",
                "context_id": "GAP-001",
                "display_name": "Redundant MPLS Path Health Unknown",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "gap" in ans or "missing" in ans or "block" in ans


def test_zaki_v2_domain_explanation_uses_authoritative_attribution():
    """Test 7: Selected domain explanation derives strictly from authoritative attribution."""
    run = simulation_manager.create_run(scenario_id="H4-WI-036")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Why is this domain attribution assigned this role?",
            "run_id": run.run_id,
            "selected_context": {
                "context_type": "DOMAIN_ATTRIBUTION",
                "context_id": "transport",
                "display_name": "Transport",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "transport" in ans
    assert data["grounded_in"].get("role") in {"PRIMARY", "CONTRIBUTING", "AFFECTED", "MONITOR ONLY"}


def test_zaki_v2_conflict_response():
    """Test 8: Explicit conflict response when domain attribution is in CONFLICT."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    # Simulate a conflict state in simulation manager state
    run.state_overrides["domain_attribution"] = {
        "attribution_status": "CONFLICT",
        "conflict_reasons": ["Leading hypothesis points to Transport but RAN is PRIMARY"],
        "domains": [],
    }

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Who caused this incident?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "conflict" in data["answer"].lower()
    assert data["grounded_in"].get("attribution_status") == "CONFLICT"


def test_zaki_v2_replay_no_lookahead():
    """Test 9: Replay mode enforces no lookahead beyond current cursor."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.is_replay = True
    run.replay_position = 2

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What will happen next in the future?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "replay mode" in ans
    assert "future" in ans or "restricted" in ans


def test_zaki_v2_response_level():
    """Test 10: Response levels (Executive, Operator, Engineer, Deep Technical) are respected."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    for level in ["executive", "operator", "engineer", "deep_technical"]:
        res = client.post(
            "/api/v1/fikracore/zaki/chat",
            json={
                "query": "Summarize the incident status",
                "run_id": run.run_id,
                "response_level": level,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["response_level"] == level
        z2 = data.get("zaki_v2", {})
        assert z2.get("response_level") == level.upper()


def test_zaki_v2_structured_entities():
    """Test 11: Entities returned have visual_role (STRUCTURE, FOCUS, CONFIRMED)."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain the Transport domain and H1 hypothesis",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    entities = data.get("entities", [])
    assert len(entities) > 0
    roles = {e.get("visual_role") for e in entities}
    assert any(r in {"STRUCTURE", "FOCUS", "CONFIRMED"} for r in roles)


def test_zaki_v2_no_raw_html():
    """Test 12: Zaki responses do not contain raw HTML tags like <div>, <span>, or <script>."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain what happened in detail",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"]
    assert "<script" not in ans
    assert "<div" not in ans
    assert "<span" not in ans


def test_zaki_v2_suggested_actions_governed():
    """Test 13: Suggested actions are governed actions with action_type and enabled status."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What should I do next?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    actions = data.get("suggested_actions", [])
    assert isinstance(actions, list)
    if actions:
        act = actions[0]
        assert "action_id" in act
        assert "action_type" in act
        assert "enabled" in act
        assert isinstance(act["enabled"], bool)


def test_zaki_v2_pathway_ui_slug_and_revision_advancement():
    """Test 14: UI pathway slugs ('dependency', 'operational') and advanced revision do not crash."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.stage_index = 5
    run.snapshot_version = 6

    # 1. UI slug 'dependency' with 'Service Dependency'
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain pathway Service Dependency",
            "scenario_id": "SCN-001",
            "run_id": run.run_id,
            "revision": 6,
            "response_level": "engineer",
            "selected_context": {
                "context_type": "PATHWAY",
                "context_id": "dependency",
                "display_name": "Service Dependency",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "Service Dependency" in data["answer"]
    assert "PATH-SERVICE-DEPENDENCY" in data["grounded_in"]["pathway_ids"]
    assert data["grounded_in"]["grounded_in_simulation"] is True
    assert data["zaki_v2"]["copilot_state"] in {"REASONING", "NEEDS_EVIDENCE", "VALIDATION_REQUIRED", "RECOMMENDATION_READY"}
    assert len(data["zaki_v2"]["sections"]) >= 2

