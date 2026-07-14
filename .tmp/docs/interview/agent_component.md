# Backend Component: Agent Component (`backend/agent/`)

This component implements the core autonomous agent logic for analyzing complaints, verifying guardrails, and querying the knowledge graph.

---

## Why (The Problem It Solves)
When operating a complex telecommunications network (NOC), operators are flooded with thousands of daily trouble tickets (complaints). 
- Manually diagnosing these tickets, identifying systemic root causes, and figuring out who/what is responsible takes too much time.
- Standard RAG (Retrieval-Augmented Generation) lacks contextual structure and cannot answer relational queries (e.g., "What are the dependencies between IT and BSCS support queues?").
- Large language models (LLMs) running raw can hallucinate commands, expose sensitive system data, or return unstructured outputs.

The **Agent Component** solves this by establishing a team of specialized, guardrailed agents that cooperatively diagnose complaints, retrieve structured knowledge-graph data, and safety-check outputs.

---

## What (Structure & Layout)
This folder houses the distinct agent roles, vector stores, and utility managers:
* **`primary_agent.py`:** The main orchestrator that intercepts user requests, identifies intent, and delegates tasks to specialized sub-agents.
* **`complaint_analyst.py`:** The core agent responsible for parsing ticket details, tracing logs, and pinpointing issue categories.
* **`data_storyteller_agent.py`:** Agent that generates narrative updates, executive summaries, and slides from raw system logs.
* **`qna_agent.py`:** The question-answering agent that answers system Q&A requests.
* **`kg_retriever.py`:** Utility that queries the local network knowledge graph (AST-based relationships) to resolve cross-file/cross-queue dependencies.
* **`guardrails.py`:** Input/Output validation layer that prevents hallucinations, sanitizes inputs, and checks compliance.
* **`skill_manager.py`:** Dynamic tool loader that equips agents with specific operational tools (e.g., database lookup, SFT triggers).
* **`causal_rules.yaml`:** Predefined domain heuristics and causal rules that guide agent analysis.
* **`vectorstore.json`:** The local semantic index used for fast, local similarity lookups of complaints.

---

## How (Implementation & Flow)

### 1. The Execution Lifecycle
1. **User Prompt Ingestion:** The user sends a query through the web dashboard or CLI.
2. **Input Guardrail Inspection (`guardrails.py`):** The input is screened for injection, safety flags, and system parameters.
3. **Intent Orchestration (`primary_agent.py`):** The primary agent routes the request.
   - If it's a general question, it routes to `qna_agent.py`.
   - If it's a troubleshooting request, it routes to `complaint_analyst.py`.
4. **Relational Context Retrieval (`kg_retriever.py`):** The analyst agent calls the knowledge graph retriever to find structural dependencies (e.g., which microservice impacts which queue).
5. **Causal Reasoning (`causal_rules.yaml`):** The agent matches log profiles against rule patterns to deduce root causes.
6. **Output Guardrail Inspection (`guardrails.py`):** The synthesized response is checked for hallucinations or private info before returning.

### 2. Key Algorithms & Systems
* **Local Semantic Search:** Uses a lightweight JSON-backed vector store (`vectorstore.json`) with cosine similarity to retrieve historically similar complaints.
* **Knowledge Graph BFS/DFS:** Traverses entities and relationships in the AST graph to trace cascading issues between departments.
