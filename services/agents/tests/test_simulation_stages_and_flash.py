"""Unit test verifying simulation start check, stage-gated disclosure, and live flash narration."""

from __future__ import annotations

import pytest
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.investigation.contracts import StandardPresentationModel


@pytest.fixture
def mock_presentation_model():
    return StandardPresentationModel(
        scenario={"id": "SCN-001", "name": "Transport Degradation"},
        impact={},
        timeline=[],
        topology={"visible_entities": [], "visible_relationships": [], "highlighted_path": []},
        reasoning={"hypotheses": [], "terminal_state": "MODEL_INSUFFICIENT", "knowledge_gaps": []},
        next_best_evidence=[],
        candidate_knowledge=[],
        validation={"state": "PENDING"},
        presentation={"active_mode": "INVESTIGATION", "current_step": 1},
    )


def test_simulation_unstarted_does_not_leak_details(mock_presentation_model):
    bridge = ZakiBridge()
    context = bridge.build_context(mock_presentation_model)
    ui_context = {
        "simulation_status": "READY",
        "events_count": 0,
        "response_level": "engineer",
        "simulation_state": {
            "status": "READY",
            "events": [],
            "scenario": {"id": "SCN-001", "display_name": "Transport Degradation"},
        },
    }

    ans = bridge.answer_query("About simulation Can you tell me about it", context, ui_context)
    resp_text = ans.get("response", "")
    spoken = ans.get("copilot", {}).get("message", "")

    # Must explicitly state simulation has not started yet
    assert "not been started yet" in resp_text.lower() or "not started yet" in resp_text.lower()
    # Must NOT leak buffer saturation or 94.2% confidence before simulation starts!
    assert "buffer saturation" not in resp_text.lower()
    assert "94.2%" not in resp_text
    assert "Start Simulation" in resp_text
    assert "not been started yet" in spoken.lower() or "not started yet" in spoken.lower()


def test_simulation_running_trigger_stage(mock_presentation_model):
    bridge = ZakiBridge()
    context = bridge.build_context(mock_presentation_model)
    ui_context = {
        "simulation_status": "RUNNING",
        "stage_index": 0,
        "events_count": 2,
        "response_level": "engineer",
        "simulation_state": {
            "status": "RUNNING",
            "events": [{"event_id": "EV-1", "title": "PE router degraded"}],
            "story_context": {
                "stage_index": 0,
                "flash_history": [
                    {
                        "time": "08:01:02Z",
                        "phase": "Trigger",
                        "spoken": "Alert: P1 anomaly detected on transport PE-RTR-21. Correlating initial observations.",
                    }
                ],
            },
        },
    }

    ans = bridge.answer_query("About simulation Can you tell me about it", context, ui_context)
    resp_text = ans.get("response", "")
    spoken = ans.get("copilot", {}).get("message", "")

    # Live flash narration must be present
    assert "Live Flash Narration" in resp_text
    assert "08:01:02Z" in resp_text
    assert "Alert: P1 anomaly detected on transport PE-RTR-21" in resp_text
    assert spoken == "Alert: P1 anomaly detected on transport PE-RTR-21. Correlating initial observations."
    # At stage 0, root cause must be unconfirmed
    assert "unconfirmed" in resp_text.lower()


def test_simulation_running_propagation_stage(mock_presentation_model):
    bridge = ZakiBridge()
    context = bridge.build_context(mock_presentation_model)
    ui_context = {
        "simulation_status": "RUNNING",
        "stage_index": 2,
        "events_count": 4,
        "response_level": "operator",
        "simulation_state": {
            "status": "RUNNING",
            "events": [{"event_id": "EV-1"}, {"event_id": "EV-2"}],
            "story_context": {
                "stage_index": 2,
                "flash_history": [
                    {
                        "time": "08:01:02Z",
                        "phase": "Trigger",
                        "spoken": "Alert: P1 anomaly detected on transport PE-RTR-21. Correlating initial observations.",
                    },
                    {
                        "time": "08:02:24Z",
                        "phase": "Propagation",
                        "spoken": "Update: Degradation has cascaded to User Plane Function 003. Mobile data sessions are dropping.",
                    },
                ],
            },
        },
    }

    ans = bridge.answer_query("About simulation Can you tell me about it", context, ui_context)
    resp_text = ans.get("response", "")
    spoken = ans.get("copilot", {}).get("message", "")

    assert "Update: Degradation has cascaded to User Plane Function 003" in resp_text
    assert spoken == "Update: Degradation has cascaded to User Plane Function 003. Mobile data sessions are dropping."


def test_simulation_running_rca_and_recovery_stages(mock_presentation_model):
    bridge = ZakiBridge()
    context = bridge.build_context(mock_presentation_model)
    ui_context_rca = {
        "simulation_status": "RUNNING",
        "stage_index": 4,
        "events_count": 6,
        "response_level": "executive",
        "simulation_state": {
            "status": "RUNNING",
            "events": [{"event_id": "EV-1"}],
            "story_context": {
                "stage_index": 4,
                "flash_history": [
                    {
                        "time": "08:01:02Z",
                        "phase": "Trigger",
                        "spoken": "Alert: P1 anomaly detected on transport PE-RTR-21. Correlating initial observations.",
                    },
                    {
                        "time": "08:02:24Z",
                        "phase": "Propagation",
                        "spoken": "Update: Degradation has cascaded to User Plane Function 003. Mobile data sessions are dropping.",
                    },
                    {
                        "time": "08:02:54Z",
                        "phase": "RCA Confirmed",
                        "spoken": "Root cause confirmed: PE-RTR-21 line card buffer saturation with 94.2% confidence. Playbook remediation dispatched.",
                    },
                ],
            },
        },
    }

    ans_rca = bridge.answer_query("About simulation Can you tell me about it", context, ui_context_rca)
    spoken_rca = ans_rca.get("copilot", {}).get("message", "")
    assert spoken_rca == "Root cause confirmed: PE-RTR-21 line card buffer saturation with 94.2% confidence. Playbook remediation dispatched."
