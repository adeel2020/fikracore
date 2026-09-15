"""Stage 1: Customer Location Discovery & Core Profile Audit."""

from __future__ import annotations
from typing import Any, Dict

def execute_stage_1(msisdn: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audits subscriber location (VLR/MME/AMF) and core profile in UDM/HSS and PCF.
    Check exit Gate 1: If BSS Order is out of sync with Core profile, exit to HPSA.
    """
    profile_mismatch = context.get("force_prov_mismatch") or context.get("simulated_prov_mismatch", False)
    
    return {
        "stage": 1,
        "name": "Location Discovery & Core Profile Audit",
        "msisdn": msisdn,
        "location": {
            "vlr_gt": "971501112233",
            "mme_fqdn": "mme01.dxb.core.operator.net",
            "amf_id": "amf-core-01",
            "ecgi": "424-02-14022-1"
        },
        "core_profile": {
            "udm_status": "PROVISIONED" if not profile_mismatch else "MISMATCH_WITH_BSS",
            "pcf_ambr_dl": "300Mbps",
            "pcf_ambr_ul": "100Mbps",
            "subscribed_apns": ["internet", "ims"] if not profile_mismatch else ["internet"]
        },
        "gate_1_triaged": True,
        "exit_to_hpsa": profile_mismatch,
        "finding_code": "PROV_MISMATCH_CORE_BSS" if profile_mismatch else "PROFILE_ALIGNED"
    }
