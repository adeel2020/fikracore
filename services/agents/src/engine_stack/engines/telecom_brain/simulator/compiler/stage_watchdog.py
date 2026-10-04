from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json

def build_stage_watchdog(
    stage_index: int,
    started_at: str = "",
    status: str = "RUNNING",
    executed_actions: Optional[list[str]] = None,
    tested_hypotheses: Optional[list[str]] = None,
    evidence_count: int = 0,
 *, _parse_runtime_timestamp: Callable, _resolve_stage_name: Callable) -> dict[str, Any]:
    """Expose why the current stage is waiting or ready to move."""
    executed_actions = executed_actions or []
    tested_hypotheses = tested_hypotheses or []
    stage_name = _resolve_stage_name(stage_index)
    next_stage = _resolve_stage_name(stage_index + 1) if stage_index < 7 else None
    base_dt = _parse_runtime_timestamp(started_at)
    entered_at = base_dt + timedelta(seconds=stage_index * 30)
    now = datetime.now(timezone.utc)
    elapsed_ms = max(0, int((now - entered_at).total_seconds() * 1000))
    next_best_evidence_completed = any(act in executed_actions for act in ("NBA-001", "nba-1", "nba-001"))
    hypothesis_tested = "HYP-001" in tested_hypotheses
    hitl_validated = any(act in executed_actions for act in ("HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE", "hitl-001", "val-001"))
    act_completed = any(act in executed_actions for act in ("ACT-001", "REMEDIATE-001", "NBA-REMEDIATE", "act-001"))

    trigger_blocked = evidence_count < 1
    flood_blocked = evidence_count < 3
    correlation_blocked = evidence_count < 3

    conditions = {
        "TRIGGER": (
            "valid_observation_count >= 1",
            {"valid_observation_count": evidence_count},
            "Awaiting initial trigger observation telemetry" if trigger_blocked else None,
        ),
        "SIGNAL_FLOOD": (
            "minimum_evidence_count >= 3",
            {"minimum_evidence_count": evidence_count},
            f"Awaiting minimum evidence flood (current: {evidence_count}, required: 3)" if flood_blocked else None,
        ),
        "CORRELATION": (
            "event_groups_created == true",
            {"event_groups_created": not correlation_blocked},
            f"Cannot correlate with insufficient evidence ({evidence_count} items admitted)" if correlation_blocked else None,
        ),
        "HYPOTHESIS_GENERATION": (
            "candidate_explanations >= 1",
            {"candidate_explanations": 1 if not flood_blocked else 0},
            "Cannot generate hypotheses without correlated evidence" if flood_blocked else None,
        ),
        "HYPOTHESIS_TESTING": (
            "leading_candidate_state in terminal_states",
            {"leading_candidate_state": "NEEDS_MORE_EVIDENCE" if not hypothesis_tested else "SUPPORTED"},
            None,
        ),
        "KNOWLEDGE_GAP_CHECK": (
            "next_best_evidence_completed == true",
            {"next_best_evidence_completed": next_best_evidence_completed},
            None if next_best_evidence_completed else "Required next-best evidence has not completed",
        ),
        "LEARNING_VALIDATION": (
            "hitl_validated == true",
            {"hitl_validated": hitl_validated},
            None if hitl_validated else "Awaiting Human-in-the-Loop (HITL) SME Validation approval",
        ),
        "ACTION": (
            "remediation_completed == true",
            {"remediation_completed": act_completed},
            None if act_completed else "Awaiting execution of recommended remediation playbook (ACT-001)",
        ),
    }
    exit_condition, current_values, blocking_reason = conditions.get(stage_name, conditions["TRIGGER"])
    waiting_for = None
    if stage_name == "TRIGGER" and trigger_blocked:
        waiting_for = "Trigger event observation"
    elif stage_name == "SIGNAL_FLOOD" and flood_blocked:
        waiting_for = "Multi-domain operational telemetry flood"
    elif stage_name == "CORRELATION" and correlation_blocked:
        waiting_for = "Admitted operational evidence stream"
    elif stage_name == "HYPOTHESIS_GENERATION" and flood_blocked:
        waiting_for = "Correlated evidence"
    elif stage_name == "KNOWLEDGE_GAP_CHECK" and not next_best_evidence_completed:
        waiting_for = "Backup-path telemetry"
    elif stage_name == "LEARNING_VALIDATION" and not hitl_validated:
        waiting_for = "HITL SME validation signoff"
    elif stage_name == "ACTION" and not act_completed:
        waiting_for = "Remediation playbook execution"

    if status == "PAUSED":
        stage_status = "PAUSED"
        blocking_reason = "Simulation is paused"
    elif blocking_reason:
        stage_status = "BLOCKED"
    else:
        stage_status = "READY_TO_ADVANCE" if next_stage else "COMPLETE"

    is_satisfied = not bool(blocking_reason) and (status != "PAUSED")
    exit_conditions_detail = [
        {
            "condition_id": f"EC-{stage_name[:3]}-01",
            "display_name": exit_condition,
            "satisfied": is_satisfied,
            "expected": "true" if "==" in exit_condition else ">= threshold",
            "actual": "true" if is_satisfied else "false",
            "reason": blocking_reason if not is_satisfied else "Condition satisfied",
        }
    ]
    return {
        "current_stage": stage_name,
        "stage_status": stage_status,
        "entered_at": entered_at.isoformat().replace("+00:00", "Z"),
        "elapsed_ms": elapsed_ms,
        "exit_conditions": [exit_condition],
        "exit_conditions_detail": exit_conditions_detail,
        "exit_condition_state": current_values,
        "next_stage": next_stage,
        "blocking_reason": blocking_reason,
        "waiting_for": waiting_for,
    }



