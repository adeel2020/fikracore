"""Unit and integration tests for FikraCore Step 4.7 Knowledge Inventory & Coverage.

Verifies the 15 required test cases from Section 52 of the specification:
1. test_inspect_knowledge_uses_inventory_not_smoke_summary
2. test_inventory_paginates_all_pages
3. test_inventory_counts_pages_correctly
4. test_inventory_deduplicates_links
5. test_domain_distribution
6. test_type_distribution
7. test_orphan_detection
8. test_alias_resolution_summary
9. test_stale_knowledge_detection
10. test_candidate_vs_confirmed_separation
11. test_gap_summary
12. test_coverage_summary
13. test_json_output
14. test_mark_zaki_uses_inventory_state
15. test_mcp_failure_not_reported_as_empty_brain
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from engine_stack.engines.telecom_brain.investigation.knowledge_inventory import (
    KnowledgeInventoryCollector,
    KnowledgeInventoryResult,
    KnowledgeState,
    GapClass,
)
from engine_stack.engines.telecom_brain.investigation.knowledge_coverage import (
    KnowledgeCoverageAnalyzer,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge


class MockMcpKnowledgeProvider:
    """Hermetic mock MCP provider for testing inventory collection and pagination."""

    def __init__(self, pages: List[Dict[str, Any]] | None = None, links: Dict[str, List[Dict[str, Any]]] | None = None):
        self.url = "http://localhost:3131/mcp"
        self.contracts = {
            "list_pages": {},
            "get_links": {},
            "get_page": {},
            "get_active_schema_pack": {},
        }
        self.pages = pages or self._default_sample_pages()
        self.links = links or self._default_sample_links()
        self.call_history = []

    def _default_sample_pages(self) -> List[Dict[str, Any]]:
        return [
            # Mobile Core
            {"slug": "domains/mobile-core/networks/5g/functions/amf-01", "type": "network-function", "title": "AMF-01", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "domains/mobile-core/networks/5g/functions/smf-01", "type": "network-function", "title": "SMF-01", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "domains/mobile-core/networks/5g/functions/upf-01", "type": "network-function", "title": "UPF-01", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "domains/mobile-core/services/embb-service", "type": "service", "title": "eMBB Service", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "mobile-core/incidents/sgi-throughput-drop", "type": "incident", "title": "Sgi Throughput Drop", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "mobile-core/evidence/pcap-sgi-01", "type": "evidence", "title": "PCAP Sgi 01", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "mobile-core/hypotheses/hyp-mtu-blackhole", "type": "hypothesis", "title": "MTU Blackhole Hypothesis", "updated_at": "2026-09-08T10:00:00Z"},
            # Transport
            {"slug": "domains/transport/routers/er-01", "type": "network-function", "title": "Edge Router 01", "updated_at": "2026-09-08T10:00:00Z"},
            {"slug": "domains/transport/routers/er-02", "type": "network-function", "title": "Edge Router 02", "updated_at": "2026-09-08T10:00:00Z"},
            # Stale incident
            {"slug": "mobile-core/incidents/amf-overload-old", "type": "incident", "title": "AMF Overload Old", "updated_at": "2026-05-01T10:00:00Z"},
            # Operational orphan (incident with 0 links)
            {"slug": "mobile-core/incidents/isolated-incident-orphan", "type": "incident", "title": "Isolated Incident", "updated_at": "2026-09-08T10:00:00Z"},
            # Non-operational note (should NOT be classified as orphan even with 0 links)
            {"slug": "notes/release-notes-2026", "type": "note", "title": "Release Notes", "updated_at": "2026-09-08T10:00:00Z"},
            # Alias page
            {"slug": "aliases/incident-alias-01", "type": "incident-alias", "title": "Alias 01", "target_slug": "missing-incident-target", "updated_at": "2026-09-08T10:00:00Z"},
        ]

    def _default_sample_links(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "domains/mobile-core/networks/5g/functions/amf-01": [
                {"from_slug": "domains/mobile-core/networks/5g/functions/amf-01", "to_slug": "domains/mobile-core/networks/5g/functions/smf-01", "link_type": "depends_on"},
                {"from_slug": "domains/mobile-core/networks/5g/functions/amf-01", "to_slug": "domains/mobile-core/services/embb-service", "link_type": "supports_service"},
            ],
            "domains/mobile-core/networks/5g/functions/smf-01": [
                {"from_slug": "domains/mobile-core/networks/5g/functions/smf-01", "to_slug": "domains/mobile-core/networks/5g/functions/upf-01", "link_type": "depends_on"},
            ],
            "domains/mobile-core/networks/5g/functions/upf-01": [
                {"from_slug": "domains/mobile-core/networks/5g/functions/upf-01", "to_slug": "domains/transport/routers/er-01", "link_type": "routes_through"},
            ],
            "domains/transport/routers/er-01": [
                {"from_slug": "domains/transport/routers/er-01", "to_slug": "domains/transport/routers/er-02", "link_type": "routes_through"},
            ],
            "mobile-core/incidents/sgi-throughput-drop": [
                {"from_slug": "mobile-core/incidents/sgi-throughput-drop", "to_slug": "domains/mobile-core/networks/5g/functions/upf-01", "link_type": "involves"},
                {"from_slug": "mobile-core/incidents/sgi-throughput-drop", "to_slug": "mobile-core/evidence/pcap-sgi-01", "link_type": "supported-by"},
            ],
        }

    def _call(self, name: str, arguments: dict) -> Any:
        self.call_history.append((name, arguments))
        if name == "get_active_schema_pack":
            return "mobile-core@0.1.0+2eea5e14"
        elif name == "list_pages":
            offset = arguments.get("offset", 0)
            limit = arguments.get("limit", 100)
            return self.pages[offset:offset + limit]
        elif name == "get_links":
            slug = arguments.get("slug", "")
            return self.links.get(slug, [])
        return None


# ==============================================================================
# 15 Test Cases
# ==============================================================================

def test_inspect_knowledge_uses_inventory_not_smoke_summary():
    """1. test_inspect_knowledge_uses_inventory_not_smoke_summary:
    Verifies that inspect knowledge produces KnowledgeInventoryResult with page/link counts
    rather than integration health metrics (checks_passed).
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert isinstance(result, KnowledgeInventoryResult)
    assert result.summary.total_pages == 13
    assert result.summary.total_unique_links > 0
    # Must contain domain distribution, not smoke checks_passed
    assert "Mobile Core" in result.domains
    assert hasattr(result.summary, "total_pages")
    assert not hasattr(result.summary, "checks_passed")


