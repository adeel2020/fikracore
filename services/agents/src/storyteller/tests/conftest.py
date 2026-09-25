"""Shared fixtures for the storyteller knowledge and reasoning layer tests.

Knowledge-layer integration tests hit gbrain through HTTP MCP, matching the
runtime storyteller transport. They are skipped when the MCP server is not
reachable or rejects the configured credentials. Reasoning-layer fixtures are
pure in-memory ``IncidentContext`` objects, so they always run.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from dotenv import load_dotenv
from storyteller.knowledge import GbrainClient, MobileCoreKnowledge
from storyteller.knowledge.context import IncidentContext
from storyteller.knowledge.provenance import fact

AMF_INCIDENT = "incidents/transport/transport-n3-mobile-data-stall"
REPO_ROOT = Path(__file__).resolve().parents[5]

load_dotenv(REPO_ROOT / ".env.test.local")
load_dotenv(REPO_ROOT / "backend" / ".env")


@pytest.fixture(scope="session")
def gbrain_available() -> bool:
    try:
        GbrainClient().call("list_pages", {"limit": 1})
        return True
    except Exception:  # noqa: BLE001 - any gbrain failure => skip integration tests
        return False


@pytest.fixture(scope="session")
def knowledge(gbrain_available: bool) -> MobileCoreKnowledge | None:
    if not gbrain_available:
        return None
    return MobileCoreKnowledge(GbrainClient())


# ---------------------------------------------------------------------------
# Reasoning-layer fixtures (pure, no gbrain).
# ---------------------------------------------------------------------------
def confirmed_hypothesis_ctx() -> IncidentContext:
    """A confirmed root-cause story: KPI -> symptom -> confirmed hypothesis ->
    evidence -> remediation -> recovery."""
    kpi = fact("RSR (Registration Success Rate)", relationship="measures",
               slug="kpi/rsr", extra={"value": 94.7, "unit": "percent"})
    kpi_event = fact("RSR critical breach at 06:14", relationship="detected-by",
                     slug="kpi-event/rsr-breach", timestamp="2026-08-09T06:14:00Z",
                     extra={"value": 94.7, "event_type": "alarm", "threshold": "critical",
                            "unit": "percent", "observed_at": "2026-08-09T06:14:00Z"})
    symptom = fact("Registration failure spike", relationship="has-symptom",
                   slug="symptom/reg-fail-spike")
    hyp = fact("AMF-01 CPU saturation from registration load", relationship="has-hypothesis",
               slug="hyp/amf-cpu-sat", confidence=0.92,
               extra={"status": "confirmed", "explains": ["symptom/reg-fail-spike"]})
    evidence1 = fact("AMF-01 CPU utilization pegged at 98%", relationship="supported-by",
                     slug="ev/cpu-98", extra={"hypothesis_slug": "hyp/amf-cpu-sat"})
    evidence2 = fact("NAS REGISTRATION REJECT 'congestion' cause", relationship="supported-by",
                     slug="ev/nas-reject", extra={"hypothesis_slug": "hyp/amf-cpu-sat"})
    rem = fact("Added AMF-01 capacity", relationship="has-remediation", slug="rem/capacity")
    rec = fact("RSR recovered to 99.9%", relationship="verified-by",
               slug="rec/rsr-recovered", timestamp="2026-08-09T07:05:00Z")
    return IncidentContext(
        incident={"slug": AMF_INCIDENT, "frontmatter": {"severity": "SEV-2", "status": "resolved"}},
        timeline=[fact("06:14 RSR critical — 07:05 recovered", relationship="timeline-entry",
                       slug=AMF_INCIDENT)],
        services=[fact("Mobile Core", relationship="affects", slug="svc/mobile-core")],
        network_functions=[fact("AMF-01", relationship="involves", slug="nf/amf-01"),
                           fact("SMF-01", relationship="involves", slug="nf/smf-01")],
        kpis=[kpi],
        kpi_events=[kpi_event],
        symptoms=[symptom],
        hypotheses=[hyp],
        evidence=[evidence1, evidence2],
        remediations=[rem],
        recovery_events=[rec],
    )


def plausible_hypothesis_ctx() -> IncidentContext:
    """A context where the hypothesis is only plausible (no confirmed status),
    so no root cause and the story stays open-ended."""
    hyp = fact("AMF-01 CPU saturation from registration load", relationship="has-hypothesis",
               slug="hyp/amf-cpu-sat", confidence=0.7,
               extra={"explains": ["symptom/reg-fail-spike"]})
    evidence1 = fact("AMF-01 CPU utilization pegged at 98%", relationship="supported-by",
                     slug="ev/cpu-98", extra={"hypothesis_slug": "hyp/amf-cpu-sat"})
    return IncidentContext(
        incident={"slug": AMF_INCIDENT, "frontmatter": {"severity": "SEV-2", "status": "open"}},
        kpi_events=[fact("RSR critical breach at 06:14", relationship="detected-by",
                         slug="kpi-event/rsr-breach")],
        symptoms=[fact("Registration failure spike", relationship="has-symptom",
                       slug="symptom/reg-fail-spike")],
        hypotheses=[hyp],
        evidence=[evidence1],
    )


def insufficient_ctx() -> IncidentContext:
    """No confidence, no evidence, no recovery — everything best-effort."""
    return IncidentContext(
        incident={"slug": AMF_INCIDENT, "frontmatter": {"severity": "SEV-3", "status": "investigating"}},
        hypotheses=[fact("Possible SBC overload", relationship="has-hypothesis",
                         slug="hyp/sbc-overload")],
    )


@pytest.fixture
def ctx_confirmed() -> IncidentContext:
    return confirmed_hypothesis_ctx()


@pytest.fixture
def ctx_plausible() -> IncidentContext:
    return plausible_hypothesis_ctx()


@pytest.fixture
def ctx_insufficient() -> IncidentContext:
    return insufficient_ctx()
