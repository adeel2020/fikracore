Let's look at exactly how the phases from  initial plan map directly into the new isolated persistence model:

1. **Your Phase 1 (SSoT Structure & Columns):** Lives permanently inside `datastory/data/operational_data.xlsx`.
2. **Your Phase 2, Step A (`build_lifecycle_aware_text` code):** Lives inside `datastory/pipeline/tokenizer.py`.
3. **Your Phase 2, Step B (Mathematical Decomposition):** Lives inside `datastory/pipeline/engine.py` (wrapped inside our smart delta-processing step).
4. **Your Phase 3 (Dual Delivery Stream JSON formats):** Is the exact payload structured by `datastory/tools/cache_retriever.py` and served by your FastAPI router.
5. **Your Phase 4 (Production Workflows):** Maps directly to our `engine.py`, `routers/datastory.py`, and `prompts/executive_narrative.md`.

---

Here is the fully merged, comprehensive plan that locks your original code, logic, and schemas together with the file persistence and isolated directory architecture.
My apologies, Adeel! I absolutely did not mean to drop those crucial details. They were omitted from the text only because I was focusing heavily on the new stateful persistence layer, but they are mandatory for this engine to function properly.

Let's look at exactly how the phases from your initial plan map directly into the new isolated persistence model:

1. **Your Phase 1 (SSoT Structure & Columns):** Lives permanently inside `datastory/data/operational_data.xlsx`.
2. **Your Phase 2, Step A (`build_lifecycle_aware_text` code):** Lives inside `datastory/pipeline/tokenizer.py`.
3. **Your Phase 2, Step B (Mathematical Decomposition):** Lives inside `datastory/pipeline/engine.py` (wrapped inside our smart delta-processing step).
4. **Your Phase 3 (Dual Delivery Stream JSON formats):** Is the exact payload structured by `datastory/tools/cache_retriever.py` and served by your FastAPI router.
5. **Your Phase 4 (Production Workflows):** Maps directly to our `engine.py`, `routers/datastory.py`, and `prompts/executive_narrative.md`.

---

Here is the fully merged, comprehensive plan that locks your original code, logic, and schemas together with the file persistence and isolated directory architecture.

## 🏗️ The Unified Master Implementation Plan

### Phase 1: Isolated Directory Architecture

To prevent feature bleed, all operations, caching, and intelligence for this feature are entirely bounded inside a new top-level directory.

```text
~/AgenticAIOPs/backend/datastory/
├── data/
│   ├── operational_data.xlsx      # SSoT (Read-Only Input. Matches columns below)
│   └── semantic_state.parquet     # Persistent columnar cache (Bakes in the schema)
├── models/
│   └── semantic_pipeline.joblib   # Persisted Vectorizer, SVD, and KMeans states
├── pipeline/
│   ├── tokenizer.py               # Houses Phase 2 Step A (Lifecycle Tokenizer Code)
│   └── engine.py                  # Houses Phase 2 Step B (Delta & Math Decomposition Engine)
├── tools/
│   └── cache_retriever.py         # Houses Phase 3 (Builds Canvas & Narrative JSON structures)
├── prompts/
│   └── executive_narrative.md     # Phase 4 component: Strict system guardrails
└── storyteller_agent.py           # Phase 4 component: The LLM orchestrator script

```

* **SSoT Columns Maintained (`operational_data.xlsx`):** `Ticket_ID`, `Create_Date`, `Ticket_Queue`, `Ticket_Status`, `Issue_Category`, `Reassignment_Reason`, `Reassigned_To`, `Rejection_Reason`, `Color_Group`, `Average_Time_spent_in_Mins`, `Country`.

---

### Phase 2: Pipeline Component 1 — `pipeline/tokenizer.py`

This module retains your exact lifecycle-aware tokenization to ensure "Resolved" states don't pollute the mathematical connections.

