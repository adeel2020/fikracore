"""Reference Topology Ingestor — Loads operator baseline knowledge into gbrain.

Reads `reference_synthetic_network.yaml` and produces a clean, sanitized
FrozenTelecomBrainProvider-compatible snapshot containing ONLY the entities
and relationships that the Brain is authorized to know (Day-0 Baseline).

All entities, domains, services, sub-clusters, and TM Forum layers are mapped to
gbrain's canonical architecture:
- Domains: Mobile Core, Transport, RAN, IMS, OCS, OSS/BSS, Cloud/NFVI, Cross-Domain Operations
- Types: network-function, service, concept
- Planes: topology, observability, operations
- Layers: RM&O, SM&O, AIOps, CCM

Hidden gaps, epistemic blind spots, simulator-only metadata, and scenario
injection fields are strictly excluded. The output passes `reject_truth()`
and is fully compatible with the existing knowledge provider contract (§18, §53).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .evidence import reject_truth

logger = logging.getLogger("fikracore.topology_ingestor")

# ── Domain Canonical Mapping (Raw YAML domain -> gbrain Canonical Domain) ──
RAW_TO_CANONICAL_DOMAIN: dict[str, str] = {
    "RAN": "RAN",
    "NSA_5G": "RAN",
    "CS_CORE": "Mobile Core",
    "PS_3G": "Mobile Core",
    "EPC_4G": "Mobile Core",
    "SA_5G_CORE": "Mobile Core",
    "MOBILE_IMS": "IMS",
    "FIXED_IMS": "IMS",
    "IP_TRANSPORT": "Transport",
    "TRANSMISSION": "Transport",
    "GPON_FIXED_ACCESS": "Transport",
    "MPLS_CLOUD": "Transport",
    "CHARGING": "OCS",
    "IN_VENDOR_A": "OCS",
    "IN_VENDOR_B": "OCS",
    "IN_VENDOR_C": "OCS",
    "CRM": "OSS/BSS",
    "BSS": "OSS/BSS",
    "PROVISIONING": "OSS/BSS",
    "OSS": "OSS/BSS",
    "VAS": "OSS/BSS",
    "IT_CLOUD_INFRA": "Cloud/NFVI",
    "EXTERNAL": "Cross-Domain Operations",
    "INFRASTRUCTURE": "Cloud/NFVI",
}

# ── Prefix to Canonical Domain Mapping ──
PREFIX_TO_CANONICAL_DOMAIN: dict[str, str] = {
    "SA5G": "Mobile Core",
    "EPC": "Mobile Core",
    "PS3G": "Mobile Core",
    "CS": "Mobile Core",
    "RAN": "RAN",
    "NSA": "RAN",
    "TX": "Transport",
    "IP": "Transport",
    "MPLS": "Transport",
    "GPON": "Transport",
    "IMSM": "IMS",
    "IMSF": "IMS",
    "CHG": "OCS",
    "IN": "OCS",
    "CRM": "OSS/BSS",
    "BSS": "OSS/BSS",
    "PROV": "OSS/BSS",
    "OSS": "OSS/BSS",
    "VAS": "OSS/BSS",
    "INFRA": "Cloud/NFVI",
    "EXT": "Cross-Domain Operations",
    "REGION": "Cross-Domain Operations",
    "SITE": "Cross-Domain Operations",
}


def _get_sub_cluster_and_layer(domain: str, entity_type: str) -> tuple[str, str]:
    """Map canonical domain & entity_type to sub_cluster and TM Forum layer."""
    etype = entity_type.lower()
    if domain == "Mobile Core":
        if etype in ("amf", "smf", "nrf", "ausf", "udm", "mme", "hss", "pcf", "scp", "diameter_router", "msc_server", "hlr", "stp", "sgsn"):
            return "mobile_core.control_plane", "RM&O"
        return "mobile_core.user_plane", "RM&O"
    elif domain == "Transport":
        return "transport.topology", "RM&O"
    elif domain == "RAN":
        return "ran.topology", "RM&O"
    elif domain == "IMS":
        return "ims.sip_core", "RM&O"
    elif domain == "OCS":
        return "ocs.charging_gateways", "CCM"
    elif domain == "OSS/BSS":
        return "oss_bss.systems", "AIOps"
    elif domain == "Cloud/NFVI":
        return "cloud_nfvi.infrastructure", "RM&O"
    elif domain == "Cross-Domain Operations":
        return "cross_domain.dependencies", "RM&O"
    return "topology.general", "RM&O"


def _load_operational_view(network_data: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Extract known_relationship_ids and hidden_from_operational_view sets."""
    op_view = network_data.get("fikracore_operational_view", {})
    known_ids = set(op_view.get("known_relationship_ids", []))
    hidden_ids = set(op_view.get("hidden_from_operational_view", []))
    return known_ids, hidden_ids


