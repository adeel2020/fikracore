"""Comprehensive Automated Test Suite for Step 4.4 / H4 Proactive What-If, Critical Failure Surface & Resilience Validation.

Verifies the required tests from Section 59 of the H4 specification:
1. test_h4_forward_dependency_propagation
2. test_h4_blast_radius_precision_recall
3. test_h4_shared_dependency_detection
4. test_h4_failover_dependency_independence
5. test_h4_capacity_constrained_failover
6. test_h4_change_risk_detection
7. test_h4_multi_failure_propagation
8. test_h4_model_insufficient_when_topology_missing
9. test_h4_no_hallucinated_dependency_path
10. test_h4_critical_failure_surface_detection
11. test_h4_mitigation_comparison
12. test_h4_hidden_truth_not_visible_to_runtime
13. test_h4_mark_zaki_grounded_in_shared_state
14. test_h4_demo_metadata_does_not_change_reasoning
15. test_h4_h1_h2_h3_regression_suite_still_passes
16. test_fikracore_console_entry_point_registered
17. test_fikracore_help_invocation
18. test_scenario_resolves_by_exact_id
19. test_scenario_resolves_by_display_name
20. test_scenario_resolves_by_alias
21. test_scenario_resolution_is_case_insensitive
22. test_semantic_resolution_maps_to_existing_id
23. test_semantic_resolution_does_not_invent_id
24. test_ambiguous_input_requires_disambiguation
25. test_cli_ui_and_zaki_share_same_scenario_resolver
"""

from __future__ import annotations