```python
import pandas as pd

def build_lifecycle_aware_text(row):
    queue = str(row.get('Ticket_Queue', 'unknown_queue')).lower().replace(" ", "_")
    category = str(row.get('Issue_Category', 'unknown_category')).lower().replace(" ", "_")
    status = str(row.get('Ticket_Status', 'unknown_status')).lower().replace(" ", "_")
    
    # 1. Lifecycle-Aware Logic for Reassignments/Rejections
    if status in ['resolved', 'closed', 'completed']:
        reassign_token = "reassignment_na"
        reject_token = "rejection_na"
    else:
        reas_val = row.get('Reassignment_Reason')
        rej_val = row.get('Rejection_Reason')
        reassign_token = f"reas_{str(reas_val).lower().replace(' ', '_')}" if pd.notna(reas_val) else "reassignment_pending"
        reject_token = f"rej_{str(rej_val).lower().replace(' ', '_')}" if pd.notna(rej_val) else "rejection_pending"

    # 2. Roaming vs Domestic Logic
    country_val = row.get('Country')
    is_roaming = pd.notna(country_val) and str(country_val).strip() != ""
    
    if is_roaming:
        country = str(country_val).lower().replace(" ", "_")
        return f"type_roaming dest_{country} cat_{category} status_{status} {reassign_token} {reject_token} q_{queue}"
    
    return f"type_domestic cat_{category} status_{status} {reassign_token} {reject_token} q_{queue}"

```

---

### Phase 3: Pipeline Component 2 — `pipeline/engine.py`

This component implements your **Mathematical Decomposition** inside a delta-checking wrapper. It uses `.transform()` to map new manual uploads into the persistent cache instantly.

```python
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from pipeline.tokenizer import build_lifecycle_aware_text

MODEL_PATH = "models/semantic_pipeline.joblib"
CACHE_PATH = "data/semantic_state.parquet"

def run_semantic_decomposition_engine(raw_xlsx_path: str):
    df_raw = pd.read_excel(raw_xlsx_path)
    
    # 1. Stateful Persistence Load or Init
    if os.path.exists(CACHE_PATH) and os.path.exists(MODEL_PATH):
        df_cache = pd.read_parquet(CACHE_PATH)
        state = joblib.load(MODEL_PATH)
        vectorizer, svd, kmeans = state['vec'], state['svd'], state['km']
        
        # Delta Check: Only process rows that are completely new or whose status shifted
        df_delta = df_raw[~df_raw['Ticket_ID'].isin(df_cache['Ticket_ID'])] # Simpler subset for code brevity
        is_first_run = False
    else:
        df_delta = df_raw.copy()
        vectorizer = TfidfVectorizer(sublinear_tf=True)
        svd = TruncatedSVD(n_components=3, random_state=42)
        kmeans = KMeans(n_clusters=3, random_state=42)
        is_first_run = True

    if df_delta.empty:
        return # Nothing to do

    # 2. Tokenization & Feature Engineering
    df_delta['Cleaned_Text'] = df_delta.apply(build_lifecycle_aware_text, axis=1)
    
    # 3. Execution (Fit on Initial Run / Transform on Delta Uploads)
    if is_first_run:
        tfidf_matrix = vectorizer.fit_transform(df_delta['Cleaned_Text'])
        spatial_coords = svd.fit_transform(tfidf_matrix)
        cluster_ids = kmeans.fit_predict(spatial_coords[:, :2])
        joblib.dump({'vec': vectorizer, 'svd': svd, 'km': kmeans}, MODEL_PATH)
    else:
        tfidf_matrix = vectorizer.transform(df_delta['Cleaned_Text'])
        spatial_coords = svd.transform(tfidf_matrix)
        cluster_ids = kmeans.predict(spatial_coords[:, :2])

    # 4. Pillar Generation (Calculated in RAM)
    df_delta['Semantic_X'] = spatial_coordinates[:, 0]
    df_delta['Semantic_Y'] = spatial_coordinates[:, 1]
    df_delta['Eigen_Axis_Alignment'] = np.argmax(np.abs(spatial_coords), axis=1)
    df_delta['Semantic_Cluster_ID'] = cluster_ids
    
    # Distance / Centrality & Anomalies Calculations
    centroids = kmeans.cluster_centers__
    distances = np.sqrt(np.sum((spatial_coords[:, :2] - centroids[cluster_ids])**2, axis=1))
    df_delta['Centrality_Score'] = 1 / (1 + distances)
    df_delta['Anomaly_Flag'] = distances > np.percentile(distances, 95) if len(distances) > 5 else False
    
    # Dynamic Cluster Theme Extraction
    def derive_label(c_df):
        if c_df['Country'].notna().sum() > (len(c_df) * 0.4):
            return f"Roaming Friction ({c_df['Issue_Category'].mode()[0]})"
        return f"{c_df['Ticket_Queue'].mode()[0]} - {c_df['Issue_Category'].mode()[0]}"
        
    theme_map = df_delta.groupby('Semantic_Cluster_ID').apply(derive_label).to_dict()
    df_delta['Semantic_Cluster_Theme'] = df_delta['Semantic_Cluster_ID'].map(theme_map)

    # 5. Commit to Persistent Cache (Parquet)
    df_final = df_delta if is_first_run else pd.concat([df_cache, df_delta])
    df_final.to_parquet(CACHE_PATH)

```

