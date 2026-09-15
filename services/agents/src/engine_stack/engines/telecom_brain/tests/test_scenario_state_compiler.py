"""Tests for Scenario-Specific State Compiler (§26, §27).

Verifies that:
- Different scenarios produce different, scenario-specific state (no cross-contamination)
- Optical scenario does not inherit MTU demo fixture
- Every snapshot carries the correct scenario_id and run_id
"""

import pytest
from engine_stack.engines.telecom_brain.simulator.scenario_state_compiler import (
    ScenarioStateCompiler,
)


@pytest.fixture
def compiler():
    return ScenarioStateCompiler()


class TestCrossScenarioContamination:
    """Two different scenarios must never return identical visual state."""

    def test_two_different_scenarios_do_not_return_identical_visual_state(self, compiler):
        """§26: Selecting SCN-001 then H4-WI-007 must not produce identical visual state."""
        state_a = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-TEST-A",
            status="RUNNING",
            stage_index=2,
        )
        state_b = compiler.compile_state(
            scenario_id="H4-WI-007",
            run_id="RUN-TEST-B",
            status="RUNNING",
            stage_index=2,
        )

        # scenario_id must differ
        assert state_a["scenario_id"] != state_b["scenario_id"]

        # At least one visual field must differ
        visual_fields_differ = False
        for field in ["events", "hypotheses", "topology", "knowledge_gaps", "next_best_actions"]:
            if state_a.get(field) != state_b.get(field):
                visual_fields_differ = True
                break
        assert visual_fields_differ, "Two different scenarios returned identical visual state"

    def test_optical_scenario_does_not_inherit_mtu_demo_fixture(self, compiler):
        """§27: H4-WI-007 (Optical) must not contain MTU-specific content."""
        state = compiler.compile_state(
            scenario_id="H4-WI-007",
            run_id="RUN-TEST-OPTICAL",
            status="RUNNING",
            stage_index=2,
        )

        # No event should reference MTU
        for event in state["events"]:
            assert "MTU" not in event["title"], (
                f"Optical scenario event references MTU: {event['title']}"
            )

        # No hypothesis should reference MTU
        for hyp in state["hypotheses"]:
            assert "MTU" not in hyp["display_name"], (
                f"Optical scenario hypothesis references MTU: {hyp['display_name']}"
            )

        # No gap should reference tr-01 (MTU-specific entity)
        for gap in state["knowledge_gaps"]:
            assert "tr-01" not in gap["label"], (
                f"Optical scenario gap references tr-01: {gap['label']}"
            )

    def test_snapshot_carries_correct_scenario_id(self, compiler):
        """Every snapshot must have scenario_id matching the requested scenario."""
        for sc_id in ["SCN-001", "H4-WI-001", "H4-WI-007", "H4-WI-015"]:
            state = compiler.compile_state(
                scenario_id=sc_id,
                run_id=f"RUN-{sc_id}",
                status="RUNNING",
                stage_index=2,
            )
            assert state["scenario_id"] == sc_id

    def test_snapshot_carries_correct_run_id(self, compiler):
        """Every snapshot must have the run_id passed in."""
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-UNIQUE-12345",
            status="RUNNING",
            stage_index=2,
        )
        assert state["run"]["run_id"] == "RUN-UNIQUE-12345"

    def test_all_scenarios_produce_nonempty_events(self, compiler):
        """Every scenario must produce at least one event."""
        for sc_id in ["SCN-001", "H4-WI-001", "H4-WI-007", "H4-WI-015", "H4-WI-025"]:
            state = compiler.compile_state(
                scenario_id=sc_id,
                run_id=f"RUN-{sc_id}",
                status="RUNNING",
                stage_index=2,
            )
            assert len(state["events"]) > 0, f"{sc_id} produced no events"

    def test_all_scenarios_produce_nonempty_hypotheses(self, compiler):
        """Every scenario must produce at least one hypothesis."""
        for sc_id in ["SCN-001", "H4-WI-001", "H4-WI-007", "H4-WI-015", "H4-WI-025"]:
            state = compiler.compile_state(
                scenario_id=sc_id,
                run_id=f"RUN-{sc_id}",
                status="RUNNING",
                stage_index=2,
            )
            assert len(state["hypotheses"]) > 0, f"{sc_id} produced no hypotheses"

    def test_trigger_stage_has_no_ranked_hypothesis(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-TRIGGER-001",
            status="RUNNING",
            stage_index=0,
        )
        assert state["current_stage"] == "TRIGGER"
        assert not any(h.get("rank") == 1 for h in state["hypotheses"])
        assert not any(node.get("state") == "ROOT_CANDIDATE" for domain in state["topology"]["domains"] for node in domain["entities"])

    def test_hypothesis_testing_enables_ranking(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-TESTING-001",
            status="RUNNING",
            stage_index=4,
        )
        assert state["current_stage"] == "HYPOTHESIS_TESTING"
        assert any(h.get("rank") == 1 for h in state["hypotheses"])
        assert state["hypotheses"][0]["confidence"] > 0

    def test_knowledge_gap_not_visible_before_detected(self, compiler):
        early_state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-EARLY-001",
            status="RUNNING",
            stage_index=2,
        )
        assert early_state["current_stage"] == "CORRELATION"
        assert early_state["knowledge_gaps"] == []

    def test_recommendation_not_visible_before_action_stage(self, compiler):
        mid_state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-MID-001",
            status="RUNNING",
            stage_index=5,
        )
        assert mid_state["current_stage"] == "KNOWLEDGE_GAP_CHECK"
        assert mid_state["next_best_actions"] == []

    def test_reasoning_events_are_stage_aware(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-EVENTS-001",
            status="RUNNING",
            stage_index=3,
        )
        assert state["current_stage"] == "HYPOTHESIS_GENERATION"
        assert all("stage" in ev for ev in state["events"])
        assert all(ev["stage"] in {"TRIGGER", "SIGNAL_FLOOD", "CORRELATION", "HYPOTHESIS_GENERATION"} for ev in state["events"])

    def test_stage_zero_floods_the_unified_event_stream(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-FLOOD-001",
            status="RUNNING",
            stage_index=0,
        )
        assert len(state["events"]) >= 5
        assert state["events"][0]["stage"] == "TRIGGER"
        assert state["events"] == state["raw_events"]

    def test_raw_event_queue_is_factual_not_correlation_claims(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-RAW-QUEUE-001",
            status="RUNNING",
            stage_index=0,
            started_at="2026-09-12T10:00:00Z",
        )
        for event in state["raw_events"]:
            assert "correlates with failure" not in event["title"].lower()
            assert "correlation" not in event["title"].lower()

    def test_stage_metadata_uses_runtime_state_not_demo_hardcodes(self, compiler):
        state = compiler.compile_state(
            scenario_id="SCN-001",
            run_id="RUN-STATE-001",
            status="RUNNING",
            stage_index=4,
            started_at="2026-09-12T10:00:00Z",
        )
        stage_labels = [stage["label"] for stage in state["stages"]]
        assert "Trigger" in stage_labels[0]
        assert stage_labels[4] == "HYPOTHESIS_TESTING"
        assert state["reasoning_trace"][0]["timestamp"].startswith("2026-09-12T10:00")
        assert "2026-09-12T10:41" not in state["reasoning_trace"][0]["timestamp"]
