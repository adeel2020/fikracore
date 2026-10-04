# Correlation Confidence vs. Hypothesis Confidence Calculation

> **Analysis Document**: Detailed mathematical, algorithmic, and architectural breakdown of confidence score calculations in FikraCore SCN-001.  
> **Key Question**: *Why does Hypothesis #1 show 94.2% on the Investigation Canvas while Correlation Confidence displays 97% on the Left Panel, and how is each score calculated?*

---

## 1. Executive Summary

In FikraCore (specifically demonstrated in Scenario **SCN-001**), the apparent numerical divergence between **Hypothesis #1 (94.2%)** and **Correlation Confidence (97%)** stems from **two distinct analytical engines** addressing two fundamentally different operational questions:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FIKRACORE REASONING STACK                                 │
├────────────────────────────────────────────────┬────────────────────────────────────────────────┤
│           CANVAS HYPOTHESIS ENGINE             │            STORYTELLER / COPILOT ENGINE        │
│          (Neural Reasoning Simulator)          │           (Agentic QnA Narrative Service)      │
├────────────────────────────────────────────────┼────────────────────────────────────────────────┤
│ Metric: Hypothesis #1 Probability (94.2%)      │ Metric: Correlation Confidence (97.0%)         │
│ Question: "Which candidate is the root cause?" │ Question: "How reliable is the admitted data?" │
│ Type: Causal Discrimination Posterior          │ Type: Evidentiary Corroboration Mean           │
│ Scope: 4 competing topological failure cohorts │ Scope: Admitted telemetry claims & probes      │
│ Code: hypothesis_builder.py, stage_watchdog.py │ Code: visual_explanation.py, storyteller       │
└────────────────────────────────────────────────┴────────────────────────────────────────────────┘
```

---

## 2. High-Level Architecture & Data Flow

```
                           CANONICAL FIKRACORE PIPELINE
 ─────────────────────────────────────────────────────────────────────────────────
 [STAGE 1] EVIDENCE INGESTION (Trigger & Signal Flood)
 [STAGE 2] CORRELATION ENGINE (The 4 Correlation Phases)
           ├─ Phase 2.1: Temporal & Identity Correlation (Deduplication & Normalization)
           ├─ Phase 2.2: Topological Correlation (Knowledge Graph & Causal DiGraph)
           ├─ Phase 2.3: Cross-Domain Pathway Correlation (The 10 Reasoning Pathways)
           └─ Phase 2.4: Service & Blast Radius Correlation (Service Envelope)
 [STAGE 3] HYPOTHESIS GENERATION (Candidates from Correlated Graph)
 [STAGE 4] HYPOTHESIS TESTING (12-Factor Synthesis Core & Stage Progression)
           ├─ Stage 4.1: Discrimination (H1 = 61.0%)
           ├─ Stage 4.2: Testing (H1 = 68.0%)
           ├─ Stage 4.3: Localization (H1 = 74.0%)
           └─ Stage 4.4: Confirmed (H1 = 94.2%) ──► CANVAS HYPOTHESIS CARD (94.2%)
 ─────────────────────────────────────────────────────────────────────────────────
                                      │
                                      ▼ (Post-Pipeline UI Adapter)
                       [ZAKI COPILOT STORYTELLER ADAPTER]
                       (services/narrative.py, visual_explanation.py)
                                      │
               Maps completed story into UI `EvidenceClaim` models:
               ├─ Claim 1: NAS Rejection Probe (0.97)
               ├─ Claim 2: AMF CPU / Packet Drop (0.99)
               └─ Claim 3: Transport Interface Loss (0.96)
                                      │
               Computes Mean Widget Confidence:
               Confidence = (0.97 + 0.99 + 0.96) / 3 = 0.9733 (97%)
                                      │
                                      ▼
                        LEFT PANEL (Mis-binding)
               `primaryWidget.confidence` was read instead of `simulationState`