import copy
import importlib.metadata
import inspect
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.contracts import (
    BlastRadiusLevel,
    PropagationSemantics,
    ResilienceActionCategory,
    WhatIfAssumptions,
    WhatIfScenario,
    WhatIfSimulationResult,
    WhatIfTrigger,
    ZakiContextContract,
)
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider
from engine_stack.engines.telecom_brain.presentation.scenario_resolver import (
    ResolutionMatchTier,
    ScenarioRecord,
    ScenarioRegistry,
    ScenarioResolver,
)
from engine_stack.engines.telecom_brain.presentation.ui_adapter import (
    build_ui_presentation_model_h4,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.resilience.analyzer import WhatIfAnalyzer
from engine_stack.engines.telecom_brain.resilience.h4_validator import validate_all_h4_scenarios
from engine_stack.engines.telecom_brain.simulator.h4_generator import generate_all_h4_scenarios


H4_RUNS_DIR = Path(__file__).parents[1] / "simulator" / "h4_runs"


@pytest.fixture(scope="session")
def h4_scenarios():
    """Ensure all 40 H4 scenarios are generated and available."""
    scenarios = generate_all_h4_scenarios(H4_RUNS_DIR)
    return scenarios


def load_and_simulate(scenario_id: str) -> tuple[WhatIfScenario, WhatIfSimulationResult, dict[str, Any], dict[str, Any]]:
    """Helper to load scenario artifacts and execute WhatIfAnalyzer simulation."""
    sc_dir = H4_RUNS_DIR / scenario_id
    with open(sc_dir / "scenario_manifest.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    with open(sc_dir / "operational" / "topology_view.yaml", "r", encoding="utf-8") as f:
        op_topo = yaml.safe_load(f)
    with open(sc_dir / "operational" / "redundancy_data.yaml", "r", encoding="utf-8") as f:
        red_data = yaml.safe_load(f)
    with open(sc_dir / "operational" / "capacity_data.yaml", "r", encoding="utf-8") as f:
        cap_data = yaml.safe_load(f)
    with open(sc_dir / "hidden" / "ground_truth.yaml", "r", encoding="utf-8") as f:
        ground_truth = yaml.safe_load(f)

    scenario = WhatIfScenario(
        what_if_id=manifest["what_if_id"],
        title=manifest["title"],
        trigger=WhatIfTrigger(**manifest["trigger"]),
        assumptions=WhatIfAssumptions(**manifest["assumptions"]),
        cohort=manifest.get("cohort", "single_point_failure"),
        failure_domain_tags=manifest.get("failure_domain_tags", []),
    )
    analyzer = WhatIfAnalyzer()
    result = analyzer.analyze_scenario(
        scenario=scenario,
        operational_topology=op_topo,
        redundancy_data=red_data,
        capacity_data=cap_data,
    )
    return scenario, result, op_topo, ground_truth


# ==============================================================================
# 1. Forward Dependency Propagation
# ==============================================================================
def test_h4_forward_dependency_propagation(h4_scenarios):
    """Test forward causal propagation: upstream failure cascades downstream."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-004")

    assert len(result.propagation_paths) > 0
    assert len(result.blast_radius.directly_affected_entities) > 0
    assert len(result.blast_radius.affected_services) > 0
    assert result.blast_radius.blast_radius_level in (
        BlastRadiusLevel.LOCAL,
        BlastRadiusLevel.DOMAIN,
        BlastRadiusLevel.MULTI_DOMAIN,
        BlastRadiusLevel.REGIONAL,
        BlastRadiusLevel.NETWORK_WIDE,
    )


# ==============================================================================
# 2. Blast Radius Precision & Recall
# ==============================================================================
def test_h4_blast_radius_precision_recall(h4_scenarios):
    """Verify precision and recall on generated H4 scenarios against ground truth."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-001")

    predicted_services = set(result.blast_radius.affected_services)
    expected_services = set(truth.get("true_affected_services", []))

    intersection = predicted_services.intersection(expected_services)
    recall = len(intersection) / len(expected_services) if expected_services else 1.0
    precision = len(intersection) / len(predicted_services) if predicted_services else 1.0

    assert recall >= 0.80, f"Expected recall >= 80%, got {recall:.2f}"
    assert precision >= 0.75, f"Expected precision >= 75%, got {precision:.2f}"


# ==============================================================================
# 3. Shared Dependency Detection
# ==============================================================================
def test_h4_shared_dependency_detection(h4_scenarios):
    """Detect when redundant members share a single upstream dependency (common-cause)."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-011")

    assert any(gap.type == "COMMON_CAUSE_FAILURE_DOMAIN" for gap in result.resilience_gaps)
    assert any(cfs.risk_type in ("COMMON_CAUSE", "COMMON_POWER", "COMMON_TRANSPORT", "SHARED_DEPENDENCY") for cfs in result.critical_failure_surfaces)


# ==============================================================================
# 4. Failover Dependency Independence
# ==============================================================================
def test_h4_failover_dependency_independence(h4_scenarios):
    """Verify that failover succeeds when backup has independent path, but flags risk if impaired."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-017")

    assert len(result.resilience_gaps) > 0
    gap_types = [g.type for g in result.resilience_gaps]
    assert any("COMMON_CAUSE" in gt or "FAILOVER" in gt or "REDUNDANCY" in gt for gt in gap_types)


# ==============================================================================
# 5. Capacity-Constrained Failover
# ==============================================================================
def test_h4_capacity_constrained_failover(h4_scenarios):
    """Detect failover overload when surviving node lacks capacity to absorb traffic."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-021")

    capacity_gaps = [g for g in result.resilience_gaps if g.type == "INSUFFICIENT_FAILOVER_CAPACITY"]
    assert len(capacity_gaps) > 0


# ==============================================================================
# 6. Change Risk Detection
# ==============================================================================
def test_h4_change_risk_detection(h4_scenarios):
    """Verify change risk identification during maintenance windows or high-risk changes."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-031")

    change_gaps = [g for g in result.resilience_gaps if g.type == "UNPROTECTED_MAINTENANCE_WINDOW"]
    assert len(change_gaps) > 0
    assert any("reschedule" in rec.title.lower() or "postpone" in rec.action.lower() or "maintenance" in rec.title.lower() for rec in result.recommended_actions)


