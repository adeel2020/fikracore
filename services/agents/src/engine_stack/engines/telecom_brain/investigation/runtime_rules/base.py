"""
Declarative Runtime Rules Model: Base Contracts & Schemas
==========================================================
Defines the first-class runtime rule contracts and evaluation output schemas
conforming to Sections 17, 18, and 23 of the FikraCore Specification:
docs/Reasoning_Contracts/FikraCore_Sanity_Checks_and_Runtime_Rules.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from zaki.contracts.base import BaseContract


class RuleDecision(str, Enum):
    """Deterministic evaluation outcome for a runtime rule."""
    PASS = "PASS"    # Condition satisfied; proceed with action / progression
    WARN = "WARN"    # Condition incomplete; proceed with explicit uncertainty
    BLOCK = "BLOCK"  # Safety, causal, or authority invariant violated; halt action


class RuntimeRuleContract(BaseContract):
    """
    First-class declarative runtime rule specification (§18).

    A runtime rule defines how to evaluate an operational condition dynamically;
    it does NOT contain scenario-specific hardcoded conclusions.
    """
    rule_id: str = Field(description="Unique semantic rule identifier (e.g. 'RULE-SAFETY-001')")
    rule_version: str = Field(default="1.0.0", description="Semantic rule version")
    rule_type: str = Field(description="Category: SAFETY, CAUSAL_VALIDATION, EMERGING_EVIDENCE, etc.")
    name: str = Field(description="Human-readable rule display name")
    description: str = Field(description="Operational rationale for why this rule exists")

    applies_to: List[str] = Field(
        default_factory=list,
        description="Contract kinds or entity types this rule evaluates (e.g. ['Hypothesis', 'Action'])"
    )
    trigger: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions triggering rule selection (e.g. {'lifecycle': ['CONFIRMED'], 'event_type': ['ALARM']})"
    )
    scope: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operational scope bounds: domains, services, entity_types"
    )

    preconditions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of prerequisite conditions required before checks run"
    )
    checks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evaluation checks and thresholds to execute"
    )
    inputs_required: List[str] = Field(
        default_factory=list,
        description="Required inputs: evidence, graph, operational_context, tool_result"
    )

    decision_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from check outcome (pass/warn/block) to operational determination"
    )
    actions_triggered: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="List of action hooks to fire on pass/warn/block"
    )

    priority: int = Field(default=100, description="Rule evaluation priority (lower = higher priority)")
    enabled: bool = Field(default=True, description="Whether rule is active in the registry")
    owner: str = Field(default="telecom_architecture", description="Domain authority owning this rule")
    provenance: str = Field(default="standard_operating_procedure", description="Originating MOP or policy source")


class RuleEvaluationResult(BaseContract):
    """
    Traceable runtime rule evaluation result (§23).

    Persisted in TaskEpisodeContract.runtime_evaluations to provide complete
    epistemic and safety auditability for every operational decision.
    """
    evaluation_id: str = Field(
        default_factory=lambda: f"EVAL-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique evaluation execution identifier"
    )
    rule_id: str = Field(description="Evaluated rule identifier")
    rule_version: str = Field(default="1.0.0", description="Version of the evaluated rule")
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when evaluation was executed"
    )

    subject_id: str = Field(description="Identifier of evaluated contract or entity (e.g. 'ACT-001', 'HYP-001')")
    subject_type: str = Field(description="Contract kind of evaluated subject")
    episode_id: Optional[str] = Field(default=None, description="Associated task episode identifier")

    decision: RuleDecision = Field(description="PASS, WARN, or BLOCK")
    reason: str = Field(description="Human-friendly explanation of why the rule passed, warned, or blocked")
    structured_reason_codes: List[str] = Field(
        default_factory=list,
        description="Machine-readable error/status reason codes"
    )

    checks_evaluated: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Granular evaluation results per check item"
    )
    actions_triggered: List[str] = Field(
        default_factory=list,
        description="Operational actions initiated as a result of this evaluation"
    )
    evaluator_version: str = Field(default="1.0.0", description="Engine evaluator version")
