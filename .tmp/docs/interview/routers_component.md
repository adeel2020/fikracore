# Backend Component: API Routers & Interfaces (`backend/routers/`)

This component defines the FastAPI endpoints, WebSockets, and routers that connect the frontend dashboard and user interface to the backend engines.

---

## Why (The Problem It Solves)
A high-performance Operations Dashboard requires real-time data feeds, file processing, and interactive LLM chat services.
* Direct coupling of backend logic (like model training or SVD execution) to the UI blocks threads and leads to timeout errors.
* We need structured endpoints that handle requests asynchronously, manage background worker processes, and format payloads cleanly for React state managers.
* Features like live complaint updates require lightweight, fast messaging interfaces (like WebSockets or Server-Sent Events).

The **API Routers Component** solves this by establishing structured FastAPI modules that organize endpoints by functional area, handle async background tasks, and standardize JSON/WebSocket interfaces.

---

## What (Structure & Layout)
This folder houses FastAPI router controllers mapping to core frontend modules:
* **`api_router.py`:** The primary router assembly that imports and mounts all sub-routers under standard prefixes.
* **`datastory.py`:** Endpoints for running/retrieving the SVD semantic decomposition clusters, cluster summaries, and data storytelling briefs.
* **`sft.py`:** Endpoints that trigger local model fine-tuning runs, report training progress logs, and trigger LoRA adapter merges.
* **`realtime_protocol.py`:** Manages real-time log ingestion and WebSocket connections for the live operational map.
* **`history.py`:** Manages analytical histories, past queries, and audit trails.
* **`storyteller_chat.py`:** Manages context-aware Q&A chat sessions with the storyteller agent.
* **`tts.py`:** Text-to-Speech endpoints that synthesize audio responses for executive briefs.

---

## How (Implementation & Flow)

### 1. Unified SVD & Narrative Pipeline Endpoint (`datastory.py`)
1. **Request:** The frontend requests `/datastory/feed`.
2. **Process:** 
   - Reads `semantic_state.parquet` to load coordinate lists.
   - Formats `ui_cloud_data` containing coordinates ($x, y, z$), centrality, anomaly flags, and reason categories.
   - Extracts eigenvalues and cluster themes.
3. **Response:** Returns a consolidated JSON payload mapped directly to the frontend's 3D SVG canvas and cluster cards.

### 2. Async SFT Trigger Pipeline (`sft.py`)
1. **Trigger:** User clicks "Start Fine-Tuning" on the UI, calling `/sft/train` (POST).
2. **Process:** Spawns `train_corda.py` as an asynchronous background subprocess.
3. **Tracking:** Exposes `/sft/logs` (GET) to read `corda.log` and return real-time standard output and training metrics to the UI progress bar.
