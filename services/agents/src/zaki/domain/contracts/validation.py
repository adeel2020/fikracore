"""Human Validation Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AuthorityLevel, ValidationDecisionType


class ValidationMetadata(BaseContract):
    id: str = Field(default_factory=lambda: f"VAL-{int(datetime.now(timezone.utc).timestamp())}")
    task_id: str
    incident_id: str


class ValidationSpec(BaseContract):
    decision: ValidationDecisionType
    target_type: str  # hypothesis, candidate_relationship, action, knowledge_promotion
    target_id: str
    reason: str
    validator_role: str = "operator"
    validator_id: str = "operator-01"
    authority: AuthorityLevel = AuthorityLevel.LEVEL_4_HITL_EXECUTE
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: str = "hitl_portal"
    modifications: Dict[str, Any] = Field(default_factory=dict)


class HumanValidationContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "HumanValidation"
    metadata: ValidationMetadata
    spec: ValidationSpec
