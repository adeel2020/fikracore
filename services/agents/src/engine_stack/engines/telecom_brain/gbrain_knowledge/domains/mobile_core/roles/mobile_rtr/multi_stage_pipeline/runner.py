"""PipelineRunner: Sequentially orchestrates the 6 stages of Mobile RTR triage."""

from __future__ import annotations
from typing import Any, Dict

from .stage_1_location_and_core_profile import execute_stage_1
from .stage_2_it_bss_subscriptions import execute_stage_2
from .stage_3_roaming_checklist import execute_stage_3
from .stage_4_active_troubleshooting import execute_stage_4
from .stage_5_deep_signaling_traces import execute_stage_5
from .stage_6_escalation_hierarchy import execute_stage_6

class PipelineRunner:
    """Executes the sequential 6-stage investigation pipeline for Mobile RTR."""

    def run(self, msisdn: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        ctx = context or {}
        results: Dict[str, Any] = {}
        
        # Stage 1
        s1 = execute_stage_1(msisdn, ctx)
        results["stage_1"] = s1
        if s1.get("exit_to_hpsa"):
            results["final_disposition"] = execute_stage_6(results)
            return results
            
        # Stage 2
        s2 = execute_stage_2(msisdn, ctx)
        results["stage_2"] = s2
        if s2.get("exit_to_billing"):
            results["final_disposition"] = execute_stage_6(results)
            return results
            
        # Stage 3
        s3 = execute_stage_3(msisdn, ctx)
        results["stage_3"] = s3
        if s3.get("exit_to_ireg"):
            results["final_disposition"] = execute_stage_6(results)
            return results
            
        # Stage 4
        s4 = execute_stage_4(msisdn, ctx)
        results["stage_4"] = s4
        if s4.get("resolved_in_rtr"):
            results["final_disposition"] = execute_stage_6(results)
            return results
            
        # Stage 5
        s5 = execute_stage_5(msisdn, ctx)
        results["stage_5"] = s5
        
        # Stage 6
        results["final_disposition"] = execute_stage_6(results)
        return results
