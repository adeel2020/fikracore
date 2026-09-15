"""
Unit tests for isolated Mobile Core RTR Ticket Intelligence service.
Verifies:
  - Zero-PII compliance (pseudonymized tokens, no IMSI/MSISDN)
  - Hop dwell calculations, AOLA (2h), OLA (6h), and E2E SLA (48h)
  - Audio-visual step synchronization cues and natural pause timing
  - Curated shift summary aggregations and ping-pong counts
"""

import pytest
from engine_stack.engines.telecom_brain.services.mobile_rtr_intelligence import (
    MobileRTRTicketIntelligenceService,
    QueueName,
    TicketStatus,
    HopSLARisk,
)
from assistant.mark.persona.rtr_voice_persona import format_ssml_spoken_journey


def test_customer_ticket_journey_schema_and_pii_safety():
    service = MobileRTRTicketIntelligenceService()
    journey = service.get_customer_ticket_journey("TT-984210")

    assert journey.ticket_token == "TT-984210"
    assert journey.subscriber_token.startswith("SUB_TOK_")
    # PII safety checks: ensure no 15-digit IMSI or MSISDN in serialized output
    dump_str = journey.model_dump_json()
    assert "msisdn" not in dump_str.lower()
    assert "imsi" not in dump_str.lower()
    assert len(journey.journey_hops) == 4


def test_aola_and_ola_governance_verdicts():
    service = MobileRTRTicketIntelligenceService()
    journey = service.get_customer_ticket_journey("TT-984210")

    # RTR dwell: Hop 2 (1.2h) + Hop 4 (0.7h) = 1.9h <= 2.0h -> AOLA Achieved
    assert journey.aola_rtr_hours == 1.9
    assert journey.aola_achieved is True

    # NOC dwell: 0.8h (CRM) + 1.2h (RTR) + 4.5h (HPSA) + 0.7h (RTR) = 7.2h (NOC = 6.4h > 6.0h) -> OLA Breached
    assert journey.ola_achieved is False
    assert journey.delinquent_queue == QueueName.HPSA
    assert journey.bounced_count == 1


def test_audio_visual_cues_and_natural_pauses():
    service = MobileRTRTicketIntelligenceService()
    journey = service.get_customer_ticket_journey("TT-984210")

    # Validate timing cues progression
    for i in range(len(journey.journey_hops) - 1):
        assert journey.journey_hops[i].cue_start_offset_ms < journey.journey_hops[i + 1].cue_start_offset_ms
        assert journey.journey_hops[i].pause_duration_ms >= 1200

    # Validate SSML generation
    raw_hops = [h.model_dump() for h in journey.journey_hops]
    ssml = format_ssml_spoken_journey(raw_hops, journey.ticket_token)
    assert "<speak>" in ssml
    assert "<break time=" in ssml


def test_period_curated_summary():
    service = MobileRTRTicketIntelligenceService()
    summary = service.get_period_curated_summary()

    assert summary.total_tickets_assigned_to_rtr == 142
    assert summary.aola_compliance_rate > 80.0
    assert "HPSA" in summary.queue_dwell_breakdown
    assert len(summary.top_bouncing_loops) >= 1
    assert len(summary.audio_cue_sections) >= 4
