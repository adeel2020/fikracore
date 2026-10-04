# GBrain & Telecom Knowledge Graph (KG) KPI Specification

This document defines the production-grade Key Performance Indicators (KPIs) for the FikraCore **GBrain** (Telecom Knowledge Graph and Cognitive Reasoning Engine), governing digital twin structural integrity, multi-domain causal discovery, zero-trust AI governance, and autonomous closed-loop safety.

---

## Strategic KPI Hierarchy

```
                    ┌────────────────────────────────────────────────────────┐
                    │               GBrain / Knowledge Graph                 │
                    │                   Executive KPIs                       │
                    └────────────────────────────────────────────────────────┘
                                                 │
         ┌───────────────────┬───────────────────┴───────────────────┬───────────────────┐
         ▼                   ▼                                       ▼                   ▼
   ┌───────────┐       ┌───────────┐                           ┌───────────┐       ┌───────────┐
   │  Tier 1   │       │  Tier 2   │                           │  Tier 3   │       │  Tier 4   │
   │ Topology  │       │  Causal   │                           │Governance │       │Autonomous │
   │ & Health  │       │ Reasoning │                           │  & Trust  │       │  Impact   │
   └───────────┘       └───────────┘                           └───────────┘       └───────────┘
```

---

## Tier 1: Graph Topology & Health (Structural Integrity)
*Validates the accuracy, freshness, and structural integrity of the network digital twin.*

| KPI Name | Formula / Metric Definition | Target Threshold | Operational Impact |
| :--- | :--- | :--- | :--- |
| **Ontology Conformance Rate** | `(Compliant Nodes / Total Nodes) × 100` based on 3GPP Rel-18 & TM Forum SID schemas. | **100.0%** | Guarantees all network functions (gNodeB, UPF, AMF, SMF, PE routers) conform strictly to telco standards. |
| **Graph Density & Connectivity** | Clustering coefficient & average degree across active network topology. | Degree $\ge 4.2$<br>Orphan nodes = **0** | Eliminates orphaned or disconnected nodes across the backhaul and core topologies. |
| **Topology Freshness / Sync Latency** | Time $\Delta$ between physical/virtual network state transition and graph sync. | **< 1.5 seconds** | Real-time mirror of physical network state changes (link flaps, pod evictions, route shifts). |
| **Topological Drift Rate** | Count of unmapped or out-of-sync interfaces / entities detected per 24-hour cycle. | **< 0.01%** | Detects unauthorized or unrecorded configuration changes (shadow configurations). |

---

## Tier 2: Causal Reasoning & Discovery (Cognitive Intelligence)
*Measures the depth and speed with which GBrain isolates root causes across domain silos.*

| KPI Name | Formula / Metric Definition | Target Threshold | Operational Impact |
| :--- | :--- | :--- | :--- |
| **Causal Path Discovery Rate** | `% of diagnosed incidents where multi-hop propagation path is reconstructed.` | **$\ge$ 92.0%** | Proves causal chain isolation (e.g. *Fiber link degradation $\to$ PE-Router interface errors $\to$ UPF GTP-U packet loss $\to$ VoNR drop*). |
| **Cross-Domain Correlation Depth** | Average operational domains linked in causal chains (RAN, Transport, Core, Cloud, External). | **$\ge$ 2.4 domains** | Breaks operational monitoring silos; eliminates domain-specific finger-pointing. |
| **Multi-Hop Traversal Efficiency** | Query latency for complex $\ge 4$-hop graph paths under alarm load. | **< 120 ms** | Delivers sub-second incident diagnosis even during massive multi-thousand alarm storms. |
| **Novel Correlation Discovery Rate** | `% of confirmed correlations discovered dynamically without pre-baked static rules.` | **15% – 35%** | Demonstrates cognitive AI discovery of emerging failure modes and architectural blind spots. |

---

## Tier 3: Governance, Trust & Anti-Hallucination (Zero-Trust AI)
*Guarantees mathematical auditability and deterministic grounding before any action is recommended.*

| KPI Name | Formula / Metric Definition | Target Threshold | Operational Impact |
| :--- | :--- | :--- | :--- |
| **Ontology Grounding Score** | `% of LLM inferences and entities strictly grounded in verified KG triples.` | **100.0%** | **Zero-Hallucination Guarantee**: Ensures LLM never references non-existent entities, interfaces, or IP subnets. |
| **Evidence Traceability Index** | Ratio of claims citing verifiable raw telemetry (PCAP, syslog, counters, alarms). | **$\ge$ 95.0%** | 100% audit-ready: every reasoning step cites verifiable raw telemetry telemetry evidence. |
| **Knowledge Gap Coverage** | Active incident parameters lacking ontology mapping or topological paths. | **0 Active Gaps** | Pinpoints unmonitored trunk links, unmodeled third-party transit providers, or telemetry voids. |
| **Contradiction Ratio** | Ratio of contradictory vs. corroborating telemetry signals captured and highlighted. | Audited continuously | Prevents confirmation bias by highlighting conflicting telemetry rather than suppressing it. |

---

## Tier 4: Autonomous Closed-Loop & Business Impact (Executive Value)
*Demonstrates measurable operational efficiency and risk containment for NOC/SOC leadership.*

| KPI Name | Formula / Metric Definition | Target Threshold | Operational Impact |
| :--- | :--- | :--- | :--- |
| **Blast Radius Isolation Margin** | `% containment margin within modeled topological blast fences.` | **$\ge$ 98.0%** | Guarantees proposed corrective actions will not cause side-effects or cascade into adjacent network slices. |
| **Mean Time to Diagnose (MTTD)** | Reduction in diagnosis duration comparing manual troubleshooting to GBrain. | **> 90% reduction**<br>(e.g. 45 min $\to$ **18 sec**) | Drastically shortens major incident lifecycle and prevents customer SLA penalties. |
| **Alarm Storm Compression Ratio** | Raw symptom alarms compressed into a single root-cause causal hypothesis. | **> 85 : 1** | Protects NOC Tier-1 operators from alarm fatigue and notification overload. |
| **HITL Autonomy Gating Compliance** | Strict enforcement of TM Forum Autonomous Network Levels (L1 to L4). | **100.0% enforced** | Mandates Human-in-the-Loop operator sign-off before modifying active traffic routing. |

---

## Zaki Intelligence & Storyteller Chip Mapping

For direct integration into the **Zaki Executive Cockpit** panels:

| Section | Recommended Executive Chip | Nominal Display |
| :--- | :--- | :--- |
| **Knowledge** | `Ontology Grounding` | `100% VERIFIED` |
| **Knowledge** | `Knowledge Support` | `94% VALIDATED` |
| **Knowledge** | `Knowledge GAP` | `0 ACTIVE GAPS` |
| **Correlation** | `Causal Depth` | `3-HOP LINKED` |
| **Correlation** | `Cross-Domain Discovery` | `RAN ↔ TRANS ↔ CORE` |
| **Governance / Trust** | `Evidence Traceability` | `98.4% AUDITED` |
| **Governance / Trust** | `Blast Containment Margin` | `99.2% ISOLATED` |
| **Governance / Trust** | `Autonomy Gate` | `HITL TIER 3 (MOP Sign-off)` |
