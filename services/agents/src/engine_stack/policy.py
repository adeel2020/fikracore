"""Policy checks shared by MARK engine-stack routing."""

from __future__ import annotations

from dataclasses import dataclass, field

from capability_registry import EngineManifest, MarkRegistry


@dataclass(frozen=True)
class EnginePolicyDecision:
    allowed: bool
    reason: str = ""
    warnings: list[str] = field(default_factory=list)


class EnginePolicy:
    """Validate an engine against capability-registry metadata."""

    def __init__(self, registry: MarkRegistry) -> None:
        self.registry = registry

    def evaluate(self, engine: EngineManifest) -> EnginePolicyDecision:
        missing_services = [service_id for service_id in engine.services if service_id not in self.registry.services]
        missing_connectors = [
            connector_id for connector_id in engine.connectors if connector_id not in self.registry.connectors
        ]
        warnings = []
        if engine.status not in {"active", "beta", "planned"}:
            warnings.append(f"engine status is {engine.status}")
        if missing_services or missing_connectors:
            reason = "engine manifest references unavailable capabilities"
            details = []
            if missing_services:
                details.append(f"missing services: {', '.join(missing_services)}")
            if missing_connectors:
                details.append(f"missing connectors: {', '.join(missing_connectors)}")
            return EnginePolicyDecision(False, f"{reason}; {'; '.join(details)}", warnings)
        return EnginePolicyDecision(True, "allowed by capability registry", warnings)
