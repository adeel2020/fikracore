"""Policy & Guardrail Engine for Zaki v1 Dark NOC."""

from __future__ import annotations

from typing import Any, Dict, Optional
from ..domain.enums import AuthorityLevel, PolicyDecisionType


class PolicyDecision:
    def __init__(
        self,
        decision: PolicyDecisionType,
        reason: str,
        approval_required: bool = False,
        policy_version: str = "1.0.0",
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.approval_required = approval_required
        self.policy_version = policy_version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "approval_required": self.approval_required,
            "policy_version": self.policy_version,
        }


class PolicyEngine:
    """Enforces zero-trust, least-privilege guardrails on agent tool execution."""

    def evaluate(
        self,
        actor: str,
        tool_id: str,
        required_authority: AuthorityLevel,
        current_authority: AuthorityLevel,
        risk_level: str = "LOW",
    ) -> PolicyDecision:
        # Action tools require Level 4 (HITL) or explicit auto-execute (Level 5)
        if required_authority >= AuthorityLevel.LEVEL_4_HITL_EXECUTE:
            if current_authority < AuthorityLevel.LEVEL_4_HITL_EXECUTE:
                return PolicyDecision(
                    decision=PolicyDecisionType.DENY,
                    reason=f"Current authority level {current_authority} insufficient for action tool {tool_id} (requires {required_authority})",
                )
            elif current_authority == AuthorityLevel.LEVEL_4_HITL_EXECUTE:
                return PolicyDecision(
                    decision=PolicyDecisionType.ALLOW_WITH_HITL,
                    reason=f"Action tool {tool_id} requires explicit operator human validation",
                    approval_required=True,
                )
            else:
                return PolicyDecision(
                    decision=PolicyDecisionType.ALLOW,
                    reason=f"Autonomous execution permitted at authority level {current_authority}",
                )

        # Read / Analysis tools
        if current_authority >= required_authority:
            return PolicyDecision(
                decision=PolicyDecisionType.ALLOW,
                reason=f"Authorized under policy profile for {tool_id}",
            )

        return PolicyDecision(
            decision=PolicyDecisionType.DENY,
            reason=f"Authority mismatch: {current_authority} < {required_authority}",
        )


default_policy_engine = PolicyEngine()
