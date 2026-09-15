"""MobileCoreKnowledge — Layer 1 (Knowledge / Retrieval).

A Python abstraction over the gbrain knowledge graph (mobile-core schema).
Every retrieval method talks to the actual gbrain ops via ``GbrainClient``
and returns provenance-wrapped facts (§5). No graph is copied into
application memory; gbrain remains the authoritative knowledge layer (§3, #11).

Schema (unchanged — reused, never recreated):
  incident -> detected-by -> kpi-event -> measures -> kpi
  incident -> involves -> network-function
  incident -> affects -> service
  incident -> has-symptom -> symptom
  incident -> has-hypothesis -> hypothesis -> supported-by -> evidence
  hypothesis -> explains -> symptom
  incident -> has-remediation -> remediation -> targets -> network-function
  remediation -> verified-by -> kpi-event
"""

from __future__ import annotations

import logging
from typing import Any

from correlation.namespaces import incident_aliases
from engine_stack.engines.telecom_brain.canonicalization import CanonicalResolver, load_default_resolver

from .context import IncidentContext
from .gbrain_client import GbrainClient
from .provenance import ProvenanceFact, fact, provenance_from_page

logger = logging.getLogger(__name__)

# Relationship (link-type) vocabulary used for traversal.
REL_DETECTED_BY = "detected-by"
REL_MEASURES = "measures"
REL_INVOLVES = "involves"
REL_AFFECTS = "affects"
REL_HAS_SYMPTOM = "has-symptom"
REL_HAS_HYPOTHESIS = "has-hypothesis"
REL_SUPPORTED_BY = "supported-by"
REL_HAS_REMEDIATION = "has-remediation"
REL_TARGETS = "targets"
REL_VERIFIED_BY = "verified-by"
REL_EXPLAINS = "explains"


