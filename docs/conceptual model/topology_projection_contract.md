# Topology Projection Contract & Knowledge Graph Visualization Architecture

> **Status:** Specification & Architecture Note  
> **Source Context:** Integration between FikraCore Simulator Runs, `TopologyProjectionContract`, and [`artifacts/telecom-knowledge-graph.html`](file:///Users/adeelarshad/FikraCore/artifacts/telecom-knowledge-graph.html)  
> **Date:** October 2, 2026  

---

## 1. Executive Summary

Currently, FikraCore projects simulated incidents onto the 12-domain telecom knowledge graph explorer ([`artifacts/telecom-knowledge-graph.html`](file:///Users/adeelarshad/FikraCore/artifacts/telecom-knowledge-graph.html)) via [`.agents/skills/telecom-knowledge-graph/scripts/build_graph.py`](file:///Users/adeelarshad/FikraCore/.agents/skills/telecom-knowledge-graph/scripts/build_graph.py).

This document captures:
1. **The Current State**: How simulation runs (such as [`story_context.json`](file:///Users/adeelarshad/FikraCore/services/agents/src/engine_stack/engines/telecom_brain/simulator/runs/RUN-SCN-001-L1-SEED-42001/operational/story_context.json) and `execution_trace_latest.json`) currently project onto the graph.
2. **The Architectural Gap**: Why file-level reverse-engineering by the visualization script creates tight coupling and schema fragility.
3. **The Target State**: How `TopologyProjectionContract` serves as the typed contract boundary between the backend reasoning engine (Correlation/Zaki) and any visualization client (the standalone HTML explorer, WebGL canvases, or live NOC dashboards).

---

## 2. Current State vs. Target State

### Current State (Ad-hoc Disk Ingestion)
```
  ┌─────────────────────────────────────────────────────────────┐
  │  Simulator Run Directory (RUN-SCN-001-...)                  │
  │  ├── operational/story_context.json                         │
  │  ├── operational/alarms.jsonl                               │
  │  ├── hidden/ground_truth.yaml                               │
  │  └── execution_trace_latest.json                            │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼ (Forensic disk parsing, loose string matching)
  ┌─────────────────────────────────────────────────────────────┐
  │  build_graph.py                                             │
  │  • Scans directories, reads YAML & JSON directly            │
  │  • Manually computes node severity & propagation paths      │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
         artifacts/telecom-knowledge-graph.html
```

*Limitations of the current approach:*
- **Coupling to Disk Structure**: Any change in simulator folder naming, field nesting, or trace JSON breaks the visualization generator.
- **Leaked Boundaries**: The visualization script reads `hidden/ground_truth.yaml`, violating the Truth-Blind boundary principle for live runtime projections.
- **Inability to Stream Live Updates**: In-flight reasoning from the Correlation Engine cannot be projected dynamically to a web frontend without serializing intermediate files to disk first.

---

### Target State (Contract-Driven Projection)
```
  ┌─────────────────────────────────────────────────────────────┐
  │  FikraCore Correlation Engine / Zaki Cognitive Actor        │
  │  • Stage 2.1: Temporal Normalization                        │
  │  • Stage 2.2: Topological Inversion                         │
  │  • Stage 2.3: 10-Pathway Analytical Spine                   │
  │  • Stage 2.4: Blast Radius Assessment                       │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼ emits pure typed contract
  ┌─────────────────────────────────────────────────────────────┐
  │  TopologyProjectionContract (Pydantic BaseModel)            │
  │  • incident_id, run_id, scenario_id                         │
  │  • node_heat_levels: Dict[str, NodeHeatState]               │
  │  • causal_propagation_chain: List[str]                      │
  │  • active_reroute_links: List[Tuple[str, str]]              │
  │  • viewport_focus: Domain, Camera Center, Zoom Level        │
  └──────────────┬──────────────────────────────┬───────────────┘
                 │                              │
                 ▼                              ▼
  ┌─────────────────────────────┐  ┌────────────────────────────┐
  │ build_graph.py              │  │ Live NOC WebGL / React UI  │
  │ Ingests contract JSON       │  │ Consumes WebSocket stream  │
  │ to generate static artifact │  │ for real-time heatmap rendering│
  └──────────────┬──────────────┘  └────────────────────────────┘
                 │
                 ▼
     artifacts/telecom-knowledge-graph.html
```

---

## 3. Specification: `TopologyProjectionContract`

Located at: `services/agents/src/zaki/contracts/topology_projection.py`

### Enum Definitions
```python
from enum import Enum
from typing import Dict, List, Optional, Tuple
from pydantic import Field
from .base import BaseContract

class NodeHeatState(str, Enum):
    """Visual degradation and causal state for network nodes."""
    FAULT_ORIGIN = "FAULT_ORIGIN"        # Pulsing red halo (Root cause)
    IMPACTED = "IMPACTED"                # Solid amber/red (Degraded service)
    AT_RISK_SHADOW = "AT_RISK_SHADOW"    # Orange ring (In blast radius, not failed yet)
    HEALTHY_BYPASS = "HEALTHY_BYPASS"    # Cyan/green (Taking rerouted traffic)
    ISOLATED = "ISOLATED"                # Gray dashed (Administratively quarantined)
    NOMINAL = "NOMINAL"                  # Standard baseline display

class LinkTrafficState(str, Enum):
    """Dynamic link state for animated particle flows."""
    SATURATED = "SATURATED"              # High packet discards / congestion
    DEGRADED = "DEGRADED"                # High latency or packet drop
    CONGESTION_REROUTE = "CONGESTION_REROUTE" # Carrying diverted detour load
    SEVERED = "SEVERED"                  # Link down / admin down
    NOMINAL = "NOMINAL"                  # Normal operating capacity
```

### Main Contract Definition
```python
class TopologyProjectionContract(BaseContract):
    """
    Standardizes operational incident projection over the telecom knowledge graph.
    Binds analytical RCA inference directly to visual layout engines without
    requiring consumers to inspect disk logs or raw simulation state.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API version")
    kind: str = Field(default="TopologyProjectionContract", description="Contract kind identifier")
    
    projection_id: str = Field(description="Unique projection identifier (e.g. PROJ-SCN-001)")
    incident_id: str = Field(description="Associated incident ticket reference")
    run_id: str = Field(description="Simulator or live execution run reference")
    scenario_id: Optional[str] = Field(default=None, description="Scenario identifier if in simulation mode")
    
    # ── Root Cause & Propagation Flow ──
    root_cause_slug: Optional[str] = Field(
        default=None,
        description="Canonical slug of the identified root failure element (e.g. 'IP:PE:RTR-21')"
    )
    causal_propagation_chain: List[str] = Field(
        default_factory=list,
        description="Ordered sequence of entity slugs showing how failure propagated across domains"
    )
    
    # ── Node-Level Visual Overlays ──
    node_heat_levels: Dict[str, NodeHeatState] = Field(
        default_factory=dict,
        description="Mapping of entity slugs to their rendered visual heat states"
    )
    node_status_tooltips: Dict[str, str] = Field(
        default_factory=dict,
        description="Operator-facing tooltips explaining the state of each affected node"
    )
    
    # ── Link-Level Visual Overlays ──
    link_states: Dict[str, LinkTrafficState] = Field(
        default_factory=dict,
        description="Mapping of link IDs (e.g. 'IP:PE:RTR-21->IP:VRF:N3-01') to traffic states"
    )
    active_reroute_links: List[Tuple[str, str]] = Field(
        default_factory=list,
        description="Pairs of (source_slug, target_slug) carrying failover detour traffic"
    )
    
    # ── Viewport & Spatial Guidance ──
    focused_domain: Optional[str] = Field(
        default=None,
        description="Primary telecom operational domain to zoom/focus (e.g. 'IP Transport & Routing')"
    )
    camera_center_node: Optional[str] = Field(
        default=None,
        description="Primary entity slug to place at center of viewport"
    )
    recommended_zoom: float = Field(
        default=1.2,
        description="Zoom multiplier for UI camera focusing"
    )
```

---

## 4. Integration with `build_graph.py` and `artifacts/`

### How `build_graph.py` Consumes the Contract
Instead of parsing `story_context.json` or searching for `ground_truth.yaml`, `build_graph.py` can accept the contract directly:

```python
# build_graph.py refactored intake:
def apply_topology_projection(scenario_dict: dict, projection: TopologyProjectionContract):
    scenario_dict["root_cause"] = projection.root_cause_slug
    scenario_dict["propagation_path"] = projection.causal_propagation_chain
    scenario_dict["affected_nodes"] = {
        slug: {
            "severity": heat_state.value,
            "status": projection.node_status_tooltips.get(slug, heat_state.value)
        }
        for slug, heat_state in projection.node_heat_levels.items()
    }
    scenario_dict["active_reroutes"] = projection.active_reroute_links
    scenario_dict["camera"] = {
        "center": projection.camera_center_node,
        "zoom": projection.recommended_zoom,
        "domain": projection.focused_domain
    }
```

### Benefits
1. **Decoupled Architecture**: Visualization is purely a consumer of typed contracts. It doesn't care whether data came from a simulation, live telemetry, or a digital twin.
2. **Truth-Blind Boundary Compliance**: Projections can only reflect what the Correlation Engine actually discovered and placed in the contract, preventing inadvertent simulator ground-truth leaks.
3. **Multi-Platform Support**: The same `TopologyProjectionContract` JSON payload can drive:
   - The static HTML graph generator (`build_graph.py`).
   - A real-time D3 / Three.js / WebGL web console.
   - Mobile and executive incident summary cards.