def _normalize_link_type(raw_type: str) -> str:
    """Convert YAML relationship_type to gbrain link_type format."""
    return raw_type.lower().replace("_", "-")


def ingest_reference_topology(
    source_path: Path,
    *,
    version_label: str | None = None,
    include_service_chains: bool = True,
    include_aliases: bool = True,
) -> dict[str, Any]:
    """Parse reference_synthetic_network.yaml and produce a clean gbrain snapshot.

    Returns a dict with keys: brain, snapshot_version, pages, relationships
    that is directly compatible with FrozenTelecomBrainProvider.
    """
    with open(source_path, "r", encoding="utf-8") as f:
        network_data = yaml.safe_load(f)

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    version = version_label or f"v2.0-full-topology-{ts}"

    known_rel_ids, hidden_rel_ids = _load_operational_view(network_data)

    pages: list[dict[str, Any]] = []
    entity_ids: set[str] = set()

    # ── 1. Regions ──
    for region in network_data.get("regions", []):
        rid = region.get("region_id")
        if rid:
            entity_ids.add(rid)
            pages.append({
                "slug": rid,
                "title": region.get("name", rid),
                "type": "concept",
                "domain": "Cross-Domain Operations",
                "plane": "topology",
                "sub_cluster": "cross_domain.regions",
                "tmforum_layer": "RM&O",
                "frontmatter": {
                    "entity_type": "region",
                    "entity_id": rid,
                    "domain": "Cross-Domain Operations",
                },
            })

    # ── 2. Sites ──
    for site in network_data.get("sites", []):
        sid = site.get("site_id")
        if sid:
            entity_ids.add(sid)
            pages.append({
                "slug": sid,
                "title": site.get("name", sid),
                "type": "concept",
                "domain": "Cross-Domain Operations",
                "plane": "topology",
                "sub_cluster": "cross_domain.sites",
                "tmforum_layer": "RM&O",
                "frontmatter": {
                    "entity_type": site.get("site_type", "site"),
                    "entity_id": sid,
                    "domain": "Cross-Domain Operations",
                    "region": site.get("region"),
                },
            })

    # ── 3. Core Entities (Network Functions) ──
    for ent in network_data.get("entities", []):
        eid = ent.get("entity_id") or ent.get("id")
        if not eid:
            continue
        entity_ids.add(eid)

        raw_dom = ent.get("domain", "EXTERNAL")
        prefix = eid.split(":")[0].split("-")[0].upper()
        canon_dom = RAW_TO_CANONICAL_DOMAIN.get(raw_dom) or PREFIX_TO_CANONICAL_DOMAIN.get(prefix, "Cross-Domain Operations")
        raw_etype = ent.get("entity_type", ent.get("type", "network-function"))
        sub_cluster, tmforum_layer = _get_sub_cluster_and_layer(canon_dom, raw_etype)

        frontmatter = {
            "entity_type": raw_etype,
            "entity_id": eid,
            "domain": canon_dom,
            "raw_domain": raw_dom,
            "site": ent.get("site"),
            "region": ent.get("region"),
        }
        if ent.get("canonical_name"):
            frontmatter["canonical_name"] = ent["canonical_name"]

        pages.append({
            "slug": eid,
            "title": ent.get("canonical_name", eid),
            "type": "network-function",
            "domain": canon_dom,
            "plane": "topology",
            "sub_cluster": sub_cluster,
            "tmforum_layer": tmforum_layer,
            "frontmatter": frontmatter,
        })

    # ── 4. Service Chains ──
    service_chain_summary: list[dict[str, Any]] = []
    if include_service_chains:
        for chain in network_data.get("service_chains", []):
            sid = chain.get("service_id")
            if not sid:
                continue
            service_slug = f"services/{sid}"
            entity_ids.add(service_slug)

            # Determine service domain
            if any(k in sid for k in ("mobile", "5g", "3g", "lte", "sim", "subscriber")):
                s_dom = "Mobile Core"
            elif any(k in sid for k in ("ims", "volte", "voice")):
                s_dom = "IMS"
            elif any(k in sid for k in ("charging", "prepaid", "recharge", "balance")):
                s_dom = "OCS"
            elif any(k in sid for k in ("gpon", "broadband", "vpn", "peering")):
                s_dom = "Transport"
            else:
                s_dom = "OSS/BSS"

            pages.append({
                "slug": service_slug,
                "title": chain.get("name", sid),
                "type": "service",
                "domain": s_dom,
                "plane": "topology",
                "sub_cluster": "services.cfs",
                "tmforum_layer": "SM&O",
                "frontmatter": {
                    "entity_type": "service",
                    "entity_id": service_slug,
                    "domain": s_dom,
                    "service_id": sid,
                    "regions": chain.get("regions", []),
                    "customer_segments": chain.get("customer_segments", []),
                },
            })

            service_chain_summary.append({
                "service_id": sid,
                "name": chain.get("name"),
                "regions": chain.get("regions", []),
                "customer_segments": chain.get("customer_segments", []),
                "path_count": len(chain.get("paths", [])),
                "nodes": sorted(set(
                    node for path in chain.get("paths", []) for node in path
                )),
            })

    # ── 5. Aliases ──
    alias_map: dict[str, list[dict[str, Any]]] = {}
    if include_aliases:
        for alias in network_data.get("aliases", []):
            eid = alias.get("entity_id")
            if eid:
                alias_map.setdefault(eid, []).append({
                    "source": alias.get("source"),
                    "name": alias.get("name"),
                    "confidence": alias.get("confidence", 0.5),
                })
        for page in pages:
            slug = page["slug"]
            if slug in alias_map:
                page["frontmatter"]["aliases"] = alias_map[slug]

    # ── 6. Relationships (Excluding Hidden Gaps) ──
    relationships: list[dict[str, Any]] = []
    all_rels = network_data.get("relationships", [])

    for rel in all_rels:
        rid = rel.get("relationship_id") or rel.get("id")
        if not rid:
            continue

        if rid in hidden_rel_ids:
            logger.info("Excluded hidden relationship (epistemic gap): %s", rid)
            continue

        if known_rel_ids and rid not in known_rel_ids:
            logger.info("Excluded relationship not in operational view: %s", rid)
            continue

        src = rel.get("source_entity") or rel.get("source")
        tgt = rel.get("target_entity") or rel.get("target")
        link_type = _normalize_link_type(
            rel.get("relationship_type") or rel.get("link_type") or "depends-on"
        )

        if not (src and tgt):
            continue

        relationships.append({
            "relationship_id": rid,
            "source": src,
            "target": tgt,
            "link_type": link_type,
            "state": "CONFIRMED",
            "confidence": rel.get("confidence", 1.0),
            "provenance": "operator-inventory-baseline",
        })

    # Add service support relationships connecting services to their main nodes
    if include_service_chains:
        for idx, chain in enumerate(network_data.get("service_chains", []), 1):
            sid = chain.get("service_id")
            if not sid:
                continue
            service_slug = f"services/{sid}"
            paths = chain.get("paths", [])
            if paths and len(paths[0]) > 0:
                first_node = paths[0][0]
                relationships.append({
                    "relationship_id": f"REL-SVC-SUP-{idx:03d}",
                    "source": first_node,
                    "target": service_slug,
                    "link_type": "supports-service",
                    "state": "CONFIRMED",
                    "confidence": 1.0,
                    "provenance": "operator-inventory-baseline",
                })

    # ── 7. Build final snapshot ──
    snapshot = {
        "brain": "telecombrain",
        "snapshot_version": version,
        "pages": pages,
        "relationships": relationships,
    }

    if service_chain_summary:
        snapshot["service_chains"] = service_chain_summary

    # ── 8. Safety — run reject_truth on provider snapshot ──
    provider_snapshot = {
        "brain": snapshot["brain"],
        "snapshot_version": snapshot["snapshot_version"],
        "pages": snapshot["pages"],
        "relationships": snapshot["relationships"],
    }
    reject_truth(provider_snapshot)

    logger.info(
        "Topology ingestion complete: %d pages, %d relationships, %d service chains",
        len(pages), len(relationships), len(service_chain_summary),
    )

    return snapshot


