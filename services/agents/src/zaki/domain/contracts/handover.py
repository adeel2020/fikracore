"""Shift Handover Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import AuthorityLevel


class HandoverRecordContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "ShiftHandover"
    handover_id: str = Field(default_factory=lambda: f"HDO-{int(datetime.now(timezone.utc).timestamp())}")
    incident_id: str
    task_id: Optional[str] = None
    from_operator: str
    to_operator: Optional[str] = None
    from_agent: str = "zaki_orchestrator"
    to_agent: str = "zaki_orchestrator"
    what: str
    why: str
    state: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    pending_actions: List[Dict[str, Any]] = Field(default_factory=list)
    pending_validations: List[Dict[str, Any]] = Field(default_factory=list)
    sla: Dict[str, Any] = Field(default_factory=dict)
    authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE
    accepted: bool = False
    acceptance_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