def test_inventory_paginates_all_pages():
    """2. test_inventory_paginates_all_pages:
    Verifies that pagination retrieves all pages across multiple batches when batch size is smaller than total.
    """
    # Create 120 dummy pages to force pagination across limit=100
    large_pages = [
        {"slug": f"domains/mobile-core/functions/fn-{i}", "type": "network-function", "title": f"Function {i}", "updated_at": "2026-09-08T10:00:00Z"}
        for i in range(120)
    ]
    provider = MockMcpKnowledgeProvider(pages=large_pages, links={})
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert result.summary.total_pages == 120
    # Check that list_pages was called at least twice (offset 0, offset 100)
    list_calls = [c for c in provider.call_history if c[0] == "list_pages"]
    assert len(list_calls) >= 2
    assert list_calls[0][1].get("offset") == 0
    assert list_calls[1][1].get("offset") == 100


def test_inventory_counts_pages_correctly():
    """3. test_inventory_counts_pages_correctly:
    Verifies that total_pages matches exact number of unique pages enumerated.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert result.summary.total_pages == len(provider.pages)
    assert len(result.entities) == len(provider.pages)


def test_inventory_deduplicates_links():
    """4. test_inventory_deduplicates_links:
    Verifies that duplicate link records are counted only once.
    """
    # Create duplicated links in provider
    dup_links = {
        "page-a": [
            {"from_slug": "page-a", "to_slug": "page-b", "link_type": "depends_on"},
            {"from_slug": "page-a", "to_slug": "page-b", "link_type": "depends_on"},  # Duplicate
        ]
    }
    pages = [
        {"slug": "page-a", "type": "network-function", "title": "Page A"},
        {"slug": "page-b", "type": "network-function", "title": "Page B"},
    ]
    provider = MockMcpKnowledgeProvider(pages=pages, links=dup_links)
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert result.summary.total_unique_links == 1
    assert len(result.unique_links) == 1


def test_domain_distribution():
    """5. test_domain_distribution:
    Verifies that pages are correctly classified into telecom domains.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert "Mobile Core" in result.domains
    assert "Transport" in result.domains
    assert result.domains["Mobile Core"]["entities_count"] > 0
    assert result.domains["Transport"]["entities_count"] == 2


def test_type_distribution():
    """6. test_type_distribution:
    Verifies that page types are accurately counted.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert "network-function" in result.page_types
    assert "incident" in result.page_types
    assert "service" in result.page_types
    assert result.page_types["network-function"] == 5  # amf, smf, upf, er1, er2


def test_orphan_detection():
    """7. test_orphan_detection:
    Verifies that operational entities with degree 0 are flagged as orphans,
    while non-operational notes/concepts are excluded.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    # isolated-incident-orphan has 0 links -> orphan
    orphan_slugs = [e.slug for e in result.entities if e.is_operational_orphan]
    assert "mobile-core/incidents/isolated-incident-orphan" in orphan_slugs
    # release-notes-2026 is a note -> NOT an orphan
    assert "notes/release-notes-2026" not in orphan_slugs
    assert result.summary.orphans_count >= 1


