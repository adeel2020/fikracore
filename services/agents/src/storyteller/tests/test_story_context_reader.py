"""Unit tests for StoryContextReader and direct IncidentStory hydration."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from storyteller.knowledge.story_context_reader import StoryContextReader
from storyteller.reasoning.pipeline import build_incident_story


@pytest.fixture
def reader() -> StoryContextReader:
    return StoryContextReader()


def test_story_context_reader_resolves_and_hydrates(reader: StoryContextReader):
    """Test reading SCN-001 story_context.json into IncidentContext and building IncidentStory."""
    # Ensure SCN-001 has story_context.json materialized for testing
    from engine_stack.engines.telecom_brain.simulator.story_compiler import compile_story_context

    base = Path(__file__).parents[2] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "runs"
    scn_runs = list(base.glob("RUN-SCN-001*"))
    assert scn_runs, "Expected RUN-SCN-001 directory"
    run_dir = scn_runs[0]

    story_data = compile_story_context(run_dir, stage_index=7)
    (run_dir / "operational" / "story_context.json").write_text(json.dumps(story_data, indent=2), encoding="utf-8")

    # Read using StoryContextReader
    ctx = reader.read("SCN-001")
    assert ctx is not None
    assert ctx.incident is not None
    assert ctx.incident["slug"] == "incidents/transport/scn-001"
    assert len(ctx.timeline) > 0
    assert len(ctx.hypotheses) == 1
    assert ctx.hypotheses[0].confidence == 0.942

    # Verify building IncidentStory directly preserves the confirmed findings
    story = build_incident_story(ctx)
    assert story.incident_id == "incidents/transport/scn-001"
    assert story.status == "resolved"
    assert story.root_cause is not None
    assert story.root_cause.confidence == 0.942
    assert "Autonomous root cause confirmed" in story.summary


def test_story_context_reader_nonexistent_returns_none(reader: StoryContextReader):
    """Non-existent scenario returns None without crashing."""
    ctx = reader.read("NON-EXISTENT-SCENARIO-999")
    assert ctx is None