class MobileCoreKnowledge:
    """Retrieval API over the gbrain mobile-core knowledge graph."""

    def __init__(self, client: GbrainClient | None = None, resolver: CanonicalResolver | None = None) -> None:
        self.client = client or GbrainClient()
        self.resolver = resolver or load_default_resolver()

    # ------------------------------------------------------------------
    # Low-level traversal helper
    # ------------------------------------------------------------------
    def _edges_from(
        self,
        slug: str,
        link_type: str | None = None,
        depth: int = 2,
        direction: str = "out",
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"slug": slug, "depth": depth, "direction": direction}
        if link_type:
            params["link_type"] = link_type
        result = self.client.call("traverse_graph", params)
        # traverse_graph returns GraphPath[] when link_type or direction set.
        if isinstance(result, list):
            return [e for e in result if isinstance(e, dict)]
        if isinstance(result, dict):
            return result.get("paths") or result.get("edges") or []
        return []

    def _edges_between(self, from_slug: str, link_type: str) -> list[dict[str, Any]]:
        """Directly connected targets of a page by a single link type."""
        return self._edges_from(from_slug, link_type=link_type, depth=1, direction="out")

    def _get_page(self, slug: str) -> dict[str, Any] | None:
        try:
            return self.client.call("get_page", {"slug": slug})
        except Exception:  # noqa: BLE001 - gbrain I/O is a soft dependency here
            logger.warning("get_page failed for %s", slug)
            return None

    # ------------------------------------------------------------------
    # Public retrieval API (requirements §3)
    # ------------------------------------------------------------------
    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        """Fetch the incident page by slug."""
        for alias in self.resolver.candidates(incident_id):
            page = self._get_page(alias)
            if page:
                return page
        return None

    def resolve_incident_id(self, incident_id: str) -> tuple[str | None, list[str]]:
        """Resolve an incident reference without semantic guessing."""
        trace: list[str] = []
        candidates = self.resolver.candidates(incident_id)
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            trace.append(f"get_page:{candidate}")
            if self._get_page(candidate):
                return candidate, trace

        suffix = incident_id.rstrip("/").split("/")[-1]
        try:
            trace.append("list_pages:type=incident")
            pages = self.client.call("list_pages", {"type": "incident", "limit": 500, "sort": "updated_desc"})
            for page in pages if isinstance(pages, list) else []:
                slug = page.get("slug")
                if isinstance(slug, str) and slug.rstrip("/").split("/")[-1] == suffix:
                    trace.append(f"list_pages:matched_suffix:{slug}")
                    return slug, trace
        except Exception as exc:  # noqa: BLE001 - optional resolver path
            trace.append(f"list_pages:error:{exc}")

        try:
            trace.append(f"query:exact:{incident_id}")
            results = self.client.call("query", {"query": incident_id, "limit": 20, "detail": "low"})
            hits = results if isinstance(results, list) else results.get("results", [])
            for hit in hits if isinstance(hits, list) else []:
                slug = hit.get("slug") if isinstance(hit, dict) else None
                if isinstance(slug, str) and (
                    slug == incident_id
                    or slug.rstrip("/").split("/")[-1] == suffix
                    or incident_id in incident_aliases(slug)
                ):
                    trace.append(f"query:matched_exact:{slug}")
                    return slug, trace
        except Exception as exc:  # noqa: BLE001 - optional resolver path
            trace.append(f"query:error:{exc}")

        return None, trace

    def get_incident_timeline(self, incident_id: str) -> list[ProvenanceFact]:
        """Timeline entries from the incident page (compiled_truth + frontmatter)."""
        page = self.get_incident(incident_id)
        if not page:
            return []
        provenance = provenance_from_page(page, relationship="incident-timeline")
        facts: list[ProvenanceFact] = []
        started = page.get("frontmatter", {}).get("started_at")
        resolved = page.get("frontmatter", {}).get("resolved_at")
        if started:
            facts.append(fact(started, source=provenance["source"], timestamp=started,
                              relationship="started_at", slug=incident_id))
        if resolved:
            facts.append(fact(resolved, source=provenance["source"], timestamp=resolved,
                              relationship="resolved_at", slug=incident_id))
        # Parse "## Timeline" bullet list from compiled_truth markdown.
        truth = page.get("compiled_truth", "") or ""
        in_timeline = False
        for line in truth.splitlines():
            stripped = line.strip()
            if stripped.startswith("## Timeline"):
                in_timeline = True
                continue
            if in_timeline:
                if stripped.startswith("## ") or (stripped and not stripped.startswith("-")):
                    # Next major section or non-bullet content ends the timeline.
                    if stripped.startswith("## "):
                        break
                    continue
                if stripped.startswith("- **") and ("—" in stripped or " - " in stripped):
                    facts.append(fact(stripped, source=provenance["source"],
                                      relationship="timeline-entry", slug=incident_id))
        return facts

    def get_incident_kpis(self, incident_id: str) -> tuple[list[ProvenanceFact], list[ProvenanceFact]]:
        """Return ``(kpi_events, kpis)`` via detected-by then measures."""
        events = self._edges_between_any_alias(incident_id, REL_DETECTED_BY)
        kpi_events: list[ProvenanceFact] = []
        kpis: list[ProvenanceFact] = []
        seen_events: set[str] = set()
        seen_kpis: set[str] = set()
        for edge in events:
            to_slug = edge.get("to_slug")
            if not to_slug or to_slug in seen_events:
                continue
            seen_events.add(to_slug)
            page = self._get_page(to_slug)
            prov = provenance_from_page(page, relationship=REL_DETECTED_BY)
            title = self._page_label(page, to_slug)
            fm = (page or {}).get("frontmatter", {}) if page else {}
            extra = {}
            for key in ("value", "event_type", "threshold", "unit", "observed_at"):
                if fm.get(key) is not None:
                    extra[key] = fm.get(key)
            kpi_events.append(fact(title, **prov, extra=extra))
            # kpi-event -> measures -> kpi
            for m in self._edges_between(to_slug, REL_MEASURES):
                k_slug = m.get("to_slug")
                if not k_slug or k_slug in seen_kpis:
                    continue
                seen_kpis.add(k_slug)
                k_page = self._get_page(k_slug)
                k_prov = provenance_from_page(k_page, relationship=REL_MEASURES)
                kpis.append(fact(self._page_label(k_page, k_slug), **k_prov))
        return kpi_events, kpis

    def get_network_functions(self, incident_id: str) -> list[ProvenanceFact]:
        return self._related_pages_any_alias(incident_id, REL_INVOLVES)

    def get_services(self, incident_id: str) -> list[ProvenanceFact]:
        return self._related_pages_any_alias(incident_id, REL_AFFECTS)

    def get_symptoms(self, incident_id: str) -> list[ProvenanceFact]:
        return self._related_pages_any_alias(incident_id, REL_HAS_SYMPTOM)

    def get_hypotheses(self, incident_id: str) -> list[ProvenanceFact]:
        edges = self._edges_between_any_alias(incident_id, REL_HAS_HYPOTHESIS)
        out: list[ProvenanceFact] = []
        seen: set[str] = set()
        for edge in edges:
            to_slug = edge.get("to_slug")
            if not to_slug or to_slug in seen:
                continue
            seen.add(to_slug)
            page = self._get_page(to_slug)
            prov = provenance_from_page(page, relationship=REL_HAS_HYPOTHESIS)
            extra = {"explains": self._target_labels(to_slug, REL_EXPLAINS)}
            status = (page or {}).get("frontmatter", {}).get("status")
            if status:
                extra["status"] = status
            out.append(fact(self._page_label(page, to_slug), **prov, extra=extra))
        return out

    def get_evidence(self, hypothesis_id: str) -> list[ProvenanceFact]:
        """Evidence supporting a hypothesis (supported-by)."""
        return self._related_pages(hypothesis_id, REL_SUPPORTED_BY)

    def get_remediations(self, incident_id: str) -> list[ProvenanceFact]:
        """Remediations, enriched with their targets + verified-by kpi-events."""
        rems = self._edges_between_any_alias(incident_id, REL_HAS_REMEDIATION)
        out: list[ProvenanceFact] = []
        seen: set[str] = set()
        for edge in rems:
            to_slug = edge.get("to_slug")
            if not to_slug or to_slug in seen:
                continue
            seen.add(to_slug)
            page = self._get_page(to_slug)
            prov = provenance_from_page(page, relationship=REL_HAS_REMEDIATION)
            extra = {"targets": self._target_labels(to_slug, REL_TARGETS),
                     "verified_by": self._target_labels(to_slug, REL_VERIFIED_BY)}
            value = self._page_label(page, to_slug)
            out.append(fact(value, **prov, extra=extra))
        return out

    def get_recovery(self, incident_id: str) -> list[ProvenanceFact]:
        """Recovery KPI events: remediation -> verified-by -> kpi-event."""
        recovery: list[ProvenanceFact] = []
        seen: set[str] = set()
        for rem in self._edges_between_any_alias(incident_id, REL_HAS_REMEDIATION):
            rem_slug = rem.get("to_slug")
            if not rem_slug:
                continue
            for v in self._edges_between(rem_slug, REL_VERIFIED_BY):
                to_slug = v.get("to_slug")
                if not to_slug or to_slug in seen:
                    continue
                seen.add(to_slug)
                page = self._get_page(to_slug)
                prov = provenance_from_page(page, relationship=REL_VERIFIED_BY)
                recovery.append(fact(self._page_label(page, to_slug), **prov))
        return recovery

    def find_similar_incidents(self, incident_id: str, limit: int = 5) -> list[ProvenanceFact]:
        """Semantic search for similar incidents (query op) + same-type listing."""
        page = self.get_incident(incident_id)
        if not page:
            return []
        title = self._page_label(page, incident_id)
        similar: list[ProvenanceFact] = []
        seen: set[str] = {incident_id}

        try:
            results = self.client.call("query", {"query": title, "limit": limit, "detail": "low"})
            hits = results if isinstance(results, list) else results.get("results", [])
            for hit in hits:
                if not isinstance(hit, dict):
                    continue
                slug = hit.get("slug")
                if not slug or slug in seen:
                    continue
                seen.add(slug)
                hit_type = hit.get("type", "")
                if hit_type not in ("incident",) and "incident" not in str(hit_type):
                    continue
                similar.append(fact(
                    hit.get("title", slug),
                    source="gbrain/query",
                    timestamp=hit.get("updated_at"),
                    relationship="similar-incident",
                    slug=slug,
                ))
        except Exception as exc:  # noqa: BLE001 - gbrain query is best-effort
            logger.warning("similar-incident query failed: %s", exc)

        # Fallback / complement: same-type listing via list_pages.
        try:
            pages = self.client.call("list_pages", {"type": "incident", "limit": limit + 1, "sort": "updated_desc"})
            for p in pages if isinstance(pages, list) else []:
                slug = p.get("slug")
                if not slug or slug in seen:
                    continue
                seen.add(slug)
                similar.append(fact(
                    p.get("title", slug),
                    source="gbrain/list_pages",
                    timestamp=p.get("updated_at"),
                    relationship="similar-incident",
                    slug=slug,
                ))
        except Exception as exc:  # noqa: BLE001 - gbrain listing is best-effort
            logger.warning("similar-incident list failed: %s", exc)

        return similar[:limit]

    def search(self, query: str, limit: int = 10) -> list[ProvenanceFact]:
        """Free-text search over the graph (query op)."""
        try:
            results = self.client.call("query", {"query": query, "limit": limit, "detail": "medium"})
        except Exception as exc:  # noqa: BLE001 - gbrain search is best-effort
            logger.warning("search failed: %s", exc)
            return []
        hits = results if isinstance(results, list) else results.get("results", [])
        out: list[ProvenanceFact] = []
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            out.append(fact(
                hit.get("title", hit.get("slug", "")),
                source=hit.get("source_id", "gbrain/query"),
                timestamp=hit.get("updated_at"),
                relationship="search-hit",
                slug=hit.get("slug"),
                extra={"type": hit.get("type")},
            ))
        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _related_pages(self, slug: str, link_type: str) -> list[ProvenanceFact]:
        edges = self._edges_between(slug, link_type)
        out: list[ProvenanceFact] = []
        seen: set[str] = set()
        for edge in edges:
            to_slug = edge.get("to_slug")
            if not to_slug or to_slug in seen:
                continue
            seen.add(to_slug)
            page = self._get_page(to_slug)
            prov = provenance_from_page(page, relationship=link_type)
            out.append(fact(self._page_label(page, to_slug), **prov))
        return out

    def _edges_between_any_alias(self, slug: str, link_type: str) -> list[dict[str, Any]]:
        for alias in self.resolver.candidates(slug):
            edges = self._edges_between(alias, link_type)
            if edges:
                return edges
        return []

    def _related_pages_any_alias(self, slug: str, link_type: str) -> list[ProvenanceFact]:
        for alias in self.resolver.candidates(slug):
            pages = self._related_pages(alias, link_type)
            if pages:
                return pages
        return []

    @staticmethod
    def _page_label(page: dict[str, Any] | None, fallback: str) -> str:
        if not page:
            return fallback
        fm = page.get("frontmatter", {}) or {}
        for key in ("title", "label", "summary", "name"):
            value = fm.get(key)
            if value:
                return str(value)
        compiled = (page.get("compiled_truth") or "").strip()
        if compiled:
            for line in compiled.splitlines():
                stripped = line.strip().lstrip("#").strip()
                if stripped and not stripped.startswith("---"):
                    return stripped[:180]
        return str(page.get("title") or fallback)

    def _target_labels(self, slug: str, link_type: str) -> list[str]:
        labels: list[str] = []
        for edge in self._edges_between(slug, link_type):
            to_slug = edge.get("to_slug")
            if to_slug:
                labels.append(to_slug)
        return labels

    # ------------------------------------------------------------------
    # Composition: build the full IncidentContext (requirements §4 / Phase 1)
    # ------------------------------------------------------------------
    def get_incident_context(self, incident_id: str) -> IncidentContext:
        """Retrieve the complete normalized context for an incident."""
        resolved_id, lookup_trace = self.resolve_incident_id(incident_id)
        if not resolved_id:
            return IncidentContext(lookup_trace=lookup_trace)

        incident_id = resolved_id
        incident = self.get_incident(incident_id)
        if not incident:
            return IncidentContext(lookup_trace=lookup_trace)

        kpi_events, kpis = self.get_incident_kpis(incident_id)
        hypotheses = self.get_hypotheses(incident_id)
        evidence: list[ProvenanceFact] = []
        for h in hypotheses:
            h_slug = h.slug
            if h_slug:
                for e in self.get_evidence(h_slug):
                    # Tag evidence with the hypothesis it supports (provenance
                    # preserved via extra, never discarded).
                    extra = dict(e.extra)
                    extra["hypothesis_slug"] = h_slug
                    evidence.append(fact(
                        e.value, source=e.source, timestamp=e.timestamp,
                        confidence=e.confidence, relationship=e.relationship,
                        slug=e.slug, extra=extra,
                    ))

        return IncidentContext(
            incident=incident,
            timeline=self.get_incident_timeline(incident_id),
            services=self.get_services(incident_id),
            network_functions=self.get_network_functions(incident_id),
            kpis=kpis,
            kpi_events=kpi_events,
            symptoms=self.get_symptoms(incident_id),
            hypotheses=hypotheses,
            evidence=evidence,
            remediations=self.get_remediations(incident_id),
            recovery_events=self.get_recovery(incident_id),
            similar_incidents=self.find_similar_incidents(incident_id),
            correlation_metadata={
                key: incident.get("frontmatter", {}).get(key)
                for key in ("correlation_key", "correlation_score", "correlation_scope", "contributing_domains", "intent_status", "correlation_reasons")
                if incident.get("frontmatter", {}).get(key) is not None
            },
            lookup_trace=lookup_trace,
        )
