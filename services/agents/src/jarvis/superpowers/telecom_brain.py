"""Compatibility bridge from MARK/Jarvis to the canonical TelecomBrainEngine."""

from __future__ import annotations

import logging
import json
import re
from pathlib import Path
from typing import Any, AsyncIterator

from engine_stack.engines.telecom_brain import TelecomBrainEngine as CanonicalTelecomBrainEngine
from assistant.mark.response import MarkResponse

logger = logging.getLogger("jarvis.telecom_brain")


_DOCS = (
    "docs/telecom-brain-cognitive-operations-architecture.md",
    "docs/telecom-brain-questionnaire.md",
    "docs/storyteller-command-reference.md",
    "docs/grafana-lgtm-integration-plan.md",
    "docs/inter-intra-domain-alarm-correlation-hld.md",
    "docs/inter-intra-domain-alarm-correlation-lld.md",
    "docs/storyteller-baseline-structure.md",
)

TELECOM_KEYWORDS = {
    "telecom", "network", "incident", "incidents", "rca", "root cause", "mttr",
    "alarm", "alarms", "kpi", "kpis", "attach", "s1-mme", "sgi", "upf", "amf",
    "smf", "gnb", "gnodeb", "enb", "enodeb", "mme", "hss", "pcf", "udm", "ausf",
    "5g", "4g", "lte", "3gpp", "core", "ims", "transport", "slice", "topology",
    "mop", "mops", "remediation", "healing", "fcaps", "storyteller", "gbrain",
    "cluster", "registry", "status", "health", "node", "nodes", "pod",
    "latency", "packet", "throughput", "cpu", "memory", "diameter", "nas", "ran",
    "architecture", "questionnaire", "playbook", "runbook", "outage", "degradation",
    "intent", "intents", "sla", "slas", "objective", "objectives", "procedure",
    "procedures", "service", "services", "cssr", "pdu", "pdp", "qos", "subscriber", "ue",
    "inventory", "inventories", "cmdb", "nautobot",
    "rtr", "msisdn", "ticket", "tickets", "prov", "provisioning", "volte", "mnp", "apn",
    "mml", "pos", "esim", "vms", "mcn", "disposition", "reassigned", "rejected", "resolved",
}


def normalize_query(raw_query: str) -> str:
    """Normalize common speech-to-text phonetic mis-transcriptions for telecom queries."""
    q = raw_query
    mappings: list[tuple[str, str]] = [
        (r"\bdysfunctions\b", "network functions"),
        (r"\bdysfunction\b", "network function"),
        (r"\bdisfunctions\b", "network functions"),
        (r"\bdisfunction\b", "network function"),
        (r"\bthese functions\b", "network functions"),
        (r"\bthis functions\b", "network function"),
        (r"\bnetworking\s+inventory\b", "network inventory"),
        (r"\bnetworking\s+event\s+(three|tree|free)\b", "network inventory"),
        (r"\bnetwork\s+event\s+(three|tree|free)\b", "network inventory"),
        (r"\bnetworking\s+in\s+the\s+tree\b", "network inventory"),
        (r"\ba\s+m\s+f\b", "AMF"),
        (r"\bu\s+p\s+f\b", "UPF"),
        (r"\bs\s+m\s+f\b", "SMF"),
        (r"\bg\s+node\s*b\b", "gNodeB"),
        (r"\bg\s+note\s*b\b", "gNodeB"),
        (r"\be\s+node\s*b\b", "eNodeB"),
        (r"\bm\s+m\s+e\b", "MME"),
        (r"\bh\s+s\s+s\b", "HSS"),
        (r"\bp\s+c\s+f\b", "PCF"),
        (r"\br\s+c\s+a\b", "RCA"),
        (r"\bm\s+t\s+t\s+r\b", "MTTR"),
        (r"\bf\s+c\s+a\s+p\s+s\b", "FCAPS"),
        (r"\b5\s+g\s+c\b", "5GC"),
        (r"\b5\s+g\s+core\b", "5G Core"),
    ]
    for pattern, repl in mappings:
        q = re.sub(pattern, repl, q, flags=re.IGNORECASE)
    return q


