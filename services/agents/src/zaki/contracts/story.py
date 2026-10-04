"""Incident Story Contract for Zaki v1 Storyteller."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from ..enums import PresentationDepth, StatementProvenance


class StoryStatement(BaseContract):
    statement_id: str
    text: str
    provenance: StatementProvenance = StatementProvenance.OBSERVED
    source_entity: Optional[str] = None
    domain: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    stage: str = "INVESTIGATION"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentStoryContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "IncidentStory"
    incident_id: str
    run_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    presentation_depth: PresentationDepth = PresentationDepth.OPERATOR

    title: str = ""
    summary: str = ""
    service_impact: Dict[str, Any] = Field(default_factory=dict)
    leading_hypothesis: Dict[str, Any] = Field(default_factory=dict)
    competing_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    correlation_narrative: Dict[str, Any] = Field(default_factory=dict)
    timeline_statements: List[StoryStatement] = Field(default_factory=list)
    next_best_action: Optional[str] = None
    outcome: Optional[str] = None
    technical_details: Dict[str, Any] = Field(default_factory=dict)
