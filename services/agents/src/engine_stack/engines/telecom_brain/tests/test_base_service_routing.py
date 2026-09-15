from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine_stack.engines.telecom_brain.engine_context import create_default_context
from engine_stack.engines.telecom_brain.models import TelecomRequest, TelecomResult
from engine_stack.engines.telecom_brain.services.base import ServiceRouter


@dataclass
class FakeService:
    id: str
    confidence: float

    async def can_handle(self, request: TelecomRequest) -> float:
        return self.confidence

    async def handle(self, request: TelecomRequest, context) -> TelecomResult:
        return TelecomResult(text=self.id)


@pytest.mark.anyio
async def test_router_selects_highest_confidence_service() -> None:
    router = ServiceRouter([FakeService("low", 0.25), FakeService("high", 0.9)])

    service, trace = await router.route(TelecomRequest(query="show current incidents"))

    assert service is not None
    assert service.id == "high"
    assert trace.selected_service == "high"
    assert trace.service_confidence == 0.9
    assert [candidate["service_id"] for candidate in trace.candidates] == ["high", "low"]


@pytest.mark.anyio
async def test_router_retains_unmatched_requests_as_observations() -> None:
    router = ServiceRouter([FakeService("weak", 0.1)], minimum_confidence=0.2)

    service, trace = await router.route(TelecomRequest(query="unknown alarm signature"))

    assert service is None
    assert trace.selected_service is None
    assert "standalone observation" in trace.warnings[0]


def test_default_context_uses_canonical_registry_and_mcp_hub() -> None:
    context = create_default_context()

    assert "telecom_brain" in context.capability_registry.engines
    assert "gbrain" in context.capability_registry.connectors
    assert hasattr(context.mcp_hub, "call_tool")