class TelecomBrainEngine:
    """Legacy MARK superpower facade backed by the canonical engine stack."""

    def __init__(self, config: Any = None, *, repo_root: Path | None = None) -> None:
        self.config = config
        self.repo_root = repo_root or self._discover_repo_root()
        self._engine = CanonicalTelecomBrainEngine()
        self.last_reply: str | None = None
        self.last_spoken_reply: str | None = None

    async def initialize(self) -> None:
        await self._engine.initialize()
        logger.info("[TelecomBrainEngine] Bridge initialized against canonical engine stack.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        norm_q = normalize_query(query)
        result = await self._engine.process(norm_q, session_id=session_id, context=context)
        self.last_reply = result.text
        self.last_spoken_reply = result.spoken_response
        if result.trace.selected_service:
            return MarkResponse(result.text, spoken_reply=result.spoken_response, presentation={
                key: result.data[key] for key in ("narrative", "visual_explanation", "telemetry_evidence", "mobile_rtr")
                if key in result.data
            })

        domain_summary = self._answer_domain_summary(norm_q)
        if domain_summary:
            self.last_reply = domain_summary["text"]
            self.last_spoken_reply = domain_summary["spoken"]
            return MarkResponse(self.last_reply, spoken_reply=self.last_spoken_reply)

        docs_context = self._answer_from_docs(norm_q)
        if docs_context:
            self.last_reply = self._format_deterministic_narrative(norm_q, docs_context, "")
            self.last_spoken_reply = "I found relevant architecture context and placed the details in chat. I did not find an approved operational runbook for this request."
            return MarkResponse(self.last_reply, spoken_reply=self.last_spoken_reply)

        has_incident_ctx = bool(context and (context.get("incident_id") or context.get("path_incident_id")))
        if not self._has_domain_term(norm_q) and not has_incident_ctx:
            self.last_reply = (
                "That query is outside my operational scope. "
                "I only manage telecom incidents, 5G Core topology, and network telemetry for our operational sites."
            )
            self.last_spoken_reply = None
            return self.last_reply
        return result.text

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        yield await self.process(query, session_id=session_id, context=context)

    async def shutdown(self) -> None:
        if hasattr(self._engine, "shutdown"):
            await self._engine.shutdown()

    def _answer_from_docs(self, query: str) -> str:
        if re.search(r"\b(playbooks?|runbooks?|commands?)\b", query, flags=re.IGNORECASE):
            return ""
        if self._is_inventory_query(query) or self._is_core_domain_query(query):
            return ""
        if not re.search(
            r"\b(architecture|architectural|design|document|docs|documentation|implementation|"
            r"questionnaire|reference|schema|hld|lld|learning\s+lens|how\s+.*built)\b",
            query,
            flags=re.IGNORECASE,
        ):
            return ""
        sections = self._rank_doc_sections(query)
        if not sections:
            return ""

        lines = ["**Technical Architecture Context**"]
        for source, heading, body, _score in sections[:4]:
            snippet = self._compress(body)
            if snippet:
                lines.append(f"- From `{source}` / {heading or source}: {snippet}")
        return "\n".join(lines)

    def _rank_doc_sections(self, query: str) -> list[tuple[str, str, str, int]]:
        terms = self._terms(query)
        if not terms:
            return []

        ranked: list[tuple[str, str, str, int]] = []
        for rel_path in _DOCS:
            path = self.repo_root / rel_path
            if not path.exists():
                continue
            for heading, body in self._sections(path.read_text(encoding="utf-8")):
                haystack = f"{heading}\n{body}".lower()
                score = sum(3 if term in heading.lower() else 1 for term in terms if term in haystack)
                if score:
                    ranked.append((rel_path, heading, body, score))
        ranked.sort(key=lambda item: item[3], reverse=True)
        return ranked

    def _answer_domain_summary(self, query: str) -> dict[str, str] | None:
        if self._is_inventory_query(query):
            return self._network_inventory_summary()
        if self._is_core_domain_query(query):
            return self._core_domain_summary()
        return None

    def _network_inventory_summary(self) -> dict[str, str]:
        topology = self._load_logical_topology()
        services = topology.get("services", {}) if isinstance(topology, dict) else {}
        intents = topology.get("intents", {}) if isinstance(topology, dict) else {}
        nodes = sorted({node for path in services.values() if isinstance(path, list) for node in path})
        domains = sorted({node.split(".")[0] for node in nodes if "." in node})

        service_text = ", ".join(sorted(services)) or "none discovered"
        intent_text = ", ".join(f"{intent} -> {service}" for intent, service in sorted(intents.items())) or "none discovered"
        domain_text = ", ".join(domains) or "none discovered"
        node_text = ", ".join(nodes[:12]) + ("..." if len(nodes) > 12 else "") if nodes else "none discovered"

        text = "\n".join([
            "**Network Inventory Summary**",
            "- Scope available: domain-level logical inventory and service dependency paths.",
            f"- Logical domains: {domain_text}.",
            f"- Service procedures: {service_text}.",
            f"- Intent mappings: {intent_text}.",
            f"- Inventory nodes: {node_text}.",
            "- Source checked: local Telecom Brain topology projection used for gbrain-backed operational context.",
            "- Not available: no live CMDB/Nautobot physical inventory snapshot is populated in this repo yet.",
        ])
        spoken = (
            "I found domain-level network inventory for the mobile core topology and service procedures. "
            "A live physical inventory source such as Nautobot or CMDB is not populated yet."
        )
        return {"text": text, "spoken": spoken}

    def _core_domain_summary(self) -> dict[str, str]:
        topology = self._load_logical_topology()
        services = topology.get("services", {}) if isinstance(topology, dict) else {}
        core_nodes = sorted({
            node
            for path in services.values()
            if isinstance(path, list)
            for node in path
            if "mobile-core" in node
        })
        node_text = ", ".join(core_nodes) if core_nodes else "AMF, SMF, UPF, UDM, AUSF, PCF are recognized as 5G Core functions, but live instances are not populated."
        service_text = ", ".join(sorted(services)) or "no service procedures discovered"
        text = "\n".join([
            "**5G Core Domain Summary**",
            "- Mark treats 5G Core as part of the Telecom Brain domain layer, not as a separate top-level brain.",
            f"- Available service procedures and dependency context: {service_text}.",
            f"- Available core/topology entities: {node_text}.",
            "- Curated interpretation: use gbrain/domain context first, then telemetry evidence, then incident/story services.",
            "- Not available: no live 5G Core inventory export or authoritative CMDB connector data is populated yet.",
        ])
        spoken = (
            "I can summarize the 5G Core from the domain model and topology context. "
            "I do not see a live authoritative inventory export yet, so I will call out that gap instead of inventing details."
        )
        return {"text": text, "spoken": spoken}

    def _load_logical_topology(self) -> dict[str, Any]:
        path = self.repo_root / "services/agents/src/correlation/fixtures/grafana-lgtm/logical_topology.json"
        if not path.exists():
            return {"services": {}, "intents": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"services": {}, "intents": {}}
        except Exception:
            return {"services": {}, "intents": {}}

    @staticmethod
    def _is_inventory_query(query: str) -> bool:
        return bool(re.search(r"\b(network\s+)?inventor(?:y|ies)\b|\bcmdb\b|\bnautobot\b", query, flags=re.IGNORECASE))

    @staticmethod
    def _is_core_domain_query(query: str) -> bool:
        return bool(re.search(r"\b(5g\s+core|5gc|mobile\s+core)\b", query, flags=re.IGNORECASE))

    @staticmethod
    def _format_deterministic_narrative(query: str, docs_context: str, gbrain_context: str) -> str:
        lines = ["**MARK Incident Operations Analysis**\n"]
        if gbrain_context:
            lines.append(f"**Local Network Telemetry (gbrain):**\n{gbrain_context}\n")
        if docs_context:
            lines.append(f"{docs_context}\n")
        return "\n".join(lines).strip()

    @staticmethod
    def _sections(text: str) -> list[tuple[str, str]]:
        sections: list[tuple[str, str]] = []
        heading = "Overview"
        lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("#"):
                if lines:
                    sections.append((heading, "\n".join(lines).strip()))
                heading = line.lstrip("#").strip()
                lines = []
            else:
                lines.append(line)
        if lines:
            sections.append((heading, "\n".join(lines).strip()))
        return sections

    @staticmethod
    def _terms(query: str) -> list[str]:
        words = re.findall(r"[a-z0-9][a-z0-9_-]{2,}", query.lower())
        stop = {
            "what", "where", "when", "which", "about", "related", "solution",
            "question", "questions", "answer", "answers", "explain", "tell",
            "show", "does", "should", "would", "could", "how", "give", "list",
        }
        return [word for word in words if word not in stop]

    @staticmethod
    def _compress(text: str, *, limit: int = 520) -> str:
        normalized = " ".join(line.strip() for line in text.splitlines() if line.strip())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

    @staticmethod
    def _has_domain_term(query: str) -> bool:
        lower = query.lower()
        words = set(re.findall(r"[a-z0-9_-]{2,}", lower))
        return bool(words & TELECOM_KEYWORDS) or any(term in lower for term in TELECOM_KEYWORDS if " " in term)

    @staticmethod
    def _discover_repo_root() -> Path:
        cur = Path(__file__).resolve()
        for parent in cur.parents:
            if (parent / "docs").exists() and (parent / "services").exists():
                return parent
        return Path.cwd()
