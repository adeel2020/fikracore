# DataEngine - Back-Office Agentic Support & Telemetry Dashboard

DataEngine is a high-performance, real-time diagnostic and operational panel designed to guide Telecom Back-Office Support Agents in troubleshooting subscriber complaints. The platform integrates a real-time visual representation of agentic workflow telemetry alongside a multi-layered interactive Telecom Knowledge Graph.

---

## 🚀 Key Features

### 1. Step-by-Step Real-Time Agentic Workflow Dashboard
- Visually tracks crew telemetry steps from `mas_app.py` in real-time.
- Shows dynamic prompt flows, reasoning logs, and action stages of signalling diagnostic crew agents.

### 2. Multi-Layered Interactive Telecom Knowledge Graph
- Centered on user complaints (**Intents**) mapping out affected **Services**, diagnostic **Preconditions**, signal **Errors**, intake **Channels**, and subscriber **Profiles**.
- Guides agents on diagnostic checks and identifies the correct technical engineering **Platform Teams** for ticket routing.
- High-contrast, dynamic HTML5 Canvas rendering of relationship edges and rotated labeling.
- Interactive Zoom In, Zoom Out, and Fit-to-Canvas controls.
- **LLM Subgraph Context Extraction:** Traces 1-hop and 2-hop neighbor subgraphs to compile flat, non-circular JSON telemetry payloads for LLM reasoning models.

---

## 📚 Technical Documentation

A detailed structural overview, physics engine modeling, custom rendering pipelines, and ontological schema properties are documented in the dedicated low-level design folder:

- **Low-Level Design (LLD):** [Telecom Knowledge Graph LLD](file:///Users/adeelarshad/DataEngine/documentation/knowledge_graph_lld.md)
