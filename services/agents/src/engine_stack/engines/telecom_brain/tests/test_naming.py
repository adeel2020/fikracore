"""Tests for Presentation Naming Resolver & Global Human-Readable Terminology."""

from engine_stack.engines.telecom_brain.presentation.naming import (
    PresentationNamingResolver,
    default_naming_resolver,
)


def test_human_readable_entity_names():
    resolver = PresentationNamingResolver()
    
    assert resolver.to_display_name("topology/transport/routers/ip-rtr-01") == "Transport Router-01"
    assert resolver.to_display_name("IP:PE:RTR-21") == "Provider Edge Router-21"
    assert resolver.to_display_name("SA5G:UPF:003") == "User Plane Function-03"
    assert resolver.to_display_name("INFRA:POWER:A") == "Power Feed A"
    assert resolver.to_display_name("INFRA:DC:A") == "Data Center Facility A"
    assert resolver.to_display_name("MPLS-PE7") == "MPLS Edge Router-07"
    assert resolver.to_display_name("DC-GW-01") == "Data Center Gateway-01"


def test_human_readable_relationship_names():
    resolver = PresentationNamingResolver()
    
    assert resolver.to_relation_label("DEPENDS_ON") == "Depends on"
    assert resolver.to_relation_label("routes-through") == "Routes through"
    assert resolver.to_relation_label("member_of") == "Member of"
    assert resolver.to_relation_label("monitored-by") == "Monitored by"
    assert resolver.to_relation_label("supports_service") == "Supports service"
    assert resolver.to_relation_label("fails-over-to") == "Fails over to"
    assert resolver.to_relation_label("powered-by") == "Powered by"


def test_acronym_expansion_on_first_use():
    resolver = PresentationNamingResolver()
    resolver.reset_expansion_cache()
    
    # First use: expanded with acronym in parentheses
    first_upf = resolver.expand_acronym("UPF")
    assert first_upf == "User Plane Function (UPF)"
    
    # Second use: standard acronym
    second_upf = resolver.expand_acronym("UPF")
    assert second_upf == "UPF"
    
    # Another acronym first use
    first_pe = resolver.expand_acronym("PE")
    assert first_pe == "Provider Edge Router (PE)"
    
    # Reset cache
    resolver.reset_expansion_cache()
    after_reset = resolver.expand_acronym("UPF")
    assert after_reset == "User Plane Function (UPF)"


def test_canonical_id_preserved_for_traceability():
    resolver = PresentationNamingResolver()
    
    formatted = resolver.format_entity("topology/transport/routers/ip-rtr-01")
    assert formatted["display_name"] == "Transport Router-01"
    assert formatted["canonical_id"] == "topology/transport/routers/ip-rtr-01"
    assert "Transport Router-01 (canonical: topology/transport/routers/ip-rtr-01)" in formatted["formatted"]


def test_unknown_acronym_not_invented():
    resolver = PresentationNamingResolver()
    
    # Never invent meaning for unknown acronym or vendor abbreviation
    assert resolver.expand_acronym("XYZABC") == "XYZABC"
    assert resolver.to_display_name("vendor-x/abc-17") == "ABC-17"
    formatted = resolver.format_entity("vendor-x/abc-17")
    assert formatted["display_name"] == "ABC-17"
    assert formatted["canonical_id"] == "vendor-x/abc-17"


def test_naming_policy_applies_to_all_h2_reports():
    resolver = PresentationNamingResolver()
    
    evidence_label = resolver.to_evidence_label("prometheus_metric")
    assert evidence_label == "Performance Metric"
    
    evidence_label2 = resolver.to_evidence_label("grafana_alert")
    assert evidence_label2 == "Monitoring Alert"
    
    sample_prose = "Router-A DEPENDS_ON Data Center Gateway; alert from prometheus_metric."
    formatted = resolver.format_text(sample_prose)
    assert "Depends on" in formatted
    assert "Performance Metric" in formatted
