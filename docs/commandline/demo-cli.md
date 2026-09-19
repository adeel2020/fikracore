# Revised Implementation Plan: Interactive CLI Showcase Demo (`fikracore demo`)

An interactive, step-by-step executive demonstration framework built directly into the FikraCore CLI ([`cli.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py)) and executable via `./fikracore demo`.

---

## 1. Executive Overview & Objectives

The goal is to provide a curated, interactive CLI walkthrough of the 3 primary autonomous telecom scenarios without re-implementing simulation logic:
1. **Use Case 1 (H1: Understand)**: Cross-Domain Service Outage (`RUN-SCN-001-L1-SEED-42001`).
2. **Use Case 2 (H2 ➜ H3: Discover & Learn)**: Unmodeled Charging Failure & Knowledge Promotion (`RUN-H2-SCN-001-K1-SEED-52002` ➜ `H3-LU-001`).
3. **Use Case 3 (H4: Predict & Resile)**: Proactive Network Resilience & Blast Radius (`H4-WI-001`).

### Key Highlights
- **Human-readable Node Names**: All technical network function identifiers include clear human-readable names in parentheses (e.g., `IP:PE:RTR-21 (SGi IP Edge Gateway Router)`).
- **Executive Color Coding**: Cyan/magenta/pink ANSI styling to clearly distinguish network functions, alarms, upstream causal drivers, downstream blast radius, and tickets.
- **Interactive Step-by-Step Flow**: Progresses stage-by-stage with keyboard controls (`[Enter]` next, `[c]` view event chronology, `[b]` blast radius details, `[q]` back).
- **Interactive Knowledge Validation (HITL)**: Prompts the executive/SME to approve candidate relationship promotion (`Y/n`), updating active reasoning memory and projecting onto the Telecom Knowledge Graph.
- **Scorecards & Concluding Metrics**: Concludes each scenario with an executive scorecard showing MTTR reduction, blast radius containment, and operational impact.

---

## 2. Interactive Scenarios & Stage Architecture

```
                               ┌──────────────────────────────────────────────┐
                               │   fikracore demo (Interactive CLI Menu)      │
                               └──────────────────────┬───────────────────────┘
                                                      │
         ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
         ▼                                            ▼                                            ▼
┌───────────────────────────────┐   ┌──────────────────────────────────────────┐   ┌───────────────────────────────┐
│ USE CASE 1: CROSS-DOMAIN      │   │ USE CASE 2: KNOWLEDGE GAP & LEARNING     │   │ USE CASE 3: PROACTIVE WHAT-IF │
│ SERVICE OUTAGE (H1)           │   │ PREPAID CHARGING (H2 ➜ H3)               │   │ NETWORK RESILIENCE (H4)       │
├───────────────────────────────┤   ├──────────────────────────────────────────┤   ├───────────────────────────────┤
│ • Transport PE Discard ➜      │   │ • Unmodeled OCS Boundary Discovery (H2)  │   │ • Aggregation Switch Failure  │
│   Mobile Core ➜ RAN Cascade   │   │ • HITL Human Validation Prompt           │   │ • Forward Cascade Propagation │
│ • Competing Hypotheses        │   │ • Governed gbrain Knowledge Promotion    │   │ • SPOF & Downstream Blast Rad │
│ • Blast Radius & Playbook     │   │ • Zero-Residual Re-test Verification(H3) │   │ • Mitigation Plan Comparison  │
└───────────────────────────────┘   └──────────────────────────────────────────┘   └───────────────────────────────┘
```

---

### Use Case 1: Cross-Domain Service Outage (H1: Understand)
- **Target Scenario**: `RUN-SCN-001-L1-SEED-42001`
- **Domains Covered**: Transport (IP/MPLS), 5G Core (SA), RAN, CRM (Trouble Tickets)
- **Guided Stages**:
  - **Stage 1: Multi-Domain Alarm Ingestion & Chronology**: Shows alarms firing on `IP:PE:RTR-21`, `IP:VRF:N3-01`, `SA5G:UPF:003`, and `CRM:TICKET:001`. Optional `[c]` shows time-ordered sequence.
  - **Stage 2: Cross-Domain Correlation**: Aggregates disparate telemetry into correlation cluster `cluster-54db6ef3`.
  - **Stage 3: Competing Hypothesis Competition**: Evaluates $H_1$ (Transport Degradation, score: 0.94) vs $H_2$ (UPF Software Degraded, score: 0.21) vs $H_3$ (Customer CRM Ticket, rejected as symptom).
  - **Stage 4: Causal Driver vs Blast Radius**:
    - **Upstream Causal Driver**: `IP:PE:RTR-21` (Transport Edge Router)
    - **Downstream Blast Radius**: `IP:VRF:N3-01` (Core Transport VRF), `SA5G:UPF:003` (5G User Plane Function), `CRM:TICKET:001` (Terminal Customer Evidence).
  - **Stage 5: Playbook Dispatch & Resolution**: Triggers automated mitigation playbook, verifying MTTR reduction from 45 mins to 2 mins.

---

### Use Case 2: Prepaid Charging Failure & Knowledge Promotion (H2 ➜ H3)
- **Target Scenarios**: `RUN-H2-SCN-001-K1-SEED-52002` (Discovery) and `H3-LU-001` (Learning & Verification)
- **Domains Covered**: 5G Core, Transport, Online Charging System (OCS), CRM
- **Guided Stages**:
  - **Stage 1: Silent Degradation & Customer Complaint**: Customer trouble ticket filed (`CRM:TICKET:001`), core alarms show normal status on AMF, but sessions drop.
  - **Stage 2: Epistemic Incompleteness Alert**: Causal engine recognizes residual unexplained observations; marks state `MODEL_INSUFFICIENT`.
  - **Stage 3: Operational Gap Discovery**: Engine identifies unmodeled boundary edge: `SA5G:UPF:003` ──[routes-through]──▶ `IP:PE:RTR-21`.
  - **Stage 4: Interactive Human-in-the-Loop (HITL) Validation**:
    ```text
    ─────────────────────────────────────────────────────────────────────────────
    ? [SME HUMAN-IN-THE-LOOP VALIDATION]
      FikraCore discovered missing causal topology edge:
      SA5G:UPF:003 (5G Core UPF) ──[routes-through]──▶ IP:PE:RTR-21 (Transport PE Router)

      Do you approve promoting this edge into the active knowledge graph? [Y/n]:
    ─────────────────────────────────────────────────────────────────────────────
    ```
  - **Stage 5: Governed Knowledge Promotion**: `PromotionEngine` executes 8 production safety checks and commits candidate edge into active memory.
  - **Stage 6: Re-test on Future Incident (`H3-FUT-001`)**: Future incident evaluated with updated graph; confidence jumps to 1.00 with zero residual error.
  - **Stage 7: Knowledge Graph Projection**: Shows instructions to view the projected incident in `artifacts/telecom-knowledge-graph.html`.

---

### Use Case 3: Network Resilience What-If (H4: Predict & Resile)
- **Target Scenario**: `H4-WI-001` (`MPLS Edge Router Failure`)
- **Domains Covered**: Transport, 5G Core, RAN, Enterprise Mobile Services
- **Guided Stages**:
  - **Stage 1: Simulated Trigger Event**: Simulates catastrophic failure of `IP:PE:RTR-07` (MPLS Edge Router-07).
  - **Stage 2: Forward Topology & Cascade Propagation**: Traverses downstream paths to dependent user plane gateways and RAN macro cells.
  - **Stage 3: Single Point of Failure (SPOF) Detection**: Identifies that `IP:PE:RTR-07` lacks redundant secondary routing uplink.
  - **Stage 4: Quantified Blast Radius**: 28,500 subscribers impacted; 100% loss of N3 mobile backhaul; estimated revenue risk calculated.
  - **Stage 5: Proactive Mitigation Comparison**:
    - **Option A (Recommended)**: Pre-provision failover detour via secondary PE router (reduces blast radius by 88%).
    - **Option B**: Core rate-limiting and admission throttling (reduces blast radius by 35%).

---

## 3. Technical Architecture & File Changes

### Primary Code Modifications
All functionality will be cleanly added to:
- [`services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py)

#### Modules to Add:
1. **`ENTITY_DISPLAY_REGISTRY` & `format_entity(slug)`**:
   - Technical slug to human name mapping:
     - `IP:PE:RTR-21` ➜ `IP:PE:RTR-21 (SGi IP Edge Gateway Router)`
     - `IP:VRF:N3-01` ➜ `IP:VRF:N3-01 (5G N3 Core Transport VRF)`
     - `SA5G:UPF:003` ➜ `SA5G:UPF:003 (5G Core User Plane Function / UPF)`
     - `CRM:TICKET:001` ➜ `CRM:TICKET:001 (Customer Trouble Ticket)`
     - `IP:PE:RTR-07` ➜ `IP:PE:RTR-07 (Transport MPLS Edge Router-07)`
   - Formatted in Bold Cyan / Pink / Orange ANSI colors.
2. **Interactive Stepper Prompt Helper (`_step_prompt`)**:
   - Handles `[Enter]`, `[c]` (chronology), `[b]` (blast radius), `[q]` (quit), and `--auto` mode with `--delay`.
3. **Use Case Walkthrough Functions**:
   - `run_demo_use_case_1(auto, delay)`
   - `run_demo_use_case_2(auto, delay)`
   - `run_demo_use_case_3(auto, delay)`
4. **Interactive Menu Runner (`run_interactive_demo_menu`)**:
   - Provides clear top-level selection for the user.
5. **Subparser Registration**:
   - `demo` command added to `build_parser()` and `COMMAND_CATEGORIES`.

---

## 4. Verification Plan

### Automated Tests
Run non-interactive automated dry-runs:
```bash
./fikracore demo --help
./fikracore demo 1 --auto --delay 0
./fikracore demo 2 --auto --delay 0
./fikracore demo 3 --auto --delay 0
```

### Manual Interactive Verification
Run interactive menu:
```bash
./fikracore demo
```
- Step through Use Case 1, test `[c]` chronology view.
- Step through Use Case 2, test interactive `[Y/n]` HITL approval prompt.
- Step through Use Case 3, verify SPOF and proactive mitigation scorecard.
