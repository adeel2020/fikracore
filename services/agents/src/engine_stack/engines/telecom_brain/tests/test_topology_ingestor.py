"""Tests for ReferenceTopologyIngestor — zero-regression safety net.

Validates:
1. Hidden epistemic gaps are excluded from the output.
2. Simulator-only fields (failure_domains, vendor_profiles, etc.) are stripped.
3. Output passes reject_truth() — no simulator secrets leak.
4. Output is FrozenTelecomBrainProvider-compatible.
5. Known operational relationships are included.
6. Entity counts, domain counts, and relationship counts match expectations.
7. Service chain metadata is present but does not leak causal paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.evidence import reject_truth
from engine_stack.engines.telecom_brain.investigation.knowledge import (
    FrozenTelecomBrainProvider,
    InMemoryKnowledgeProvider,
)
from engine_stack.engines.telecom_brain.investigation.topology_ingestor import (
    dry_run_report,
    ingest_reference_topology,
    write_snapshot,
)


REFERENCE_NETWORK_PATH = (
    Path(__file__).parents[1] / "simulator" / "operator_model" / "reference_synthetic_network.yaml"
)


@pytest.fixture
def reference_network_path():
    assert REFERENCE_NETWORK_PATH.exists(), f"Reference network not found: {REFERENCE_NETWORK_PATH}"
    return REFERENCE_NETWORK_PATH


@pytest.fixture
def snapshot(reference_network_path):
    return ingest_reference_topology(reference_network_path, version_label="test-v2.0")


# ── 1. Hidden Gaps Exclusion ──

def test_hidden_relationships_excluded(snapshot, reference_network_path):
    """Hidden epistemic blind spots must NOT appear in the ingested snapshot."""
    with open(reference_network_path) as f:
        raw = yaml.safe_load(f)

    hidden_ids = set(
        raw.get("fikracore_operational_view", {}).get("hidden_from_operational_view", [])
    )
    assert len(hidden_ids) > 0, "Test requires hidden relationships to be defined"

    ingested_rel_ids = {r["relationship_id"] for r in snapshot["relationships"]}
    leaked = ingested_rel_ids & hidden_ids

    assert len(leaked) == 0, f"Hidden epistemic gaps leaked into snapshot: {leaked}"


def test_candidate_relationships_excluded(snapshot, reference_network_path):
    """Candidate relationships (CAND-REL-*) must NOT be pre-loaded."""
    with open(reference_network_path) as f:
        raw = yaml.safe_load(f)

    candidates = raw.get("fikracore_operational_view", {}).get("candidate_relationships", [])
    candidate_ids = {c["relationship_id"] for c in candidates}

    ingested_rel_ids = {r["relationship_id"] for r in snapshot["relationships"]}
    leaked = ingested_rel_ids & candidate_ids

    assert len(leaked) == 0, f"Candidate relationships leaked into snapshot: {leaked}"


# ── 2. Simulator-Only Sections Stripped ──

def test_no_simulator_sections_in_output(snapshot):
    """Simulator-only top-level sections must not appear in the snapshot."""
    forbidden_keys = {
        "failure_domains", "vendor_profiles", "failure_propagation_models",
        "observability_sources", "operational_imperfections", "difficulty_profiles",
        "customer_impact_model", "fikracore_operational_view",
        "scenario_catalog_contract", "scenario_generator_contract",
        "example_hidden_causal_paths",
    }
    for key in forbidden_keys:
        assert key not in snapshot, f"Simulator-only section '{key}' found in snapshot"


def test_entity_fields_stripped(snapshot):
    """Entity-level simulator fields (failure_domains, vendor_profile) must be stripped."""
    for page in snapshot["pages"]:
        fm = page.get("frontmatter", {})
        assert "failure_domains" not in fm, f"failure_domains found in {page['slug']}"
        assert "vendor_profile" not in fm, f"vendor_profile found in {page['slug']}"


# ── 3. reject_truth() Safety ──

def test_reject_truth_passes(snapshot):
    """The ingested snapshot must pass the reject_truth() safety check."""
    provider_data = {
        "brain": snapshot["brain"],
        "snapshot_version": snapshot["snapshot_version"],
        "pages": snapshot["pages"],
        "relationships": snapshot["relationships"],
    }
    # Should not raise
    reject_truth(provider_data)


def test_no_simulator_world_provenance(snapshot):
    """No relationship should have 'SIMULATOR_WORLD' as provenance."""
    for rel in snapshot["relationships"]:
        assert rel.get("provenance") != "SIMULATOR_WORLD", (
            f"Relationship {rel['relationship_id']} has SIMULATOR_WORLD provenance"
        )
        assert "simulator" not in rel.get("provenance", "").lower(), (
            f"Relationship {rel['relationship_id']} has simulator-tainted provenance"
        )


# ── 4. FrozenTelecomBrainProvider Compatibility ──

def test_frozen_provider_compatible(snapshot, tmp_path):
    """Snapshot must be loadable by FrozenTelecomBrainProvider."""
    snapshot_path = tmp_path / "test-snapshot.json"
    write_snapshot(snapshot, snapshot_path)

    # FrozenTelecomBrainProvider expects exactly: brain, snapshot_version, pages, relationships
    with open(snapshot_path) as f:
        data = json.load(f)

    assert set(data.keys()) == {"brain", "snapshot_version", "pages", "relationships"}
    assert data["brain"] == "telecombrain"

    # Verify it loads without error
    provider = FrozenTelecomBrainProvider(snapshot_path)
    assert provider.metadata["brain"] == "telecombrain"


def test_frozen_provider_page_retrieval(snapshot, tmp_path):
    """Pages loaded via FrozenTelecomBrainProvider must be retrievable by slug."""
    snapshot_path = tmp_path / "test-snapshot.json"
    write_snapshot(snapshot, snapshot_path)

    provider = FrozenTelecomBrainProvider(snapshot_path)

    # UPF should be findable
    page = provider.get_page("SA5G:UPF:003")
    assert page is not None
    assert page["slug"] == "SA5G:UPF:003"

    # AMF should be findable
    page = provider.get_page("SA5G:AMF:001")
    assert page is not None


def test_frozen_provider_traversal(snapshot, tmp_path):
    """Graph traversal via FrozenTelecomBrainProvider must work on ingested data."""
    snapshot_path = tmp_path / "test-snapshot.json"
    write_snapshot(snapshot, snapshot_path)

    provider = FrozenTelecomBrainProvider(snapshot_path)

    # Traverse from UPF outward
    edges = provider.traverse("SA5G:UPF:003", depth=1, direction="out")
    assert len(edges) > 0, "UPF should have outgoing relationships"

    # Traverse from AMF outward
    edges = provider.traverse("SA5G:AMF:001", depth=1, direction="out")
    assert len(edges) > 0, "AMF should have outgoing relationships"


# ── 5. Known Operational Relationships Included ──

def test_known_relationships_included(snapshot, reference_network_path):
    """All known operational relationships must be present in the snapshot."""
    with open(reference_network_path) as f:
        raw = yaml.safe_load(f)

    known_ids = set(
        raw.get("fikracore_operational_view", {}).get("known_relationship_ids", [])
    )
    assert len(known_ids) > 0, "Test requires known relationships to be defined"

    ingested_rel_ids = {r["relationship_id"] for r in snapshot["relationships"]}
    missing = known_ids - ingested_rel_ids

    assert len(missing) == 0, f"Known relationships missing from snapshot: {missing}"


# ── 6. Entity & Relationship Counts ──

def test_entity_count(snapshot, reference_network_path):
    """Entity count must match reference network (entities + regions + sites + service chains)."""
    with open(reference_network_path) as f:
        raw = yaml.safe_load(f)

    expected_entities = len(raw.get("entities", []))
    expected_regions = len(raw.get("regions", []))
    expected_sites = len(raw.get("sites", []))
    expected_services = len(raw.get("service_chains", []))

    total_expected = expected_entities + expected_regions + expected_sites + expected_services
    actual = len(snapshot["pages"])

    assert actual == total_expected, (
        f"Page count mismatch: expected {total_expected} "
        f"(entities={expected_entities}, regions={expected_regions}, "
        f"sites={expected_sites}, services={expected_services}), got {actual}"
    )


def test_relationship_count(snapshot, reference_network_path):
    """Relationship count must include known operational relationships + service support links."""
    with open(reference_network_path) as f:
        raw = yaml.safe_load(f)

    known_ids = set(
        raw.get("fikracore_operational_view", {}).get("known_relationship_ids", [])
    )
    expected_services = len(raw.get("service_chains", []))
    expected_total = len(known_ids) + expected_services
    actual = len(snapshot["relationships"])

    assert actual == expected_total, (
        f"Relationship count mismatch: expected {expected_total} "
        f"(known={len(known_ids)}, service_links={expected_services}), got {actual}"
    )


def test_all_canonical_domains_present(snapshot):
    """All 8 canonical gbrain domains must be represented across the snapshot pages."""
    canonical_domains = {
        "Mobile Core", "Transport", "RAN", "IMS", "OCS", "OSS/BSS", "Cloud/NFVI", "Cross-Domain Operations"
    }
    found_domains = {p["domain"] for p in snapshot["pages"]}
    missing = canonical_domains - found_domains
    assert len(missing) == 0, f"Missing canonical domain pages: {missing}"


# ── 7. Service Chain Metadata ──

def test_service_chains_present(snapshot):
    """Service chain metadata must be present in snapshot."""
    chains = snapshot.get("service_chains", [])
    assert len(chains) > 0, "Service chains should be included"

    # Each chain should have required fields
    for chain in chains:
        assert "service_id" in chain
        assert "name" in chain
        assert "nodes" in chain


def test_service_chains_no_causal_paths(snapshot):
    """Service chain metadata must not contain causal/hidden path information."""
    chains = snapshot.get("service_chains", [])
    for chain in chains:
        assert "causal_chain" not in chain
        assert "hidden" not in json.dumps(chain).lower()
        assert "root_condition" not in chain


# ── 8. Provenance Tagging ──

def test_provenance_tag(snapshot):
    """All ingested relationships must have operator-inventory-baseline provenance."""
    for rel in snapshot["relationships"]:
        assert rel["provenance"] == "operator-inventory-baseline", (
            f"Relationship {rel['relationship_id']} has wrong provenance: {rel['provenance']}"
        )


# ── 9. InMemoryKnowledgeProvider Compatibility ──

def test_in_memory_provider_compatible(snapshot):
    """Snapshot pages and relationships must be loadable by InMemoryKnowledgeProvider."""
    provider = InMemoryKnowledgeProvider(
        pages=snapshot["pages"],
        relationships=snapshot["relationships"],
        version=snapshot["snapshot_version"],
    )
    assert provider.metadata["brain"] == "telecombrain"

    # Search should work
    results = provider.search("UPF")
    assert len(results) > 0, "UPF should be searchable"


# ── 10. Dry Run Report ──

def test_dry_run_report(snapshot):
    """Dry run report must be generated without errors."""
    report = dry_run_report(snapshot)
    assert "Dry Run Report" in report
    assert "reject_truth()" in report
    assert len(report) > 200


# ── 11. Write Snapshot ──

def test_write_snapshot_metadata(snapshot, tmp_path):
    """write_snapshot must return valid metadata."""
    path = tmp_path / "out.json"
    meta = write_snapshot(snapshot, path)

    assert path.exists()
    assert "sha256" in meta
    assert meta["total_pages"] == len(snapshot["pages"])
    assert meta["total_relationships"] == len(snapshot["relationships"])


# ── 12. Version Label ──

def test_version_label(reference_network_path):
    """Custom version label must be propagated."""
    snap = ingest_reference_topology(reference_network_path, version_label="v3.0-custom")
    assert snap["snapshot_version"] == "v3.0-custom"


def test_default_version_label(reference_network_path):
    """Default version label must start with v2.0-full-topology."""
    snap = ingest_reference_topology(reference_network_path)
    assert snap["snapshot_version"].startswith("v2.0-full-topology")


# ── 13. Restore Snapshot & Obsolete MVP Cleanup ──

def test_restore_snapshot_clean_and_mcp_format(tmp_path, monkeypatch):
    """Restoring a snapshot must clean obsolete MVP pages and use valid put_page schema."""
    from engine_stack.engines.telecom_brain.investigation.snapshot import SnapshotManager

    snap_file = tmp_path / "test-snap.json"
    snap_data = {
        "brain": "telecombrain",
        "snapshot_version": "v-test",
        "pages": [
            {"slug": "NODE:001", "title": "Node 1", "type": "network-function", "domain": "Mobile Core"},
            {"slug": "NODE:002", "title": "Node 2", "type": "network-function", "domain": "RAN"},
        ],
        "relationships": [
            {"source": "NODE:001", "target": "NODE:002", "link_type": "depends-on"}
        ],
    }
    snap_file.write_text(json.dumps(snap_data))

    class MockProvider:
        contracts = {
            "list_pages": {"properties": {"offset": {}, "limit": {}}},
            "delete_page": {"properties": {"slug": {}}, "required": ["slug"]},
            "put_page": {"properties": {"slug": {}, "content": {}}, "required": ["slug", "content"]},
            "add_link": {"properties": {"from": {}, "to": {}, "link_type": {}}, "required": ["from", "to"]},
        }

        def __init__(self, *args, **kwargs):
            self.calls = []
            self.deleted = []
            self.put = {}
            self.links = []

        def _call(self, name, args):
            self.calls.append((name, args))
            if name == "list_pages":
                return [{"slug": "OLD:MVP:001"}, {"slug": "NODE:001"}]
            elif name == "delete_page":
                self.deleted.append(args["slug"])
                return {"status": "ok"}
            elif name == "put_page":
                assert set(args.keys()) == {"slug", "content"}
                assert args["content"].startswith("---\n")
                self.put[args["slug"]] = args["content"]
                return {"status": "ok"}
            elif name == "add_link":
                self.links.append((args["from"], args["to"], args["link_type"]))
                return {"status": "ok"}

    mock = MockProvider()
    monkeypatch.setattr(
        "engine_stack.engines.telecom_brain.investigation.knowledge.GbrainTelecomBrainProvider",
        lambda *args, **kwargs: mock,
    )

    sm = SnapshotManager(snapshots_dir=tmp_path)
    res = sm.restore_snapshot(snap_file, clean=True)

    assert res["status"] == "success"
    assert res["mcp_cleaned_pages"] == 1
    assert "OLD:MVP:001" in mock.deleted
    assert res["mcp_restored_pages"] == 2
    assert "NODE:001" in mock.put
    assert "NODE:002" in mock.put
    assert res["mcp_restored_links"] == 1
    assert (tmp_path / "gbrain-snapshot-active.json").exists()

