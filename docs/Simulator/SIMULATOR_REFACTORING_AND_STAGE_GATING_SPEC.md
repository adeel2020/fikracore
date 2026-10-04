# Simulator Refactoring & Stage-Gated Neural Reasoning Map Specification

> **Status:** Architecture Plan & Execution Note  
> **Source Files:**  
> - Frontend: [`frontend/src/app/simulator/investigate/page.tsx`](file:///Users/adeelarshad/FikraCore/frontend/src/app/simulator/investigate/page.tsx) (8,077 lines)  
> - Backend: [`services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py`](file:///Users/adeelarshad/FikraCore/services/agents/src/engine_stack/engines/telecom_brain/simulator/scenario_state_compiler.py)  
> **Date:** October 2, 2026  

---

## 1. Problem Statement

### 1.1 Premature Reasoning Pathway Illumination
In the Simulator Investigation workspace:
- **Observed Behavior (Defect):** At **Stage 2 (Signal Flood)**, reasoning pathways (e.g. *Operational Evidence*, *Service Dependency*, *Change & Configuration*) and the central *Reasoning Core* immediately light up active cyan/blue with lit conduits to the core.
- **Architectural Requirement:**
  - **Stage 1 (Trigger):** Only the single trigger event dot is present. Rest is dormant.
  - **Stage 2 (Signal Flood):** The multi-domain **Evidence Column** is active. The **cross-connection conduits** between Evidence and Pathways must light up and stream telemetry particles (showing the raw signals actively flooding across domains into the ingestion intakes). However, the **Reasoning Pathways themselves must remain DORMANT / UNLIT**, and the **Reasoning Core must remain IDLE / OBSERVING** because correlation has not yet executed.
  - **Stage 3 (Correlation):** The **10 Reasoning Pathways** ignite into active evaluated states. The conduits from Pathways into the **Reasoning Core** ignite, and the core transitions to `CORRELATING` / `CONVERGING`.

### 1.2 Monolithic File Debt
- `frontend/src/app/simulator/investigate/page.tsx` contains **8,077 lines** combining UI layout, canvas SVG math, 4 modals, and data transforms.
- `services/.../simulator/scenario_state_compiler.py` contained **3,938 lines** in a single `ScenarioStateCompiler` class with 35 private methods.

---

## 2. Visual & Behavioral State Matrix by Stage

| Stage | Stepper Index | Evidence Column | Cross-Conduits (Ev $\to$ Pathways) | Reasoning Pathways (10 Funnels) | Conduits (Pathways $\to$ Core) | Reasoning Core Orb |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1: Trigger** | `0` | Trigger item only | Dormant (dim) | Dormant (dim) | Dormant (dim) | `IDLE` |
| **Stage 2: Signal Flood** | `1` | **Active** (Alarms, Logs, Metrics, Changes) | **Active & Pulsing** (Streaming flood particles into intakes) | **Dormant / Unlit** (Awaiting correlation) | Dormant (dim) | `OBSERVING` / `IDLE` |
| **Stage 3: Correlation** | `2` | Active | Active | **Active & Illuminated** (Colored glowing badges) | **Active & Lit** | **`CORRELATING` / `CONVERGING`** |
| **Stage 4: Hypothesis Gen** | `3` | Active | Active | Active | Active | **`SYNTHESIZING`** (Feeding candidate hypotheses) |
| **Stage 5: Hypothesis Testing** | `4` | Active | Active | Active | Active | **`VALIDATING`** |

---

## 3. Step 1: Stage-Gating Logic Fix ✅ COMPLETED

### 3.1 Backend Fix (`scenario_state_compiler.py`) — ✅ DONE
Applied in `ScenarioStateCompiler._build_reasoning_map()` (lines ~2478–2547):
- Introduced `is_correlation_stage = stage_index >= 2`
- All 10 pathways strictly gate `"ACTIVE"` state through `is_correlation_stage`
- Pathways remain `"DORMANT"` or `"DISCOVERED"` when `stage_index < 2`

### 3.2 Frontend Fix (`page.tsx`) — ✅ DONE
Applied changes:
1. **`buildPathwayItems`** (`L847–L864, L907–L915`): Added `activeStageIndex: number = -1` parameter; `active` flag now gated by `activeStageIndex >= 2`.
2. **`NeuralReasoningCanvas` caller** (`L2405–2408`): Derives `localActiveStageIndex` and passes it to `buildPathwayItems`.
3. **`activeTrace` useMemo** (`L2669–2717`): Split:
   - Stage 2 (`localActiveStageIndex >= 1`): Lights cross-conduits from evidence into pathway intakes.
   - Stage 3 (`localActiveStageIndex >= 2`): Ignites reasoning pathway badges + conduits to core + sets `core = true`.
4. **Outer page caller** (`L5240`): Passes `activeStageIndex` to `buildPathwayItems`.

---

## 4. Step 2: Modular Refactoring Plans

### 4.1 Frontend Refactoring Plan (`frontend/src/app/simulator/investigate/`)

**Status Legend:** ✅ Done | 🔄 In Progress | ⏳ Planned

```
frontend/src/app/simulator/investigate/
├── page.tsx                           # Main orchestrator (8,077 lines — TO BE SLIMMED to ~500)
├── lib/                               # ✅ Created
│   ├── types.ts                       # ✅ All shared interfaces/types (~220 lines)
│   ├── conduit-math.ts                # ✅ SVG math, conduit arrays, catalogs (~260 lines)
│   └── index.ts                       # ✅ Barrel re-export
├── components/
│   ├── StageStepper.tsx               # ⏳ Top 7-stage workflow bar
│   ├── EventStreamColumn.tsx          # ⏳ Left column: Before/After flood table
│   ├── ZakiCopilotColumn.tsx          # ⏳ Right column: Zaki copilot bridge
│   ├── BottomInsightCards.tsx         # ⏳ Bottom 3 cards (Attribution, Story, Metrics)
│   └── canvas/
│       ├── NeuralReasoningCanvas.tsx  # ⏳ Central neural map container (L2382–5059)
│       ├── ReasoningCoreOrb.tsx       # ⏳ 3D/SVG central HUD orb & pulsing rings
│       ├── EvidencePillar.tsx         # ⏳ Column 1: Evidence intake sockets
│       ├── PathwayPillar.tsx          # ⏳ Column 2: Reasoning pathway badges
│       └── HypothesisPillar.tsx       # ⏳ Column 4: Hypothesis ranking cards
└── modals/
    ├── ConduitTelemetryModal.tsx      # ⏳ Modal when clicking neural conduits (L1825–1996)
    ├── CoreSynthesisDetailModal.tsx   # ⏳ Core synthesis telemetry modal (L2000–2178)
    ├── NeuralEntityDetailModal.tsx    # ⏳ Entity detail modal (L2182–2378)
    ├── KnowledgeGraphProjectionModal.tsx  # ⏳ Digital twin KG projection (L6862–7069)
    ├── ExecutiveTelemetryModal.tsx    # ⏳ Executive telemetry modal (L7101–7895)
    └── EventTelemetryDetailModal.tsx  # ⏳ Event telemetry detail (L7896–8077)
```

**Pure functions to move into `lib/transforms.ts` (⏳ planned):**
- `getScenarioAttributionProfile` (L416–710)
- `buildEvidenceItems` (L712–845)
- `buildPathwayItems` (L847–931)
- `buildEventStreamItems` (L975–1103)
- `buildHypothesisItems` (L1135–1218)
- `buildGapItems` (L1220–1239)
- `buildNextBestEvidenceItems` (L1259–1364)
- `resolveConduitTelemetry` (L1454–1608)
- `resolveEntityModal` (L1610–1821)
- `renderStyledMessage` (L5061–5114)

### 4.2 Backend Refactoring Plan — ✅ COMPLETED

```
services/agents/src/engine_stack/engines/telecom_brain/simulator/
├── scenario_state_compiler.py         # ✅ Slimmed coordinator (~2,185 lines, from 3,938)
└── compiler/
    ├── __init__.py                    # ✅ 16 lines
    ├── telemetry_loader.py            # ✅ 436 lines
    ├── reasoning_map_builder.py       # ✅ 651 lines
    ├── hypothesis_builder.py          # ✅ 226 lines
    ├── topology_builder.py            # ✅ 136 lines
    ├── zaki_builder.py                # ✅ 37 lines
    └── stage_watchdog.py              # ✅ 346 lines
```

---

## 5. Remaining Frontend Work

To complete the frontend refactoring, the following steps remain:

### Step A: Create `lib/transforms.ts`
Extract all pure data transform functions from `page.tsx` (lines 416–1821 approximately).
These are pure TS functions with no JSX — safe to extract without changing any logic.

### Step B: Extract modals (line ranges in current `page.tsx`)
- `ConduitDetailModal` → `modals/ConduitTelemetryModal.tsx` (L1825–1996)
- `CoreSynthesisDetailModal` → `modals/CoreSynthesisDetailModal.tsx` (L2000–2178)
- `NeuralEntityDetailModal` → `modals/NeuralEntityDetailModal.tsx` (L2182–2378)
- `KnowledgeGraphProjectionModal` → `modals/KnowledgeGraphProjectionModal.tsx` (L6862–7069)
- `ExecutiveTelemetryModal` → `modals/ExecutiveTelemetryModal.tsx` (L7101–7895)
- `EventTelemetryDetailModal` → `modals/EventTelemetryDetailModal.tsx` (L7896–8077)

### Step C: Extract `NeuralReasoningCanvas` (L2382–5059)
The largest single component (~2,680 lines). Uses `useFikraCore()` context internally.
Depends on `lib/types`, `lib/conduit-math`, `lib/transforms`, and the modal components.

### Step D: Extract column components
- `StageStepper` from `InvestigatePage`
- `EventStreamColumn` from `InvestigatePage`
- `ZakiCopilotColumn` from `InvestigatePage`
- `BottomInsightCards` from `InvestigatePage`

### Step E: Slim `page.tsx` to orchestrator
After all extractions, `page.tsx` should be ~400–600 lines: imports + `InvestigatePage` layout.
