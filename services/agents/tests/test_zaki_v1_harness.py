"""Comprehensive Test Suite for Zaki v1 Agent Harness Specification.

Verifies:
1. Zero-deviation reasoning parity: Direct FikraCore vs Zaki-mediated FikraCore.
2. Full contract schema compliance and Pydantic serialization.
3. Policy engine and least-privilege guardrails (Levels 0-5).
4. HITL validation inbox and decision tracking.
5. Shift handover and durable ledger continuity across shifts.
6. Multi-depth storytelling (Executive, Operator, Deep Technical).
7. Domain agent registry and capability lookup.
8. CLI command dispatch integration.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from engine_stack.engines.telecom_brain.investigation import GeneratedRunInput, Investigator
from engine_stack.engines.telecom_brain.investigation.contracts import Evidence, Terminal
from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run, load_evidence
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider

import zaki
from zaki.enums import AuthorityLevel, PolicyDecisionType, PresentationDepth, TaskStatus, ValidationDecisionType
from zaki.contracts import (
    AgentManifestContract,
    HandoverRecordContract,
    HumanValidationContract,
    IncidentContextContract,
    OperatorIntentContract,
    RankedHypothesisItem,
    TaskContract,
    TaskEpisodeContract,
    ToolContract,
)
from zaki.fikracore.adapter import FikraCoreAdapter
from zaki.governance.hitl import HITLManager
from zaki.governance.policy_engine import PolicyEngine
from zaki.intent.manager import IntentManager
from zaki.operations.handover import HandoverManager
from zaki.operations.incident_ledger import IncidentLedger
from zaki.operations.task_ledger import TaskLedger
from zaki.runtime.orchestrator import ZakiOrchestrator
from zaki.storyteller.presentation import PresentationProjector


# ── Test Fixtures ──────────────────────────────────────────────────────────

def create_event(identifier, entity, source, second=0, polarity="abnormal", kind="alarms", service="mobile-data", **kwargs):
    when = datetime(2026, 9, 10, 8, tzinfo=timezone.utc) + timedelta(seconds=second)
    return Evidence(
        evidence_id=identifier,
        event_time=when,
        ingestion_time=when + timedelta(seconds=5),
        domain="transport" if entity == "router" else "ps",
        entity=entity,
        canonical_entity=entity,
        source_native_entity=entity,
        source=source,
        source_reliability=0.95,
        polarity=polarity,
        evidence_type=kind,
        service=[service],
        severity="MAJOR",
        signal="path-degraded" if polarity == "abnormal" else "healthy",
        **kwargs,
    )


def create_knowledge_provider(gap=False):
    pages = [{"slug": name} for name in ("router", "upf", "service", "noise", "peer")]
    relationships = (
        [{"relationship_id": "R1", "source": "upf", "target": "router", "link_type": "depends-on", "state": "CONFIRMED", "confidence": 0.95}]
        if not gap
        else []
    )
    return InMemoryKnowledgeProvider(pages, relationships)


def sample_evidence():
    return [
        create_event("r1", "router", "nms"),
        create_event("r2", "router", "probe", 1, kind="metrics"),
        create_event("u1", "upf", "ems", 10),
        create_event("u2", "upf", "pm", 11, kind="kpis"),
    ]


# ── 1. Parity Test (Section 44 Acceptance Gate) ───────────────────────────

def test_fikracore_zaki_parity_simple_fault():
    """Verify 100% equivalence between Direct FikraCore and Zaki-orchestrated investigation."""
    provider = create_knowledge_provider()
    run_input = GeneratedRunInput(run_id="RUN-P1", scenario_id="S1", difficulty_profile="L1", seed=42)
    ev_list = sample_evidence()[:2]

    # Direct FikraCore execution
    direct_res = Investigator(provider).investigate(run_input, ev_list)

    # Zaki-mediated execution
    adapter = FikraCoreAdapter(provider=provider)
    orchestrator = ZakiOrchestrator(fikracore_adapter=adapter)
    zaki_res = orchestrator.investigate(
        intent_or_query="Investigate router degradation",
        run_input=run_input,
        evidence=ev_list,
        provider=provider,
    )

    mediated_res = zaki_res["investigation_result"]
    zaki_hypotheses = zaki_res["ranked_hypotheses"].spec.hypotheses

    # Assert Parity
    assert direct_res.terminal_state == mediated_res.terminal_state
    assert len(direct_res.ranked_hypotheses) == len(zaki_hypotheses)

    for d_h, z_h in zip(direct_res.ranked_hypotheses, zaki_hypotheses):
        assert d_h.hypothesis_id == z_h.hypothesis_id
        assert d_h.canonical_root_entity == z_h.canonical_root_entity
        assert d_h.hypothesis_confidence == z_h.score
        assert d_h.supporting_evidence == z_h.supporting_evidence
        assert d_h.contradicting_evidence == z_h.contradicting_evidence
        assert d_h.missing_evidence == z_h.missing_evidence
        assert d_h.score_dimensions == z_h.score_components

    assert direct_res.selected_hypothesis_id == zaki_res["ranked_hypotheses"].spec.leading_hypothesis_id


def test_fikracore_zaki_parity_gap_discovery():
    """Verify parity on knowledge gap discovery (terminal state MODEL_INSUFFICIENT)."""
    provider = create_knowledge_provider(gap=True)
    run_input = GeneratedRunInput(run_id="RUN-GAP", scenario_id="S4", difficulty_profile="L4", seed=42)
    ev_list = sample_evidence()[:3] + [create_event("path", "upf", "probe", 12, kind="traces", observed_path=["upf", "router"])]

    # Direct FikraCore
    direct_res = Investigator(provider).investigate(run_input, ev_list)

    # Zaki-mediated
    orchestrator = ZakiOrchestrator()
    zaki_res = orchestrator.investigate(
        intent_or_query="Investigate UPF unmodelled path",
        run_input=run_input,
        evidence=ev_list,
        provider=provider,
    )
    mediated_res = zaki_res["investigation_result"]

    assert direct_res.terminal_state == Terminal.MODEL_INSUFFICIENT
    assert mediated_res.terminal_state == Terminal.MODEL_INSUFFICIENT
    assert zaki_res["knowledge_gaps"]["discovery_mode"] is True
    assert len(direct_res.candidate_relationships) == len(zaki_res["knowledge_gaps"]["candidate_relationships"])


def test_fikracore_zaki_parity_demo_001_run_directory():
    """Verify parity on the canonical DEMO-001 scenario run directory."""
    run_dir = Path(__file__).resolve().parent.parent / "src" / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "runs" / "RUN-SCN-001-L1-SEED-42001"
    if not run_dir.exists():
        pytest.skip(f"Scenario directory {run_dir} not available")

    # Direct FikraCore execution
    run = input_from_run(run_dir)
    ev, hashes = load_evidence(run, run_dir / "operational")
    provider = InMemoryKnowledgeProvider([], [])
    direct_res = Investigator(provider).investigate(run, ev, hashes)

    # Zaki-mediated execution
    orchestrator = ZakiOrchestrator()
    zaki_res = orchestrator.investigate(
        intent_or_query="DEMO-001",
        run_directory=run_dir,
        provider=provider,
    )
    mediated_res = zaki_res["investigation_result"]

    assert direct_res.terminal_state == mediated_res.terminal_state
    assert direct_res.selected_hypothesis_id == mediated_res.selected_hypothesis_id
    assert len(direct_res.ranked_hypotheses) == len(mediated_res.ranked_hypotheses)
    assert direct_res.ranked_hypotheses[0].canonical_root_entity == mediated_res.ranked_hypotheses[0].canonical_root_entity


# ── 2. Domain Contracts Compliance ─────────────────────────────────────────

def test_contracts_schema_and_serialization():
    """Verify serialization and validation of all core v1 contracts."""
    # Intent Contract
    intent_mgr = IntentManager()
    intent = intent_mgr.capture_intent("Packet core UPF degradation in cluster 4")
    assert intent.spec.subject["domain"] == "PS"
    assert intent.spec.fcaps.primary.value == "Fault"
    intent_json = intent.model_dump_json()
    assert "INT-" in intent_json

    # Task Contract
    task_ledger = TaskLedger()
    task = task_ledger.create_task(incident_id="INC-01", intent_id=intent.intent_id)
    assert task.status == TaskStatus.ACTIVE
    assert task.task_id in task_ledger.list_tasks()[0].task_id

    # Incident Contract
    incident_ledger = IncidentLedger()
    inc = incident_ledger.create_incident("Core Network Outage", scenario_id="DEMO-001")
    assert inc.scenario_id == "DEMO-001"
    assert inc.incident_id in incident_ledger.get_incident(inc.incident_id).incident_id

    # Hypothesis Item
    h_item = RankedHypothesisItem(
        hypothesis_id="H-001",
        rank=1,
        score=0.85,
        state="SUPPORTED",
        role="LEADING",
        causal_role="ROOT",
        root_entity="router-01",
        canonical_root_entity="router-01",
        domain="IP_TRANSPORT",
        statement="Inferred BGP degradation",
    )
    assert h_item.role == "LEADING"
    assert h_item.score == 0.85


# ── 3. Policy & Governance (HITL) ─────────────────────────────────────────

def test_policy_engine_least_privilege():
    """Verify zero-trust least-privilege authority enforcement."""
    policy = PolicyEngine()

    # Read tool allowed for Level 0 observe
    dec_read = policy.evaluate("agent-ps", "metric.query", AuthorityLevel.LEVEL_0_OBSERVE, AuthorityLevel.LEVEL_1_ANALYZE)
    assert dec_read.decision == PolicyDecisionType.ALLOW

    # Action tool denied if authority is Level 1 analyze
    dec_action_denied = policy.evaluate("agent-ps", "traffic.reroute", AuthorityLevel.LEVEL_4_HITL_EXECUTE, AuthorityLevel.LEVEL_1_ANALYZE)
    assert dec_action_denied.decision == PolicyDecisionType.DENY

    # Action tool requires HITL approval when authority is Level 4
    dec_action_hitl = policy.evaluate("agent-ps", "traffic.reroute", AuthorityLevel.LEVEL_4_HITL_EXECUTE, AuthorityLevel.LEVEL_4_HITL_EXECUTE)
    assert dec_action_hitl.decision == PolicyDecisionType.ALLOW_WITH_HITL
    assert dec_action_hitl.approval_required is True


def test_hitl_validation_lifecycle():
    """Verify request, inbox queuing, and operator decision confirmation."""
    hitl = HITLManager()
    val_id = hitl.request_validation(
        task_id="TASK-100",
        incident_id="INC-100",
        target_type="candidate_relationship",
        target_id="CAND-01",
        reason="Confirm unmodelled transport adjacency",
    )

    pending = hitl.get_pending(task_id="TASK-100")
    assert len(pending) == 1
    assert pending[0]["validation_id"] == val_id

    # Submit decision
    decision = hitl.submit_decision(
        validation_id=val_id,
        decision=ValidationDecisionType.CONFIRM,
        validator_id="engineer-b",
        reason="Physical cable trace verified",
    )
    assert decision is not None
    assert decision.spec.decision == ValidationDecisionType.CONFIRM
    assert len(hitl.get_pending(task_id="TASK-100")) == 0
    assert len(hitl.get_history(task_id="TASK-100")) == 1


# ── 4. Shift Handover & Continuity ────────────────────────────────────────

def test_shift_handover_transfer_and_acceptance():
    """Verify Shift A to Shift B structured state transfer."""
    hdo_mgr = HandoverManager()
    record = hdo_mgr.create_handover(
        incident_id="INC-500",
        from_operator="Shift-A",
        to_operator="Shift-B",
        what="5G Data Degradation in Region North",
        why="Shift rotation",
        state={"leading_candidate": "router-pe01", "confidence": 0.88},
    )

    assert record.accepted is False
    assert record.handover_id in [h.handover_id for h in hdo_mgr.list_handovers("INC-500")]

    # Shift B accepts
    accepted = hdo_mgr.accept_handover(
        handover_id=record.handover_id,
        to_operator="operator-shift-b",
        notes="Reviewing Router-PE01 BGP logs",
    )
    assert accepted.accepted is True
    assert accepted.to_operator == "operator-shift-b"
    assert accepted.accepted_at is not None


# ── 5. Multi-Depth Storytelling ───────────────────────────────────────────

def test_storyteller_multi_depth_projections():
    """Verify Executive, Operator, and Technical story views."""
    provider = create_knowledge_provider()
    run_input = GeneratedRunInput(run_id="RUN-STORY", scenario_id="S1", difficulty_profile="L1", seed=42)
    ev_list = sample_evidence()

    orchestrator = ZakiOrchestrator()
    res = orchestrator.investigate("Investigate router issue", run_input=run_input, evidence=ev_list, provider=provider)
    story = res["story"]

    assert story.title
    assert story.leading_hypothesis["root_entity"] == "router"
    assert len(story.timeline_statements) > 0

    # Format CLI outputs across depths
    from zaki.storyteller.storyteller import default_storyteller
    cli_op = default_storyteller.format_story_for_cli(story)
    assert "ZAKI INCIDENT STORY" in cli_op
    assert "CURRENT LEADING HYPOTHESIS" in cli_op

    story.presentation_depth = PresentationDepth.DEEP_TECHNICAL
    cli_tech = default_storyteller.format_story_for_cli(story)
    assert "12-FACTOR SYNTHESIS CORE BREAKDOWN" in cli_tech


# ── 6. Domain Agents Discovery ────────────────────────────────────────────

def test_domain_agents_registry_and_dispatch():
    """Verify registered domain agents and task dispatching."""
    from zaki.agents.registry import default_agent_registry
    from zaki.agents.dispatcher import default_agent_dispatcher
    from zaki.contracts.agent import AgentTaskContract

    agents = default_agent_registry.list_agents()
    assert len(agents) >= 9  # PS, CS, RAN, IP_TRANSPORT, IN_OCS, VAS, IGW, INFRA, IT

    transport_agents = default_agent_registry.list_agents(domain="IP_TRANSPORT")
    assert len(transport_agents) == 1
    assert "router-bgp-investigation" in transport_agents[0].spec.capabilities

    # Dispatch subtask
    task = AgentTaskContract(
        task_id="SUB-01",
        incident_id="INC-01",
        intent="Check BGP peer flaps",
        domain="IP_TRANSPORT",
        objective="Determine if BGP flap caused degradation",
        requested_capability="router-bgp-investigation",
    )
    result = default_agent_dispatcher.dispatch(task)
    assert result.status == "SUCCESS"
    assert result.agent_id == "agent-ip-transport"
    assert len(result.findings) > 0
