"""
Human-In-The-Loop (HITL) Validation Contracts
=============================================
This module defines the HumanValidationContract for human SME review and digital approval
routed through Zaki's hub-and-spoke operational inbox.

Key Architectural Guarantees:
- Located under `zaki/governance/validation.py` enforcing governance boundaries.
- Domain Scoping: Every work order is explicitly attributed to a technical domain
  (e.g., IP_TRANSPORT, PS_CORE) so that requests are routed to the qualified engineering SME.
- Provenance & Originating Agent: Identifies the proposing specialist agent and rationale.
- Authority & Audit: Captures validator credentials, decision type, modifications, and timestamps.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import Field

from ..contracts.base import BaseContract
from ..enums import AuthorityLevel, ValidationDecisionType


class ValidationMetadata(BaseContract):
    """
    Metadata header identifying a human validation request.

    Attributes:
        id: Unique semantic validation request ID.
        task_id: Associated operational task reference ID.
        incident_id: Associated incident identifier.
        domain: Governing operational domain (e.g. 'IP_TRANSPORT').
        originating_agent_id: Identifier of the specialist agent proposing the action/knowledge.
    """
    id: str = Field(
        default_factory=lambda: f"VAL-{int(datetime.now(timezone.utc).timestamp())}",
        description="Unique validation work order identifier"
    )
    task_id: str = Field(description="Associated operational task identifier")
    incident_id: str = Field(description="Associated incident identifier")
    domain: str = Field(
        default="IP_TRANSPORT",
        description="Telecom operational domain governing this approval"
    )
    originating_agent_id: Optional[str] = Field(
        default=None,
        description="Identifier of the proposing specialist agent"
    )


class ValidationSpec(BaseContract):
    """
    Detailed specification of a human validation review and approval decision.

    Attributes:
        decision: Decision rendered (VALIDATE, REJECT, MODIFY, NEED_MORE_EVIDENCE).
        target_type: Object class under review (hypothesis, candidate_relationship, action, knowledge_promotion).
        target_id: Identifier of the evaluated candidate object.
        reason: Explanatory rationale authored by the human engineer.
        validator_role: Engineering title or persona (e.g. 'Transport Domain SME').
        validator_id: Specific human engineer username or employee ID.
        authority: Operational authority tier of the validator.
        timestamp: Timestamp when validation was signed.
        provenance: Interface through which decision was submitted (e.g. 'hitl_portal', 'slack_bot').
        modifications: Explicit parameter or topological adjustments if decision was MODIFY.
    """
    decision: ValidationDecisionType = Field(description="Review determination rendered by SME")
    target_type: str = Field(
        description="Target category: hypothesis, candidate_relationship, action, knowledge_promotion"
    )
    target_id: str = Field(description="Identifier of candidate element under evaluation")
    reason: str = Field(description="SME technical justification and operational notes")
    validator_role: str = Field(
        default="Transport Domain SME",
        description="Engineering persona or stakeholder role"
    )
    validator_id: str = Field(
        default="operator-01",
        description="Unique employee or engineer credential identifier"
    )
    authority: AuthorityLevel = Field(
        default=AuthorityLevel.LEVEL_4_HITL_EXECUTE,
        description="Approval authority ceiling of the signing engineer"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when decision was formally signed"
    )
    provenance: str = Field(
        default="hitl_portal",
        description="Operational portal through which decision was recorded"
    )
    modifications: Dict[str, Any] = Field(
        default_factory=dict,
        description="Payload overrides applied by engineer if decision was MODIFY"
    )


class HumanValidationContract(BaseContract):
    """
    Authoritative Human-In-The-Loop validation contract record.

    Attributes:
        api_version: Schema version identifier ('zaki.ai/v1').
        kind: Contract kind ('HumanValidation').
        metadata: Request context metadata and domain routing attributes.
        spec: Detailed approval or rejection specification.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="HumanValidation", description="Contract kind identifier")
    metadata: ValidationMetadata = Field(description="Validation routing metadata")
    spec: ValidationSpec = Field(description="Validation decision specification")
