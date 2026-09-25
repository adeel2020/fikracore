"""Phase 2 tests: deterministic reasoning layer (story, causal chain, ranking,
provenance, insufficient/conflicting evidence, LLM-disabled story)."""

from __future__ import annotations

import pytest

from storyteller.knowledge.provenance import (
    CONFIRMED_ROOT_CAUSE,
    CORRELATION,
    EVIDENCE,
    FACT,
    HYPOTHESIS,
    OBSERVATION,
)
from storyteller.conversation.intents import render_spoken_answer
from storyteller.reasoning.hypothesis import (
    CONFLICTING,
    CONFIRMED,
    INSUFFICIENT,
    PLAUSIBLE,
    rank_hypotheses,
)
from storyteller.reasoning.pipeline import build_incident_story, build_story_response
from storyteller.reasoning.story import IncidentStory, StoryResponse


class TestStoryConstruction:
    def test_confirmed_story_fields(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)
        assert isinstance(story, IncidentStory)
        assert story.incident_id == ctx_confirmed.incident_id
        assert story.severity == "SEV-2"
        assert story.status == "resolved"
        assert len(story.services) == 1
        assert len(story.network_functions) == 2
        assert len(story.timeline) == 1
        assert len(story.kpis) == 1
        assert len(story.kpi_events) == 1
        assert len(story.symptoms) == 1
        assert len(story.hypotheses) == 1
        assert len(story.remediations) == 1
        assert len(story.recovery_events) == 1
        assert story.generated_by == "deterministic"

    def test_story_preserves_provenance(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)
        evidence_facts = story.hypotheses[0].evidence
        for f in evidence_facts:
            assert f.relationship == "supported-by"
            assert f.extra.get("hypothesis_slug") == "hyp/amf-cpu-sat"
        assert story.recovery_events[0].relationship == "verified-by"
        assert story.kpi_events[0].extra["value"] == 94.7
        assert story.root_cause is not None

    def test_incident_id_unknown_when_missing(self, ctx_insufficient):
        ctx_insufficient.incident = None
        story = build_incident_story(ctx_insufficient)
        assert story.incident_id == "unknown"
        assert story.to_dict()["incident_id"] == "unknown"


class TestHypothesisRanking:
    def test_confirmed_ranked_first(self):
        confirmed = pytest.importorskip("storyteller.knowledge.provenance").fact
        h1 = confirmed("Confirmed root", confidence=0.5,
                       extra={"status": "confirmed", "explains": []}, slug="h/1")
        h2 = confirmed("High conf plausible", confidence=0.95, extra={"explains": []}, slug="h/2")
        ranked = rank_hypotheses([h1, h2], {}, {})
        assert ranked[0].status == CONFIRMED
        assert ranked[1].status == PLAUSIBLE

    def test_no_fabrication_on_missing_fields(self):
        from storyteller.knowledge.provenance import fact
        h = fact("Possible SBC overload", slug="h/sbc")
        ranked = rank_hypotheses([h], {}, {})
        assert ranked[0].status == INSUFFICIENT
        assert ranked[0].score == 0.0
        assert ranked[0].evidence == []

    def test_conflicting_evidence_demotes(self):
        from storyteller.knowledge.provenance import fact
        h = fact("AMF CPU saturation", confidence=0.9, slug="h/amf")
        ev = fact("Test results ruled out CPU saturation", slug="ev/neg",
                  extra={"hypothesis_slug": "h/amf"})
        ranked = rank_hypotheses([h], {"h/amf": [ev]}, {})
        assert ranked[0].status == CONFLICTING

    def test_score_uses_confidence_and_evidence(self):
        from storyteller.knowledge.provenance import fact
        h = fact("Hypothesis A", confidence=0.8, slug="h/a")
        ev = fact("Supports A", slug="ev/a", extra={"hypothesis_slug": "h/a"})
        ranked = rank_hypotheses([h], {"h/a": [ev]}, {})
        assert 0.8 < ranked[0].score <= 1.0


