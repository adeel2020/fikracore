"""Floating Zaki copilot response contract tests."""

from __future__ import annotations

from engine_stack.engines.telecom_brain.investigation.contracts import ZakiContextContract
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge


def _context() -> ZakiContextContract:
    return ZakiContextContract(
        active_scenario="SCN-001",
        active_stage="H2",
        current_terminal_state="MODEL_INSUFFICIENT",
        knowledge_gap_state={
            "boundary": {
                "display_name": "Transport Edge",
            },
            "residuals": ["downstream impact cluster"],
        },
        next_best_evidence=[
            {
                "request_id": "NBA-001",
                "question": "Collect backup path telemetry",
                "priority": 1,
            }
        ],
    )


def test_answer_query_adds_detached_floating_copilot_contract():
    bridge = ZakiBridge()
    response = bridge.answer_query(
        "Why is the model insufficient?",
        _context(),
        ui_context={"workspace": "discover", "response_level": "engineer"},
    )

    assert response["assistant_identity"] == "Mark / Zaki"
    assert response["response"]
    assert response["copilot"]["identity"] == "Zaki"
    assert response["copilot"]["surface"] == "floating_conversation_assistant"
    assert response["copilot"]["placement"] == "floating"
    assert response["copilot"]["ui_attachment"] == "detached"
    assert response["copilot"]["requires_panel_mount"] is False
    assert response["copilot"]["conversation_first"] is True
    assert response["conversation"]["reply"] == response["copilot"]["message"]
    assert "MODEL_INSUFFICIENT" in response["copilot"]["message"] or "model" in response["copilot"]["message"].lower()
    assert response["copilot"]["conversation_starters"]


def test_answer_copilot_query_preserves_legacy_response_fields():
    bridge = ZakiBridge()
    response = bridge.answer_copilot_query("Hello", _context())

    assert response["grounded"] is True
    assert response["truth_blind"] is True
    assert response["candidate_status_safe"] is True
    assert "Zaki" in response["copilot"]["message"]