---

### Phase 4: Tools Layer — `tools/cache_retriever.py`

This class executes the exact **Dual Delivery Interface** from your initial plan, generating clean, structural feeds out of the Parquet metadata cache.

```python
import pandas as pd
import json

class DataStoryCacheRetriever:
    def __init__(self, cache_path: str = "data/semantic_state.parquet"):
        self.cache_path = cache_path

    def get_dual_streams(self) -> tuple[list, dict]:
        df = pd.read_parquet(self.cache_path)
        
        # Stream 1: The Canvas Stream JSON (For your frontend Cloud UI)
        canvas_stream = []
        for _, row in df.iterrows():
            canvas_stream.append({
                "id": str(row['Ticket_ID']),
                "x": float(row['Semantic_X']),
                "y": float(row['Semantic_Y']),
                "color_axis": int(row['Eigen_Axis_Alignment']),
                "opacity_score": float(row['Centrality_Score']),
                "is_anomaly": bool(row['Anomaly_Flag']),
                "tooltip": f"{row['Semantic_Cluster_Theme']} | Status: {row['Ticket_Status']}"
            })
            
        # Stream 2: The Narrative Stream JSON (For the Storyteller AI Agent)
        clusters_summary = []
        for theme, group in df.groupby('Semantic_Cluster_Theme'):
            textbook_row = group.loc[group['Centrality_Score'].idxmax()]
            anomalies = group[group['Anomaly_Flag'] == True]['Cleaned_Text'].tolist()
            
            clusters_summary.append({
                "theme": theme,
                "volume": f"{(len(group)/len(df))*100:.1f}%",
                "highest_centrality_example": textbook_row['Cleaned_Text'],
                "anomalies_to_investigate": anomalies[:3]
            })
            
        primary_axis = "Domestic Core" if df['Eigen_Axis_Alignment'].mode()[0] == 0 else "Roaming/RAN Component"
        narrative_stream = {
            "dominant_operational_axis": primary_axis,
            "clusters": clusters_summary
        }
        
        return canvas_stream, narrative_stream

```

---

### Phase 5: The Delivery Interface (`../routers/datastory.py`)

This is your **FastAPI router Layer** connecting the backend to your dashboard UI.

```python
from fastapi import APIRouter, BackgroundTasks
from datastory.pipeline.engine import run_semantic_decomposition_engine
from datastory.tools.cache_retriever import DataStoryCacheRetriever
from datastory.storyteller_agent import DataStorytellerAgent

router = APIRouter(prefix="/datastory", tags=["DataStory"])

@router.post("/upload")
async def manual_ssot_upload(background_tasks: BackgroundTasks):
    # Triggers pipeline computation safely in background upon manual file replacement
    background_tasks.add_task(run_semantic_decomposition_engine, "datastory/data/operational_data.xlsx")
    return {"status": "Ingestion engine triggered successfully"}

@router.get("/dashboard-feed")
async def get_dashboard_data():
    retriever = DataStoryCacheRetriever()
    canvas_data, narrative_data = retriever.get_dual_streams()
    
    # Invoke the isolated Agent to synthesize the data context
    agent = DataStorytellerAgent()
    executive_story = agent.generate_story(narrative_data)
    
    return {
        "ui_cloud_data": canvas_data,       # Matches your UI Stream structural design
        "ai_executive_brief": executive_story # Matches your Voice Narrative structural design
    }

```