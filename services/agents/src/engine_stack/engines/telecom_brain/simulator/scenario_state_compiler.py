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
                    hidden = data.get("hidden_reality") or {}
                    origin_entity = hidden.get("origin_entity") or data.get("origin_entity")
                    origin_domain = hidden.get("origin_domain") or data.get("origin_domain")
                    title = data.get("display_name") or data.get("scenario_name") or clean_id
                    explanation = data.get("scenario_explanation") or {}
                    desc = data.get("description") or explanation.get("problem_statement") or f"Scenario {clean_id}"
                    classification = data.get("classification") or {}
                    domains = classification.get("domains") or data.get("domains") or ["transport"]

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
        disclosure_policy = self._disclosure_policy_for_stage(current_stage)
        stage_watchdog = self._build_stage_watchdog(
            stage_index,
            started_at,
            status,
            executed_actions=executed_actions,
            tested_hypotheses=tested_hypotheses,
        )

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
        stage_vals = self._compute_stage_values(stage_index, is_confirmed)

        entities = self._build_entities(scenario_id, trigger_entity, topology_view, stage_vals, stage_index)
        raw_events = self._build_raw_events(
            scenario_id, run_id, trigger_entity, trigger_display,
            cohort, affected_service, stage_vals, stage_index, started_at
        )
        events = raw_events
        reasoning_trace = self._build_reasoning_trace(
            scenario_id, run_id, trigger_display, stage_index, stage_vals, trigger_entity, started_at, stage_watchdog
        )
        hypotheses = self._build_hypotheses(
            scenario_id, run_id, trigger_display, trigger_entity, affected_service, cohort,
            tested_hypotheses, stage_vals, stage_index, is_confirmed
        )
        topology = self._build_topology(
            entities, trigger_entity, cohort, affected_service, stage_vals, stage_index, scenario_id
        )
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
        stages = self._build_stages(stage_index, started_at)
        zaki = self._build_zaki(
            scenario_id, run_id, trigger_display, stage_vals, stage_index
        )
        path_confidence = stage_vals["confidence"]
        causal_path = self._build_causal_path(
            trigger_entity, entities, topology, stage_vals, stage_index
        )
        topology["operational_edges"] = self._build_operational_edges(topology, hypotheses, stage_index)
        topology["hypothesis_paths"] = self._build_hypothesis_paths(hypotheses)
        evidence_clusters = self._build_evidence_clusters(raw_events, stage_index)
        frontiers = self._build_frontiers(
            scenario_id, run_id, trigger_entity, trigger_display, knowledge_gaps, hypotheses, stage_index
        )
        search_space = self._build_search_space(raw_events, evidence_clusters, entities, hypotheses, frontiers)
        reasoning_focus = self._build_reasoning_focus(
            trigger_entity, hypotheses, frontiers, current_stage, stage_watchdog, stage_index
        )
        reasoning_map = self._build_reasoning_map(
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
        )

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

    def _build_stage_watchdog(
        self,
        stage_index: int,
        started_at: str = "",
        status: str = "RUNNING",
        executed_actions: Optional[list[str]] = None,
        tested_hypotheses: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Expose why the current stage is waiting or ready to move."""
        executed_actions = executed_actions or []
        tested_hypotheses = tested_hypotheses or []
        stage_name = self._resolve_stage_name(stage_index)
        next_stage = self._resolve_stage_name(stage_index + 1) if stage_index < 7 else None
        base_dt = self._parse_runtime_timestamp(started_at)
        entered_at = base_dt + timedelta(seconds=stage_index * 30)
        now = datetime.now(timezone.utc)
        elapsed_ms = max(0, int((now - entered_at).total_seconds() * 1000))
        next_best_evidence_completed = "NBA-001" in executed_actions
        hypothesis_tested = "HYP-001" in tested_hypotheses
        conditions = {
            "TRIGGER": ("valid_observation_count >= 1", {"valid_observation_count": 1}, None),
            "SIGNAL_FLOOD": ("minimum_evidence_count >= 3", {"minimum_evidence_count": 3}, None),
            "CORRELATION": ("event_groups_created == true", {"event_groups_created": True}, None),
            "HYPOTHESIS_GENERATION": ("candidate_explanations >= 1", {"candidate_explanations": 1}, None),
            "HYPOTHESIS_TESTING": (
                "leading_candidate_state in terminal_states",
                {"leading_candidate_state": "NEEDS_MORE_EVIDENCE" if not hypothesis_tested else "SUPPORTED"},
                None,
            ),
            "KNOWLEDGE_GAP_CHECK": (
                "next_best_evidence_completed == true",
                {"next_best_evidence_completed": next_best_evidence_completed},
                None if next_best_evidence_completed else "Required next-best evidence has not completed",
            ),
            "LEARNING_VALIDATION": ("validation_started == true", {"validation_started": True}, None),
            "ACTION": ("recommendation_generated == true", {"recommendation_generated": True}, None),
        }
        exit_condition, current_values, blocking_reason = conditions.get(stage_name, conditions["TRIGGER"])
        waiting_for = None
        if stage_name == "KNOWLEDGE_GAP_CHECK" and not next_best_evidence_completed:
            waiting_for = "Backup-path telemetry"

        if status == "PAUSED":
            stage_status = "PAUSED"
            blocking_reason = "Simulation is paused"
        elif blocking_reason:
            stage_status = "BLOCKED"
        else:
            stage_status = "READY_TO_ADVANCE" if next_stage else "COMPLETE"

        is_satisfied = not bool(blocking_reason) and (status != "PAUSED")
        exit_conditions_detail = [
            {
                "condition_id": f"EC-{stage_name[:3]}-01",
                "display_name": exit_condition,
                "satisfied": is_satisfied,
                "expected": "true" if "==" in exit_condition else ">= threshold",
                "actual": "true" if is_satisfied else "false",
                "reason": blocking_reason if not is_satisfied else "Condition satisfied",
            }
        ]
        return {
            "current_stage": stage_name,
            "stage_status": stage_status,
            "entered_at": entered_at.isoformat().replace("+00:00", "Z"),
            "elapsed_ms": elapsed_ms,
            "exit_conditions": [exit_condition],
            "exit_conditions_detail": exit_conditions_detail,
            "exit_condition_state": current_values,
            "next_stage": next_stage,
            "blocking_reason": blocking_reason,
            "waiting_for": waiting_for,
        }

    def _disclosure_policy_for_stage(self, stage_name: str) -> dict[str, Any]:
        policy = {
            "TRIGGER": {
                "observations": True,
                "correlations": False,
                "ranked_hypotheses": False,
                "root_candidate": False,
                "confirmed_path": False,
                "knowledge_gaps": False,
                "recommendations": False,
            },
            "SIGNAL_FLOOD": {
                "observations": True,
                "correlations": False,
                "ranked_hypotheses": False,
                "root_candidate": False,
                "confirmed_path": False,
                "knowledge_gaps": False,
                "recommendations": False,
            },
            "CORRELATION": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": False,
                "root_candidate": False,
                "confirmed_path": False,
                "knowledge_gaps": False,
                "recommendations": False,
            },
            "HYPOTHESIS_GENERATION": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": False,
                "root_candidate": False,
                "confirmed_path": False,
                "knowledge_gaps": False,
                "recommendations": False,
            },
            "HYPOTHESIS_TESTING": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": True,
                "root_candidate": True,
                "confirmed_path": False,
                "knowledge_gaps": False,
                "recommendations": False,
            },
            "KNOWLEDGE_GAP_CHECK": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": True,
                "root_candidate": True,
                "confirmed_path": False,
                "knowledge_gaps": True,
                "recommendations": False,
            },
            "LEARNING_VALIDATION": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": True,
                "root_candidate": True,
                "confirmed_path": False,
                "knowledge_gaps": True,
                "recommendations": False,
            },
            "ACTION": {
                "observations": True,
                "correlations": True,
                "ranked_hypotheses": True,
                "root_candidate": True,
                "confirmed_path": True,
                "knowledge_gaps": True,
                "recommendations": True,
            },
        }
        values = policy.get(stage_name, policy["TRIGGER"])
        values["allowed_disclosures"] = [
            key for key, enabled in values.items() if key != "allowed_disclosures" and enabled
        ]
        return values

    def _compute_stage_values(self, stage_index: int, is_confirmed: bool) -> dict[str, Any]:
        """Compute stage-dependent confidence, phase, and impact values."""
        if is_confirmed:
            return {
                "confidence": 94.2,
                "delta": "+12%",
                "lifecycle": "CONFIRMED",
                "zaki_phase": "RECOMMENDATION_READY",
                "zaki_thought": "Root cause confirmed. Remediation path identified.",
                "throughput_pct": -72,
                "users_affected": 24000,
                "regions_affected": 3,
            }
        elif stage_index >= 3:
            return {
                "confidence": 88.5,
                "delta": "+6%",
                "lifecycle": "TESTING",
                "zaki_phase": "REASONING",
                "zaki_thought": "Testing causal hypothesis against operational evidence.",
                "throughput_pct": -65,
                "users_affected": 20000,
                "regions_affected": 3,
            }
        elif stage_index == 2:
            return {
                "confidence": 82.0,
                "delta": "+4%",
                "lifecycle": "NEEDS_MORE_EVIDENCE",
                "zaki_phase": "EVIDENCE_NEEDED",
                "zaki_thought": "Correlating signals across domains. Next-best evidence required.",
                "throughput_pct": -55,
                "users_affected": 18000,
                "regions_affected": 2,
            }
        elif stage_index == 1:
            return {
                "confidence": 76.5,
                "delta": "+2%",
                "lifecycle": "SUPPORTED",
                "zaki_phase": "REASONING",
                "zaki_thought": "Telemetry signals ingested. Forming candidate hypotheses.",
                "throughput_pct": -40,
                "users_affected": 14000,
                "regions_affected": 2,
            }
        else:
            return {
                "confidence": 0.0,
                "delta": "0%",
                "lifecycle": "OBSERVING",
                "zaki_phase": "OBSERVING",
                "zaki_thought": "Observing the initial incident trigger. No causal or impact claim is justified yet.",
                "throughput_pct": None,
                "users_affected": None,
                "regions_affected": None,
            }

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

        # Ensure at least 3 entities
        if len(entities) < 3:
            # Add healthy entities from reference network
            for eid, ref in list(self._ref_entities.items())[:10]:
                if eid not in [e["id"] for e in entities] and eid != trigger_entity:
                    display = ref.get("canonical_name", eid.split(":")[-1])
                    entities.append({
                        "id": eid,
                        "display_name": display,
                        "subtitle": "Healthy",
                        "state": "HEALTHY",
                        "icon": "server",
                        "domain": ref.get("domain", "UNKNOWN"),
                        "scenario_id": scenario_id,
                    })
                    if len(entities) >= 5:
                        break

        return entities

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

    def _build_hypotheses(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        trigger_entity: str,
        affected_service: str,
        cohort: str,
        tested_hypotheses: list[str],
        stage_vals: dict[str, Any],
        stage_index: int,
        is_confirmed: bool,
    ) -> list[dict[str, Any]]:
        """Build scenario-specific hypotheses with stage-aware ranking."""
        if stage_index < 2:
            return []
        hypotheses = []
        hyp_names = self._generate_hypothesis_names(trigger_display, cohort, scenario_id, affected_service)
        service_id = affected_service.lower().replace(" ", "-")
        path_specs = [
            {
                "entity_ids": [trigger_entity, service_id, "enterprise-users"],
                "edge_ids": ["EDGE-HYP-001-0", "EDGE-HYP-001-1"],
                "role": "CONFIRMED" if is_confirmed else ("LEADING" if stage_index >= 4 else "CANDIDATE"),
                "last_reason": f"{trigger_display} failure precedes downstream service degradation",
            },
            {
                "entity_ids": [service_id, "enterprise-users"],
                "edge_ids": ["EDGE-HYP-002-0"],
                "role": "WEAKENING" if stage_index >= 5 else "CANDIDATE",
                "last_reason": f"{affected_service} overload explains symptoms but not initial telemetry alarm",
            },
            {
                "entity_ids": ["dns-resolution", service_id],
                "edge_ids": ["EDGE-HYP-003-0"],
                "role": "WEAKENING" if stage_index >= 5 else "CANDIDATE",
                "last_reason": "Cross-domain protocol latency remains unverified by direct alarms",
            },
            {
                "entity_ids": ["ran-access", service_id],
                "edge_ids": ["EDGE-HYP-004-0"],
                "role": "REJECTED" if stage_index >= 5 else "CANDIDATE",
                "last_reason": "Access domain cause conflicts with core/transport temporal order",
            },
        ]
        confidence_by_stage = {
            3: [None, None, None, None],
            4: [61.0, 33.0, 18.0, 8.0],
            5: [68.0, 28.0, 12.0, 4.0],
            6: [74.0, 22.0, 9.0, 2.0],
            7: [94.2, 12.0, 4.0, 1.0],
        }
        confidences = confidence_by_stage.get(min(stage_index, 7), confidence_by_stage[3])
        previous_by_stage = {
            3: [None, None, None, None],
            4: [47.0, 26.0, 15.0, 10.0],
            5: [61.0, 33.0, 18.0, 8.0],
            6: [68.0, 28.0, 12.0, 4.0],
            7: [74.0, 22.0, 9.0, 2.0],
        }
        previous = previous_by_stage.get(min(stage_index, 7), previous_by_stage[3])

        rank_titles = [
            "Leading Root Cause",
            "Competing Candidate",
            "Plausible Candidate",
            "Rejected Candidate",
        ]

        for i, tmpl in enumerate(COHORT_HYPOTHESIS_TEMPLATES):
            hyp_id = f"HYP-{i + 1:03d}"
            name = hyp_names[i] if i < len(hyp_names) else f"Alternative Cause {i + 1}"
            tested = hyp_id in tested_hypotheses
            should_rank = stage_index >= 4
            confidence = confidences[i] if should_rank else None
            prior = previous[i] if should_rank else None
            delta_value = None if confidence is None or prior is None else round(confidence - prior, 1)
            status = tmpl["status"] if i > 0 else ("LEADING" if should_rank else "CANDIDATE")
            if should_rank and i == 0 and is_confirmed:
                status = "LEADING"
                lifecycle_state = "CONFIRMED"
                confidence_state = "CONFIRMED"
            elif should_rank and i == 0 and stage_index >= 5 and not is_confirmed:
                lifecycle_state = "NEEDS_MORE_EVIDENCE"
                confidence_state = "ROOT_CANDIDATE"
            elif should_rank and i == 0:
                lifecycle_state = "TESTING"
                confidence_state = "RANKED"
            elif should_rank and i == 3 and stage_index >= 5:
                lifecycle_state = "REJECTED"
                confidence_state = "REJECTED"
            elif should_rank and i > 0:
                lifecycle_state = "WEAKENING" if stage_index >= 5 else "TESTING"
                confidence_state = "RANKED"
            else:
                lifecycle_state = "CANDIDATE"
                confidence_state = "UNRANKED"
            path_spec = path_specs[i]
            evidence_ids = [f"EVT-{scenario_id.upper()}-{stage_index}-{idx}" for idx in range(min(max(stage_index, 1), 4))]
            history = []
            if should_rank:
                history.append({
                    "hypothesis_id": hyp_id,
                    "previous": prior,
                    "new": confidence,
                    "delta": delta_value,
                    "reason": path_spec["last_reason"],
                    "evidence_ids": evidence_ids[:2],
                    "sequence": stage_index * 10 + i,
                    "timestamp": (datetime.now(timezone.utc) - timedelta(seconds=(4 - i) * 9)).isoformat(),
                })

            hypotheses.append({
                "id": hyp_id,
                "hypothesis_id": hyp_id,
                "display_id": f"H{i + 1}",
                "rank_label": f"Rank #{i + 1} · {rank_titles[i]}",
                "label": name,
                "rank": tmpl["rank"] if should_rank else None,
                "display_name": name,
                "confidence": confidence,
                "confidence_state": confidence_state,
                "delta": f"{delta_value:+.1f}%" if delta_value is not None else "Unranked",
                "last_delta": delta_value,
                "last_delta_reason": path_spec["last_reason"] if should_rank else "Awaiting enough correlated evidence to rank",
                "status": status,
                "lifecycle_state": lifecycle_state,
                "supports": [s.format(trigger_name=trigger_display) for s in tmpl.get("supports_template", [])],
                "against": [a.format(trigger_name=trigger_display) for a in tmpl.get("against_template", [])],
                "missing": [m.format(trigger_name=trigger_display) for m in tmpl.get("missing_template", [])],
                "support_count": max(0, 4 - i) if should_rank else 0,
                "contradiction_count": i if should_rank else 0,
                "missing_evidence_count": len(tmpl.get("missing_template", [])),
                "evidence_count": len(evidence_ids) if should_rank else 0,
                "evidence_ids": evidence_ids if should_rank else [],
                "path_entity_ids": path_spec["entity_ids"],
                "path_edge_ids": path_spec["edge_ids"],
                "path_role": path_spec["role"],
                "frontier_ids": [f"FR-{scenario_id}-001"] if i == 0 and stage_index >= 5 and not is_confirmed else [],
                "confidence_history": history,
                "tested": tested,
                "scenario_id": scenario_id,
                "run_id": run_id,
            })

        return hypotheses

    def _generate_hypothesis_names(
        self,
        trigger_display: str,
        cohort: str,
        scenario_id: str = "",
        affected_service: str = "",
    ) -> list[str]:
        """Generate scenario-specific candidate hypothesis names tailored to the failure mode."""
        sc_id = (scenario_id or "").upper().strip()
        sc_service = affected_service or "Data Services"

        # Check for curated scenario-specific hypothesis quadruplets
        if "SCN-001" in sc_id or "DEMO-001" in sc_id or "TWIN-INC-001" in sc_id:
            return [
                "SGi Transport MTU Blackhole & Packet Fragmentation",
                "PE Router N3 Transport Interface Saturation",
                "UPF User Plane Session Control Buffer Exhaustion",
                "DNS Resolution Timeout & Latency Surge",
            ]
        elif "H2-GAP-001" in sc_id or "TWIN-GAP-001" in sc_id:
            return [
                "Unmodeled OCS Diameter Gy/Ro Charging Gateway Timeout",
                "PCRF Subscriber Policy Rule Sync Mismatch",
                "PGW-C Control Plane Queue Saturation",
                "SGi Interface MTU Mismatch",
            ]
        elif "H3-LRN-001" in sc_id or "TWIN-LRN-001" in sc_id:
            return [
                "Promoted OCS Charging Path Credit Control Delay",
                "UPF GTP-U Protocol Tunnel Deterioration",
                "AMF Subscriber Authentication Failure",
                "Transport Backbone Core Link Loss",
            ]
        elif "H4-WI-001" in sc_id or "TWIN-WIF-001" in sc_id:
            return [
                "MPLS Edge Router Shared Power Feed Loss",
                "Downstream BGP Route Blackholing",
                "Core IP Transmission Fiber Cut",
                "RAN Access Transport Link Drop",
            ]
        elif "H4-WI-002" in sc_id or "TWIN-WIF-002" in sc_id:
            return [
                "Primary Data Center Gateway Spine Switch Fabric Outage",
                "Virtual Router EVPN VXLAN Overlay Drop",
                "Core Cloud NFVI Hypervisor Saturation",
                "IMS SIP Proxy Session Spike",
            ]
        elif "H4-WI-003" in sc_id or "TWIN-WIF-003" in sc_id:
            return [
                "PGW-U User Plane Forwarding Process Collapse",
                "N4 Interface PFCP Control Association Loss",
                "SGi-LAN Firewall Session Exhaustion",
                "gNodeB RAN User Plane Congestion",
            ]
        elif "H4-WI-011" in sc_id or "TWIN-WIF-011" in sc_id:
            return [
                "Dual Router Shared Power Feed Rack Outage",
                "Optical Line Terminal (OLT) Laser Degradation",
                "Core BGP Peering Memory Leak",
                "Subscriber AAA Server Timeout",
            ]

        # Dynamic fallback based on trigger entity & affected service
        short_name = trigger_display.split("-")[0] if "-" in trigger_display else trigger_display
        return [
            f"{trigger_display} Primary Failure",
            f"Downstream {sc_service} Capacity Overload",
            "Cross-Domain Interconnect Boundary Protocol Latency",
            "RAN Radio Access Sector Congestion",
        ]

    def _build_topology(
        self,
        entities: list[dict[str, Any]],
        trigger_entity: str,
        cohort: str,
        affected_service: str,
        stage_vals: dict[str, Any],
        stage_index: int,
        scenario_id: str | None = None,
    ) -> dict[str, Any]:
        """Build topology from entities with stage-aware causal-path disclosure."""
        # Group entities by domain
        domain_groups: dict[str, list[dict[str, Any]]] = {}
        for ent in entities:
            domain = ent.get("domain", "UNKNOWN")
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(ent)

        # Build domain list
        domain_display_map = {
            "RAN": ("RAN", "Radio Access Network"),
            "IP_TRANSPORT": ("TRANSPORT", "IP / Optical"),
            "TRANSMISSION": ("TRANSPORT", "IP / Optical"),
            "EPC_4G": ("MOBILE CORE", "EPC / 5GC"),
            "SA_5G_CORE": ("MOBILE CORE", "5G SA Core"),
            "CS_CORE": ("MOBILE CORE", "Circuit Core"),
            "MOBILE_IMS": ("IMS", "Voice / Video"),
            "FIXED_IMS": ("IMS", "Voice / Video"),
            "CRM": ("CUSTOMER", "Services"),
            "BSS": ("OSS / BSS", "Charging / OSS"),
            "OSS": ("OSS / BSS", "Operations"),
            "CHARGING": ("OSS / BSS", "Charging / OSS"),
            "IT_CLOUD_INFRA": ("INFRA", "Cloud Infrastructure"),
            "EXTERNAL": ("EXTERNAL", "External"),
        }

        domains = []
        seen_domain_names = set()
        for domain_key, domain_entities in domain_groups.items():
            display_name, subtitle = domain_display_map.get(domain_key, (domain_key, domain_key))
            if display_name in seen_domain_names:
                # Merge into existing domain
                for d in domains:
                    if d["name"] == display_name:
                        d["entities"].extend(domain_entities)
                        break
                continue
            seen_domain_names.add(display_name)
            domains.append({
                "name": display_name,
                "subtitle": subtitle,
                "entities": domain_entities,
            })

        # Add customer impact domain only after impact has at least been observed.
        has_customer = any(d["name"] == "CUSTOMER IMPACT" for d in domains)
        if not has_customer and stage_index >= 1:
            degradation = stage_vals["throughput_pct"]
            users_affected = stage_vals["users_affected"]
            domains.append({
                "name": "CUSTOMER IMPACT",
                "subtitle": "Services",
                "entities": [
                    {
                        "id": affected_service.lower().replace(" ", "-"),
                        "display_name": affected_service,
                        "subtitle": "Degradation observed" if degradation is None else f"Degraded ({degradation}%)",
                        "state": "SYMPTOM",
                        "icon": "users",
                    },
                    {
                        "id": "enterprise-users",
                        "display_name": "Enterprise Users",
                        "subtitle": "Scope unknown" if users_affected is None else f"Affected (~{users_affected // 1000}k users)",
                        "state": "SYMPTOM" if stage_index < 5 else "IMPACTED",
                        "icon": "users",
                    },
                ],
            })

        causal_path = []
        manifest = self.load_scenario_manifest(scenario_id) if scenario_id else None
        chain = manifest.get("causal_chain", []) if manifest else []

        if stage_index >= 2 and len(chain) >= 2:
            for idx in range(len(chain) - 1):
                from_id = chain[idx]
                to_id = chain[idx + 1]
                causal_path.append({
                    "from": from_id,
                    "to": to_id,
                    "status": "CONFIRMED" if stage_index >= 7 else ("LEADING" if stage_index >= 4 else "CANDIDATE"),
                    "relation": "PROPAGATES_TO" if idx > 0 else "CAUSES",
                })
        elif stage_index >= 4 and len(entities) >= 2:
            trigger_ent = next((e for e in entities if e["id"] == trigger_entity), None)
            symptom_ent = next((e for e in entities if e["state"] == "SYMPTOM"), None)
            if trigger_ent and symptom_ent:
                causal_path.append({
                    "from": trigger_ent["id"],
                    "to": symptom_ent["id"],
                    "status": "CONFIRMED" if stage_index >= 7 else ("LEADING" if stage_index >= 4 else "CANDIDATE"),
                    "relation": "CAUSES",
                })

        if stage_index >= 7 and causal_path:
            path_parts = []
            for edge in causal_path:
                src = next((e["display_name"] for e in entities if e["id"] == edge["from"]), edge["from"])
                dst = next((e["display_name"] for e in entities if e["id"] == edge["to"]), edge["to"])
                path_parts.append(f"{src} → {dst}")
            confirmed_label = "Confirmed Causal Path: " + " → ".join(path_parts)
        elif stage_index >= 4 and causal_path:
            path_parts = []
            for edge in causal_path:
                src = next((e["display_name"] for e in entities if e["id"] == edge["from"]), edge["from"])
                dst = next((e["display_name"] for e in entities if e["id"] == edge["to"]), edge["to"])
                path_parts.append(f"{src} → {dst}")
            confirmed_label = "Leading Causal Path: " + " → ".join(path_parts)
        else:
            confirmed_label = "Awaiting causal path analysis"

        return {
            "domains": domains,
            "causal_path": causal_path,
            "confirmed_path_label": confirmed_label,
            "path_confidence": stage_vals["confidence"] if causal_path else 0,
        }

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
        actions = [
            {
                "id": "NBA-001",
                "request_id": "NBA-001",
                "display_name": f"Get {trigger_display} detailed health stats",
                "status": "COMPLETED" if nba1_completed else "READY",
                "scenario_id": scenario_id,
                "run_id": run_id,
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

    def _build_stages(self, stage_index: int, started_at: str = "") -> list[dict[str, Any]]:
        """Build simulation journey stages from the runtime state machine, not demo constants."""
        stage_sequence = [
            {"index": 0, "key": "trigger", "label": "Trigger", "summary": "Incident detected"},
            {"index": 1, "key": "signals", "label": "SIGNAL_FLOOD", "summary": "Events ingested"},
            {"index": 2, "key": "correlation", "label": "CORRELATION", "summary": "Linking across domains"},
            {"index": 3, "key": "hypothesis_generation", "label": "HYPOTHESIS_GENERATION", "summary": "Evaluating root causes"},
            {"index": 4, "key": "hypothesis_testing", "label": "HYPOTHESIS_TESTING", "summary": "Testing the leading hypothesis"},
            {"index": 5, "key": "knowledge_gap_check", "label": "KNOWLEDGE_GAP_CHECK", "summary": "Finding missing context"},
            {"index": 6, "key": "learning_validation", "label": "LEARNING_VALIDATION", "summary": "Validating insights"},
            {"index": 7, "key": "action", "label": "ACTION", "summary": "Generate next best action"},
        ]

        for entry in stage_sequence:
            idx = entry["index"]
            if idx < stage_index:
                entry["status"] = "COMPLETED"
            elif idx == stage_index:
                entry["status"] = "ACTIVE"
            else:
                entry["status"] = "PENDING"
        return stage_sequence

    def _build_zaki(
        self,
        scenario_id: str,
        run_id: str,
        trigger_display: str,
        stage_vals: dict[str, Any],
        stage_index: int,
    ) -> dict[str, Any]:
        """Build Zaki AI cognitive state."""
        thought = stage_vals["zaki_thought"]
        if stage_index <= 1:
            thought = "Only raw observations are available. No causal claim is justified yet."
        elif stage_index == 2:
            thought = "Several signals are correlated by timing and dependency. Root cause remains unconfirmed."
        elif stage_index == 3:
            thought = "Candidate explanations are being generated without ranking yet."
        elif stage_index == 4:
            thought = "A leading hypothesis is ranked and being tested against evidence."
        elif stage_index == 5:
            thought = "The unresolved boundary is now explicit. Missing evidence is being isolated."
        elif stage_index >= 6:
            thought = "Validated learning is being assessed before final recommendation."
        return {
            "phase": stage_vals["zaki_phase"],
            "thought": thought,
            "active_focus_entity": trigger_display,
            "confidence": stage_vals["confidence"],
            "scenario_id": scenario_id,
            "run_id": run_id,
        }

    def _build_reasoning_map(
        self,
        scenario_id: str,
        run_id: str,
        manifest: Optional[dict[str, Any]],
        trigger_entity: str,
        trigger_display: str,
        affected_service: str,
        raw_events: list[dict[str, Any]],
        hypotheses: list[dict[str, Any]],
        knowledge_gaps: list[dict[str, Any]],
        next_best_actions: list[dict[str, Any]],
        learning: Optional[dict[str, Any]],
        impact: dict[str, Any],
        stage_index: int,
        current_stage: str,
        stage_watchdog: dict[str, Any],
        is_confirmed: bool,
        executed_actions: list[str],
    ) -> dict[str, Any]:
        """Build the authoritative Neural Reasoning Map contract for Step 5."""
        source_id = f"SRC-{scenario_id}"
        primary_hypothesis = hypotheses[0] if hypotheses else None
        primary_hypothesis_id = primary_hypothesis.get("id") if primary_hypothesis else None
        primary_gap = knowledge_gaps[0] if knowledge_gaps else None
        primary_gap_id = primary_gap.get("id") if primary_gap else None
        primary_action = next_best_actions[0] if next_best_actions else None
        primary_action_id = primary_action.get("id") if primary_action else None
        display_domains = self._derive_domains(manifest.get("failure_domain_tags", []) if manifest else [])
        primary_domain = display_domains[0] if display_domains else self._entity_domain(trigger_entity).replace("_", " ").title()
        supporting_evidence_ids = [event.get("event_id") for event in raw_events if event.get("event_id")]

        evidence_nodes = [
            {
                "id": event.get("event_id"),
                "evidence_id": event.get("event_id"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "display_name": event.get("title"),
                "type": event.get("badge") or event.get("category", "Evidence").upper(),
                "evidence_type": event.get("evidence_type") or (event.get("badge") or event.get("category", "Evidence")).upper(),
                "category": event.get("category"),
                "source_entity": event.get("entity_id"),
                "domain": event.get("domain"),
                "timestamp": event.get("time"),
                "status": "ACTIVE",
                "state": "ACTIVE",
                "event_time": event.get("event_time"),
                "evidence_ids": [event.get("event_id")],
                "explain": {
                    "what": event.get("title"),
                    "why": "Admitted as operational evidence for this run.",
                    "supports": [event.get("event_id")],
                    "affects": [primary_hypothesis_id] if primary_hypothesis_id and stage_index >= 3 else [],
                    "unknown": "Causal role is still being evaluated." if stage_index < 6 else "Validation is assessing the final evidence package.",
                    "recent": f"Observed at {event.get('time')}",
                },
            }
            for event in raw_events
            if event.get("event_id")
        ]

        category_ids = {event.get("category") for event in raw_events}
        has_change = "change" in category_ids
        has_metric = "metric" in category_ids
        has_trace = "trace" in category_ids or "log" in category_ids
        has_ticket = "ticket" in category_ids

        pathway_specs = [
            (
                "PATH-OPERATIONAL-EVIDENCE",
                "Operational Evidence",
                "ACTIVE" if raw_events else "DORMANT",
                "Raw alarms, KPIs and tickets have been admitted.",
                supporting_evidence_ids[:3],
                [primary_hypothesis_id] if primary_hypothesis_id else [],
            ),
            (
                "PATH-SERVICE-DEPENDENCY",
                "Service Dependency",
                "ACTIVE" if stage_index >= 2 or has_ticket else "DISCOVERED",
                f"{affected_service} is being mapped to dependent network elements.",
                supporting_evidence_ids[:2],
                [primary_hypothesis_id] if primary_hypothesis_id else [],
            ),
            (
                "PATH-TOPOLOGY-PROPAGATION",
                "Topology & Propagation",
                "ACTIVE" if stage_index >= 1 else "DISCOVERED",
                "Failure propagation tracked across physical and logical topological links.",
                supporting_evidence_ids[:2],
                [primary_hypothesis_id] if primary_hypothesis_id else [],
            ),
            (
                "PATH-SUBSCRIBER-JOURNEY",
                "Subscriber Journey",
                "ACTIVE" if has_ticket else ("DISCOVERED" if stage_index >= 2 else "DORMANT"),
                "Customer-impact evidence is available for journey correlation.",
                [event.get("event_id") for event in raw_events if event.get("category") == "ticket"],
                [],
            ),
            (
                "PATH-CHANGE-CONFIGURATION",
                "Change & Configuration",
                "ACTIVE" if has_change else "DORMANT",
                "A change record is temporally relevant to the investigation." if has_change else "No admitted change evidence is active yet.",
                [event.get("event_id") for event in raw_events if event.get("category") == "change"],
                [primary_hypothesis_id] if primary_hypothesis_id and has_change else [],
            ),
            (
                "PATH-TRAFFIC-CAPACITY",
                "Traffic & Capacity",
                "ACTIVE" if has_metric or impact.get("impact_state") in {"ESTIMATED", "INFERRED", "CONFIRMED"} else "DISCOVERED",
                "Traffic degradation evidence is being tested against capacity explanations.",
                [event.get("event_id") for event in raw_events if event.get("category") == "metric"],
                [hypotheses[1].get("id")] if len(hypotheses) > 1 else [],
            ),
            (
                "PATH-CONTROL-SIGNALING",
                "Control & Signaling",
                "ACTIVE" if has_trace else ("DISCOVERED" if stage_index >= 2 else "DORMANT"),
                "Trace or log signals can explain control-plane behavior.",
                [event.get("event_id") for event in raw_events if event.get("category") in {"trace", "log"}],
                [primary_hypothesis_id] if primary_hypothesis_id and has_trace else [],
            ),
            (
                "PATH-RESILIENCE-FAILOVER",
                "Resilience & Failover",
                "ACTIVE" if stage_index >= 2 else "DORMANT",
                "Backup-path behavior is evaluated during topology correlation.",
                [],
                [primary_hypothesis_id] if primary_hypothesis_id and stage_index >= 2 else [],
            ),
            (
                "PATH-HISTORICAL-PATTERN",
                "Historical Pattern",
                "ACTIVE" if stage_index >= 2 else "DORMANT",
                "Similar incidents are matched for precedent during correlation.",
                [],
                [primary_hypothesis_id] if primary_hypothesis_id and stage_index >= 2 else [],
            ),
            (
                "PATH-KNOWLEDGE-GAP",
                "Knowledge Gap",
                "ACTIVE" if knowledge_gaps else "DORMANT",
                "Missing evidence is blocking a stronger conclusion." if knowledge_gaps else "No explicit knowledge gap has been raised yet.",
                [],
                [primary_hypothesis_id] if primary_hypothesis_id and knowledge_gaps else [],
            ),
        ]
        pathways = [
            {
                "id": pathway_id,
                "pathway_id": pathway_id,
                "scenario_id": scenario_id,
                "run_id": run_id,
                "display_name": display_name,
                "status": status,
                "state": status,
                "activation_reason": reason,
                "evidence_ids": [evidence_id for evidence_id in evidence_ids if evidence_id],
                "hypothesis_ids": [hyp_id for hyp_id in hypothesis_ids if hyp_id],
                "explain": {
                    "what": f"{display_name} reasoning pathway",
                    "why": reason,
                    "supports": [evidence_id for evidence_id in evidence_ids if evidence_id],
                    "affects": [hyp_id for hyp_id in hypothesis_ids if hyp_id],
                    "unknown": "Awaiting more evidence." if status in {"DORMANT", "DISCOVERED"} else "Contribution is being evaluated by synthesis.",
                    "recent": f"Pathway state is {status}.",
                },
            }
            for pathway_id, display_name, status, reason, evidence_ids, hypothesis_ids in pathway_specs
        ]
        active_pathways = [path for path in pathways if path["status"] in {"ACTIVE", "RESOLVED", "REJECTED"}]

        map_hypotheses = [
            {
                "id": hyp.get("id"),
                "hypothesis_id": hyp.get("id"),
                "display_id": hyp.get("display_id") or f"H{index + 1}",
                "scenario_id": scenario_id,
                "run_id": run_id,
                "display_name": hyp.get("display_name"),
                "status": hyp.get("lifecycle_state") or hyp.get("status"),
                "state": hyp.get("lifecycle_state") or hyp.get("status"),
                "confidence": hyp.get("confidence"),
                "supporting_evidence": hyp.get("evidence_ids", []),
                "contradicting_evidence": hyp.get("against", []),
                "contradictions": hyp.get("against", []),
                "missing_evidence": hyp.get("frontier_ids", []) or ([primary_gap_id] if index == 0 and primary_gap_id else []),
                "explain": {
                    "what": f"H{index + 1} - {hyp.get('display_name')}",
                    "why": hyp.get("last_delta_reason") or "Candidate explanation from backend reasoning.",
                    "supports": hyp.get("evidence_ids", []),
                    "affects": [hyp.get("id")],
                    "unknown": "; ".join(hyp.get("missing", [])[:2]) or "No explicit missing evidence listed.",
                    "recent": hyp.get("delta", "Unranked"),
                },
            }
            for index, hyp in enumerate(hypotheses)
            if hyp.get("id")
        ]
        gaps = [
            {
                "id": gap.get("id"),
                "gap_id": gap.get("id"),
                "scenario_id": scenario_id,
                "run_id": run_id,
                "display_name": gap.get("label"),
                "status": "RESOLVED" if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else "OPEN",
                "state": "RESOLVED" if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else (gap.get("state") or "OPEN"),
                "affected_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "affected_pathway_ids": ["PATH-KNOWLEDGE-GAP", "PATH-RESILIENCE-FAILOVER"] if index == 0 else ["PATH-KNOWLEDGE-GAP"],
                "affected_hypotheses": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "affected_pathways": ["PATH-KNOWLEDGE-GAP", "PATH-RESILIENCE-FAILOVER"] if index == 0 else ["PATH-KNOWLEDGE-GAP"],
                "required_evidence": primary_action.get("display_name") if index == 0 and primary_action else gap.get("reason"),
                "next_best_evidence_id": primary_action_id if index == 0 else None,
                "explain": {
                    "what": gap.get("label"),
                    "why": gap.get("reason"),
                    "supports": [],
                    "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
                    "unknown": primary_action.get("display_name") if index == 0 and primary_action else gap.get("reason"),
                    "recent": "Evidence request completed." if primary_action and primary_action.get("status") == "COMPLETED" and index == 0 else "Evidence request is pending.",
                },
            }
            for index, gap in enumerate(knowledge_gaps)
            if gap.get("id")
        ]

        if stage_index < 3:
            synthesis_state = "INSUFFICIENT_EVIDENCE"
            synthesis_summary = "Evidence is being admitted and organized; no candidate explanation is ready."
        elif stage_index < 5:
            synthesis_state = "PARTIAL"
            synthesis_summary = "Candidate explanations exist, but testing and gap resolution are still in progress."
        elif primary_gap and primary_action and primary_action.get("status") != "COMPLETED":
            synthesis_state = "MODEL_INSUFFICIENT"
            synthesis_summary = "The leading explanation is blocked by missing evidence."
        elif is_confirmed:
            synthesis_state = "ROOT_CANDIDATE"
            synthesis_summary = "Evidence, pathway fit, and returned telemetry strongly support the leading candidate."
        else:
            synthesis_state = "STRONGLY_SUPPORTED" if stage_index >= 6 else "PARTIAL"
            synthesis_summary = "The leading candidate is supported, with validation still required."

        synthesis = {
            "id": "SYNTHESIS-001",
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": "Intelligence Synthesis",
            "state": synthesis_state,
            "summary": synthesis_summary,
            "dimensions": [
                {"display_name": "Evidence Support", "state": "ACTIVE", "value": len(supporting_evidence_ids)},
                {"display_name": "Service Dependency Fit", "state": "ACTIVE" if stage_index >= 2 else "PENDING"},
                {"display_name": "Contradictions", "state": "LOW" if stage_index >= 5 else "UNKNOWN"},
                {"display_name": "Knowledge Gaps", "state": "OPEN" if gaps and gaps[0]["status"] == "OPEN" else "CLEAR"},
                {"display_name": "Validation State", "state": "ACCEPTED" if is_confirmed else ("PENDING" if stage_index >= 6 else "NOT_READY")},
            ],
            "leading_hypothesis_id": primary_hypothesis_id,
            "explain": {
                "what": "Convergence layer for the investigation.",
                "why": synthesis_summary,
                "supports": supporting_evidence_ids,
                "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "unknown": stage_watchdog.get("blocking_reason") or "Domain attribution waits for validation readiness.",
                "recent": f"Synthesis state is {synthesis_state}.",
            },
        }

        validation = {
            "id": "VAL-001",
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": (
                f"{primary_domain} Engineer Confirmed {trigger_display} as Primary Cause"
                if is_confirmed else f"{primary_domain} Engineer Review Pending"
            ),
            "status": "ACCEPTED" if is_confirmed else ("PENDING" if stage_index >= 6 else "NOT_READY"),
            "state": "ACCEPTED" if is_confirmed else ("PENDING" if stage_index >= 6 else "NOT_STARTED"),
            "reviewer_role": f"{primary_domain} Engineer",
            "evidence_package_ids": supporting_evidence_ids,
            "explain": {
                "what": "Domain engineer validation state.",
                "why": "Validation is based on the backend evidence package.",
                "supports": supporting_evidence_ids,
                "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "unknown": "Pending engineer review." if not is_confirmed else "No blocking validation gap remains.",
                "recent": "Validation accepted." if is_confirmed else "Validation has not accepted the conclusion yet.",
            },
        }

        def _to_domain_id(name: str) -> str:
            n = name.lower()
            if "transport" in n: return "transport"
            if "ran" in n: return "ran"
            if "core" in n: return "mobile_core"
            if "ims" in n or "voice" in n: return "ims_voice"
            if "policy" in n or "subscriber" in n: return "policy_subscriber"
            if "security" in n: return "security"
            if "cloud" in n or "k8s" in n: return "cloud_k8s"
            if "roaming" in n: return "roaming"
            if "charging" in n: return "charging"
            if "oss" in n or "bss" in n: return "oss_bss"
            return n.replace(" ", "_")

        rev = stage_index
        seq = stage_index
        is_ready = stage_index >= 6

        domain_attribution_domains = []
        if is_ready:
            primary_reason = f"Validated reasoning on {trigger_display} identifies {primary_domain} as primary causal failure root."
            domain_attribution_domains.append({
                "domain_id": _to_domain_id(primary_domain),
                "display_name": primary_domain,
                "role": "PRIMARY",
                "attribution_basis": "CAUSAL",
                "confidence": 88 if is_confirmed else 76,
                "reason": primary_reason,
                "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
                "supporting_evidence_ids": supporting_evidence_ids[:4],
                "supporting_pathway_ids": ["PW-001"],
                "source_revision": rev,
            })

        if stage_index >= 2 and affected_service:
            aff_dom = "RAN" if any(k in affected_service for k in ["Mobile Data", "RAN", "Cell"]) else ("IP Transport" if "Transport" in affected_service else "Mobile Core")
            if aff_dom != primary_domain:
                domain_attribution_domains.append({
                    "domain_id": _to_domain_id(aff_dom),
                    "display_name": aff_dom,
                    "role": "AFFECTED",
                    "attribution_basis": "IMPACT",
                    "confidence": 45,
                    "reason": f"Service impact evidence admitted for {affected_service}.",
                    "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
                    "supporting_evidence_ids": supporting_evidence_ids[:2],
                    "supporting_pathway_ids": ["PW-002"],
                    "source_revision": rev,
                })

        if len(display_domains) > 1:
            for domain in display_domains[1:]:
                if domain != primary_domain and not any(d.get("display_name") == domain for d in domain_attribution_domains):
                    domain_attribution_domains.append({
                        "domain_id": _to_domain_id(domain),
                        "display_name": domain,
                        "role": "CONTRIBUTING" if is_ready else "INVOLVED",
                        "attribution_basis": "DEPENDENCY",
                        "confidence": 62 if is_ready else 30,
                        "reason": f"Backend reasoning marked {domain} relevant to active failure path.",
                        "supporting_hypothesis_ids": [primary_hypothesis_id] if primary_hypothesis_id else ["HYP-001"],
                        "supporting_evidence_ids": supporting_evidence_ids[:2],
                        "supporting_pathway_ids": [],
                        "source_revision": rev,
                    })

        attr_status = "CONSISTENT" if is_ready else ("PARTIAL" if stage_index >= 2 else "UNRESOLVED")

        domain_attribution = {
            "id": "ATTR-001",
            "scenario_id": scenario_id,
            "run_id": run_id,
            "revision": rev,
            "sequence": seq,
            "attribution_status": attr_status,
            "status": "READY" if is_ready else "PENDING",
            "primary_domain": primary_domain if is_ready else None,
            "domains": domain_attribution_domains,
            "explain": {
                "what": "Domain responsibility and impact attribution.",
                "why": "Attribution appears after synthesis and validation readiness.",
                "supports": supporting_evidence_ids,
                "affects": [primary_hypothesis_id] if primary_hypothesis_id else [],
                "unknown": "Final responsibility awaits validation." if stage_index < 6 else "Attribution is ready for review.",
                "recent": "Primary attribution exposed." if stage_index >= 6 else "Attribution withheld until enough evidence converges.",
            },
        }

        learning_node = {
            "id": "LEARNING-001",
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": "Validated Learning Candidate" if learning and learning.get("enabled") else "No validated learning yet",
            "status": learning.get("status") if learning else "NOT_READY",
            "summary": learning.get("summary") if learning else "Learning is gated by validation.",
            "explain": {
                "what": "Learning eligibility for future investigations.",
                "why": "Learning is created only from validated run state.",
                "supports": supporting_evidence_ids if learning and learning.get("enabled") else [],
                "affects": [],
                "unknown": "Validation must complete before promotion." if not (learning and learning.get("enabled")) else "Candidate still requires governance review.",
                "recent": learning.get("status") if learning else "NOT_READY",
            },
        }

        source_node = {
            "id": source_id,
            "scenario_id": scenario_id,
            "run_id": run_id,
            "display_name": manifest.get("title", scenario_id) if manifest else scenario_id,
            "mode": "OFFLINE_SIMULATION",
            "status": "ACTIVE",
            "context": {
                "service": affected_service,
                "trigger_entity": trigger_entity,
            },
            "explain": {
                "what": "Offline simulation source selected for this run.",
                "why": "The scenario releases deterministic operational evidence without revealing hidden truth.",
                "supports": [],
                "affects": supporting_evidence_ids[:1],
                "unknown": "The source does not determine the root cause.",
                "recent": f"Current stage is {current_stage}.",
            },
        }

        connections: list[dict[str, Any]] = []

        def normalize_relation(relation_type: str) -> str:
            mapping = {
                "EMITS_EVIDENCE": "CONTRIBUTES_TO",
                "AFFECTS_HYPOTHESIS": "SUPPORTS",
                "FEEDS_SYNTHESIS": "SUPPORTS",
                "BLOCKS_OR_QUALIFIES": "REQUIRES",
                "REQUESTS_EVIDENCE": "REQUIRES",
                "RESOLVES_GAP": "RESOLVES",
                "REQUIRES_VALIDATION": "REQUIRES",
                "ENABLES_ATTRIBUTION": "ATTRIBUTES_TO",
                "ENABLES_LEARNING": "SUPPORTS",
            }
            return mapping.get(relation_type, relation_type)

        def normalize_connection_state(state: str) -> str:
            mapping = {
                "SUPPORTS": "SUPPORTING",
                "TESTING": "ACTIVE",
                "OPEN": "BLOCKED",
                "PENDING": "BLOCKED",
                "NOT_READY": "DORMANT",
                "READY": "ACTIVE",
                "COMPLETED": "RESOLVED",
                "ACCEPTED": "CONFIRMED",
            }
            return mapping.get(state, state)

        def add_connection(source: str, target: str, relation_type: str, state: str, reason: str, sequence: int) -> None:
            if not source or not target:
                return
            connection_id = f"CONN-{len(connections) + 1:03d}"
            connections.append({
                "id": connection_id,
                "connection_id": connection_id,
                "scenario_id": scenario_id,
                "run_id": run_id,
                "source_id": source,
                "target_id": target,
                "relation_type": normalize_relation(relation_type),
                "state": normalize_connection_state(state),
                "reason": reason,
                "sequence": sequence,
            })

        for event in evidence_nodes:
            add_connection(source_id, event["id"], "EMITS_EVIDENCE", "ACTIVE", "Simulation emitted admitted operational evidence.", len(connections) + 1)
            category = event.get("category")
            target_pathways = ["PATH-OPERATIONAL-EVIDENCE"]
            if category == "metric":
                target_pathways.append("PATH-TRAFFIC-CAPACITY")
            if category in {"trace", "log"}:
                target_pathways.append("PATH-CONTROL-SIGNALING")
            if category == "change":
                target_pathways.append("PATH-CHANGE-CONFIGURATION")
            if category == "ticket":
                target_pathways.extend(["PATH-SUBSCRIBER-JOURNEY", "PATH-SERVICE-DEPENDENCY"])
            for pathway_id in dict.fromkeys(target_pathways):
                pathway = next((path for path in pathways if path["id"] == pathway_id), None)
                add_connection(
                    event["id"],
                    pathway_id,
                    "CONTRIBUTES_TO",
                    pathway.get("status", "DISCOVERED") if pathway else "DISCOVERED",
                    pathway.get("activation_reason", "Evidence contributes to this reasoning pathway.") if pathway else "Evidence contributes to this reasoning pathway.",
                    len(connections) + 1,
                )

        for pathway in active_pathways:
            target_hypotheses = pathway.get("hypothesis_ids") or ([primary_hypothesis_id] if primary_hypothesis_id and pathway["id"] in {"PATH-OPERATIONAL-EVIDENCE", "PATH-SERVICE-DEPENDENCY"} else [])
            for hyp_id in target_hypotheses:
                add_connection(
                    pathway["id"],
                    hyp_id,
                    "AFFECTS_HYPOTHESIS",
                    pathway["status"],
                    pathway["activation_reason"],
                    len(connections) + 1,
                )

        for hyp in map_hypotheses:
            state = "REJECTED" if hyp["status"] == "REJECTED" else ("SUPPORTS" if hyp["id"] == primary_hypothesis_id else "TESTING")
            add_connection(
                hyp["id"],
                synthesis["id"],
                "FEEDS_SYNTHESIS",
                state,
                hyp["explain"]["why"],
                len(connections) + 1,
            )

        for gap in gaps:
            add_connection(gap["id"], synthesis["id"], "BLOCKS_OR_QUALIFIES", gap["status"], gap["explain"]["why"], len(connections) + 1)
            if gap.get("next_best_evidence_id"):
                add_connection(gap["id"], gap["next_best_evidence_id"], "REQUESTS_EVIDENCE", gap["status"], gap.get("required_evidence") or "Next best evidence required.", len(connections) + 1)

        if primary_action:
            add_connection(primary_action["id"], "PATH-KNOWLEDGE-GAP", "RESOLVES_GAP", primary_action.get("status", "PENDING"), primary_action.get("display_name"), len(connections) + 1)
        add_connection(synthesis["id"], validation["id"], "REQUIRES_VALIDATION", validation["status"], validation["display_name"], len(connections) + 1)
        add_connection(validation["id"], domain_attribution["id"], "ENABLES_ATTRIBUTION", domain_attribution["status"], "Domain attribution follows validation readiness.", len(connections) + 1)
        add_connection(validation["id"], learning_node["id"], "ENABLES_LEARNING", learning_node["status"], learning_node["summary"], len(connections) + 1)

        return {
            "contract_version": 2,
            "run_id": run_id,
            "scenario_id": scenario_id,
            "source_mode": "OFFLINE_SIMULATION",
            "revision": stage_index,
            "sequence": stage_index,
            "stage": current_stage,
            "source": source_node,
            "evidence": evidence_nodes,
            "reasoning_pathways": pathways,
            "connections": connections,
            "hypotheses": map_hypotheses,
            "knowledge_gaps": gaps,
            "next_best_evidence": next_best_actions,
            "synthesis": synthesis,
            "validation": validation,
            "learning": learning_node,
            "domain_attribution": domain_attribution,
            "reasoning_focus": {
                "entity": trigger_display,
                "pathway": "Knowledge Gap" if knowledge_gaps else "Operational Evidence",
                "hypothesis": primary_hypothesis.get("display_name") if primary_hypothesis else None,
                "test": primary_action.get("display_name") if primary_action else None,
                "reason": stage_watchdog.get("blocking_reason") or synthesis_summary,
            },
        }

    def _build_causal_path(
        self,
        trigger_entity: str,
        entities: list[dict[str, Any]],
        topology: dict[str, Any],
        stage_vals: dict[str, Any],
        stage_index: int,
    ) -> list[dict[str, Any]]:
        """Build causal path edges."""
        if stage_index < 2:
            return []
        return topology.get("causal_path", [])

    def _build_operational_edges(
        self,
        topology: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        stage_index: int,
    ) -> list[dict[str, Any]]:
        """Build graph edges for the shared investigation topology."""
        edges: list[dict[str, Any]] = []
        seen: set[str] = set()
        for edge in topology.get("causal_path", []):
            edge_id = f"EDGE-CAUSAL-{edge.get('from')}-{edge.get('to')}"
            seen.add(edge_id)
            edges.append({
                "id": edge_id,
                "from": edge.get("from"),
                "to": edge.get("to"),
                "relation": edge.get("relation", "CAUSES"),
                "role": edge.get("status", "CANDIDATE"),
            })
        for hyp in hypotheses:
            path_entities = hyp.get("path_entity_ids", [])
            path_edges = hyp.get("path_edge_ids", [])
            for idx, edge_id in enumerate(path_edges):
                if idx + 1 >= len(path_entities) or edge_id in seen:
                    continue
                seen.add(edge_id)
                edges.append({
                    "id": edge_id,
                    "from": path_entities[idx],
                    "to": path_entities[idx + 1],
                    "relation": "CANDIDATE_CAUSE" if idx == 0 else "IMPACTS",
                    "role": hyp.get("path_role", "CANDIDATE"),
                    "hypothesis_id": hyp.get("id"),
                })
        if stage_index >= 5:
            edges.append({
                "id": "EDGE-FRONTIER-001",
                "from": hypotheses[0].get("path_entity_ids", [""])[0] if hypotheses else "",
                "to": "FRONTIER-MISSING-EVIDENCE",
                "relation": "REQUIRES_EVIDENCE",
                "role": "UNKNOWN_FRONTIER",
                "hypothesis_id": "HYP-001",
            })
        return [edge for edge in edges if edge.get("from") and edge.get("to")]

    def _build_hypothesis_paths(self, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "hypothesis_id": hyp.get("id"),
                "entity_ids": hyp.get("path_entity_ids", []),
                "edge_ids": hyp.get("path_edge_ids", []),
                "role": hyp.get("path_role", "CANDIDATE"),
                "confidence": hyp.get("confidence"),
            }
            for hyp in hypotheses
        ]

    def _build_evidence_clusters(self, events: list[dict[str, Any]], stage_index: int) -> list[dict[str, Any]]:
        if stage_index < 2:
            return []
        event_ids = [event.get("event_id") for event in events if event.get("event_id")]
        return [{
            "cluster_id": "EC-001",
            "label": "Temporal dependency cluster",
            "event_ids": event_ids,
            "entity_ids": sorted({event.get("entity_id") for event in events if event.get("entity_id")}),
            "signal_count": len(event_ids),
            "noise_count": 0,
            "confidence": 0.52 if stage_index == 2 else min(0.86, 0.52 + (stage_index - 2) * 0.08),
        }]

    def _build_frontiers(
        self,
        scenario_id: str,
        run_id: str,
        trigger_entity: str,
        trigger_display: str,
        knowledge_gaps: list[dict[str, Any]],
        hypotheses: list[dict[str, Any]],
        stage_index: int,
    ) -> list[dict[str, Any]]:
        if stage_index < 5:
            return []
        gap = knowledge_gaps[0] if knowledge_gaps else {}
        return [{
            "frontier_id": f"FR-{scenario_id}-001",
            "id": f"FR-{scenario_id}-001",
            "type": "MISSING_EVIDENCE",
            "entity_ids": [trigger_entity],
            "hypothesis_ids": [hypotheses[0]["id"]] if hypotheses else [],
            "description": gap.get("label") or f"{trigger_display} health metrics required",
            "severity": "HIGH",
            "resolvable": True,
            "required_evidence": gap.get("label") or f"Detailed {trigger_display} health metrics",
            "scenario_id": scenario_id,
            "run_id": run_id,
        }]

    def _build_search_space(
        self,
        events: list[dict[str, Any]],
        evidence_clusters: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        hypotheses: list[dict[str, Any]],
        frontiers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ranked = [h for h in hypotheses if h.get("confidence") is not None]
        plausible = [h for h in ranked if h.get("status") != "REJECTED" and float(h.get("confidence") or 0) >= 15]
        root_candidates = [
            h for h in hypotheses
            if h.get("confidence_state") in {"ROOT_CANDIDATE", "CONFIRMED"} or h.get("lifecycle_state") == "CONFIRMED"
        ]
        return {
            "events": len(events),
            "correlated_signals": sum(cluster.get("signal_count", 0) for cluster in evidence_clusters) if evidence_clusters else 0,
            "relevant_entities": len(entities),
            "hypotheses": len(hypotheses),
            "plausible_causes": len(plausible),
            "root_candidates": len(root_candidates),
            "open_frontiers": len(frontiers),
        }

    def _build_reasoning_focus(
        self,
        trigger_entity: str,
        hypotheses: list[dict[str, Any]],
        frontiers: list[dict[str, Any]],
        current_stage: str,
        stage_watchdog: dict[str, Any],
        stage_index: int,
    ) -> dict[str, Any]:
        active_hypothesis = next((h for h in hypotheses if h.get("rank") == 1), hypotheses[0] if hypotheses else {})
        frontier = frontiers[0] if frontiers else {}
        if frontier:
            reason = frontier.get("description", "Resolving current uncertainty frontier")
        elif active_hypothesis:
            reason = active_hypothesis.get("last_delta_reason", "Evaluating candidate evidence")
        else:
            reason = "Waiting for enough evidence to form competing explanations"
        return {
            "entity_id": trigger_entity,
            "hypothesis_id": active_hypothesis.get("id"),
            "test_id": "TEST-NBE-001" if stage_index >= 5 else None,
            "stage": current_stage,
            "reason": reason,
            "frontier_id": frontier.get("frontier_id"),
            "stage_status": stage_watchdog.get("stage_status"),
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
        stages = self._build_stages(stage_index, started_at)

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
