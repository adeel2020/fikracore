"""Unit tests for provenance wrapping and the claim taxonomy (§5, §7)."""

from __future__ import annotations

from storyteller.knowledge import (
    CONFIRMED_ROOT_CAUSE,
    CORRELATION,
    EVIDENCE,
    FACT,
    HYPOTHESIS,
    OBSERVATION,
    fact,
    provenance_from_page,
)


def test_fact_constructor_defaults() -> None:
    f = fact("value")
    assert f.value == "value"
    assert f.source is None
    assert f.timestamp is None
    assert f.confidence is None
    assert f.relationship is None
    assert f.extra == {}


def test_fact_full_provenance() -> None:
    f = fact(
        "RSR dropped to 94.7%",
        source="nms/amf-01/rsr",
        timestamp="2026-08-09T06:14:00Z",
        confidence=0.9,
        relationship="detected-by",
        slug="mobile-core/kpi-events/amf-rsr-drop-06-14",
        extra={"metric_value": 94.7},
    )
    d = f.to_dict()
    assert d["value"] == "RSR dropped to 94.7%"  # core value wins over extra
    assert d["source"] == "nms/amf-01/rsr"
    assert d["confidence"] == 0.9
    assert d["relationship"] == "detected-by"
    # extra is flattened in, but never clobbers core fields
    assert d.get("metric_value") == 94.7


def test_provenance_from_page_frontmatter() -> None:
    page = {
        "slug": "mobile-core/hypotheses/amf-cpu-saturation",
        "frontmatter": {
            "source": "incident-bridge/engineer-jdoe",
            "confidence": 0.92,
            "proposed_at": "2026-08-09T06:20:00Z",
        },
        "source_kind": "mcp:put_page",
        "updated_at": "2026-08-09T06:21:00Z",
    }
    p = provenance_from_page(page, relationship="has-hypothesis")
    assert p["source"] == "incident-bridge/engineer-jdoe"
    assert p["confidence"] == 0.92
    assert p["timestamp"] == "2026-08-09T06:20:00Z"
    assert p["relationship"] == "has-hypothesis"
    assert p["slug"] == "mobile-core/hypotheses/amf-cpu-saturation"


def test_provenance_from_page_confidence_parse_failure() -> None:
    page = {"frontmatter": {"confidence": "high"}}
    p = provenance_from_page(page)
    assert p["confidence"] is None


def test_claim_taxonomy_vocabulary() -> None:
    assert FACT in ("FACT",)
    assert OBSERVATION == "OBSERVATION"
    assert CORRELATION == "CORRELATION"
    assert HYPOTHESIS == "HYPOTHESIS"
    assert EVIDENCE == "EVIDENCE"
    assert CONFIRMED_ROOT_CAUSE == "CONFIRMED_ROOT_CAUSE"


def test_provenance_fact_frozen() -> None:
    f = fact("x")
    try:
        f.value = "y"  # type: ignore[misc]
        assert False, "ProvenanceFact should be frozen"
    except Exception:  # noqa: BLE001 - any mutation attempt must fail
        assert f.value == "x"
