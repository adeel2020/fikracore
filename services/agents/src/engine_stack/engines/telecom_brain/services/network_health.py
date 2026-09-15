"""Network health summary service."""

from __future__ import annotations

from correlation.registry import IncidentRegistry

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, IncidentRef, TelecomRequest, TelecomResult, TelecomTrace


class NetworkHealthService:
    id = "network_health"

    def __init__(self, registry: IncidentRegistry | None = None) -> None:
        self.registry = registry or IncidentRegistry()

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("network health", "brief me", "health summary", "operations brief")):
            score += 0.65
        if any(term in query for term in ("active incidents", "degraded kpis", "alarm pressure", "risky service")):
            score += 0.25
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        incidents = self.registry.list(limit=20)
        active = [row for row in incidents if row.get("status") in {"open", "candidate", "acknowledged", "reopened"}]
        degraded = [kpi for kpi in request.kpis if kpi.breached]
        domains = {}
        for alarm in request.alarms:
            domain = str(alarm.labels.get("domain") or "unknown")
            domains[domain] = domains.get(domain, 0) + 1
        text = self._format(active, degraded, domains)
        return TelecomResult(
            text=text,
            spoken_response=f"Network health brief: {len(active)} active incidents, {len(degraded)} degraded KPIs, {len(domains)} domains with alarm pressure.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["correlation.IncidentRegistry", "telecom_brain.request_context"]),
            incidents=[self._incident_ref(row) for row in active],
            kpi_evidence=degraded,
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"active_incidents": active, "degraded_kpis": [kpi.model_dump() for kpi in degraded], "alarm_pressure": domains},
        )

    @staticmethod
    def _format(active: list[dict], degraded: list, domains: dict[str, int]) -> str:
        lines = ["**Network Health Brief**"]
        lines.append(f"- Active incidents: {len(active)}")
        lines.append(f"- Degraded KPIs: {len(degraded)}")
        if domains:
            pressure = ", ".join(f"{domain}: {count}" for domain, count in sorted(domains.items(), key=lambda item: item[1], reverse=True))
            lines.append(f"- Alarm pressure: {pressure}")
        else:
            lines.append("- Alarm pressure: no alarm context provided")
        return "\n".join(lines)

    @staticmethod
    def _incident_ref(row: dict) -> IncidentRef:
        return IncidentRef(
            id=row.get("incident_id", "unknown"),
            status=row.get("status"),
            severity=str(row.get("score")) if row.get("score") is not None else None,
            source="correlation.registry",
            metadata={"scope": row.get("scope"), "domains": row.get("domains", []), "services": row.get("services", [])},
        )
