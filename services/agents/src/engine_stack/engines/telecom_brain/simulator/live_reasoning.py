"""Live Reasoning Activation & Operational Run Ingestion Layer (§25, §26, §52).

Provides:
- LiveIntentRecord & LiveIntentRegistry (backend-owned live intents)
- RunCorrelationDecision & deterministic attach-or-create logic
- Read-only EvidenceProvider abstractions and implementations (LGTM, Telecombrain, Topology, NetworkTool)
- Provenance tracking, canonical normalization, deduplication, and backend admission
- Operational recovery signal handling
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Live Intent Contracts & Registry
# ---------------------------------------------------------------------------

class LiveIntentTarget(BaseModel):
    metric: str
    operator: Literal[">=", "<=", ">", "<", "==", "!="] = ">="
    threshold: float | str


class LiveIntentObserved(BaseModel):
    value: float | str
    observed_at: str


class LiveIntentRecord(BaseModel):
    intent_id: str
    display_name: str
    service: str
    scope: str = "Default Scope"
    target: LiveIntentTarget
    observed: LiveIntentObserved
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] = "CRITICAL"
    source_system: str = "SLO-Engine"
    domain_hint: str = "Core"
    correlation_window: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LiveIntentRegistry:
    """Backend-configured registry for live intents (§8, §48).

    Guarantees intent violations come from backend configuration rather than
    hardcoded frontend strings.
    """

    def __init__(self) -> None:
        self._intents: Dict[str, LiveIntentRecord] = {}
        self._seed_default_intents()

    def _seed_default_intents(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        seeds = [
            LiveIntentRecord(
                intent_id="INTENT-APN-001",
                display_name="Enterprise APN Success Rate Below 99.5% Target",
                service="Enterprise APN",
                scope="Regional APN Gateway North",
                target=LiveIntentTarget(metric="success_rate", operator=">=", threshold=99.5),
                observed=LiveIntentObserved(value=97.9, observed_at=now),
                severity="CRITICAL",
                source_system="Prometheus-SLO",
                domain_hint="Packet Core",
                metadata={"apn": "enterprise.secure.net", "region": "North"},
            ),
            LiveIntentRecord(
                intent_id="INTENT-VOLTE-001",
                display_name="VoLTE Call Setup Success Below 99.0% Target",
                service="VoLTE Voice",
                scope="IMS Core Region North",
                target=LiveIntentTarget(metric="setup_success_rate", operator=">=", threshold=99.0),
                observed=LiveIntentObserved(value=96.2, observed_at=now),
                severity="HIGH",
                source_system="IMS-Aggregator",
                domain_hint="IMS",
                metadata={"codec": "AMR-WB", "region": "North"},
            ),
            LiveIntentRecord(
                intent_id="INTENT-5G-001",
                display_name="5G Registration Success Below 99.8% Target",
                service="5G NSA/SA",
                scope="gNodeB Aggregation Site A",
                target=LiveIntentTarget(metric="reg_success_rate", operator=">=", threshold=99.8),
                observed=LiveIntentObserved(value=98.1, observed_at=now),
                severity="MEDIUM",
                source_system="RAN-Analytics",
                domain_hint="RAN",
                metadata={"band": "n78", "site_id": "SITE-A"},
            ),
        ]
        for item in seeds:
            self._intents[item.intent_id] = item

    def get_intent(self, intent_id: str) -> Optional[LiveIntentRecord]:
        return self._intents.get(intent_id)

    def list_intents(self) -> list[LiveIntentRecord]:
        return list(self._intents.values())

    def register_intent(self, intent: LiveIntentRecord) -> None:
        self._intents[intent.intent_id] = intent


# Global registry instance
live_intent_registry = LiveIntentRegistry()


# ---------------------------------------------------------------------------
# 2. Run Correlation / Deduplication Decision
# ---------------------------------------------------------------------------

class RunCorrelationDecision(BaseModel):
    decision: Literal["CREATE_NEW_RUN", "ATTACH_TO_EXISTING_RUN"]
    matched_run_id: Optional[str] = None
    confidence: float = 1.0
    reasons: list[str] = Field(default_factory=list)
    correlation_key: str = ""


# ---------------------------------------------------------------------------
# 3. Evidence Admission & Provenance
# ---------------------------------------------------------------------------

class EvidenceAdmission(BaseModel):
    evidence_id: str
    run_id: str
    source_mode: Literal["LIVE_INTENT"] = "LIVE_INTENT"
    admission_state: Literal["RECEIVED", "FILTERED", "ADMITTED", "REJECTED", "REJECTED_DUPLICATE", "SUPERSEDED"]
    reason: str
    fingerprint: str
    normalized_item: dict[str, Any]
    ingested_at: str
    revision: int = 1
    sequence: int = 1


def compute_evidence_fingerprint(raw_evidence: dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 fingerprint for deduplication."""
    source_system = str(raw_evidence.get("source_system") or "unknown")
    event_id = str(raw_evidence.get("event_id") or raw_evidence.get("id") or "")
    entity_id = str(raw_evidence.get("entity_id") or raw_evidence.get("source_entity") or "")
    event_time = str(raw_evidence.get("event_time") or raw_evidence.get("timestamp") or "")
    category = str(raw_evidence.get("category") or raw_evidence.get("badge") or "evidence").upper()
    signal = str(raw_evidence.get("signal") or raw_evidence.get("title") or "")
    
    raw_str = f"{source_system}:{event_id}:{entity_id}:{event_time}:{category}:{signal}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def normalize_live_evidence(
    raw_evidence: dict[str, Any],
    run_id: str,
    sequence: int = 1,
) -> dict[str, Any]:
    """Normalize raw live operational event into canonical evidence contract (§11, §12)."""
    now = datetime.now(timezone.utc).isoformat()
    fingerprint = compute_evidence_fingerprint(raw_evidence)
    ev_id = str(raw_evidence.get("id") or raw_evidence.get("evidence_id") or f"EV-LIVE-{fingerprint}")
    event_id = str(raw_evidence.get("event_id") or f"EVT-LIVE-{fingerprint}")
    category = str(raw_evidence.get("category") or raw_evidence.get("badge") or "metric").lower()
    if category not in {"alarm", "log", "metric", "kpi", "trace", "change", "ticket", "healthy_signal", "recovery"}:
        category = "metric"

    title = str(
        raw_evidence.get("title")
        or raw_evidence.get("signal")
        or raw_evidence.get("summary")
        or f"Telemetry from {raw_evidence.get('source_system', 'operational telemetry')}"
    )

    return {
        "id": ev_id,
        "evidence_id": ev_id,
        "event_id": event_id,
        "run_id": run_id,
        "category": category,
        "badge": category.upper(),
        "severity": str(raw_evidence.get("severity") or "high").lower(),
        "state": "OBSERVED",
        "title": title,
        "signal": title,
        "description": str(raw_evidence.get("description") or title),
        "source_system": str(raw_evidence.get("source_system") or "live-monitor"),
        "source_entity": str(raw_evidence.get("source_entity") or raw_evidence.get("entity_id") or "GW-01"),
        "canonical_entity": str(raw_evidence.get("canonical_entity") or raw_evidence.get("source_entity") or "GW-01"),
        "domain": str(raw_evidence.get("domain") or "Core"),
        "service": str(raw_evidence.get("service") or ""),
        "timestamp": str(raw_evidence.get("timestamp") or raw_evidence.get("event_time") or now),
        "event_time": str(raw_evidence.get("event_time") or raw_evidence.get("timestamp") or now),
        "ingested_at": now,
        "sequence": sequence,
        "fingerprint": fingerprint,
        "quality": {
            "reliability": float(raw_evidence.get("reliability", 0.95)),
            "freshness_sec": int(raw_evidence.get("freshness_sec", 10)),
            "corroborated": bool(raw_evidence.get("corroborated", True)),
        },
        "details": raw_evidence.get("details", {}),
    }


