# Revised Implementation Plan: Explainable Causal AI CLI Showcase (`fikracore demo`)

An interactive, step-by-step executive demonstration framework built directly into the FikraCore CLI ([`cli.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py)), powered by a clean presentation adapter ([`demo_presenter.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/demo_presenter.py)) and driven by the real simulation and reasoning engines (`Investigator`, `PromotionEngine`, `WhatIfAnalyzer`).

---

## 1. Executive Vision & Core Value Proposition

Conventional AIOps tools rely on timestamps and alarm severities. In real telecommunications networks where **hundreds of alarms arrive at the exact same second ($t_0$)**, those tools fail because they blame the loudest symptom.

**FikraCore is True Explainable Causal AI**:
- It does **not** rely on time precedence alone.
- It uses **structural graph invariants**: downstream reachability cones, cross-domain telemetry independence, counterfactual negative evidence (healthy checks), and structural leaf-sink penalization.
- It shows **why** a root cause was chosen and **why alternative hypotheses were mathematically disproven**.

---

## 2. Architecture & Modular Scaffolding

To keep `cli.py` clean, modular, and maintainable, the presentation logic is decoupled from user input handling:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        User Input (Terminal CLI)                       │
│                   ./fikracore demo (or --live)                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    investigation/cli.py (Interactive Loop)             │
│  • Keyboard navigation: [Enter] Step, [c] Chronology, [b] Blast, [q]   │
│  • Interactive HITL prompt: [Y/n] for Knowledge Promotion              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               investigation/demo_presenter.py (Causal Views)           │
│  • Disentanglement Matrix (Simultaneous Alarm Classification)          │
│  • Competing Hypotheses & 12-Factor Scoring Breakdown                  │
│  • Counterfactual Falsification (Why other hypotheses were ruled out)  │
│  • Layered Hop-by-Hop Propagation Conduit                              │
│  • Executive Scorecards (MTTR, Coverage, Blast Radius Reduction)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Underlying Simulation Backend (SSOT)                │
│    Investigator.run() · PromotionEngine · WhatIfAnalyzer               │
│    (100% UNTOUCHED — NO CODE, DATA, OR MODEL CHANGES)                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The 3 Interactive Use Cases & Stage-by-Stage Inner Workings

