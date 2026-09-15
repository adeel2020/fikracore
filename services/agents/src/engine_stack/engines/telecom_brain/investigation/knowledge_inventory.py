"""FikraCore Step 4.7 Knowledge Inventory Collector & Data Models.

Inspects, enumerates, and summarizes live knowledge stored in telecombrain
over the live gbrain MCP protocol. Strictly read-only; never mutates the brain.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("fikracore.knowledge_inventory")


# ==============================================================================
# Domain Constants & Normalization
# ==============================================================================

DOMAIN_CANONICAL_NAMES = {
    "mobile-core": "Mobile Core",
    "transport": "Transport",
    "ims": "IMS",
    "ocs": "OCS",
    "ran": "RAN",
    "oss-bss": "OSS/BSS",
    "cloud-nfvi": "Cloud/NFVI",
    "observability": "Observability / Telemetry",
}

RELATIONSHIP_HUMAN_NAMES = {
    "depends_on": "Depends on",
    "depends-on": "Depends on",
    "routes_through": "Routes through",
    "routes-through": "Routes through",
    "hosted_on": "Hosted on",
    "hosted-on": "Hosted on",
    "supports_service": "Supports service",
    "supports-service": "Supports service",
    "serves": "Serves",
    "monitored_by": "Monitored by",
    "monitored-by": "Monitored by",
    "fails_over_to": "Fails over to",
    "fails-over-to": "Fails over to",
    "involves": "Involves",
    "observed_on": "Observed on",
    "observed-on": "Observed on",
    "relates_to": "Relates to",
    "relates-to": "Relates to",
    "correlates_with": "Correlates with",
    "correlates-with": "Correlates with",
}


# ==============================================================================
# Data Models
# ==============================================================================

class KnowledgeState(str):
    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"
    STALE = "STALE"
    STATE_NOT_AVAILABLE = "STATE_NOT_AVAILABLE"


class GapClass(str):
    ORPHAN_ENTITY = "ORPHAN_ENTITY"
    UNRESOLVED_ALIAS = "UNRESOLVED_ALIAS"
    MISSING_RELATIONSHIP = "MISSING_RELATIONSHIP"
    SPARSE_DOMAIN = "SPARSE_DOMAIN"
    SPARSE_SERVICE = "SPARSE_SERVICE"
    STALE_KNOWLEDGE = "STALE_KNOWLEDGE"
    CANDIDATE_ONLY_KNOWLEDGE = "CANDIDATE_ONLY_KNOWLEDGE"
    INCOMPLETE_CROSS_DOMAIN_COVERAGE = "INCOMPLETE_CROSS_DOMAIN_COVERAGE"
    INCOMPLETE_SERVICE_MAPPING = "INCOMPLETE_SERVICE_MAPPING"


class KnowledgeGap(BaseModel):
    model_config = ConfigDict(extra="ignore")

    gap_class: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    entity_or_domain: str
    description: str
    recommendation: str


class EntityRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    slug: str
    title: str
    type: str
    domain: str
    knowledge_state: str = KnowledgeState.CONFIRMED
    updated_at: Optional[str] = None
    in_degree: int = 0
    out_degree: int = 0
    is_operational_orphan: bool = False
    evidence_count: int = 0


class LinkRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    from_slug: str
    link_type: str
    human_link_type: str
    to_slug: str
    source_domain: str
    target_domain: str
    is_cross_domain: bool = False


class KnowledgeInventorySummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    brain: str = "telecombrain"
    schema_identity: str = "mobile-core@0.1.0+2eea5e14"
    total_pages: int = 0
    total_unique_links: int = 0
    domains_count: int = 0
    services_count: int = 0
    network_functions_count: int = 0
    incidents_count: int = 0
    tickets_count: int = 0
    evidence_count: int = 0
    hypotheses_count: int = 0
    orphans_count: int = 0
    unresolved_aliases_count: int = 0
    stale_knowledge_count: int = 0
    overall_coverage_pct: float = 0.0
    overall_health_status: str = "Healthy"


class KnowledgeInventoryResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    brain: str = "telecombrain"
    schema_identity: str = "mobile-core@0.1.0+2eea5e14"
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provenance: Dict[str, Any] = Field(default_factory=dict)
    summary: KnowledgeInventorySummary = Field(default_factory=KnowledgeInventorySummary)
    page_types: Dict[str, int] = Field(default_factory=dict)
    link_types: Dict[str, int] = Field(default_factory=dict)
    domains: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    entities: List[EntityRecord] = Field(default_factory=list)
    unique_links: List[LinkRecord] = Field(default_factory=list)
    knowledge_states: Dict[str, int] = Field(default_factory=dict)
    coverage: Dict[str, Any] = Field(default_factory=dict)
    gaps: List[KnowledgeGap] = Field(default_factory=list)


# ==============================================================================
# Collector Implementation
# ==============================================================================

class KnowledgeInventoryCollector:
    """Collects and deduplicates knowledge inventory from telecombrain over MCP."""

    # Page types treated as operational entities when assessing orphans
    OPERATIONAL_TYPES = {
        "network-function",
        "domain-function",
        "service",
        "incident",
        "ticket-journey",
        "evidence",
    }

    # Standalone or non-operational types excluded from orphan classification
    EXCLUDED_ORPHAN_TYPES = {
        "concept",
        "note",
        "learning-note",
        "playbook",
        "procedure",
        "service-procedure",
        "story",
        "story-run",
        "query-asset",
        "observation",
        "remediation",
        "symptom",
        "incident-alias",
    }

    def __init__(
        self,
        provider: Any = None,
        stale_threshold_days: int = 30,
    ):
        self.provider = provider
        self.stale_threshold_days = stale_threshold_days

    def _ensure_provider(self):
        if self.provider is not None:
            return
        from .knowledge import GbrainTelecomBrainProvider
        self.provider = GbrainTelecomBrainProvider()

    def collect(self) -> KnowledgeInventoryResult:
        """Executes full live knowledge collection across all pages and links."""
        self._ensure_provider()
        now = datetime.now(timezone.utc)
        retrieved_at = now.isoformat()

        # 1. Paginating all pages (Section 20 safety)
        pages = self._paginate_all_pages()

        # 2. Get active schema and stats
        schema_identity = "mobile-core@0.1.0+2eea5e14"
        if hasattr(self.provider, "contracts") and "get_active_schema_pack" in self.provider.contracts:
            try:
                schema_identity = self.provider._call("get_active_schema_pack", {}) or schema_identity
            except Exception:
                pass

        # 3. Collect and deduplicate links (Section 21 safety)
        unique_links_set: Set[Tuple[str, str, str]] = set()
        links_list: List[LinkRecord] = []
        in_degree: Dict[str, int] = {p.get("slug", ""): 0 for p in pages}
        out_degree: Dict[str, int] = {p.get("slug", ""): 0 for p in pages}

        for page in pages:
            slug = page.get("slug", "")
            if not slug:
                continue

            # Query get_links
            try:
                page_links = self.provider._call("get_links", {"slug": slug}) or []
            except Exception:
                page_links = []

            for link in page_links:
                from_slug = link.get("from_slug") or slug
                to_slug = link.get("to_slug")
                link_type = link.get("link_type") or "relates-to"
                if not to_slug:
                    continue

                edge_key = (from_slug, link_type, to_slug)
                if edge_key not in unique_links_set:
                    unique_links_set.add(edge_key)
                    src_dom = self._detect_domain(from_slug)
                    tgt_dom = self._detect_domain(to_slug)
                    is_cross = (src_dom != tgt_dom and src_dom != "Other" and tgt_dom != "Other")
                    h_name = RELATIONSHIP_HUMAN_NAMES.get(link_type.lower(), link_type.replace("_", " ").title())

                    links_list.append(
                        LinkRecord(
                            from_slug=from_slug,
                            link_type=link_type,
                            human_link_type=h_name,
                            to_slug=to_slug,
                            source_domain=src_dom,
                            target_domain=tgt_dom,
                            is_cross_domain=is_cross,
                        )
                    )
                    out_degree[from_slug] = out_degree.get(from_slug, 0) + 1
                    in_degree[to_slug] = in_degree.get(to_slug, 0) + 1

        # 4. Process page types and domains
        page_types: Dict[str, int] = {}
        link_types: Dict[str, int] = {}
        for link in links_list:
            link_types[link.link_type] = link_types.get(link.link_type, 0) + 1

        domain_pages: Dict[str, List[Dict[str, Any]]] = {}
        domain_services: Dict[str, List[str]] = {}
        domain_nfs: Dict[str, List[str]] = {}

        entities: List[EntityRecord] = []
        knowledge_states: Dict[str, int] = {
            KnowledgeState.CONFIRMED: 0,
            KnowledgeState.INFERRED: 0,
            KnowledgeState.CANDIDATE: 0,
            KnowledgeState.STALE: 0,
            KnowledgeState.STATE_NOT_AVAILABLE: 0,
        }

        stale_count = 0
        orphans_count = 0
        unresolved_aliases: List[KnowledgeGap] = []
        alias_pages: List[Dict[str, Any]] = []

        all_slugs = {p.get("slug", "") for p in pages}

        for page in pages:
            slug = page.get("slug", "")
            p_type = page.get("type", "unknown")
            page_types[p_type] = page_types.get(p_type, 0) + 1

            dom = self._detect_domain(slug)
            if dom not in domain_pages:
                domain_pages[dom] = []
                domain_services[dom] = []
                domain_nfs[dom] = []
            domain_pages[dom].append(page)

            if p_type == "service":
                domain_services[dom].append(slug)
            elif p_type in ("network-function", "domain-function"):
                domain_nfs[dom].append(slug)
            elif p_type == "incident-alias":
                alias_pages.append(page)

            # Degree computation
            deg_in = in_degree.get(slug, 0)
            deg_out = out_degree.get(slug, 0)
            total_deg = deg_in + deg_out

            # Check orphan rule
            is_orphan = (p_type in self.OPERATIONAL_TYPES and total_deg == 0)
            if is_orphan:
                orphans_count += 1

            # Check staleness
            updated_at_str = page.get("updated_at")
            is_stale = False
            if updated_at_str:
                try:
                    up_dt = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                    age_days = (now - up_dt).days
                    if age_days > self.stale_threshold_days:
                        is_stale = True
                        stale_count += 1
                except Exception:
                    pass

            # Classify state
            k_state = KnowledgeState.CONFIRMED
            if is_stale:
                k_state = KnowledgeState.STALE
            elif p_type == "hypothesis":
                k_state = KnowledgeState.CANDIDATE
            elif p_type in ("observation", "correlation-cluster"):
                k_state = KnowledgeState.INFERRED

            knowledge_states[k_state] = knowledge_states.get(k_state, 0) + 1

            entities.append(
                EntityRecord(
                    slug=slug,
                    title=page.get("title", slug.split("/")[-1]),
                    type=p_type,
                    domain=dom,
                    knowledge_state=k_state,
                    updated_at=updated_at_str,
                    in_degree=deg_in,
                    out_degree=deg_out,
                    is_operational_orphan=is_orphan,
                )
            )

        # 5. Check unresolved aliases (Section 27)
        for ap in alias_pages:
            slug = ap.get("slug", "")
            target_slug = ap.get("target_slug") or slug.replace("incident-alias", "incident")
            if target_slug not in all_slugs:
                unresolved_aliases.append(
                    KnowledgeGap(
                        gap_class=GapClass.UNRESOLVED_ALIAS,
                        severity="MEDIUM",
                        entity_or_domain=slug,
                        description=f"Incident alias '{slug}' points to unresolved canonical target '{target_slug}'.",
                        recommendation=f"Update alias mapping for '{slug}' to a registered canonical incident.",
                    )
                )

        # 6. Domain Summary Objects
        domains_summary: Dict[str, Dict[str, Any]] = {}
        for dom, d_pages in domain_pages.items():
            nfs = domain_nfs.get(dom, [])
            svcs = domain_services.get(dom, [])
            incidents = [p for p in d_pages if p.get("type") == "incident"]
            evidence = [p for p in d_pages if p.get("type") == "evidence"]
            hypotheses = [p for p in d_pages if p.get("type") == "hypothesis"]
            tickets = [p for p in d_pages if p.get("type") == "ticket-journey"]

            dom_slugs = {p.get("slug") for p in d_pages}
            dom_links = [l for l in links_list if l.from_slug in dom_slugs or l.to_slug in dom_slugs]

            domains_summary[dom] = {
                "name": dom,
                "entities_count": len(d_pages),
                "services_count": len(svcs),
                "network_functions_count": len(nfs),
                "incidents_count": len(incidents),
                "evidence_count": len(evidence),
                "hypotheses_count": len(hypotheses),
                "tickets_count": len(tickets),
                "relationships_count": len(dom_links),
                "coverage_status": "WELL_COVERED" if len(d_pages) >= 20 else ("PARTIALLY_COVERED" if len(d_pages) >= 5 else "SPARSE"),
            }

        # 7. Services Summary Objects
        services_summary: Dict[str, Dict[str, Any]] = {}
        for page in pages:
            if page.get("type") == "service":
                s_slug = page.get("slug", "")
                s_links = [l for l in links_list if l.from_slug == s_slug or l.to_slug == s_slug]
                services_summary[s_slug] = {
                    "slug": s_slug,
                    "title": page.get("title", s_slug),
                    "domain": self._detect_domain(s_slug),
                    "relationships_count": len(s_links),
                    "supporting_functions": [l.from_slug for l in s_links if l.link_type in ("supports_service", "serves", "depends_on")],
                }

        # 8. Identify Initial Gaps
        gaps: List[KnowledgeGap] = list(unresolved_aliases)

        for ent in entities:
            if ent.is_operational_orphan:
                gaps.append(
                    KnowledgeGap(
                        gap_class=GapClass.ORPHAN_ENTITY,
                        severity="LOW",
                        entity_or_domain=ent.slug,
                        description=f"Operational entity '{ent.title}' ({ent.type}) has no incoming or outgoing topology relationships.",
                        recommendation=f"Add dependency or service link to connect '{ent.slug}' into the operational graph.",
                    )
                )

        for dom, dom_data in domains_summary.items():
            if dom_data["coverage_status"] == "SPARSE" and dom not in ("Other", "Observability / Telemetry"):
                gaps.append(
                    KnowledgeGap(
                        gap_class=GapClass.SPARSE_DOMAIN,
                        severity="MEDIUM",
                        entity_or_domain=dom,
                        description=f"Domain '{dom}' has sparse representation ({dom_data['entities_count']} entities).",
                        recommendation=f"Ingest topology and service definitions for domain '{dom}'.",
                    )
                )

        # 9. Cross-Domain Coverage Gaps (§24)
        cross_domain_counts: Dict[str, int] = {}
        for l in links_list:
            if l.is_cross_domain:
                pair = f"{l.source_domain} ↔ {l.target_domain}"
                cross_domain_counts[pair] = cross_domain_counts.get(pair, 0) + 1

        expected_pairs = [
            ("Mobile Core", "Transport"),
            ("Mobile Core", "OCS"),
            ("IMS", "Transport"),
        ]
        for src, tgt in expected_pairs:
            pair_forward = f"{src} ↔ {tgt}"
            pair_reverse = f"{tgt} ↔ {src}"
            total_cross = cross_domain_counts.get(pair_forward, 0) + cross_domain_counts.get(pair_reverse, 0)
            if total_cross == 0:
                gaps.append(
                    KnowledgeGap(
                        gap_class=GapClass.INCOMPLETE_CROSS_DOMAIN_COVERAGE,
                        severity="HIGH",
                        entity_or_domain=f"{src} ↔ {tgt}",
                        description=f"Zero cross-domain dependency links between '{src}' and '{tgt}'.",
                        recommendation=f"Define transport routing and inter-domain links connecting {src} functions to {tgt}.",
                    )
                )

        # 10. Summary Object
        total_p = len(pages)
        total_l = len(links_list)
        summary = KnowledgeInventorySummary(
            brain="telecombrain",
            schema_identity=str(schema_identity) if isinstance(schema_identity, str) else "mobile-core@0.1.0+2eea5e14",
            total_pages=total_p,
            total_unique_links=total_l,
            domains_count=len(domains_summary),
            services_count=len(services_summary),
            network_functions_count=sum(d["network_functions_count"] for d in domains_summary.values()),
            incidents_count=page_types.get("incident", 0),
            tickets_count=page_types.get("ticket-journey", 0),
            evidence_count=page_types.get("evidence", 0),
            hypotheses_count=page_types.get("hypothesis", 0),
            orphans_count=orphans_count,
            unresolved_aliases_count=len(unresolved_aliases),
            stale_knowledge_count=stale_count,
            overall_coverage_pct=round(min(100.0, (total_l / max(1, total_p)) * 40.0), 1),
            overall_health_status="Healthy" if orphans_count <= 5 and len(unresolved_aliases) == 0 else "Needs Attention",
        )

        return KnowledgeInventoryResult(
            brain="telecombrain",
            schema_identity=summary.schema_identity,
            retrieved_at=retrieved_at,
            provenance={
                "source": "gbrain-mcp",
                "endpoint": getattr(self.provider, "url", "http://localhost:3131/mcp"),
                "provider_type": type(self.provider).__name__,
                "retrieved_at": retrieved_at,
            },
            summary=summary,
            page_types=page_types,
            link_types=link_types,
            domains=domains_summary,
            services=services_summary,
            entities=entities,
            unique_links=links_list,
            knowledge_states=knowledge_states,
            coverage={"cross_domain_links": cross_domain_counts},
            gaps=gaps,
        )

    def _paginate_all_pages(self) -> List[Dict[str, Any]]:
        """Paginates all pages via list_pages following next offset/limit until exhausted."""
        all_pages: List[Dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            try:
                batch = self.provider._call("list_pages", {"offset": offset, "limit": limit})
            except Exception as exc:
                if not all_pages:
                    raise RuntimeError(f"KNOWLEDGE_INVENTORY_MCP_FAILURE: list_pages failed: {exc}") from exc
                break

            if not batch or not isinstance(batch, list):
                break

            all_pages.extend(batch)
            if len(batch) < limit:
                break
            offset += len(batch)

        return all_pages

    @staticmethod
    def _detect_domain(slug: str) -> str:
        """Detects high-level telecom domain from canonical slug path or prefix."""
        parts = slug.lower().split("/")
        if not parts:
            return "Other"

        if "mobile-core" in parts:
            return "Mobile Core"
        if "transport" in parts:
            return "Transport"
        if "ims" in parts:
            return "IMS"
        if "ocs" in parts:
            return "OCS"
        if "ran" in parts:
            return "RAN"
        if "oss-bss" in parts or "oss" in parts or "bss" in parts:
            return "OSS/BSS"
        if "grafana" in parts or "observability" in parts or "telemetry" in parts:
            return "Observability / Telemetry"

        first = parts[0]
        if first in DOMAIN_CANONICAL_NAMES:
            return DOMAIN_CANONICAL_NAMES[first]

        return "Other"
