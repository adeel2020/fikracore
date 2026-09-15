"""MCP writer for correlation outputs using the existing gbrain schema."""

from __future__ import annotations

import json
import re
from typing import Any

from storyteller.knowledge.gbrain_client import GbrainClient

from .models import AlarmEvent, CorrelationResult, EvidenceEvent
from .namespaces import (
    canonicalize_incident_slug,
    correlation_cluster_slug,
    correlation_decision_slug,
    correlation_hypothesis_slug,
    incident_aliases,
    incident_slug as make_incident_slug,
)


class GbrainWriter:
    def __init__(self, client: GbrainClient | None = None) -> None:
        self.client = client or GbrainClient()

    def write(self, result: CorrelationResult) -> str:
        """Upsert a correlation hypothesis and its evidence using existing types."""
        service = result.services[0] if result.services else "unmapped-service"
        incident_slug = make_incident_slug(service, result.correlation_key)
        aliases = incident_aliases(incident_slug)
        hypothesis_slug = correlation_hypothesis_slug(result.correlation_key)
        cluster_slug = correlation_cluster_slug(result.correlation_key)
        decision_slug = correlation_decision_slug(result.correlation_key)
        timeline = self._timeline_body(result)
        incident_frontmatter = {
            "title": self._incident_title(result),
            "status": "open" if result.outcome == "incident" else "candidate",
            "severity": self._severity(result),
            "correlation_key": result.correlation_key,
            "correlation_score": result.score,
            "correlation_scope": result.scope,
            "contributing_domains": result.domains,
            "intent_status": result.intent_status,
            "correlation_reasons": result.reasons,
            "canonical_slug": incident_slug,
            "legacy_aliases": aliases,
            "fcaps": self._incident_fcaps(result),
        }
        self._put(incident_slug, "incident", incident_frontmatter, f"Correlation outcome: {result.outcome}.\n\n{timeline}")
        for alias in aliases:
            self._put(alias, "incident-alias", {
                **incident_frontmatter,
                "alias_of": incident_slug,
            }, f"Legacy alias for {incident_slug}.\n\n{timeline}")
        self._put(hypothesis_slug, "hypothesis", {
            "title": self._hypothesis_title(result),
            "status": "plausible",
            "confidence": min(result.score / 100, 0.99),
            "correlation_key": result.correlation_key,
            "fcaps": self._incident_fcaps(result),
        }, self._hypothesis_title(result))
        self._put(cluster_slug, "correlation-cluster", {
            "title": f"Correlation cluster {result.correlation_key}",
            "correlation_key": result.correlation_key,
            "score": result.score,
            "scope": result.scope,
            "outcome": result.outcome,
            "domains": result.domains,
            "services": result.services,
            "reasons": result.reasons,
            "fcaps": self._incident_fcaps(result),
        }, self._correlation_body(result))
        self._put(decision_slug, "correlation-decision", {
            "title": f"Correlation decision {result.correlation_key}",
            "correlation_key": result.correlation_key,
            "outcome": result.outcome,
            "score": result.score,
            "promotion_reasons": result.reasons,
            "fcaps": self._incident_fcaps(result),
        }, f"Decision: {result.outcome}; score: {result.score}.")
        self._link(incident_slug, hypothesis_slug, "has-hypothesis")
        self._link(incident_slug, cluster_slug, "derived-from")
        self._link(cluster_slug, decision_slug, "has-decision")
        for alias in aliases:
            self._link(alias, incident_slug, "alias-of")
            self._link(alias, hypothesis_slug, "has-hypothesis")
            self._link(alias, cluster_slug, "derived-from")
        for service_id in result.services:
            service_slug = self._service_procedure_slug(service_id)
            self._put(service_slug, "service-procedure", {
                "title": self._display_name(service_id),
                "source": "correlation-worker",
                "domain": "mobile-core",
                "fcaps": self._procedure_fcaps(service_id),
            }, self._display_name(service_id))
            self._link(incident_slug, service_slug, "affects")
            for alias in aliases:
                self._link(alias, service_slug, "affects")
        component_slugs: set[str] = set()
        for index, alarm in enumerate(result.alarms):
            evidence_slug = self._alarm_evidence_slug(alarm, result.correlation_key, index)
            component_slug = self._function_slug(alarm)
            if component_slug not in component_slugs:
                component_slugs.add(component_slug)
                self._put(component_slug, "domain-function", {
                    "title": f"{alarm.object_id} ({alarm.component_kind}, {alarm.domain})",
                    "source": alarm.source_system,
                    "domain": alarm.domain,
                    "component_kind": alarm.component_kind,
                    "location": alarm.location,
                    "fcaps": {"primary": "fault", "related": ["performance", "change"]},
                }, f"{alarm.object_id} ({alarm.component_kind}, {alarm.domain})")
                self._link(incident_slug, component_slug, "involves")
                for alias in aliases:
                    self._link(alias, component_slug, "involves")
            self._put(evidence_slug, "evidence", {
                "title": self._alarm_title(alarm),
                "source": alarm.source_system,
                "source_event_id": alarm.source_id,
                "domain": alarm.domain,
                "object_id": alarm.object_id,
                "component_kind": alarm.component_kind,
                "observed_at": alarm.timestamp.isoformat(),
                "severity": alarm.severity,
                "evidence_kind": "alarm",
                "fcaps": {"primary": "fault", "related": ["performance"]},
            }, f"Alarm {alarm.alarm_code} observed on {alarm.object_id}.")
            self._link(hypothesis_slug, evidence_slug, "supported-by")
            self._link(cluster_slug, evidence_slug, "grouped")
            self._link(evidence_slug, component_slug, "observed-on")
        for index, evidence in enumerate(result.evidence):
            if evidence.kind == "kpi":
                event_slug = f"incidents/mobile-core/kpi-events/{self._slug_part(evidence.source_id)}"
                kpi_name = evidence.attributes.get("kpi") or evidence.attributes.get("name") or "service KPI"
                self._put(event_slug, "kpi-event", {
                    "title": self._evidence_title(evidence),
                    "source": evidence.source_id,
                    "event_type": "breach" if evidence.breached else "observation",
                    "threshold": "breached" if evidence.breached else "observed",
                    "observed_at": evidence.timestamp.isoformat(),
                    "service_id": evidence.service_id,
                    "kpi": kpi_name,
                    "fcaps": {"primary": "performance", "related": ["fault"]},
                }, f"{kpi_name} {'breached' if evidence.breached else 'observed'} for {evidence.service_id or 'unknown service'}.")
                kpi_slug = f"knowledge/mobile-core/kpis/{self._slug_part(str(kpi_name))}"
                self._put(kpi_slug, "kpi", {
                    "title": self._display_name(str(kpi_name)),
                    "source": "correlation-worker",
                    "fcaps": {"primary": "performance", "related": ["fault"]},
                }, self._display_name(str(kpi_name)))
                self._link(incident_slug, event_slug, "detected-by")
                self._link(event_slug, kpi_slug, "measures")
                for alias in aliases:
                    self._link(alias, event_slug, "detected-by")
            evidence_slug = self._evidence_slug(evidence, result.correlation_key, index)
            self._put(evidence_slug, "evidence", {
                "title": self._evidence_title(evidence),
                "source": evidence.source_id,
                "source_namespace": evidence.source_namespace,
                "source_kind": evidence.attributes.get("source_kind"),
                "observed_at": evidence.timestamp.isoformat(),
                "evidence_kind": evidence.kind,
                "service_id": evidence.service_id,
                "breached": evidence.breached,
                "domain": evidence.attributes.get("domain"),
                "object_id": evidence.attributes.get("object_id"),
                "grafana_url": evidence.attributes.get("grafana_url"),
                "query_hash": evidence.attributes.get("query_hash"),
                "window_start": evidence.attributes.get("window_start"),
                "window_end": evidence.attributes.get("window_end"),
                "fcaps": self._evidence_fcaps(evidence),
            }, self._evidence_body(evidence))
            self._link(hypothesis_slug, evidence_slug, "supported-by")
            self._link(cluster_slug, evidence_slug, "grouped")
        self._write_storytelling_trace(result, incident_slug)
        self._write_learning_note(result, incident_slug)
        return incident_slug

    def _put(self, slug: str, page_type: str, frontmatter: dict[str, Any], body: str) -> None:
        content = "---\n" + "\n".join(
            f"{key}: {json.dumps(value)}" for key, value in {"type": page_type, **frontmatter}.items()
        ) + f"\n---\n\n{body}\n"
        self.client.call("put_page", {"slug": slug, "content": content, "ingested_via": "correlation-worker"})

    def _link(self, source: str, target: str, link_type: str) -> None:
        links = self.client.call("get_links", {"slug": source})
        if any(link.get("to_slug") == target and link.get("link_type") == link_type for link in links if isinstance(link, dict)):
            return
        self.client.call("add_link", {"from": source, "to": target, "link_type": link_type, "link_source": "correlation-worker"})

    @staticmethod
    def _severity(result: CorrelationResult) -> str:
        if any(alarm.severity.lower() == "critical" for alarm in result.alarms):
            return "SEV-1"
        return "SEV-2" if result.outcome == "incident" else "SEV-3"

    @staticmethod
    def _slug_part(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
        return slug or "unknown"

    def _alarm_evidence_slug(self, alarm: AlarmEvent, correlation_key: str, index: int) -> str:
        if alarm.source_system.startswith("grafana"):
            suffix = self._source_suffix(alarm.source_id, correlation_key, index)
            return f"grafana/alerts/{suffix}"
        return f"mobile-core/evidence/alarm-{correlation_key}-{index}"

    def _evidence_slug(self, evidence: EvidenceEvent, correlation_key: str, index: int) -> str:
        namespace = evidence.source_namespace
        if namespace == "grafana":
            folder = {
                "kpi": "metrics",
                "log": "logs",
                "trace": "traces",
                "dashboard": "dashboards",
                "panel": "panels",
                "ticket": "tickets",
                "change": "changes",
            }.get(evidence.kind, "evidence")
            suffix = self._source_suffix(evidence.source_id, correlation_key, index)
            return f"grafana/{folder}/{suffix}"
        return f"mobile-core/evidence/{self._slug_part(evidence.kind)}-{correlation_key}-{index}"

    def _source_suffix(self, source_id: str, correlation_key: str, index: int) -> str:
        source = self._slug_part(source_id)
        if source and source != "unknown":
            return source
        return f"{correlation_key}-{index}"

    def _service_procedure_slug(self, service_id: str) -> str:
        network = {
            "lte-attach": "lte",
            "ue-registration": "5gcn",
            "sgi-data": "ps",
            "voice-call-setup": "ims",
        }.get(service_id, "shared")
        procedure = {
            "sgi-data": "sgi-data-forwarding",
        }.get(service_id, service_id)
        return f"domains/mobile-core/networks/{network}/service-procedures/{self._slug_part(procedure)}"

    def _function_slug(self, alarm: AlarmEvent) -> str:
        domain = self._slug_part(alarm.domain)
        if domain == "mobile-core":
            network = self._network_area(alarm)
            return f"domains/mobile-core/networks/{network}/functions/{self._slug_part(alarm.object_id)}"
        return f"domains/{domain}/functions/{self._slug_part(alarm.object_id)}"

    @staticmethod
    def _network_area(alarm: AlarmEvent) -> str:
        domain = alarm.domain.lower()
        kind = alarm.component_kind.lower()
        if domain in {"ims", "cs", "ps", "lte", "5gcn", "vas", "iot"}:
            return domain
        if "mme" in kind or "hss" in kind or "enodeb" in kind:
            return "lte"
        if "pgw" in kind or "sgw" in kind or "firewall" in kind or "nat" in kind:
            return "ps"
        if "pcscf" in kind or "scscf" in kind:
            return "ims"
        return "shared"

    @staticmethod
    def _incident_fcaps(result: CorrelationResult) -> dict[str, Any]:
        related = ["performance"] if result.intent_status == "violated" else []
        if any(item.kind == "change" for item in result.evidence):
            related.append("change")
        return {"primary": "fault", "related": sorted(set(related + ["change"]))}

    @staticmethod
    def _procedure_fcaps(service_id: str) -> dict[str, Any]:
        primary = "performance" if service_id in {"sgi-data", "lte-attach", "voice-call-setup", "ue-registration"} else "fault"
        return {"primary": primary, "related": ["fault", "change"]}

    @staticmethod
    def _evidence_fcaps(evidence: EvidenceEvent) -> dict[str, Any]:
        if evidence.kind == "kpi":
            return {"primary": "performance", "related": ["fault"]}
        if evidence.kind == "change":
            return {"primary": "change", "related": ["fault", "performance"]}
        if evidence.kind in {"log", "trace", "ticket"}:
            return {"primary": "fault", "related": ["performance"]}
        return {"primary": "fault", "related": []}

    def _write_storytelling_trace(self, result: CorrelationResult, incident_slug: str) -> None:
        from .namespaces import story_run_slug, story_slug

        story = story_slug(incident_slug)
        run = story_run_slug(incident_slug, result.correlation_key)
        self._put(story, "story", {
            "title": f"Story for {incident_slug}",
            "incident_id": incident_slug,
            "story_kind": "deterministic-incident-story",
            "fcaps": self._incident_fcaps(result),
        }, f"Deterministic story artifact for {incident_slug}.")
        self._put(run, "story-run", {
            "title": f"Story build trace for {incident_slug}",
            "incident_id": incident_slug,
            "correlation_key": result.correlation_key,
            "inputs": {
                "alarms": [alarm.source_id for alarm in result.alarms],
                "evidence": [item.source_id for item in result.evidence],
            },
            "fcaps": self._incident_fcaps(result),
        }, "Story run records the deterministic inputs used to build the incident narrative.")
        self._link(story, incident_slug, "narrates")
        self._link(run, incident_slug, "builds-story-for")
        self._link(incident_slug, story, "has-story")

    def _write_learning_note(self, result: CorrelationResult, incident_slug: str) -> None:
        service = result.services[0] if result.services else "unmapped-service"
        note_slug = f"learning/mobile-core/notes/{self._slug_part(service)}-{self._slug_part(result.correlation_key)}"
        playbook_slug = f"assets/mobile-core/playbooks/{self._slug_part(service)}-failure-triage"
        query_slug = f"assets/mobile-core/queries/promql/{self._slug_part(service)}"
        self._put(playbook_slug, "playbook", {
            "title": f"{self._display_name(service)} failure triage",
            "status": "candidate",
            "fcaps": self._incident_fcaps(result),
        }, "Candidate playbook proposed from correlation learning.")
        self._put(query_slug, "query-asset", {
            "title": f"{self._display_name(service)} telemetry query",
            "status": "candidate",
            "fcaps": {"primary": "performance", "related": ["fault"]},
        }, "Candidate reusable Grafana query asset proposed from correlation learning.")
        self._put(note_slug, "learning-note", {
            "title": f"Learning note for {self._display_name(service)}",
            "status": "needs_review",
            "confidence": min(result.score / 100, 0.99),
            "area": "mobile-core",
            "service_procedure": service,
            "problem": "service procedure degraded or at risk",
            "intent_status": result.intent_status,
            "fcaps": self._incident_fcaps(result),
            "fcaps_review": self._fcaps_review(result),
            "asset_gap": True,
            "proposed_assets": [playbook_slug, query_slug],
        }, self._learning_note_body(result, service))
        self._link(note_slug, incident_slug, "learned-from")
        self._link(note_slug, playbook_slug, "proposes-asset")
        self._link(note_slug, query_slug, "proposes-asset")
        self._link(incident_slug, note_slug, "has-learning-note")

    def _learning_note_body(self, result: CorrelationResult, service: str) -> str:
        evidence = ", ".join(item.source_id for item in result.evidence) or "no supporting non-alarm evidence"
        return (
            f"This note captures a reusable learning opportunity for {self._display_name(service)}. "
            f"The correlation score was {result.score}, the scope was {result.scope}, "
            f"and the supporting evidence included {evidence}. Review before promoting proposed assets."
        )

    @staticmethod
    def _fcaps_review(result: CorrelationResult) -> dict[str, Any]:
        return {
            "fault": {"findings": result.reasons},
            "change": {"findings": [], "gaps": ["No change request source is linked yet."]},
            "accounting": {"findings": [], "gaps": ["No usage or subscriber-volume evidence is linked yet."]},
            "performance": {"findings": [item.source_id for item in result.evidence if item.kind == "kpi"]},
            "security": {"findings": [], "gaps": ["No security evidence source is linked yet."]},
        }

    def _correlation_body(self, result: CorrelationResult) -> str:
        lines = [
            f"Correlation key: {result.correlation_key}",
            f"Outcome: {result.outcome}",
            f"Scope: {result.scope}",
            f"Score: {result.score}",
            "",
            "Reasons:",
        ]
        lines.extend(f"- {reason}" for reason in result.reasons)
        return "\n".join(lines)

    @staticmethod
    def _display_name(value: str) -> str:
        words = str(value).replace("-", " ").replace("_", " ").split()
        acronyms = {"amf", "cpu", "gnb", "kpi", "lte", "ran", "rsr", "sgi", "ue"}
        return " ".join(word.upper() if word.lower() in acronyms else word.title() for word in words)

    def _incident_title(self, result: CorrelationResult) -> str:
        services = ", ".join(self._display_name(s) for s in result.services) or "Unmapped Service"
        return f"{result.scope.title()} incident candidate for {services}"

    def _hypothesis_title(self, result: CorrelationResult) -> str:
        services = ", ".join(self._display_name(s) for s in result.services) or "unmapped service"
        domains = ", ".join(result.domains) or "unknown domains"
        return f"{result.scope.title()} alarm correlation impacting {services} across {domains}"

    @staticmethod
    def _alarm_title(alarm) -> str:
        return f"{alarm.severity.title()} {alarm.domain} alarm {alarm.alarm_code} on {alarm.object_id}"

    @staticmethod
    def _evidence_title(evidence) -> str:
        label = evidence.attributes.get("label") or evidence.attributes.get("description")
        if label:
            return str(label)
        service = evidence.service_id or "unknown service"
        state = "breach" if evidence.breached else "observation"
        return f"{evidence.kind.upper()} {state} for {service}"

    def _evidence_body(self, evidence) -> str:
        body = self._evidence_title(evidence)
        if evidence.attributes:
            body += "\n\nAttributes:\n" + "\n".join(
                f"- {key}: {value}" for key, value in sorted(evidence.attributes.items())
            )
        return body

    def _timeline_body(self, result: CorrelationResult) -> str:
        entries: list[str] = ["## Timeline"]
        timeline_items = [
            (alarm.timestamp, self._alarm_title(alarm)) for alarm in result.alarms
        ] + [
            (evidence.timestamp, self._evidence_title(evidence)) for evidence in result.evidence
        ]
        for timestamp, title in sorted(timeline_items, key=lambda item: item[0]):
            entries.append(f"- **{timestamp.isoformat()}** - {title}")
        return "\n".join(entries)