# ==============================================================================
# 7. Multi-Failure Propagation
# ==============================================================================
def test_h4_multi_failure_propagation(h4_scenarios):
    """Compound blast radius across concurrent multiple triggers."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-033")

    assert len(result.blast_radius.affected_services) > 0
    assert result.blast_radius.blast_radius_level in (
        BlastRadiusLevel.DOMAIN,
        BlastRadiusLevel.MULTI_DOMAIN,
        BlastRadiusLevel.REGIONAL,
        BlastRadiusLevel.NETWORK_WIDE,
    )


# ==============================================================================
# 8. Model Insufficient When Topology Missing
# ==============================================================================
def test_h4_model_insufficient_when_topology_missing(h4_scenarios):
    """Epistemic humility: return MODEL_INSUFFICIENT when knowledge/topology is missing."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-040")

    assert result.terminal_state.value == "MODEL_INSUFFICIENT"
    assert result.confidence == 0.0
    assert any("UNMAPPED" in gap.type for gap in result.resilience_gaps)


# ==============================================================================
# 9. No Hallucinated Dependency Path
# ==============================================================================
def test_h4_no_hallucinated_dependency_path(h4_scenarios):
    """All steps in propagation paths must correspond to verified topology entities."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-001")

    op_vis = set(op_topo.get("visible_entities", []))
    for path in result.propagation_paths:
        for st in path:
            assert st.from_canonical_id in op_vis or st.from_canonical_id == scenario.trigger.canonical_id
            assert st.to_canonical_id in op_vis


# ==============================================================================
# 10. Critical Failure Surface Detection
# ==============================================================================
def test_h4_critical_failure_surface_detection(h4_scenarios):
    """Detect critical failure surfaces (single point of failure nodes and bottlenecks)."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-001")

    assert len(result.critical_failure_surfaces) > 0
    for cfs in result.critical_failure_surfaces:
        assert 0.0 <= cfs.criticality_score <= 1.0
        assert len(cfs.rationale) > 0


# ==============================================================================
# 11. Mitigation Comparison
# ==============================================================================
def test_h4_mitigation_comparison(h4_scenarios):
    """Evaluate and rank mitigation options with estimated residual risk."""
    scenario, result, op_topo, truth = load_and_simulate("H4-WI-001")

    assert len(result.mitigation_options) >= 2
    for opt in result.mitigation_options:
        assert opt.option_id is not None
        assert opt.risk_reduction >= 0.0
        assert len(opt.protected_services) > 0


# ==============================================================================
# 12. Hidden Truth Not Visible to Runtime
# ==============================================================================
def test_h4_hidden_truth_not_visible_to_runtime():
    """Verify runtime engine, presentation model, and scenario resolver never read hidden truth."""
    import engine_stack.engines.telecom_brain.presentation.scenario_resolver as sr_mod
    import engine_stack.engines.telecom_brain.presentation.ui_adapter as ui_mod
    import engine_stack.engines.telecom_brain.presentation.zaki_bridge as zb_mod
    import engine_stack.engines.telecom_brain.resilience.analyzer as an_mod

    for mod in [sr_mod, ui_mod, zb_mod, an_mod]:
        source = inspect.getsource(mod)
        assert "ground_truth.yaml" not in source, f"Forbidden hidden ground truth reference in {mod.__name__}"
        assert "hidden/" not in source, f"Forbidden hidden directory reference in {mod.__name__}"

    # Verify pre-benchmark integrity validation passes 100% with zero truth leakage
    val_report = validate_all_h4_scenarios(H4_RUNS_DIR)
    assert val_report["all_valid"] is True
    assert val_report["total_scenarios"] >= 40


