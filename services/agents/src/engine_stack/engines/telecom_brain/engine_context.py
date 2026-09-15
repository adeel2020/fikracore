"""Runtime context for TelecomBrainEngine service calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from capability_registry import MarkRegistry, load_default_registry
from mcp_hub import MCPClientHub, get_default_mcp_client_hub


@dataclass
class TelecomContext:
    capability_registry: MarkRegistry
    mcp_hub: MCPClientHub
    memory: dict[str, Any] = field(default_factory=dict)


def create_default_context() -> TelecomContext:
    return TelecomContext(
        capability_registry=load_default_registry(),
        mcp_hub=get_default_mcp_client_hub(),
    )
