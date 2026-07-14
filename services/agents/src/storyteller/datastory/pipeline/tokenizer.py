"""Lifecycle-aware tokenization for semantic decomposition."""

import math

import pandas as pd


def _time_bucket(mins: float) -> str:
    if pd.isna(mins) or mins <= 0:
        return "time_unknown"
    if mins <= 30:
        return "time_fast"
    if mins <= 120:
        return "time_medium"
    if mins <= 480:
        return "time_slow"
    return "time_very_slow"


def build_lifecycle_aware_text(row: pd.Series) -> str:
    """Build a text token focusing ONLY on the three operational reason dimensions:
    Reassignment_Reason, Rejection_Reason, and Resolution_Reason (Resolution_reason).
    """
    reas_val = row.get("Reassignment_Reason")
    rej_val = row.get("Rejection_Reason")
    res_val = row.get("Resolution_Reason", row.get("Resolution_reason"))

    tokens = []

    if pd.notna(reas_val) and str(reas_val).strip() != "":
        tokens.append(f"reas_{str(reas_val).lower().replace(' ', '_')}")
    else:
        tokens.append("reassignment_na")

    if pd.notna(rej_val) and str(rej_val).strip() != "":
        tokens.append(f"rej_{str(rej_val).lower().replace(' ', '_')}")
    else:
        tokens.append("rejection_na")

    if pd.notna(res_val) and str(res_val).strip() != "":
        tokens.append(f"res_{str(res_val).lower().replace(' ', '_')}")
    else:
        tokens.append("resolution_na")

    return " ".join(tokens)
