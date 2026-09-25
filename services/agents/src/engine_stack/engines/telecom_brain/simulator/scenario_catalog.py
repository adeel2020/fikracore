"""Unified Scenario Catalog for FikraCore.

Exposes the full FikraCore conceptual capability model:
Understand (H1) -> Discover (H2) -> Learn (H3) -> Anticipate (H4).

Unifies declarative scenario YAMLs (e.g. DEMO-001), legacy incidents (SCN-001),
H2 gap scenarios, H3 learning units, and H4 what-if resilience scenarios into
one authoritative, searchable catalog.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import BaseModel, Field

STAGE_CONCEPT_MAP: dict[str, str] = {
    "H1": "Understand",
    "H2": "Discover",
    "H3": "Learn",
    "H4": "Anticipate",
}

CONCEPT_STAGE_MAP: dict[str, str] = {
    "UNDERSTAND": "H1",
    "DISCOVER": "H2",
    "LEARN": "H3",
    "ANTICIPATE": "H4",
}


def concept_for_stage(stage: str) -> str:
    return STAGE_CONCEPT_MAP.get(stage.upper(), "Understand")


def stage_for_concept(concept: str) -> str:
    return CONCEPT_STAGE_MAP.get(concept.upper(), "H1")


class UnifiedScenario(BaseModel):
    id: str
    display_name: str
    stage: str = "H1"
    concept: str = "Understand"
    scenario_type: str = "INCIDENT"  # INCIDENT, KNOWLEDGE_GAP, LEARNING_UNIT, WHAT_IF
    domains: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    description: str = ""
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: str = "L2"
    status: str = "READY"
    source: str = "declarative"
    demo_enabled: bool = True
    legacy: bool = False
    is_benchmark_run: bool = False
    scenario_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        return data


class ScenarioCatalog:
    """Authoritative scenario catalog consolidating all FikraCore scenarios."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent

        self._scenarios: dict[str, UnifiedScenario] = {}
        self._loaded: bool = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load_all()
            self._loaded = True

    def _load_all(self) -> None:
        self._scenarios.clear()

        # 1. Load Declarative Scenario YAMLs (scenarios/)
        self._load_declarative_scenarios()

        # 2. Load Legacy SCN-001 & H1 Incenarios
        self._load_h1_scenarios()

        # 3. Load H2 Knowledge Gap Scenarios
        self._load_h2_scenarios()

        # 4. Load H3 Learning Units
        self._load_h3_scenarios()

        # 5. Load H4 What-If Scenarios
        self._load_h4_scenarios()

    def _load_declarative_scenarios(self) -> None:
        scenarios_dir = self.base_dir / "scenarios"
        if not scenarios_dir.exists():
            return

        for path in sorted(scenarios_dir.glob("*.yaml")):
            if path.name == "h4_registry.yaml" or path.name == "index.yaml":
                continue
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue

            spec = data.get("spec") if isinstance(data.get("spec"), dict) else data
            scenario_id = str(spec.get("scenario_id") or spec.get("id") or data.get("id") or data.get("scenario_id") or path.stem).upper()
            if not scenario_id:
                continue

            stage = str(spec.get("stage") or data.get("stage") or "H1").upper()
            concept = concept_for_stage(stage)
            meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
            annotations = meta.get("annotations") if isinstance(meta.get("annotations"), dict) else {}

            display_name = str(
                annotations.get("presentation.telecom.ai/display-title")
                or spec.get("display_name")
                or spec.get("scenario_name")
                or data.get("display_name")
                or data.get("scenario_name")
                or scenario_id
            )
            
            classification = spec.get("classification") or data.get("classification") or {}
            explanation = spec.get("scenario_explanation") or data.get("scenario_explanation") or {}
            
            raw_domains = spec.get("domains") or classification.get("domains") or data.get("domains") or []
            raw_services = spec.get("affected_services") or classification.get("affected_services") or data.get("affected_services") or []
            domains = [str(d).replace("_", " ").title() for d in raw_domains]
            services = [str(s).replace("_", " ").title() for s in raw_services]
            aliases = [str(a) for a in (spec.get("aliases") or data.get("aliases") or [])]
            if meta.get("name") and meta["name"] not in aliases:
                aliases.append(meta["name"])

            demo_meta = spec.get("demo_metadata") or data.get("demo_metadata") or {}
            demo_enabled = bool(demo_meta.get("enabled", True)) if isinstance(demo_meta, dict) else True
            desc = str(
                annotations.get("presentation.telecom.ai/business-impact")
                or spec.get("description")
                or explanation.get("problem_statement")
                or data.get("description")
                or f"Declarative scenario {scenario_id}"
            )
            difficulty = str(spec.get("difficulty") or classification.get("difficulty_profile") or data.get("difficulty") or "L1")

            sc = UnifiedScenario(
                id=scenario_id,
                display_name=display_name,
                stage=stage,
                concept=concept,
                scenario_type=str(spec.get("scenario_type") or data.get("scenario_type") or "INCIDENT"),
                domains=domains or ["IP Transport", "5G SA Core", "CRM"],
                services=services or ["5G SA Mobile Data"],
                description=desc,
                aliases=aliases,
                difficulty=difficulty,
                status="READY" if demo_enabled else "AVAILABLE",
                source="declarative_scenario",
                demo_enabled=demo_enabled,
                scenario_path=str(path),
                metadata=data,
            )
            self._scenarios[scenario_id] = sc

    def _load_h1_scenarios(self) -> None:
        # All H1 scenarios (SCN-001 to SCN-100) are dynamically loaded from scenarios/ and runs/
        # Ensure standard aliases point to canonical records
        if "SCN-001" in self._scenarios:
            self._scenarios["TWIN-INC-001"] = self._scenarios["SCN-001"]
            self._scenarios["H1-INC-001"] = self._scenarios["SCN-001"]

    def _load_h2_scenarios(self) -> None:
        # Curated representative H2 scenario
        curated_h2 = UnifiedScenario(
            id="H2-GAP-001",
            display_name="Missing OCS Charging Dependency",
            stage="H2",
            concept="Discover",
            scenario_type="KNOWLEDGE_GAP",
            domains=["Mobile Core", "OCS"],
            services=["Subscriber Charging", "5G Data Session"],
            description="Exposes an unmodeled billing/charging dependency boundary causing unexplained service dropouts.",
            aliases=["TWIN-GAP-001", "missing ocs dependency", "charging gap", "H2-SCN-001"],
            tags=["charging", "ocs", "knowledge_gap", "boundary"],
            difficulty="K2",
            status="READY",
            source="h2_catalog",
            demo_enabled=True,
            scenario_path="simulator/h2_runs/RUN-H2-SCN-001-K1-SEED-52002/",
        )
        self._scenarios["H2-GAP-001"] = curated_h2
        self._scenarios["TWIN-GAP-001"] = curated_h2

        # Index available runs from h2_runs directory
        h2_dir = self.base_dir / "h2_runs"
        if h2_dir.exists():
            for d in sorted(h2_dir.iterdir()):
                if not d.is_dir() or not d.name.startswith("RUN-H2-"):
                    continue
                manifest_file = d / "scenario_manifest.yaml"
                if not manifest_file.exists():
                    continue
                try:
                    m = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
                except Exception:
                    continue
                sc_id = str(m.get("scenario_id") or d.name)
                if sc_id not in self._scenarios:
                    gap_type = str(m.get("gap_type") or "Knowledge Gap").replace("_", " ").title()
                    self._scenarios[sc_id] = UnifiedScenario(
                        id=sc_id,
                        display_name=f"{gap_type} ({sc_id})",
                        stage="H2",
                        concept="Discover",
                        scenario_type="KNOWLEDGE_GAP",
                        domains=["Transport", "Mobile Core"],
                        services=["Core Connectivity"],
                        description=f"Automated H2 knowledge gap scenario: {gap_type}.",
                        difficulty=str(m.get("difficulty_profile") or "K1"),
                        status="READY" if "001" in sc_id else "AVAILABLE",
                        source="h2_runs",
                        demo_enabled="001" in sc_id,
                        scenario_path=str(d),
                    )

    def _load_h3_scenarios(self) -> None:
        # Curated representative H3 scenario
        curated_h3 = UnifiedScenario(
            id="H3-LRN-001",
            display_name="Validated OCS Charging Dependency Promotion",
            stage="H3",
            concept="Learn",
            scenario_type="LEARNING_UNIT",
            domains=["Mobile Core", "OCS"],
            services=["Subscriber Charging"],
            description="Curated learning unit demonstrating SME validation and promotion of discovered charging path.",
            aliases=["TWIN-LRN-001", "validated charging dependency", "h3 learning unit", "H3-LU-001"],
            tags=["learning", "promotion", "curated_learning", "fcaps"],
            difficulty="L3",
            status="READY",
            source="h3_catalog",
            demo_enabled=True,
            scenario_path="simulator/h3_runs/H3-LU-001/",
        )
        self._scenarios["H3-LRN-001"] = curated_h3
        self._scenarios["TWIN-LRN-001"] = curated_h3

        # Index available runs from h3_runs directory
        h3_dir = self.base_dir / "h3_runs"
        if h3_dir.exists():
            for d in sorted(h3_dir.iterdir()):
                if not d.is_dir() or not d.name.startswith("H3-LU-"):
                    continue
                manifest_file = d / "learning_unit_manifest.yaml"
                if not manifest_file.exists():
                    continue
                try:
                    m = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
                except Exception:
                    continue
                lu_id = str(m.get("learning_unit_id") or d.name)
                if lu_id not in self._scenarios:
                    cohort = str(m.get("cohort") or "learning").replace("_", " ").title()
                    self._scenarios[lu_id] = UnifiedScenario(
                        id=lu_id,
                        display_name=f"{cohort} Learning Unit ({lu_id})",
                        stage="H3",
                        concept="Learn",
                        scenario_type="LEARNING_UNIT",
                        domains=["Mobile Core", "OCS"],
                        services=["Subscriber Services"],
                        description=str(m.get("expected_learning_value") or f"Curated learning unit {lu_id}."),
                        difficulty="L3",
                        status="READY" if "001" in lu_id else "AVAILABLE",
                        source="h3_runs",
                        demo_enabled="001" in lu_id,
                        scenario_path=str(d),
                    )

    def _load_h4_scenarios(self) -> None:
        registry_file = self.base_dir / "scenarios" / "h4_registry.yaml"
        if not registry_file.exists():
            return

        try:
            records = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or []
        except Exception:
            return

        domain_map = {
            "transport": "Transport",
            "mobile_core": "Mobile Core",
            "packet_core": "Packet Core",
            "core": "Core",
            "ran": "RAN",
            "database": "Database",
            "dns": "DNS",
            "security": "Security",
            "signaling": "Signaling",
            "facilities": "Facilities",
            "power": "Facilities",
        }

        for item in records:
            sc_id = item.get("id")
            if not sc_id:
                continue

            # SCN-001 is handled as H1 / Understand, so do not override it with H4
            if sc_id == "SCN-001":
                continue

            tags = item.get("tags") or []
            domains = list(dict.fromkeys(domain_map[t] for t in tags if t in domain_map))
            aliases = item.get("aliases") or []

            self._scenarios[sc_id] = UnifiedScenario(
                id=sc_id,
                display_name=item.get("display_name", sc_id),
                stage="H4",
                concept="Anticipate",
                scenario_type="WHAT_IF",
                domains=domains or ["Transport"],
                services=["Transmission"] if "transport" in tags else ["Core Services"],
                description=item.get("description", ""),
                aliases=aliases,
                tags=tags,
                difficulty="ADVANCED",
                status="READY" if item.get("demo_enabled", True) else "AVAILABLE",
                source="h4_registry",
                demo_enabled=item.get("demo_enabled", True),
                scenario_path=item.get("scenario_path", f"simulator/h4_runs/{sc_id}/"),
            )

    def all(self) -> list[UnifiedScenario]:
        self._ensure_loaded()
        seen = set()
        unique = []
        for sc in self._scenarios.values():
            if sc.id not in seen:
                seen.add(sc.id)
                unique.append(sc)
        return unique

    def get(self, scenario_id: str) -> Optional[UnifiedScenario]:
        self._ensure_loaded()
        cleaned = scenario_id.strip().upper()
        if cleaned in self._scenarios:
            return self._scenarios[cleaned]

        # Check aliases
        query_norm = scenario_id.strip().lower()
        for sc in self.all():
            if sc.id.strip().lower() == query_norm or sc.display_name.strip().lower() == query_norm:
                return sc
            for al in sc.aliases:
                if al.strip().lower() == query_norm or al.strip().upper() == cleaned:
                    return sc
        return None

    def filter_by_concept(self, concept: str) -> list[UnifiedScenario]:
        self._ensure_loaded()
        target = concept.strip().upper()
        if target == "ALL":
            return self.all()
        return [sc for sc in self.all() if sc.concept.upper() == target]

    def filter_by_stage(self, stage: str) -> list[UnifiedScenario]:
        self._ensure_loaded()
        target = stage.strip().upper()
        if target == "ALL":
            return self.all()
        return [sc for sc in self.all() if sc.stage.upper() == target]

    def get_yaml(self, scenario_id: str) -> tuple[str, str, bool]:
        """Return (yaml_content, source_filename, is_read_only)."""
        self._ensure_loaded()
        sc = self.get(scenario_id)
        if not sc:
            raise KeyError(f"Scenario '{scenario_id}' not found.")

        # Check if scenario_path exists as a file or folder
        candidate_paths: list[Path] = []
        if sc.scenario_path:
            p = Path(sc.scenario_path)
            if p.is_absolute():
                candidate_paths.append(p)
            else:
                candidate_paths.append(self.base_dir / sc.scenario_path)
                candidate_paths.append(p)

        # Standard scenarios directory candidates
        candidate_paths.append(self.base_dir / "scenarios" / f"{sc.id}.yaml")
        candidate_paths.append(self.base_dir / "scenarios" / f"{sc.id.lower()}.yaml")

        for cp in candidate_paths:
            if cp.is_file() and cp.exists():
                try:
                    return cp.read_text(encoding="utf-8"), cp.name, False
                except Exception:
                    pass
            elif cp.is_dir() and cp.exists():
                for sub in ["scenario_manifest.yaml", "learning_unit_manifest.yaml", "demo_metadata.yaml"]:
                    sub_p = cp / sub
                    if sub_p.exists():
                        try:
                            return sub_p.read_text(encoding="utf-8"), f"{cp.name}/{sub}", False
                        except Exception:
                            pass

        # If no file exists, serialize scenario metadata or synthesized manifest as YAML
        data = sc.metadata or {
            "scenario_id": sc.id,
            "display_name": sc.display_name,
            "stage": sc.stage,
            "concept": sc.concept,
            "scenario_type": sc.scenario_type,
            "domains": sc.domains,
            "services": sc.services,
            "description": sc.description,
            "aliases": sc.aliases,
            "tags": sc.tags,
            "difficulty": sc.difficulty,
            "status": sc.status,
            "demo_enabled": sc.demo_enabled,
        }
        yaml_str = yaml.dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)
        return yaml_str, f"{sc.id}.yaml", False

    def save_yaml(self, scenario_id: str, content: str) -> tuple[bool, str]:
        """Validate and save updated YAML definition for a scenario."""
        self._ensure_loaded()
        sc = self.get(scenario_id)
        if not sc:
            return False, f"Scenario '{scenario_id}' not found."

        try:
            parsed = yaml.safe_load(content)
            if not isinstance(parsed, dict):
                return False, "Invalid YAML: Root must be a key-value mapping (dictionary)."
        except yaml.YAMLError as err:
            return False, f"YAML Syntax Error: {err}"

        # Find target write path
        write_path: Optional[Path] = None
        if sc.scenario_path:
            p = Path(sc.scenario_path)
            cand = p if p.is_absolute() else self.base_dir / sc.scenario_path
            if cand.is_file() and cand.exists():
                write_path = cand
            elif cand.is_dir() and cand.exists():
                for sub in ["scenario_manifest.yaml", "learning_unit_manifest.yaml", "demo_metadata.yaml"]:
                    sub_p = cand / sub
                    if sub_p.exists():
                        write_path = sub_p
                        break

        if not write_path:
            scenarios_dir = self.base_dir / "scenarios"
            scenarios_dir.mkdir(parents=True, exist_ok=True)
            write_path = scenarios_dir / f"{sc.id}.yaml"

        try:
            write_path.write_text(content, encoding="utf-8")
        except Exception as e:
            return False, f"Failed to write file '{write_path.name}': {e}"

        # Update in-memory scenario record from parsed YAML
        if "display_name" in parsed or "scenario_name" in parsed:
            sc.display_name = str(parsed.get("display_name") or parsed.get("scenario_name"))
        if "description" in parsed:
            sc.description = str(parsed["description"])
        if "domains" in parsed and isinstance(parsed["domains"], list):
            sc.domains = [str(d).replace("_", " ").title() for d in parsed["domains"]]
        if "affected_services" in parsed and isinstance(parsed["affected_services"], list):
            sc.services = [str(s).replace("_", " ").title() for s in parsed["affected_services"]]
        elif "services" in parsed and isinstance(parsed["services"], list):
            sc.services = [str(s).replace("_", " ").title() for s in parsed["services"]]
        if "stage" in parsed:
            sc.stage = str(parsed["stage"]).upper()
            sc.concept = concept_for_stage(sc.stage)
        sc.metadata = parsed
        sc.scenario_path = str(write_path)

        return True, f"Successfully saved to {write_path.name}."


# Global singleton catalog instance
scenario_catalog = ScenarioCatalog()
