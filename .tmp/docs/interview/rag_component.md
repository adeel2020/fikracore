# Backend Component: Retrieval-Augmented Generation (`backend/rag/`)

This component manages data ingestion, embeddings generation, vector storage, and query pipelines to provide domain-specific context to the agents.

---

## Why (The Problem It Solves)
General-purpose LLMs do not know about internal network topologies, ticket escalation guidelines, or historical vendor logs. 
* Fine-tuning a model on these documents is computationally expensive and slow to update.
* Raw keyword search is too simple and misses semantic matches (e.g., searching for "APN configuration" should retrieve articles talking about "packet core profile mismatch").
* Retaining high accuracy during document retrieval requires a structured database, clean text chunking, and localized vector lookups.

The **RAG Component** solves this by maintaining a localized vector database of operational manuals, wikis, and historical logs, and providing a retrieval pipeline that injects relevant context directly into the agent prompts.

---

## What (Structure & Layout)
This component is organized into modular layers:
* **`database.py`:** Configures connection pools, schemas, and sessions for the underlying database storing raw documents.
* **`config.py`:** Configures vector indices, chunking sizes (e.g. 512 tokens), and similarity thresholds.
* **`pipelines/`:** Contains execution scripts to chunk, parse, embed, and upload source documents into the vector store.
* **`routers/`:** FastAPI endpoints that expose RAG lookup services (e.g. `/rag/search`) for external clients and sub-agents.
* **`services/`:** Business logic handling embedding model loading (e.g. SentenceTransformers) and query expansion.

---

## How (Implementation & Flow)

### 1. Ingestion & Embedding Pipeline
1. **Document Loading:** Reads raw text files, PDFs (manuals), and JSON logs.
2. **Text Chunking:** Splits documents into overlapping segments (e.g., chunk size 500 characters, overlap 50 characters) to preserve contextual boundaries.
3. **Embeddings Computation:** Runs the chunks through a local embedding model (e.g. `ms-marco-MiniLM-L-6-v2`) to produce 384-dimensional dense vectors.
4. **Index Insertion:** Persists the vectors and metadata in the vector database.

### 2. Retrieval Flow
1. **Query Embeddings:** When an agent queries the RAG pipeline, the user's natural language question is encoded using the same embedding model.
2. **Similarity Search:** Executes a Cosine Similarity search over the vector index.
3. **Reranking:** Orders matching chunks by proximity score.
4. **Context Injection:** Returns the top $K$ chunks (with metadata like source filename and line numbers) to the calling agent to be appended to the LLM system prompt.
