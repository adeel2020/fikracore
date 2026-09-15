"""HTTP transport helpers for MCP Hub."""

from __future__ import annotations

from typing import Any

from capability_registry import ConnectorManifest

from .hub import MCPClientHub


def call_http_method(hub: MCPClientHub, connector: ConnectorManifest, method: str, params: dict[str, Any]) -> Any:
    """Call an MCP HTTP method through the canonical hub implementation."""
    return hub._call_http_method(connector, method, params)


__all__ = ["call_http_method"]
