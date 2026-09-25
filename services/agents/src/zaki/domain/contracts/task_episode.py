"""Task Episode Contract for Zaki v1 Learning."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract
from .intent import FCAPSClassification


class TaskEpisodeContract(BaseContract):
    api_version: str = "zaki.ai/v1"
    kind: str = "TaskEpisode"
    episode_id: str = Field(default_factory=lambda: f"EP-{int(datetime.now(timezone.utc).timestamp())}")
    task_id: str
    incident_id: str
    operator_intent: str
    fcaps: FCAPSClassification = Field(default_factory=FCAPSClassification)
    domains: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    evidence_requested: List[str] = Field(default_factory=list)
    evidence_observed: List[str] = Field(default_factory=list)
    ranked_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    selected_workflow: Optional[str] = None
    agent_recommendation: Optional[str] = None
    human_actions: List[Dict[str, Any]] = Field(default_factory=list)
    human_corrections: List[Dict[str, Any]] = Field(default_factory=list)
    outcome: str = "SUCCESS"
    learned_pattern: Optional[Dict[str, Any]] = None
    provenance: str = "task_episode_recorder"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
