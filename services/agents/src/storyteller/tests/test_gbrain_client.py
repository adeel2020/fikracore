"""Unit tests for the gbrain transport — no live gbrain required.

Tests the subprocess transport's error handling and JSON extraction using a
fake CLI binary, plus the HTTP MCP URL/route construction logic.
"""

from __future__ import annotations

import json

import pytest
from storyteller.knowledge.gbrain_client import GbrainClient, GbrainError, _extract_json


class FakeCli:
    """Emulates the gbrain call CLI for a single tool invocation."""

    def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __call__(self, argv: list[str], **kwargs) -> FakeCliResult:
        return FakeCliResult(self)


class FakeCliResult:
    def __init__(self, fake: FakeCli) -> None:
        self.returncode = fake.returncode
        self.stdout = fake.stdout
        self.stderr = fake.stderr


def test_extract_json_object() -> None:
    text = "notice: upgrading\n" + json.dumps({"slug": "x"})
    assert _extract_json(text) == {"slug": "x"}


def test_extract_json_array() -> None:
    text = json.dumps([{"a": 1}])
    assert _extract_json(text) == [{"a": 1}]


def test_extract_json_missing_raises() -> None:
    with pytest.raises(GbrainError):
        _extract_json("no json here")


def test_subprocess_error_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GBRAIN_MCP_URL", raising=False)
    monkeypatch.delenv("GBRAIN_MCP_TOKEN", raising=False)
    client = GbrainClient(cli="fake")
    monkeypatch.setattr("storyteller.knowledge.gbrain_client.shutil.which", lambda _: "/usr/bin/fake-gbrain")
    monkeypatch.setattr(
        "storyteller.knowledge.gbrain_client.subprocess.run",
        FakeCli(0, json.dumps({"error": "page_not_found"}), ""),
    )
    with pytest.raises(GbrainError, match="page_not_found"):
        client.call("get_page", {"slug": "nope"})


def test_subprocess_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GBRAIN_MCP_URL", raising=False)
    monkeypatch.delenv("GBRAIN_MCP_TOKEN", raising=False)
    client = GbrainClient(cli="fake")
    monkeypatch.setattr("storyteller.knowledge.gbrain_client.shutil.which", lambda _: "/usr/bin/fake-gbrain")
    monkeypatch.setattr(
        "storyteller.knowledge.gbrain_client.subprocess.run",
        FakeCli(1, "", "boom"),
    )
    with pytest.raises(GbrainError, match="boom"):
        client.call("get_page", {"slug": "x"})


def test_http_mode_selection() -> None:
    client = GbrainClient(mcp_url="http://localhost:8787", mcp_token="tok")
    assert client._http_mode is True


def test_http_mode_routes_through_mcp_hub_first(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    class FakeHub:
        def call_tool_sync(self, connector_id: str, tool: str, params: dict) -> dict:
            calls.append((connector_id, tool, params))
            return {"slug": params["slug"]}

    monkeypatch.setattr("mcp_hub.get_default_mcp_client_hub", lambda: FakeHub())

    client = GbrainClient(mcp_url="http://localhost:8787", mcp_token="tok")
    assert client.call("get_page", {"slug": "mobile-core/incidents/test"}) == {"slug": "mobile-core/incidents/test"}
    assert calls == [("gbrain", "get_page", {"slug": "mobile-core/incidents/test"})]


def test_default_transport_is_local_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GBRAIN_MCP_URL", raising=False)
    monkeypatch.delenv("GBRAIN_MCP_TOKEN", raising=False)
    client = GbrainClient()
    assert client._http_mode is True
    assert client.mcp_url.rstrip("/").removesuffix("/mcp") == "http://localhost:3131"


def test_subprocess_mode_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GBRAIN_MCP_URL", raising=False)
    monkeypatch.delenv("GBRAIN_MCP_TOKEN", raising=False)
    client = GbrainClient(cli="/usr/bin/gbrain")
    assert client._http_mode is False
