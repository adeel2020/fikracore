# Backend Component: Data Storyteller & Semantic Decomposition (`backend/datastory/`)

This component implements the semantic modeling engine (TF-IDF → SVD → KMeans) and the CrewAI data storytelling workflow.

---

## Why (The Problem It Solves)
NOC ticket data contains text logs detailing reassignments, rejections, and resolutions. 
* Individually, these logs are noisy and hard to read.
* Standard keyword searches fail to capture the latent thematic dimensions (e.g., differentiating between eSIM activation issues, VolLTE configuration mismatches, or roaming connectivity failures).
* Executives need a macro-level, statistically sound narrative of *why* complaints occur, rather than digging through raw Excel spreadsheets.

The **Data Storyteller Component** solves this by applying mathematical dimensionality reduction to group complaints into latent semantic topics, and then using a multi-agent writing crew to generate natural language executive stories from those topics.

---

## What (Structure & Layout)
This component is divided into the semantic mathematical pipeline and the writing crew:
* **`pipeline/engine.py`:** The stateful engine that runs the SVD decomposition and K-Means clustering over new and cached ticket rows.
* **`pipeline/tokenizer.py`:** Prepares raw ticket records by extracting key reason columns (`Reassignment_Reason`, `Rejection_Reason`, `Resolution_Reason`) into structured token strings.
* **`crewai_storyteller.py`:** Defines the CrewAI pipeline, specifying the agents (e.g., Data Analyst, Technical Writer) and tasks needed to produce reports.
* **`storyteller_agent.py`:** Integrates the CrewAI outputs into the backend application context.
* **`sync_story.py` & `sync_watcher.py`:** File system monitors that detect changes in the underlying spreadsheet (`operational_data.xlsx`) and automatically trigger SVD rebuilding and story updates.

---

## How (Implementation & Flow)

### 1. The Mathematical Decomposition Flow
1. **Incremental Ingestion (`engine.py`):** The `DataLoader` reads `operational_data.xlsx`. If `semantic_state.parquet` exists, it identifies delta rows to avoid duplicate processing.
2. **Context-Oriented Tokenization (`tokenizer.py`):** Converts reasons into normalized token lists:
   - `reas_roaming_bundle_not_active rejection_na resolution_na`
3. **TF-IDF Vectorization:** The text tokens are transformed into a sparse high-dimensional matrix.
4. **Truncated SVD (Singular Value Decomposition):** Reduces the high-dimensional matrix to 3 dense orthogonal components:
   - **Axis 0:** Domestic Core (Direct Resolution / Rejection)
   - **Axis 1:** Cross-Departmental Escalations (IT / BSCS / SRO)
   - **Axis 2:** International Roaming (Overseas Connectivity)
5. **K-Means Clustering:** Groups the coordinates in the 3D space into 14 distinct semantic clusters.
6. **Multi-Reason Labeling:** Dynamically derives the cluster theme by finding the most common reason across all three reason columns for the tickets in that cluster.

### 2. CrewAI Story Generation Flow
Once the clusters are mapped:
1. **Data Analyst Agent:** Evaluates the SVD clusters and calculates statistics (volume, anomaly percentage, top queues).
2. **Technical Writer Agent:** Synthesizes these raw statistics into a markdown executive brief.
3. **Output:** Saved to `semantic_state.parquet` (for the frontend 3D canvas) and a generated narrative text file.