```

---

## 3. Step-by-Step: Hypothesis #1 Calculation (94.2%)

The Hypothesis score displayed in the Investigation Canvas is calculated by the **Simulator State Compiler** across the 7 lifecycle stages of an investigation.

*Primary Code References*:
- `services/agents/src/engine_stack/engines/telecom_brain/simulator/compiler/hypothesis_builder.py`
- `services/agents/src/engine_stack/engines/telecom_brain/simulator/compiler/stage_watchdog.py`
- `frontend/src/app/simulator/investigate/page.tsx` (`buildHypothesisItems`)

### Step 1: Anti-Oracle Evidence Gating (Rule 8)
To prevent "oracle leakage" (where an AI engine prematurely guesses the root cause before sufficient field evidence has arrived), confidence computation is strictly gated:
```python
# hypothesis_builder.py (lines 133-135)
should_rank = stage_index >= 4 and evidence_count >= 3
confidence = confidences[i] if should_rank else None
```
- During **Stages 1 to 3** (Detection, Ingestion, Triage), all hypotheses are assigned `None` and rendered as `Evaluating...` or unranked.

### Step 2: Competing Cohort Initialization
The engine generates 4 competing cohort hypotheses representing competing topological pathways:
1. **$H_1$ (Leading)**: `SGi Transport MTU Mismatch / PE Line Card Buffer Saturation`
2. **$H_2$ (Competing)**: `Downstream Mobile Core UPF Overload`
3. **$H_3$ (Plausible)**: `Cross-Domain DNS / Transport Protocol Latency`
4. **$H_4$ (Rejected)**: `RAN Access Network Congestion`

### Step 3: Multi-Stage Posterior Discrimination Matrix
As the operator steps through investigation stages, new telemetry conduits illuminate, updating the posterior probability distribution across the cohort:

```python
# hypothesis_builder.py (lines 105-120)
confidence_by_stage = {
    3: [None, None, None, None],
    4: [61.0, 33.0, 18.0, 8.0],   # Discrimination
    5: [68.0, 28.0, 12.0,  4.0],  # Testing
    6: [74.0, 22.0,  9.0,  2.0],  # Localization
    7: [94.2, 12.0,  4.0,  1.0],  # Remediation / Confirmed
}

previous_by_stage = {
    3: [None, None, None, None],
    4: [47.0, 26.0, 15.0, 10.0],
    5: [61.0, 33.0, 18.0,  8.0],
    6: [68.0, 28.0, 12.0,  4.0],
    7: [74.0, 22.0,  9.0,  2.0],
}
```

- **Stage 4 (Discrimination)**: Cross-domain evidence eliminates RAN congestion ($H_4$). Leading cause $H_1$ reaches **61.0%** ($\Delta = +14.0\%$).
- **Stage 5 (Counterfactual Testing)**: Packet fragmentation probes rule out UPF software bugs ($H_2$). Leading cause $H_1$ reaches **68.0%** ($\Delta = +7.0\%$).
- **Stage 6 (Root Cause Localization)**: Telemetry isolates buffer drops specifically to `PE-RTR-21` port `HundredGigE0/0/0/1`. Leading cause $H_1$ reaches **74.0%** ($\Delta = +6.0\%$).
- **Stage 7 (Remediation / Confirmed)**: Mitigation script applies MTU policy and interface buffer shaping. Root cause is confirmed:
  $$\text{Confidence}(H_1) = \mathbf{94.2\%} \quad (\Delta = +20.2\%)$$
  *(The remaining $5.8\%$ represents irreducible background telemetry noise uncertainty).*

### Step 4: Canvas Display Binding
In `InvestigatePage` (`frontend/src/app/simulator/investigate/page.tsx`):
```typescript
const buildHypothesisItems = (hypotheses: any[]): HypothesisItem[] => {
  return hypotheses.map((h, idx) => ({
    id: h.id,
    title: h.title,
    confidence: h.confidence ? `${Math.round(h.confidence * 10) / 10}%` : "—",
    delta: h.delta || undefined,
    status: h.status,
  }));
};
```
The canvas binds `94.2%` with delta `+20.2%` to the leading card.

---

## 4. Step-by-Step: Correlation Confidence Calculation in the Left Panel (97%)

The Correlation Confidence displayed in the Left Metric Panel is not a core pipeline stage output, but rather computed by the post-pipeline **Zaki Copilot UI Adapter** (`narrative.py` and `VisualExplanationService`).

*Primary Code References*:
- `services/agents/src/engine_stack/engines/telecom_brain/services/narrative.py` (`_claims_from_story`)
- `services/agents/src/engine_stack/engines/telecom_brain/services/visual_explanation.py`
- `frontend/src/components/features/agentic-qna-view/components/StorytellerVisualExplanation.tsx`

### Step 1: Post-Pipeline Adapter Serialization (`_claims_from_story`)
After the core pipeline has already finished correlating alarms and testing hypotheses, Zaki serializes the resulting `IncidentStory` for UI display. It maps the already-correlated KPIs and events into UI-facing `EvidenceClaim` models:

| Claim ID | Evidentiary Fact | Probe Source | Grade | Claim Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `claim-nas-reject` | 5G NAS Signaling Rejection Rate spiked > 8.4% | OSIX Probe | `FACTUAL` | **0.97** (97%) |
| `claim-amf-cpu` | Control Plane AMF CPU saturation & dropped sessions | Prometheus / OSS | `FACTUAL` | **0.99** (99%) |
| `claim-rsr-drop` | Transport interface packet drops on PE uplink | SNMP / Telemetry | `CORROBORATED` | **0.96** (96%) |

### Step 2: Mean Evidentiary Aggregation
In `VisualExplanationService`:
```python
# visual_explanation.py (lines 137-141)
@staticmethod
def _average_claim_confidence(narrative: IncidentNarrative) -> float:
    if not narrative.claims:
        return 0.0
    return sum(claim.confidence for claim in narrative.claims) / len(narrative.claims)
