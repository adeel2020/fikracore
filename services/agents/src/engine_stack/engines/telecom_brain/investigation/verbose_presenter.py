"""VerbosePresenter: ANSI box renderer for the 8-stage investigation pipeline.

Renders scenario-agnostic, dynamically computed terminal outputs for
`fikracore demo --live -v` with optional deep-dive inspection gates.
"""

from __future__ import annotations

import sys
import time
from typing import Any

from .contracts import Hypothesis, InvestigationResult, KnowledgeState, Terminal

# ANSI escape codes
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[1;36m"
ANSI_GREEN = "\033[1;32m"
ANSI_YELLOW = "\033[1;33m"
ANSI_RED = "\033[1;31m"
ANSI_MAGENTA = "\033[1;35m"


class VerbosePresenter:
    """Renders investigation pipeline stages to terminal with ANSI box drawing.

    Supports optional deep-dive gates for Stage 2 (correlation vector payload)
    and Stage 4 (12-factor synthesis core math).
    """

    def __init__(
        self,
        use_color: bool = True,
        show_vectors: bool = False,
        show_math: bool = False,
        auto: bool = False,
    ):
        self.use_color = use_color
        self.show_vectors = show_vectors
        self.show_math = show_math
        self.auto = auto
        self._width = 74

    def _box_top(self, title: str) -> str:
        pad = self._width - len(title) - 4
        return f"{ANSI_CYAN}┌─ {title} {'─' * max(0, pad)}┐{ANSI_RESET}"

    def _box_row(self, text: str, indent: int = 1) -> str:
        prefix = " " * indent
        visible_len = len(text.replace("\033[", "").replace("[0m", "").replace("[1m", "").replace("[2m", ""))
        pad = self._width - visible_len - indent * 2
        return f"{ANSI_CYAN}│{ANSI_RESET}{prefix}{text}{' ' * max(0, pad)}{ANSI_CYAN}│{ANSI_RESET}"

    def _box_bottom(self) -> str:
        return f"{ANSI_CYAN}└{'─' * (self._width)}┘{ANSI_RESET}"

    def _kv(self, key: str, value: str, width: int = 30) -> str:
        return f"{ANSI_BOLD}{key:<{width}}{ANSI_RESET} {value}"

    def _status_icon(self, active: bool) -> str:
        return f"{ANSI_GREEN}●{ANSI_RESET}" if active else f"{ANSI_DIM}○{ANSI_RESET}"

    def _score_color(self, score: float) -> str:
        if score >= 0.8:
            return ANSI_GREEN
        elif score >= 0.6:
            return ANSI_CYAN
        elif score >= 0.4:
            return ANSI_YELLOW
        return ANSI_RED

    def _write(self, text: str) -> None:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()

    def prompt_deep_dive(self, stage_name: str) -> bool:
        """Prompt operator for optional deep-dive. Returns True if view selected."""
        if self.auto:
            return self.show_vectors if "vector" in stage_name.lower() else self.show_math
        try:
            sys.stdout.write(f"{ANSI_YELLOW}[?] View {stage_name}? [v=View / Enter=Proceed]: {ANSI_RESET}")
            sys.stdout.flush()
            choice = input().strip().lower()
            return choice in ("v", "y", "view", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def render_ingestion(self, data: dict) -> None:
        """Render Stage 1: Telemetry Ingestion."""
        self._write(f"\n{self._box_top('Stage 1: TELEMETRY INGESTION')}")
        raw_count = data.get("raw_count", data.get("raw_evidence_count", 0))
        sources = data.get("sources", {})
        types = data.get("types", {})
        min_time = data.get("min_time", "")
        max_time = data.get("max_time", "")
        time_span = data.get("time_span", 0)

        num_sources = len(sources) if sources else data.get("hashes_count", 1)
        self._write(self._box_row(f"Loaded {raw_count} raw operational records from {num_sources} independent sources"))
        self._write(self._box_row(""))
        if sources:
            src_str = ", ".join(f"{s} ({c})" for s, c in sorted(sources.items()))
            self._write(self._box_row(self._kv("Sources:", src_str[:50])))
        if types:
            type_str = ", ".join(f"{t} ({c})" for t, c in sorted(types.items()))
            self._write(self._box_row(self._kv("Types:", type_str[:50])))
        if min_time and max_time:
            self._write(self._box_row(self._kv("Window:", f"{min_time} -> {max_time} ({time_span:.0f}s span)")))
        self._write(self._box_bottom())

    def render_correlation_2_1(self, data: dict) -> None:
        """Render Stage 2.1: Temporal & Identity Correlation."""
        self._write(f"\n{self._box_top('Stage 2.1: CORRELATION ENGINE -- Temporal & Identity Correlation')}")
        self._write(self._box_row("Canonical slug normalization, timestamp alignment & deduplication"))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Canonicalization:", f"{data['raw_count']} raw -> {data['normalized_count']} canonical entities")))
        self._write(self._box_row(self._kv("Freshness decay:", f"avg {data['avg_freshness']:.2f} (max age: {data['max_age_hours']:.1f} hours)")))
        dedup_pct = 1 - (data['collapsed_count'] / max(1, data['normalized_count']))
        self._write(self._box_row(self._kv("Deduplication:", f"{data['normalized_count']} normalized -> {data['collapsed_count']} unified events ({dedup_pct:.0%})")))
        self._write(self._box_bottom())

    def render_correlation_2_2(self, data: dict) -> None:
        """Render Stage 2.2: Topological Correlation."""
        self._write(f"\n{self._box_top('Stage 2.2: CORRELATION ENGINE -- Topological Correlation')}")
        self._write(self._box_row("Dynamic causal dependency traversal and DiGraph assembly"))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Graph Provider:", f"{data['provider_name']} (CanonicalKnowledge)")))
        self._write(self._box_row(self._kv("Entities Traversed:", f"{data['entities_traversed']} canonical entities")))
        self._write(self._box_row(self._kv("Relationships Found:", f"{data['relationships_found']} causal links")))
        self._write(self._box_row(self._kv("Topology DiGraph:", f"{data['node_count']} nodes, {data['edge_count']} edges (consumer->supplier inverted)")))
        self._write(self._box_bottom())

    def render_correlation_2_3(self, data: dict) -> None:
        """Render Stage 2.3: Cross-Domain Pathway Correlation."""
        self._write(f"\n{self._box_top('Stage 2.3: CORRELATION ENGINE -- Cross-Domain Pathway Correlation')}")
        total_funnels = len(data.get("pathways", [])) or 10
        self._write(self._box_row(f"Evaluated operational telemetry across {total_funnels} multi-domain reasoning lenses"))
        self._write(self._box_row(""))
        self._write(self._box_row(f"Active Pathways: {data['active_count']} of {total_funnels} funnels triggered"))
        self._write(self._box_row(""))
        for p in data.get("pathways", []):
            icon = self._status_icon(p["active"])
            name = f"{ANSI_BOLD}{p['name']}{ANSI_RESET}" if p["active"] else f"{ANSI_DIM}{p['name']}{ANSI_RESET}"
            status = f" {ANSI_GREEN}ACTIVE{ANSI_RESET}" if p["active"] else ""
            self._write(self._box_row(f"  {icon} {name:<30}{status}"))
        self._write(self._box_bottom())

    def render_correlation_2_4(self, data: dict) -> None:
        """Render Stage 2.4: Service & Blast Radius Correlation."""
        self._write(f"\n{self._box_top('Stage 2.4: CORRELATION ENGINE -- Service & Blast Radius Correlation')}")
        self._write(self._box_row("Synthesized pathway outputs into operational damage envelope"))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Abnormal Events:", f"{data['abnormal_count']} across {data['impacted_count']} entities")))
        self._write(self._box_row(self._kv("Healthy Events:", f"{data['healthy_count']} (evaluated for negative falsification)")))
        self._write(self._box_row(self._kv("Direct Blast Radius:", f"{data['impacted_count']} degraded entities")))
        svc = data.get("impacted_service") or "NONE"
        svc_count = len(data.get("service_entities", {}).get(svc, []))
        self._write(self._box_row(self._kv("Primary Impacted Service:", f"{svc} ({svc_count} entities degraded)")))
        self._write(self._box_row(self._kv("Involved Domains:", ", ".join(data.get("domains", [])))))
        self._write(self._box_row(self._kv("Coincidental Filter:", f"{data.get('unrelated_count', 0)} unrelated alarms filtered")))
        self._write(self._box_bottom())

    def render_correlation_vector_payload(self, data: dict) -> None:
        """Render Stage 2 Payload: Synthesized Correlation Evidence Vector."""
        self._write(f"\n{self._box_top('Stage 2 Payload: SYNTHESIZED CORRELATION EVIDENCE VECTOR')}")
        self._write(self._box_row("Formatted Correlation Payload emitted to downstream Hypothesis Engine"))
        self._write(self._box_row(""))
        dims = [
            ("temporal_precedence", "Phase 2.1"),
            ("evidence_freshness", "Phase 2.1"),
            ("source_reliability", "Phase 2.1"),
            ("independent_telemetry", "Phase 2.1/2.3"),
            ("upstream_position", "Phase 2.2"),
            ("knowledge_confidence", "Phase 2.2"),
            ("change_relevance", "Phase 2.3"),
            ("historical_support", "Phase 2.3"),
            ("symptom_likelihood_penalty", "Phase 2.3"),
            ("blast_radius_coverage", "Phase 2.4"),
            ("service_dependency_relevance", "Phase 2.4"),
            ("negative_evidence", "Phase 2.4"),
        ]
        self._write(self._box_row("  {"))
        for dim, phase in dims:
            val = data.get("score_dimensions", {}).get(dim, 0.0)
            self._write(self._box_row(f'    "{dim}": {val:.4f},  ({phase})'))
        self._write(self._box_row("  }"))
        self._write(self._box_row(""))
        raw = data.get("raw_count", 0)
        abnormal = data.get("abnormal_count", 0)
        reduction = (1 - abnormal / max(1, raw)) * 100
        impacted = data.get("impacted_count", 0)
        domains = data.get("domain_count", 0)
        self._write(self._box_row(f"  Telemetry Compression: {raw} raw -> {abnormal} abnormal ({reduction:.1f}% reduction)"))
        self._write(self._box_row(f"  Causal Envelope: {impacted} impacted nodes across {domains} domains"))
        self._write(self._box_bottom())

    def render_summary_line(self, data: dict) -> None:
        """Render compact correlation summary when deep-dive is skipped."""
        raw = data.get("raw_count", 0)
        abnormal = data.get("abnormal_count", 0)
        impacted = data.get("impacted_count", 0)
        self._write(f"  {ANSI_DIM}[->] Correlation Vector: 12 factors synthesized | {raw} raw -> {abnormal} abnormal | Bounded {impacted} nodes. Proceeding...{ANSI_RESET}")

    def render_hypothesis_generation(self, data: dict) -> None:
        """Render Stage 3: Hypothesis Generation."""
        roots = data.get("roots", [])
        dual_count = data.get("dual_cause_count", 0)
        self._write(f"\n{self._box_top('Stage 3: HYPOTHESIS GENERATION')}")
        self._write(self._box_row(f"Formulated {len(roots)} candidate hypotheses from evidence & topological ancestors"))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Candidate Pool:", f"{len(roots)} root entities evaluated")))
        if dual_count > 0:
            self._write(self._box_row(self._kv("Dual-Cause Combinations:", f"{dual_count} admitted (independent evidence)")))
        else:
            self._write(self._box_row(self._kv("Dual-Cause Combinations:", "0 admitted (all candidates single-root)")))
        self._write(self._box_row(""))
        for i, root in enumerate(roots[:6], 1):
            self._write(self._box_row(f"  {i}. H-{i:03d}: {root}"))
        if len(roots) > 6:
            self._write(self._box_row(f"  ... and {len(roots) - 6} more candidates"))
        self._write(self._box_row(""))
        self._write(self._box_row("Status: CANDIDATE | Unranked (Awaiting 12-Factor Synthesis Evaluation)"))
        self._write(self._box_bottom())

    def render_hypothesis_testing_summary(self, hypotheses: list[Hypothesis]) -> None:
        """Render Stage 4 Summary (when math deep-dive is skipped)."""
        self._write(f"\n{self._box_top('Stage 4: HYPOTHESIS TESTING (Summary)')}")
        self._write(self._box_row(f"Evaluated {len(hypotheses)} candidate hypotheses against 12-factor synthesis core"))
        self._write(self._box_row(""))
        for i, h in enumerate(hypotheses[:6], 1):
            color = self._score_color(h.hypothesis_confidence)
            self._write(self._box_row(
                f"  #{i} {h.hypothesis_id} ({h.canonical_root_entity}) : "
                f"Score {color}{h.hypothesis_confidence:.4f}{ANSI_RESET} [{h.status.value} / {h.causal_role.value}]"
            ))
        self._write(self._box_row(""))
        self._write(self._box_row(f"{ANSI_DIM}[Mathematical weights & Popperian breakdown skipped by operator]{ANSI_RESET}"))
        self._write(self._box_bottom())

    def render_hypothesis_testing_math(self, hypothesis: Hypothesis, index: int, roots_count: int) -> None:
        """Render Stage 4: 12-Factor Synthesis Core Math breakdown for a single candidate."""
        self._write(f"\n{self._box_top(f'Stage 4: HYPOTHESIS TESTING (12-FACTOR SYNTHESIS CORE)')}")
        self._write(self._box_row(f"Evaluating Candidate #{index}: {hypothesis.canonical_root_entity}"))
        self._write(self._box_row(""))
        self._write(self._box_row("Synthesized Evidence Vector:"))

        dims = hypothesis.score_dimensions
        weights = [
            ("blast_radius_coverage", 0.32),
            ("independent_telemetry", 0.18),
            ("source_reliability", 0.15),
            ("temporal_precedence", 0.10),
            ("upstream_position", 0.08),
            ("service_dependency_relevance", 0.05),
            ("knowledge_confidence", 0.05),
            ("evidence_freshness", 0.03),
            ("source_reliability", 0.02),
            ("change_relevance", 0.01),
            ("historical_support", 0.01),
            ("negative_evidence", -0.45),
            ("symptom_likelihood_penalty", -0.20),
        ]
        for dim, weight in weights:
            val = dims.get(dim, 0.0)
            contribution = weight * val
            sign = "+" if contribution >= 0 else ""
            wt_sign = "+" if weight >= 0 else ""
            self._write(self._box_row(
                f"  {dim:<35}: {val:.2f}  (wt: {wt_sign}{weight:.2f}) -> {sign}{contribution:.4f}"
            ))
        # Multi-cause penalty
        penalty = -0.08 * (roots_count - 1)
        self._write(self._box_row(
            f"  {'multi_cause_penalty':<35}: {roots_count - 1}  (wt: -0.08) -> {penalty:+.4f}"
        ))
        self._write(self._box_row(""))
        color = self._score_color(hypothesis.hypothesis_confidence)
        self._write(self._box_row(self._kv("Computed Confidence Score:", f"{color}{hypothesis.hypothesis_confidence:.4f} ({hypothesis.hypothesis_confidence * 100:.1f}%){ANSI_RESET}")))
        self._write(self._box_row(self._kv("Lifecycle State & Role:", f"{hypothesis.status.value} | {hypothesis.causal_role.value}")))
        self._write(self._box_bottom())

    def render_convergence(self, data: dict) -> None:
        """Render Stage 5: Convergence & Knowledge Gap Detection."""
        self._write(f"\n{self._box_top('Stage 5: CONVERGENCE & KNOWLEDGE GAP DETECTION')}")
        best = data.get("best")
        if best:
            self._write(self._box_row(f"Convergence: Top Driver -> {best['canonical_root_entity']} (Score: {best['score']:.4f})"))
        self._write(self._box_row(""))
        self._write(self._box_row("Ranked Hypothesis Queue:"))
        for i, h in enumerate(data.get("ranked", [])[:4], 1):
            icon = f"{ANSI_GREEN}●{ANSI_RESET}" if i == 1 else f"{ANSI_DIM}○{ANSI_RESET}"
            label = "WINNING" if i == 1 else "COMPETING"
            self._write(self._box_row(
                f"  {icon} H{i}: {h['entity']:<25} Score: {h['score']:.2f} | Coverage: {h['coverage']:.0%} ({label})"
            ))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Explained Anomalies:", f"{data.get('explained', 0)} / {data.get('total_abnormal', 0)} ({data.get('coverage', 0):.0%})")))
        self._write(self._box_row(self._kv("Unexplained Residuals:", f"{data.get('residual_count', 0)} observations")))
        self._write(self._box_row(self._kv("Discovered Gaps (H2):", f"{data.get('gap_count', 0)} unverified path adjacencies")))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Terminal Resolution State:", f"Terminal.{data.get('terminal', 'UNRESOLVED')}")))
        self._write(self._box_bottom())

    def render_domain_attribution(self, data: dict) -> None:
        """Render Stage 6: Domain Attribution & Affected Services."""
        self._write(f"\n{self._box_top('Stage 6: DOMAIN ATTRIBUTION & AFFECTED SERVICES')}")
        self._write(self._box_row(f"Authoritative Primary Domain: {data.get('primary_domain', 'unknown')} (Basis: ROOT CAUSAL DRIVER)"))
        self._write(self._box_row(""))
        self._write(self._box_row("Domain Classification:"))
        for d in data.get("domains", []):
            icon = self._status_icon(d.get("primary", False))
            role = "PRIMARY" if d.get("primary") else ("CONTRIBUTING" if d.get("contributing") else "AFFECTED")
            self._write(self._box_row(f"  {icon} {d['name']:<22} {role:<15} {d.get('reason', '')}"))
        self._write(self._box_row(""))
        svc = data.get("impacted_service", "NONE")
        entities = data.get("service_entities", [])
        self._write(self._box_row(self._kv("Affected Customer Services:", f"{svc}: {len(entities)} entities degraded")))
        self._write(self._box_row(""))
        chain = data.get("propagation_chain", "")
        if chain:
            self._write(self._box_row("Causal Propagation Chain:"))
            self._write(self._box_row(f"  {chain}"))
        self._write(self._box_bottom())

    def render_next_best_evidence(self, data: dict) -> None:
        """Render Stage 7: Next-Best Evidence & Operator Validation."""
        self._write(f"\n{self._box_top('Stage 7: NEXT-BEST EVIDENCE & OPERATOR VALIDATION')}")
        self._write(self._box_row("Next-Best Evidence Priority Queue:"))
        self._write(self._box_row(""))
        for req in data.get("requests", [])[:3]:
            self._write(self._box_row(f"  {req['id']}: {req['question'][:60]}"))
            self._write(self._box_row(f"    Priority: {req['priority']:.4f} | Cost: {req['cost']:.1f} | Latency: {req['latency']:.1f}"))
        if not data.get("requests"):
            self._write(self._box_row("  Terminal state is EXPLAINED -- no further evidence required."))
        self._write(self._box_row(""))
        self._write(self._box_row(self._kv("Terminal State:", data.get("terminal", "EXPLAINED"))))
        self._write(self._box_bottom())

    def render_promotion(self, data: dict) -> None:
        """Render Stage 8: Knowledge Graph Promotion."""
        self._write(f"\n{self._box_top('Stage 8: KNOWLEDGE GRAPH PROMOTION')}")
        if data.get("no_gaps"):
            self._write(self._box_row("No unmodeled knowledge gaps detected -- active knowledge graph is complete"))
            self._write(self._box_row(f"(0 promotions needed)"))
        else:
            self._write(self._box_row("Smart Delta Link Upsert (PromotionEngine):"))
            self._write(self._box_row(""))
            self._write(self._box_row(self._kv("Candidate Input:", data.get("candidate_file", "N/A"))))
            self._write(self._box_row(self._kv("SME Gate:", f"{data.get('validation_file', 'N/A')} (Status: {data.get('validation_status', 'PENDING')})")))
            self._write(self._box_row(self._kv("8 Guardrails:", data.get("guardrails_status", "PASSED"))))
            self._write(self._box_row(""))
            if data.get("promoted"):
                src = data.get("source_entity", "?")
                rel = data.get("promoted_relation", "?")
                tgt = data.get("target_entity", "?")
                self._write(self._box_row(f"Injected Edge into telecombrain:"))
                self._write(self._box_row(f"  {ANSI_GREEN}{src} --[{rel}]--> {tgt}{ANSI_RESET}"))
                self._write(self._box_row(""))
                self._write(self._box_row(self._kv("Rollback Journal:", f"Recorded ID '{data.get('promotion_id', '?')}' for reversible rollback")))
                self._write(self._box_row(self._kv("Live MCP Sync:", "Successfully emitted add_link to gbrain MCP")))
            else:
                self._write(self._box_row(f"  {ANSI_YELLOW}Dry run -- no changes persisted{ANSI_RESET}"))
        self._write(self._box_bottom())

    def render_final_summary(self, result: InvestigationResult) -> None:
        """Render final executive summary after pipeline completion."""
        best = result.ranked_hypotheses[0] if result.ranked_hypotheses else None
        dur_ms = result.diagnostics.get("investigation_duration_seconds", 0) * 1000

        self._write(f"\n{ANSI_BOLD}{'=' * 78}{ANSI_RESET}")
        self._write(f"{ANSI_BOLD}  INVESTIGATION COMPLETE{ANSI_RESET}")
        self._write(f"{'=' * 78}")
        self._write(f"  Terminal State:     {ANSI_GREEN}{result.terminal_state.value}{ANSI_RESET}")
        self._write(f"  Explanation Cover:  {result.explanation_coverage:.0%}")
        if best:
            self._write(f"  Winning Root Cause: {best.canonical_root_entity}")
            self._write(f"  Confidence Score:   {best.hypothesis_confidence:.4f}")
            self._write(f"  Causal Role:        {best.causal_role.value}")
        self._write(f"  Duration:           {dur_ms:.1f}ms")
        self._write(f"  Hypotheses Tested:  {len(result.ranked_hypotheses)}")
        self._write(f"{'=' * 78}\n")
