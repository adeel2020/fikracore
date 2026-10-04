"""
Task Episode Contract: Dynamic Operational Spine (Plane 3 - Reasoning Spine)
=============================================================================
This module defines the central operational spine connecting all contracts across
an investigation lifecycle in Zaki and FikraCore.

Architectural Role:
- Located at `zaki/contracts/task_episode.py` as Zaki's core operational cognitive ledger.
- Binds Operator Intent, Operational Context, Behavioral Guardrails, Competing Hypotheses,
  Discrimination Probes, Human Validation, and Knowledge Promotion into a single graph node.
- Stored under Plane 3 (EPISODES index) in gbrain for longitudinal tracking and audit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract

try:
    from ..contracts.intent import FCAPSClassification
except ImportError:
    class FCAPSClassification(BaseContract):  # type: ignore[no-redef]
        primary: str = "FAULT"
        secondary: List[str] = Field(default_factory=list)
        domain: str = "PS"
        confidence: float = 0.9
        clarification_required: bool = False


class StageOutcome(BaseContract):
    """Execution outcome for a specific simulation or diagnostic investigation stage."""
    stage_number: int = Field(description="Stage index (e.g. 1 to 6)")
    stage_name: str = Field(description="Stage name (e.g. OBSERVATION, HYPOTHESIS, PROBING, CONVERGENCE, SIMULATION, REMEDIATION)")
    status: str = Field(default="COMPLETED", description="COMPLETED, IN_PROGRESS, FAILED, SKIPPED")
    summary: str = Field(default="", description="Operator summary of stage findings")
    capability_ref: Optional[str] = Field(default=None, description="Reference to output contract produced in this stage")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskEpisodeContract(BaseContract):
    """
    Authoritative cognitive spine linking every diagnostic decision, probe, and validation.

    Attributes:
        api_version: Schema version identifier ('zaki.ai/v1').
        kind: Contract type name ('TaskEpisode').
        episode_id: Unique semantic episode identifier (e.g., 'EP-1727732400').
        task_id: Associated operational task reference ID.
        incident_id: Associated active or historic incident ID.
        operator_intent: Normalized intent string guiding the agent's focus.
        fcaps: FCAPS classification (Fault, Configuration, Accounting, Performance, Security).
        domains: Telecom operational domains traversed during the episode.
        context: Execution environment context dictionary.
        operational_context_ref: Reference to the active OperationalContextContract snapshot.
        behavior_contract_ref: Reference to the governing BehaviorContract enforcing safety guardrails.
        evidence_requested: Telemetry queries and sensor reads dispatched.
        evidence_observed: Telemetry observations ingested during reasoning.
        ranked_hypotheses: Ordered list of competing causal hypotheses evaluated.
        discrimination_probes: Active discrimination probes dispatched in Step 3.
        selected_workflow: Orchestration workflow executed by Zaki.
        playbook_ref: Remediation playbook ID selected to mitigate the condition.
        agent_recommendation: Prescriptive recommendation formulated by autonomous agent.
        human_validations: Domain SME validation decisions and signatures.
        human_actions: Interventions performed manually by human engineers.
        human_corrections: Adjustments made by human SME overriding agent proposals.
        outcome: Resolution terminal state (SUCCESS, PARTIAL, FAILED, ESCALATED).
        learned_pattern: Extracted operational pattern staged for knowledge promotion.
        provenance: Provenance audit string identifying originating service/agent.
        created_at: Timestamp when episode was initiated.
        closed_at: Timestamp when episode was formally resolved or closed.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="TaskEpisode", description="Contract kind identifier")
    episode_id: str = Field(
        default_factory=lambda: f"EP-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique semantic episode identifier"
    )
    task_id: str = Field(description="Operational task identifier")
    incident_id: str = Field(description="Incident identifier governed by this episode")
    operator_intent: str = Field(description="Human operator intent or high-level mission statement")
    fcaps: FCAPSClassification = Field(default_factory=FCAPSClassification, description="FCAPS operational category")
    domains: List[str] = Field(default_factory=list, description="Telecom technical domains in scope")
    context: Dict[str, Any] = Field(default_factory=dict, description="Operational execution parameters")
    operational_context_ref: Optional[str] = Field(
        default=None,
        description="Reference to active OperationalContextContract snapshot"
    )
    behavior_contract_ref: Optional[str] = Field(
        default=None,
        description="Reference to governing BehaviorContract enforcing safety guardrails"
    )
    evidence_requested: List[str] = Field(
        default_factory=list,
        description="List of telemetry queries requested during reasoning"
    )
    evidence_observed: List[str] = Field(
        default_factory=list,
        description="List of admitted evidence records evaluated"
    )
    ranked_hypotheses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competing causal explanations ranked by confidence score"
    )
    discrimination_probes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Active discrimination probes dispatched in Step 3"
    )
    selected_workflow: Optional[str] = Field(
        default=None,
        description="Active orchestration workflow identifier"
    )
    playbook_ref: Optional[str] = Field(
        default=None,
        description="RemediationPlaybookContract ID selected for mitigation"
    )
    agent_recommendation: Optional[str] = Field(
        default=None,
        description="Prescriptive action formulated by autonomous specialist"
    )
    human_validations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Human SME validation records and digital signatures"
    )
    human_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Manual operational actions taken during the episode"
    )
    human_corrections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="SME feedback and manual hypothesis corrections"
    )
    outcome: str = Field(
        default="SUCCESS",
        description="Episode resolution status: SUCCESS, PARTIAL, FAILED, ESCALATED"
    )
    learned_pattern: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Operational pattern signature extracted for continuous learning promotion"
    )
    promotion_records: List[str] = Field(
        default_factory=list,
        description="Foreign key references to promoted knowledge ledger records"
    )
    finding_refs: List[str] = Field(
        default_factory=list,
        description="Foreign key references to validated findings generated during the episode"
    )
    delegated_task_refs: List[str] = Field(
        default_factory=list,
        description="References to delegated sub-tasks assigned to specialist spoke agents"
    )
    runtime_evaluations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Audit log of runtime rule evaluations (PASS/WARN/BLOCK) executed during the episode"
    )

    # Simulation & Diagnostic Stagewise Execution
    stagewise_outcomes: List[StageOutcome] = Field(
        default_factory=list,
        description="Ordered outcomes for each simulation or diagnostic investigation stage"
    )

    # Capability Outputs (Agnostic to incident or event type)
    root_cause_analysis: Optional[Any] = Field(
        default=None,
        description="Authoritative RootCauseAnalysisContract produced during episode"
    )
    causal_propagation: Optional[Any] = Field(
        default=None,
        description="Authoritative CausalPropagationContract produced during episode"
    )
    what_if_analysis: Optional[Any] = Field(
        default=None,
        description="Authoritative WhatIfSimulationContract evaluating candidate actions"
    )
    remediation_strategy: Optional[Any] = Field(
        default=None,
        description="Authoritative RemediationStrategyContract formulated for resolution"
    )
    provenance: str = Field(
        default="task_episode_recorder",
        description="Subsystem or agent authoring this cognitive record"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when episode was instantiated"
    )
    closed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when episode reached terminal resolution"
    )
