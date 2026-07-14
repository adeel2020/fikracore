"""Stateful semantic decomposition engine with DataLoader and delta processing.

Builds a TF-IDF → TruncatedSVD → KMeans pipeline over operational ticket
data, persisting vectorizer and cluster state to ``.joblib`` and the
augmented dataframe to ``.parquet`` for later retrieval.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.datastory.pipeline.tokenizer import build_lifecycle_aware_text

# ---------------------------------------------------------------------------
# Paths (relative to this file's parent = backend/datastory/)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent.parent
MODEL_PATH = _HERE / "models" / "semantic_pipeline.joblib"
CACHE_PATH = _HERE / "data" / "semantic_state.parquet"
SSOT_PATH = _HERE / "data" / "operational_data.xlsx"

EXPECTED_COLUMNS: List[str] = [
    "Ticket_ID",
    "Create_Date",
    "Ticket_Queue",
    "Ticket_Status",
    "Issue_Category",
    "Reassignment_Reason",
    "Reassigned_To",
    "Rejection_Reason",
    "Color_Group",
    "Average_Time_spent_in_Mins",
    "Country",
]

REQUIRED_COLUMNS: List[str] = [
    "Ticket_ID",
    "Ticket_Queue",
    "Ticket_Status",
    "Issue_Category",
]


# ---------------------------------------------------------------------------
# Data Loader — robust, read-only SSoT ingestion
# ---------------------------------------------------------------------------
class DataLoader:
    """Safely ingest the ``operational_data.xlsx`` SSoT file.

    * Validates that required columns exist (raises early if missing).
    * Fills optional missing columns with sensible defaults.
    * Keeps the original file read-only (never writes back).
    """

    def __init__(self, path: str | Path = SSOT_PATH) -> None:
        self.path = Path(path)

    def load(self) -> pd.DataFrame:
        """Read and validate the Excel SSoT, returning a clean DataFrame."""
        if not self.path.exists():
            raise FileNotFoundError(
                f"SSoT file not found at {self.path}. "
                "Place operational_data.xlsx in datastory/data/."
            )

        df = pd.read_excel(self.path, engine="openpyxl")

        # -- required column check ------------------------------------------
        missing_req = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_req:
            raise ValueError(
                f"SSoT is missing required columns: {missing_req}. "
                f"Expected: {EXPECTED_COLUMNS}"
            )

        # -- fill optional missing columns with defaults --------------------
        column_defaults = {
            "Reassignment_Reason": None,
            "Reassigned_To": None,
            "Rejection_Reason": None,
            "Color_Group": "",
            "Average_Time_spent_in_Mins": 0.0,
            "Country": None,
            "Create_Date": pd.NaT,
        }
        for col, default in column_defaults.items():
            if col not in df.columns:
                df[col] = default

        return df


# ---------------------------------------------------------------------------
# Delta-aware decomposition engine
# ---------------------------------------------------------------------------
def _derive_cluster_label(group: pd.DataFrame) -> str:
    """Derive a human-readable theme label for a cluster group by combining all reasons."""
    all_reasons = []
    res_col = "Resolution_Reason" if "Resolution_Reason" in group.columns else "Resolution_reason"
    
    for col in [res_col, "Rejection_Reason", "Reassignment_Reason"]:
        if col in group.columns:
            valid_series = group[col].dropna().astype(str).str.strip()
            # Exclude empty values or values indicating NA
            valid_series = valid_series[
                (valid_series != "") & 
                (valid_series.str.lower() != "nan") & 
                (valid_series.str.lower() != "none")
            ]
            all_reasons.extend(valid_series.tolist())
            
    if all_reasons:
        series = pd.Series(all_reasons)
        top_reason = series.mode()
        if not top_reason.empty and top_reason.iloc[0]:
            return str(top_reason.iloc[0])
            
    return "General NOC Support"


def run_semantic_decomposition_engine(raw_xlsx_path: str | Path | None = None) -> None:
    """Execute or incrementally update the semantic decomposition pipeline.

    Steps
    -----
    1. Load the SSoT via ``DataLoader`` (read-only).
    2. Check for a pre-existing cache + model; identify delta rows.
    3. Tokenise, vectorise, decompose (SVD), and cluster (KMeans).
    4. Compute centrality, anomaly flags, and dynamic cluster themes.
    5. Persist the augmented dataframe to ``.parquet`` and the pipeline to
       ``.joblib``.
    """
    loader = DataLoader(raw_xlsx_path or SSOT_PATH)
    df_raw: pd.DataFrame = loader.load()

    # ---- 1. Stateful persistence load / init ------------------------------
    if CACHE_PATH.exists() and MODEL_PATH.exists():
        df_cache = pd.read_parquet(CACHE_PATH)
        state = joblib.load(MODEL_PATH)
        vectorizer: TfidfVectorizer = state["vec"]
        svd: TruncatedSVD = state["svd"]
        kmeans: KMeans = state["km"]

        df_delta = df_raw[~df_raw["Ticket_ID"].isin(df_cache["Ticket_ID"])].copy()
        is_first_run = False
    else:
        df_delta = df_raw.copy()
        vectorizer = TfidfVectorizer(sublinear_tf=True)
        svd = TruncatedSVD(n_components=3, random_state=42)
        kmeans = KMeans(n_clusters=14, random_state=42, n_init="auto")
        is_first_run = True

    if df_delta.empty:
        return  # no new rows to process

    # ---- 2. Tokenisation --------------------------------------------------
    df_delta["Cleaned_Text"] = df_delta.apply(build_lifecycle_aware_text, axis=1)

    # ---- 3. Fit (first run) / transform (delta) ---------------------------
    if is_first_run:
        tfidf_matrix = vectorizer.fit_transform(df_delta["Cleaned_Text"])
        spatial_coords = svd.fit_transform(tfidf_matrix)
        cluster_ids = kmeans.fit_predict(spatial_coords[:, :2])
        joblib.dump({"vec": vectorizer, "svd": svd, "km": kmeans, "eigenvalues": svd.singular_values_.tolist()}, MODEL_PATH)
    else:
        tfidf_matrix = vectorizer.transform(df_delta["Cleaned_Text"])
        spatial_coords = svd.transform(tfidf_matrix)
        cluster_ids = kmeans.predict(spatial_coords[:, :2])

    # ---- 4. Pillar columns ------------------------------------------------
    df_delta["Semantic_X"] = spatial_coords[:, 0]
    df_delta["Semantic_Y"] = spatial_coords[:, 1]
    df_delta["Semantic_Z"] = spatial_coords[:, 2]
    df_delta["Eigen_Axis_Alignment"] = np.argmax(np.abs(spatial_coords), axis=1)
    df_delta["Semantic_Cluster_ID"] = cluster_ids

    # Distance / centrality
    centroids = kmeans.cluster_centers_
    distances = np.sqrt(
        ((spatial_coords[:, :2] - centroids[cluster_ids]) ** 2).sum(axis=1)
    )
    df_delta["Centrality_Score"] = 1.0 / (1.0 + distances)
    if len(distances) > 5:
        threshold = float(np.percentile(distances, 95))
        df_delta["Anomaly_Flag"] = distances > threshold
    else:
        df_delta["Anomaly_Flag"] = False

    # Dynamic cluster theme
    theme_map = (
        df_delta.groupby("Semantic_Cluster_ID")
        .apply(_derive_cluster_label)
        .to_dict()
    )
    df_delta["Semantic_Cluster_Theme"] = (
        df_delta["Semantic_Cluster_ID"].map(theme_map)
    )

    # ---- 5. Persist -------------------------------------------------------
    df_final = df_delta if is_first_run else pd.concat([df_cache, df_delta], ignore_index=True)
    # Ensure the parent directory exists
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(CACHE_PATH, index=False)
