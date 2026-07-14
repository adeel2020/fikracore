# RAG Console: Verification and CLI Cheat Sheet

This guide provides a comprehensive list of commands and methods to test, verify, inspect, and evaluate the Retrieval-Augmented Generation (RAG) pipeline, databases, and services.

---

## 1. Automated Testing (Pytest)

Run these commands from the project root directory to execute the automated test suites validating RAG components.

| Command | Description |
|:---|:---|
| `PYTHONPATH=. uv run pytest tests/test_rag.py` | Validates core RAG ingestion endpoints, vector search functionality, and LLM text generation logic. |
| `PYTHONPATH=. uv run pytest tests/test_retrieval.py` | Verifies routing logic between structured relational retrieval and unstructured document chunk matching. |
| `PYTHONPATH=. uv run pytest tests/test_orchestrate.py` | Tests end-to-end multi-agent orchestration for QnA request routing and response generation. |
| `PYTHONPATH=. uv run pytest tests/test_graph_coherence.py` | Assesses the coherence and integrity of the persistent knowledge graph relationships. |

---

## 2. Vector Database (ChromaDB) Inspection

Use this customized helper script to print vectorized documents, metadata counts, and active table schemas inside ChromaDB.

### Run Inspection Utility:
```bash
PYTHONPATH=. uv run python backend/rag/data/inspect_vector_db.py
```

### Outputs include:
* Active collection names and item counts.
* Categorization count of metadata nodes (Schemas vs. Summaries vs. Chunks).
* Previews of all table schemas currently indexed.

---

## 3. Relational Database (SQLite) Inspection

Excel/CSV files are written directly into SQLite for query aggregation. Use these SQLite commands to verify ingestion results.

### Ingestion Task Logs DB (`tasks.db`)
Inspect the status and error logs of document ingestion tasks:
```bash
# List tables
sqlite3 backend/rag/data/tasks.db ".tables"

# View all ingestion tasks
sqlite3 backend/rag/data/tasks.db "SELECT task_id, status, metadata FROM tasks WHERE task_type = 'INGESTION';"
```

### RAG Relational Data DB (`rag_relational.db`)
Check relational tables and verify row counts of ingested spreadsheets:
```bash
# List all ingested tables (e.g. tbl_operational_data)
sqlite3 backend/rag/data/rag_relational.db ".tables"

# Count rows in a specific table
sqlite3 backend/rag/data/rag_relational.db "SELECT COUNT(*) FROM tbl_operational_data;"

# Preview first 3 rows of a table
sqlite3 backend/rag/data/rag_relational.db "SELECT * FROM tbl_operational_data LIMIT 3;"
```

---

## 4. Automated Evaluation Pipeline

To run evaluations against test query datasets and compute metrics (latency, retrieval overlap, or accuracy):
```bash
PYTHONPATH=. uv run python backend/rag/tests/eval.py
```

---

## 5. API Endpoint Verification (CURL)

### List Ingested Documents
Fetch all ingested files (tasks database merged with ChromaDB schema scan):
```bash
curl -s http://localhost:8000/rag/ingest/list
```

### Submit a QnA Query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the count of resolution reasons in tbl_operational_data?", "chat_history": []}'
```

## List the rag nodes:

```bash
curl -s http://localhost:8000/rag/ingest/list | jq
```
### ouput:
```json
[
  {
    "task_id": "3adc80d4-eb52-4736-9733-38e680302fce",
    "filename": "Complaint_managment_dashboard_new.xlsx",
    "status": "COMPLETED",
    "child_nodes": 5,
    "parent_nodes": 1,
    "timestamp": "2026-06-15T11:55:40.086055"
  },
  {
    "task_id": "sync_tbl_operations_dashboard_data_template",
    "filename": "Operations_Dashboard_Data_Template.xlsx",
    "status": "COMPLETED",
    "child_nodes": 0,
    "parent_nodes": 0,
    "timestamp": "2026-07-08T00:00:00"
  }
]
```