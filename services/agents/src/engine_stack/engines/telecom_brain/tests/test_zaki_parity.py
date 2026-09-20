"""Parity test: run DEMO-001 two ways (direct Investigator vs Zaki) and compare key fields."""
import pytest
from pathlib import Path

from engine_stack.engines.telecom_brain.investigation.evidence import input_from_run, load_evidence
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider
from engine_stack.engines.telecom_brain.investigation.investigator import Investigator


def load_demo_run():
    base_dir = Path(__file__).resolve().parent.parent / "simulator" / "runs" / "RUN-SCN-001-L1-SEED-42001"
    if not base_dir.exists():
        pytest.skip("Demo run data not present")
    run = input_from_run(base_dir)
    op_dir = base_dir / "operational"
    evidence, hashes = load_evidence(run, op_dir)
    import yaml
    with open(op_dir / "topology_view.yaml", "r", encoding="utf-8") as f:
        topo = yaml.safe_load(f)
    pages = [{"slug": e} for e in topo.get("visible_entities", [])]
    provider = InMemoryKnowledgeProvider(pages, [], version="test-v1")
    return run, op_dir, evidence, hashes, provider


def extract_key(result):
    best = result.ranked_hypotheses[0] if result.ranked_hypotheses else None
    return {
        "selected_hypothesis_id": result.selected_hypothesis_id,
        "explanation_coverage": result.explanation_coverage,
        "terminal_state": result.terminal_state.value,
        "ranked": [(h.hypothesis_id, h.hypothesis_confidence) for h in result.ranked_hypotheses],
        "knowledge_gaps": result.knowledge_gaps,
    }


def test_demo_parity_direct_vs_zaki():
    run, op_dir, evidence, hashes, provider = load_demo_run()
    # Direct
    investigator = Investigator(provider)
    direct = investigator.investigate(run, evidence, hashes)

    # Zaki-mediated
    try:
        from engine_stack.engines.telecom_brain.investigation.zaki.orchestrator import ZakiOrchestrator
    except Exception:
        pytest.skip("Zaki orchestrator not available")
    orchestrator = ZakiOrchestrator(provider)
    zaki_result = orchestrator.start_investigation(run, op_dir)

    d = extract_key(direct)
    z = extract_key(zaki_result)

    assert d["terminal_state"] == z["terminal_state"]
    assert abs(d["explanation_coverage"] - z["explanation_coverage"]) < 1e-6
    assert d["selected_hypothesis_id"] == z["selected_hypothesis_id"]
    assert [r for r in d["ranked"]] == [r for r in z["ranked"]]
    assert d["knowledge_gaps"] == z["knowledge_gaps"]
