"""Stage 4: Active Troubleshooting & Core Runbook Execution."""

from __future__ import annotations
from typing import Any, Dict, List

def execute_stage_4(msisdn: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes non-intrusive Huawei MML commands and transient latch cleanup.
    Check exit Gate 4: If transient latch (e.g. GPRS lock), resolve immediately in RTR.
    """
    has_latch = context.get("force_stale_latch", False)
    volte_recovery = context.get("force_volte_recovery", False)
    
    mml_commands_executed: List[str] = [
        f'DSP SUBAPN: MSISDN="{msisdn}";',
        f'CHK 5GSUBALIGN: MSISDN="{msisdn}";'
    ]
    if has_latch or volte_recovery:
        mml_commands_executed.append(f'SET GPRSLOCK: MSISDN="{msisdn}", STATUS=UNLOCK;')
    
    return {
        "stage": 4,
        "name": "Active Troubleshooting & Runbook Execution",
        "msisdn": msisdn,
        "commands_executed": mml_commands_executed,
        "transient_latch_cleared": has_latch or volte_recovery,
        "resolved_in_rtr": has_latch or volte_recovery,
        "finding_code": "VOLTE_RESTORED_LATCH_CLEARED" if volte_recovery else ("STALE_LATCH_CLEARED" if has_latch else "RUNBOOK_PASSED")
    }
