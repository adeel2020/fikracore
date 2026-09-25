"""Action & Remediation Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AuthorityLevel


class ActionContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "Action"
    action_id: str = Field(default_factory=lambda: f"ACT-{int(datetime.now(timezone.utc).timestamp())}")
    task_id: str
    incident_id: str
    title: str
    action_type: str  # remediation, reroute, restart, change_create, verify
    target_entity: str
    domain: str
    required_authority: AuthorityLevel = AuthorityLevel.LEVEL_4_HITL_EXECUTE
    status: str = "PROPOSED"  # PROPOSED, APPROVED, REJECTED, EXECUTED, VERIFIED, FAILED, ROLLED_BACK
    proposed_by: str = "zaki_orchestrator"
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    execution_timestamp: Optional[datetime] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rollback_plan: Dict[str, Any] = Field(default_factory=dict)
    risk_assessment: str = "LOW"
    result: Dict[str, Any] = Field(default_factory=dict)
    provenance: str = "orchestrator_action_gateway"
