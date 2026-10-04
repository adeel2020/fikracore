"""
Operational Context Contract (Section 22 Context Scaffolding Envelope)
======================================================================
This module defines the OperationalContextContract representing the live
operational context presented to Zaki and specialist agents.

Key Architectural Guarantees:
1. Truth-Blind Boundary: Supplies admitted telemetry, visible topology, and active
   incident state without exposing hidden simulator ground truth.
2. Multi-Domain Context Scaffolding: Encapsulates network health state, active shift
   jurisdiction, active maintenance windows, and speech completion barriers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class OperationalContextContract(BaseContract):
    """
    Live operational context scaffolding envelope passed to Zaki and specialist agents.

    Attributes:
        api_version: Schema version identifier ('zaki.ai/v1').
        kind: Contract kind ('OperationalContext').
        context_id: Unique semantic context snapshot ID.
        scenario_id: Active scenario identifier (if running under simulation).
        run_id: Execution run identifier.
        active_incident_id: Active incident under operational triage.
        primary_domain: Primary technical domain jurisdiction for current shift.
        active_domains: List of operational domains exhibiting degradation or alarms.
        visible_entities: Network entities authorized for agent observation.
        visible_topology_subgraph: Topology nodes and edges within active blast radius.
        admitted_evidence_ids: List of verified evidence records admitted to reasoning.
        active_knowledge_gaps: Topological or causal knowledge gaps currently open.
        active_maintenance_windows: Scheduled maintenance activities that could cause alarms.
        speech_pacing_active: True if simulation progression must hold for voice delivery.
        human_sme_role: Engineering role currently collaborating with Zaki (e.g. 'IP Transport SME').
        created_at: Snapshot creation timestamp.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="OperationalContext", description="Contract kind identifier")
    context_id: str = Field(
        default_factory=lambda: f"CTX-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique context snapshot identifier"
    )
    scenario_id: Optional[str] = Field(default=None, description="Active simulation scenario identifier")
    run_id: Optional[str] = Field(default=None, description="Simulation run execution identifier")
    active_incident_id: Optional[str] = Field(default=None, description="Active incident ID under investigation")
    primary_domain: str = Field(default="IP_TRANSPORT", description="Primary domain of focus")
    active_domains: List[str] = Field(default_factory=list, description="All operational domains exhibiting degradation")
    visible_entities: List[str] = Field(
        default_factory=list,
        description="Network node slugs within authorized observation boundary"
    )
    visible_topology_subgraph: Dict[str, Any] = Field(
        default_factory=dict,
        description="Authorized topology nodes and edges"
    )
    admitted_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Telemetry observation IDs admitted for cognitive inference"
    )
    active_knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Knowledge gap IDs currently bounding reasoning"
    )
    active_maintenance_windows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Scheduled maintenance events active in the incident window"
    )
    speech_pacing_active: bool = Field(
        default=True,
        description="Enforces stage advancement holds until speech completion barrier clears"
    )
    human_sme_role: str = Field(
        default="Transport Domain SME",
        description="Role of human engineer currently supervising Zaki"
    )
    operational_mode: str = Field(
        default="SIMULATION",
        description="Execution mode: PRODUCTION, LIVE_INTENT, SIMULATION, CANARY"
    )
    active_incident_ids: List[str] = Field(
        default_factory=list,
        description="List of all concurrent incidents visible in current operational scope"
    )
    active_delegations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Active and recently completed task delegations to specialist agents"
    )
    pending_approvals: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Actions, probes, or promotions currently awaiting human SME sign-off"
    )
    impact_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="High-level customer, service, slice, and throughput blast radius"
    )
    resilience_profiles: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Structural resilience design profiles (redundancy models, self-healing mechanisms) for entities in scope"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when context envelope was captured"
    )


# ---------------------------------------------------------------------------
# Shared runtime resolution — ONE OperationalContext per Zaki response
# ---------------------------------------------------------------------------
# Every analytical lens (Storyteller, Blast Radius, Causal Propagation,
# Remediation Strategy, ...) consumes the SAME context built here. It is
# derived ONLY from the authoritative run snapshot — never from presentation
# fallbacks — so an absent run yields an empty context instead of SCN-001
# defaults.

CONTEXT_NO_INCIDENT = "NO_INCIDENT"
CONTEXT_AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
CONTEXT_READY = "READY"


def build_operational_context(ui_context: Dict[str, Any]) -> OperationalContextContract:
    """Build the single OperationalContextContract for the current Zaki turn.

    Anchored to the run_id supplied by the client. A scenario state that the API
    loaded as a presentation fallback (no run selected) is NOT operational context.
    """
    run_id = ui_context.get("run_id")
    sim_state = (ui_context.get("simulation_state") or {}) if run_id else {}
    scenario_id = sim_state.get("scenario_id") if sim_state else None

    topo = sim_state.get("topology") or {}
    domains = [d.get("name") for d in topo.get("domains", []) if isinstance(d, dict) and d.get("name")]
    entities = [
        e.get("id") or e.get("display_name")
        for d in topo.get("domains", []) if isinstance(d, dict)
        for e in d.get("entities", []) if isinstance(e, dict) and (e.get("id") or e.get("display_name"))
    ]
    evidence_ids = [
        str(ev.get("id") or ev.get("event_id"))
        for ev in (sim_state.get("events") or [])
        if isinstance(ev, dict) and (ev.get("id") or ev.get("event_id"))
    ]
    gaps = [
        str(g.get("id"))
        for g in (sim_state.get("knowledge_gaps") or [])
        if isinstance(g, dict) and g.get("id")
    ]

    fields: Dict[str, Any] = {
        "scenario_id": scenario_id,
        "run_id": run_id,
        "active_incident_id": scenario_id,
        "active_domains": domains,
        "visible_entities": entities,
        "visible_topology_subgraph": {"causal_path": topo.get("causal_path") or []} if topo else {},
        "admitted_evidence_ids": evidence_ids,
        "active_knowledge_gaps": gaps,
        "operational_mode": str(sim_state.get("source_mode") or ui_context.get("source_mode") or "SIMULATION"),
        "active_incident_ids": [scenario_id] if scenario_id else [],
        "impact_summary": sim_state.get("impact") or {},
    }
    if domains:
        fields["primary_domain"] = domains[0]
    if run_id:
        fields["context_id"] = f"CTX-{run_id}"
    return OperationalContextContract(**fields)


def operational_context_readiness(ctx: OperationalContextContract, ui_context: Dict[str, Any]) -> str:
    """Classify whether the shared context can support an operational narrative."""
    sim_state = ui_context.get("simulation_state") or {}
    if not ctx.run_id or not sim_state:
        return CONTEXT_NO_INCIDENT
    has_ranked_hyp = any(
        isinstance(h, dict) and h.get("confidence") is not None
        for h in (sim_state.get("hypotheses") or [])
    )
    if not ctx.admitted_evidence_ids and not sim_state.get("events") and not has_ranked_hyp:
        return CONTEXT_AWAITING_EVIDENCE
    return CONTEXT_READY


def resolve_operational_context(ui_context: Dict[str, Any]) -> tuple[OperationalContextContract, str]:
    """Return (context, readiness), building once and caching on ui_context."""
    ctx = ui_context.get("operational_context")
    if not isinstance(ctx, OperationalContextContract):
        ctx = build_operational_context(ui_context)
        ui_context["operational_context"] = ctx
    readiness = ui_context.get("operational_context_readiness") or operational_context_readiness(ctx, ui_context)
    ui_context["operational_context_readiness"] = readiness
    return ctx, readiness