def disclosure_policy_for_stage(stage_name: str) -> dict[str, Any]:
    policy = {
        "TRIGGER": {
            "observations": True,
            "correlations": False,
            "ranked_hypotheses": False,
            "root_candidate": False,
            "confirmed_path": False,
            "knowledge_gaps": False,
            "recommendations": False,
        },
        "SIGNAL_FLOOD": {
            "observations": True,
            "correlations": False,
            "ranked_hypotheses": False,
            "root_candidate": False,
            "confirmed_path": False,
            "knowledge_gaps": False,
            "recommendations": False,
        },
        "CORRELATION": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": False,
            "root_candidate": False,
            "confirmed_path": False,
            "knowledge_gaps": False,
            "recommendations": False,
        },
        "HYPOTHESIS_GENERATION": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": False,
            "root_candidate": False,
            "confirmed_path": False,
            "knowledge_gaps": False,
            "recommendations": False,
        },
        "HYPOTHESIS_TESTING": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": True,
            "root_candidate": True,
            "confirmed_path": False,
            "knowledge_gaps": False,
            "recommendations": False,
        },
        "KNOWLEDGE_GAP_CHECK": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": True,
            "root_candidate": True,
            "confirmed_path": False,
            "knowledge_gaps": True,
            "recommendations": False,
        },
        "LEARNING_VALIDATION": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": True,
            "root_candidate": True,
            "confirmed_path": False,
            "knowledge_gaps": True,
            "recommendations": False,
        },
        "ACTION": {
            "observations": True,
            "correlations": True,
            "ranked_hypotheses": True,
            "root_candidate": True,
            "confirmed_path": True,
            "knowledge_gaps": True,
            "recommendations": True,
        },
    }
    values = policy.get(stage_name, policy["TRIGGER"])
    values["allowed_disclosures"] = [
        key for key, enabled in values.items() if key != "allowed_disclosures" and enabled
    ]
    return values



def compute_stage_values(stage_index: int, is_confirmed: bool) -> dict[str, Any]:
    """Compute stage-dependent confidence, phase, and impact values."""
    if is_confirmed:
        return {
            "confidence": 94.2,
            "delta": "+12%",
            "lifecycle": "CONFIRMED",
            "zaki_phase": "RECOMMENDATION_READY",
            "zaki_thought": "Root cause confirmed. Remediation path identified.",
            "throughput_pct": -72,
            "users_affected": 24000,
            "regions_affected": 3,
        }
    elif stage_index >= 3:
        return {
            "confidence": 88.5,
            "delta": "+6%",
            "lifecycle": "TESTING",
            "zaki_phase": "REASONING",
            "zaki_thought": "Testing causal hypothesis against operational evidence.",
            "throughput_pct": -65,
            "users_affected": 20000,
            "regions_affected": 3,
        }
    elif stage_index == 2:
        return {
            "confidence": 82.0,
            "delta": "+4%",
            "lifecycle": "NEEDS_MORE_EVIDENCE",
            "zaki_phase": "EVIDENCE_NEEDED",
            "zaki_thought": "Correlating signals across domains. Next-best evidence required.",
            "throughput_pct": -55,
            "users_affected": 18000,
            "regions_affected": 2,
        }
    elif stage_index == 1:
        return {
            "confidence": 76.5,
            "delta": "+2%",
            "lifecycle": "SUPPORTED",
            "zaki_phase": "REASONING",
            "zaki_thought": "Telemetry signals ingested. Forming candidate hypotheses.",
            "throughput_pct": -40,
            "users_affected": 14000,
            "regions_affected": 2,
        }
    else:
        return {
            "confidence": 0.0,
            "delta": "0%",
            "lifecycle": "OBSERVING",
            "zaki_phase": "OBSERVING",
            "zaki_thought": "Observing the initial incident trigger. No causal or impact claim is justified yet.",
            "throughput_pct": None,
            "users_affected": None,
            "regions_affected": None,
        }