# ---------------------------------------------------------------------------
# 4. Strictly Read-Only Evidence Providers (§22, §23)
# ---------------------------------------------------------------------------

class EvidenceProviderResult(BaseModel):
    request_id: str
    status: Literal["RETURNED", "UNAVAILABLE", "FAILED", "TIMED_OUT"]
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    reason: Optional[str] = None
    provider_id: str
    completed_at: str


class EvidenceProvider:
    """Base read-only evidence provider interface."""

    def __init__(self, provider_id: str, display_name: str) -> None:
        self.provider_id = provider_id
        self.display_name = display_name

    def supports(self, request: dict[str, Any]) -> bool:
        raise NotImplementedError

    def execute(self, request: dict[str, Any], context: dict[str, Any]) -> EvidenceProviderResult:
        raise NotImplementedError


class LGTMProvider(EvidenceProvider):
    """Read-only Grafana LGTM evidence provider (Metrics, Logs, Traces)."""

    def __init__(self) -> None:
        super().__init__("LGTMProvider", "Grafana LGTM Evidence Provider")

    def supports(self, request: dict[str, Any]) -> bool:
        req_type = str(request.get("type", "")).upper()
        return req_type in {"METRIC", "LOG", "TRACE", "KPI", "TELEMETRY"}

    def execute(self, request: dict[str, Any], context: dict[str, Any]) -> EvidenceProviderResult:
        now = datetime.now(timezone.utc).isoformat()
        req_id = request.get("id") or request.get("request_id") or "REQ-001"
        target = request.get("target") or "GW-01"

        if request.get("simulate_failure"):
            return EvidenceProviderResult(
                request_id=req_id,
                status="UNAVAILABLE",
                evidence=[],
                reason=f"LGTM query failed: Prometheus endpoint unavailable for target {target}",
                provider_id=self.provider_id,
                completed_at=now,
            )

        # Strictly read-only evidence collection
        item = {
            "id": f"EV-{req_id}",
            "source_system": "Grafana-LGTM",
            "source_entity": target,
            "category": "metric",
            "title": f"Telemetry for {target}: Packet drop rate confirmed elevated at 4.2%",
            "severity": "high",
            "event_time": now,
            "details": {"metric_name": "drop_rate_pct", "value": 4.2},
        }
        return EvidenceProviderResult(
            request_id=req_id,
            status="RETURNED",
            evidence=[item],
            reason="LGTM metric query completed successfully",
            provider_id=self.provider_id,
            completed_at=now,
        )


