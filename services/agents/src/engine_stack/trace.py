"""Shared trace models for engine-stack routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EngineCandidate:
    engine_id: str
    confidence: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class EngineRouteTrace:
    query: str
    selected_engine: str | None = None
    engine_confidence: float = 0.0
    candidates: list[EngineCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "selected_engine": self.selected_engine,
            "engine_confidence": self.engine_confidence,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "warnings": self.warnings,
        }
