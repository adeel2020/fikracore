"""
Runtime Rule Selector
=====================
Selects applicable rules dynamically based on operational triggers, domain scope,
lifecycle state, and contract type (§19).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .base import RuntimeRuleContract
from .registry import RuleRegistry, default_rule_registry


class RuleSelector:
    """Selects the minimal, strictly applicable subset of rules for an operational event."""

    def __init__(self, registry: Optional[RuleRegistry] = None) -> None:
        self.registry = registry or default_rule_registry

    def select_rules(
        self,
        contract_type: str,
        lifecycle_state: Optional[str] = None,
        domain: Optional[str] = None,
        event_type: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> List[RuntimeRuleContract]:
        """
        Query the registry and filter rules whose applies_to, trigger, and scope match.
        """
        all_rules = self.registry.list_rules(enabled_only=True)
        selected: List[RuntimeRuleContract] = []

        for rule in all_rules:
            # 1. Target contract type filter
            if rule.applies_to and contract_type not in rule.applies_to and "*" not in rule.applies_to:
                continue

            # 2. Lifecycle state trigger filter
            trigger_lifecycle = rule.trigger.get("lifecycle") or rule.trigger.get("lifecycle_state")
            if trigger_lifecycle and lifecycle_state:
                if isinstance(trigger_lifecycle, list) and lifecycle_state.upper() not in [s.upper() for s in trigger_lifecycle]:
                    continue
                elif isinstance(trigger_lifecycle, str) and lifecycle_state.upper() != trigger_lifecycle.upper():
                    continue

            # 3. Action type trigger filter
            trigger_action = rule.trigger.get("action_type") or rule.trigger.get("safety_tier")
            if trigger_action and action_type:
                if isinstance(trigger_action, list) and action_type.upper() not in [a.upper() for a in trigger_action]:
                    continue
                elif isinstance(trigger_action, str) and action_type.upper() != trigger_action.upper():
                    continue

            # 4. Domain scope filter
            rule_domains = rule.scope.get("domains")
            if rule_domains and domain:
                if domain.upper() not in [d.upper() for d in rule_domains] and "*" not in rule_domains:
                    continue

            selected.append(rule)

        return selected
