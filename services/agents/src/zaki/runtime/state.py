"""Authoritative State Manager for Zaki v1."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..domain.contracts.base import BaseContract


class AuthoritativeRunState(BaseContract):
    run_id: str
    scenario_id: Optional[str] = None
    task_id: Optional[str] = None
    incident_id: Optional[str] = None
    revision: int = 1
    sequence: int = 0
    current_stage: str = "INGESTION"
    terminal_state: Optional[str] = None
    ranked_hypotheses: list = []
    correlation_data: Dict[str, Any] = {}
    knowledge_gaps: Dict[str, Any] = {}
    impact: list = []
    diagnostics: Dict[str, Any] = {}

    def bump_revision(self, stage: Optional[str] = None) -> None:
        self.revision += 1
        self.sequence += 1
        if stage:
            self.current_stage = stage
