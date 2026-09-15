"""Grafana/LGTM evidence provider through the shared MCP Client Hub."""

from __future__ import annotations

import json
from typing import Any

from storyteller.knowledge.provenance import ProvenanceFact, fact


class GrafanaEvidenceProvider:
    """Fetch telemetry evidence on demand and normalize it into provenance facts."""

    connector_id = "grafana"
    _TOOL_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("alerts", ("read_alerts", "list_alerts", "list_alert_rules", "query_alerts", "query_alarm_window")),
        ("metrics", ("query_prometheus", "query_prometheus_range", "query_kpi_window", "query_metrics")),
        ("logs", ("query_loki_logs", "query_loki", "query_logs")),
        ("traces", ("query_tempo", "query_traces")),
        ("dashboards", ("get_service_dashboard_evidence", "search_dashboards", "read_dashboards", "get_dashboard")),
    )

    def __init__(self, hub: Any | None = None) -> None:
        self._hub = hub
        self.last_errors: list[str] = []
        self._datasource_cache: dict[str, str] = {}

    def evidence_for_incident(self, incident_id: str, *, query: str = "", limit: int = 10) -> list[ProvenanceFact]:
        """Return best-effort Grafana/LGTM evidence for an incident."""
        evidence: list[ProvenanceFact] = []
        self.last_errors = []
        for tool_name, args in self._tool_requests(incident_id, query=query, limit=limit):
            try:
                result = self._call(tool_name, args)
            except Exception as exc:
                self.last_errors.append(f"{tool_name}: {exc}")
                continue
            evidence.extend(self._normalize(tool_name, result, incident_id))
        return evidence[:limit]

    def _call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        hub = self._hub
        if hub is None:
            from mcp_hub import get_default_mcp_client_hub

            hub = get_default_mcp_client_hub()
        return hub.call_tool_sync(self.connector_id, tool_name, arguments)

    def _tool_requests(self, incident_id: str, *, query: str, limit: int) -> list[tuple[str, dict[str, Any]]]:
        available = self._available_tool_names()
        requests: list[tuple[str, dict[str, Any]]] = []
        for evidence_kind, candidates in self._TOOL_GROUPS:
            tool_name = self._select_tool(candidates, available)
            if not tool_name:
                continue
            requests.append((tool_name, self._arguments_for(evidence_kind, tool_name, incident_id, query=query, limit=limit, available=available)))
        return requests

    def _available_tool_names(self) -> set[str] | None:
        hub = self._hub
        if hub is None:
            try:
                from mcp_hub import get_default_mcp_client_hub

                hub = get_default_mcp_client_hub()
            except Exception as exc:
                self.last_errors.append(f"tools/list: {exc}")
                return None
        list_tools = getattr(hub, "list_tools_sync", None)
        if not callable(list_tools):
            return None
        try:
            payload = list_tools(self.connector_id)
        except Exception as exc:
            self.last_errors.append(f"tools/list: {exc}")
            return None
        return self._tool_names_from_payload(payload)

    @staticmethod
    def _tool_names_from_payload(payload: Any) -> set[str]:
        if isinstance(payload, dict):
            raw_tools = payload.get("tools") or payload.get("data") or payload.get("results") or []
        elif isinstance(payload, list):
            raw_tools = payload
        else:
            raw_tools = []
        names: set[str] = set()
        for tool in raw_tools:
            if isinstance(tool, str):
                names.add(tool)
            elif isinstance(tool, dict):
                name = tool.get("name") or tool.get("id")
                if name:
                    names.add(str(name))
        return names

    @staticmethod
    def _select_tool(candidates: tuple[str, ...], available: set[str] | None) -> str | None:
        if available is None:
            return candidates[0]
        for candidate in candidates:
            if candidate in available:
                return candidate
        return None

    def _arguments_for(
        self,
        evidence_kind: str,
        tool_name: str,
        incident_id: str,
        *,
        query: str,
        limit: int,
        available: set[str] | None,
    ) -> dict[str, Any]:
        service_id = _service_hint(incident_id, query)
        promql = _promql_for(service_id, query or incident_id)
        logql = _logql_for(service_id, query or incident_id)

        if tool_name == "query_prometheus":
            args: dict[str, Any] = {"expr": promql, "queryType": "instant", "endTime": "now"}
            datasource_uid = self._datasource_uid("prometheus", available)
            if datasource_uid:
                args["datasourceUid"] = datasource_uid
            return args
        if tool_name == "query_loki_logs":
            args = {"logql": logql, "limit": min(limit, 100), "direction": "backward"}
            datasource_uid = self._datasource_uid("loki", available)
            if datasource_uid:
                args["datasourceUid"] = datasource_uid
            return args

        base: dict[str, Any] = {"incident_id": incident_id, "query": query or incident_id, "limit": limit}
        if evidence_kind == "metrics":
            base.setdefault("expr", promql)
            base.setdefault("service_id", service_id)
        elif evidence_kind == "logs":
            base.setdefault("logql", logql)
        elif evidence_kind == "traces":
            base.setdefault("service_name", service_id)
        elif evidence_kind == "dashboards":
            base.setdefault("service_id", service_id)
        return base

    def _datasource_uid(self, datasource_type: str, available: set[str] | None) -> str | None:
        if datasource_type in self._datasource_cache:
            return self._datasource_cache[datasource_type]
        if available is not None and "list_datasources" not in available:
            return None
        try:
            result = self._call("list_datasources", {})
        except Exception as exc:
            self.last_errors.append(f"list_datasources: {exc}")
            return None
        for datasource in _records_from_result(result):
            if not isinstance(datasource, dict):
                continue
            ds_type = str(datasource.get("type") or datasource.get("typeName") or "").lower()
            name = str(datasource.get("name") or "").lower()
            uid = datasource.get("uid") or datasource.get("datasourceUid")
            if not uid:
                continue
            if "prometheus" in ds_type or "prometheus" in name:
                self._datasource_cache["prometheus"] = str(uid)
            if "loki" in ds_type or "loki" in name:
                self._datasource_cache["loki"] = str(uid)
        return self._datasource_cache.get(datasource_type)

    @staticmethod
    def _normalize(tool_name: str, result: Any, incident_id: str) -> list[ProvenanceFact]:
        records = _records_from_result(result)

        out: list[ProvenanceFact] = []
        for idx, record in enumerate(records, start=1):
            if isinstance(record, dict):
                title = (
                    record.get("title")
                    or record.get("name")
                    or record.get("alertname")
                    or record.get("metric")
                    or record.get("message")
                    or record.get("expr")
                    or record.get("traceID")
                    or record.get("uid")
                    or f"{tool_name} evidence"
                )
                timestamp = record.get("timestamp") or record.get("time") or record.get("startsAt")
                confidence = record.get("confidence")
                extra = {k: v for k, v in record.items() if k not in {"title", "name", "message"}}
            else:
                title = str(record)
                timestamp = None
                confidence = None
                extra = {}
            out.append(
                fact(
                    str(title),
                    source=f"grafana/{tool_name}",
                    timestamp=str(timestamp) if timestamp else None,
                    confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
                    relationship="telemetry-evidence",
                    slug=f"grafana/{incident_id}/{tool_name}/{idx}",
                    extra=extra,
                )
            )
        return out


