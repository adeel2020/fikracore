"""Incident registry service wrapper over the existing correlation registry."""

from __future__ import annotations

from typing import Any

from correlation.registry import IncidentRegistry
from storyteller.conversation.service import extract_incident_ref

from ..engine_context import TelecomContext
from ..models import AlarmEvidence, FCAPSClassification, IncidentRef, TelecomRequest, TelecomResult, TelecomTrace


class IncidentRegistryService:
    id = "incident_registry"

    def __init__(self, registry: IncidentRegistry | None = None) -> None:
        self.registry = registry or IncidentRegistry()

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        has_incident = "incident" in query or "incidents" in query
        is_list_query = any(term in query for term in ("list", "queue", "all", "current", "status", "registry", "open", "active", "recent", "overview"))

        # Explicit request to list or browse incidents
        if is_list_query and has_incident:
            return 0.95

        if has_incident:
            score += 0.35
        if is_list_query:
            score += 0.35
        if any(term in query for term in ("create", "candidate", "update", "acknowledge", "assign", "resolve")):
            score += 0.2
        if extract_incident_ref(request.query):
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        query = request.query.lower()
        if any(term in query for term in ("list", "show", "current", "active", "open", "all")):
            return await self._list(request)

        incident_id = extract_incident_ref(request.query)
        if incident_id:
            return await self._get(incident_id)

        if "candidate" in query or request.alarms:
            return await self._candidate(request)

        return TelecomResult(
            text="Please provide an incident ID or ask to list current incidents.",
            spoken_response="Please provide an incident ID or ask me to list current incidents.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, warnings=["incident registry request lacked a target"]),
            alarm_evidence=self._retained_alarms(request),
        )

    async def _list(self, request: TelecomRequest) -> TelecomResult:
        rows = self.registry.list(limit=50)
        incidents = [self._to_ref(row) for row in rows]
        if not rows:
            text = "No incidents are currently recorded in the local incident registry."
            spoken = "There are no incidents currently recorded in the local incident registry."
        else:
            lines = ["**Current Incidents Under Management**"]
            for row in rows:
                lines.append(f"- {row.get('incident_id')} | {row.get('status')} | {row.get('scope')} | score={row.get('score')}")
            text = "\n".join(lines)
            spoken = f"I found {len(rows)} incidents currently recorded in the registry. Details are shown on your screen."
        return TelecomResult(
            text=text,
            spoken_response=spoken,
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["correlation.IncidentRegistry"]),
            incidents=incidents,
            fcaps=[FCAPSClassification.FAULT],
            data={"incidents": rows},
        )

    async def _get(self, incident_id: str) -> TelecomResult:
        try:
            row = self.registry.get(incident_id)
        except KeyError:
            message = f"Incident '{incident_id}' was not found in the local incident registry."
            return TelecomResult(
                text=message,
                spoken_response=message,
                service_id=self.id,
                trace=TelecomTrace(selected_service=self.id, warnings=[message]),
            )

        text = f"Incident {row.get('incident_id')} is {row.get('status')} with scope {row.get('scope')} and score {row.get('score')}."
        return TelecomResult(
            text=text,
            spoken_response=text,
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["correlation.IncidentRegistry"]),
            incidents=[self._to_ref(row)],
            fcaps=[FCAPSClassification.FAULT],
            data={"incident": row},
        )

    async def _candidate(self, request: TelecomRequest) -> TelecomResult:
        alarms = self._retained_alarms(request)
        message = "Retained incident candidate for review."
        return TelecomResult(
            text=message,
            spoken_response=message,
            service_id=self.id,
            trace=TelecomTrace(
                selected_service=self.id,
                provenance=["correlation.IncidentRegistry"],
                warnings=["Candidate persistence awaits correlation output; unmatched alarms were retained."],
            ),
            alarm_evidence=alarms,
            fcaps=[FCAPSClassification.FAULT],
            data={"candidate": True, "retained_alarm_count": len(alarms)},
        )

    @staticmethod
    def _retained_alarms(request: TelecomRequest) -> list[AlarmEvidence]:
        return [
            alarm.model_copy(update={"retained_reason": alarm.retained_reason or "not filtered by intent"})
            for alarm in request.alarms
        ]

    @staticmethod
    def _to_ref(row: dict[str, Any]) -> IncidentRef:
        return IncidentRef(
            id=row.get("incident_id", "unknown"),
            status=row.get("status"),
            severity=str(row.get("score")) if row.get("score") is not None else None,
            source="correlation.registry",
            metadata={
                "tenant_id": row.get("tenant_id"),
                "scope": row.get("scope"),
                "domains": row.get("domains", []),
                "services": row.get("services", []),
                "owner": row.get("owner"),
            },
        )
