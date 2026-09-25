"""Automated unit test suite for Stage-Wise Story Artifact Compiler.

Verifies:
1. Stage-wise progressive disclosure (Stage 0 -> Stage 4 -> Stage 7).
2. Authentic timestamp extraction from operational alarms.jsonl.
3. Zero oracle leakage (ground_truth.yaml is never accessed).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine_stack.engines.telecom_brain.simulator.story_compiler import compile_story_context


@pytest.fixture
def sample_scn001_run_dir() -> Path:
    base = Path(__file__).parent / "runs"
    matches = list(base.glob("RUN-SCN-001*"))
    assert len(matches) > 0, "Expected at least one SCN-001 run directory"
    return matches[0]


def test_stage_0_trigger_has_no_root_cause_spoilers(sample_scn001_run_dir: Path):
    """At Stage 0 (TRIGGER), root_cause must be None with zero causal certainty."""
    story = compile_story_context(sample_scn001_run_dir, stage_index=0)

    assert story["stage_index"] == 0
    assert story["status"] == "investigating"
    assert story["root_cause"] is None, "Stage 0 must not disclose root cause"
    assert len(story["timeline"]) == 1, "Stage 0 should only disclose the initial trigger event"
    assert "Autonomous correlation has been initiated" in story["executive_summary"]
    # Verify authentic timestamps from alarms.jsonl
    assert story["timeline"][0]["time"].startswith("2026-09-10T08:01:02")


def test_stage_2_correlation_remains_unconfirmed(sample_scn001_run_dir: Path):
    """At Stage 2 (CORRELATION), multiple alarms exist but root cause remains unconfirmed."""
    story = compile_story_context(sample_scn001_run_dir, stage_index=2)

    assert story["stage_index"] == 2
    assert story["status"] == "correlating"
    assert story["root_cause"] is None, "Stage 2 must not confirm root cause prematurely"
    assert len(story["timeline"]) >= 2
    assert any(ev["event"] == "KPI_DEGRADATION" for ev in story["timeline"])


def test_stage_4_hypothesis_testing_shows_leading_candidate(sample_scn001_run_dir: Path):
    """At Stage 4 (HYPOTHESIS_TESTING), leading hypothesis is disclosed as an unconfirmed candidate."""
    mock_run_state = {
        "scenario_id": "SCN-001",
        "run_id": "RUN-TEST-001",
        "hypotheses": [
            {
                "entity_id": "IP:PE:RTR-21",
                "summary": "Line card ingress buffer saturation",
            }
        ],
        "topology": {
            "causal_path": ["IP:PE:RTR-21", "IP:VRF:N3-01", "SA5G:UPF:003"],
        },
    }
    story = compile_story_context(sample_scn001_run_dir, stage_index=4, run_state=mock_run_state)

    assert story["stage_index"] == 4
    assert story["status"] == "testing"
    assert story["root_cause"] is not None
    assert story["root_cause"]["status"] == "LEADING_HYPOTHESIS"
    assert story["root_cause"]["entity"] == "IP:PE:RTR-21"
    assert story["root_cause"]["confidence"] == 0.72


def test_stage_7_resolution_has_confirmed_root_cause_and_recovery(sample_scn001_run_dir: Path):
    """At Stage 7 (ACTION/RECOVERY), root cause is CONFIRMED and recovery MOP is verified."""
    mock_run_state = {
        "scenario_id": "SCN-001",
        "run_id": "RUN-TEST-001",
        "hypotheses": [
            {
                "entity_id": "IP:PE:RTR-21",
                "summary": "Line card ingress buffer saturation",
            }
        ],
        "topology": {
            "causal_path": ["IP:PE:RTR-21", "IP:VRF:N3-01", "SA5G:UPF:003", "CRM:TICKET:001"],
        },
    }
    story = compile_story_context(sample_scn001_run_dir, stage_index=7, run_state=mock_run_state)

    assert story["stage_index"] == 7
    assert story["status"] == "resolved"
    assert story["resolved_at"] is not None
    assert story["root_cause"] is not None
    assert story["root_cause"]["status"] == "CONFIRMED"
    assert story["root_cause"]["confidence"] == 0.942
    assert any(ev["event"] == "RECOVERY_VERIFIED" for ev in story["timeline"])
    assert len(story["causal_chain"]) == 4


def test_zero_oracle_peeking(sample_scn001_run_dir: Path, monkeypatch):
    """Verifies that hidden/ground_truth.yaml is NEVER accessed or read."""
    hidden_file = sample_scn001_run_dir / "hidden" / "ground_truth.yaml"
    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if "ground_truth.yaml" in str(self) or "hidden_reality" in str(self):
            raise AssertionError(f"ILLEGAL ACCESS: Attempted to read ground truth oracle: {self}")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    # Compile across all stages — must never touch ground truth!
    for stage in range(8):
        story = compile_story_context(sample_scn001_run_dir, stage_index=stage)
        assert story is not None
