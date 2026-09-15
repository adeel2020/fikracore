"""Test suite for Zaki Reasoning Pathways Grounding & Zero-Internet Verification."""

from fastapi.testclient import TestClient
import pytest
from fastapi import FastAPI

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import simulation_manager

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_zaki_explains_specific_pathway_from_simulation():
    """Verify Zaki explains a specific pathway using live simulation state."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.stage_index = 3
    run.snapshot_version = 4

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain the Service Dependency pathway",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "service dependency" in ans
    assert "grounded strictly in local simulation run" in ans or "simulation" in ans
    assert "internet" in ans or "offline" in ans

    grounded = data["grounded_in"]
    assert "PATH-SERVICE-DEPENDENCY" in grounded.get("pathway_ids", [])
    assert grounded.get("internet_access") is False
    assert grounded.get("grounded_in_simulation") is True


def test_zaki_explains_pathway_via_selected_pathway_id():
    """Verify Zaki grounds response when selected_pathway_id is passed."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.stage_index = 2
    run.snapshot_version = 3

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What is the status of this selected pathway?",
            "run_id": run.run_id,
            "selected_pathway_id": "PATH-RESILIENCE-FAILOVER",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "resilience" in data["answer"].lower()
    assert "PATH-RESILIENCE-FAILOVER" in data["grounded_in"].get("pathway_ids", [])
    assert data["grounded_in"].get("internet_access") is False


def test_zaki_explains_pathway_via_selected_context_object():
    """Verify Zaki grounds response when selected_context with type=pathway is passed."""
    run = simulation_manager.create_run(scenario_id="SCN-001")

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Explain what this pathway evaluates",
            "run_id": run.run_id,
            "selected_context": {
                "type": "pathway",
                "id": "PATH-TOPOLOGY-PROPAGATION",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "topology" in data["answer"].lower()
    assert "PATH-TOPOLOGY-PROPAGATION" in data["grounded_in"].get("pathway_ids", [])
    assert data["grounded_in"].get("internet_access") is False


def test_zaki_explains_all_pathways_overview():
    """Verify Zaki provides a multi-pathway overview strictly from simulation."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.stage_index = 4

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What are all the reasoning pathways active in this simulation?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "reasoning pathways" in ans
    assert "never sourced from the internet" in ans or "simulation" in ans
    assert len(data["grounded_in"].get("pathway_ids", [])) > 0
    assert data["grounded_in"].get("internet_access") is False


def test_zaki_asserts_zero_internet_dependency():
    """Verify Zaki explicitly confirms zero internet dependency and air-gapped simulation grounding."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Did you search the web or internet for this incident?",
            "scenario_id": "SCN-001",
        },
    )
    assert res.status_code == 200
    data = res.json()
    ans = data["answer"].lower()
    assert "air-gapped" in ans or "offline" in ans or "never queries" in ans
    assert "internet" in ans
    assert data["grounded_in"].get("internet_access") is False
    assert data["grounded_in"].get("grounded_in_simulation") is True