def write_snapshot(
    snapshot: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Write the ingested snapshot to disk as a FrozenTelecomBrainProvider-compatible JSON file."""
    provider_data = {
        "brain": snapshot["brain"],
        "snapshot_version": snapshot["snapshot_version"],
        "pages": snapshot["pages"],
        "relationships": snapshot["relationships"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(provider_data, indent=2, ensure_ascii=False)
    output_path.write_text(raw, encoding="utf-8")

    sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    meta = {
        "output_path": str(output_path),
        "snapshot_version": snapshot["snapshot_version"],
        "sha256": sha256,
        "total_pages": len(snapshot["pages"]),
        "total_relationships": len(snapshot["relationships"]),
        "total_service_chains": len(snapshot.get("service_chains", [])),
    }
    logger.info("Snapshot written to %s (sha256: %s)", output_path, sha256)
    return meta


def dry_run_report(snapshot: dict[str, Any]) -> str:
    """Generate a human-readable dry-run report summarizing the ingestion result."""
    pages = snapshot["pages"]
    rels = snapshot["relationships"]
    chains = snapshot.get("service_chains", [])

    type_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    for page in pages:
        ptype = page.get("type", "unknown")
        domain = page.get("domain", "unknown")
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    rel_type_counts: dict[str, int] = {}
    for rel in rels:
        lt = rel.get("link_type", "unknown")
        rel_type_counts[lt] = rel_type_counts.get(lt, 0) + 1

    lines = [
        "╭──────────────────────────────────────────────────────────────────────╮",
        "│         FikraCore Topology Ingestion — Dry Run Report               │",
        "├──────────────────────────────────────────────────────────────────────┤",
        f"│  Snapshot Version  : {snapshot['snapshot_version']:<47}│",
        f"│  Total Pages       : {len(pages):<47}│",
        f"│  Total Relationships: {len(rels):<46}│",
        f"│  Service Chains    : {len(chains):<47}│",
        "├──────────────────────────────────────────────────────────────────────┤",
        "│  Entity Types                                                       │",
        "├──────────────────────────────────────────────────────────────────────┤",
    ]
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"│    {etype:<34} {count:>4}                          │")

    lines += [
        "├──────────────────────────────────────────────────────────────────────┤",
        "│  Domains                                                            │",
        "├──────────────────────────────────────────────────────────────────────┤",
    ]
    for dom, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        lines.append(f"│    {dom:<34} {count:>4}                          │")

    lines += [
        "├──────────────────────────────────────────────────────────────────────┤",
        "│  Relationship Types                                                 │",
        "├──────────────────────────────────────────────────────────────────────┤",
    ]
    for rtype, count in sorted(rel_type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"│    {rtype:<34} {count:>4}                          │")

    lines += [
        "├──────────────────────────────────────────────────────────────────────┤",
        "│  ✔ reject_truth() passed — zero simulator secrets in output        │",
        "│  ✔ Hidden epistemic gaps excluded from relationships                │",
        "│  ✔ Simulator-only sections stripped                                 │",
        "╰──────────────────────────────────────────────────────────────────────╯",
    ]
    return "\n".join(lines)