def _records_from_result(result: Any) -> list[Any]:
    result = _unwrap_content(result)
    if isinstance(result, list):
        return result
    if not isinstance(result, dict):
        return [result] if result else []

    data = result.get("data")
    if isinstance(data, dict) and isinstance(data.get("result"), list):
        return data["result"]
    if isinstance(data, list):
        return data

    for key in (
        "results",
        "alerts",
        "frames",
        "kpis",
        "metrics",
        "series",
        "streams",
        "logs",
        "traces",
        "dashboards",
        "panels",
        "datasources",
    ):
        value = result.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
    return [result] if result else []


def _unwrap_content(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    content = result.get("content")
    if not isinstance(content, list):
        return result
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        text = item.get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return result


def _service_hint(incident_id: str, query: str) -> str:
    text = query or incident_id
    tail = text.rstrip("/").split("/")[-1]
    if not tail:
        return "unknown"
    parts = tail.split("-")
    if len(parts) > 2:
        return "-".join(parts[:2])
    return tail


def _promql_for(service_id: str, fallback: str) -> str:
    by_service = {
        "voice-call": 'cssr_percent{service_id="voice-call-setup"}',
        "voice-call-setup": 'cssr_percent{service_id="voice-call-setup"}',
        "sgi-data": 'sgi_throughput_percent{service_id="sgi-data"}',
        "lte-attach": 'lte_attach_success_rate_percent{service_id="lte-attach"}',
    }
    return by_service.get(service_id, fallback)


def _logql_for(service_id: str, fallback: str) -> str:
    by_service = {
        "voice-call": '{service_name="telecom.voice-call-setup"}',
        "voice-call-setup": '{service_name="telecom.voice-call-setup"}',
        "sgi-data": '{service_name="telecom.sgi-data"}',
        "lte-attach": '{service_name="telecom.lte-attach"}',
    }
    return by_service.get(service_id, f'{{service_id="{fallback}"}}')
