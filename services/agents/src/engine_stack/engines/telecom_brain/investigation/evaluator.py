"""Examiner-only baseline comparison. The investigator never imports this module."""

from .contracts import InvestigationResult, Terminal


def compare(result: InvestigationResult, expected_roots: list[str], unknown_correct: bool = False) -> dict:
    evidence = result.metadata["evidence"]
    severe = [event for event in evidence if event["evidence_type"] == "alarms" and
              event["severity"].upper() in {"CRITICAL", "MAJOR", "SEV-1", "SEV-2"}]
    earliest = min(severe, key=lambda event: (event["event_time"], event["evidence_id"]), default=None)
    baseline_roots = [earliest["canonical_entity"]] if earliest else []
    ranked = [h for h in result.ranked_hypotheses if h.status.value != "REJECTED"]
    predicted = {entity for h in ranked[:3] for entity in h.root_entities}
    expected = set(expected_roots)
    falsified = [h for h in result.ranked_hypotheses if h.status.value == "REJECTED"]
    wrong = [h for h in result.ranked_hypotheses if not set(h.root_entities).intersection(expected)]
    cited = {event["evidence_id"] for event in evidence}
    valid_provenance = sum(bool(h.supporting_evidence) and set(h.supporting_evidence).issubset(cited) for h in ranked)
    return {
        "run_id": result.run_id, "scenario_id": result.scenario_id,
        "baseline": "earliest severe alarm", "baseline_root_entities": baseline_roots,
        "baseline_correct": set(baseline_roots) == expected if not unknown_correct else not baseline_roots,
        "root_cause_top_3_accuracy": None if unknown_correct else int(bool(expected) and expected.issubset(predicted)),
        "method_b_correct": result.terminal_state != Terminal.EXPLAINED if unknown_correct else bool(
            ranked and set(ranked[0].root_entities) == expected and result.terminal_state == Terminal.EXPLAINED),
        "wrong_hypotheses_correctly_falsified": sum(not set(h.root_entities).intersection(expected) for h in falsified),
        "wrong_hypotheses_total": len(wrong),
        "evidence_requests_before_terminal_decision": len(result.next_best_evidence),
        "steps_to_first_useful_hypothesis": result.diagnostics["steps_to_first_useful_hypothesis"],
        "time_seconds": result.diagnostics["investigation_duration_seconds"],
        "forced_rca_when_unknown_correct": int(unknown_correct and result.terminal_state == Terminal.EXPLAINED),
        "explanation_provenance_quality": valid_provenance / max(1, len(ranked)),
        "terminal_state": result.terminal_state.value, "explanation_coverage": result.explanation_coverage,
        "unexplained_residual": len(result.unexplained_observations),
    }
