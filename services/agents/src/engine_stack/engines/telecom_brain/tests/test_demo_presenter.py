import json
from pathlib import Path

from ..investigation import demo_presenter


def test_render_table_and_strip_ansi():
    out = demo_presenter.render_table("T", ["A", "B"], [["one", "two"], ["three", "four"]])
    assert isinstance(out, str)
    assert "T" in out


def test_render_disentanglement_with_empty():
    s = demo_presenter.render_disentanglement_matrix([], [])
    assert isinstance(s, str)
    assert "No abnormal evidence" in s or "COGNITIVE DISENTANGLEMENT" in s


def test_render_falsification_with_empty():
    s = demo_presenter.render_falsification_scorecard([])
    assert isinstance(s, str)
    assert "No hypotheses ranked" in s or "EXPLAINABLE REASONING" in s


def test_causal_chain_from_result_empty():
    class Dummy:
        pass

    res = Dummy()
    res.ranked_hypotheses = []
    res.metadata = {"evidence": [], "relationships": []}
    chain = demo_presenter.causal_chain_from_result(res)
    assert isinstance(chain, list)


def test_verbose_presenter_rendering():
    from ..investigation.verbose_presenter import VerbosePresenter
    from ..investigation.contracts import Hypothesis, CausalRole, KnowledgeState, Terminal, InvestigationResult

    presenter = VerbosePresenter(use_color=False, show_vectors=True, show_math=True, auto=True)

    # Ingestion
    presenter.render_ingestion({"raw_count": 16, "sources": {"nms": 10, "ems": 6}, "types": {"alarms": 16}, "min_time": "2026-09-10T08:00:00Z", "max_time": "2026-09-10T08:02:00Z", "time_span": 120})

    # Phases 2.1 - 2.4
    presenter.render_correlation_2_1({"raw_count": 16, "normalized_count": 16, "collapsed_count": 14, "avg_freshness": 0.95, "max_age_hours": 1.0})
    presenter.render_correlation_2_2({"provider_name": "InMemory", "entities_traversed": 4, "relationships_found": 3, "node_count": 4, "edge_count": 3})
    presenter.render_correlation_2_3({"active_count": 4, "pathways": [{"name": "Operational Evidence", "active": True, "reason": "Found"}]})
    presenter.render_correlation_2_4({"abnormal_count": 14, "healthy_count": 1, "impacted_count": 4, "impacted_service": "5g_sa", "service_entities": {"5g_sa": ["n1"]}, "domains": ["IP"], "unrelated_count": 0})

    # Payload
    presenter.render_correlation_vector_payload({"score_dimensions": {"temporal_precedence": 1.0}, "raw_count": 16, "abnormal_count": 14, "impacted_count": 4, "domain_count": 2})
    presenter.render_summary_line({"raw_count": 16, "abnormal_count": 14, "impacted_count": 4})

    # Deep dive check
    assert presenter.prompt_deep_dive("correlation vector payload") is True
    assert presenter.prompt_deep_dive("12-factor synthesis core math") is True

    # Hypothesis generation
    presenter.render_hypothesis_generation({"roots": ["RTR-01", "UPF-01"], "dual_cause_count": 0})

    # Hypothesis testing
    h = Hypothesis(
        hypothesis_id="H-001",
        statement="Impairment at RTR-01",
        candidate_root_domain="IP",
        candidate_root_entity="RTR-01",
        canonical_root_entity="RTR-01",
        root_entities=["RTR-01"],
        causal_role=CausalRole.ROOT,
        assumptions=[],
        expected_observations=[],
        supporting_evidence=["e1"],
        contradicting_evidence=[],
        missing_evidence=[],
        knowledge_relationships_used=[],
        status=KnowledgeState.SUPPORTED,
        hypothesis_confidence=0.91,
        causal_confidence=0.85,
        explanation_coverage=1.0,
        score_dimensions={"blast_radius_coverage": 1.0, "independent_telemetry": 1.0},
        failed_assumptions=[],
    )
    presenter.render_hypothesis_testing_summary([h])
    presenter.render_hypothesis_testing_math(h, 1, 2)

    # Convergence, Domain, Evidence, Promotion
    presenter.render_convergence({"best": {"canonical_root_entity": "RTR-01", "score": 0.91}, "ranked": [{"entity": "RTR-01", "score": 0.91, "coverage": 1.0}], "explained": 14, "total_abnormal": 14, "coverage": 1.0, "residual_count": 0, "gap_count": 0, "terminal": "EXPLAINED"})
    presenter.render_domain_attribution({"primary_domain": "IP", "domains": [{"name": "IP", "primary": True}], "impacted_service": "5g_sa", "service_entities": ["n1"], "propagation_chain": "RTR-01 -> UPF-01"})
    presenter.render_next_best_evidence({"requests": [], "terminal": "EXPLAINED"})
    presenter.render_promotion({"no_gaps": True})


def test_cli_demo_command_execution():
    from ..investigation.cli import main
    # Run Demo 1 in auto mode with verbose
    exit_code = main(["demo", "1", "--auto", "--delay", "0.0", "--live", "-v"])
    assert exit_code == 0

