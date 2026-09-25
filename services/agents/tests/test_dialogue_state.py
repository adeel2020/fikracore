import pytest
from engine_stack.engines.telecom_brain.presentation.dialogue_state import (
    DialogueStateManager,
    dialogue_state_manager,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.investigation.contracts import ZakiContextContract


def test_dialogue_state_manager_turn_memory():
    mgr = DialogueStateManager()
    session = mgr.get_or_create("test-sess-1", scenario_id="SCN-001", run_id="RUN-001", stage="CORRELATING")
    assert session.session_id == "test-sess-1"

    mgr.record_user_turn("test-sess-1", "I can investigate the UPF node", detected_entity="UPF-01")
    assert session.focused_entity == "UPF-01"
    assert len(session.turns) == 1
    assert session.turns[0].role == "user"

    mgr.record_assistant_turn("test-sess-1", "Understood. Correlating UPF-01 alarms.", focused_entity="UPF-01")
    assert len(session.turns) == 2
    assert session.turns[1].role == "assistant"

    # Pronoun resolution
    resolved = mgr.resolve_anaphora_entity("What was its drop rate?", session)
    assert resolved == "UPF-01"


def test_zaki_bridge_conversational_response():
    bridge = ZakiBridge()
    context = ZakiContextContract(
        active_scenario="SCN-001",
        active_stage="CORRELATING",
        active_presentation_mode="INVESTIGATION",
        current_presentation_step=1,
        visible_evidence=[],
        visible_topology={"domains": [{"name": "Mobile Core", "entities": [{"id": "UPF-01", "display_name": "UPF-01"}]}]},
        current_hypotheses=[],
        current_terminal_state="PARTIALLY_EXPLAINED",
        knowledge_gap_state={"gaps": [], "residuals": [], "boundary": {}},
        next_best_evidence=[{"display_name": "UPF Drop Probe"}],
        candidate_knowledge=[],
        validation_status="PENDING",
        human_readable_display_names={},
        learning_state={},
        resilience_state={},
    )

    # Conversational offer "I can"
    ans = bridge.answer_query("I can look into the UPF", context, ui_context={"run_id": "RUN-001", "simulation_stage": "CORRELATING"})
    resp_text = ans.get("response", "")

    # Must NOT contain the robotic IVR prefix
    assert "Investigation focus: operational explanation and telemetry correlation" not in resp_text
    assert "Appreciate the support" in resp_text or "Understood" in resp_text
    assert "UPF" in resp_text
