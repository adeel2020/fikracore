"""Policy helpers for MCP Hub connector calls."""

from __future__ import annotations

from capability_registry import ConnectorManifest


SIDE_EFFECT_PREFIXES = (
    "send",
    "create",
    "update",
    "delete",
    "write",
    "run",
    "execute",
    "deploy",
    "apply",
)


def requires_approval(connector: ConnectorManifest, tool_name: str, explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    if any(permission.endswith("requires_approval") for permission in connector.permissions):
        return tool_name.split("/")[-1].startswith(SIDE_EFFECT_PREFIXES)
    return False


__all__ = ["SIDE_EFFECT_PREFIXES", "requires_approval"]