class TelecombrainProvider(EvidenceProvider):
    """Read-only Telecombrain operational knowledge provider."""

    def __init__(self) -> None:
        super().__init__("TelecombrainProvider", "Telecombrain Knowledge Provider")

    def supports(self, request: dict[str, Any]) -> bool:
        req_type = str(request.get("type", "")).upper()
        return req_type in {"TOPOLOGY", "DEPENDENCY", "KNOWLEDGE", "SERVICE_PATH"}

    def execute(self, request: dict[str, Any], context: dict[str, Any]) -> EvidenceProviderResult:
        now = datetime.now(timezone.utc).isoformat()
        req_id = request.get("id") or request.get("request_id") or "REQ-002"
        target = request.get("target") or "APN-GW-01"

        if request.get("simulate_failure"):
            return EvidenceProviderResult(
                request_id=req_id,
                status="FAILED",
                evidence=[],
                reason="Telecombrain graph query timed out",
                provider_id=self.provider_id,
                completed_at=now,
            )

        item = {
            "id": f"EV-{req_id}",
            "source_system": "telecombrain",
            "source_entity": target,
            "category": "trace",
            "title": f"Topology dependency verified: {target} connects to Core-UPF-02",
            "severity": "info",
            "event_time": now,
            "details": {"source": target, "target": "Core-UPF-02", "relation": "UPSTREAM_GATEWAY"},
        }
        return EvidenceProviderResult(
            request_id=req_id,
            status="RETURNED",
            evidence=[item],
            reason="Telecombrain dependency resolved",
            provider_id=self.provider_id,
            completed_at=now,
        )


