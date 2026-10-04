"""Scenario-Specific State Compiler for FikraCore Live Simulator.

Generates scenario-specific runtime state from compiled scenario manifests,
topology views, and the reference synthetic network. Replaces the hardcoded
SCN-001 demo payload with dynamic per-scenario state generation.

Spec: fikracore-step5-scenario-scoped-backend-state-generation-fix.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
import json
import yaml


H4_RUNS_DIR = Path(__file__).parent / "h4_runs"
SCENARIOS_DIR = Path(__file__).parent / "scenarios"
REFERENCE_NETWORK_PATH = (
    Path(__file__).parent / "operator_model" / "reference_synthetic_network.yaml"
)

# Domain tag to display name mapping
DOMAIN_TAG_MAP: dict[str, str] = {
    "transport": "Transport",
    "optical": "Transport",
    "mobile_core": "Mobile Core",
    "packet_core": "Packet Core",
    "core": "Core",
    "ran": "RAN",
    "ims": "IMS",
    "database": "Database",
    "dns": "DNS",
    "security": "Security",
    "signaling": "Signaling",
    "routing": "Transport",
    "spof": "",
    "resilience": "",
    "5g": "",
    "4g": "",
    "tcp": "",
    "mtu": "",
    "subscriber": "Database",
}

# Cohort to event/hypothesis template mapping
COHORT_EVENT_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "single_point_failure": [
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "{trigger_name} Failure Detected"},
        {"category": "metric", "badge": "METRIC", "severity": "high", "state": "OBSERVED",
         "title_template": "Traffic drop on {trigger_name} downstream path"},
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Service degradation alert for {affected_service}"},
        {"category": "ticket", "badge": "TICKET", "severity": "high", "state": "INVOLVED",
         "title_template": "Customer impact report: {affected_service} outage"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1 created: {failure_type}"},
        {"category": "trace", "badge": "TRACE", "severity": "high", "state": "CONFIRMED",
         "title_template": "Path trace confirms failure propagation from {trigger_name}"},
    ],
    "shared_common_cause": [
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Correlated alarms across {domain_count} domains"},
        {"category": "metric", "badge": "METRIC", "severity": "high", "state": "OBSERVED",
         "title_template": "Simultaneous degradation on shared dependency"},
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Common cause failure pattern detected"},
        {"category": "ticket", "badge": "TICKET", "severity": "high", "state": "INVOLVED",
         "title_template": "Multi-service impact reported"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1: Shared {shared_component} failure"},
    ],
    "failover_capacity": [
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "{trigger_name} failover path exhausted"},
        {"category": "metric", "badge": "METRIC", "severity": "critical", "state": "OBSERVED",
         "title_template": "Backup capacity at 0% headroom"},
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Traffic reroute failed: no valid backup"},
        {"category": "ticket", "badge": "TICKET", "severity": "critical", "state": "INVOLVED",
         "title_template": "Service outage: failover trap triggered"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1: Failover capacity exhaustion"},
    ],
    "change_risk": [
        {"category": "change", "badge": "CHANGE", "severity": "high", "state": "OBSERVED",
         "title_template": "Configuration change observed on {trigger_name}"},
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Degradation signal on {trigger_name}"},
        {"category": "metric", "badge": "METRIC", "severity": "high", "state": "OBSERVED",
         "title_template": "KPI regression after maintenance window"},
        {"category": "ticket", "badge": "TICKET", "severity": "high", "state": "INVOLVED",
         "title_template": "Operational incident reported"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1 created for {failure_type}"},
    ],
    "multi_failure": [
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Multiple independent failures detected"},
        {"category": "alarm", "badge": "ALARM", "severity": "critical", "state": "OBSERVED",
         "title_template": "Secondary failure compound impact"},
        {"category": "metric", "badge": "METRIC", "severity": "critical", "state": "OBSERVED",
         "title_template": "Cascading degradation across domains"},
        {"category": "ticket", "badge": "TICKET", "severity": "critical", "state": "INVOLVED",
         "title_template": "Major incident: multi-domain outage"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1: Multi-failure cascade"},
    ],
    "unknown_knowledge": [
        {"category": "alarm", "badge": "ALARM", "severity": "high", "state": "OBSERVED",
         "title_template": "Anomalous behavior detected on {trigger_name}"},
        {"category": "metric", "badge": "METRIC", "severity": "high", "state": "OBSERVED",
         "title_template": "Unexplained metric deviation"},
        {"category": "alarm", "badge": "ALARM", "severity": "high", "state": "OBSERVED",
         "title_template": "Knowledge gap: insufficient topology data"},
        {"category": "action", "badge": "ACTION", "severity": "info", "state": "TESTING",
         "title_template": "Hypothesis H1: Unknown root cause"},
    ],
}

COHORT_HYPOTHESIS_TEMPLATES: list[dict[str, Any]] = [
    {
        "rank": 1,
        "status": "LEADING",
        "supports_template": [
            "{trigger_name} failure precedes service impact",
            "Blast radius consistent with single point of failure",
            "Temporal correlation confirmed",
        ],
        "against_template": [
            "No redundant path verification yet",
        ],
        "missing_template": [
            "Detailed {trigger_name} health metrics",
        ],
    },
    {
        "rank": 2,
        "status": "COMPETING",
        "confidence_base": 25.0,
        "supports_template": [
            "Symptom pattern matches secondary cause",
        ],
        "against_template": [
            "Primary evidence points to {trigger_name}",
        ],
        "missing_template": [],
    },
    {
        "rank": 3,
        "status": "COMPETING",
        "confidence_base": 12.0,
        "supports_template": [
            "Latency pattern correlation",
        ],
        "against_template": [
            "Insufficient evidence for alternative",
        ],
        "missing_template": [],
    },
    {
        "rank": 4,
        "status": "REJECTED",
        "confidence_base": 3.0,
        "supports_template": [],
        "against_template": [
            "Contradicted by observed evidence",
        ],
        "missing_template": [],
    },
]


from .compiler.telemetry_loader import load_operational_telemetry_lifecycle
from .compiler.reasoning_map_builder import build_reasoning_map
from .compiler.reasoning_map_builder import build_causal_path
from .compiler.reasoning_map_builder import build_operational_edges
from .compiler.reasoning_map_builder import build_hypothesis_paths
from .compiler.reasoning_map_builder import build_evidence_clusters
from .compiler.hypothesis_builder import build_hypotheses
from .compiler.hypothesis_builder import generate_hypothesis_names
from .compiler.topology_builder import build_topology
from .compiler.zaki_builder import build_zaki
from .compiler.stage_watchdog import build_stage_watchdog
from .compiler.stage_watchdog import disclosure_policy_for_stage
from .compiler.stage_watchdog import compute_stage_values
from .compiler.stage_watchdog import build_stages
from .compiler.stage_watchdog import build_frontiers
from .compiler.stage_watchdog import build_search_space
from .compiler.stage_watchdog import build_reasoning_focus


class ScenarioStateCompiler:
    """Compiles scenario-specific runtime state from manifests and reference data."""

    def __init__(self) -> None:
        self._ref_network: Optional[dict[str, Any]] = None
        self._ref_entities: dict[str, dict[str, Any]] = {}
        self._ref_relationships: list[dict[str, Any]] = []

    def _load_ref_network(self) -> None:
        if self._ref_network is not None:
            return
        try:
            with open(REFERENCE_NETWORK_PATH, "r", encoding="utf-8") as f:
                self._ref_network = yaml.safe_load(f)
            self._ref_entities = {
                e["entity_id"]: e
                for e in self._ref_network.get("entities", [])
            }
            self._ref_relationships = self._ref_network.get("relationships", [])
        except Exception:
            self._ref_network = {}
            self._ref_entities = {}
            self._ref_relationships = []

    def load_scenario_manifest(self, scenario_id: str) -> Optional[dict[str, Any]]:
        """Load scenario manifest from runs/, h4_runs/, declarative scenarios, or registry fallback."""
        clean_id = scenario_id.upper().strip()

        # 1. Check pre-compiled benchmark runs in runs/ directory (e.g. RUN-SCN-093-L3-SEED-42093)
        runs_dir = Path(__file__).parent / "runs"
        if runs_dir.exists():
            for run_path in sorted(runs_dir.glob(f"RUN-{clean_id}*")):
                if not run_path.is_dir():
                    continue
                gt_file = run_path / "hidden" / "ground_truth.yaml"
                manifest_file = run_path / "scenario_manifest.yaml"
                if gt_file.exists():
                    try:
                        with open(gt_file, "r", encoding="utf-8") as f:
                            gt_data = yaml.safe_load(f) or {}
                        ht = gt_data.get("hidden_truth") or {}
                        root_entity = ht.get("root_entity")
                        root_name = ht.get("root_entity_name") or (root_entity.split(":")[-1] if root_entity else None)
                        root_domain = ht.get("root_domain") or "TRANSMISSION"
                        blast = ht.get("actual_blast_radius") or {}
                        services = blast.get("services") or ["5g_sa_mobile_data"]
                        title = ht.get("root_condition", f"Incident {clean_id}")
                        if ":" in title:
                            title = title.split(":")[0]

                        raw_chain = ht.get("causal_chain") or []
                        causal_chain = [c["entity"] if isinstance(c, dict) and "entity" in c else str(c) for c in raw_chain]

                        return {
                            "what_if_id": clean_id,
                            "title": title,
                            "description": str(ht.get("root_condition") or f"Declarative scenario {clean_id}"),
                            "cohort": "single_point_failure",
                            "causal_chain": causal_chain,
                            "trigger": {
                                "canonical_id": root_entity or "IP:PE:RTR-21",
                                "entity_display_name": root_name or "MPLS Edge Router-07",
                                "event_type": "FAILURE",
                                "severity": "CRITICAL",
                            },
                            "failure_domain_tags": [root_domain.lower()] + [s.lower() for s in services],
                        }
                    except Exception:
                        pass
                elif manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            m_data = yaml.safe_load(f) or {}
                        return m_data
                    except Exception:
                        pass

        # 2. Check DEMO-001 explicit file
        if clean_id == "DEMO-001":
            demo_file = SCENARIOS_DIR / "DEMO-001-transport-mobile-data.yaml"
            if demo_file.exists():
                try:
                    with open(demo_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    return {
                        "what_if_id": "DEMO-001",
                        "title": data.get("display_name", "Transport-Induced Mobile Data Degradation"),
                        "description": "Cross-domain transport-induced mobile data degradation.",
                        "cohort": "single_point_failure",
                        "trigger": {
                            "canonical_id": "IP:PE:RTR-21",
                            "entity_display_name": "MPLS Edge Router-07",
                            "event_type": "FAILURE",
                            "severity": "CRITICAL",
                        },
                        "failure_domain_tags": ["transport", "mobile_core", "ran"],
                    }
                except Exception:
                    pass

        # 3. Check direct scenario manifest in h4_runs directory
        manifest_path = H4_RUNS_DIR / clean_id / "scenario_manifest.yaml"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        # 4. Check scenarios directory for any matching YAML (e.g. SCN-093.yaml)
        for fpath in sorted(SCENARIOS_DIR.glob("*.yaml")):
            if fpath.name == "h4_registry.yaml":
                continue
            if fpath.stem.upper() == clean_id or fpath.name.upper().startswith(clean_id):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    spec = data.get("spec") if isinstance(data.get("spec"), dict) else data
                    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                    annotations = meta.get("annotations") if isinstance(meta.get("annotations"), dict) else {}
                    hidden = spec.get("hidden_reality") or data.get("hidden_reality") or {}
                    origin_entity = hidden.get("origin_entity") or spec.get("origin_entity") or data.get("origin_entity")
                    origin_domain = hidden.get("origin_domain") or spec.get("origin_domain") or data.get("origin_domain")
                    title = annotations.get("presentation.telecom.ai/display-title") or spec.get("display_name") or spec.get("scenario_name") or data.get("display_name") or data.get("scenario_name") or clean_id
                    explanation = spec.get("scenario_explanation") or data.get("scenario_explanation") or {}
                    desc = annotations.get("presentation.telecom.ai/business-impact") or spec.get("description") or explanation.get("problem_statement") or data.get("description") or f"Scenario {clean_id}"
                    classification = spec.get("classification") or data.get("classification") or {}
                    domains = classification.get("domains") or spec.get("domains") or data.get("domains") or ["transport"]

                    if origin_entity:
                        canonical_id = origin_entity
                        entity_display = origin_entity.split(":")[-1] if ":" in origin_entity else origin_entity
                        if "FIBER" in origin_entity:
                            entity_display = f"Fiber Route {entity_display}"
                        elif "UPF" in origin_entity:
                            entity_display = f"UPF-{entity_display}"
                    else:
                        canonical_id = "IP:PE:RTR-21"
                        entity_display = "MPLS Edge Router-07"

                    return {
                        "what_if_id": clean_id,
                        "title": title,
                        "description": desc,
                        "cohort": "single_point_failure",
                        "trigger": {
                            "canonical_id": canonical_id,
                            "entity_display_name": entity_display,
                            "event_type": "FAILURE",
                            "severity": "CRITICAL",
                        },
                        "failure_domain_tags": [str(d).lower() for d in domains],
                    }
                except Exception:
                    pass

        # 5. Fallback: build manifest from H4 registry file
        registry_file = SCENARIOS_DIR / "h4_registry.yaml"
        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    registry_list = yaml.safe_load(f)
                registry = {entry["id"]: entry for entry in registry_list if "id" in entry}
                rec = registry.get(clean_id)
                if rec:
                    trigger_entity = rec.get("aliases", [clean_id])[0] if rec.get("aliases") else clean_id
                    return {
                        "what_if_id": clean_id,
                        "title": rec.get("display_name", clean_id),
                        "description": rec.get("description", ""),
                        "cohort": "single_point_failure",
                        "trigger": {
                            "canonical_id": rec.get("trigger_entity", clean_id),
                            "entity_display_name": trigger_entity,
                            "event_type": "FAILURE",
                            "severity": "CRITICAL",
                        },
                        "failure_domain_tags": rec.get("tags", ["transport"]),
                    }
            except Exception:
                pass

        return None

    def load_topology_view(self, scenario_id: str) -> Optional[dict[str, Any]]:
        """Load operational topology view with fallback."""
        topo_path = H4_RUNS_DIR / scenario_id / "operational" / "topology_view.yaml"
        if topo_path.exists():
            try:
                with open(topo_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        # Fallback to default H4-WI-001 topology view if scenario does not have a dedicated one
        default_topo = H4_RUNS_DIR / "H4-WI-001" / "operational" / "topology_view.yaml"
        if default_topo.exists():
            try:
                with open(default_topo, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception:
                pass

        return None

    def compile_state(
        self,
        scenario_id: str,
        run_id: str = "default_run",
        status: str = "RUNNING",
        stage_index: int = 2,
        executed_actions: Optional[list[str]] = None,
        tested_hypotheses: Optional[list[str]] = None,
        speed: float = 1.0,
        elapsed_seconds: int = 0,
        started_at: str = "",
    ) -> dict[str, Any]:
        """Compile scenario-specific runtime state.

        Returns a complete simulation state dict ready for snapshot serialization.
        """
        self._load_ref_network()
        executed_actions = executed_actions or []
        tested_hypotheses = tested_hypotheses or []
        stage_index = max(0, min(int(stage_index), 7))
        current_stage = self._resolve_stage_name(stage_index)
        disclosure_policy = disclosure_policy_for_stage(current_stage)

        manifest = self.load_scenario_manifest(scenario_id)
        topology_view = self.load_topology_view(scenario_id)

        trigger_entity = manifest.get("trigger", {}).get("canonical_id", "UNKNOWN") if manifest else "UNKNOWN"
        trigger_display = manifest.get("trigger", {}).get("entity_display_name", "Unknown Node") if manifest else "Unknown Node"
        failure_domain_tags = manifest.get("failure_domain_tags", []) if manifest else []
        cohort = manifest.get("cohort", "single_point_failure") if manifest else "single_point_failure"
        event_type = manifest.get("trigger", {}).get("event_type", "FAILURE") if manifest else "FAILURE"
        severity = manifest.get("trigger", {}).get("severity", "CRITICAL") if manifest else "CRITICAL"

        display_domains = self._derive_domains(failure_domain_tags)
        affected_service = self._derive_affected_service(manifest, failure_domain_tags)

        is_confirmed = "NBA-001" in executed_actions
        stage_vals = compute_stage_values(stage_index, is_confirmed)

        entities = self._build_entities(scenario_id, trigger_entity, topology_view, stage_vals, stage_index)
        raw_events, events, noise_events = load_operational_telemetry_lifecycle(
            scenario_id, run_id, trigger_entity, trigger_display,
            cohort, affected_service, stage_vals, stage_index, started_at
        , _parse_runtime_timestamp=self._parse_runtime_timestamp, _derive_impact_scope=self._derive_impact_scope, _format_natural_evidence_observation=self._format_natural_evidence_observation, _entity_domain=self._entity_domain)

        evidence_count = len(raw_events)
        stage_watchdog = build_stage_watchdog(
            stage_index,
            started_at,
            status,
            executed_actions=executed_actions,
            tested_hypotheses=tested_hypotheses,
            evidence_count=evidence_count,
         _resolve_stage_name=self._resolve_stage_name, _parse_runtime_timestamp=self._parse_runtime_timestamp)

        reasoning_trace = self._build_reasoning_trace(
            scenario_id, run_id, trigger_display, stage_index, stage_vals, trigger_entity, started_at, stage_watchdog
        )
        hypotheses = build_hypotheses(
            scenario_id, run_id, trigger_display, trigger_entity, affected_service, cohort,
            tested_hypotheses, stage_vals, stage_index, is_confirmed, evidence_count=evidence_count
        , _generate_hypothesis_names=generate_hypothesis_names)
        self._bind_hypothesis_evidence(hypotheses, events, trigger_entity)
        topology = build_topology(
            entities, trigger_entity, cohort, affected_service, stage_vals, stage_index, scenario_id
        , load_scenario_manifest=self.load_scenario_manifest)
        impact = self._build_impact(
            scenario_id, run_id, affected_service, cohort, stage_vals, stage_index
        )
        knowledge_gaps = self._build_knowledge_gaps(
            scenario_id, run_id, trigger_display, cohort
        ) if disclosure_policy["knowledge_gaps"] else []
        next_best_actions = self._build_next_best_actions(
            scenario_id, run_id, trigger_display, cohort, executed_actions
        ) if stage_index >= 6 else []
        next_best_evidence = self._build_next_best_actions(
            scenario_id, run_id, trigger_display, cohort, executed_actions
        ) if stage_index >= 5 else []
        reasoning_tasks = self._build_reasoning_tasks(
            scenario_id, run_id, trigger_display, cohort, stage_index
        )
        learning = self._build_learning(
            scenario_id, run_id, trigger_display, stage_vals, stage_index
        ) if stage_index >= 6 else None
        stages = build_stages(stage_index, started_at)
        zaki = build_zaki(
            scenario_id, run_id, trigger_display, stage_vals, stage_index
        )
        path_confidence = stage_vals["confidence"]
        causal_path = build_causal_path(
            trigger_entity, entities, topology, stage_vals, stage_index
        )
        topology["operational_edges"] = build_operational_edges(topology, hypotheses, stage_index)
        topology["hypothesis_paths"] = build_hypothesis_paths(hypotheses)
        evidence_clusters = build_evidence_clusters(raw_events, stage_index)
        frontiers = build_frontiers(
            scenario_id, run_id, trigger_entity, trigger_display, knowledge_gaps, hypotheses, stage_index
        )
        search_space = build_search_space(raw_events, evidence_clusters, entities, hypotheses, frontiers)
        reasoning_focus = build_reasoning_focus(
            trigger_entity, hypotheses, frontiers, current_stage, stage_watchdog, stage_index
        )
        reasoning_map = build_reasoning_map(
            scenario_id=scenario_id,
            run_id=run_id,
            manifest=manifest,
            trigger_entity=trigger_entity,
            trigger_display=trigger_display,
            affected_service=affected_service,
            raw_events=raw_events,
            hypotheses=hypotheses,
            knowledge_gaps=knowledge_gaps,
            next_best_actions=next_best_evidence,
            learning=learning,
            impact=impact,
            stage_index=stage_index,
            current_stage=current_stage,
            stage_watchdog=stage_watchdog,
            is_confirmed=is_confirmed,
            executed_actions=executed_actions,
         _derive_domains=self._derive_domains, _entity_domain=self._entity_domain)

        state = {
            "scenario_id": scenario_id,
            "run_id": run_id,
            "status": status,
            "current_stage": current_stage,
            "stage_status": stage_watchdog["stage_status"],
            "entered_at": stage_watchdog["entered_at"],
            "elapsed_ms": stage_watchdog["elapsed_ms"],
            "exit_conditions": stage_watchdog["exit_conditions"],
            "exit_conditions_detail": stage_watchdog.get("exit_conditions_detail", []),
            "exit_condition_state": stage_watchdog["exit_condition_state"],
            "next_stage": stage_watchdog["next_stage"],
            "blocking_reason": stage_watchdog["blocking_reason"],
            "waiting_for": stage_watchdog.get("waiting_for"),
            "allowed_disclosures": disclosure_policy["allowed_disclosures"],
            "disclosure_policy": disclosure_policy,
            "snapshot_version": 1,
            "sequence": 0,
            "updated_at": started_at,
            "scenario": {
                "id": scenario_id,
                "display_name": manifest.get("title", scenario_id) if manifest else scenario_id,
                "stage": "STAGE H4",
                "service": affected_service,
                "domains": display_domains,
                "status": status,
            },
            "run": {
                "run_id": run_id,
                "scenario_id": scenario_id,
                "status": status,
                "speed": speed,
                "started_at": started_at,
                "elapsed_seconds": elapsed_seconds,
                "elapsed_formatted": f"{elapsed_seconds // 3600:02d}:{(elapsed_seconds % 3600) // 60:02d}:{elapsed_seconds % 60:02d}",
                "active_entity_id": trigger_entity,
                "active_event_id": events[0]["event_id"] if events else "",
            },
            "zaki": zaki,
            "stages": stages,
            "events": events,
            "raw_events": raw_events,
            "noise_events": noise_events,
            "reasoning_trace": reasoning_trace,
            "topology": topology,
            "evidence_clusters": evidence_clusters,
            "frontiers": frontiers,
            "search_space": search_space,
            "reasoning_focus": reasoning_focus,
            "reasoning_map": reasoning_map,
            "hypotheses": hypotheses,
            "reasoning_tasks": reasoning_tasks,
            "impact": impact,
            "knowledge_gaps": knowledge_gaps,
            "next_best_actions": next_best_actions,
            "next_best_evidence": next_best_evidence,
            "learning": learning,
            "provenance": {
                "scenario_source": "h4_registry",
                "topology_source": "scenario_manifest + reference_network",
                "evidence_source": "scenario_state_compiler",
                "hypothesis_source": "scenario_state_compiler",
                "impact_source": "scenario_state_compiler",
                "gap_source": "scenario_state_compiler",
                "action_source": "scenario_state_compiler",
                "data_source": "LIVE_FIKRACORE",
            },
        }

        state["topology"]["causal_path"] = causal_path
        state["topology"]["path_confidence"] = path_confidence
        return state

    @staticmethod
    def _bind_hypothesis_evidence(
        hypotheses: list[dict[str, Any]],
        events: list[dict[str, Any]],
        trigger_entity: str,
    ) -> None:
        """Bind each ranked hypothesis to evidence that actually exists.

        Hypothesis templates emit placeholder evidence pointers. Any pointer that
        does not resolve to an admitted event is discarded; ranked hypotheses are
        then bound to real events whose canonical entity lies on the hypothesis
        path (or, for the leading hypothesis, the trigger entity). Noise events
        are never bound. A hypothesis with no matching evidence gets an empty
        list rather than a fabricated reference.
        """
        admitted = [
            e for e in events
            if (e.get("event_id") or e.get("evidence_id"))
            and str(e.get("classification", "")).upper() not in ("NOISE", "HEALTHY_NEGATIVE")
        ]
        by_id = {str(e.get("event_id") or e.get("evidence_id")): e for e in admitted}

        def _entity(e: dict[str, Any]) -> str:
            return str(e.get("canonical_entity") or e.get("entity_id") or "")

        for idx, hyp in enumerate(hypotheses):
            if not hyp.get("evidence_ids"):
                continue  # unranked: nothing to bind
            bound = [eid for eid in hyp["evidence_ids"] if eid in by_id]
            if not bound:
                path_entities = set(hyp.get("path_entity_ids") or [])
                if idx == 0 and trigger_entity:
                    path_entities.add(trigger_entity)
                bound = [
                    eid for eid, e in by_id.items()
                    if _entity(e) and _entity(e) in path_entities
                ]
            # Deduplicate while preserving order
            bound = list(dict.fromkeys(bound))
            hyp["evidence_ids"] = bound
            hyp["evidence_count"] = len(bound)
            for entry in hyp.get("confidence_history") or []:
                entry["evidence_ids"] = bound[:2]

    def _derive_domains(self, tags: list[str]) -> list[str]:
        """Derive display domain names from scenario tags."""
        domains = []
        seen = set()
        for tag in tags:
            name = DOMAIN_TAG_MAP.get(tag, "")
            if name and name not in seen:
                domains.append(name)
                seen.add(name)
        return domains or ["Transport"]

    def _derive_affected_service(self, manifest: Optional[dict[str, Any]], tags: list[str]) -> str:
        """Derive affected service name from manifest or tags."""
        if manifest:
            trigger_domain = manifest.get("failure_domain_tags", [])
            if "5g" in trigger_domain or "packet_core" in trigger_domain:
                return "5G SA Mobile Data"
            if "4g" in trigger_domain or "mobile_core" in trigger_domain:
                return "4G LTE Data"
            if "ims" in trigger_domain:
                return "VoLTE"
            if "database" in trigger_domain or "subscriber" in trigger_domain:
                return "Subscriber Services"
            if "dns" in trigger_domain:
                return "Core DNS Resolution"
            if "security" in trigger_domain or "signaling" in trigger_domain:
                return "Roaming Traffic"
            title = manifest.get("title", "")
            if "MPLS" in title or "Router" in title or "Transport" in title or "Optical" in title:
                return "IP Transport Services"
            if "Gateway" in title and "DC" in title:
                return "Core DC Services"
            if "Packet" in title or "PGW" in title or "UPF" in title:
                return "5G SA Mobile Data"
            if "DNS" in title:
                return "Core DNS Resolution"
        if "5g" in tags or "packet_core" in tags:
            return "5G SA Mobile Data"
        if "4g" in tags or "mobile_core" in tags:
            return "4G LTE Data"
        if "transport" in tags or "optical" in tags or "routing" in tags:
            return "IP Transport Services"
        return "Network Services"

    def _resolve_stage_name(self, stage_index: int) -> str:
        mapping = {
            0: "TRIGGER",
            1: "SIGNAL_FLOOD",
            2: "CORRELATION",
            3: "HYPOTHESIS_GENERATION",
            4: "HYPOTHESIS_TESTING",
            5: "KNOWLEDGE_GAP_CHECK",
            6: "LEARNING_VALIDATION",
            7: "ACTION",
        }
        return mapping.get(max(0, min(int(stage_index), 7)), "TRIGGER")

    def _build_entities(
        self,
        scenario_id: str,
        trigger_entity: str,
        topology_view: Optional[dict[str, Any]],
        stage_vals: dict[str, Any],
        stage_index: int,
    ) -> list[dict[str, Any]]:
        """Build entity list from topology view and reference network."""
        entities = []
        trigger_ref = self._ref_entities.get(trigger_entity, {})

        trigger_state = "ROOT_CANDIDATE" if stage_index >= 4 else "SYMPTOM"
        trigger_display = trigger_ref.get("canonical_name", trigger_entity.split(":")[-1])
        entities.append({
            "id": trigger_entity,
            "display_name": trigger_display,
            "subtitle": f"{stage_vals['lifecycle']} — Root Cause" if stage_index >= 4 else "Observed signal",
            "state": trigger_state,
            "icon": "alert",
            "domain": trigger_ref.get("domain", "UNKNOWN"),
            "scenario_id": scenario_id,
        })

        # Add entities from topology view
        if topology_view:
            for vis_entity in topology_view.get("visible_entities", []):
                if vis_entity == trigger_entity:
                    continue
                ref = self._ref_entities.get(vis_entity, {})
                display = ref.get("canonical_name", vis_entity.split(":")[-1])
                entities.append({
                    "id": vis_entity,
                    "display_name": display,
                    "subtitle": "Affected",
                    "state": "SYMPTOM",
                    "icon": "server",
                    "domain": ref.get("domain", "UNKNOWN"),
                    "scenario_id": scenario_id,
                })

        # Add dependent entities from reference network relationships
        for rel in self._ref_relationships:
            source = rel.get("source", "")
            target = rel.get("target", "")
            if source == trigger_entity and target not in [e["id"] for e in entities]:
                ref = self._ref_entities.get(target, {})
                if ref:
                    display = ref.get("canonical_name", target.split(":")[-1])
                    entities.append({
                        "id": target,
                        "display_name": display,
                        "subtitle": "Observed neighbor" if stage_index < 5 else "Impacted",
                        "state": "SYMPTOM" if stage_index < 5 else "IMPACTED",
                        "icon": "server",
                        "domain": ref.get("domain", "UNKNOWN"),
                        "scenario_id": scenario_id,
                    })

        # Ensure at least 3 entities by adding healthy neighbors from the same domain
        if len(entities) < 3:
            trigger_domain = trigger_ref.get("domain", "")
            # Prefer entities from the same domain or core infrastructure
            for eid, ref in self._ref_entities.items():
                if eid in [e["id"] for e in entities] or eid == trigger_entity:
                    continue
                ref_domain = ref.get("domain", "")
                # Never inject EXTERNAL or VAS entities into unrelated incidents
                if ref_domain in ("EXTERNAL", "VAS") and trigger_domain not in ("EXTERNAL", "VAS"):
                    continue
                # If trigger has a domain, prefer entities in that domain or transport/core
                if trigger_domain and ref_domain != trigger_domain and len(entities) >= 2:
                    continue
                display = ref.get("canonical_name", eid.split(":")[-1])
                entities.append({
                    "id": eid,
                    "display_name": display,
                    "subtitle": "Healthy",
                    "state": "HEALTHY",
                    "icon": "server",
                    "domain": ref_domain or "UNKNOWN",
                    "scenario_id": scenario_id,
                })
                if len(entities) >= 3:
                    break

        return entities

    @staticmethod
    def _derive_impact_scope(item: dict[str, Any], cat: str, entity: str, domain: str, metric: str, alarm: str, val: Any) -> str:
        cat_lower = (cat or "").lower()
        domain_upper = (domain or "").upper().replace(" ", "_")
        metric_lower = (metric or "").lower()
        alarm_upper = (alarm or "").upper()
        entity_upper = (entity or "").upper()

        if item.get("classification") == "HEALTHY_NEGATIVE" or ("cpu" in metric_lower and val is not None and val < 70):
            return "Nominal Compute Baseline"
        if cat_lower == "ticket" or "TICKET" in entity_upper or "CRM" in domain_upper:
            if "complaint" in metric_lower:
                return "Ticket Escalation Surge"
            elif "success" in metric_lower or "rate" in metric_lower:
                return "Service SLA Breach"
            elif cat_lower == "ticket":
                return "Enterprise Trouble Ticket"
            return "Customer Experience Impact"
        if cat_lower == "trace" or item.get("trace_type"):
            return "End-to-End Verification"
        if cat_lower in ("change", "recovery") or item.get("intervention"):
            return "Mitigation & Recovery"
        if "UPF" in entity_upper or "5G_CORE" in domain_upper or "PACKET_CORE" in domain_upper:
            if "throughput" in metric_lower or "drop" in metric_lower or "DEGRADED" in alarm_upper:
                return "User Plane Starvation"
            return "Core User-Plane Impact"
        if "VRF" in entity_upper or "ROUTING" in domain_upper or "TUNNEL" in entity_upper:
            return "Routing Forwarding Drop"
        if "TRANSPORT" in domain_upper or "PE:" in entity_upper or "RTR" in entity_upper:
            if "latency" in metric_lower:
                return "Transmission Latency Breach"
            elif "loss" in metric_lower or "timeout" in metric_lower:
                return "Transport Packet Discard"
            elif "DEGRADED" in alarm_upper:
                return "Transport Bottleneck"
            return "Transport Procedure Stall"
        if "RAN" in domain_upper or "GNB" in entity_upper:
            return "Radio Link Degradation"
        clean_d = domain_upper.replace("_", " ").title()
        return clean_d + " Degradation" if clean_d else "Correlated Impact"

    @staticmethod
    def _format_natural_evidence_observation(item: dict[str, Any], cat: str, native: str, val: Any, base: Any) -> tuple[str, str]:
        alarm = item.get("alarm_name")
        metric = item.get("metric_name") or item.get("kpi_name")
        msg = item.get("message")
        ticket_id = item.get("ticket_id")
        trace_type = item.get("trace_type")
        intervention = item.get("intervention")
        unit = item.get("unit") or ""

        if alarm:
            sig_name = str(alarm)
            desc = f"Alarm {alarm} active on {native}"
            parts = []
            if item.get("domain"): parts.append("domain: " + str(item["domain"]))
            if item.get("service_context"): parts.append("service: " + ", ".join(item["service_context"]))
            if item.get("vendor_profile"): parts.append("vendor: " + str(item["vendor_profile"]))
            obs = desc + (" [" + " | ".join(parts) + "]" if parts else "")
        elif metric:
            sig_name = (f"{metric}: {val} {unit}").strip()
            desc = (f"{metric} recorded at {val} {unit}").strip()
            parts = []
            if base is not None: parts.append((f"baseline: {base} {unit}").strip())
            if item.get("threshold"): parts.append("threshold: " + str(item["threshold"]))
            if item.get("domain"): parts.append("domain: " + str(item["domain"]))
            if item.get("service_context"): parts.append("service: " + ", ".join(item["service_context"]))
            obs = desc + (" (" + ", ".join(parts) + ")" if parts else "")
        elif msg:
            sig_name = msg[:50] + ("..." if len(msg) > 50 else "")
            desc = str(msg)
            parts = []
            if item.get("domain"): parts.append("domain: " + str(item["domain"]))
            if item.get("confidence") is not None: parts.append("confidence: " + str(item["confidence"]))
            obs = desc + (" [" + ", ".join(parts) + "]" if parts else "")
        elif ticket_id:
            category = item.get("complaint_category", "Customer Ticket")
            sig_name = f"{ticket_id} ({category})"
            desc = f"Customer trouble ticket {ticket_id}: {category}"
            parts = []
            if item.get("impacted_service"): parts.append("service: " + str(item["impacted_service"]))
            if item.get("impacted_region"): parts.append("region: " + str(item["impacted_region"]))
            if item.get("affected_segment"): parts.append("segment: " + str(item["affected_segment"]))
            obs = desc + (" (" + ", ".join(parts) + ")" if parts else "")
        elif trace_type:
            result = item.get("result", "completed")
            sig_name = f"{trace_type}: {result}"
            desc = f"Synthetic dependency probe: {result}"
            path_str = " ➔ ".join(item.get("observed_path", []))
            obs = desc + (f" [path: {path_str}]" if path_str else "")
        elif intervention:
            sig_name = f"Intervention: {intervention}"
            desc = f"Remediation action: {intervention}"
            effect = item.get("actual_effect") or item.get("expected_effect")
            obs = desc + (f" [effect: {effect}]" if effect else "")
        else:
            sig_name = item.get("title") or "Telemetry Signal"
            obs = f"Telemetry signal recorded on {native}."
        return sig_name, obs

    def _build_raw_events(
        self,
        scenario_id: str,
        run_id: str,
        trigger_entity: str,
        trigger_display: str,
        cohort: str,
        affected_service: str,
        stage_vals: dict[str, Any],
        stage_index: int,
        started_at: str = "",
    ) -> list[dict[str, Any]]:
        """Build only raw operational events. Reasoning artifacts live in reasoning_trace."""
        op_events = self._load_operational_evidence_events(
            scenario_id=scenario_id,
            run_id=run_id,
            trigger_entity=trigger_entity,
            trigger_display=trigger_display,
            affected_service=affected_service,
            stage_index=stage_index,
            started_at=started_at,
        )
        if op_events:
            return op_events

        templates = COHORT_EVENT_TEMPLATES.get(cohort, COHORT_EVENT_TEMPLATES["single_point_failure"])
        raw_templates = [
            tmpl for tmpl in templates if tmpl["category"] in {"alarm", "metric", "log", "trace", "change", "ticket"}
        ]
        if not raw_templates:
            raw_templates = templates

        events = []
        base_dt = self._parse_runtime_timestamp(started_at)

        if stage_index == 0:
            visible_templates = raw_templates
        elif stage_index == 1:
            visible_templates = raw_templates[: min(3, len(raw_templates))]
        elif stage_index == 2:
            visible_templates = raw_templates[: min(4, len(raw_templates))]
        else:
            visible_templates = raw_templates[: max(1, min(len(raw_templates), 3 + stage_index))] if stage_index < 3 else raw_templates

        for i, tmpl in enumerate(visible_templates):
            title = tmpl["title_template"].format(
                trigger_name=trigger_display,
                affected_service=affected_service,
                failure_type="failure",
                domain_count="multiple",
                shared_component="transport",
            )
            event_time = base_dt + timedelta(seconds=i * 18)
            event_id = f"EVT-{scenario_id.upper()}-{stage_index}-{i}"
            stage_name = self._resolve_stage_name(stage_index if stage_index <= 3 else 3)
            if stage_index >= 4:
                stage_name = "HYPOTHESIS_TESTING"

            events.append({
                "event_id": event_id,
                "evidence_id": event_id,
                "time": event_time.strftime("%H:%M:%S"),
                "category": tmpl["category"],
                "badge": tmpl["badge"],
                "title": title,
                "domain": self._entity_domain(trigger_entity),
                "entity_id": trigger_entity if i < 3 else f"hyp-{i:03d}",
                "severity": tmpl["severity"],
                "state": tmpl["state"],
                "stage": stage_name,
                "event_type": "OBSERVATION",
                "evidence_type": (tmpl["badge"] or tmpl["category"]).upper(),
                "display_name": title,
                "event_time": event_time.isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
            })

        return events

    def _build_reasoning_trace(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        stage_index: int,
        stage_vals: dict[str, Any],
        trigger_entity: str,
        started_at: str = "",
        stage_watchdog: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Build a dedicated reasoning trace separate from raw operational signals."""
        stage_names = [
            "TRIGGER",
            "SIGNAL_FLOOD",
            "CORRELATION",
            "HYPOTHESIS_GENERATION",
            "HYPOTHESIS_TESTING",
            "KNOWLEDGE_GAP_CHECK",
            "LEARNING_VALIDATION",
            "ACTION",
        ]
        records: list[dict[str, Any]] = []
        base_dt = self._parse_runtime_timestamp(started_at)
        records.append({
            "timestamp": base_dt.isoformat().replace("+00:00", "Z"),
            "scenario_id": scenario_id,
            "run_id": run_id,
            "sequence": 0,
            "stage": "TRIGGER",
            "component": "simulation_manager",
            "event_type": "run_created",
            "entity_ids": [trigger_entity],
            "message": f"Clean simulation run created for {trigger_display}",
            "details": {"initial_state": "epistemically_empty"},
            "provenance": "fikracore_simulation_runtime",
        })
        records.append({
            "timestamp": (base_dt + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
            "scenario_id": scenario_id,
            "run_id": run_id,
            "sequence": 1,
            "stage": "TRIGGER",
            "component": "scenario_state_compiler",
            "event_type": "run_state_initialized",
            "entity_ids": [trigger_entity],
            "message": "Operational state initialized with unknown impact, no hypotheses, no root candidate, and no learning.",
            "details": {
                "impact_state": "UNKNOWN",
                "hypotheses": 0,
                "root_candidate": None,
                "causal_path": None,
            },
            "provenance": "fikracore_simulation_runtime",
        })
        for idx, stage_name in enumerate(stage_names):
            if idx > stage_index:
                continue
            event_type = "stage_transition" if idx < stage_index else "stage_enter"
            message = f"{stage_name} stage entered for {trigger_display}"
            details: dict[str, Any] = {
                "confidence": stage_vals["confidence"],
                "lifecycle": stage_vals["lifecycle"],
            }
            if idx == stage_index and stage_watchdog and stage_watchdog.get("blocking_reason"):
                event_type = "stage_blocked"
                message = stage_watchdog["blocking_reason"]
                details.update({
                    "required_condition": stage_watchdog.get("exit_conditions", [None])[0],
                    "actual": stage_watchdog.get("exit_condition_state", {}),
                    "next_stage": stage_watchdog.get("next_stage"),
                })
            records.append({
                "timestamp": (base_dt + timedelta(seconds=idx * 30)).isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "sequence": idx + 2,
                "stage": stage_name,
                "component": "hypothesis_engine",
                "event_type": event_type,
                "entity_ids": [trigger_entity],
                "hypothesis_id": "HYP-001" if stage_index >= 3 else None,
                "message": message,
                "details": details,
                "provenance": "fikracore_reasoning_engine",
            })

        if stage_index >= 4:
            records.append({
                "timestamp": (base_dt + timedelta(seconds=(stage_index + 1) * 30)).isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "sequence": stage_index + 10,
                "stage": "HYPOTHESIS_TESTING",
                "component": "hypothesis_engine",
                "event_type": "confidence_update",
                "entity_ids": [trigger_entity],
                "hypothesis_id": "HYP-001",
                "message": "Leading hypothesis is being evaluated against live evidence.",
                "details": {"previous_confidence": 0.58, "new_confidence": round(stage_vals["confidence"] / 100, 2)},
                "provenance": "fikracore_reasoning_engine",
            })
        if stage_index >= 5:
            records.append({
                "timestamp": (base_dt + timedelta(seconds=(stage_index + 2) * 30)).isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "sequence": stage_index + 11,
                "stage": "KNOWLEDGE_GAP_CHECK",
                "component": "knowledge_gap_engine",
                "event_type": "knowledge_gap_detected",
                "entity_ids": [trigger_entity],
                "hypothesis_id": "HYP-001",
                "message": "Missing telemetry prevents a final causal claim.",
                "details": {"missing_signal": "detailed health metrics"},
                "provenance": "fikracore_reasoning_engine",
            })
        if stage_index >= 6:
            records.append({
                "timestamp": (base_dt + timedelta(seconds=(stage_index + 3) * 30)).isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "sequence": stage_index + 12,
                "stage": "LEARNING_VALIDATION",
                "component": "learning_engine",
                "event_type": "learning_candidate_created",
                "entity_ids": [trigger_entity],
                "hypothesis_id": "HYP-001",
                "message": "Candidate lesson has been created for future validation.",
                "details": {"status": "CANDIDATE"},
                "provenance": "fikracore_reasoning_engine",
            })
        if stage_index >= 7:
            records.append({
                "timestamp": (base_dt + timedelta(seconds=(stage_index + 4) * 30)).isoformat().replace("+00:00", "Z"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "sequence": stage_index + 13,
                "stage": "ACTION",
                "component": "recommendation_engine",
                "event_type": "recommendation_generated",
                "entity_ids": [trigger_entity],
                "hypothesis_id": "HYP-001",
                "message": "Recommended evidence collection and remediation path generated.",
                "details": {"recommendation": "Validate root candidate with targeted telemetry"},
                "provenance": "fikracore_reasoning_engine",
            })
        return records

    def _build_impact(
        self,
        scenario_id: str,
        run_id: str,
        affected_service: str,
        cohort: str,
        stage_vals: dict[str, Any],
        stage_index: int,
    ) -> dict[str, Any]:
        """Build scenario-specific impact with epistemic labeling."""
        if stage_index <= 0:
            return {
                "service": affected_service,
                "impact_state": "UNKNOWN",
                "state": "UNKNOWN",
                "throughput_impact_pct": None,
                "degradation_pct": None,
                "regions_affected": None,
                "regions": [],
                "affected_users": None,
                "affected_services": [],
                "affected_label": "Unknown",
                "confidence": None,
                "evidence_ids": [],
                "status_label": "Unknown",
                "summary": "No customer-impact evidence yet.",
                "trend_sparkline": [],
                "scenario_id": scenario_id,
                "run_id": run_id,
            }
        if stage_index <= 1:
            impact_state = "OBSERVED"
            confidence = 0.35
            label = "Observed"
            users = None
            regions = []
            affected_label = "Scope unknown"
        elif stage_index <= 3:
            impact_state = "ESTIMATED"
            confidence = 0.64
            label = "Estimated"
            users = stage_vals["users_affected"]
            regions = stage_vals["regions_affected"]
            affected_label = f"~{users:,}" if users is not None else "Estimating"
        elif stage_index <= 5:
            impact_state = "INFERRED"
            confidence = round(stage_vals["confidence"] / 100, 2)
            label = "Inferred"
            users = stage_vals["users_affected"]
            regions = stage_vals["regions_affected"]
            affected_label = f"~{users:,}" if users is not None else "Estimating"
        else:
            impact_state = "CONFIRMED"
            confidence = round(stage_vals["confidence"] / 100, 2)
            label = "Confirmed"
            users = stage_vals["users_affected"]
            regions = stage_vals["regions_affected"]
            affected_label = f"{users:,}" if users is not None else "Confirmed"
        degradation = stage_vals["throughput_pct"] if stage_index >= 2 else None
        sparkline_base = degradation or -10
        return {
            "service": affected_service,
            "impact_state": impact_state,
            "state": impact_state,
            "throughput_impact_pct": degradation,
            "degradation_pct": degradation,
            "regions_affected": regions,
            "regions": regions if isinstance(regions, list) else list(range(1, regions + 1)),
            "affected_users": users,
            "affected_services": [affected_service] if stage_index >= 1 else [],
            "affected_label": affected_label,
            "confidence": confidence,
            "evidence_ids": [f"EVT-{scenario_id.upper()}-{stage_index}-0"],
            "status_label": label,
            "summary": f"{label} impact for {affected_service}." if impact_state != "UNKNOWN" else "No customer-impact evidence yet.",
            "trend_sparkline": [
                max(1, 12 + sparkline_base // 10),
                max(1, 10 + sparkline_base // 10),
                max(1, 8 + sparkline_base // 10),
                max(1, 4 + sparkline_base // 10),
                max(1, 3 + sparkline_base // 10),
                max(1, 2 + sparkline_base // 10),
                max(1, 2 + sparkline_base // 10),
            ],
            "scenario_id": scenario_id,
            "run_id": run_id,
        }

    def _build_knowledge_gaps(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        cohort: str,
    ) -> list[dict[str, Any]]:
        """Build scenario-specific knowledge gaps."""
        gaps = [
            {
                "id": f"KG-{hash(scenario_id) % 1000:03d}-01",
                "gap_id": f"KG-{hash(scenario_id) % 1000:03d}-01",
                "label": f"{trigger_display} detailed health metrics",
                "display_name": f"{trigger_display} detailed health metrics",
                "state": "NEEDS_EVIDENCE",
                "reason": "Needed to confirm root cause behavior",
                "priority": "HIGH",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": f"KG-{hash(scenario_id) % 1000:03d}-02",
                "gap_id": f"KG-{hash(scenario_id) % 1000:03d}-02",
                "label": "Similar incidents in this topology",
                "display_name": "Similar incidents in this topology",
                "state": "OPEN",
                "reason": "Historical precedent check",
                "priority": "MEDIUM",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": f"KG-{hash(scenario_id) % 1000:03d}-03",
                "gap_id": f"KG-{hash(scenario_id) % 1000:03d}-03",
                "label": "Impact on other services",
                "display_name": "Impact on other services",
                "state": "OPEN",
                "reason": "Scope isolation",
                "priority": "MEDIUM",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
        ]
        return gaps

    def _build_next_best_actions(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        cohort: str,
        executed_actions: list[str],
    ) -> list[dict[str, Any]]:
        """Build scenario-specific next-best actions."""
        nba1_completed = "NBA-001" in executed_actions or "nba-1" in executed_actions or "nba-001" in executed_actions
        nba2_completed = "NBA-002" in executed_actions or "nba-2" in executed_actions or "nba-002" in executed_actions
        hitl_completed = any(act in executed_actions for act in ("HITL-001", "VAL-001", "HITL_VALIDATE", "VAL-APPROVE", "hitl-001", "val-001"))
        act_completed = any(act in executed_actions for act in ("ACT-001", "REMEDIATE-001", "NBA-REMEDIATE", "act-001"))
        actions = [
            {
                "id": "NBA-001",
                "request_id": "NBA-001",
                "display_name": f"Get {trigger_display} detailed health stats",
                "status": "COMPLETED" if nba1_completed else "READY",
                "scenario_id": scenario_id,
                "run_id": run_id,
                "action_type": "EVIDENCE",
            },
            {
                "id": "HITL-001",
                "request_id": "HITL-001",
                "display_name": "HITL SME Validation & Knowledge Promotion",
                "status": "COMPLETED" if hitl_completed else ("READY" if nba1_completed else "PENDING"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "action_type": "VALIDATION",
            },
            {
                "id": "ACT-001",
                "request_id": "ACT-001",
                "display_name": f"Execute Remediation: Reroute traffic & isolate {trigger_display}",
                "status": "COMPLETED" if act_completed else ("READY" if hitl_completed else "PENDING"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "action_type": "REMEDIATION",
            },
            {
                "id": "NBA-002",
                "request_id": "NBA-002",
                "display_name": f"Validate {trigger_display} end-to-end path",
                "status": "COMPLETED" if nba2_completed else ("READY" if nba1_completed else "PENDING"),
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": "NBA-003",
                "request_id": "NBA-003",
                "display_name": "Check packet capture for failure pattern",
                "status": "PENDING",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": "NBA-004",
                "request_id": "NBA-004",
                "display_name": "Query historical incidents (similar topology)",
                "status": "PENDING",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": "NBA-005",
                "request_id": "NBA-005",
                "display_name": "Assess change window for recent modifications",
                "status": "PENDING",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
            {
                "id": "NBA-006",
                "request_id": "NBA-006",
                "display_name": "Validate impact on dependent services",
                "status": "PENDING",
                "scenario_id": scenario_id,
                "run_id": run_id,
            },
        ]
        return actions

    def _build_reasoning_tasks(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        cohort: str,
        stage_index: int,
    ) -> list[dict[str, Any]]:
        """Build scenario-specific reasoning tasks."""
        task_templates = {
            "single_point_failure": [
                f"Correlating alarms from {trigger_display}",
                "Analyzing failure propagation path",
                "Tracing packet flow across domains",
                "Evaluating hypothesis confidence",
                "Checking similar historical incidents",
                "Generating next best evidence",
            ],
            "shared_common_cause": [
                "Identifying shared dependency",
                "Correlating alarms across multiple domains",
                "Analyzing common cause pattern",
                "Evaluating hypothesis confidence",
                "Checking redundancy status",
                "Generating next best evidence",
            ],
            "failover_capacity": [
                "Analyzing failover path capacity",
                "Checking backup resource utilization",
                "Testing reroute availability",
                "Evaluating hypothesis confidence",
                "Assessing capacity reservation",
                "Generating next best evidence",
            ],
            "change_risk": [
                "Correlating change window with failure",
                "Analyzing post-change metrics",
                "Checking change approval records",
                "Evaluating hypothesis confidence",
                "Assessing rollback options",
                "Generating next best evidence",
            ],
            "multi_failure": [
                "Identifying independent failure points",
                "Analyzing cascade propagation",
                "Correlating multiple alarm sources",
                "Evaluating hypothesis confidence",
                "Assessing compound impact",
                "Generating next best evidence",
            ],
            "unknown_knowledge": [
                "Analyzing anomalous behavior pattern",
                "Checking topology completeness",
                "Identifying knowledge gaps",
                "Evaluating hypothesis confidence",
                "Requesting additional evidence",
                "Generating next best evidence",
            ],
        }

        templates = task_templates.get(cohort, task_templates["single_point_failure"])
        tasks = []
        for i, name in enumerate(templates):
            if i < stage_index:
                status = "COMPLETED"
            elif i == stage_index:
                status = "RUNNING"
            else:
                status = "PENDING"
            tasks.append({
                "id": i + 1,
                "name": name,
                "status": status,
                "scenario_id": scenario_id,
                "run_id": run_id,
            })
        return tasks

    def _build_learning(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        stage_vals: dict[str, Any],
        stage_index: int,
    ) -> dict[str, Any]:
        """Build learning state with validation gating."""
        learning_status = "CANDIDATE" if stage_index < 6 else "PROMOTED"
        return {
            "candidate_count": 1,
            "summary": f"Pattern observed: {trigger_display} failure propagation",
            "rule": f"{trigger_display} failure can cause cascading service degradation through dependent paths",
            "confidence": 0.87,
            "status": learning_status,
            "enabled": stage_index >= 6,
            "scenario_id": scenario_id,
            "run_id": run_id,
        }

    def _parse_runtime_timestamp(self, started_at: str = "") -> datetime:
        """Parse the runtime started_at value if provided; otherwise use the current UTC time."""
        if started_at:
            normalized = started_at.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(normalized)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)

    def compile_live_state(
        self,
        run_id: str,
        intent_id: str,
        status: str = "RUNNING",
        stage_index: int = 0,
        admitted_evidence: Optional[list[dict[str, Any]]] = None,
        executed_actions: Optional[list[str]] = None,
        tested_hypotheses: Optional[list[str]] = None,
        provider_failures: Optional[list[dict[str, Any]]] = None,
        recovery_signals: Optional[list[dict[str, Any]]] = None,
        speed: float = 1.0,
        elapsed_seconds: int = 0,
        started_at: str = "",
        terminal_state: Optional[str] = None,
        is_replay: bool = False,
    ) -> dict[str, Any]:
        """Compile live operational run state without any simulator hidden truth (§25, §26).

        Provides complete epistemic isolation from offline simulation manifests.
        """
        from .live_reasoning import live_intent_registry

        intent_rec = live_intent_registry.get_intent(intent_id)
        intent_display = intent_rec.display_name if intent_rec else f"Intent {intent_id}"
        intent_service = intent_rec.service if intent_rec else "Enterprise APN"
        intent_scope = intent_rec.scope if intent_rec else "Regional Gateway"
        intent_domain = intent_rec.domain_hint if intent_rec else "Packet Core"
        intent_metric = intent_rec.target.metric if intent_rec else "success_rate"
        intent_op = intent_rec.target.operator if intent_rec else ">="
        intent_target_val = intent_rec.target.threshold if intent_rec else 99.5
        intent_observed_val = intent_rec.observed.value if intent_rec else 97.9
        intent_severity = intent_rec.severity if intent_rec else "CRITICAL"

        admitted_evidence = list(admitted_evidence or [])
        executed_actions = list(executed_actions or [])
        tested_hypotheses = list(tested_hypotheses or [])
        provider_failures = list(provider_failures or [])
        recovery_signals = list(recovery_signals or [])

        stage_index = max(0, min(int(stage_index), 7))
        current_stage = self._resolve_stage_name(stage_index)

        now_dt = self._parse_runtime_timestamp(started_at)
        now_iso = now_dt.isoformat()

        # Stage status & Watchdog
        is_blocked = status == "BLOCKED" or (stage_index == 5 and not executed_actions and len(admitted_evidence) < 2)
        if is_blocked:
            stage_status = "BLOCKED"
            blocking_reason = "Awaiting evidence verification: Knowledge gap KG-LIVE-01 requires telemetry confirmation"
        elif stage_index == 7 and terminal_state:
            stage_status = "COMPLETED"
            blocking_reason = None
        else:
            stage_status = "READY_TO_ADVANCE" if stage_index < 7 else "ACTIVE"
            blocking_reason = None

        waiting_for = blocking_reason if stage_status == "BLOCKED" else None

        # Exit conditions
        exit_conditions_map = {
            0: ["Admit live intent violation", "Establish operational scope"],
            1: ["Collect initial telemetry window", "Normalize signals to canonical schema"],
            2: ["Correlate multi-domain telemetry", "Identify affected service path"],
            3: ["Generate competing candidate causes", "Bound failure search space"],
            4: ["Evaluate telemetry against candidates", "Rank most plausible cause"],
            5: ["Identify unobserved dependencies", "Issue Next-Best Evidence query"],
            6: ["Human operator validation", "Review candidate causal pattern"],
            7: ["Formulate remediation recommendation", "Confirm incident terminal status"],
        }
        current_exit_conds = exit_conditions_map.get(stage_index, ["Complete stage requirements"])
        exit_conditions_detail = [
            {
                "condition_id": f"cond_live_{stage_index}_{i}",
                "display_name": c,
                "satisfied": stage_status != "BLOCKED",
                "expected": "Met",
                "actual": "Met" if stage_status != "BLOCKED" else "Pending",
                "reason": blocking_reason or "",
            }
            for i, c in enumerate(current_exit_conds)
        ]

        # Events & Raw Events
        trigger_event = {
            "id": f"EV-INTENT-{intent_id}",
            "evidence_id": f"EV-INTENT-{intent_id}",
            "event_id": f"EVT-INTENT-{intent_id}",
            "run_id": run_id,
            "scenario_id": f"LIVE-{intent_id}",
            "category": "alarm",
            "badge": "ALARM",
            "severity": intent_severity.lower(),
            "state": "OBSERVED",
            "title": f"Intent Violation: {intent_display}",
            "signal": f"{intent_metric} observed at {intent_observed_val} (target {intent_op} {intent_target_val})",
            "description": f"Live intent violation admitted for service '{intent_service}'",
            "source_system": intent_rec.source_system if intent_rec else "SLO-Engine",
            "source_entity": intent_scope,
            "canonical_entity": intent_scope,
            "domain": intent_domain,
            "service": intent_service,
            "timestamp": started_at or now_iso,
            "event_time": started_at or now_iso,
            "sequence": 1,
        }

        all_events = [trigger_event]
        for i, ev in enumerate(admitted_evidence):
            ev_copy = dict(ev)
            ev_copy.setdefault("sequence", i + 2)
            ev_copy.setdefault("scenario_id", f"LIVE-{intent_id}")
            ev_copy.setdefault("run_id", run_id)
            all_events.append(ev_copy)

        for i, sig in enumerate(recovery_signals):
            rec_event = {
                "id": f"EV-RECOVERY-{i+1}",
                "evidence_id": f"EV-RECOVERY-{i+1}",
                "event_id": f"EVT-RECOVERY-{i+1}",
                "run_id": run_id,
                "scenario_id": f"LIVE-{intent_id}",
                "category": "recovery",
                "badge": "RECOVERY",
                "severity": "info",
                "state": "OBSERVED",
                "title": f"Service recovery signal: {sig.get('metric', 'Metric')} restored to {sig.get('value')}",
                "signal": f"{sig.get('metric', 'Metric')} recovered to {sig.get('value')}",
                "description": "Healthy recovery telemetry received from operational monitor",
                "source_system": "Live-Monitor",
                "source_entity": intent_scope,
                "canonical_entity": intent_scope,
                "domain": intent_domain,
                "service": intent_service,
                "timestamp": sig.get("observed_at") or now_iso,
                "event_time": sig.get("observed_at") or now_iso,
                "sequence": len(all_events) + 1,
            }
            all_events.append(rec_event)

        # Topology
        top_entities = [
            {
                "id": "APN-GW-01",
                "canonical_id": "APN-GW-01",
                "display_name": f"{intent_service} Gateway",
                "domain": intent_domain,
                "state": "DEGRADED" if stage_index >= 1 else "OBSERVED",
            },
            {
                "id": "Core-UPF-02",
                "canonical_id": "Core-UPF-02",
                "display_name": "Core User Plane 02",
                "domain": "Packet Core",
                "state": "MONITOR_ONLY",
            },
            {
                "id": "Transport-PE-01",
                "canonical_id": "Transport-PE-01",
                "display_name": "Edge Router PE-01",
                "domain": "Transport",
                "state": "MONITOR_ONLY",
            },
        ]
        topology = {
            "nodes": top_entities,
            "domains": [
                {"name": intent_domain, "entities": [top_entities[0], top_entities[1]]},
                {"name": "Transport", "entities": [top_entities[2]]},
            ],
            "causal_path": [
                {"from": "APN-GW-01", "to": "Core-UPF-02", "relation": "UPSTREAM"},
                {"from": "Core-UPF-02", "to": "Transport-PE-01", "relation": "EGRESS_LINK"},
            ],
            "path_confidence": min(85.0, 30.0 + len(admitted_evidence) * 15.0),
            "operational_edges": [
                {"from": "APN-GW-01", "to": "Core-UPF-02", "status": "ACTIVE"},
            ],
            "hypothesis_paths": [],
        }

        # Progressive Hypotheses (H1, H2)
        nbe_completed = "NBA-LIVE-001" in executed_actions or "NBA-001" in executed_actions
        base_h1_conf = 32.0 if stage_index <= 1 else (45.0 if stage_index <= 3 else (68.0 if not nbe_completed else 78.0))
        if recovery_signals:
            # Recovery adds evidence but does NOT auto-confirm root cause
            base_h1_conf = min(82.0, base_h1_conf + 4.0)

        h1_status = "CONFIRMED" if (stage_index >= 6 and nbe_completed and not recovery_signals) else "TESTING"
        if stage_index == 0:
            h1_status = "PROPOSED"
            base_h1_conf = 28.0

        hypotheses = [
            {
                "id": "HYP-001",
                "hypothesis_id": "HYP-001",
                "rank": 1,
                "display_id": "H1",
                "display_name": f"Plausible Cause: {intent_service} gateway queue saturation",
                "title": f"{intent_service} gateway egress degradation",
                "confidence": base_h1_conf,
                "confidence_state": "TESTING" if stage_index > 0 else "PROPOSED",
                "status": h1_status,
                "lifecycle_state": h1_status,
                "supporting_evidence": [ev["id"] for ev in admitted_evidence if ev.get("category") in {"metric", "alarm"}],
                "contradicting_evidence": [],
                "missing_evidence": ["Egress link buffer telemetry breakdown"] if not nbe_completed else [],
                "tested": "HYP-001" in tested_hypotheses or stage_index >= 4,
                "last_delta_reason": "Admitted live telemetry corroborates queue pressure",
            },
            {
                "id": "HYP-002",
                "hypothesis_id": "HYP-002",
                "rank": 2,
                "display_id": "H2",
                "display_name": f"Alternative: Transport backbone optical degradation",
                "title": "Transport backbone degradation",
                "confidence": 18.0 if stage_index >= 2 else 24.0,
                "confidence_state": "DISFAVORED" if stage_index >= 3 else "PROPOSED",
                "status": "DISFAVORED" if stage_index >= 3 else "TESTING",
                "lifecycle_state": "DISFAVORED" if stage_index >= 3 else "TESTING",
                "supporting_evidence": [],
                "contradicting_evidence": [ev["id"] for ev in admitted_evidence if "Transport" in str(ev)],
                "missing_evidence": [],
                "tested": stage_index >= 4,
                "last_delta_reason": "Optical BER telemetry indicates clean transmission",
            },
        ]

        # Impact - starts UNKNOWN for early stages (§45, test_live_impact_starts_unknown)
        if stage_index <= 3:
            impact = {
                "service": intent_service,
                "state": "UNKNOWN",
                "impact_state": "UNKNOWN",
                "confidence": "UNKNOWN",
                "summary": "Service impact undergoing initial operational discovery; blast radius currently UNKNOWN",
                "throughput_impact_pct": None,
                "degradation_pct": None,
                "regions_affected": None,
                "affected_users": None,
                "affected_label": "Unknown",
                "trend_sparkline": [100, 99, 98, 97],
            }
        else:
            impact = {
                "service": intent_service,
                "state": "OBSERVED",
                "impact_state": "OBSERVED",
                "confidence": 75.0,
                "summary": f"Observed degradation on {intent_service}: 2.1% drop rate",
                "throughput_impact_pct": 2.1,
                "degradation_pct": 2.1,
                "regions_affected": 1,
                "affected_users": 1420,
                "affected_label": "1,420 subscribers",
                "trend_sparkline": [100, 98, 95, 96],
            }

        # Domain Attribution - delayed until supported (§46, test_live_domain_attribution_delayed_until_supported)
        live_rev = stage_index + 1
        live_seq = len(all_events)
        if stage_index <= 4:
            domain_attribution = {
                "id": "DA-LIVE-01",
                "revision": live_rev,
                "sequence": live_seq,
                "attribution_status": "UNRESOLVED" if stage_index < 2 else "PARTIAL",
                "status": "PENDING",
                "primary_domain": None,
                "attribution_delay_reason": "Domain attribution delayed pending multi-signal evidence and hypothesis testing",
                "domains": [
                    {
                        "domain_id": "packet_core" if "core" in intent_domain.lower() else "transport",
                        "display_name": intent_domain,
                        "role": "CONTRIBUTING",
                        "attribution_basis": "DEPENDENCY",
                        "confidence": 35,
                        "reason": f"Initial operational scope bounded to {intent_domain}.",
                        "supporting_hypothesis_ids": ["HYP-001"],
                        "source_revision": live_rev,
                    },
                    {
                        "domain_id": "transport",
                        "display_name": "Transport",
                        "role": "MONITOR_ONLY",
                        "attribution_basis": "DEPENDENCY",
                        "confidence": 0,
                        "reason": "Transport metrics within nominal limits.",
                        "supporting_hypothesis_ids": [],
                        "source_revision": live_rev,
                    },
                ],
            }
        else:
            domain_attribution = {
                "id": "DA-LIVE-01",
                "revision": live_rev,
                "sequence": live_seq,
                "attribution_status": "CONSISTENT",
                "status": "READY",
                "primary_domain": intent_domain,
                "attribution_delay_reason": None,
                "domains": [
                    {
                        "domain_id": "packet_core" if "core" in intent_domain.lower() else "transport",
                        "display_name": intent_domain,
                        "role": "PRIMARY",
                        "attribution_basis": "CAUSAL",
                        "confidence": 82,
                        "reason": f"Confirmed {intent_service} gateway queue saturation within {intent_domain}.",
                        "supporting_hypothesis_ids": ["HYP-001"],
                        "source_revision": live_rev,
                    },
                    {
                        "domain_id": "transport",
                        "display_name": "Transport",
                        "role": "CONTRIBUTING",
                        "attribution_basis": "DEPENDENCY",
                        "confidence": 55,
                        "reason": "Egress link backpressure contributing to buffer exhaustion.",
                        "supporting_hypothesis_ids": ["HYP-001"],
                        "source_revision": live_rev,
                    },
                ],
            }

        # Knowledge Gaps
        knowledge_gaps = []
        if stage_index >= 3 and not nbe_completed:
            knowledge_gaps.append({
                "id": "KG-LIVE-01",
                "gap_id": "KG-LIVE-01",
                "label": f"Missing egress interface drop telemetry on {intent_scope}",
                "reason": "Telemetry window has not returned interface drop counter breakdown",
                "priority": "HIGH",
                "status": "OPEN",
                "resolvable": True,
                "required_evidence": f"Interface drop breakdown from {intent_scope}",
                "scenario_id": f"LIVE-{intent_id}",
                "run_id": run_id,
            })
        for i, pf in enumerate(provider_failures):
            knowledge_gaps.append({
                "id": f"KG-PROV-{i+1}",
                "gap_id": f"KG-PROV-{i+1}",
                "label": f"Provider unavailable: {pf.get('provider_id')}",
                "reason": pf.get("reason", "Provider request failed or timed out"),
                "priority": "HIGH",
                "status": "OPEN",
                "resolvable": False,
                "required_evidence": f"Restore connectivity to {pf.get('provider_id')}",
                "scenario_id": f"LIVE-{intent_id}",
                "run_id": run_id,
            })

        # Next-Best Actions (NBE)
        next_best_actions = []
        if stage_index >= 4:
            next_best_actions.append({
                "id": "NBA-LIVE-001",
                "display_name": f"Query egress queue telemetry for {intent_scope}",
                "status": "COMPLETED" if nbe_completed else "READY",
                "action_type": "REQUEST_EVIDENCE",
                "target": "APN-GW-01",
                "provider_id": "LGTMProvider",
                "scenario_id": f"LIVE-{intent_id}",
                "run_id": run_id,
            })

        # Stages
        stages = build_stages(stage_index, started_at)

        # Reasoning Map
        op_pathway_status = "ACTIVE" if len(admitted_evidence) > 0 else "DISCOVERED"
        svc_pathway_status = "ACTIVE" if any("UPF" in str(ev) for ev in admitted_evidence) else "DORMANT"
        gap_pathway_status = "ACTIVE" if len(knowledge_gaps) > 0 else "DORMANT"

        explain_dummy = {
            "what": "Operational live telemetry and evidence",
            "why": "Admitted live signals from monitored network entities",
            "supports": ["HYP-001"],
            "affects": ["APN-GW-01"],
            "unknown": "Egress drop breakdown",
            "recent": "Live metric update",
        }

        reasoning_map = {
            "contract_version": 1,
            "run_id": run_id,
            "scenario_id": f"LIVE-{intent_id}",
            "source_mode": "LIVE",
            "revision": 1,
            "sequence": 1,
            "stage": current_stage,
            "source": {
                "id": f"SRC-{intent_id}",
                "display_name": intent_display,
                "mode": "LIVE",
                "status": status,
                "explain": explain_dummy,
            },
            "evidence": [
                {
                    "id": ev["id"],
                    "evidence_id": ev["id"],
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_name": ev.get("title", "Evidence"),
                    "type": ev.get("category", "metric"),
                    "status": "ADMITTED",
                    "evidence_ids": [ev["id"]],
                    "explain": explain_dummy,
                }
                for ev in all_events
            ],
            "reasoning_pathways": [
                {
                    "id": "RP-01",
                    "pathway_id": "RP-01",
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_name": "Operational Evidence",
                    "status": op_pathway_status,
                    "state": op_pathway_status,
                    "activation_reason": "Admitted operational signals from live telemetry",
                    "evidence_ids": [ev["id"] for ev in all_events],
                    "hypothesis_ids": ["HYP-001"],
                    "explain": explain_dummy,
                },
                {
                    "id": "RP-02",
                    "pathway_id": "RP-02",
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_name": "Service Dependency",
                    "status": svc_pathway_status,
                    "state": svc_pathway_status,
                    "activation_reason": "Cross-domain dependency linking Gateway to UPF",
                    "evidence_ids": [],
                    "hypothesis_ids": ["HYP-001"],
                    "explain": explain_dummy,
                },
                {
                    "id": "RP-03",
                    "pathway_id": "RP-03",
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_name": "Knowledge Gap",
                    "status": gap_pathway_status,
                    "state": gap_pathway_status,
                    "activation_reason": "Detected unobserved telemetry in current reasoning window",
                    "evidence_ids": [],
                    "hypothesis_ids": ["HYP-001"],
                    "explain": explain_dummy,
                },
            ],
            "connections": [
                {
                    "id": "CONN-01",
                    "connection_id": "CONN-01",
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "source_id": f"EV-INTENT-{intent_id}",
                    "target_id": "RP-01",
                    "kind": "SUPPORTS",
                    "weight": 0.8,
                    "reason": "Intent trigger feeds operational evidence pathway",
                    "explain": explain_dummy,
                }
            ],
            "hypotheses": [
                {
                    "id": h["id"],
                    "hypothesis_id": h["id"],
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_id": h["display_id"],
                    "display_name": h["display_name"],
                    "status": h["status"],
                    "state": h["status"],
                    "confidence": h["confidence"],
                    "supporting_evidence": h["supporting_evidence"],
                    "contradicting_evidence": h["contradicting_evidence"],
                    "contradictions": h["contradicting_evidence"],
                    "missing_evidence": h["missing_evidence"],
                    "explain": explain_dummy,
                }
                for h in hypotheses
            ],
            "knowledge_gaps": [
                {
                    "id": g["id"],
                    "gap_id": g["id"],
                    "scenario_id": f"LIVE-{intent_id}",
                    "run_id": run_id,
                    "display_name": g["label"],
                    "status": g["status"],
                    "state": g["status"],
                    "affected_hypotheses": ["HYP-001"],
                    "affected_pathways": ["RP-01"],
                    "required_evidence": g["required_evidence"],
                    "explain": explain_dummy,
                }
                for g in knowledge_gaps
            ],
            "next_best_evidence": next_best_actions,
            "synthesis": {
                "id": "SYN-LIVE-01",
                "summary": f"Operational reasoning for {intent_service}: leading candidate {hypotheses[0]['display_name']}",
                "status": "CONVERGING" if stage_index >= 4 else "EXPLORING",
                "confidence": hypotheses[0]["confidence"],
                "leading_hypothesis_id": "HYP-001",
                "contradiction_count": 0,
                "unresolved_gap_count": len(knowledge_gaps),
                "terminal_state": terminal_state or ("MODEL_INSUFFICIENT" if knowledge_gaps else "PARTIALLY_EXPLAINED"),
                "explain": explain_dummy,
            },
            "validation": {
                "id": "VAL-LIVE-01",
                "state": "PENDING",
                "governance_status": "AWAITING_REVIEW",
                "explain": explain_dummy,
            },
            "learning": {
                "id": "LRN-LIVE-01",
                "candidate_count": 1 if stage_index >= 6 else 0,
                "summary": "Candidate operational rule: Buffer threshold correlation",
                "status": "CANDIDATE",
                "confidence": 70.0,
                "explain": explain_dummy,
            },
            "domain_attribution": {
                "id": "DA-MAP-01",
                "status": domain_attribution["status"],
                "domains": domain_attribution["domains"],
                "explain": explain_dummy,
            },
            "reasoning_focus": {
                "entity": intent_scope,
                "pathway": "Operational Evidence",
                "hypothesis": "HYP-001",
                "test": "NBA-LIVE-001" if stage_index >= 4 else None,
                "reason": "Correlating live telemetry signals",
            },
        }

        # Reasoning Trace
        reasoning_trace = [
            {
                "timestamp": started_at or now_iso,
                "scenario_id": f"LIVE-{intent_id}",
                "run_id": run_id,
                "sequence": 1,
                "stage": "TRIGGER",
                "component": "LiveIntentIngestion",
                "event_type": "INTENT_VIOLATION_ADMITTED",
                "entity_ids": [intent_scope],
                "message": f"Admitted live intent violation '{intent_display}' for {intent_service}",
                "provenance": "SLO-Engine",
            }
        ]
        for i, ev in enumerate(admitted_evidence):
            reasoning_trace.append({
                "timestamp": ev.get("timestamp") or now_iso,
                "scenario_id": f"LIVE-{intent_id}",
                "run_id": run_id,
                "sequence": i + 2,
                "stage": current_stage,
                "component": "EvidenceAdmission",
                "event_type": "EVIDENCE_ADMITTED",
                "entity_ids": [ev.get("source_entity", intent_scope)],
                "message": ev.get("title", "Admitted operational evidence"),
                "provenance": ev.get("source_system", "Live-Monitor"),
            })

        # Zaki Cognitive State
        zaki = {
            "phase": "REASONING" if stage_index >= 3 else "OBSERVING",
            "thought": f"Analyzing live intent violation for {intent_service}. {len(admitted_evidence)} evidence items admitted. Primary domain attribution is {domain_attribution['status']}.",
            "active_focus_entity": intent_scope,
            "confidence": hypotheses[0]["confidence"],
            "source_mode": "LIVE_INTENT",
            "intent_id": intent_id,
            "intent_display_name": intent_display,
        }

        # Learning
        learning = {
            "candidate_count": 1 if stage_index >= 6 else 0,
            "summary": "Candidate learning: Correlated gateway drop signature",
            "rule": "IF gateway_drop_elevated AND upstream_healthy THEN throttle_ingress",
            "confidence": 70.0,
            "status": "CANDIDATE",
            "enabled": stage_index >= 6,
        }

        # Search space & Frontiers
        frontiers = [
            {
                "id": "FR-01",
                "frontier_id": "FR-01",
                "type": "MISSING_EVIDENCE",
                "entity_ids": ["APN-GW-01"],
                "hypothesis_ids": ["HYP-001"],
                "description": "Resolving gateway egress queue saturation",
                "severity": "HIGH",
                "resolvable": True,
                "required_evidence": "Queue telemetry breakdown",
            }
        ]
        search_space = {
            "events": len(all_events),
            "correlated_signals": len(admitted_evidence),
            "relevant_entities": len(top_entities),
            "hypotheses": len(hypotheses),
            "plausible_causes": len(hypotheses),
            "root_candidates": 1 if stage_index >= 5 else 0,
            "open_frontiers": len(frontiers),
        }
        reasoning_focus = {
            "entity_id": intent_scope,
            "hypothesis_id": "HYP-001",
            "test_id": "NBA-LIVE-001" if stage_index >= 4 else None,
            "stage": current_stage,
            "reason": "Evaluating live operational evidence against candidate cause",
            "frontier_id": "FR-01",
            "stage_status": stage_status,
        }

        evidence_clusters = [
            {
                "cluster_id": "CLUST-LIVE-01",
                "label": f"{intent_service} Telemetry Cluster",
                "event_ids": [ev["id"] for ev in all_events],
                "entity_ids": [top_entities[0]["id"]],
                "signal_count": len(all_events),
                "noise_count": 0,
                "confidence": 85.0,
            }
        ]

        # Final unified operational run state dict (epistemically clean - NO HIDDEN TRUTH)
        state: dict[str, Any] = {
            "scenario_id": f"LIVE-{intent_id}",
            "run_id": run_id,
            "source_mode": "LIVE_INTENT",
            "intent_id": intent_id,
            "source_display_name": intent_display,
            "status": status,
            "current_stage": current_stage,
            "stage_status": stage_status,
            "entered_at": started_at or now_iso,
            "elapsed_ms": elapsed_seconds * 1000,
            "exit_conditions": current_exit_conds,
            "exit_conditions_detail": exit_conditions_detail,
            "exit_condition_state": {c: stage_status != "BLOCKED" for c in current_exit_conds},
            "next_stage": self._resolve_stage_name(stage_index + 1) if stage_index < 7 else None,
            "blocking_reason": blocking_reason,
            "waiting_for": waiting_for,
            "terminal_state": terminal_state,
            "is_replay": is_replay,
            "scenario": {
                "id": f"LIVE-{intent_id}",
                "display_name": f"Live Operations: {intent_display}",
                "stage": current_stage,
                "service": intent_service,
                "domains": [intent_domain, "Transport"],
                "status": status,
                "mode": "live",
            },
            "run": {
                "run_id": run_id,
                "scenario_id": f"LIVE-{intent_id}",
                "source_mode": "LIVE_INTENT",
                "intent_id": intent_id,
                "source_display_name": intent_display,
                "status": status,
                "speed": speed,
                "started_at": started_at or now_iso,
                "elapsed_seconds": elapsed_seconds,
                "stage_index": stage_index,
                "terminal_state": terminal_state,
                "is_replay": is_replay,
            },
            "stages": stages,
            "events": all_events,
            "raw_events": all_events,
            "reasoning_trace": reasoning_trace,
            "topology": topology,
            "evidence_clusters": evidence_clusters,
            "frontiers": frontiers,
            "search_space": search_space,
            "reasoning_focus": reasoning_focus,
            "reasoning_map": reasoning_map,
            "hypotheses": hypotheses,
            "impact": impact,
            "domain_attribution": domain_attribution,
            "reasoning_tasks": [
                {"id": 1, "name": "Admit and normalize live telemetry", "status": "COMPLETED", "scenario_id": f"LIVE-{intent_id}", "run_id": run_id},
                {"id": 2, "name": "Test competing explanations", "status": "RUNNING" if stage_index >= 3 else "PENDING", "scenario_id": f"LIVE-{intent_id}", "run_id": run_id},
            ],
            "knowledge_gaps": knowledge_gaps,
            "next_best_actions": next_best_actions,
            "learning": learning,
            "zaki": zaki,
        }

        return state

    def _entity_domain(self, entity_id: str, display_name: Optional[str] = None) -> str:
        """Get canonical display domain for an entity."""
        ref = self._ref_entities.get(entity_id, {})
        domain = ref.get("domain", "")
        if domain and domain.lower() in DOMAIN_TAG_MAP:
            mapped = DOMAIN_TAG_MAP[domain.lower()]
            if mapped:
                return mapped

        token = f"{entity_id} {display_name or ''}".upper()
        if any(k in token for k in ["RTR", "ROUTER", "TRANS", "OPTICAL", "DWDM", "IP:CORE", "IP:PE", "MPLS", "SWITCH", "IP TRANSPORT", "LEASED"]):
            return "Transport"
        if any(k in token for k in ["UPF", "AMF", "SMF", "MME", "PGW", "SGW", "AUSF", "NRF", "PACKET_CORE", "MOBILE_CORE", "5GC"]):
            return "Mobile Core"
        if any(k in token for k in ["GNB", "ENB", "RAN", "CELL", "CU", "DU", "ANTENNA", "FRONTHAUL"]):
            return "RAN"
        if any(k in token for k in ["IMS", "SBC", "CSCF", "VOLTE", "VONR"]):
            return "IMS"
        if any(k in token for k in ["PCF", "PCRF", "UDM", "UDR", "HSS", "DATABASE", "DB"]):
            return "Database"
        if any(k in token for k in ["SECURITY", "FIREWALL", "SEGW", "HSM"]):
            return "Security"
        if any(k in token for k in ["K8S", "NFVI", "OPENSTACK", "CONTAINER", "CNI"]):
            return "Cloud"
        if any(k in token for k in ["ROAMING", "DEA", "IPX"]):
            return "Roaming"
        if any(k in token for k in ["CHARGING", "OCS", "CHF", "BILLING"]):
            return "Charging"

        return domain or "Transport"



# Singleton compiler instance
_compiler: Optional[ScenarioStateCompiler] = None


def get_compiler() -> ScenarioStateCompiler:
    """Get or create the singleton scenario state compiler."""
    global _compiler
    if _compiler is None:
        _compiler = ScenarioStateCompiler()
    return _compiler


def validate_domain_attribution(state_or_run: dict[str, Any]) -> dict[str, Any]:
    """Validate domain attribution consistency against hypothesis and run state (§9)."""
    state = state_or_run.get("simulation_state", state_or_run)
    da = state.get("domain_attribution") or state.get("reasoning_map", {}).get("domain_attribution") or {}
    if not isinstance(da, dict):
        return {}

    hypotheses = state.get("hypotheses", [])
    leading_hyp = hypotheses[0] if hypotheses else {}
    issues: list[str] = []

    primary_domains = [d for d in da.get("domains", []) if d.get("role") == "PRIMARY"]
    status = da.get("status")
    attr_status = da.get("attribution_status")

    if status == "READY" or attr_status == "CONSISTENT":
        if not primary_domains:
            issues.append("Attribution marked READY/CONSISTENT but no PRIMARY domain assigned.")
        for pd in primary_domains:
            if not pd.get("reason"):
                issues.append(f"PRIMARY domain {pd.get('display_name')} missing mandatory explanation reason.")
            if not pd.get("supporting_hypothesis_ids"):
                issues.append(f"PRIMARY domain {pd.get('display_name')} missing supporting hypothesis IDs.")
            if pd.get("attribution_basis") == "IMPACT":
                issues.append(f"PRIMARY domain {pd.get('display_name')} erroneously assigned with IMPACT basis.")

            # Check consistency with leading hypothesis
            leading_name = str(leading_hyp.get("display_name") or leading_hyp.get("title") or "").lower()
            pd_name = str(pd.get("display_name") or "").lower()
            if "router" in leading_name and pd_name not in ["transport", "ip transport"]:
                issues.append(f"Leading hypothesis '{leading_name}' implies Transport, but PRIMARY domain is '{pd.get('display_name')}'.")

    # Stale attribution check (§8)
    run_rev = state.get("run", {}).get("snapshot_version") or state.get("snapshot_version") or state.get("revision")
    da_rev = da.get("revision") or (primary_domains[0].get("source_revision") if primary_domains else None)
    if run_rev is not None and da_rev is not None and da_rev < run_rev:
        da["attribution_status"] = "UNRESOLVED"
        da["stale_attribution"] = True

    if issues:
        da["attribution_status"] = "CONFLICT"
        da["conflict_reasons"] = issues

    return da
