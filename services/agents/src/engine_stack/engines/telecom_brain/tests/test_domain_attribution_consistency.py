"""Test suite for FikraCore Step 5.2.1 Domain Attribution & Zaki Context Consistency (§22, §23)."""

from fastapi.testclient import TestClient
import pytest

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import simulation_manager
from engine_stack.engines.telecom_brain.simulator.scenario_state_compiler import (
    get_compiler,
    validate_domain_attribution,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.investigation.contracts import ZakiContextContract

from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_primary_domain_requires_reason():
    """Verify PRIMARY domain has mandatory non-empty explanation reason (§6)."""
    compiler = get_compiler()
    state = compiler.compile_state("SCN-001", stage_index=6)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    primary = next((d for d in da.get("domains", []) if d.get("role") == "PRIMARY"), None)
    assert primary is not None, "At stage 6, PRIMARY domain should be assigned"
    assert primary.get("reason") is not None and len(primary.get("reason").strip()) > 0
    assert primary.get("attribution_basis") == "CAUSAL"


def test_primary_domain_requires_supporting_hypothesis():
    """Verify PRIMARY domain has supporting hypothesis IDs (§6)."""
    compiler = get_compiler()
    state = compiler.compile_state("SCN-001", stage_index=6)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    primary = next((d for d in da.get("domains", []) if d.get("role") == "PRIMARY"), None)
    assert primary is not None
    assert len(primary.get("supporting_hypothesis_ids", [])) > 0


def test_attribution_source_revision_matches_run_revision():
    """Verify domain attribution revision and source_revision match the run revision (§8)."""
    compiler = get_compiler()
    state = compiler.compile_state("SCN-001", stage_index=6)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    assert da.get("revision") is not None
    primary = next((d for d in da.get("domains", []) if d.get("role") == "PRIMARY"), None)
    if primary:
        assert primary.get("source_revision") == da.get("revision")


def test_stale_attribution_marked_unresolved():
    """Verify stale domain attribution is detected and marked UNRESOLVED (§8)."""
    state = {
        "snapshot_version": 5,
        "hypotheses": [{"display_name": "Core Router Failure"}],
        "domain_attribution": {
            "revision": 3,
            "status": "READY",
            "attribution_status": "CONSISTENT",
            "domains": [{"role": "PRIMARY", "display_name": "Transport", "reason": "Test", "supporting_hypothesis_ids": ["H1"]}],
        },
    }
    validated = validate_domain_attribution(state)
    assert validated.get("attribution_status") == "UNRESOLVED"
    assert validated.get("stale_attribution") is True


def test_impact_score_does_not_assign_primary_domain():
    """Verify AFFECTED domain with high impact is NOT assigned role PRIMARY with CAUSAL basis (§5, §11)."""
    compiler = get_compiler()
    state = compiler.compile_state("SCN-001", stage_index=6)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    affected = [d for d in da.get("domains", []) if d.get("role") == "AFFECTED"]
    for d in affected:
        assert d.get("attribution_basis") == "IMPACT"
        assert d.get("role") != "PRIMARY"


def test_canonical_entity_to_domain_mapping():
    """Verify canonical entity resolution correctly identifies domains without guessing (§10)."""
    compiler = get_compiler()
    assert compiler._entity_domain("IP:CORE:RTR-01", "Core Transport Router-01") == "Transport"
    assert compiler._entity_domain("UPF-01", "Core User Plane Function") == "Mobile Core"
    assert compiler._entity_domain("GNB-SITE-44", "RAN Cell-44") == "RAN"
    assert compiler._entity_domain("IMS-SBC-01", "Session Border Controller") == "IMS"


def test_domain_attribution_conflict_detected():
    """Verify inconsistency between leading hypothesis and primary domain is flagged as CONFLICT (§9)."""
    state = {
        "hypotheses": [{"display_name": "Core Transport Router Outage"}],
        "domain_attribution": {
            "status": "READY",
            "attribution_status": "CONSISTENT",
            "domains": [
                {
                    "role": "PRIMARY",
                    "display_name": "RAN",
                    "reason": "Test",
                    "supporting_hypothesis_ids": ["H1"],
                    "attribution_basis": "CAUSAL",
                }
            ],
        },
    }
    validated = validate_domain_attribution(state)
    assert validated.get("attribution_status") == "CONFLICT"
    assert len(validated.get("conflict_reasons", [])) > 0


def test_h4_wi_36_attribution_consistency():
    """Verify scenario H4-WI-036 attributes to Transport/IP Transport with no UI/Zaki conflict (§20)."""
    compiler = get_compiler()
    state = compiler.compile_state("H4-WI-036", stage_index=6)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    primary = next((d for d in da.get("domains", []) if d.get("role") == "PRIMARY"), None)
    assert primary is not None, "H4-WI-036 at stage 6 should have a PRIMARY domain"
    assert primary.get("display_name") in ["Transport", "IP Transport"]
    assert primary.get("attribution_basis") == "CAUSAL"


def test_zaki_uses_authoritative_domain_attribution():
    """Verify Zaki answers domain attribution using authoritative backend domain_attribution object (§13, §14)."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.stage_index = 6
    run.snapshot_version = 6
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Why is this domain primary?", "run_id": run.run_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert "primary" in data["answer"].lower()
    assert data["grounded_in"].get("role") == "PRIMARY"


def test_zaki_reports_attribution_conflict():
    """Verify Zaki reports ATTRIBUTION CONFLICT when backend state has conflict (§15)."""
    bridge = ZakiBridge()
    context = ZakiContextContract(
        active_scenario="H4-WI-036",
        active_stage="STAGE_6",
        active_presentation_mode="INVESTIGATION",
        current_presentation_step=6,
        current_hypotheses=[{"display_name": "H1 — Core Router Failure"}],
    )
    ui_context = {
        "simulation_state": {
            "domain_attribution": {
                "attribution_status": "CONFLICT",
                "conflict_reasons": ["Leading hypothesis implies Transport, but PRIMARY domain is RAN"],
                "domains": [],
            }
        }
    }
    ans = bridge.answer_query("Why is RAN primary?", context, ui_context=ui_context)
    resp = ans.get("response", "")
    assert "conflict" in resp.lower()
    assert ans["grounded_in"].get("attribution_status") == "CONFLICT"


def test_zaki_rejects_stale_revision():
    """Verify /zaki/chat rejects stale revisions with 409 STALE_REVISION (§16, §17)."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.snapshot_version = 4
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Status check", "run_id": run.run_id, "revision": 2},
    )
    assert res.status_code == 409
    assert "STALE_REVISION" in res.json()["detail"]


def test_zaki_rejects_future_revision():
    """Verify /zaki/chat rejects invalid future revisions with 409 INVALID_REVISION (§16, §17)."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    run.snapshot_version = 2
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Status check", "run_id": run.run_id, "revision": 5},
    )
    assert res.status_code == 409
    assert "INVALID_REVISION" in res.json()["detail"]


def test_zaki_returns_highlighted_entities():
    """Verify Zaki response includes structured highlighted entities with cyan/magenta (§27.9)."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "What is the status of H1 and IP Transport?", "scenario_id": "SCN-001"},
    )
    assert res.status_code == 200
    data = res.json()
    entities = data.get("entities", [])
    assert isinstance(entities, list)
    assert len(entities) > 0
    cyan_entities = [e for e in entities if e.get("highlight") == "CYAN"]
    magenta_entities = [e for e in entities if e.get("highlight") == "MAGENTA"]
    assert len(cyan_entities) > 0, "Should have CYAN highlighted operational entities/domains"
    assert len(magenta_entities) > 0, "Should have MAGENTA highlighted identifiers/hypotheses"