### Use Case 1: Cross-Domain Service Outage & Simultaneous Alarm Disentanglement (H1: Understand)
* **Target Scenario**: `RUN-SCN-001-L1-SEED-42001`
* **Domains**: Transport (IP/MPLS) ➜ 5G Core (SA) ➜ RAN ➜ CRM (Customer Tickets)
* **Guided Stages**:
  1. **Stage 1: Simultaneous Alarm Ingestion & Disentanglement Matrix**:
     - Explains to management how simultaneous alarms at $t_0$ are classified into topological roles:
       ```text
       ┌── 🔬 COGNITIVE DISENTANGLEMENT MATRIX (Simultaneous Evidence at t0) ────────┐
       │ Entity (Human Name)          │ Domain       │ Signal / Alarm     │ Structural Role    │ Downstream Reach │
       ├──────────────────────────────┼──────────────┼────────────────────┼────────────────────┼──────────────────┤
       │ IP:PE:RTR-21 (Edge Router)   │ IP_TRANSPORT │ SGi Discard Spike  │ Upstream Driver    │ 100% (3 nodes)   │
       │ IP:VRF:N3-01 (Transport VRF) │ IP_TRANSPORT │ N3 Throughput Drop │ Transit Conduit    │  66% (2 nodes)   │
       │ SA5G:UPF:003 (5G Core UPF)   │ SA_5G_CORE   │ Session Drop Storm │ Affected Function  │  33% (1 node)    │
       │ CRM:TICKET:001 (Trouble Tkt) │ CRM          │ SLA Breach Ticket  │ Terminal Leaf Sink │   0% (0 nodes)   │
       └──────────────────────────────┴──────────────┴────────────────────┴────────────────────┴──────────────────┘
       ```
  2. **Stage 2: Cross-Domain Correlation Convergence**:
     - Converges multi-domain signals into correlation cluster `cluster-54db6ef3`.
     - Validates multi-source telemetry independence across IP NMS, Core EMS, and CRM.
  3. **Stage 3: Competing Hypothesis Evaluation & Falsification Breakdown**:
     - Explains *why* Transport won and *why* Core and CRM were disproven:
       ```text
       ┌── ⚖️ EXPLAINABLE REASONING: COMPETING HYPOTHESIS FALSIFICATION ─────────────────────┐
       │                                                                                     │
       │  [Hypothesis H2: 5G Core UPF Software Fault]                                        │
       │  • Downstream Coverage: 33% (Cannot explain Transport VRF or PE Router alarms).    │
       │  • Counterfactual Check: Core AMF & SMF report 100% healthy control-plane state.   │
       │  • Verdict: ❌ DEMOTED (Symptom of upstream starvation, not the root cause).         │
       │                                                                                     │
       │  [Hypothesis H1: Transport Edge Router IP:PE:RTR-21]                                │
       │  • Downstream Coverage: 100% (Traverses VRF ──▶ UPF ──▶ Enterprise Customer Sink).  │
       │  • Score: 0.9400 (Max reachability + multi-source confirmation).                    │
       │  • Verdict:  CONFIRMED ROOT CAUSE (Explains all observed anomalies).              │
       │                                                                                     │
       │  [Hypothesis H3: Customer CRM Ticket]                                               │
       │  • Structural Role: Terminal Evidence Sink (Leaf node).                             │
       │  • Verdict: ❌ REJECTED (Customer tickets report pain; they cannot cause it).        │
       │                                                                                     │
       └─────────────────────────────────────────────────────────────────────────────────────┘
       ```
  4. **Stage 4: Causal Propagation Conduit & Blast Radius**:
     - Visualizes the physical-to-logical-to-service chain:
       `IP:PE:RTR-21` ──[routes-through]──▶ `IP:VRF:N3-01` ──[depends-on]──▶ `SA5G:UPF:003` ──▶ `CRM:TICKET:001`.
  5. **Stage 5: Playbook Dispatch & Executive Scorecard**:
     - Automated transport traffic reroute executed.
     - Confirms MTTR reduction from 45 minutes to 2 minutes with 100% explanation coverage.

---

### Use Case 2: Prepaid Charging Failure & Knowledge Promotion (H2 ➜ H3: Discover & Learn)
* **Target Scenarios**: `RUN-H2-SCN-001-K1-SEED-52002` (Discovery) ➜ `H3-LU-001` (Learning & Verification)
* **Domains**: 5G Core, Transport, Online Charging System (OCS), CRM
* **Guided Stages**:
  1. **Stage 1: Silent Quota Failures & Customer Complaints**:
     - Subscribers experience session terminations, but Core AMF/SMF report healthy.
  2. **Stage 2: Epistemic Incompleteness Alert (`MODEL_INSUFFICIENT`)**:
     - Causal engine flags model deficiency: residual observations cannot be mapped to the current topology.
  3. **Stage 3: Operational Gap Discovery**:
     - Engine identifies the unmodeled boundary edge:
       `SA5G:UPF:003` ──[routes-through]──▶ `IP:PE:RTR-21` (Confidence: 0.85, Evidence: `EV-H2-H2-SCN-001-001`).
  4. **Stage 4: Interactive Human-in-the-Loop (HITL) Validation Prompt**:
     - The CLI pauses and prompts the user:
       ```text
       ─────────────────────────────────────────────────────────────────────────────
       ? [SME HUMAN-IN-THE-LOOP VALIDATION]
         FikraCore discovered missing causal topology edge:
         SA5G:UPF:003 (5G Core UPF) ──[routes-through]──▶ IP:PE:RTR-21 (Transport PE Router)

         Do you approve promoting this edge into the active knowledge graph? [Y/n]: 
       ─────────────────────────────────────────────────────────────────────────────
       ```
  5. **Stage 5: Governed Knowledge Promotion (8 Production Guardrails)**:
     - `PromotionEngine` verifies guardrails (cycle checks, schema validation, SME signature) and issues a rollback journal ID.
  6. **Stage 6: Zero-Residual Re-test on Future Incident (`H3-FUT-001`)**:
     - Re-evaluates future incident with the updated in-memory graph.
     - Engine dynamically proves:
       - Confidence jumps from **0% ➜ 100%**.
       - State shifts from **`MODEL_INSUFFICIENT` ➜ `EXPLAINED`**.
       - Unexplained residuals drop from **1 ➜ 0**.

