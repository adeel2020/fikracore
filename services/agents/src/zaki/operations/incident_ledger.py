"""Durable Incident Ledger for Zaki v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from ..domain.contracts.incident import IncidentContextContract
from ..domain.contracts.hypothesis import RankedHypothesisItem
from ..domain.enums import AuthorityLevel


class IncidentLedger:
    """Maintains incident context across tasks, shifts, and reasoning updates."""

    def __init__(self) -> None:
        self._incidents: Dict[str, IncidentContextContract] = {}

    def create_incident(
        self,
        title: str = "Telecom Operational Incident",
        scenario_id: Optional[str] = None,
        current_run_id: Optional[str] = None,
        authority: AuthorityLevel = AuthorityLevel.LEVEL_1_ANALYZE,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IncidentContextContract:
        incident = IncidentContextContract(
            title=title,
            scenario_id=scenario_id,
            current_run_id=current_run_id,
            current_authority=authority,
            metadata=metadata or {},
        )
        self._incidents[incident.incident_id] = incident
        return incident

    def get_incident(self, incident_id: str) -> Optional[IncidentContextContract]:
        return self._incidents.get(incident_id)

    def update_incident_state(
        self,
        incident_id: str,
        current_stage: Optional[str] = None,
        terminal_state: Optional[str] = None,
        ranked_hypotheses: Optional[List[RankedHypothesisItem]] = None,
        leading_hypothesis_id: Optional[str] = None,
        domain_involvement: Optional[List[str]] = None,
        pending_validations: Optional[List[Dict[str, Any]]] = None,
        evidence_requests: Optional[List[Dict[str, Any]]] = None,
        recovery_state: Optional[Dict[str, Any]] = None,
        learning_state: Optional[Dict[str, Any]] = None,
    ) -> Optional[IncidentContextContract]:
        inc = self._incidents.get(incident_id)
        if not inc:
            return None
        if current_stage:
            inc.current_stage = current_stage
        if terminal_state:
            inc.terminal_state = terminal_state
        if ranked_hypotheses is not None:
            inc.ranked_hypotheses = ranked_hypotheses
        if leading_hypothesis_id is not None:
            inc.leading_hypothesis_id = leading_hypothesis_id
        if domain_involvement is not None:
            inc.domain_involvement = domain_involvement
        if pending_validations is not None:
            inc.pending_validations = pending_validations
        if evidence_requests is not None:
            inc.evidence_requests = evidence_requests
        if recovery_state is not None:
            inc.recovery_state = recovery_state
        if learning_state is not None:
            inc.learning_state = learning_state
        inc.updated_at = datetime.now(timezone.utc)
        return inc

    def attach_task(self, incident_id: str, task_id: str) -> bool:
        inc = self._incidents.get(incident_id)
        if not inc:
            return False
        if task_id not in inc.task_ids:
            inc.task_ids.append(task_id)
            inc.updated_at = datetime.now(timezone.utc)
        return True

    def list_incidents(self) -> List[IncidentContextContract]:
        return list(self._incidents.values())


default_incident_ledger = IncidentLedger()