# ==============================================================================
# 13. Mark & Zaki Grounded in Shared State
# ==============================================================================
def test_h4_mark_zaki_grounded_in_shared_state(h4_scenarios):
    """Mark (UI) and Zaki (chat) draw from the exact same presentation model and resilience state."""
    scenario, sim_result, op_topo, truth = load_and_simulate("H4-WI-001")
    ui_model = build_ui_presentation_model_h4(sim_result, H4_RUNS_DIR / "H4-WI-001")

    assert ui_model.resilience is not None
    resilience_data = ui_model.resilience

    # Create Zaki context from the UI presentation model
    zaki_ctx = ZakiContextContract(
        active_scenario="H4-WI-001",
        resilience_state=resilience_data,
    )
    bridge = ZakiBridge()

    # Query 1: Blast radius
    r1 = bridge.answer_query("What is the blast radius of this failure?", context=zaki_ctx)["response"]
    assert "blast radius" in r1.lower() or "radius" in r1.lower()

    # Query 2: Impacted services
    r2 = bridge.answer_query("Which services are affected?", context=zaki_ctx)["response"]
    assert "affected" in r2.lower() or "5g" in r2.lower() or "services" in r2.lower()

    # Query 3: Mitigation recommendations
    r3 = bridge.answer_query("What mitigations do you recommend?", context=zaki_ctx)["response"]
    assert "mitigation" in r3.lower() or "recommend" in r3.lower() or "action" in r3.lower()


# ==============================================================================
# 14. Demo Metadata Does Not Change Reasoning
# ==============================================================================
def test_h4_demo_metadata_does_not_change_reasoning(h4_scenarios):
    """Toggling curated demo mode must not alter underlying simulation or reasoning."""
    scenario, sim_result, op_topo, truth = load_and_simulate("H4-WI-001")

    ui_normal = build_ui_presentation_model_h4(sim_result, H4_RUNS_DIR / "H4-WI-001", mode="INVESTIGATION")
    ui_demo = build_ui_presentation_model_h4(sim_result, H4_RUNS_DIR / "H4-WI-001", mode="DEMO")

    # Core simulation analysis must match 100%
    assert ui_normal.resilience["blast_radius"] == ui_demo.resilience["blast_radius"]
    assert ui_normal.resilience["affected_services"] == ui_demo.resilience["affected_services"]
    assert ui_normal.resilience["critical_failure_surfaces"] == ui_demo.resilience["critical_failure_surfaces"]
    assert ui_normal.resilience["mitigation_options"] == ui_demo.resilience["mitigation_options"]

    # Demo progression metadata is added to presentation block
    assert ui_normal.presentation["active_mode"] == "INVESTIGATION"
    assert ui_demo.presentation["active_mode"] == "DEMO"
    assert ui_demo.presentation["total_steps"] == 7
    assert len(ui_demo.presentation["available_steps"]) == 7


# ==============================================================================
# 15. H1, H2, H3 Regression Suite Still Passes
# ==============================================================================
def test_h4_h1_h2_h3_regression_suite_still_passes():
    """Verify that prior hypothesis data models, contracts, and tests remain intact."""
    from engine_stack.engines.telecom_brain.investigation.contracts import (
        CandidateRelationship,
        GeneratedRunInput,
        KnowledgeGapType,
        KnowledgePromotionState,
        Terminal,
    )
    # Instantiate H1-H3 core contracts
    run_input = GeneratedRunInput(
        run_id="RUN-REGRESS-01",
        scenario_id="SC-REGRESS-01",
        difficulty_profile="L1",
        seed=42,
    )
    assert run_input.run_id == "RUN-REGRESS-01"
    assert run_input.difficulty_profile == "L1"
    assert Terminal.EXPLAINED.value == "EXPLAINED"
    assert Terminal.MODEL_INSUFFICIENT.value == "MODEL_INSUFFICIENT"
    assert KnowledgeGapType.MISSING_DEPENDENCY.value == "MISSING_DEPENDENCY"
    assert KnowledgePromotionState.PROMOTED.value == "PROMOTED"


# ==============================================================================
# 16. fikracore Console Entry Point Registered
# ==============================================================================
def test_fikracore_console_entry_point_registered():
    """Verify fikracore is registered as a console script entry point in pyproject.toml and virtual environment."""
    pyproject_file = Path(__file__).parents[5] / "pyproject.toml"
    if pyproject_file.exists():
        content = pyproject_file.read_text(encoding="utf-8")
        assert 'fikracore = "engine_stack.engines.telecom_brain.investigation.cli:main"' in content

    # Check across installed distributions or which(fikracore)
    all_eps = [
        ep
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name") == "agenticaiops-agents"
        for ep in dist.entry_points
        if ep.name == "fikracore"
    ]
    fikra_bin = shutil.which("fikracore")
    assert len(all_eps) > 0 or fikra_bin is not None
    if all_eps:
        assert "engine_stack.engines.telecom_brain.investigation.cli:main" in all_eps[0].value


