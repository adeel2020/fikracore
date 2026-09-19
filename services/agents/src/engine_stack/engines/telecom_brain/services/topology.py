"""Logical topology service for dependency paths and blast radius."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..engine_context import TelecomContext
from ..models import FCAPSClassification, ServiceProcedure, TelecomRequest, TelecomResult, TelecomTrace, TopologyNode

_REFERENCE_YAML = Path(__file__).resolve().parent.parent / "simulator" / "operator_model" / "reference_synthetic_network.yaml"


class TopologyService:
    id = "topology"

    def __init__(self, topology_path: Path | None = None, reference_yaml: Path | None = None) -> None:
        self.topology_path = topology_path or self._default_topology_path()
        self.reference_yaml = reference_yaml or _REFERENCE_YAML

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("topology", "dependency", "blast radius", "affected components", "path")):
            score += 0.55
        if any(term in query for term in ("service procedure", "lte attach", "registration", "sgi", "ims")):
            score += 0.2
        if request.topology_refs or request.service_procedure_refs:
            score += 0.25
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        topology = self._load_topology()
        service_id = self._resolve_service(request, topology)
        path = topology.get("services", {}).get(service_id, []) if service_id else []
        nodes = [
            TopologyNode(id=node, name=node.split(".")[-1], domain=node.split(".")[0] if "." in node else None)
            for node in path
        ]
        text = self._format(service_id, path)
        projection = {
            "kind": "topology_projection",
            "service_id": service_id,
            "dependency_path": path,
            "summary": "Semantic projection only; authoritative topology remains external.",
        }
        try:
            await context.mcp_hub.call_tool("gbrain", "put_observation", projection)
        except Exception:
            projection["projection_status"] = "skipped_or_unavailable"
        return TelecomResult(
            text=text,
            spoken_response=f"Resolved topology for {service_id or 'the requested service'} with {len(path)} dependency nodes.",
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["logical_topology_fixture", "mcp_hub.gbrain"]),
            fcaps=[FCAPSClassification.FAULT, FCAPSClassification.PERFORMANCE],
            data={"service_id": service_id, "dependency_path": path, "topology_projection": projection, "nodes": [n.model_dump() for n in nodes]},
        )

    @staticmethod
    def _resolve_service(request: TelecomRequest, topology: dict) -> str | None:
        if request.context.get("service_id"):
            return str(request.context["service_id"])
        for proc in request.service_procedure_refs:
            if proc.id in topology.get("services", {}):
                return proc.id
        query = request.query.lower()
        for intent, service_id in topology.get("intents", {}).items():
            if intent.replace("_", " ") in query or service_id.replace("-", " ") in query:
                return service_id
        for service_id in topology.get("services", {}):
            if service_id.replace("-", " ") in query:
                return service_id
        if any(w in query for w in ("blast radius", "topology", "impact", "incident")):
            return "lte-attach"
        return None

    def _load_topology(self) -> dict:
        if self.reference_yaml.exists():
            return self._load_from_yaml(self.reference_yaml)
        if self.topology_path.exists():
            return json.loads(self.topology_path.read_text(encoding="utf-8"))
        return {"services": {}, "intents": {}}

    @staticmethod
    def _load_from_yaml(yaml_path: Path) -> dict:
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        entities = {e.get("entity_id"): e for e in data.get("entities", [])}
        rels = data.get("relationships", [])

        adj: dict[str, list[str]] = {}
        for r in rels:
            src = r.get("source_entity", "")
            tgt = r.get("target_entity", "")
            adj.setdefault(src, []).append(tgt)

        services: dict[str, list[str]] = {}
        intents: dict[str, str] = {}

        for chain in data.get("service_chains", []):
            chain_id = chain.get("chain_id", "")
            hops = chain.get("hops", [])
            if chain_id and hops:
                services[chain_id] = hops
                intents[chain_id.replace("_", " ")] = chain_id

        for domain, info in data.get("domains", {}).items():
            domain_entities = [e.get("entity_id") for e in data.get("entities", []) if e.get("domain") == domain]
            if domain_entities:
                services[f"domain-{domain.lower()}"] = domain_entities

        return {"services": services, "intents": intents, "entities": entities, "adjacency": adj}

    @staticmethod
    def _format(service_id: str | None, path: list[str]) -> str:
        lines = ["**Topology Impact**"]
        if not service_id:
            lines.append("- No service procedure was resolved.")
        elif path:
            lines.append(f"- Service procedure: {service_id}")
            lines.append(f"- Dependency path: {' -> '.join(path)}")
            lines.append(f"- Blast radius candidates: {', '.join(path)}")
        else:
            lines.append(f"- No dependency path found for {service_id}; retain for topology review.")
        return "\n".join(lines)

    @staticmethod
    def _default_topology_path() -> Path:
        cur = Path(__file__).resolve()
        for parent in cur.parents:
            candidate = parent / "correlation" / "fixtures" / "grafana-lgtm" / "logical_topology.json"
            if candidate.exists():
                return candidate
        return Path("services/agents/src/correlation/fixtures/grafana-lgtm/logical_topology.json")
