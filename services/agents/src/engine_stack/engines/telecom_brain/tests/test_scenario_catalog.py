"""Tests for Unified Scenario Catalog and Conceptual Model Mapping (§7, §8, §23)."""

import pytest
from fastapi.testclient import TestClient
from ..simulator.scenario_catalog import (
    scenario_catalog,
    concept_for_stage,
    stage_for_concept,
    STAGE_CONCEPT_MAP,
)
from ..presentation.scenario_resolver import ScenarioResolver, get_unified_registry
from ..api.capability_api import router
from fastapi import FastAPI


@pytest.fixture
def api_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_stage_concept_mapping():
    assert STAGE_CONCEPT_MAP["H1"] == "Understand"
    assert STAGE_CONCEPT_MAP["H2"] == "Discover"
    assert STAGE_CONCEPT_MAP["H3"] == "Learn"
    assert STAGE_CONCEPT_MAP["H4"] == "Anticipate"

    assert concept_for_stage("H1") == "Understand"
    assert concept_for_stage("H2") == "Discover"
    assert concept_for_stage("H3") == "Learn"
    assert concept_for_stage("H4") == "Anticipate"

    assert stage_for_concept("Understand") == "H1"
    assert stage_for_concept("Discover") == "H2"
    assert stage_for_concept("Learn") == "H3"
    assert stage_for_concept("Anticipate") == "H4"


def test_catalog_returns_demo_001():
    demo = scenario_catalog.get("DEMO-001")
    assert demo is not None
    assert demo.id == "DEMO-001"
    assert demo.stage == "H1"
    assert demo.concept == "Understand"
    assert demo.scenario_type == "INCIDENT"
    assert demo.demo_enabled is True
    assert "Transport" in demo.domains or "IP TRANSPORT" in [d.upper() for d in demo.domains]


def test_catalog_returns_scn_001_as_understand():
    scn = scenario_catalog.get("SCN-001")
    assert scn is not None
    assert scn.id == "SCN-001"
    assert scn.stage == "H1"
    assert scn.concept == "Understand"
    assert scn.scenario_type == "INCIDENT"


def test_catalog_returns_all_conceptual_groups():
    understand_scenarios = scenario_catalog.filter_by_concept("Understand")
    discover_scenarios = scenario_catalog.filter_by_concept("Discover")
    learn_scenarios = scenario_catalog.filter_by_concept("Learn")
    anticipate_scenarios = scenario_catalog.filter_by_concept("Anticipate")

    assert len(understand_scenarios) >= 2  # DEMO-001 and SCN-001
    assert len(discover_scenarios) >= 1   # H2-GAP-001 / H2-SCN-*
    assert len(learn_scenarios) >= 1      # H3-LRN-001 / H3-LU-*
    assert len(anticipate_scenarios) >= 10  # H4-WI-*


def test_scenario_resolver_resolves_demo_001():
    reg = get_unified_registry()
    resolver = ScenarioResolver(reg)
    rec, _, _ = resolver.resolve_or_disambiguate("DEMO-001")
    assert rec is not None
    assert rec.id == "DEMO-001"
    assert rec.stage == "H1"
    assert rec.concept == "Understand"


def test_api_scenarios_endpoint(api_client):
    res = api_client.get("/api/v1/fikracore/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    scenarios = data["scenarios"]
    ids = {s["id"] for s in scenarios}
    assert "DEMO-001" in ids
    assert "SCN-001" in ids
    assert "H4-WI-001" in ids

    # Check concepts
    concepts = {s["concept"] for s in scenarios}
    assert "Understand" in concepts
    assert "Discover" in concepts
    assert "Learn" in concepts
    assert "Anticipate" in concepts


def test_api_scenarios_endpoint_filter_by_concept(api_client):
    res = api_client.get("/api/v1/fikracore/scenarios?concept=Understand")
    assert res.status_code == 200
    data = res.json()
    for s in data["scenarios"]:
        assert s["concept"] == "Understand"
        assert s["stage"] == "H1"


def test_scenario_catalog_get_yaml():
    content, filename, is_ro = scenario_catalog.get_yaml("DEMO-001")
    assert "DEMO-001" in content
    assert filename.endswith(".yaml")
    assert is_ro is False

    # Also test SCN-001
    scn_content, scn_file, _ = scenario_catalog.get_yaml("SCN-001")
    assert "SCN-001" in scn_content


def test_scenario_catalog_yaml_validation():
    # Invalid YAML should fail gracefully
    ok, err = scenario_catalog.save_yaml("DEMO-001", "invalid: yaml: :")
    assert ok is False
    assert "YAML" in err


def test_api_scenario_yaml_endpoints(api_client):
    res = api_client.get("/api/v1/fikracore/scenarios/DEMO-001/yaml")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "DEMO-001" in data["content"]
    assert data["filename"].endswith(".yaml")