def test_alias_resolution_summary():
    """8. test_alias_resolution_summary:
    Verifies that incident-alias pointing to missing target is reported as an unresolved alias gap.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    alias_gaps = [g for g in result.gaps if g.gap_class == GapClass.UNRESOLVED_ALIAS]
    assert len(alias_gaps) >= 1
    assert "aliases/incident-alias-01" in alias_gaps[0].entity_or_domain


def test_stale_knowledge_detection():
    """9. test_stale_knowledge_detection:
    Verifies that records older than stale_threshold_days are classified as STALE.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider, stale_threshold_days=30)
    result = collector.collect()

    stale_entities = [e for e in result.entities if e.knowledge_state == KnowledgeState.STALE]
    assert len(stale_entities) >= 1
    assert any("amf-overload-old" in e.slug for e in stale_entities)
    assert result.summary.stale_knowledge_count >= 1


def test_candidate_vs_confirmed_separation():
    """10. test_candidate_vs_confirmed_separation:
    Verifies that candidate knowledge (e.g. hypotheses) is distinct from confirmed knowledge.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert result.knowledge_states[KnowledgeState.CANDIDATE] >= 1
    assert result.knowledge_states[KnowledgeState.CONFIRMED] >= 1

    hyp = [e for e in result.entities if e.type == "hypothesis"][0]
    assert hyp.knowledge_state == KnowledgeState.CANDIDATE


def test_gap_summary():
    """11. test_gap_summary:
    Verifies that gaps list contains actionable classes and recommendations.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    assert len(result.gaps) > 0
    for g in result.gaps:
        assert g.gap_class in (
            GapClass.ORPHAN_ENTITY,
            GapClass.UNRESOLVED_ALIAS,
            GapClass.MISSING_RELATIONSHIP,
            GapClass.SPARSE_DOMAIN,
            GapClass.SPARSE_SERVICE,
            GapClass.STALE_KNOWLEDGE,
            GapClass.INCOMPLETE_CROSS_DOMAIN_COVERAGE,
            GapClass.INCOMPLETE_SERVICE_MAPPING,
        )
        assert len(g.recommendation) > 0


def test_coverage_summary():
    """12. test_coverage_summary:
    Verifies that KnowledgeCoverageAnalyzer computes valid composite scores and labels.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    analyzer = KnowledgeCoverageAnalyzer(result)
    report = analyzer.analyze()

    assert 0.0 <= report.overall_composite_score_pct <= 100.0
    assert report.overall_status in ("WELL_COVERED", "PARTIALLY_COVERED", "SPARSE", "UNKNOWN")
    assert "Mobile Core" in report.domain_scores
    assert len(report.cross_domain_matrix) > 0


def test_json_output(tmp_path):
    """13. test_json_output:
    Verifies that all 6 artifacts are generated as valid JSON and Markdown.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    analyzer = KnowledgeCoverageAnalyzer(result)
    artifacts = analyzer.generate_all_artifacts(output_dir=tmp_path)

    assert len(artifacts) == 6
    assert (tmp_path / "knowledge-inventory.json").exists()
    assert (tmp_path / "knowledge-inventory.md").exists()
    assert (tmp_path / "knowledge-gaps.json").exists()
    assert (tmp_path / "knowledge-gaps.md").exists()
    assert (tmp_path / "coverage-report.json").exists()
    assert (tmp_path / "coverage-report.md").exists()

    with open(tmp_path / "knowledge-inventory.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"]["total_pages"] == 13


def test_mark_zaki_uses_inventory_state():
    """14. test_mark_zaki_uses_inventory_state:
    Verifies that ZakiBridge can answer operator queries using structured inventory state.
    """
    provider = MockMcpKnowledgeProvider()
    collector = KnowledgeInventoryCollector(provider=provider)
    result = collector.collect()

    bridge = ZakiBridge()

    # Query 1: Mobile core
    ans1 = bridge.answer_inventory_query("What does FikraCore know about Mobile Core?", inventory=result)
    assert "Mobile Core" in ans1["response"]
    assert ans1["grounded"] is True

    # Query 2: Services
    ans2 = bridge.answer_inventory_query("What services do you know?", inventory=result)
    assert "services" in ans2["response"].lower() or "embb" in ans2["response"].lower()

    # Query 3: Gaps
    ans3 = bridge.answer_inventory_query("Where are the biggest knowledge gaps?", inventory=result)
    assert "gaps" in ans3["response"].lower() or "operational" in ans3["response"].lower()


def test_mcp_failure_not_reported_as_empty_brain():
    """15. test_mcp_failure_not_reported_as_empty_brain:
    Verifies that an MCP failure throws KNOWLEDGE_INVENTORY_MCP_FAILURE rather than reporting 0 pages.
    """
    class BrokenMcpProvider:
        contracts = {"list_pages": {}}
        def _call(self, name, args):
            raise ConnectionError("Connection refused by MCP server")

    collector = KnowledgeInventoryCollector(provider=BrokenMcpProvider())
    with pytest.raises(RuntimeError) as exc_info:
        collector.collect()
    assert "KNOWLEDGE_INVENTORY_MCP_FAILURE" in str(exc_info.value)