def build_stages(stage_index: int, started_at: str = "") -> list[dict[str, Any]]:
    """Build simulation journey stages from the runtime state machine, not demo constants."""
    stage_sequence = [
        {"index": 0, "key": "trigger", "label": "Trigger", "summary": "Incident detected"},
        {"index": 1, "key": "signals", "label": "SIGNAL_FLOOD", "summary": "Events ingested"},
        {"index": 2, "key": "correlation", "label": "CORRELATION", "summary": "Linking across domains"},
        {"index": 3, "key": "hypothesis_generation", "label": "HYPOTHESIS_GENERATION", "summary": "Evaluating root causes"},
        {"index": 4, "key": "hypothesis_testing", "label": "HYPOTHESIS_TESTING", "summary": "Testing the leading hypothesis"},
        {"index": 5, "key": "knowledge_gap_check", "label": "KNOWLEDGE_GAP_CHECK", "summary": "Finding missing context"},
        {"index": 6, "key": "learning_validation", "label": "LEARNING_VALIDATION", "summary": "Validating insights"},
        {"index": 7, "key": "action", "label": "ACTION", "summary": "Generate next best action"},
    ]

    for entry in stage_sequence:
        idx = entry["index"]
        if idx < stage_index:
            entry["status"] = "COMPLETED"
        elif idx == stage_index:
            entry["status"] = "ACTIVE"
        else:
            entry["status"] = "PENDING"
    return stage_sequence



def build_frontiers(
    
    scenario_id: str,
    run_id: str,
    trigger_entity: str,
    trigger_display: str,
    knowledge_gaps: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    stage_index: int,
) -> list[dict[str, Any]]:
    if stage_index < 5:
        return []
    gap = knowledge_gaps[0] if knowledge_gaps else {}
    return [{
        "frontier_id": f"FR-{scenario_id}-001",
        "id": f"FR-{scenario_id}-001",
        "type": "MISSING_EVIDENCE",
        "entity_ids": [trigger_entity],
        "hypothesis_ids": [hypotheses[0]["id"]] if hypotheses else [],
        "description": gap.get("label") or f"{trigger_display} health metrics required",
        "severity": "HIGH",
        "resolvable": True,
        "required_evidence": gap.get("label") or f"Detailed {trigger_display} health metrics",
        "scenario_id": scenario_id,
        "run_id": run_id,
    }]



def build_search_space(
    
    events: list[dict[str, Any]],
    evidence_clusters: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
    frontiers: list[dict[str, Any]],
) -> dict[str, Any]:
    ranked = [h for h in hypotheses if h.get("confidence") is not None]
    plausible = [h for h in ranked if h.get("status") != "REJECTED" and float(h.get("confidence") or 0) >= 15]
    root_candidates = [
        h for h in hypotheses
        if h.get("confidence_state") in {"ROOT_CANDIDATE", "CONFIRMED"} or h.get("lifecycle_state") == "CONFIRMED"
    ]
    return {
        "events": len(events),
        "correlated_signals": sum(cluster.get("signal_count", 0) for cluster in evidence_clusters) if evidence_clusters else 0,
        "relevant_entities": len(entities),
        "hypotheses": len(hypotheses),
        "plausible_causes": len(plausible),
        "root_candidates": len(root_candidates),
        "open_frontiers": len(frontiers),
    }



def build_reasoning_focus(
    
    trigger_entity: str,
    hypotheses: list[dict[str, Any]],
    frontiers: list[dict[str, Any]],
    current_stage: str,
    stage_watchdog: dict[str, Any],
    stage_index: int,
) -> dict[str, Any]:
    active_hypothesis = next((h for h in hypotheses if h.get("rank") == 1), hypotheses[0] if hypotheses else {})
    frontier = frontiers[0] if frontiers else {}
    if frontier:
        reason = frontier.get("description", "Resolving current uncertainty frontier")
    elif active_hypothesis:
        reason = active_hypothesis.get("last_delta_reason", "Evaluating candidate evidence")
    else:
        reason = "Waiting for enough evidence to form competing explanations"
    return {
        "entity_id": trigger_entity,
        "hypothesis_id": active_hypothesis.get("id"),
        "test_id": "TEST-NBE-001" if stage_index >= 5 else None,
        "stage": current_stage,
        "reason": reason,
        "frontier_id": frontier.get("frontier_id"),
        "stage_status": stage_watchdog.get("stage_status"),
    }


