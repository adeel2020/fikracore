"""Registry-backed connector shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from capability_registry import ConnectorManifest, MarkRegistry, load_default_registry
from mcp_hub import MCPClientHub, get_default_mcp_client_hub


@dataclass
class RegistryBackedConnector:
    """A connector descriptor whose runtime calls go through MCP Hub."""

    connector_id: str
    registry: MarkRegistry | None = None
    hub: MCPClientHub | None = None

    @property
    def manifest(self) -> ConnectorManifest:
        registry = self.registry or load_default_registry()
        return registry.connectors[self.connector_id]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        hub = self.hub or get_default_mcp_client_hub()
        return await hub.call_tool(self.connector_id, tool_name, arguments or {})

    def call_tool_sync(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        hub = self.hub or get_default_mcp_client_hub()
        return hub.call_tool_sync(self.connector_id, tool_name, arguments or {})


__all__ = ["RegistryBackedConnector"]
