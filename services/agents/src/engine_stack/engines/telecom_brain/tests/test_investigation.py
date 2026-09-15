"""Scenario and boundary tests use operational fixtures independently of examiner answers."""

import ast
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from engine_stack.engines.telecom_brain.canonicalization import CanonicalResolver
from engine_stack.engines.telecom_brain.investigation import GeneratedRunInput, Investigator
from engine_stack.engines.telecom_brain.investigation.contracts import Evidence, Terminal
from engine_stack.engines.telecom_brain.investigation.evidence import load_evidence, normalize
from engine_stack.engines.telecom_brain.investigation.evaluator import compare
from engine_stack.engines.telecom_brain.investigation.knowledge import (
    CanonicalKnowledge, FrozenTelecomBrainProvider, GbrainTelecomBrainProvider, InMemoryKnowledgeProvider, ProviderError)


def run_input(scenario="S1", level="L1"):
    return GeneratedRunInput(run_id=f"RUN-{scenario}", scenario_id=scenario, difficulty_profile=level, seed=42)


def event(identifier, entity, source, second=0, polarity="abnormal", kind="alarms", service="mobile-data", **kwargs):
    when = datetime(2026, 9, 10, 8, tzinfo=timezone.utc) + timedelta(seconds=second)
    return Evidence(evidence_id=identifier, event_time=when, ingestion_time=when + timedelta(seconds=5),
        domain="transport" if entity == "router" else "ps", entity=entity, canonical_entity=entity,
        source_native_entity=entity, source=source, source_reliability=.95, polarity=polarity,
        evidence_type=kind, service=[service], severity="MAJOR", signal="path-degraded" if polarity == "abnormal" else "healthy", **kwargs)


def provider(gap=False):
    return InMemoryKnowledgeProvider(
        [{"slug": name} for name in ("router", "upf", "service", "noise", "peer")],
        [{"relationship_id": "R1", "source": "upf", "target": "router", "link_type": "depends-on", "state": "CONFIRMED", "confidence": .95}] if not gap else [])


def cross_events():
    return [event("r1", "router", "nms"), event("r2", "router", "probe", 1, kind="metrics"),
            event("u1", "upf", "ems", 10), event("u2", "upf", "pm", 11, kind="kpis")]


def test_s1_simple_fault():
    result = Investigator(provider()).investigate(run_input(), cross_events()[:2])
    assert result.terminal_state == Terminal.EXPLAINED
    assert result.ranked_hypotheses[0].canonical_root_entity == "router"
    assert result.provenance[0]["evidence_ids"] == ["r1", "r2"]


def test_s2_cross_domain_and_baseline():
    result = Investigator(provider()).investigate(run_input("S2"), cross_events())
    assert result.terminal_state == Terminal.EXPLAINED
    assert result.ranked_hypotheses[0].knowledge_relationships_used == ["R1"]
    assert result.causal_event_graph
    assert compare(result, ["router"])["root_cause_top_3_accuracy"] == 1


def test_s3_noise_misleading_change_and_order():
    evidence = cross_events()
    evidence += [event(f"dup-{i}", "upf", "ems", 10) for i in range(80)]
    evidence += [event("change", "noise", "change-system", -30, kind="changes", polarity="context", service="other")]
    evidence += [event("unrelated", "noise", "other-nms", -20, service="other")]
    result = Investigator(provider()).investigate(run_input("S3", "L2"), list(reversed(evidence)))
    assert result.terminal_state == Terminal.EXPLAINED
    assert result.ranked_hypotheses[0].canonical_root_entity == "router"
    assert result.diagnostics["collapsed_evidence_count"] == 6
    assert "unrelated" in result.diagnostics["coincidental_evidence"]
    assert compare(result, ["router"])["baseline_correct"] is False
    second = Investigator(provider()).investigate(run_input("S3", "L2"), evidence)
    assert result.ranked_hypotheses == second.ranked_hypotheses


def test_s4_missing_relationship_never_promoted():
    p = provider(gap=True)
    evidence = cross_events()[:3] + [event("path", "upf", "probe", 12, kind="traces", observed_path=["upf", "router"])]
    result = Investigator(p).investigate(run_input("S4", "L4"), evidence)
    assert result.terminal_state == Terminal.MODEL_INSUFFICIENT
    assert result.discovery_mode
    assert result.candidate_relationships[0].state.value == "CANDIDATE"
    assert p.relationships == []
    assert result.next_best_evidence