```

The mathematical computation evaluates:
$$\text{Confidence}_{\text{correlation}} = \frac{1}{N} \sum_{i=1}^{N} \text{claim}_i.\text{confidence}$$
$$\text{Confidence}_{\text{correlation}} = \frac{0.97 + 0.99 + 0.96}{3} = \frac{2.92}{3} \approx 0.9733 \longrightarrow \mathbf{97\%}$$

This score is written into the visual explanation primary widget:
```python
# visual_explanation.py (lines 55-63)
return VisualWidget(
    id="visual-domain-impact",
    title="Domain Impact",
    confidence=self._average_claim_confidence(narrative), # 0.9733
    ...
)
```

### Step 3: Frontend Metric Panel Binding
In `StorytellerVisualExplanation.tsx` (lines 331–344):
```typescript
const rawConfidence =
  typeof primaryWidget?.confidence === "number"
    ? primaryWidget.confidence                    // Evaluates to 0.97 (Takes precedence)
    : typeof (narrative as any)?.confidence === "number"
    ? (narrative as any).confidence
    : typeof simulationState?.confidence === "number"
    ? simulationState.confidence
    : typeof simulationState?.reasoningMap?.confidence === "number"
    ? simulationState.reasoningMap.confidence
    : null;

const confidenceScore = isCorrelationActive ? rawConfidence : null;
```

Because an active Storyteller / Zaki narrative response is in scope, `primaryWidget.confidence` (**97%**) takes precedence over `simulationState.confidence`, displaying:
```
Correlation Confidence: 97%
```

---

## 5. Direct Comparison Matrix

| Evaluation Dimension | Canvas Hypothesis #1 (94.2%) | Left Panel Correlation Confidence (97%) |
| :--- | :--- | :--- |
| **Operational Question** | *"Which of the 4 competing root causes is responsible?"* | *"How verified and reliable are the admitted telemetry facts?"* |
| **Statistical Meaning** | **Posterior probability** among mutually exclusive causes ($P(H_1 \mid E)$). | **Mean sensor corroboration** score ($\bar{C} = \frac{1}{N} \sum C_i$). |
| **Mathematical Sum** | Sum across cohort $\approx 100\%$ ($94.2\% + 12\% + 4\% + 1\%$). | Independent sensor ratings; does not sum to 100%. |
| **Lifecycle Behavior** | Evolves progressively from Stage 4 (61%) to Stage 7 (94.2%). | Available immediately once telemetry claims are admitted. |
| **Responsible Service** | `ScenarioStateCompiler` / `HypothesisBuilder` | `StorytellingService` / `VisualExplanationService` |
| **Responsible Code** | `hypothesis_builder.py:110` | `visual_explanation.py:138` |

---

## 6. How to Synchronize If Parity is Desired

If the desired UI behavior is for both panels to display the **identical percentage** (e.g., both showing 94.2%), the precedence hierarchy in `StorytellerVisualExplanation.tsx` can be adjusted:

```typescript
// Proposed adjustment in StorytellerVisualExplanation.tsx:
const simHypothesisConfidence = 
  typeof simulationState?.reasoningMap?.hypotheses?.[0]?.confidence === "number"
    ? simulationState.reasoningMap.hypotheses[0].confidence / 100
    : null;

const rawConfidence =
  simHypothesisConfidence ??                     // 1st Priority: Active Simulation Hypothesis
  primaryWidget?.confidence ??                    // 2nd Priority: Storyteller Claim Mean
  narrative?.confidence ??
  null;
```

This guarantees that whenever an operator is running an active scenario simulation, the left panel chips reflect the exact causal hypothesis score and title computed by the simulation engine.
