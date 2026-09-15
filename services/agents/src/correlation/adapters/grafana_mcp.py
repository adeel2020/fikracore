"""Grafana MCP transport helpers.

This module intentionally stays transport-only. Normalization into
``AlarmEvent`` and ``EvidenceEvent`` belongs to source-specific adapters so the
correlation engine remains deterministic and source-agnostic.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


class GrafanaMcpError(RuntimeError):
    """Raised when Grafana MCP returns an error or cannot be reached."""


class GrafanaMcpClient:
    """Minimal JSON-RPC client for an HTTP-exposed Grafana MCP server."""

    def __init__(self, *, mcp_url: str | None = None, token: str | None = None) -> None:
        self.mcp_url = (mcp_url or os.environ.get("GRAFANA_MCP_URL") or "").rstrip("/")
        self.token = token or os.environ.get("GRAFANA_MCP_TOKEN")
        if not self.mcp_url:
            raise GrafanaMcpError("GRAFANA_MCP_URL is not configured")

    def call(self, tool: str, arguments: dict[str, Any] | None = None) -> Any:
        url = self.mcp_url if self.mcp_url.endswith("/mcp") else self.mcp_url + "/mcp"
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments or {}},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = _extract_payload(response.read().decode("utf-8"), response.headers.get("Content-Type", ""))
        except Exception as exc:  # noqa: BLE001 - caller reports transport context
            raise GrafanaMcpError(f"Grafana MCP call '{tool}' failed: {exc}") from exc
        if payload.get("error"):
            raise GrafanaMcpError(f"Grafana MCP tool '{tool}' error: {payload['error']}")
        return _extract_tool_result(payload.get("result", {}))


def _extract_payload(text: str, content_type: str) -> dict[str, Any]:
    if "text/event-stream" not in content_type.lower():
        return json.loads(text)
    for line in text.splitlines():
        if line.startswith("data:"):
            data = line.removeprefix("data:").strip()
            if data and data != "[DONE]":
                return json.loads(data)
    raise GrafanaMcpError("No JSON-RPC payload in Grafana MCP response")


def _extract_tool_result(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    content = result.get("content", [])
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text") or ""
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return result
