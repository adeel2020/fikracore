"""FikraCore Step 4.7 Knowledge Coverage Analyzer & Artifact Generator.

Calculates transparent coverage metrics across domains and services,
identifies cross-domain and service-topology gaps, and generates
markdown and JSON artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from .knowledge_inventory import (
    KnowledgeInventoryResult,
    KnowledgeGap,
    GapClass,
)


class DomainCoverageScore(BaseModel):
    model_config = ConfigDict(extra="ignore")

    domain: str
    entity_count: int
    relationship_count: int
    service_count: int
    network_function_count: int
    entity_coverage_pct: float
    relationship_coverage_pct: float
    service_mapping_coverage_pct: float
    evidence_coverage_pct: float
    validated_knowledge_pct: float
    composite_score_pct: float
    coverage_label: str  # "WELL_COVERED", "PARTIALLY_COVERED", "SPARSE", "UNKNOWN"


class CrossDomainPairCoverage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source_domain: str
    target_domain: str
    link_count: int
    status: str  # "CONNECTED", "SPARSE", "UNLINKED"


class TelemetryInstrumentationScore(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_telemetry_entities: int = 0
    loki_log_streams: int = 0
    prometheus_metric_streams: int = 0
    trace_spans: int = 0
    alert_rules: int = 0
    monitored_entities_count: int = 0
    telemetry_links_count: int = 0
    instrumentation_coverage_pct: float = 0.0
    status: str = "INSTRUMENTED"


class ServiceTopologyCoverage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    service_slug: str
    service_name: str
    domain: str
    supporting_functions: List[str]
    has_transport_path: bool
    has_charging_dependency: bool
    has_monitoring_dependency: bool
    completeness_score_pct: float


class CoverageReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    overall_composite_score_pct: float
    overall_status: str
    scoring_formula: str = (
        "25% entity_cov + 25% rel_cov + 20% service_cov + 15% evidence_cov + 15% validated_cov"
    )
    domain_scores: Dict[str, DomainCoverageScore] = Field(default_factory=dict)
    telemetry_instrumentation: Optional[TelemetryInstrumentationScore] = None
    cross_domain_matrix: List[CrossDomainPairCoverage] = Field(default_factory=list)
    service_topologies: List[ServiceTopologyCoverage] = Field(default_factory=list)
    top_gaps: List[KnowledgeGap] = Field(default_factory=list)


class KnowledgeCoverageAnalyzer:
    """Analyzes knowledge inventory to compute coverage and generate reports."""

    REFERENCE_DOMAIN_ENTITY_BASELINES = {
        "Mobile Core": 30,
        "Transport": 15,
        "IMS": 12,
        "OCS": 10,
        "RAN": 20,
        "OSS/BSS": 10,
        "Cross-Domain Operations": 5,
    }

    EXPECTED_CROSS_DOMAIN_PAIRS = [
        ("Mobile Core", "Transport"),
        ("Mobile Core", "OCS"),
        ("IMS", "Transport"),
        ("Mobile Core", "RAN"),
        ("Mobile Core", "IMS"),
    ]

    def __init__(self, inventory: KnowledgeInventoryResult):
        self.inventory = inventory

    def analyze(self) -> CoverageReport:
        """Computes transparent coverage scores across all dimensions (§14, §48)."""
        domain_scores: Dict[str, DomainCoverageScore] = {}
        total_entities = len(self.inventory.entities)

        # 1. Compute per-domain coverage scores
        for dom, dom_data in self.inventory.domains.items():
            e_cnt = dom_data["entities_count"]
            r_cnt = dom_data["relationships_count"]
            s_cnt = dom_data["services_count"]
            nf_cnt = dom_data["network_functions_count"]
            ev_cnt = dom_data["evidence_count"]

            expected_e = self.REFERENCE_DOMAIN_ENTITY_BASELINES.get(dom, 10)
            entity_cov = min(1.0, e_cnt / max(1, expected_e)) * 100.0

            # Entities with links
            dom_entities = [e for e in self.inventory.entities if e.domain == dom]
            linked_e = [e for e in dom_entities if (e.in_degree + e.out_degree) > 0]
            rel_cov = (len(linked_e) / max(1, len(dom_entities))) * 100.0 if dom_entities else 0.0

            # Services with functions
            dom_svcs = [s for s in self.inventory.services.values() if s.get("domain") == dom]
            mapped_svcs = [s for s in dom_svcs if len(s.get("supporting_functions", [])) > 0]
            service_cov = (len(mapped_svcs) / max(1, len(dom_svcs))) * 100.0 if dom_svcs else (100.0 if s_cnt == 0 else 0.0)

            # Evidence coverage
            incidents_in_dom = [e for e in dom_entities if e.type == "incident"]
            ev_in_dom = [e for e in dom_entities if e.type == "evidence"]
            evidence_cov = 100.0 if ev_in_dom and incidents_in_dom else (50.0 if ev_in_dom else 0.0)

            # Validated knowledge coverage
            confirmed_in_dom = [e for e in dom_entities if e.knowledge_state == "CONFIRMED"]
            validated_cov = (len(confirmed_in_dom) / max(1, len(dom_entities))) * 100.0 if dom_entities else 0.0

            # Weighted formula (§14)
            composite = (
                0.25 * entity_cov
                + 0.25 * rel_cov
                + 0.20 * service_cov
                + 0.15 * evidence_cov
                + 0.15 * validated_cov
            )

            if composite >= 75.0:
                label = "WELL_COVERED"
            elif composite >= 40.0:
                label = "PARTIALLY_COVERED"
            elif e_cnt > 0:
                label = "SPARSE"
            else:
                label = "UNKNOWN"

            domain_scores[dom] = DomainCoverageScore(
                domain=dom,
                entity_count=e_cnt,
                relationship_count=r_cnt,
                service_count=s_cnt,
                network_function_count=nf_cnt,
                entity_coverage_pct=round(entity_cov, 1),
                relationship_coverage_pct=round(rel_cov, 1),
                service_mapping_coverage_pct=round(service_cov, 1),
                evidence_coverage_pct=round(evidence_cov, 1),
                validated_knowledge_pct=round(validated_cov, 1),
                composite_score_pct=round(composite, 1),
                coverage_label=label,
            )

        # 2. Cross-domain coverage (§24) - Physical Interfaces & Cross-Domain Incident Bridges
        cross_matrix: List[CrossDomainPairCoverage] = []
        links = self.inventory.unique_links

        # Index domains connected by cross-domain incidents/correlations
        incident_connected_domains: Dict[str, Set[str]] = {}
        for l in links:
            if l.source_domain == "Cross-Domain Operations" and l.target_domain in ("Mobile Core", "Transport", "RAN", "OCS", "IMS"):
                incident_connected_domains.setdefault(l.from_slug, set()).add(l.target_domain)

        for src, tgt in self.EXPECTED_CROSS_DOMAIN_PAIRS:
            direct_cnt = sum(
                1 for l in links
                if (not getattr(l, "is_telemetry_link", False))
                and ((l.source_domain == src and l.target_domain == tgt)
                or (l.source_domain == tgt and l.target_domain == src))
            )
            # Count incidents that bridge both domains
            bridge_cnt = sum(1 for inc, doms in incident_connected_domains.items() if src in doms and tgt in doms)
            cnt = direct_cnt + bridge_cnt

            status = "CONNECTED" if cnt >= 5 else ("SPARSE" if cnt > 0 else "UNLINKED")
            cross_matrix.append(
                CrossDomainPairCoverage(
                    source_domain=src,
                    target_domain=tgt,
                    link_count=cnt,
                    status=status,
                )
            )

        # 3. Telemetry & Observability Layer Coverage (§35)
        telem_ents = [e for e in self.inventory.entities if getattr(e, "plane", "") == "observability" or "grafana" in e.slug or e.type in ("evidence", "kpi", "kpi-event", "observation")]
        loki_logs = sum(1 for e in telem_ents if "loki" in e.slug or "log" in e.slug)
        prom_metrics = sum(1 for e in telem_ents if "prom" in e.slug or "metric" in e.slug or e.type == "kpi")
        tempo_traces = sum(1 for e in telem_ents if "tempo" in e.slug or "trace" in e.slug)
        alerts = sum(1 for e in telem_ents if "alert" in e.slug or "alarm" in e.slug)
        
        telem_links = [l for l in links if getattr(l, "is_telemetry_link", False) or "grafana" in l.from_slug or "grafana" in l.to_slug]
        monitored_nodes = {l.to_slug for l in telem_links} | {l.from_slug for l in telem_links if "grafana" not in l.from_slug}
        op_nodes = [e for e in self.inventory.entities if e.type in ("network-function", "domain-function", "service")]
        inst_cov = min(100.0, (len(monitored_nodes) / max(1, len(op_nodes))) * 100.0) if op_nodes else 100.0
        
        telem_score = TelemetryInstrumentationScore(
            total_telemetry_entities=len(telem_ents),
            loki_log_streams=loki_logs,
            prometheus_metric_streams=prom_metrics,
            trace_spans=tempo_traces,
            alert_rules=alerts,
            monitored_entities_count=len(monitored_nodes),
            telemetry_link_count=len(telem_links),
            instrumentation_coverage_pct=round(inst_cov, 1),
            status="INSTRUMENTED" if inst_cov >= 60.0 else "PARTIALLY_INSTRUMENTED",
        )

        # 4. Service topology coverage (§35)
        service_topologies: List[ServiceTopologyCoverage] = []
        for s_slug, s_info in self.inventory.services.items():
            title = s_info.get("title", s_slug)
            dom = s_info.get("domain", "Other")
            funcs = s_info.get("supporting_functions", [])

            # Check links related to this service
            svc_links = [l for l in links if l.from_slug == s_slug or l.to_slug == s_slug]
            has_transport = any(l.target_domain == "Transport" or l.source_domain == "Transport" for l in svc_links)
            has_charging = any("ocs" in (l.to_slug + l.from_slug).lower() for l in svc_links)
            has_mon = any(getattr(l, "is_telemetry_link", False) or "grafana" in (l.to_slug + l.from_slug).lower() for l in svc_links)

            score = 25.0
            if funcs:
                score += 25.0
            if has_transport:
                score += 25.0
            if has_mon:
                score += 25.0

            service_topologies.append(
                ServiceTopologyCoverage(
                    service_slug=s_slug,
                    service_name=title,
                    domain=dom,
                    supporting_functions=funcs,
                    has_transport_path=has_transport,
                    has_charging_dependency=has_charging,
                    has_monitoring_dependency=has_mon,
                    completeness_score_pct=score,
                )
            )

        # 5. Overall composite score
        valid_scores = [s.composite_score_pct for s in domain_scores.values() if s.domain not in ("Other", "Unknown")]
        overall_pct = round(sum(valid_scores) / max(1, len(valid_scores)), 1) if valid_scores else 0.0

        if overall_pct >= 75.0:
            overall_status = "WELL_COVERED"
        elif overall_pct >= 40.0:
            overall_status = "PARTIALLY_COVERED"
        else:
            overall_status = "SPARSE"

        return CoverageReport(
            overall_composite_score_pct=overall_pct,
            overall_status=overall_status,
            domain_scores=domain_scores,
            telemetry_instrumentation=telem_score,
            cross_domain_matrix=cross_matrix,
            service_topologies=service_topologies,
            top_gaps=self.inventory.gaps[:10],
        )

    def generate_all_artifacts(self, output_dir: Path | str = "artifacts/knowledge-inventory") -> Dict[str, str]:
        """Generates all 6 required artifacts (§38, §39, §40, §41)."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        report = self.analyze()

        created = {}

        # 1. knowledge-inventory.json
        inv_json_path = out / "knowledge-inventory.json"
        with open(inv_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.inventory.model_dump(mode="json"), indent=2))
        created["knowledge_inventory_json"] = str(inv_json_path)

        # 2. knowledge-inventory.md
        inv_md_path = out / "knowledge-inventory.md"
        with open(inv_md_path, "w", encoding="utf-8") as f:
            f.write(self._format_inventory_markdown(report))
        created["knowledge_inventory_md"] = str(inv_md_path)

        # 3. knowledge-gaps.json
        gaps_json_path = out / "knowledge-gaps.json"
        with open(gaps_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps([g.model_dump(mode="json") for g in self.inventory.gaps], indent=2))
        created["knowledge_gaps_json"] = str(gaps_json_path)

        # 4. knowledge-gaps.md
        gaps_md_path = out / "knowledge-gaps.md"
        with open(gaps_md_path, "w", encoding="utf-8") as f:
            f.write(self._format_gaps_markdown(report))
        created["knowledge_gaps_md"] = str(gaps_md_path)

        # 5. coverage-report.json
        cov_json_path = out / "coverage-report.json"
        with open(cov_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report.model_dump(mode="json"), indent=2))
        created["coverage_report_json"] = str(cov_json_path)

        # 6. coverage-report.md
        cov_md_path = out / "coverage-report.md"
        with open(cov_md_path, "w", encoding="utf-8") as f:
            f.write(self._format_coverage_markdown(report))
        created["coverage_report_md"] = str(cov_md_path)

        return created

    def _format_inventory_markdown(self, report: CoverageReport) -> str:
        s = self.inventory.summary
        lines = [
            "# FikraCore Knowledge Inventory Report",
            "",
            f"- **Brain Identity**: `{s.brain}`",
            f"- **Schema Identity**: `{s.schema_identity}`",
            f"- **Retrieved At**: `{self.inventory.retrieved_at}`",
            f"- **Total Pages**: `{s.total_pages}`",
            f"- **Total Unique Relationships**: `{s.total_unique_links}`",
            f"- **Overall Health Status**: **`{s.overall_health_status}`**",
            f"- **Overall Coverage Score**: **`{report.overall_composite_score_pct}%` ({report.overall_status})**",
            "",
            "## 1. Executive Summary",
            "",
            f"Telecombrain currently contains **{s.total_pages} pages** across **{s.domains_count} domains** and **{s.total_unique_links} unique operational relationships**.",
            f"The dominant operational domain is **Mobile Core** with **{self.inventory.domains.get('Mobile Core', {}).get('entities_count', 0)} entities**.",
            f"There are **{s.orphans_count} operational orphans**, **{s.unresolved_aliases_count} unresolved aliases**, and **{s.stale_knowledge_count} stale knowledge records**.",
            "",
            "## 2. Domain Distribution",
            "",
            "| Domain | Entities | Services | Network Functions | Incidents | Relationships | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for dom, sc in report.domain_scores.items():
            lines.append(
                f"| **{dom}** | {sc.entity_count} | {sc.service_count} | {sc.network_function_count} | {self.inventory.domains.get(dom, {}).get('incidents_count', 0)} | {sc.relationship_count} | `{sc.coverage_label}` |"
            )

        lines.extend([
            "",
            "## 3. Knowledge Type Breakdown",
            "",
            "| Knowledge Type | Count | Percentage |",
            "| :--- | :--- | :--- |",
        ])
        for p_type, count in sorted(self.inventory.page_types.items(), key=lambda x: x[1], reverse=True):
            pct = round((count / max(1, s.total_pages)) * 100.0, 1)
            lines.append(f"| `{p_type}` | {count} | {pct}% |")

        lines.extend([
            "",
            "## 4. Knowledge States & Epistemic Segregation",
            "",
            "| State | Count | Percentage |",
            "| :--- | :--- | :--- |",
        ])
        for state, count in self.inventory.knowledge_states.items():
            pct = round((count / max(1, s.total_pages)) * 100.0, 1)
            lines.append(f"| **`{state}`** | {count} | {pct}% |")

        lines.extend([
            "",
            "## 5. Prioritized Operational Gaps",
            "",
        ])
        if self.inventory.gaps:
            for i, g in enumerate(self.inventory.gaps[:7], 1):
                lines.append(f"{i}. **[{g.severity}] {g.gap_class}** (`{g.entity_or_domain}`): {g.description}")
                lines.append(f"   - *Recommendation*: {g.recommendation}")
        else:
            lines.append("No critical knowledge gaps detected.")

        lines.append("\n---\n*Generated automatically by FikraCore Step 4.7 Knowledge Inventory Harness.*")
        return "\n".join(lines)

    def _format_gaps_markdown(self, report: CoverageReport) -> str:
        lines = [
            "# FikraCore Live Knowledge Gaps Assessment",
            "",
            f"- **Brain**: `{self.inventory.brain}`",
            f"- **Total Identified Gaps**: `{len(self.inventory.gaps)}`",
            f"- **Timestamp**: `{self.inventory.retrieved_at}`",
            "",
            "## 1. Gap Classification Summary",
            "",
            "| Gap Class | Severity | Target Entity / Domain | Description | Actionable Recommendation |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for g in self.inventory.gaps:
            lines.append(
                f"| `{g.gap_class}` | **{g.severity}** | `{g.entity_or_domain}` | {g.description} | {g.recommendation} |"
            )

        lines.append("\n---\n*Generated automatically by FikraCore Step 4.7 Knowledge Gaps Harness.*")
        return "\n".join(lines)

    def _format_coverage_markdown(self, report: CoverageReport) -> str:
        lines = [
            "# FikraCore Knowledge Coverage & Topology Report",
            "",
            f"- **Overall Coverage Score**: **`{report.overall_composite_score_pct}%` ({report.overall_status})**",
            f"- **Formula**: `{report.scoring_formula}`",
            f"- **Timestamp**: `{self.inventory.retrieved_at}`",
            "",
            "## 1. Domain Coverage Matrix",
            "",
            "| Domain | Entity Cov | Rel Cov | Service Cov | Evidence Cov | Validated Cov | Composite Score | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for dom, sc in report.domain_scores.items():
            lines.append(
                f"| **{dom}** | {sc.entity_coverage_pct}% | {sc.relationship_coverage_pct}% | {sc.service_mapping_coverage_pct}% | {sc.evidence_coverage_pct}% | {sc.validated_knowledge_pct}% | **{sc.composite_score_pct}%** | `{sc.coverage_label}` |"
            )

        lines.extend([
            "",
            "## 2. Cross-Domain Dependency Coverage (§24)",
            "",
            "| Source Domain | Target Domain | Known Links | Status |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for cd in report.cross_domain_matrix:
            lines.append(f"| **{cd.source_domain}** | **{cd.target_domain}** | {cd.link_count} | `{cd.status}` |")

        if report.telemetry_instrumentation:
            ti = report.telemetry_instrumentation
            lines.extend([
                "",
                "## 3. Telemetry & Observability Layer Instrumentation",
                "",
                f"- **Overall Instrumentation Coverage**: **`{ti.instrumentation_coverage_pct}%` ({ti.status})**",
                f"- **Total Telemetry Artifacts**: `{ti.total_telemetry_entities}` (Logs: {ti.loki_log_streams}, Metrics: {ti.prometheus_metric_streams}, Traces: {ti.trace_spans}, Alerts: {ti.alert_rules})",
                f"- **Monitored Network Functions / Services**: `{ti.monitored_entities_count}`",
                f"- **Active Telemetry Linkages**: `{ti.telemetry_links_count}`",
            ])

        lines.extend([
            "",
            "## 4. Service Topology Completeness (§35)",
            "",
            "| Service | Domain | Functions Mapped | Transport Path | Charging | Monitoring | Completeness |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for st in report.service_topologies:
            t_str = "Yes" if st.has_transport_path else "No"
            c_str = "Yes" if st.has_charging_dependency else "No"
            m_str = "Yes" if st.has_monitoring_dependency else "No"
            lines.append(
                f"| **{st.service_name}** | {st.domain} | {len(st.supporting_functions)} | {t_str} | {c_str} | {m_str} | **{st.completeness_score_pct}%** |"
            )

        lines.append("\n---\n*Generated automatically by FikraCore Step 4.7 Knowledge Coverage Harness.*")
        return "\n".join(lines)
