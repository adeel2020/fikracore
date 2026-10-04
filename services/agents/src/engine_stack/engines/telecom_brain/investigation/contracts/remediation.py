"""
Remediation Playbook & Operational Procedure Contracts (Plane 4 - Enterprise Intelligence)
========================================================================================
This module defines the canonical operational procedures (MOPs - Method of Procedures)
for telecommunications infrastructure remediation.

Key Principles:
1. Operational Safety: Remediation procedures are strictly categorized by ActionSafetyTier.
2. Mandatory Preconditions: Actions cannot be initiated until all operational preconditions
   (e.g., redundant path is UP and capacity verified) evaluate to satisfied.
3. Guaranteed Rollback: Every playbook must provide an explicit, ordered sequence of
   RollbackStep definitions with execution timeouts.
4. Human-In-The-Loop (HITL): High-impact actions (ActionSafetyTier.DISRUPTIVE) strictly
   enforce `requires_hitl = True` before execution.
"""

from typing import Any
from pydantic import Field
from .base import Contract, ActionSafetyTier


class PlaybookPrecondition(Contract):
    """
    Mandatory operational prerequisite that must evaluate to True prior to executing a playbook.
    Examples: Verifying standby router is alive, link capacity >= 50%, or failover path operational.

    Attributes:
        precondition_id: Unique precondition identifier.
        condition_expression: Technical assertion to evaluate (e.g. 'standby_peer_bgp_state == ESTABLISHED').
        target_entity: Network node or link on which precondition is verified.
        verification_tool_ref: Tool identifier in DomainToolRegistry used to verify condition.
        is_satisfied: Dynamic status indicating whether precondition passed validation.
    """
    precondition_id: str = Field(description="Unique semantic precondition identifier")
    condition_expression: str = Field(description="Human and machine-readable logic expression for check")
    target_entity: str = Field(description="Target node or interface to check")
    verification_tool_ref: str = Field(description="Registered tool ID used to evaluate the precondition")
    is_satisfied: bool = Field(default=False, description="Verification result (must be True before proceeding)")


class RollbackStep(Contract):
    """
    Explicit automated or guided step to safely undo a remediation action if health checks fail.

    Attributes:
        step_number: 1-indexed execution sequence number.
        action_name: Operational command or script name (e.g. 'revert_bgp_cost', 'unshut_interface').
        target_entity: Network element receiving the rollback command.
        execution_tool_ref: Tool identifier in DomainToolRegistry executing the rollback.
        params: Key-value parameters passed to the rollback tool.
        timeout_seconds: Maximum permissible execution window before raising an emergency abort alert.
    """
    step_number: int = Field(description="Sequential execution order number")
    action_name: str = Field(description="Action name describing rollback operation")
    target_entity: str = Field(description="Canonical slug of the entity being restored")
    execution_tool_ref: str = Field(description="Tool reference ID authorized to execute rollback")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters required for rollback execution")
    timeout_seconds: int = Field(default=60, description="Timeout limit before aborting rollback execution")


class RemediationPlaybookContract(Contract):
    """
    Canonical specification of a telecommunications Method of Procedure (MOP).
    Stored under Plane 4 (Enterprise Intelligence) and registered in FikraCore's PlaybookRegistry.

    Attributes:
        playbook_id: Unique semantic playbook identifier (e.g., 'PLAYBOOK_DRAIN_AGG_BGP').
        name: Standard operational title of the MOP.
        domain: Primary operational domain (e.g., 'IP_TRANSPORT').
        target_procedure_type: Category of action: FAILOVER, DRAIN, RATE_LIMIT, RESTART, CONFIG_ROLLBACK.
        target_entity_types: Network element classes this playbook applies to (e.g., ['PE_ROUTER']).
        preconditions: List of prerequisites that must evaluate to True prior to initiation.
        execution_steps: Sequential list of execution tasks with tool references and parameters.
        rollback_steps: Sequential list of compensatory actions if post-validation fails.
        safety_tier: Action safety classification (READ_ONLY_DIAGNOSTIC, CONTROLLED_REVERSIBLE, DISRUPTIVE).
        requires_hitl: Whether human engineer confirmation is mandatory prior to execution.
        estimated_duration_seconds: Expected duration to complete execution and initial health check.
        description: Comprehensive technical explanation of the procedure and operational impacts.
    """
    playbook_id: str = Field(description="Unique semantic playbook identifier (e.g., 'PLAYBOOK_DRAIN_AGG_BGP')")
    name: str = Field(description="Human-readable title formatted for NOC SME interfaces")
    domain: str = Field(description="Governing technical domain (DomainCode or domain string)")
    target_procedure_type: str = Field(
        description="Standard telecom operation type: FAILOVER, DRAIN, RATE_LIMIT, RESTART, CONFIG_ROLLBACK"
    )
    target_entity_types: list[str] = Field(
        default_factory=list,
        description="Applicable network entity classes (e.g. ['PE_ROUTER', 'IP_FABRIC_SWITCH'])"
    )
    preconditions: list[PlaybookPrecondition] = Field(
        default_factory=list,
        description="Mandatory conditions that must be verified as satisfied prior to execution"
    )
    execution_steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered sequence of execution tasks, tools, and parameter schemas"
    )
    rollback_steps: list[RollbackStep] = Field(
        default_factory=list,
        description="Ordered sequence of rollback operations executed in reverse on abort"
    )
    safety_tier: ActionSafetyTier = Field(
        default=ActionSafetyTier.CONTROLLED_REVERSIBLE,
        description="Operational risk and reversibility tier"
    )
    requires_hitl: bool = Field(
        default=True,
        description="Enforces mandatory human SME validation and digital signature before execution"
    )
    estimated_duration_seconds: int = Field(
        default=120,
        description="Estimated execution and settling window in seconds"
    )
    description: str = Field(
        default="",
        description="Detailed technical description of operational procedure, risks, and post-checks"
    )