def test_s5_unknown_is_successful_abstention():
    result = Investigator(provider()).investigate(run_input("S5", "L5"), cross_events()[:1])
    assert result.terminal_state == Terminal.INSUFFICIENT_EVIDENCE
    assert result.selected_hypothesis_id is None
    assert compare(result, [], True)["forced_rca_when_unknown_correct"] == 0


@pytest.mark.parametrize("level", ["L1", "L2", "L3", "L4", "L5"])
def test_difficulty_is_metadata_not_answer_or_scoring_shortcut(level):
    result = Investigator(provider()).investigate(run_input(level=level), cross_events())
    assert result.terminal_state == Terminal.EXPLAINED
    assert result.metadata["difficulty_profile"] == level


def test_negative_evidence_falsifies_unsupported_branch():
    result = Investigator(provider()).investigate(run_input(), cross_events() + [event("negative", "peer", "probe", polarity="healthy")])
    peer = next(h for h in result.ranked_hypotheses if h.canonical_root_entity == "peer")
    assert peer.status.value == "REJECTED"
    assert peer.failed_assumptions
    assert compare(result, ["router"])["wrong_hypotheses_correctly_falsified"] >= 1


def test_conflicting_evidence_prevents_rca():
    result = Investigator(provider()).investigate(run_input(), cross_events()[:2] + [event("healthy", "router", "independent", polarity="healthy")])
    assert result.terminal_state == Terminal.CONFLICTING_EVIDENCE


def test_multicause_explanation():
    evidence = cross_events()[:2] + [event("n1", "noise", "nms"), event("n2", "noise", "probe", 1)]
    result = Investigator(provider()).investigate(run_input(), evidence)
    assert set(result.ranked_hypotheses[0].root_entities) == {"router", "noise"}
    assert result.terminal_state == Terminal.EXPLAINED


def test_chained_canonical_reads_and_legacy_fallback():
    resolver = CanonicalResolver([{"action": "alias", "legacy_slug": "old", "canonical_slug": "middle"},
                                  {"action": "alias", "legacy_slug": "middle", "canonical_slug": "router"}])
    knowledge = CanonicalKnowledge(provider(), resolver)
    assert knowledge.get_page("old")["slug"] == "router"
    assert knowledge.traverse("old")[0].target == "router"
    legacy = CanonicalKnowledge(InMemoryKnowledgeProvider([{"slug": "old"}], []), resolver)
    assert legacy.get_page("old")["slug"] == "old"
    assert "router" in legacy.failures


def test_native_alias_identity_is_preserved():
    p = InMemoryKnowledgeProvider([{"slug": "router", "aliases": ["VendorRouter"]}], [])
    result = Investigator(p).investigate(run_input(), [event("a", "VendorRouter", "nms"), event("b", "VendorRouter", "probe")])
    assert result.metadata["evidence"][0]["source_native_entity"] == "VendorRouter"
    assert result.metadata["evidence"][0]["canonical_entity"] == "router"


@pytest.mark.parametrize("field", ["ground_truth", "hidden_truth", "root_condition", "noise_manifest"])
def test_hidden_fields_rejected(field):
    with pytest.raises(ValueError, match="Evaluator-only"):
        normalize({field: {}}, "alarms")
    with pytest.raises(ValueError, match="Evaluator-only"):
        InMemoryKnowledgeProvider([{"slug": "x", "frontmatter": {field: "secret"}}], [])


def test_hidden_path_symlink_and_contract_rejected(tmp_path):
    operational = tmp_path / "operational"
    operational.mkdir()
    hidden = tmp_path / "hidden"
    hidden.mkdir()
    truth = hidden / "ground_truth.jsonl"
    truth.write_text('{"root_entity":"secret"}')
    alias = operational / "alarms.jsonl"
    alias.symlink_to(truth)
    run = run_input().model_copy(update={"alarms_path": str(alias)})
    with pytest.raises(ValueError, match="operational directory"):
        load_evidence(run, operational)
    with pytest.raises(ValidationError):
        GeneratedRunInput(**run_input().model_dump(), operational_graph_path="hidden.yaml")


def test_engine_has_no_evaluator_or_world_import():
    import engine_stack.engines.telecom_brain.investigation.investigator as module
    tree = ast.parse(Path(module.__file__).read_text())
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any("evaluator" in name or "simulator" in name for name in imports)


