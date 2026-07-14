"""Dual-stream JSON retriever over the persisted semantic Parquet cache.

Produces two payloads:
* **Canvas Stream** — per-ticket x/y co-ordinates, colour axis, opacity, and
  anomaly flags (for the front-end semantic cloud visualisation).
* **Narrative Stream** — cluster-level themes, volumes, exemplar rows, and
  anomalies (for the AI Storyteller agent).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

_HERE = Path(__file__).resolve().parent.parent
_DEFAULT_CACHE = _HERE / "data" / "semantic_state.parquet"


class DataStoryCacheRetriever:
    """Read the Parquet cache and build the dual delivery streams."""

    CATEGORICAL_COLUMNS: List[str] = [
        "Ticket_Queue",
        "Ticket_Status",
        "Issue_Category",
        "Reassignment_Reason",
        "Reassigned_To",
        "Rejection_Reason",
        "Color_Group",
        "Country",
    ]

    def __init__(self, cache_path: str | Path | None = None) -> None:
        self.cache_path = Path(cache_path) if cache_path else _DEFAULT_CACHE

    def get_dual_streams(
        self,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
        """Return ``(canvas_stream, narrative_stream, available_fields)``."""
        if not self.cache_path.exists():
            raise FileNotFoundError(
                "Semantic cache not found — upload operational_data.xlsx first."
            )

        df: pd.DataFrame = pd.read_parquet(self.cache_path)

        # -------------------------------------------------------------------
        # Stream 1 — Canvas (semantic cloud UI)
        # -------------------------------------------------------------------
        canvas_stream: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            canvas_stream.append(
                {
                    "id": str(row["Ticket_ID"]),
                    "x": float(row["Semantic_X"]),
                    "y": float(row["Semantic_Y"]),
                    "z": float(row["Semantic_Z"]),
                    "color_axis": int(row["Eigen_Axis_Alignment"]),
                    "opacity_score": float(row["Centrality_Score"]),
                    "is_anomaly": bool(row["Anomaly_Flag"]),
                    "reassignment_reason": str(row["Reassignment_Reason"]) if pd.notna(row["Reassignment_Reason"]) else "",
                    "reassigned_to": str(row["Reassigned_To"]) if pd.notna(row["Reassigned_To"]) else "",
                    "ticket_queue": str(row["Ticket_Queue"]) if pd.notna(row["Ticket_Queue"]) else "",
                    "issue_category": str(row["Issue_Category"]) if pd.notna(row["Issue_Category"]) else "",
                    "ticket_status": str(row["Ticket_Status"]) if pd.notna(row["Ticket_Status"]) else "",
                    "rejection_reason": str(row["Rejection_Reason"]) if pd.notna(row["Rejection_Reason"]) else "",
                    "resolution_reason": str(row["Resolution_reason"]) if ("Resolution_reason" in row and pd.notna(row["Resolution_reason"])) else (str(row["Resolution_Reason"]) if ("Resolution_Reason" in row and pd.notna(row["Resolution_Reason"])) else ""),
                    "color_group": str(row["Color_Group"]) if pd.notna(row["Color_Group"]) else "",
                    "country": str(row["Country"]) if pd.notna(row["Country"]) else "",
                    "tooltip": (
                        f"{row['Semantic_Cluster_Theme']} | "
                        f"Status: {row['Ticket_Status']}"
                    ),
                }
            )

        # -------------------------------------------------------------------
        # Stream 2 — Narrative (executive brief)
        # -------------------------------------------------------------------
        clusters_summary: List[Dict[str, Any]] = []
        for theme, group in df.groupby("Semantic_Cluster_Theme"):
            centroid_idx = group["Centrality_Score"].idxmax()
            textbook_row = group.loc[centroid_idx]
            anomalies = group[group["Anomaly_Flag"] == True][
                "Cleaned_Text"
            ].tolist()

            clusters_summary.append(
                {
                    "theme": theme,
                    "volume": f"{(len(group) / len(df)) * 100:.1f}%",
                    "highest_centrality_example": str(
                        textbook_row["Cleaned_Text"]
                    ),
                    "anomalies_to_investigate": anomalies[:3],
                    "complaints_count": len(group),
                    "service_journeys": group["Issue_Category"].dropna().unique().tolist(),
                    "ticket_queues": group["Ticket_Queue"].dropna().unique().tolist(),
                    "reassigned_to": group["Reassigned_To"].dropna().unique().tolist(),
                }
            )

        dominant_axis = (
            "Domestic Core"
            if df["Eigen_Axis_Alignment"].mode().iloc[0] == 0
            else "Roaming/RAN Component"
        )

        narrative_stream: Dict[str, Any] = {
            "dominant_operational_axis": dominant_axis,
            "total_tickets": len(df),
            "clusters": clusters_summary,
        }

        available_fields: List[str] = [
            col for col in self.CATEGORICAL_COLUMNS if col in df.columns
        ]

        return canvas_stream, narrative_stream, available_fields
