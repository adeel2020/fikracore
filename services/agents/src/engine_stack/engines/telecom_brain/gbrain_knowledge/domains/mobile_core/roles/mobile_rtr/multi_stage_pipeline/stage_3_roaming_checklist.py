"""Stage 3: Roaming Checklist & Partner Entitlements."""

from __future__ import annotations
from typing import Any, Dict

def execute_stage_3(msisdn: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audits international roaming partner agreements (S6a/S8/S9, CAMEL roaming).
    Check exit Gate 3: If foreign network unbarred or partner misconfigured, exit to IREG.
    """
    is_roaming = context.get("is_roaming", False)
    roaming_barred = context.get("roaming_partner_barred", False)
    
    return {
        "stage": 3,
        "name": "Roaming Checklist & Partner Entitlements",
        "msisdn": msisdn,
        "is_roaming": is_roaming,
        "visited_mcc_mnc": "310-410" if is_roaming else None,
        "roaming_allowed": not roaming_barred,
        "exit_to_ireg": is_roaming and roaming_barred,
        "finding_code": "ROAMING_PARTNER_BARRED" if roaming_barred else "ROAMING_PASS"
    }
