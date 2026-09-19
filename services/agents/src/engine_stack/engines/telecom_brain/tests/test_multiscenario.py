"""Step 5 v3 multi-scenario discovery and capability availability tests."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import simulation_manager


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_scenario_registry_loaded_from_backend():
    res = client.get("/api/v1/fikracore/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["total_scenarios"] >= 2
    first = data["scenarios"][0]
    for field in ["id", "display_name", "aliases", "stage", "capabilities", "domains", "services", "difficulty", "status", "source"]:
        assert field in first


def test_multiple_scenarios_supported():
    scenarios = client.get("/api/v1/fikracore/scenarios").json()["scenarios"]
    ids = {scenario["id"] for scenario in scenarios}
    assert "SCN-001" in ids
    assert "H4-WI-001" in ids


def test_no_hardcoded_scn001_dependency():
    res = client.get("/api/v1/fikracore/scenarios/H4-WI-001/state")
    assert res.status_code == 200
    state = res.json()
    assert state["scenario"]["id"] == "H4-WI-001"
    assert state["run"]["scenario_id"] == "H4-WI-001"


def test_scenario_search_filter_by_stage_domain_service():
    scenarios = client.get("/api/v1/fikracore/scenarios").json()["scenarios"]
    h4 = [s for s in scenarios if s["stage"] == "H4"]
    transport = [s for s in scenarios if "Transport" in s["domains"]]
    mobile_data = [s for s in scenarios if any("Mobile Data" in srv for srv in s.get("services", []))]
    assert h4
    assert transport
    assert any(s["id"] == "SCN-001" for s in mobile_data)


def test_scenario_alias_resolution():
    res = client.get("/api/v1/fikracore/scenarios/edge router outage")
    assert res.status_code == 200
    assert res.json()["scenario"]["id"] == "H4-WI-001"


def test_scenario_switch_clears_stale_state():
    scn1 = simulation_manager.get_state("SCN-001")
    scn2 = simulation_manager.get_state("H4-WI-001")
    assert scn1["scenario"]["id"] == "SCN-001"
    assert scn2["scenario"]["id"] == "H4-WI-001"
    assert scn2["run"]["scenario_id"] == "H4-WI-001"


def test_scenario_capability_availability():
    res = client.get("/api/v1/fikracore/scenarios/H4-WI-001/capabilities")
    assert res.status_code == 200
    caps = res.json()["capabilities"]
    assert caps["investigate"] is True
    assert caps["discover"] is True
    assert caps["learn"] is True
    assert caps["predict"] is True


def test_multiple_runs_per_scenario():
    first = client.post("/api/v1/fikracore/simulations", json={"scenario_id": "SCN-001", "speed": 1.0}).json()
    second = client.post("/api/v1/fikracore/simulations", json={"scenario_id": "H4-WI-001", "speed": 1.0}).json()
    assert first["run_id"] != second["run_id"]
    assert first["scenario_id"] == "SCN-001"
    assert second["scenario_id"] == "H4-WI-001"