class TestCausalChain:
    def test_confirmed_chain_order_and_labels(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)
        chain = story.causal_chain
        assert chain is not None
        labels = [s.claim_type for s in chain.steps]
        # KPI -> symptom -> hypothesis -> evidence -> evidence -> root cause -> recovery
        assert labels[0] == CORRELATION
        assert OBSERVATION in labels
        assert HYPOTHESIS in labels
        assert labels.count(EVIDENCE) == 2
        assert labels[-2] == CONFIRMED_ROOT_CAUSE
        assert labels[-1] == FACT

    def test_root_cause_only_when_confirmed(self, ctx_plausible):
        story = build_incident_story(ctx_plausible)
        assert story.root_cause is None
        assert story.causal_chain is not None
        labels = [s.claim_type for s in story.causal_chain.steps]
        assert CONFIRMED_ROOT_CAUSE not in labels

    def test_chain_best_effort_on_missing_links(self, ctx_insufficient):
        story = build_incident_story(ctx_insufficient)
        # No KPI event, no symptom, no evidence, no recovery — only hypothesis.
        chain = story.causal_chain
        assert chain is not None
        labels = [s.claim_type for s in chain.steps]
        assert CORRELATION not in labels
        assert OBSERVATION not in labels
        assert labels[0] == HYPOTHESIS
        assert story.root_cause is None


class TestStoryResponse:
    def test_response_without_llm(self, ctx_confirmed, monkeypatch):
        # Force synthesis off (model unset) even if env has one.
        monkeypatch.delenv("STORYTELLER_MODEL", raising=False)
        monkeypatch.delenv("STORYTELLER_BASE_URL", raising=False)
        monkeypatch.delenv("STORYTELLER_API_KEY", raising=False)
        resp = build_story_response(ctx_confirmed)
        assert isinstance(resp, StoryResponse)
        assert resp.story is not None
        assert resp.synthesized is False
        assert resp.narrative == ""
        assert resp.model is None

    def test_response_to_dict_contains_story(self, ctx_confirmed, monkeypatch):
        monkeypatch.delenv("STORYTELLER_MODEL", raising=False)
        d = build_story_response(ctx_confirmed).to_dict()
        assert "story" in d
        assert d["story"]["incident_id"] == ctx_confirmed.incident_id


class TestUnresolvedQuestions:
    def test_confirmed_story_has_questions_about_missing_parts(self, ctx_plausible):
        story = build_incident_story(ctx_plausible)
        assert "root cause is not confirmed" in story.unresolved_questions

    def test_insufficient_story_lists_all_gaps(self, ctx_insufficient):
        story = build_incident_story(ctx_insufficient)
        assert "no remediation recorded" in story.unresolved_questions
        assert "no recovery observed" in story.unresolved_questions
        assert "no similar incidents found to corroborate the story" in story.unresolved_questions

    def test_no_similar_incidents_present(self, ctx_confirmed):
        assert ctx_confirmed.similar_incidents == []


class TestSummary:
    def test_summary_mentions_root_cause_when_confirmed(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)
        assert "root cause" in story.summary

    def test_summary_mentions_leading_hypothesis_when_plausible(self, ctx_plausible):
        story = build_incident_story(ctx_plausible)
        assert "leading hypothesis" in story.summary

    def test_summary_has_severity(self, ctx_confirmed):
        assert "SEV-2" in build_incident_story(ctx_confirmed).summary


class TestSpokenAnswer:
    def test_spoken_story_is_briefing_not_markdown_reader(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)

        spoken = render_spoken_answer("story", story)

        assert story.incident_id not in spoken
        assert "mobile-core/incidents" not in spoken
        assert "**" not in spoken
        assert "# " not in spoken
        assert "SEV-2" not in spoken
        assert "severity 2" in spoken
        assert "Mobile Core" in spoken
        assert "confirmed root cause" in spoken.lower()

    def test_spoken_timeline_avoids_raw_incident_id(self, ctx_confirmed):
        story = build_incident_story(ctx_confirmed)

        spoken = render_spoken_answer("timeline", story)

        assert story.incident_id not in spoken
        assert "timeline event" in spoken
