"""Base service contract and confidence router."""

from __future__ import annotations

from typing import Protocol

from ..engine_context import TelecomContext
from ..models import TelecomRequest, TelecomResult, TelecomTrace


class TelecomService(Protocol):
    id: str

    async def can_handle(self, request: TelecomRequest) -> float:
        ...

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        ...


class ServiceRouter:
    def __init__(self, services: list[TelecomService], minimum_confidence: float = 0.2) -> None:
        self.services = services
        self.minimum_confidence = minimum_confidence

    async def route(self, request: TelecomRequest) -> tuple[TelecomService | None, TelecomTrace]:
        candidates = []
        for service in self.services:
            confidence = await service.can_handle(request)
            candidates.append({"service_id": service.id, "confidence": confidence})

        candidates.sort(key=lambda item: item["confidence"], reverse=True)
        trace = TelecomTrace(candidates=candidates)
        if not candidates or candidates[0]["confidence"] < self.minimum_confidence:
            trace.warnings.append("No service met routing confidence; retained request as standalone observation.")
            return None, trace

        selected = next(service for service in self.services if service.id == candidates[0]["service_id"])
        trace.selected_service = selected.id
        trace.service_confidence = candidates[0]["confidence"]
        return selected, trace
