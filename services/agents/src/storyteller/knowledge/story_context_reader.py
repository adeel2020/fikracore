"""StoryContextReader — Loads operational/story_context.json into IncidentContext.

Provides sub-millisecond hydration of Storyteller's Layer 1 contract directly
from authentic simulation run materialized views, bypassing heavy graph traversal.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .context import IncidentContext
from .provenance import CONFIRMED_ROOT_CAUSE, FACT, HYPOTHESIS, OBSERVATION, ProvenanceFact

logger = logging.getLogger(__name__)


class StoryContextReader:
    """Reads operational/story_context.json from simulation runs into IncidentContext."""

    def __init__(self, runs_dir: Optional[Path | str] = None) -> None:
        if runs_dir:
            self.runs_dir = Path(runs_dir).resolve()
        else:
            # Default to engine_stack/engines/telecom_brain/simulator/runs
            here = Path(__file__).resolve()
            # Navigate to services/agents/src/engine_stack/engines/telecom_brain/simulator/runs
            self.runs_dir = here.parents[2] / "engine_stack" / "engines" / "telecom_brain" / "simulator" / "runs"

    def resolve_story_file(self, incident_or_scenario_id: str) -> Optional[Path]:
        """Resolve the path to operational/story_context.json for a given incident/scenario."""
        if not self.runs_dir.is_dir():
            return None

        raw = incident_or_scenario_id.strip()
        # Clean slug prefixes
        clean = raw
        if "/" in clean:
            clean = clean.split("/")[-1]

        # Extract SCN-XXX or DEMO-XXX if present
        scn_id = clean.upper()
        if "TRANSPORT-N3-MOBILE-DATA-STALL" in scn_id or "TRANSPORT_N3" in scn_id:
            scn_id = "SCN-001"

        # 1. Match RUN-<ID>*
        matches = list(self.runs_dir.glob(f"RUN-{scn_id}*"))
        if not matches:
            # Try case-insensitive matching
            matches = [
                d for d in self.runs_dir.glob("RUN-*")
                if scn_id.lower() in d.name.lower()
            ]

        for m in matches:
            story_file = m / "operational" / "story_context.json"
            if story_file.is_file():
                return story_file

        return None

    def read(self, incident_or_scenario_id: str) -> Optional[IncidentContext]:
        """Read story_context.json and project into IncidentContext."""
        story_file = self.resolve_story_file(incident_or_scenario_id)
        if not story_file:
            return None

        try:
            data = json.loads(story_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to parse story_context.json at %s: %e", story_file, e)
            return None

        scn_id = data.get("scenario_id", "SCN-001")
        raw_domain = data.get("domain", "transport").lower()
        domain = "transport" if "transport" in raw_domain else raw_domain
        requested_slug = incident_or_scenario_id.strip() if incident_or_scenario_id.startswith("incidents/") else None
        canonical_slug = requested_slug or f"incidents/{domain}/{scn_id.lower()}"
        source_label = f"operational/story_context.json ({data.get('run_id')})"

        # 1. Top-level incident object
        incident = {
            "slug": canonical_slug,
            "title": data.get("title", f"Incident {scn_id}"),
            "frontmatter": {
                "severity": data.get("severity", "MAJOR"),
                "status": data.get("status", "resolved"),
                "started_at": data.get("started_at"),
                "resolved_at": data.get("resolved_at"),
                "canonical_slug": canonical_slug,
                "domain": domain,
                "pre_resolved_root_cause": (data.get("root_cause") or {}).get("entity") if data.get("root_cause") else None,
            },
            "summary": data.get("executive_summary", ""),
        }

        # 2. Timeline facts
        timeline: list[ProvenanceFact] = []
        for item in data.get("timeline", []):
            ent = item.get("entity") or scn_id
            timeline.append(
                ProvenanceFact(
                    value=f"{item.get('event')}: {item.get('summary')}",
                    source=source_label,
                    timestamp=item.get("time"),
                    relationship="milestone",
                    slug=ent,
                    extra=item,
                )
            )

        # 3. Blast radius & affected components
        network_functions: list[ProvenanceFact] = []
        services: list[ProvenanceFact] = []
        for br in data.get("blast_radius", []):
            ent = br.get("entity", "")
            fact = ProvenanceFact(
                value=f"{ent} ({br.get('role', 'AFFECTED')}): {br.get('status', 'degraded')}",
                source=source_label,
                relationship="blast_radius",
                slug=ent or scn_id,
                extra=br,
            )
            if "SERVICE" in ent or "DATA" in ent or "CRM" in ent:
                services.append(fact)
            else:
                network_functions.append(fact)

        # 4. Root cause hypothesis
        hypotheses: list[ProvenanceFact] = []
        rc = data.get("root_cause")
        if rc and isinstance(rc, dict):
            status = rc.get("status", "CONFIRMED")
            hyp_slug = rc.get("entity") or scn_id
            hypotheses.append(
                ProvenanceFact(
                    value=f"{rc.get('entity')}: {rc.get('condition')}",
                    source=source_label,
                    confidence=rc.get("confidence", 0.942),
                    relationship="root_cause",
                    slug=hyp_slug,
                    extra={
                        "hypothesis_slug": hyp_slug,
                        "status": "confirmed" if status == "CONFIRMED" else "plausible",
                        "score": rc.get("confidence", 0.942),
                        "is_confirmed": status == "CONFIRMED",
                    },
                )
            )

        # 5. Causal chain as evidence facts
        evidence: list[ProvenanceFact] = []
        chain_steps = data.get("causal_chain", [])
        for step in chain_steps:
            evidence.append(
                ProvenanceFact(
                    value=str(step),
                    source=source_label,
                    relationship="causal_hop",
                    slug=str(step),
                    extra={"hypothesis_slug": rc.get("entity") if rc else None},
                )
            )

        # 6. Recovery events & remediations
        recovery_events: list[ProvenanceFact] = []
        remediations: list[ProvenanceFact] = []
        if data.get("resolved_at"):
            recovery_events.append(
                ProvenanceFact(
                    value="Remediation verified; service nominal",
                    source=source_label,
                    timestamp=data.get("resolved_at"),
                    relationship="recovery",
                    slug=scn_id,
                )
            )
            remediations.append(
                ProvenanceFact(
                    value="Playbook remediation executed successfully",
                    source=source_label,
                    timestamp=data.get("resolved_at"),
                    relationship="remediation",
                    slug=scn_id,
                )
            )

        # 7. KPIs & Symptoms
        kpis: list[ProvenanceFact] = []
        kpi_events: list[ProvenanceFact] = []
        symptoms: list[ProvenanceFact] = []
        metrics = data.get("metrics", {})
        if metrics.get("kpi_breach"):
            kb = metrics["kpi_breach"]
            k_slug = kb.get("name") or scn_id
            kpi_fact = ProvenanceFact(
                value=f"{kb.get('name')}: {kb.get('value')} (baseline {kb.get('baseline')})",
                source=source_label,
                relationship="kpi_breach",
                slug=k_slug,
                extra=kb,
            )
            kpis.append(kpi_fact)
            kpi_events.append(kpi_fact)
            symptoms.append(kpi_fact)

        ctx = IncidentContext(
            incident=incident,
            timeline=timeline,
            services=services,
            network_functions=network_functions,
            kpis=kpis,
            kpi_events=kpi_events,
            symptoms=symptoms,
            hypotheses=hypotheses,
            evidence=evidence,
            remediations=remediations,
            recovery_events=recovery_events,
            similar_incidents=[],
            correlation_metadata={"source": "materialized_presentation_view"},
            lookup_trace=[f"hit: {story_file}"],
        )

        return ctx