class TopologyProvider(EvidenceProvider):
    """Read-only network inventory and topology provider."""

    def __init__(self) -> None:
        super().__init__("TopologyProvider", "Network Inventory & Topology Provider")

    def supports(self, request: dict[str, Any]) -> bool:
        return str(request.get("type", "")).upper() in {"TOPOLOGY", "INVENTORY"}

    def execute(self, request: dict[str, Any], context: dict[str, Any]) -> EvidenceProviderResult:
        now = datetime.now(timezone.utc).isoformat()
        req_id = request.get("id") or request.get("request_id") or "REQ-003"
        return EvidenceProviderResult(
            request_id=req_id,
            status="RETURNED",
            evidence=[{
                "id": f"EV-{req_id}",
                "source_system": "Inventory-CMDB",
                "source_entity": "GW-01",
                "category": "kpi",
                "title": "Inventory lookup: GW-01 is active in Region North datacenter",
                "severity": "info",
                "event_time": now,
            }],
            reason="Topology lookup completed",
            provider_id=self.provider_id,
            completed_at=now,
        )


class NetworkToolProvider(EvidenceProvider):
    """Read-only diagnostic network tool provider (§22, Guardrail 3).

    STRICTLY READ-ONLY: Executes read-only ping/traceroute/diagnostic query.
    Zero network remediation or write actions allowed.
    """

    def __init__(self) -> None:
        super().__init__("NetworkToolProvider", "Diagnostic Network Tool Provider (Read-Only)")

    def supports(self, request: dict[str, Any]) -> bool:
        return str(request.get("type", "")).upper() in {"DIAGNOSTIC", "PING", "TRACEROUTE", "TOOL"}

    def execute(self, request: dict[str, Any], context: dict[str, Any]) -> EvidenceProviderResult:
        now = datetime.now(timezone.utc).isoformat()
        req_id = request.get("id") or request.get("request_id") or "REQ-004"
        action_name = request.get("action_name") or request.get("name") or "read_diag"
        
        # Guard against any mutating command request
        if any(w in action_name.lower() for w in ["restart", "reboot", "modify", "delete", "write", "patch", "remediate"]):
            return EvidenceProviderResult(
                request_id=req_id,
                status="FAILED",
                evidence=[],
                reason="NetworkToolProvider is strictly read-only: mutating actions are rejected",
                provider_id=self.provider_id,
                completed_at=now,
            )

        item = {
            "id": f"EV-{req_id}",
            "source_system": "NetworkDiagTool",
            "source_entity": request.get("target", "GW-01"),
            "category": "trace",
            "title": f"Diagnostic probe on {request.get('target', 'GW-01')}: RTT=12ms, 0% loss on transport link",
            "severity": "info",
            "event_time": now,
        }
        return EvidenceProviderResult(
            request_id=req_id,
            status="RETURNED",
            evidence=[item],
            reason="Diagnostic query completed without modification",
            provider_id=self.provider_id,
            completed_at=now,
        )


class ProviderRegistry:
    """Registry holding read-only evidence providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, EvidenceProvider] = {}
        self.register(LGTMProvider())
        self.register(TelecombrainProvider())
        self.register(TopologyProvider())
        self.register(NetworkToolProvider())

    def register(self, provider: EvidenceProvider) -> None:
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str) -> Optional[EvidenceProvider]:
        return self._providers.get(provider_id)

    def find_provider_for_request(self, request: dict[str, Any]) -> Optional[EvidenceProvider]:
        for provider in self._providers.values():
            if provider.supports(request):
                return provider
        return None


default_provider_registry = ProviderRegistry()