---

### Use Case 3: Proactive Network Resilience What-If (H4: Predict & Resile)
* **Target Scenario**: `H4-WI-001` (`MPLS Edge Router Failure`)
* **Domains**: Transport, 5G Core, RAN, Enterprise Mobile Services
* **Guided Stages**:
  1. **Stage 1: Simulated Trigger Event**:
     - Simulates total outage on `IP:PE:RTR-07` (MPLS Edge Router-07).
  2. **Stage 2: Forward Topology & Cascade Propagation Paths**:
     - `WhatIfAnalyzer` traces forward propagation downstream into dependent core user-plane gateways and macro cells.
  3. **Stage 3: Single Point of Failure (SPOF) Analysis**:
     - Identifies missing dual-homed redundancy uplink (Criticality Score: 1.0, Risk Type: `SPOF`).
  4. **Stage 4: Quantified Blast Radius**:
     - 28,500 active subscribers affected; 100% loss of N3 mobile backhaul.
  5. **Stage 5: Proactive Mitigation Plan Comparison**:
     - Evaluates competing mitigations:
       - **Mitigation A (Recommended)**: Pre-provision failover detour via secondary PE router (88% blast radius reduction, Low complexity).
       - **Mitigation B**: Core admission throttling (35% blast radius reduction, Medium disruption).

---

## 4. Technical Implementation Details

### File Additions and Modifications

1. **[NEW] [`services/agents/src/engine_stack/engines/telecom_brain/investigation/demo_presenter.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/demo_presenter.py)**:
   - Contains high-clarity ANSI renderers:
     - `render_disentanglement_matrix(evidence_list, graph)`
     - `render_falsification_scorecard(hypotheses)`
     - `render_propagation_conduit(causal_chain)`
     - `render_spof_resilience_matrix(whatif_result)`
     - `render_executive_scorecard(metrics)`
   - Uses `default_naming_resolver` to resolve all network functions into colored, human-readable names.

2. **[MODIFY] [`services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py)**:
   - Keeps the CLI interactive loop lightweight and modular.
   - Registers `--live` argument on `fikracore demo`.
   - Dispatches to `demo_presenter.py` and existing backend engines (`Investigator`, `PromotionEngine`, `WhatIfAnalyzer`).

---

## 5. Verification Plan

### Automated Verification
Run these commands from the repository root (use the `PYTHONPATH` invocation for local development):
```bash
# 1. CLI help verification
PYTHONPATH=services/agents/src python3 -m engine_stack.engines.telecom_brain.investigation.cli demo --help

# 2. Automated dry-run of all 3 use cases in live engine mode
PYTHONPATH=services/agents/src python3 -m engine_stack.engines.telecom_brain.investigation.cli demo 1 --live --auto --delay 0
PYTHONPATH=services/agents/src python3 -m engine_stack.engines.telecom_brain.investigation.cli demo 2 --live --auto --delay 0
PYTHONPATH=services/agents/src python3 -m engine_stack.engines.telecom_brain.investigation.cli demo 3 --live --auto --delay 0
```

Notes:
- The `--live` flag attempts to run the `Investigator` live against the simulator/provider and will safely fall back to the canned interactive demo if the provider or scenario is unavailable.
- The `--snapshot <path>` flag runs using a frozen JSON snapshot as a deterministic knowledge provider.
- The automated dry-runs above were executed locally and completed successfully; the presenter rendered outputs for each use case.

### Manual Interactive Verification
Use the interactive demo to exercise HITL flows and playbook prompts:
```bash
PYTHONPATH=services/agents/src python3 -m engine_stack.engines.telecom_brain.investigation.cli demo --live
```
- Select Use Case 1: verify Disentanglement Matrix, Falsification Scorecard, and test `[c]` (chronology) and `[b]` (blast radius).
- Select Use Case 2: verify HITL prompt (`Y/n`), approve promotion, and observe dynamic confidence jump to 100%.
- Select Use Case 3: verify SPOF detection and proactive mitigation comparison table.
