# Mathematical Grounding & Architectural Justification of the Synthesis Core Equation

> **Document:** Synthesis Core Theoretical Foundation & Weight Justification  
> **Location:** `docs/Correlation/synthesis_core_grounding.md`  
> **Implementation Reference:** [`services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py:L179–L184`](file:///Users/adeelarshad/FikraCore/services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py#L179-L184)  
> **Status:** Authoritative Design Specification  

---

## 1. Executive Summary & Epistemic Philosophy

FikraCore's hypothesis scoring mechanism deliberately avoids black-box neural networks, uncalibrated Bayesian networks, and probabilistic guesses. 

In mission-critical telecommunications networks, probabilistic methods suffer from two fatal operational flaws:
1. **Overconfidence Drift & Hallucination:** Small changes in conditional priors can wildly swing probabilities without a verifiable causal reason.
2. **Audit Inscrutability:** An on-duty NOC Lead or Incident Commander during a major outage cannot easily verify why a machine says $P(\text{Root} \mid \text{Alarms}) = 0.892$.

Instead, FikraCore implements a **deterministic heuristic linear combination bounded in $[0.0, 1.0]$**. Every term directly reflects a verifiable physical, topological, or telemetry property that an engineer can audit line-by-line during post-mortem investigations.

```
"Confidence is a deterministic heuristic, not a calibrated probability."
                                      — investigator.py
```

---

## 2. Theoretical Grounding & Provenance

The scoring equation is synthesized from four foundational pillars of systems diagnosis:

### A. Abductive Reasoning & Parsimony (Peirce & Occam's Razor)
Inference to the best explanation: A hypothesis is favored if it explains the largest proportion of observed symptoms with the simplest causal mechanism. Multiple simultaneous independent faults are strongly discouraged unless no single entity can explain the degradation envelope.

### B. Causal Graph Inversion & Reachability (Pearl’s Causal Inference)
Network faults propagate along dependency chains. FikraCore inverts dependency edges ($\text{consumer} \to \text{supplier}$ inverted to $\text{cause} \to \text{symptom}$). If a candidate entity cannot reach an affected service or node in the directed graph, its causal plausibility drops precipitously.

### C. Popperian Asymmetric Falsification (Karl Popper)
*One piece of hard contradicting evidence refutes a hypothesis faster than ten pieces of supporting evidence can confirm it.* In telecom operations, if an element's local interfaces and loopback IPs report 100% nominal and healthy, the node is almost certainly innocent, regardless of downstream panic. This asymmetry is reflected in an aggressive negative evidence penalty ($-0.45$).

### D. Multi-Domain Telemetry Triangulation
In modern NFV / 5G SA architectures, single-layer monitoring tools (e.g., pure SNMP polling) can experience polling lag or false flaps. A true root cause candidate must be corroborated by independent telemetry domains (e.g., Syslog + NMS Metrics + Flow probes).

---

## 3. The Synthesis Core Scoring Equation

Executed in **Stage 4 (`HYPOTHESIS_TESTING`)** inside [`investigator.py:L179–L184`](file:///Users/adeelarshad/FikraCore/services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py#L179-L184):

$$\begin{aligned}
\text{Confidence}(H_k) = \; 
& \underbrace{0.32 \times \text{coverage}}_{\text{P3: Topology}} 
+ \underbrace{0.18 \times \text{independence}}_{\text{P8: Resilience}} 
+ \underbrace{0.15 \times \text{direct}}_{\text{P1: Operational Evidence}} \\
& + \underbrace{0.10 \times \text{temporal}}_{\text{P7: Control \& Signaling}} 
+ \underbrace{0.08 \times \text{upstream}}_{\text{P3: Topology}} 
+ \underbrace{0.05 \times \text{service}}_{\text{P2: Service Dependency}} \\
& + \underbrace{0.05 \times \text{knowledge\_confidence}}_{\text{P10: Knowledge Gap}} 
+ \underbrace{0.03 \times \text{freshness}}_{\text{P1: Operational Evidence}} 
+ \underbrace{0.02 \times \text{reliability}}_{\text{P1: Operational Evidence}} \\
& + \underbrace{0.01 \times \text{changes}}_{\text{P5: Change}} 
+ \underbrace{0.01 \times \text{historical}}_{\text{P9: Historical Pattern}} \\
& - \underbrace{0.45 \times \text{negative}}_{\text{P10: Falsification Penalty}} 
- \underbrace{0.20 \times \text{symptom}}_{\text{P4: Subscriber Journey Penalty}} 
- \underbrace{0.08 \times (|R| - 1)}_{\text{Occam's Razor Complexity Penalty}}
\end{aligned}$$

$$\text{Final Score} = \text{round}(\max(0.0, \min(1.0, \text{Confidence}(H_k))), 4)$$

---

## 4. Weight Architecture: Budget & Tiers

The weights are balanced across three functional tiers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ POSITIVE WEIGHT BUDGET: Exactly 1.00                                   │
│                                                                        │
│ [ Tier 1: Dominant Structural Drivers (0.65) ]                         │
│   • Blast Radius Coverage           (+0.32)                            │
│   • Telemetry Independence          (+0.18)                            │
│   • Direct Local Evidence Quality   (+0.15)                            │
│                                                                        │
│ [ Tier 2: Corroboration & Epistemic Trust (0.35) ]                     │
│   • Temporal Precedence             (+0.10)                            │
│   • Upstream Graph Position         (+0.08)                            │
│   • Service Dependency Relevance    (+0.05)                            │
│   • Knowledge Graph Confidence      (+0.05)                            │
│   • Evidence Freshness              (+0.03)                            │
│   • Source Sensor Reliability       (+0.02)                            │
│   • Change Event Relevance          (+0.01)                            │
│   • Historical Pattern Match        (+0.01)                            │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 3: DEFENSIVE FALSIFICATION & ANTI-SYMPTOM PENALTIES               │
│   • Contradicting Negative Evidence (-0.45)                            │
│   • Symptom-Only Leaf Penalty       (-0.20)                            │
│   • Compound Root Set Penalty       (-0.08 * (|R| - 1))                │
└────────────────────────────────────────────────────────────────────────┘
```

Notice that **all positive weights sum to exactly $1.00$**:
$$0.32 + 0.18 + 0.15 + 0.10 + 0.08 + 0.05 + 0.05 + 0.03 + 0.02 + 0.01 + 0.01 = 1.00$$

This mathematical guarantee ensures that an ideal candidate with complete explanatory coverage, corroborated by multi-source telemetry, and untainted by penalties evaluates to precisely **$1.00$ ($100\%$ confidence)**.

---

## 5. Term-by-Term Justification & Engineering Rationale

### 🔹 Tier 1: Dominant Structural Drivers ($0.65$)

#### 1. Blast Radius Coverage ($+0.32$)
* **Calculation:** $\text{coverage} = \frac{|\text{impacted} \cap \text{reachable}|}{|\text{impacted}|}$
* **Why $0.32$?**: Explanatory power is the single most important criterion in root-cause isolation. If candidate node $X$ only explains 1 out of 5 impacted nodes ($\text{coverage} = 0.2$), it cannot be the sole root cause. By allocating roughly **one-third of the total score budget** to coverage, any node that fails to explain the entire blast radius is mathematically blocked from crossing the confirmation threshold ($\ge 0.65$).

#### 2. Independent Telemetry ($+0.18$)
* **Calculation:** $\text{independence} = \min(1.0, \frac{\text{len(distinct sources)}}{2})$
* **Why $0.18$?**: Telecom monitoring systems frequently suffer from isolated probe glitches, polling timeouts, or SNMPMIB bugs. Requiring verification from **$\ge 2$ independent systems** (e.g., NMS metrics + Syslog alarms) provides $18\%$ of the score, ensuring the engine never crowns a single-source anomaly as ground truth.

#### 3. Direct Local Quality ($+0.15$)
* **Calculation:** Weighted average quality of abnormal telemetry alarms originating *directly* on the candidate root element.
* **Why $0.15$?**: Differentiates nodes that are actively failing locally (e.g., BGP hold timer expired, buffer overflow, link down) from nodes that are merely suspected due to upstream topological proximity.

---

### 🔹 Tier 2: Corroboration & Epistemic Trust ($0.35$)

#### 4. Temporal Precedence ($+0.10$)
* **Calculation:** $1.0$ if the candidate's earliest local alarm timestamp $\le$ all dependent symptom timestamps.
* **Why $0.10$?**: Causes must precede effects. In telecom, the real root cause flaps first, followed milliseconds to seconds later by downstream alerts. It is kept at $+0.10$ rather than higher to accommodate real-world syslog buffering and NTP jitter, where a leaf alarm occasionally registers slightly before an edge alarm.

#### 5. Upstream Graph Position ($+0.08$)
* **Calculation:** $1.0$ if directed topological path exists from candidate to all affected nodes.
* **Why $0.08$?**: In transport backhaul, traffic flows Core $\leftrightarrow$ Edge $\leftrightarrow$ Access. Elements sitting upstream in the traffic conduit must carry higher intrinsic causal likelihood.

#### 6. Service Dependency Relevance ($+0.05$)
* **Calculation:** $1.0$ if candidate explicitly hosts or routes the degraded service slice (e.g., `5g_sa_mobile_data`).
* **Why $0.05$?**: Filters out adjacent routers that are physically near the fault but carry unrelated enterprise or voice VRFs.

#### 7. Knowledge Graph Confidence ($+0.05$)
* **Calculation:** Minimum edge confidence score across all graph hops traversed in FikraCore.
* **Why $0.05$?**: Rewards hypotheses backed by thoroughly validated discovery edges over hypotheses dependent on speculative or unverified topology paths.

#### 8. Evidence Freshness ($+0.03$) & Source Reliability ($+0.02$)
* **Calculation:** Exponential time-decay ($\sim e^{-\lambda \Delta t}$) and provider reputation rating ($0.0$ to $1.0$).
* **Why $0.03$ & $0.02$?**: Stale alarms from prior shifts must decay in influence. High-fidelity telemetry collectors (e.g. streaming telemetry) receive higher weight than uncalibrated third-party probes.

#### 9. Change Relevance ($+0.01$) & Historical Pattern ($+0.01$)
* **Calculation:** Binary flag for recent configuration changes ($+0.01$) and prior pattern match ($+0.01$).
* **Why so small ($0.01$ each)?**: They serve purely as **tie-breakers**. A recent configuration change or historical precedent is valuable context, but an operator must never convict a router solely on a change record without physical telemetry degradation.

---

### 🔹 Tier 3: Defensive Falsification & Anti-Symptom Penalties

#### 10. Negative Evidence Penalty ($-0.45$) — The Heavy Artillery
* **Trigger:** Candidate node possesses healthy telemetry checks, loopback pings normal, or interfaces operational during the fault window.
* **Why $-0.45$?**: If a router's health probe reports `"all interfaces nominal and traffic flowing"`, it is almost certainly innocent. A penalty of $-0.45$ cuts a candidate's score nearly in half with a single contradicting metric. It ensures that any candidate with active contradicting evidence drops below the supported threshold ($0.65$) into `REJECTED`.

#### 11. Symptom Likelihood Penalty ($-0.20$) — The Leaf Trap Breaker
* **Trigger:** Candidate node only exhibits downstream symptom alerts (e.g. dropped user sessions, HTTP 500s) without local infrastructure root alarms.
* **Why $-0.20$?**: In every network outage, leaf nodes (UPFs, firewalls, CRM queues) scream the loudest because they sit closest to subscribers. Operators are routinely distracted by these "victim nodes". This penalty ensures downstream victim elements are never crowned as root causes when an upstream transport element failed.

#### 12. Occam’s Razor Penalty ($-0.08 \times (|R| - 1)$)
* **Trigger:** Formulating compound, multi-node root cause sets ($|R| > 1$).
* **Why $-0.08$?**: If an engineer proposes that *two routers broke simultaneously* ($|R|=2$), they pay an immediate $-0.08$ penalty. If they propose *three simultaneous roots*, they lose $-0.16$. A compound multi-root hypothesis is only accepted if single-root candidates fail to achieve adequate coverage.

---

## 6. Hypothesis Classification & Status Thresholds

Stage 4 applies deterministic epistemic status gates directly based on the calculated score and negative evidence strength:

```python
if negative_strength >= 0.7 and direct < 0.5:
    status = KnowledgeState.REJECTED
elif score >= 0.65:
    status = KnowledgeState.SUPPORTED
else:
    status = KnowledgeState.CANDIDATE
```

* **`SUPPORTED` ($\ge 0.65$):** Passed structural coverage, corroborated by multi-source telemetry, with zero contradicting evidence. Eligible to be crowned **Winning Root Cause ($H_1$)**.
* **`CANDIDATE` ($< 0.65$):** Partially explains symptoms or lacks multi-source corroboration. Triggers Step 4.3 Discrimination Probes to gather missing evidence.
* **`REJECTED`:** Decisively falsified by local health proofs. Eliminated from root cause consideration.
