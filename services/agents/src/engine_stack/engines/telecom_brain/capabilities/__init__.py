"""Unified Capability Registry Package for FikraCore (§9, §10, §47)."""

from .registry import (
    CapabilityDefinition,
    CapabilityError,
    CapabilityExecutionResult,
    CapabilityRegistry,
    ExecutionContext,
    RolePermission,
    build_shared_state_from_presentation,
)
from .investigate import investigate_capability
from .discover import discover_capability
from .learn import learn_capability
from .predict import predict_capability
from .simulate import simulate_capability
from .inspect import inspect_capability
from .present import present_capability
from .benchmark import benchmark_capability
from .report import report_capability
from .validate import validate_capability
from .snapshot import snapshot_capability


def create_default_registry() -> CapabilityRegistry:
    """Build and populate default capability registry with all core capabilities."""
    reg = CapabilityRegistry()
    reg.register(investigate_capability)
    reg.register(discover_capability)
    reg.register(learn_capability)
    reg.register(predict_capability)
    reg.register(simulate_capability)
    reg.register(inspect_capability)
    reg.register(present_capability)
    reg.register(benchmark_capability)
    reg.register(report_capability)
    reg.register(validate_capability)
    reg.register(snapshot_capability)
    return reg


default_capability_registry: CapabilityRegistry = create_default_registry()

__all__ = [
    "CapabilityDefinition",
    "CapabilityError",
    "CapabilityExecutionResult",
    "CapabilityRegistry",
    "ExecutionContext",
    "RolePermission",
    "build_shared_state_from_presentation",
    "default_capability_registry",
    "create_default_registry",
    "investigate_capability",
    "discover_capability",
    "learn_capability",
    "predict_capability",
    "simulate_capability",
    "inspect_capability",
    "present_capability",
    "benchmark_capability",
    "report_capability",
    "validate_capability",
    "snapshot_capability",
]
