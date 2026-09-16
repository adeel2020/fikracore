---
name: telecom-knowledge-graph
description: Generates a fresh, production-grade interactive telecom knowledge graph directly from FikraCore simulator runs, causal models, and operational topologies. Produces an interactive HTML topology explorer identical to artifacts/telecom-knowledge-graph.html.
role: Telecom Knowledge Graph Specialist
argument-hint: ["[output-html-path]"]
---

# /telecom-knowledge-graph

Extracts the live operational telecom knowledge graph directly from FikraCore scenario runs (`simulator/runs/` and `simulator/h2_runs/`) and builds a standalone, production-grade interactive visualizer with:
- **11 Domain-Grouped Clusters** (Mobile Core 5G SA, IP Transport, Cloud NFVI, OCS/Charging, 4G EPC, IMS/VoNR, RAN, DWDM/OTN, CRM, OSS, Roaming)
- **Live Causal Relationships & Directional Blast-Radius Propagation**
- **Entity Inspector Drawer** (Incoming upstream drivers & downstream affected nodes)
- **Causal Flow Presets** (H1 SGi MTU Degradation, H2 OCS Charging Discovery, Optical Transport)
- **Dynamic Domain Filters & Live Search**

## Execution Path

The skill executes the local workspace builder script:
`.agents/skills/telecom-knowledge-graph/scripts/build_graph.py`

## Usage & Commands

```bash
# Generate fresh graph at the default location (artifacts/telecom-knowledge-graph.html)
python3 .agents/skills/telecom-knowledge-graph/scripts/build_graph.py

# Or specify a custom output path
python3 .agents/skills/telecom-knowledge-graph/scripts/build_graph.py --output artifacts/my-custom-graph.html
```

## Action Steps for the Agent

When this skill is invoked:
1. Run the Python builder script via `run_command`:
   ```bash
   python3 .agents/skills/telecom-knowledge-graph/scripts/build_graph.py --output artifacts/telecom-knowledge-graph.html
   ```
2. Confirm the extracted entity count, causal link count, and domain count returned in the JSON summary.
3. Provide the user with the file link to open: [telecom-knowledge-graph.html](file:///Users/adeelarshad/kagent/artifacts/telecom-knowledge-graph.html).
