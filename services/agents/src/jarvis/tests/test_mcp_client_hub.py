from __future__ import annotations

import asyncio
from dataclasses import replace
import sys

import pytest

from capability_registry import ConnectorManifest, load_default_registry
from mcp_hub import MCPClientHub, MCPPolicyError, get_default_mcp_client_hub


def test_hub_reports_all_registered_connectors_as_mcp_managed():
    hub = MCPClientHub()
    statuses = hub.connector_status()

    assert len(statuses) == 10
    assert statuses["gbrain"]["managed_by"] == "mcp_client_hub"
    assert statuses["codex"]["protocol"] == "stdio"
    assert all(status["transport"] == "mcp" for status in statuses.values())


def test_hybrid_protocol_policy_keeps_codex_stdio_and_shared_services_http():
    hub = MCPClientHub()
    statuses = hub.connector_status()

    assert statuses["codex"]["protocol"] == "stdio"
    assert statuses["gbrain"]["protocol"] == "http"
    assert statuses["grafana"]["protocol"] == "http"
    assert statuses["gmail"]["protocol"] == "http"
    assert statuses["microsoft_teams"]["protocol"] == "http"


def test_grafana_can_override_to_stdio_protocol(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GRAFANA_MCP_PROTOCOL", "stdio")
    monkeypatch.setenv("GRAFANA_MCP_COMMAND", sys.executable)

    statuses = MCPClientHub().connector_status()

    assert statuses["grafana"]["protocol"] == "stdio"
    assert statuses["grafana"]["configured"] is True


def test_hub_blocks_side_effect_without_approval():
    hub = MCPClientHub()

    with pytest.raises(MCPPolicyError):
        asyncio.run(hub.call_tool("gmail", "send_email", {"body": "hello"}))


def test_hub_allows_side_effect_with_approval(monkeypatch: pytest.MonkeyPatch):
    hub = MCPClientHub()

    def fake_call(connector, method, params):
        return {"method": method, "params": params}

    monkeypatch.setenv("GMAIL_MCP_URL", "http://localhost:3999/mcp")
    monkeypatch.setattr(hub, "_call_http_method", fake_call)

    result = asyncio.run(
        hub.call_tool(
            "gmail",
            "send_email",
            {"body": "approved"},
            approval_granted=True,
        )
    )

    assert result["method"] == "tools/call"
    assert result["params"]["name"] == "send_email"
    assert hub.latest_traces(1)[0]["status"] == "ok"
    assert hub.latest_traces(1)[0]["approval_required"] is True


def test_hub_can_list_http_connector_tools(monkeypatch: pytest.MonkeyPatch):
    hub = MCPClientHub()

    def fake_call(connector, method, params):
        return {"tools": [{"name": "get_page"}], "params": params}

    monkeypatch.setattr(hub, "_call_http_method", fake_call)

    result = asyncio.run(hub.list_tools("gbrain"))

    assert result["tools"][0]["name"] == "get_page"
    assert hub.latest_traces(1)[0]["tool_name"] == "tools/list"


def test_hub_can_list_http_connector_tools_synchronously(monkeypatch: pytest.MonkeyPatch):
    hub = MCPClientHub()

    def fake_call(connector, method, params):
        return {"tools": [{"name": "query_prometheus"}], "params": params}

    monkeypatch.setattr(hub, "_call_http_method", fake_call)

    result = hub.list_tools_sync("grafana")

    assert result["tools"][0]["name"] == "query_prometheus"
    assert hub.latest_traces(1)[0]["tool_name"] == "tools/list"


def test_hub_initializes_session_required_http_connector(monkeypatch: pytest.MonkeyPatch):
    hub = MCPClientHub()
    calls = []

    def fake_send(connector, method, params, *, session_id, include_id):
        calls.append((method, session_id, include_id))
        if method == "initialize":
            return {"serverInfo": {"name": "grafana-mcp"}}, {"Mcp-Session-Id": "session-1"}
        if method == "notifications/initialized":
            return {}, {}
        return {"tools": [{"name": "query_prometheus"}]}, {}

    monkeypatch.setattr(hub, "_send_http_jsonrpc", fake_send)

    result = hub.list_tools_sync("grafana")

    assert result["tools"][0]["name"] == "query_prometheus"
    assert calls == [
        ("initialize", None, True),
        ("notifications/initialized", "session-1", False),
        ("tools/list", "session-1", True),
    ]
    assert hub.connector_status()["grafana"]["http_session_active"] is True


def test_hub_persistent_stdio_session_reuses_server_process(tmp_path):
    server = tmp_path / "fake_mcp_server.py"
    server.write_text(
        r"""
import json
import os
import sys

def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if line.strip() == b"":
            break
        if not line:
            raise SystemExit
        key, value = line.decode().strip().split(":", 1)
        headers[key.lower()] = value.strip()
    body = sys.stdin.buffer.read(int(headers["content-length"]))
    return json.loads(body.decode())

def write_message(message):
    body = json.dumps(message).encode()
    sys.stdout.buffer.write(b"Content-Length: " + str(len(body)).encode() + bytes([13, 10, 13, 10]) + body)
    sys.stdout.buffer.flush()

while True:
    msg = read_message()
    method = msg.get("method")
    if method == "notifications/initialized":
        continue
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {}, "serverInfo": {"name": "fake", "version": "1"}}
    elif method == "tools/list":
        result = {"tools": [{"name": "echo"}]}
    elif method == "tools/call":
        result = {"content": [{"type": "text", "text": json.dumps({"pid": os.getpid(), "args": msg["params"]["arguments"]})}]}
    else:
        result = {}
    write_message({"jsonrpc": "2.0", "id": msg.get("id"), "result": result})
""",
        encoding="utf-8",
    )
    registry = load_default_registry()
    connectors = dict(registry.connectors)
    connectors["fake_stdio"] = ConnectorManifest(
        id="fake_stdio",
        name="Fake Stdio",
        kind="test",
        transport="mcp",
        managed_by="mcp_client_hub",
        raw={
            "mcp_runtime": {
                "protocol": "stdio",
                "default_command": sys.executable,
                "args": [str(server)],
                "timeout_seconds": 5,
            }
        },
    )
    hub = MCPClientHub(replace(registry, connectors=connectors))

    tools = asyncio.run(hub.list_tools("fake_stdio"))
    first = asyncio.run(hub.call_tool("fake_stdio", "echo", {"n": 1}))
    second = asyncio.run(hub.call_tool("fake_stdio", "echo", {"n": 2}))

    assert tools["tools"][0]["name"] == "echo"
    assert first["content"][0]["type"] == "text"
    assert second["content"][0]["text"]
    first_payload = __import__("json").loads(first["content"][0]["text"])
    second_payload = __import__("json").loads(second["content"][0]["text"])
    assert first_payload["pid"] == second_payload["pid"]
    assert first_payload["args"] == {"n": 1}
    assert second_payload["args"] == {"n": 2}
    hub.close()


def test_hub_records_failed_call_trace():
    hub = MCPClientHub()

    with pytest.raises(Exception):
        asyncio.run(hub.call_tool("unknown", "anything", {}))

    assert hub.latest_traces() == []


def test_default_hub_is_shared_singleton():
    assert get_default_mcp_client_hub() is get_default_mcp_client_hub()
