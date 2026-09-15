"""Phase 2 integration tests against the real AMF incident (gbrain).

These exercise the end-to-end deterministic pipeline over a real context and
are skipped when gbrain is unavailable or locked.
"""

from __future__ import annotations

import pytest

from storyteller.knowledge.provenance import (
    CONFIRMED_ROOT_CAUSE,
    CORRELATION,
    EVIDENCE,
    HYPOTHESIS,
    OBSERVATION,
)
from storyteller.reasoning.pipeline import build_incident_story, build_story_response


@pytest.fixture(scope="session")
def amf_context(knowledge):
    """Full AMF incident context, fetched once per session (gbrain subprocess
    calls are slow; every test reuses the same context)."""
    if knowledge is None:
        pytest.skip("gbrain unavailable")
    return knowledge.get_incident_context("mobile-core/incidents/amf-overload-2026-08-09")


def test_amf_context_pipeline(amf_context):
    ctx = amf_context
    assert ctx.incident is not None
    story = build_incident_story(ctx)
    assert story.incident_id == "mobile-core/incidents/amf-overload-2026-08-09"
    assert story.severity == "SEV-2"
    assert story.status == "resolved"
    # AMF context facts verified in Phase 1.
    assert len(story.kpi_events) == 1
    assert len(story.symptoms) == 1
    assert len(story.hypotheses) == 1
    assert len(story.hypotheses[0].evidence) == 2
    assert len(story.remediations) == 1
    assert len(story.recovery_events) == 1


def test_amf_causal_chain(amf_context):
    story = build_incident_story(amf_context)
    chain = story.causal_chain
    assert chain is not None
    labels = [s.claim_type for s in chain.steps]
    assert labels[0] == CORRELATION  # RSR critical breach
    assert OBSERVATION in labels      # symptom
    assert HYPOTHESIS in labels       # AMF-01 CPU saturation
    assert labels.count(EVIDENCE) == 2
    assert labels[-2] == CONFIRMED_ROOT_CAUSE
    assert story.root_cause is not None


def test_amf_hypothesis_confirmed(amf_context):
    story = build_incident_story(amf_context)
    top = story.hypotheses[0]
    assert top.status == "confirmed"
    assert top.score >= 0.9
    assert top.hypothesis.extra.get("status") == "confirmed"


def test_amf_provenance_preserved(amf_context):
    story = build_incident_story(amf_context)
    for ev in story.hypotheses[0].evidence:
        assert ev.extra.get("hypothesis_slug")
        assert ev.relationship == "supported-by"
    assert story.kpi_events[0].extra["value"] == 94.7
    assert story.recovery_events[0].relationship == "verified-by"


def test_amf_response_deterministic_without_llm(amf_context, monkeypatch):
    monkeypatch.delenv("STORYTELLER_MODEL", raising=False)
    resp = build_story_response(amf_context)
    assert resp.synthesized is False
    assert resp.narrative == ""
    assert resp.story.root_cause is not None

