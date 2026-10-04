"""
Runtime Rule Registry
=====================
Data-driven registry managing declarative runtime rules with versioning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .base import RuntimeRuleContract


class RuleRegistry:
    """Central store for active and versioned runtime rules."""

    def __init__(self) -> None:
        self._rules: Dict[str, RuntimeRuleContract] = {}

    def register_rule(self, rule: RuntimeRuleContract) -> None:
        """Register or update a runtime rule."""
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[RuntimeRuleContract]:
        """Fetch a rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(
        self,
        rule_type: Optional[str] = None,
        enabled_only: bool = True,
        applies_to: Optional[str] = None,
    ) -> List[RuntimeRuleContract]:
        """List rules matching optional type and target contract filters."""
        matched: List[RuntimeRuleContract] = []
        for rule in self._rules.values():
            if enabled_only and not rule.enabled:
                continue
            if rule_type and rule.rule_type != rule_type:
                continue
            if applies_to and applies_to not in rule.applies_to:
                continue
            matched.append(rule)
        # Sort by priority ascending (lower priority number = executed first)
        return sorted(matched, key=lambda r: r.priority)

    def clear(self) -> None:
        """Clear registry."""
        self._rules.clear()


# Default singleton instance
default_rule_registry = RuleRegistry()
