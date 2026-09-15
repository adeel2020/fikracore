from pathlib import Path
import asyncio

from assistant.mark import JARVIS, PowerUp
from jarvis.superpowers.telecom_brain import TelecomBrainEngine, normalize_query


def test_jarvis_routes_solution_questions_to_telecom_brain():
    jarvis = JARVIS()

    assert jarvis._route_query("Where does FCAPS fit in the telecom brain?", None) == PowerUp.TELECOM_BRAIN
    assert jarvis._route_query("Tell the story for incidents/mobile-core/lte-attach-123", None) == PowerUp.TELECOM_BRAIN
    assert jarvis._route_query("Show all incidents", None) == PowerUp.TELECOM_BRAIN


def test_jarvis_handles_voice_check_without_telecom_lookup():
    jarvis = JARVIS()

    answer = asyncio.run(jarvis.process("Hello Mark, can you listen to me?"))

    assert "I can hear you" in answer
    assert "telecom brain" in answer


def test_jarvis_handles_general_discussion_without_scope_refusal():
    jarvis = JARVIS()

    answer = asyncio.run(jarvis.process("What do you think about planning a focused morning?"))

    assert "outside my operational scope" not in answer
    assert "I am with you" in answer


def test_jarvis_keeps_operational_questions_on_telecom_path():
    jarvis = JARVIS()

    assert jarvis._needs_operational_context("why did volte cssr drop?", None) is True
    assert jarvis._needs_operational_context("tell me a simple joke", None) is False


class FakeTelecomPower:
    async def process(self, query, session_id=None, context=None):
        self.last_spoken_reply = "Spoken executive summary."
        return "# Full technical incident story\n\n| KPI | Value |"


def test_jarvis_keeps_full_reply_and_spoken_reply_separate():
    jarvis = JARVIS()
    jarvis._superpowers[PowerUp.TELECOM_BRAIN] = FakeTelecomPower()

    answer = asyncio.run(jarvis.process("Tell the incident story for incidents/mobile-core/test-1"))

    assert answer.startswith("# Full technical incident story")
    assert jarvis.last_reply == answer
    assert jarvis.last_spoken_reply == "Spoken executive summary."


def test_telecom_brain_answers_from_solution_docs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "telecom-brain-cognitive-operations-architecture.md").write_text(
        "# Architecture\n\n"
        "## FCAPS As The Learning Lens\n\n"
        "FCAPS is used as a cross-cutting learning lens for evidence, incidents, "
        "learning notes, and assets.\n",
        encoding="utf-8",
    )

    engine = TelecomBrainEngine(config=None, repo_root=tmp_path)
    answer = engine._answer_from_docs("How is FCAPS used as a learning lens?")

    assert "Technical Architecture Context" in answer
    assert "FCAPS As The Learning Lens" in answer
    assert "cross-cutting learning lens" in answer


def test_voice_misheard_network_inventory_is_normalized():
    query = normalize_query("I would like to Know about the networking event three")

    assert "network inventory" in query.lower()


def test_network_inventory_uses_domain_summary_not_docs(tmp_path):
    fixture = tmp_path / "services/agents/src/correlation/fixtures/grafana-lgtm"
    fixture.mkdir(parents=True)
    (fixture / "logical_topology.json").write_text(
        '{"services":{"lte-attach":["ran.enodeb","mobile-core.lte.mme","mobile-core.lte.hss"]},'
        '"intents":{"4g_attach_sr":"lte-attach"}}',
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "telecom-brain-cognitive-operations-architecture.md").write_text(
        "# Architecture\n\nThis document should not be used for inventory answers.\n",
        encoding="utf-8",
    )

    engine = TelecomBrainEngine(config=None, repo_root=tmp_path)
    answer = asyncio.run(engine.process("I would like to know about the network inventory"))

    assert "Network Inventory Summary" in answer
    assert "lte-attach" in answer
    assert "Technical Architecture Context" not in answer
    assert "runbook" not in (engine.last_spoken_reply or "").lower()


def test_5g_core_uses_domain_summary_not_docs(tmp_path):
    fixture = tmp_path / "services/agents/src/correlation/fixtures/grafana-lgtm"
    fixture.mkdir(parents=True)
    (fixture / "logical_topology.json").write_text(
        '{"services":{"pdu-session":["ran.gnodeb","mobile-core.5gc.amf","mobile-core.5gc.smf","mobile-core.5gc.upf"]},'
        '"intents":{"data_session_establishment":"pdu-session"}}',
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "telecom-brain-cognitive-operations-architecture.md").write_text(
        "# Architecture\n\nThis document should not be used for core domain answers.\n",
        encoding="utf-8",
    )

    engine = TelecomBrainEngine(config=None, repo_root=tmp_path)
    answer = asyncio.run(engine.process("I want to know about the 5G core"))

    assert "5G Core Domain Summary" in answer
    assert "mobile-core.5gc.amf" in answer
    assert "Technical Architecture Context" not in answer


def test_telecom_brain_uses_repo_root_discovery():
    root = TelecomBrainEngine(config=None)._discover_repo_root()

    assert isinstance(root, Path)


def test_mark_presentation_is_attached_to_each_turn_and_cleared_for_general_chat():
    from assistant.mark.response import MarkResponse

    class VisualPower:
        async def process(self, query, session_id=None, context=None):
            await asyncio.sleep(0)
            return MarkResponse(query, spoken_reply=f"Brief {session_id}", presentation={
                "narrative": {"incident_id": session_id},
                "visual_explanation": {"widgets": [{"id": session_id}]},
            })

    async def run():
        jarvis = JARVIS()
        jarvis._superpowers[PowerUp.TELECOM_BRAIN] = VisualPower()
        a, b = await asyncio.gather(
            jarvis.process("Tell incident A story", session_id="A"),
            jarvis.process("Tell incident B story", session_id="B"),
        )
        assert a.presentation["narrative"]["incident_id"] == "A"
        assert b.presentation["narrative"]["incident_id"] == "B"
        assert a.spoken_reply == "Brief A"
        general = await jarvis.process("hello")
        assert general.presentation == {}
        assert general.spoken_reply is None

    asyncio.run(run())


def test_http_response_preserves_turn_presentation(monkeypatch):
    from assistant.mark.response import MarkResponse
    from jarvis import router

    class FakeMark:
        async def process(self, message, session_id):
            return MarkResponse("Technical story", spoken_reply="Executive brief", presentation={
                "narrative": {"incident_id": "incident-a"},
                "visual_explanation": {"widgets": [{"id": "impact"}]},
            })

    async def get_mark():
        return FakeMark()

    monkeypatch.setattr(router, "_get_jarvis", get_mark)
    response = asyncio.run(router.process(router.JarvisRequest(message="tell incident story")))
    assert response.spoken_reply == "Executive brief"
    assert response.visual_explanation["widgets"][0]["id"] == "impact"


def test_jarvis_lists_intents_when_requested():
    jarvis = JARVIS()

    for phrase in ["list the intents", "what are the intents", "show intents", "explain intents"]:
        answer = asyncio.run(jarvis.process(phrase))
        assert "Operational Service Intents" in answer
        assert "ue_registration" in answer
        assert "lte_attach_sr" in answer
        assert "volte_cssr" in answer
        assert "sgi_throughput" in answer
        assert "data_session_establishment" in answer
        assert "ims_registration" in answer
        assert "I am with you. We can discuss that normally" not in answer
