"""Lightweight registry-backed engine scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from capability_registry import EngineManifest, MarkRegistry, load_default_registry


@dataclass
class RegistryBackedEngine:
    """Represents a registered engine that has not moved to a concrete package yet."""

    engine_id: str
    registry: MarkRegistry | None = None

    @property
    def manifest(self) -> EngineManifest:
        registry = self.registry or load_default_registry()
        return registry.engines[self.engine_id]

    async def initialize(self) -> None:
        """Match the async lifecycle contract used by concrete engines."""

    async def process(self, query: str, **_: Any) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "query": query,
            "status": "registered",
            "message": f"{self.manifest.name} is registered in capability_registry; concrete package migration is pending.",
        }
