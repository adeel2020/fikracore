"""Unified Capability Registry for FikraCore (§9, §10, §47, §89).

Single authoritative registry exposing all 10 FikraCore core capabilities:
- investigate: Explain what happened and why (H1)
- discover: Identify missing or insufficient operational knowledge (H2)
- learn: Validate, promote and manage learned knowledge (H3)
- predict: Run proactive what-if and resilience analysis (H4)
- simulate: Execute simulator scenarios across any stage
- inspect: Inspect knowledge inventory, topology, scenarios and reasoning
- present: Produce investigation or curated-demo presentation state
- benchmark: Run H1-H4 and integration benchmarks
- report: Generate benchmark and analysis reports
- validate: Validate scenarios, learning units and artifacts

Adheres strictly to:
- One Telecom Brain. One Capability Layer. One Shared State.
- Zero Truth Leakage: Hidden truth isolated exclusively to benchmark/evaluator contexts.
- Strict Role and Permission Boundaries (RBAC).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import time
from typing import Any, Callable, Type
from pydantic import BaseModel, Field

from ..investigation.contracts import (
    StandardPresentationModel,
    SharedStructuredState,
)


class RolePermission(str, Enum):
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    SME_VALIDATOR = "SME_VALIDATOR"
    ADMIN = "ADMIN"


class ExecutionContext(BaseModel):
    caller_id: str = "operator-01"
    caller_role: RolePermission = RolePermission.OPERATOR
    session_id: str = "default-session"
    mode: str = "INVESTIGATION"  # INVESTIGATION or DEMO
    current_step: int = 1
    options: dict[str, Any] = Field(default_factory=dict)


class CapabilityError(Exception):
    def __init__(self, error_code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class CapabilityExecutionResult(BaseModel):
    success: bool
    capability_name: str
    data: Any = None
    errors: list[str] = Field(default_factory=list)
    error_code: str | None = None
    execution_time_ms: float = 0.0
    provenance: dict[str, Any] = Field(default_factory=dict)
    terminal_state: str | None = None


class CapabilityDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    permissions: list[RolePermission] = Field(
        default_factory=lambda: [RolePermission.OPERATOR, RolePermission.ADMIN]
    )
    supports_cli: bool = True
    supports_ui: bool = True
    supports_zaki: bool = True
    supports_demo: bool = True
    supports_api: bool = True
    read_only: bool = True
    handler: Callable[[dict[str, Any], ExecutionContext], Any] = Field(exclude=True)


class CapabilityRegistry:
    """Unified Capability Registry maintaining all capability definitions and enforcing access."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDefinition] = {}
        self.audit_log: list[dict[str, Any]] = []

    def register(self, capability: CapabilityDefinition) -> None:
        self._capabilities[capability.name.lower()] = capability

    def get(self, name: str) -> CapabilityDefinition | None:
        return self._capabilities.get(name.lower())

    def list_all(self) -> list[CapabilityDefinition]:
        return list(self._capabilities.values())

    def execute(
        self,
        name: str,
        input_data: dict[str, Any] | None = None,
        context: ExecutionContext | None = None,
    ) -> CapabilityExecutionResult:
        """Executes capability with permissions checking, audit logging, and timing."""
        ctx = context or ExecutionContext()
        cap_name = name.lower()
        cap = self.get(cap_name)

        if not cap:
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                errors=[f"Capability '{name}' not found in registry."],
                error_code="CAPABILITY_NOT_FOUND",
            )

        # RBAC Check
        if ctx.caller_role not in cap.permissions:
            err_msg = (
                f"Permission denied: role '{ctx.caller_role.value}' does not have permission "
                f"to execute capability '{cap_name}' (requires one of {[p.value for p in cap.permissions]})."
            )
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                errors=[err_msg],
                error_code="PERMISSION_DENIED",
            )

        inputs = input_data or {}
        start_time = time.perf_counter()
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            raw_output = cap.handler(inputs, ctx)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            # Extract terminal_state if available
            term_state = None
            if isinstance(raw_output, dict):
                term_state = raw_output.get("terminal_state")
            elif hasattr(raw_output, "terminal_state"):
                term_val = getattr(raw_output, "terminal_state")
                term_state = term_val.value if hasattr(term_val, "value") else str(term_val)

            audit_entry = {
                "timestamp": timestamp,
                "capability": cap_name,
                "caller_id": ctx.caller_id,
                "caller_role": ctx.caller_role.value,
                "session_id": ctx.session_id,
                "success": True,
                "duration_ms": elapsed_ms,
                "read_only": cap.read_only,
            }
            self.audit_log.append(audit_entry)

            provenance = {
                "capability": cap_name,
                "executed_at": timestamp,
                "caller_id": ctx.caller_id,
                "caller_role": ctx.caller_role.value,
                "session_id": ctx.session_id,
                "duration_ms": elapsed_ms,
            }

            return CapabilityExecutionResult(
                success=True,
                capability_name=cap_name,
                data=raw_output,
                execution_time_ms=elapsed_ms,
                provenance=provenance,
                terminal_state=term_state,
            )

        except CapabilityError as ce:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            self.audit_log.append({
                "timestamp": timestamp,
                "capability": cap_name,
                "caller_id": ctx.caller_id,
                "caller_role": ctx.caller_role.value,
                "session_id": ctx.session_id,
                "success": False,
                "duration_ms": elapsed_ms,
                "error": ce.message,
                "error_code": ce.error_code,
            })
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                errors=[ce.message],
                error_code=ce.error_code,
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            self.audit_log.append({
                "timestamp": timestamp,
                "capability": cap_name,
                "caller_id": ctx.caller_id,
                "caller_role": ctx.caller_role.value,
                "session_id": ctx.session_id,
                "success": False,
                "duration_ms": elapsed_ms,
                "error": str(exc),
                "error_code": "INTERNAL_ERROR",
            })
            return CapabilityExecutionResult(
                success=False,
                capability_name=cap_name,
                errors=[f"{type(exc).__name__}: {exc}"],
                error_code="EXECUTION_FAILED",
                execution_time_ms=elapsed_ms,
            )

    def get_audit_trail(self) -> list[dict[str, Any]]:
        return list(self.audit_log)


def build_shared_state_from_presentation(
    model: StandardPresentationModel,
    capability_name: str = "investigate",
    session_id: str = "default-session",
) -> SharedStructuredState:
    """Constructs the Section 55 SharedStructuredState model from a StandardPresentationModel."""
    return SharedStructuredState(
        session={"session_id": session_id, "timestamp": datetime.now(timezone.utc).isoformat()},
        scenario=model.scenario,
        capability={"name": capability_name, "status": "ACTIVE"},
        impact=model.impact,
        timeline=model.timeline,
        topology=model.topology,
        evidence=model.timeline,
        reasoning=model.reasoning,
        knowledge_gap={
            "gaps": model.reasoning.get("knowledge_gaps", []),
            "unexplained_residuals": model.reasoning.get("unexplained_residual", []),
            "boundary": model.topology.get("gap_boundary"),
        },
        learning=model.learning or {},
        resilience=model.resilience or {},
        knowledge_inventory=model.knowledge_inventory or {},
        provenance={"provider": "FikraCore-Unified-Brain", "timestamp": datetime.now(timezone.utc).isoformat()},
        presentation=model.presentation,
    )