def test_frozen_snapshot_requires_explicit_operational_contract(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"brain": "telecombrain", "snapshot_version": "v1", "pages": [{"slug": "router"}], "relationships": []}))
    p = FrozenTelecomBrainProvider(path)
    assert p.metadata["snapshot_version"] == "v1"
    assert p.metadata["snapshot_sha256"]
    assert p.get_page("router")


def test_provider_outage_is_explicit(monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    with pytest.raises(ProviderError, match="no substitute"):
        GbrainTelecomBrainProvider(token="test-only")


def test_live_contract_arguments_and_not_found(monkeypatch):
    def rpc(self, method, params):
        if method == "tools/list":
            return {"tools": [{"name": name, "inputSchema": {"properties": {"slug": {}}, "required": []}}
                              for name in self.REQUIRED]}
        return {"isError": True, "content": [{"type": "text", "text": '{"error":"page_not_found"}'}]}
    monkeypatch.setattr(GbrainTelecomBrainProvider, "_rpc", rpc)
    p = GbrainTelecomBrainProvider(token="test-only")
    assert p.get_page("absent") is None
    with pytest.raises(ProviderError, match="Arguments"):
        p._call("get_page", {"graph": "invented"})


def test_real_generated_run_operational_ingestion():
    from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run
    root = Path(__file__).parents[1] / "simulator/runs/RUN-SCN-001-L1-SEED-42001"
    run = input_from_run(root)
    evidence, hashes = load_evidence(run, root / "operational")
    assert evidence and len(hashes) == 8
    result = Investigator(InMemoryKnowledgeProvider([], [])).investigate(run, evidence, hashes)
    assert result.terminal_state != Terminal.EXPLAINED
    assert result.knowledge_gaps


def test_all_100_generated_runs_parse_without_truth():
    from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run
    root = Path(__file__).parents[1] / "simulator/runs"
    directories = sorted(path.parent for path in root.glob("*/scenario_manifest.yaml"))
    assert len(directories) == 100
    for directory in directories:
        run = input_from_run(directory)
        observations, hashes = load_evidence(run, directory / "operational")
        assert observations and len(hashes) == 8


def test_healthy_cpu_does_not_falsify_transport_loss():
    healthy = event("cpu", "router", "cpu-monitor", polarity="healthy").model_copy(update={"signal": "CPU normal"})
    result = Investigator(provider()).investigate(run_input(), cross_events() + [healthy])
    assert result.terminal_state == Terminal.EXPLAINED
    assert "cpu" not in result.ranked_hypotheses[0].contradicting_evidence


def test_delayed_upstream_alarm_does_not_make_symptom_root():
    events = cross_events()
    events[0] = events[0].model_copy(update={"event_time": events[2].event_time + timedelta(seconds=3)})
    events[1] = events[1].model_copy(update={"event_time": events[2].event_time + timedelta(seconds=4)})
    result = Investigator(provider()).investigate(run_input(), events)
    assert result.ranked_hypotheses[0].canonical_root_entity == "router"


def test_candidate_decision_is_local_immutable_audit(tmp_path, monkeypatch):
    from engine_stack.engines.telecom_brain.investigation.cli import main
    result = Investigator(provider(True)).investigate(run_input("S4"),
        cross_events() + [event("path", "upf", "probe", kind="traces", observed_path=["upf", "router"])])
    result_path = tmp_path / "result.json"
    result_path.write_text(result.model_dump_json())
    output = tmp_path / "decision.json"
    monkeypatch.setattr("sys.argv", ["cli", "validate-candidate", str(result_path), "REL-001",
        "--decision", "validate", "--validator", "operator", "--reason", "Independent path capture reviewed", "--output", str(output)])
    main()
    decision = json.loads(output.read_text())
    assert decision["candidate"]["state"] == "CANDIDATE"
    assert decision["validator"] == "operator"
    with pytest.raises(SystemExit):
        main()


def test_missing_expected_alarm_requires_complete_monitoring():
    p = provider()
    p.pages["peer"]["frontmatter"] = {"monitoring_complete": True, "expected_fault_signals": ["peer-failure"]}
    observations = cross_events() + [event("peer-context", "peer", "inventory", polarity="context")]
    result = Investigator(p).investigate(run_input(), observations)
    hypothesis = next(h for h in result.ranked_hypotheses if h.canonical_root_entity == "peer")
    assert hypothesis.status.value == "REJECTED"
    assert "Expected signal absent" in hypothesis.failed_assumptions[0]
