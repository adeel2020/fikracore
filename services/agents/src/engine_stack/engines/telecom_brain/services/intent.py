"""Intent relevance scoring service that never drops unmatched alarms."""

from __future__ import annotations

from ..engine_context import TelecomContext
from ..models import AlarmEvidence, FCAPSClassification, IntentViolation, ServiceProcedure, TelecomRequest, TelecomResult, TelecomTrace


class IntentService:
    id = "intent"

    DEFAULT_INTENTS: dict[str, tuple[str, ...]] = {
        "lte_attach_sr": ("lte attach", "attach", "mme", "hss", "s1-mme"),
        "ue_registration": ("ue registration", "registration", "amf", "ausf", "udm"),
        "volte_cssr": ("volte", "cssr", "ims", "pcscf", "scscf"),
        "sgi_throughput": ("sgi", "throughput", "pgw", "upf"),
        "ims_registration": ("ims registration", "ims", "sip"),
        "data_session_establishment": ("data session", "pdp", "pdu session", "smf", "upf"),
    }

    async def can_handle(self, request: TelecomRequest) -> float:
        query = request.query.lower()
        score = 0.0
        if any(term in query for term in ("intent", "intents", "objective", "objectives", "sla", "slas", "service procedure", "relevance")):
            score += 0.6
        if any(term in query for term in ("list", "what", "which", "show", "describe", "catalog", "all")) and ("intent" in query or "sla" in query):
            score += 0.3
        if request.alarms or request.kpis:
            score += 0.2
        if any(kpi.breached for kpi in request.kpis):
            score += 0.2
        return min(score, 1.0)

    async def handle(self, request: TelecomRequest, context: TelecomContext) -> TelecomResult:
        query = request.query.lower()
        is_catalog_query = any(w in query for w in ("list", "what", "which", "show", "describe", "explain", "catalog", "all")) and ("intent" in query or "objective" in query or "sla" in query)

        observations = [self._score_alarm(alarm, request) for alarm in request.alarms]
        violations = self._violations(request, observations)
        retained = [
            alarm.model_copy(update={"retained_reason": alarm.retained_reason or self._retention_reason(obs)})
            for alarm, obs in zip(request.alarms, observations)
        ]

        if is_catalog_query or (not observations and ("intent" in query or not request.alarms)):
            text = self._format_catalog()
            spoken = "I track 6 operational service intents: UE Registration, PDU Session Establishment, SGi Throughput, LTE Attach, VoLTE Call Setup, and IMS Registration."
        else:
            text = self._format(observations, violations)
            spoken = f"Intent scoring found {len(violations)} possible violations and retained {len(retained)} alarm observations."

        return TelecomResult(
            text=text,
            spoken_response=spoken,
            service_id=self.id,
            trace=TelecomTrace(selected_service=self.id, provenance=["capability_registry.intent"], warnings=[
                "Intent is relevance scoring only; unmatched alarms are retained."
            ]),
            alarm_evidence=retained,
            intent_violations=violations,
            fcaps=[FCAPSClassification.PERFORMANCE, FCAPSClassification.FAULT],
            data={"intent_scores": observations},
        )

    def _score_alarm(self, alarm: AlarmEvidence, request: TelecomRequest) -> dict:
        haystack = " ".join([
            request.query.lower(),
            alarm.name.lower(),
            " ".join(str(v).lower() for v in alarm.labels.values()),
        ])
        matches = []
        for intent_id, terms in self.DEFAULT_INTENTS.items():
            hits = [term for term in terms if term in haystack]
            if hits:
                matches.append({"intent_id": intent_id, "score": min(1.0, 0.35 + 0.15 * len(hits)), "hits": hits})
        if not matches:
            return {"alarm": alarm.name, "matched": False, "score": 0.0, "intent_id": None, "retained": True}
        best = sorted(matches, key=lambda item: item["score"], reverse=True)[0]
        return {"alarm": alarm.name, "matched": True, "retained": True, **best}

    @staticmethod
    def _violations(request: TelecomRequest, observations: list[dict]) -> list[IntentViolation]:
        breached = any(kpi.breached for kpi in request.kpis)
        violations = []
        for obs in observations:
            if obs.get("matched") and (breached or obs.get("score", 0) >= 0.65):
                violations.append(
                    IntentViolation(
                        intent_id=obs.get("intent_id"),
                        procedure=obs.get("intent_id"),
                        description=f"Potential service intent violation related to {obs.get('alarm')}.",
                        confidence=float(obs.get("score", 0)),
                        retained=True,
                    )
                )
        return violations

    @staticmethod
    def _retention_reason(obs: dict) -> str:
        if obs.get("matched"):
            return f"intent_score={obs.get('score')}; intent_id={obs.get('intent_id')}"
        return "unmatched intent; retained as standalone observation"

    @classmethod
    def _format_catalog(cls) -> str:
        lines = [
            "**Operational Service Intents Monitored by Telecom Brain:**",
            "",
            "- **`ue_registration`**: 5G Core UE Registration & Authentication (AMF, AUSF, UDM)",
            "- **`data_session_establishment`**: 5G PDU Session / PDP Context Setup (SMF, UPF)",
            "- **`sgi_throughput`**: SGi / N6 User Plane Data Throughput & Saturation (PGW, UPF)",
            "- **`lte_attach_sr`**: 4G LTE Initial Attach Success Rate (MME, HSS, S1-MME)",
            "- **`volte_cssr`**: VoLTE Call Setup Success Rate & SIP Signaling (IMS, P-CSCF, S-CSCF)",
            "- **`ims_registration`**: IMS SIP Initial & Periodic Registration (IMS, SIP)",
            "",
            "These service intents score alarms and KPI deviations to pinpoint subscriber-impacting degradation."
        ]
        return "\n".join(lines)

    @staticmethod
    def _format(observations: list[dict], violations: list[IntentViolation]) -> str:
        lines = ["**Intent Scoring**"]
        for obs in observations:
            if obs.get("matched"):
                lines.append(f"- {obs['alarm']}: {obs['intent_id']} score={obs['score']:.2f}")
            else:
                lines.append(f"- {obs['alarm']}: no intent match; retained")
        if not observations:
            lines.append("- No alarms were provided for intent scoring.")
        if violations:
            lines.append(f"- Possible violations: {len(violations)}")
        return "\n".join(lines)

