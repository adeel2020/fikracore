from typing import Any, Optional, Callable
from pathlib import Path
from datetime import datetime
import json

def build_zaki(
    
    scenario_id: str,
    run_id: str,
    trigger_display: str,
    stage_vals: dict[str, Any],
    stage_index: int,
) -> dict[str, Any]:
    """Build Zaki AI cognitive state."""
    thought = stage_vals["zaki_thought"]
    if stage_index <= 1:
        thought = "Only raw observations are available. No causal claim is justified yet."
    elif stage_index == 2:
        thought = "Several signals are correlated by timing and dependency. Root cause remains unconfirmed."
    elif stage_index == 3:
        thought = "Candidate explanations are being generated without ranking yet."
    elif stage_index == 4:
        thought = "A leading hypothesis is ranked and being tested against evidence."
    elif stage_index == 5:
        thought = "The unresolved boundary is now explicit. Missing evidence is being isolated."
    elif stage_index >= 6:
        thought = "Validated learning is being assessed before final recommendation."
    return {
        "phase": stage_vals["zaki_phase"],
        "thought": thought,
        "active_focus_entity": trigger_display,
        "confidence": stage_vals["confidence"],
        "scenario_id": scenario_id,
        "run_id": run_id,
    }


