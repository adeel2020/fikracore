"""Tests for Mobile RTR Troubleshooting Service and Semantic Layer."""

from __future__ import annotations

import pytest

from engine_stack.engines.telecom_brain import TelecomBrainEngine
from engine_stack.engines.telecom_brain.engine_context import create_default_context
from engine_stack.engines.telecom_brain.models import TelecomRequest
from engine_stack.engines.telecom_brain.services.mobile_rtr import MobileRTRService
from storyteller.knowledge.gbrain_client import GbrainClient


@pytest.mark.anyio
async def test_mobile_rtr_service_confidence_routing() -> None:
    service = MobileRTRService()

    # Query with MSISDN and trouble ticket terms
    score_msisdn = await service.can_handle(TelecomRequest(query="Investigate trouble ticket for MSISDN 971501234567"))
    assert score_msisdn >= 0.85

    # Query for shift reporting
    score_shift = await service.can_handle(TelecomRequest(query="Give me the Mobile Core RTR shift report with ticket counts"))
    assert score_shift >= 0.85

    # Query with Huawei MML
    score_mml = await service.can_handle(TelecomRequest(query="DSP SUBAPN: MSISDN=\"971501234567\";"))
    assert score_mml >= 0.85

    # Unrelated query
    score_unrelated = await service.can_handle(TelecomRequest(query="what is the weather today in Paris"))
    assert score_unrelated == 0.0


@pytest.mark.anyio
async def test_mobile_rtr_shift_telemetry_report() -> None:
    service = MobileRTRService()
    request = TelecomRequest(query="Generate Mobile Core RTR shift report and disposition breakdown")

    result = await service.handle(request, create_default_context())

    assert result.service_id == "mobile_rtr_troubleshooting"
    assert "Mobile Core RTR Shift Disposition & Telemetry Report" in result.text
    assert "70.4%" in result.text
    assert "PROV_MISMATCH_CORE_BSS" in result.text
    assert result.spoken_response
    assert "One hundred forty-two trouble tickets investigated" in result.spoken_response

    data = result.data["mobile_rtr"]
    assert data["total_tickets"] == 142
    assert data["reassigned_count"] == 104
    assert data["rejected_count"] == 22
    assert data["resolved_count"] == 16
    assert data["provisioning_mismatch_share"] == 70.4

    # Check visual widgets
    assert "visual_explanation" in result.data
    widgets = result.data["visual_explanation"]["widgets"]
    assert any(w["type"] == "domain_impact_map" for w in widgets)
    assert any(w["type"] == "next_action_tree" for w in widgets)


@pytest.mark.anyio
async def test_mobile_rtr_provisioning_mismatch_exit_gate_1() -> None:
    service = MobileRTRService()
    request = TelecomRequest(query="Investigate 4G/5G data activation failure for subscriber 971508821900")

    result = await service.handle(request, create_default_context())

    assert result.service_id == "mobile_rtr_troubleshooting"
    assert "971508821900" in result.text
    assert "REASSIGNED" in result.text
    assert "PROV_MISMATCH_CORE_BSS" in result.text
    assert "IT Provisioning Team" in result.text
    assert "ORD-20260907-883921" in result.text
    assert "MOD SUBAPN" in result.text
    assert "DSP SUBAPN" in result.text

    data = result.data["mobile_rtr"]
    assert data["exit_stage"] == 1
    assert data["disposition"] == "REASSIGNED"
    assert data["reason_code"] == "PROV_MISMATCH_CORE_BSS"


@pytest.mark.anyio
async def test_mobile_rtr_commercial_fup_exit_gate_2() -> None:
    service = MobileRTRService()
    request = TelecomRequest(query="Customer 971509988771 complains of slow data and severe slowness bandwidth")

    result = await service.handle(request, create_default_context())

    assert "REJECTED" in result.text
    assert "COMMERCIAL_FUP_THROTTLED" in result.text
    assert "Rating-Group 432" in result.text

    data = result.data["mobile_rtr"]
    assert data["exit_stage"] == 2
    assert data["disposition"] == "REJECTED"
    assert data["reason_code"] == "COMMERCIAL_FUP_THROTTLED"


@pytest.mark.anyio
async def test_mobile_rtr_volte_recovery_exit_gate_4() -> None:
    service = MobileRTRService()
    request = TelecomRequest(query="Subscriber 971503344552 cannot make VoLTE calls after update")

    result = await service.handle(request, create_default_context())

    assert "RESOLVED" in result.text
    assert "RES_VOLTE_ENABLED" in result.text

    data = result.data["mobile_rtr"]
    assert data["exit_stage"] == 4
    assert data["disposition"] == "RESOLVED"


@pytest.mark.anyio
async def test_mobile_rtr_mnp_definition_mismatch_exit_gate_5() -> None:
    service = MobileRTRService()
    request = TelecomRequest(query="Inbound calls fail for ported MNP number 971507766554")

    result = await service.handle(request, create_default_context())

    assert "REASSIGNED" in result.text
    assert "SPS_MNP_ROUTING_MISMATCH" in result.text
    assert "SPS / Signaling Operations Team" in result.text

    data = result.data["mobile_rtr"]
    assert data["exit_stage"] == 5
    assert data["disposition"] == "REASSIGNED"