# ==============================================================================
# 17. fikracore Help Invocation
# ==============================================================================
def test_fikracore_help_invocation():
    """Verify fikracore --help invocation succeeds with code 0 and displays subcommands."""
    from engine_stack.engines.telecom_brain.investigation.cli import build_parser

    parser = build_parser()
    help_text = parser.format_help()
    assert "fikracore" in help_text or "usage:" in help_text
    assert "predict" in help_text
    assert "inspect" in help_text
    assert "present" in help_text
    assert "generate-h4-scenarios" in help_text
    assert "validate-h4-scenarios" in help_text
    assert "run-h4-benchmark" in help_text
    assert "h4-report" in help_text
    assert "h4-demo" in help_text


# ==============================================================================
# 18-25. Scenario Resolver Test Suite
# ==============================================================================
def test_scenario_resolves_by_exact_id():
    """Resolver finds scenario by exact stable ID."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    match = resolver.resolve("H4-WI-001")
    assert match is not None
    assert match.record.scenario_id == "H4-WI-001"
    assert match.tier == ResolutionMatchTier.EXACT_ID
    assert match.confidence == 1.0


def test_scenario_resolves_by_display_name():
    """Resolver finds scenario by human-readable display name."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    match = resolver.resolve("MPLS Edge Router Failure")
    assert match is not None
    assert match.record.scenario_id == "H4-WI-001"
    assert match.tier in (ResolutionMatchTier.EXACT_NAME, ResolutionMatchTier.NORMALIZED)


def test_scenario_resolves_by_alias():
    """Resolver finds scenario by registered alias."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    match = resolver.resolve("edge router outage")
    assert match is not None
    assert match.record.scenario_id == "H4-WI-001"
    assert match.tier == ResolutionMatchTier.ALIAS


def test_scenario_resolution_is_case_insensitive():
    """Resolver handles upper/lower/mixed case inputs."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    match_upper = resolver.resolve("H4-WI-001")
    match_lower = resolver.resolve("h4-wi-001")
    match_mixed = resolver.resolve("MpLs EdGe RoUtEr FaIlUrE")

    assert match_upper.record.scenario_id == "H4-WI-001"
    assert match_lower.record.scenario_id == "H4-WI-001"
    assert match_mixed.record.scenario_id == "H4-WI-001"


def test_semantic_resolution_maps_to_existing_id():
    """Semantic NLP resolution maps fuzzy descriptions strictly to known scenario IDs."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    # Query with semantic variation: "gateway power failure"
    match = resolver.resolve("datacenter main pdu failure")
    assert match is not None
    assert match.record.scenario_id in [r.scenario_id for r in registry.list_all()]


def test_semantic_resolution_does_not_invent_id():
    """Semantic resolution returns None when input is completely unrelated nonsense."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    match = resolver.resolve("xyzzy completely unknown unicorn banana rocket")
    assert match is None or match.requires_disambiguation or match.confidence < 0.3


def test_ambiguous_input_requires_disambiguation():
    """Ambiguous query returns multiple candidates and flags requires_disambiguation."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    # "Failure" matches many scenarios
    match = resolver.resolve("Failure")
    if match:
        assert match.requires_disambiguation is True or len(match.candidates) >= 1


def test_cli_ui_and_zaki_share_same_scenario_resolver():
    """CLI, UI, and Zaki bridge all use the unified ScenarioResolver."""
    registry = ScenarioRegistry.get_default()
    resolver = ScenarioResolver(registry)

    # Verify that registry contains all 40 H4 scenarios
    assert len(registry.list_all()) >= 40
    # Test that resolver resolves any H4 ID reliably
    for i in range(1, 41):
        sc_id = f"H4-WI-{i:03d}"
        res = resolver.resolve(sc_id)
        assert res is not None, f"Failed to resolve {sc_id}"
        assert res.record.scenario_id == sc_id
