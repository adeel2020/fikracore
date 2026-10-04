"""
Generic Runtime Rule Evaluator
==============================
Executes selected runtime rules against operational contracts and resolves conflicts
with deterministic precedence (§32): BLOCK > WARN > PASS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from .base import RuleDecision, RuleEvaluationResult, RuntimeRuleContract
from .selectors import RuleSelector


class GenericRuleEvaluator:
    """Evaluates rules against operational subjects and emits auditable results."""

    def __init__(self, selector: Optional[RuleSelector] = None) -> None:
        self.selector = selector or RuleSelector()

    def evaluate_check(
        self,
        check_def: Dict[str, Any],
        subject: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Tuple[bool, Any, Any]:
        """
        Evaluate a single check expression.
        Returns: (passed: bool, actual_value: Any, expected_threshold: Any)
        """
        field_name = check_def.get("field")
        op = check_def.get("operator", "==")
        threshold = check_def.get("value")

        actual = subject.get(field_name) if field_name in subject else context.get(field_name)

        if op == "==":
            return (actual == threshold, actual, threshold)
        elif op == "!=":
            return (actual != threshold, actual, threshold)
        elif op == ">=":
            try:
                return (float(actual or 0) >= float(threshold or 0), actual, threshold)
            except (ValueError, TypeError):
                return (False, actual, threshold)
        elif op == "<=":
            try:
                return (float(actual or 0) <= float(threshold or 0), actual, threshold)
            except (ValueError, TypeError):
                return (False, actual, threshold)
        elif op == "is_true":
            return (bool(actual), actual, True)
        elif op == "is_false":
            return (not bool(actual), actual, False)
        elif op == "in":
            return (actual in (threshold or []), actual, threshold)
        elif op == "not_in":
            return (actual not in (threshold or []), actual, threshold)

        return (True, actual, threshold)

    def evaluate_rule(
        self,
        rule: RuntimeRuleContract | str,
        subject_id: str,
        subject_type: str,
        subject_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        episode_id: Optional[str] = None,
    ) -> RuleEvaluationResult:
        """Evaluate a single rule against a subject contract."""
        if isinstance(rule, str):
            resolved_rule = self.selector.registry.get_rule(rule)
            if not resolved_rule:
                raise ValueError(f"Rule '{rule}' not found in registry")
            rule = resolved_rule

        ctx = context or {}

        check_evaluations: List[Dict[str, Any]] = []
        rule_decision = RuleDecision.PASS
        reason_codes: List[str] = []
        failure_messages: List[str] = []

        # 1. Evaluate Preconditions
        for prec in rule.preconditions:
            passed, act, exp = self.evaluate_check(prec, subject_data, ctx)
            if not passed:
                # Precondition not met; rule skips without blocking
                return RuleEvaluationResult(
                    rule_id=rule.rule_id,
                    rule_version=rule.rule_version,
                    subject_id=subject_id,
                    subject_type=subject_type,
                    episode_id=episode_id,
                    decision=RuleDecision.PASS,
                    reason=f"Precondition '{prec.get('field')}' not met; rule evaluation skipped.",
                    structured_reason_codes=["PRECONDITION_SKIPPED"],
                )

        # 2. Evaluate Checks
        for check in rule.checks:
            passed, act, exp = self.evaluate_check(check, subject_data, ctx)
            check_evaluations.append({
                "check_id": check.get("check_id", "check"),
                "passed": passed,
                "actual": act,
                "expected": exp,
            })
            if not passed:
                severity = check.get("failure_severity", "BLOCK").upper()
                if severity == "BLOCK":
                    rule_decision = RuleDecision.BLOCK
                elif severity == "WARN" and rule_decision != RuleDecision.BLOCK:
                    rule_decision = RuleDecision.WARN

                reason_codes.append(check.get("check_id", "CHECK_FAILED"))
                msg = check.get("failure_message", f"Check {check.get('check_id')} failed: expected {exp}, got {act}")
                failure_messages.append(msg)

        if rule_decision == RuleDecision.BLOCK:
            reason = "; ".join(failure_messages) if failure_messages else f"Rule {rule.rule_id} blocked execution."
        elif rule_decision == RuleDecision.WARN:
            reason = "; ".join(failure_messages) if failure_messages else f"Rule {rule.rule_id} generated warning."
        else:
            reason = f"Rule {rule.rule_id} ({rule.name}) verified successfully."
            reason_codes.append("ALL_CHECKS_PASSED")

        actions_key = rule_decision.value.lower()
        actions = rule.actions_triggered.get(f"on_{actions_key}", [])

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_version=rule.rule_version,
            subject_id=subject_id,
            subject_type=subject_type,
            episode_id=episode_id,
            decision=rule_decision,
            reason=reason,
            structured_reason_codes=reason_codes,
            checks_evaluated=check_evaluations,
            actions_triggered=actions,
        )

    def evaluate_all(
        self,
        subject_id: str,
        subject_type: str,
        subject: Any,
        context: Optional[Dict[str, Any]] = None,
        episode_id: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
        domain: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> Tuple[RuleDecision, List[RuleEvaluationResult]]:
        """
        Select and evaluate all applicable rules.
        Resolves conflicts using strict precedence (§32): BLOCK > WARN > PASS.
        """
        subject_data = subject.model_dump() if isinstance(subject, BaseModel) else (subject if isinstance(subject, dict) else {})
        ctx = context or {}

        rules = self.selector.select_rules(
            contract_type=subject_type,
            lifecycle_state=lifecycle_state or subject_data.get("status"),
            domain=domain or subject_data.get("domain"),
            action_type=action_type or subject_data.get("action_type") or subject_data.get("safety_tier"),
        )

        evaluations: List[RuleEvaluationResult] = []
        overall_decision = RuleDecision.PASS

        for rule in rules:
            res = self.evaluate_rule(
                rule=rule,
                subject_id=subject_id,
                subject_type=subject_type,
                subject_data=subject_data,
                context=ctx,
                episode_id=episode_id,
            )
            evaluations.append(res)
            if res.decision == RuleDecision.BLOCK:
                overall_decision = RuleDecision.BLOCK
            elif res.decision == RuleDecision.WARN and overall_decision != RuleDecision.BLOCK:
                overall_decision = RuleDecision.WARN

        return overall_decision, evaluations
