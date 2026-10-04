"""
FikraCore Declarative Runtime Rules Engine
==========================================
Central entrypoint for data-driven, declarative runtime rules evaluation.
"""

from .base import RuleDecision, RuleEvaluationResult, RuntimeRuleContract
from .registry import RuleRegistry, default_rule_registry
from .selectors import RuleSelector
from .evaluator import GenericRuleEvaluator
from .rca_rules import RULE_RCA_001
from .action_rules import RULE_SAFETY_001

# Register default core operational rules
default_rule_registry.register_rule(RULE_RCA_001)
default_rule_registry.register_rule(RULE_SAFETY_001)

# Default evaluator instance
default_rule_evaluator = GenericRuleEvaluator(RuleSelector(default_rule_registry))

__all__ = [
    "RuleDecision",
    "RuleEvaluationResult",
    "RuntimeRuleContract",
    "RuleRegistry",
    "default_rule_registry",
    "RuleSelector",
    "GenericRuleEvaluator",
    "default_rule_evaluator",
    "RULE_RCA_001",
    "RULE_SAFETY_001",
]
