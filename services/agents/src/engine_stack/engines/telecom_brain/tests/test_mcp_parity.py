"""Automated Test Suite for Step 4.6 Live MCP Parity & Benchmark Validation.

Implements all 16 required test cases specified in Section 50 of Step 4.6:
1. test_live_provider_contract_matches_snapshot_provider
2. test_parity_exact_match_classification
3. test_parity_semantic_match_classification
4. test_explained_delta_classification
5. test_unexplained_delta_classification
6. test_mcp_failure_not_treated_as_empty_graph
7. test_timeout_marks_provider_unavailable
8. test_live_canonical_resolution
9. test_live_relationship_direction_normalization
10. test_live_provider_provenance
11. test_mark_zaki_uses_active_provider_state
12. test_hidden_truth_not_sent_to_mcp
13. test_h1_live_parity
14. test_h2_live_parity
15. test_h3_live_parity
16. test_h4_live_parity
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from engine_stack.engines.telecom_brain.canonicalization import load_default_resolver
from engine_stack.engines.telecom_brain.investigation.contracts import (
    Terminal,
    ZakiContextContract,
)
from engine_stack.engines.telecom_brain.investigation.knowledge import (
    CanonicalKnowledge,
    InMemoryKnowledgeProvider,
    ProviderError,
)
from engine_stack.engines.telecom_brain.investigation.mcp_parity import (
    DriftType,
    LiveMcpParityProvider,
    McpParityRunner,
    ParityClass,
    classify_parity_result,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.tests.test_mcp_smoke import FakeMockProvider


# 1. test_live_provider_contract_matches_snapshot_provider (§50.1)
def test_live_provider_contract_matches_snapshot_provider():
    fake_mcp = FakeMockProvider()
    live_prov = LiveMcpParityProvider(fake_mcp, overlay_pages=[{"slug": "test-node"}])
    snap_prov = InMemoryKnowledgeProvider([{"slug": "test-node"}], [])

    # Both must implement the protocol methods:
    for method_name in ["get_page", "get_links", "get_backlinks", "traverse", "search", "query"]:
        assert hasattr(live_prov, method_name)
        assert hasattr(snap_prov, method_name)

    assert live_prov.metadata["brain"] == snap_prov.metadata["brain"] == "telecombrain"


# 2. test_parity_exact_match_classification (§50.2)
def test_parity_exact_match_classification():
    snap = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "sgi-edge-01"}
    live = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "sgi-edge-01"}
    p_class, drift, reason = classify_parity_result(snap, live, "H1")
    assert p_class == ParityClass.EXACT_PARITY
    assert drift == DriftType.NO_DRIFT
    assert reason is None


# 3. test_parity_semantic_match_classification (§50.3)
def test_parity_semantic_match_classification():
    snap = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "sgi-edge-01"}
    live = {"terminal_state": "PARTIALLY_EXPLAINED", "top_hypothesis_root": "sgi-edge-01"}
    p_class, drift, reason = classify_parity_result(snap, live, "H1")
    assert p_class == ParityClass.SEMANTIC_PARITY
    assert drift == DriftType.NO_DRIFT


# 4. test_explained_delta_classification (§50.4)
def test_explained_delta_classification():
    snap = {"blast_radius_level": "DOMAIN", "affected_services": ["5G Data"]}
    live = {"blast_radius_level": "DOMAIN", "affected_services": ["5G Data", "VoLTE"], "has_newer_knowledge": True}
    p_class, drift, reason = classify_parity_result(snap, live, "H4")
    assert p_class == ParityClass.EXPLAINED_DELTA
    assert drift == DriftType.NEW_KNOWLEDGE
    assert "Live telecombrain knows additional" in reason


# 5. test_unexplained_delta_classification (§50.5)
def test_unexplained_delta_classification():
    snap = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "node-A"}
    live = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "node-B", "has_newer_knowledge": False}
    p_class, drift, reason = classify_parity_result(snap, live, "H1")
    assert p_class == ParityClass.UNEXPLAINED_DELTA
    assert drift == DriftType.UNEXPECTED_DRIFT
    assert "Root cause mismatch" in reason


# 6. test_mcp_failure_not_treated_as_empty_graph (§50.6, §30)
def test_mcp_failure_not_treated_as_empty_graph():
    fake_mcp = FakeMockProvider()
    fake_mcp.get_links = MagicMock(side_effect=ProviderError("offline: connection timeout"))
    prov = LiveMcpParityProvider(fake_mcp)

    with pytest.raises(ProviderError, match="KNOWLEDGE_PROVIDER_UNAVAILABLE"):
        prov.get_links("sgi-edge-01")


# 7. test_timeout_marks_provider_unavailable (§50.7, §31)
def test_timeout_marks_provider_unavailable():
    fake_mcp = FakeMockProvider()
    fake_mcp.traverse = MagicMock(side_effect=ProviderError("offline: socket timed out"))
    prov = LiveMcpParityProvider(fake_mcp)

    with pytest.raises(ProviderError, match="KNOWLEDGE_PROVIDER_UNAVAILABLE"):
        prov.traverse("mme-01")


# 8. test_live_canonical_resolution (§50.8, §25)
def test_live_canonical_resolution():
    fake_mcp = FakeMockProvider()
    prov = LiveMcpParityProvider(fake_mcp)
    resolver = load_default_resolver()
    ck = CanonicalKnowledge(prov, resolver)

    # Legacy slug mapped by default resolver
    page = ck.get_page("mobile-core/incidents/sgi-throughput-drop")
    assert page is not None
    assert page["slug"] == "incidents/mobile-core/sgi-data-a154bb7a3997859c"


# 9. test_live_relationship_direction_normalization (§50.9, §26)
def test_live_relationship_direction_normalization():
    fake_mcp = FakeMockProvider()
    prov = LiveMcpParityProvider(fake_mcp)
    resolver = load_default_resolver()
    ck = CanonicalKnowledge(prov, resolver)

    edges = ck.traverse("domains/mobile-core/networks/lte/functions/mme-01")
    assert isinstance(edges, list)
    for edge in edges:
        assert hasattr(edge, "source")
        assert hasattr(edge, "target")
        assert hasattr(edge, "link_type")


# 10. test_live_provider_provenance (§50.10, §32)
def test_live_provider_provenance():
    fake_mcp = FakeMockProvider()
    prov = LiveMcpParityProvider(fake_mcp)
    page = prov.get_page("domains/mobile-core/networks/lte/functions/mme-01")
    assert page is not None
    assert page.get("provenance") == "gbrain-mcp"


# 11. test_mark_zaki_uses_active_provider_state (§50.11, §33)
def test_mark_zaki_uses_active_provider_state():
    bridge = ZakiBridge()
    ctx = ZakiContextContract(
        active_scenario="H4-WI-001",
        resilience_state={
            "trigger": {"entity_display_name": "MPLS Edge Router-07"},
            "blast_radius": {"blast_radius_level": "DOMAIN"},
            "affected_services": ["5G SA Mobile Data"],
        },
    )
    ans = bridge.answer_query("Why is this service affected?", context=ctx)
    assert ans["grounded"] is True
    assert "MPLS Edge Router-07" in ans["response"]


# 12. test_hidden_truth_not_sent_to_mcp (§50.12, §21)
def test_hidden_truth_not_sent_to_mcp():
    runner = McpParityRunner()
    payload = {"entity": "mme-01", "hidden_ground_truth": {"root": "router-01"}}
    runner._check_truth_leakage(payload, "test_mcp_call")
    assert runner.hidden_truth_leakage == 1


# 13. test_h1_live_parity (§50.13)
def test_h1_live_parity():
    snap = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "sgi-edge-01", "hypotheses_count": 2}
    live = {"terminal_state": "EXPLAINED", "top_hypothesis_root": "sgi-edge-01", "hypotheses_count": 2, "has_newer_knowledge": True}
    p_class, drift, reason = classify_parity_result(snap, live, "H1")
    assert p_class in (ParityClass.EXACT_PARITY, ParityClass.SEMANTIC_PARITY)


# 14. test_h2_live_parity (§50.14)
def test_h2_live_parity():
    snap = {"terminal_state": "MODEL_INSUFFICIENT", "discovery_mode": True, "candidates_count": 1}
    live = {"terminal_state": "MODEL_INSUFFICIENT", "discovery_mode": True, "candidates_count": 1, "has_newer_knowledge": True}
    p_class, drift, reason = classify_parity_result(snap, live, "H2")
    assert p_class == ParityClass.EXACT_PARITY
    assert drift == DriftType.NO_DRIFT


# 15. test_h3_live_parity (§50.15)
def test_h3_live_parity():
    snap = {"reused": True, "cohort": "positive_transfer", "decision": "ACCEPT"}
    live = {"reused": True, "cohort": "positive_transfer", "decision": "ACCEPT", "has_newer_knowledge": True}
    p_class, drift, reason = classify_parity_result(snap, live, "H3")
    assert p_class == ParityClass.EXACT_PARITY


# 16. test_h4_live_parity (§50.16)
def test_h4_live_parity():
    snap = {"blast_radius_level": "DOMAIN", "affected_services": ["5G SA Mobile Data"], "surfaces_count": 1, "mitigations_count": 3}
    live = {"blast_radius_level": "DOMAIN", "affected_services": ["5G SA Mobile Data"], "surfaces_count": 1, "mitigations_count": 3, "has_newer_knowledge": True}
    p_class, drift, reason = classify_parity_result(snap, live, "H4")
    assert p_class == ParityClass.EXACT_PARITY
    assert drift == DriftType.NO_DRIFT
