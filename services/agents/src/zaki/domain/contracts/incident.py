"""Incident Context Contract for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from .hypothesis import RankedHypothesisItem
from ..enums import AuthorityLevel


class IncidentContextContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "IncidentContext"
    incident_id: str = Field(default_factory=lambda: f"INC-{int(datetime.now(timezone.utc).timestamp())}")
    title: str = "Telecom Operational Incident"
    status: str = "ACTIVE"
    current_run_id: Optional[str] = None
    scenario_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_stage: str = "INGESTION"
    terminal_state: Optional[str] = None

    # Operational state tracking
    active_evidence_window: Dict[str, Any] = Field(default_factory=dict)
    ranked_hypotheses: List[RankedHypothesisItem] = Field(default_factory=list)
    leading_hypothesis_id: Optional[str] = None
    evidence_requests: List[Dict[str, Any]] = Field(default_factory=list)
    domain_involvement: List[str] = Field(default_factory=list)
    pending_validations: List[Dict[str, Any]] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    current_authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE
    recovery_state: Dict[str, Any] = Field(default_factory=dict)
    learning_state: Dict[str, Any] = Field(default_factory=dict)
    provenance_references: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
