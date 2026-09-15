#!/usr/bin/env python3
"""Validate the live LGTM -> Grafana MCP -> MCP Hub path."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


PROMQL_BY_SERVICE = {
    "voice-call-setup": 'cssr_percent{service_id="voice-call-setup"}',
    "sgi-data": 'sgi_throughput_percent{service_id="sgi-data"}',
    "lte-attach": 'lte_attach_success_rate_percent{service_id="lte-attach"}',
}

LOGQL_BY_SERVICE = {
    "voice-call-setup": '{service_name="telecom.voice-call-setup"}',
    "sgi-data": '{service_name="telecom.sgi-data"}',
    "lte-attach": '{service_name="telecom.lte-attach"}',
}


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tool_names(payload: Any) -> list[str]:
    if isinstance(payload, dict) and isinstance(payload.get("tools"), dict):
        payload = payload["tools"]
    if isinstance(payload, dict):
        raw_tools = payload.get("tools") or payload.get("data") or payload.get("results") or []
    else:
        raw_tools = payload if isinstance(payload, list) else []
    names: list[str] = []
    for tool in raw_tools:
        if isinstance(tool, str):
            names.append(tool)
        elif isinstance(tool, dict) and (tool.get("name") or tool.get("id")):
            names.append(str(tool.get("name") or tool.get("id")))
    return sorted(set(names))


def _pick(names: list[str], candidates: tuple[str, ...]) -> str | None:
    available = set(names)
    for candidate in candidates:
        if candidate in available:
            return candidate
    return None


def _call_connector(base: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    return _post_json(
        f"{base}/api/jarvis/connectors/grafana/call",
        {"tool_name": tool_name, "arguments": arguments},
    )


def _records_from_connector_result(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "result" in payload:
        payload = payload["result"]
    if isinstance(payload, dict):
        for key in ("datasources", "data", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if payload:
            return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _datasource_uids(base: str, tool_names: list[str]) -> dict[str, str]:
    if "list_datasources" not in tool_names:
        return {}
    payload = _call_connector(base, "list_datasources", {})
    uids: dict[str, str] = {}
    for row in _records_from_connector_result(payload):
        uid = row.get("uid") or row.get("datasourceUid")
        ds_type = str(row.get("type") or row.get("typeName") or "").lower()
        name = str(row.get("name") or "").lower()
        if not uid:
            continue
        if "prometheus" in ds_type or "prometheus" in name:
            uids["prometheus"] = str(uid)
        if "loki" in ds_type or "loki" in name:
            uids["loki"] = str(uid)
    return uids


def validate(api_base: str, service_id: str) -> dict[str, Any]:
    base = api_base.rstrip("/")
    report: dict[str, Any] = {"api_base": base, "service_id": service_id}
    report["status"] = _get_json(f"{base}/api/jarvis/connectors/status")
    tools_payload = _get_json(f"{base}/api/jarvis/connectors/grafana/tools")
    names = _tool_names(tools_payload)
    report["grafana_tools"] = names
    datasource_uids = _datasource_uids(base, names)
    report["datasource_uids"] = datasource_uids

    metric_tool = _pick(names, ("query_prometheus", "query_prometheus_range", "query_kpi_window", "query_metrics"))
    log_tool = _pick(names, ("query_loki_logs", "query_loki", "query_logs"))
    report["selected_tools"] = {"metrics": metric_tool, "logs": log_tool}
    calls: list[dict[str, Any]] = []

    if metric_tool:
        arguments = {"expr": PROMQL_BY_SERVICE.get(service_id, service_id), "queryType": "instant", "endTime": "now"}
        if datasource_uids.get("prometheus"):
            arguments["datasourceUid"] = datasource_uids["prometheus"]
        calls.append(
            {
                "kind": "metric",
                "tool": metric_tool,
                "arguments": arguments,
                "result": _call_connector(base, metric_tool, arguments),
            }
        )
    if log_tool:
        arguments = {"logql": LOGQL_BY_SERVICE.get(service_id, service_id), "limit": 5, "direction": "backward"}
        if datasource_uids.get("loki"):
            arguments["datasourceUid"] = datasource_uids["loki"]
        calls.append(
            {
                "kind": "log",
                "tool": log_tool,
                "arguments": arguments,
                "result": _call_connector(base, log_tool, arguments),
            }
        )

    report["calls"] = calls
    report["traces"] = _get_json(f"{base}/api/jarvis/connectors/traces?limit=20")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Grafana MCP through Mark's MCP Hub.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--service-id", default="voice-call-setup", choices=sorted(PROMQL_BY_SERVICE))
    parser.add_argument("--output", help="Optional report JSON path")
    args = parser.parse_args()

    try:
        report = validate(args.api_base, args.service_id)
    except urllib.error.URLError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "api_base": args.api_base}, indent=2))
        return 1

    report["ok"] = bool(report.get("grafana_tools"))
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
