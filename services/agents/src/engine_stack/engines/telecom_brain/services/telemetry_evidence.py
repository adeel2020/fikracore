"""Telemetry evidence service with MCP Hub first access to Grafana."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, KpiEvidence, TelecomRequest, TelecomResult, TelecomTrace


class TelemetryEvidenceService:
    id = "telemetry_evidence"

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("grafana", "lgtm", "metric", "metrics", "logs", "traces", "dashboard")):
            score += 0.5
        if any(term in query for term in ("kpi", "telemetry", "evidence", "alert", "alerts", "panel")):
            score += 0.3
        if request.kpis:
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        tool_name, arguments = self._select_tool(request)
        result = await context.mcp_hub.call_tool("grafana", tool_name, arguments)
        kpis = self._kpis_from_result(result, request)
        projection = self._semantic_projection(tool_name, arguments, result, kpis)
        await self._project_to_gbrain(context, projection)
        text = self._format(tool_name, kpis, result)
        return TelecomResult(
            text=text,
            spoken_response=f"Retrieved Grafana telemetry evidence through MCP Hub using {tool_name}.",
            service_id=self.id,
            trace=TelecomTrace(
                selected_service=self.id,
                provenance=["mcp_hub.grafana", "mcp_hub.gbrain"],
            ),
            kpi_evidence=kpis,
            fcaps=[FCAPSClassification.PERFORMANCE, FCAPSClassification.FAULT],
            data={"tool": tool_name, "arguments": arguments, "result": result, "gbrain_projection": projection},
        )

    @staticmethod
    def _select_tool(request: TelecomRequest) -> tuple[str, dict[str, Any]]:
        query = request.query.lower()
        service = request.context.get("service_id") or request.context.get("service") or "unknown"
        window = request.context.get("window") or request.context.get("time_window") or "15m"
        if "dashboard" in query or "panel" in query:
            return "get_service_dashboard_evidence", {"service_id": service, "window": window}
        if "component" in query or "health" in query:
            component = request.context.get("component_id") or request.context.get("component") or service
            return "get_component_health", {"component_id": component, "window": window}
        if "alarm" in query or "alert" in query:
            return "query_alarm_window", {"service_id": service, "window": window}
        return "query_kpi_window", {"service_id": service, "window": window}

    @staticmethod
    def _kpis_from_result(result: Any, request: TelecomRequest) -> list[KpiEvidence]:
        if request.kpis:
            return request.kpis
        rows = []
        if isinstance(result, dict):
            raw_rows = result.get("kpis") or result.get("metrics") or result.get("series") or []
            if isinstance(raw_rows, dict):
                raw_rows = [raw_rows]
            for idx, row in enumerate(raw_rows):
                if isinstance(row, dict):
                    rows.append(
                        KpiEvidence(
                            name=str(row.get("name") or row.get("metric") or f"kpi-{idx}"),
                            value=row.get("value"),
                            unit=row.get("unit"),
                            threshold=row.get("threshold"),
                            breached=row.get("breached"),
                            source="grafana",
                            raw_ref=str(row.get("id") or row.get("ref") or f"grafana-kpi-{idx}"),
                            labels={"service_id": row.get("service_id"), "source_namespace": "grafana"},
                        )
                    )
        return rows

    @staticmethod
    def _semantic_projection(tool_name: str, arguments: dict[str, Any], result: Any, kpis: list[KpiEvidence]) -> dict[str, Any]:
        return {
            "kind": "telemetry_evidence_projection",
            "source": "grafana",
            "tool": tool_name,
            "arguments": arguments,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "kpis": [
                {"name": kpi.name, "breached": kpi.breached, "raw_ref": kpi.raw_ref}
                for kpi in kpis
            ],
            "summary": "Compact semantic projection only; raw telemetry remains in Grafana/LGTM.",
            "result_ref": result.get("ref") if isinstance(result, dict) else None,
        }

    @staticmethod
    async def _project_to_gbrain(context: TelecomContext, projection: dict[str, Any]) -> None:
        try:
            await context.mcp_hub.call_tool("gbrain", "put_observation", projection)
        except Exception:
            projection["projection_status"] = "skipped_or_unavailable"

    @staticmethod
    def _format(tool_name: str, kpis: list[KpiEvidence], result: Any) -> str:
        lines = [f"**Telemetry Evidence**", f"- Grafana tool: `{tool_name}` via MCP Hub"]
        if kpis:
            for kpi in kpis:
                status = "breached" if kpi.breached else "observed"
                value = "" if kpi.value is None else f" value={kpi.value}"
                lines.append(f"- KPI {kpi.name}: {status}{value}")
        elif result:
            lines.append("- Evidence result received; no KPI rows were normalized.")
        else:
            lines.append("- No telemetry evidence returned by the connector.")
        return "\n".join(lines)