@pytest.mark.anyio
async def test_telecom_brain_engine_end_to_end_routing() -> None:
    engine = TelecomBrainEngine()
    result = await engine.process("Run Mobile RTR ticket triage for subscriber 971501112233")

    assert result.trace.selected_service == "mobile_rtr_troubleshooting"
    assert "Mobile Core RTR Multi-Stage Investigation Report" in result.text
    assert "971501112233" in result.text
    assert "mobile_rtr" in result.data


@pytest.mark.anyio
def test_gbrain_embedded_rtr_knowledge_nodes() -> None:
    client = GbrainClient()

    page = client.call("get_page", {"slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline"})
    assert page is not None
    assert page["type"] == "procedure"
    assert "STAGE 0: Ingestion & Frontline Precheck Validation Gate" in page["compiled_truth"]
    assert "STAGE 1: Customer Location Discovery" in page["compiled_truth"]
    assert "~70% of tickets" in page["compiled_truth"]

    matrix_page = client.call("get_page", {"slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/concern-findings-matrix"})
    assert matrix_page is not None
    assert "PROV_MISMATCH_CORE_BSS" in matrix_page["compiled_truth"]
    assert "routeSelectFailure" in matrix_page["compiled_truth"]

    catalog_page = client.call("get_page", {"slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/services-and-tools-catalog"})
    assert catalog_page is not None
    assert "Multi-Device / Multi-SIM" in catalog_page["compiled_truth"]
    assert "POS Devices & IoT" in catalog_page["compiled_truth"]
    assert "Corporate Private APNs" in catalog_page["compiled_truth"]
    assert "eSIM Profile Services" in catalog_page["compiled_truth"]
    assert "Toll-Free Numbers (TFN 800)" in catalog_page["compiled_truth"]

    runbook_page = client.call("get_page", {"slug": "telecom-brain/domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks"})
    assert runbook_page is not None
    assert "DSP SUBAPN" in runbook_page["compiled_truth"]
    assert "MOD SUBAPN" in runbook_page["compiled_truth"]
    assert "SET GPRSLOCK" in runbook_page["compiled_truth"]


def test_mobile_rtr_knowledge_retrieval() -> None:
    from engine_stack.engines.telecom_brain.gbrain_knowledge.domains.mobile_core.roles.mobile_rtr.knowledge_retrieval import (
        MobileRTRKnowledge,
    )

    rtr_knowledge = MobileRTRKnowledge()
    gov = rtr_knowledge.get_sla_governance()
    assert gov["aola_target_hours"] == 2.0
    assert gov["ola_target_hours"] == 6.0
    assert gov["sla_target_hours"] == 48.0

    ticket_data = rtr_knowledge.get_ticket_journey_data("TT-984210")
    assert ticket_data is not None
    assert len(ticket_data.get("hops", [])) == 4

    topo = rtr_knowledge.get_queue_topology()
    assert topo is not None

    mml = rtr_knowledge.get_huawei_mml_catalog()
    assert mml is not None

    services = rtr_knowledge.get_telecom_services_catalog()
    assert services is not None


def test_mobile_rtr_ticket_intelligence_dynamic_journey() -> None:
    from engine_stack.engines.telecom_brain.services.mobile_rtr_intelligence import (
        MobileRTRTicketIntelligenceService,
        QueueName,
    )

    service = MobileRTRTicketIntelligenceService()
    journey = service.get_customer_ticket_journey("TT-984210")

    assert journey.ticket_token == "TT-984210"
    assert journey.subscriber_token == "SUB_TOK_7B9A2F"
    assert len(journey.journey_hops) == 4
    assert journey.aola_achieved is True
    assert journey.delinquent_queue == QueueName.HPSA
    assert journey.bounced_count == 1
    assert "TT-984210" in journey.spoken_journey_script


def test_mobile_rtr_multi_stage_pipeline_runner() -> None:
    from engine_stack.engines.telecom_brain.gbrain_knowledge.domains.mobile_core.roles.mobile_rtr.multi_stage_pipeline import (
        PipelineRunner,
    )

    runner = PipelineRunner()
    # Test nominal run
    res = runner.run("971501234567", {})
    assert "stage_1" in res
    assert "stage_2" in res
    assert "stage_3" in res
    assert "stage_4" in res
    assert "stage_5" in res
    assert res["final_disposition"]["disposition"] == "RESOLVED_IN_RTR"

    # Test Gate 1 exit to HPSA on BSS provisioning mismatch
    mismatch_res = runner.run("971501234567", {"force_prov_mismatch": True})
    assert mismatch_res["stage_1"]["exit_to_hpsa"] is True
    assert mismatch_res["final_disposition"]["target_queue"] == "HPSA"

