# Implementation Plan: Comprehensive Modular Correlation & CLI Architecture Refactoring (`fikracore --live -v`)

Perform an end-to-end architectural refactoring across [`investigator.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py) and [`cli.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py). Extract presentation formatting into a dedicated [`verbose_presenter.py`](file:///Users/adeelarshad/kagent/services/agents/src/engine_stack/engines/telecom_brain/investigation/verbose_presenter.py) module to eliminate terminal-drawing bloat from `cli.py`, and replace `cli.py`'s 950-line `if/elif` chain with a clean **Command Dispatch Registry**. Explicitly architect the **Correlation Engine** as a 4-dimensional engine (Temporal/Identity, Topological, Cross-Domain Pathways, and Service/Blast Radius) feeding the Hypothesis Evaluation and Continuous Learning engines for `fikracore demo --live -v` (and shortcut `fikracore --live -v`) with **100% dynamically computed** scenario-agnostic terminal outputs. Update [`docs/Correlation/correlation.md`](file:///Users/adeelarshad/kagent/docs/Correlation/correlation.md).

---

## User Review Required

> [!IMPORTANT]
> **Architectural Realignment: The 4 Dimensions of the Correlation Engine**:
> In telecom incident root cause analysis, **Correlation** is not a single isolated step or just "Reasoning Pathways". Correlation is the **overarching engine** that transforms disparate, noisy operational events into a structured, bounded causal envelope across 4 explicit dimensions:
> 1. **Phase 2.1: Temporal & Identity Correlation** (Canonical slug normalization, timestamp alignment, freshness decay, and deduplication/event collapse).
> 2. **Phase 2.2: Topological Correlation** (Knowledge graph traversal & dynamic causal DiGraph inversion from consumer/supplier to causal driver/sink).
> 3. **Phase 2.3: Cross-Domain Pathway Correlation** (The 9 parallel analytical lenses evaluating Transport, RAN, Core, Power, Change, Signaling, Subscriber, Resilience, and Knowledge Gaps).
> 4. **Phase 2.4: Service & Blast Radius Correlation** (Primary impacted customer service identification, coincidental alarm filtering, and damage envelope boundary).
>
> Once Correlation completes, the **Hypothesis & Reasoning Engine** executes:
> - **Stage 3: Hypothesis Generation** (Candidate root formulation via topology ancestry & observed evidence).
> - **Stage 4: Hypothesis Testing** (12-Factor Synthesis Core Evaluation & Popperian Falsification).
> - **Stage 5: Convergence & Knowledge Gap Detection** (Winning root cause, unexplained residuals, and H2 gaps).
> - **Stage 6: Domain Attribution & Affected Services** (Authoritative root domain & blast metrics).
> - **Stage 7: Next-Best Evidence & Operator Validation** (`validation_decision.yaml` SME approval gate).
> - **Stage 8: Knowledge Graph Promotion** (Smart Delta Link Upsert via MCP & rollback journal).

> [!IMPORTANT]
> **Optional Deep-Dive Inspection Gates in `demo --live -v`**:
> To keep the live investigation streamlined for executives while empowering deep technical auditability, the **Synthesized Evidence Vector Payload** (Stage 2) and the **12-Factor Synthesis Core Math Computation** (Stage 4) will be **interactive optional deep-dives**:
> 1. **Stage 2 Payload Gate**: Operator is prompted: `[?] View SYNTHESIZED CORRELATION EVIDENCE VECTOR payload? [v=View / Enter=Proceed]: `
>    - If selected (`v` / `y`): Renders full 12-factor JSON payload card.
>    - If skipped (Enter / `p`): Displays a concise 1-line summary and proceeds immediately to Stage 3.
> 2. **Stage 4 Synthesis Math Gate**: Operator is prompted: `[?] View 12-FACTOR SYNTHESIS CORE mathematical breakdown? [v=View / Enter=Proceed]: `
>    - If selected (`v` / `y`): Renders the itemized weights, vector products, and Popperian falsification calculations for each candidate.
>    - If skipped (Enter / `p`): Displays the ranked candidate table with final scores and proceeds to Convergence.
> 3. **Non-Interactive & CI Support**: In automated mode (`--auto`), proceeds cleanly without blocking unless `--show-vectors` or `--show-math` flags are explicitly supplied.

> [!IMPORTANT]
> **`cli.py` Internal Refactoring**:
> 1. **Command Dispatch Registry**: Replaces the 950-line `if/elif` block in `main()` with a modular dictionary of command handlers (`DISPATCH_MAP`).
> 2. **Modular Subparser Builders**: Breaks the monolithic 250-line `build_parser()` into categorized registration functions (`_register_investigation_commands()`, `_register_demo_commands()`, `_register_snapshot_commands()`, `_register_learning_commands()`).
> 3. **Streamlined `run_live_use_case_1()`**: Strips out ~200 lines of inline ANSI string padding and stdout writes, making it a clean ~40-line coordinator that delegates to `verbose_presenter` or the compact live monitor.
> 4. **CLI Flag Routing**: Adds `-v` / `--verbose`, `--show-vectors`, and `--show-math` to `demo` and enables direct top-level shortcut execution (`fikracore --live -v`).

---

## File Structure After Refactoring

```
services/agents/src/engine_stack/engines/telecom_brain/investigation/
├── correlation/                               <── [NEW SUBPACKAGE: Stage 2]
│   ├── __init__.py                            <── Exports CorrelationEngine & sub-correlators
│   ├── temporal_identity.py                   <── Phase 2.1: Temporal & Identity Correlation
│   ├── topological.py                         <── Phase 2.2: Topological Correlation
│   ├── pathways.py                            <── Phase 2.3: Cross-Domain Pathway Correlation
│   ├── blast_radius.py                        <── Phase 2.4: Service & Blast Radius Correlation
│   └── engine.py                              <── CorrelationEngine coordinator & vector payload
├── investigator.py                            <── [REFACTORED] High-level orchestrator
├── verbose_presenter.py                       <── [NEW] Dedicated ANSI box renderer
├── cli.py                                     <── [REFACTORED] Command Dispatcher Map & Modular Subparsers
└── demo_presenter.py                          <── Preserved baseline demo presentation
```

---

## Detailed Plan: `cli.py` Internal Refactoring

### 1. Command Dispatch Registry
Replace the 950-line `if/elif` chain in `main()` with a clean handler mapping:

```python
COMMAND_HANDLERS = {
    "demo": handle_demo_command,
    "investigate": handle_investigate_command,
    "discover": handle_discover_command,
    "learn": handle_learn_command,
    "simulate": handle_simulate_command,
    "predict": handle_predict_command,
    "inspect": handle_inspect_command,
    "present": handle_present_command,
    "snapshot": handle_snapshot_command,
    "restore": handle_restore_command,
    "validate-candidate": handle_validate_candidate_command,
    "promote-knowledge": handle_promote_knowledge_command,
    "rollback-promotion": handle_rollback_promotion_command,
    "run-h2-benchmark": handle_h2_benchmark_command,
    "run-h3-benchmark": handle_h3_benchmark_command,
    "run-h4-benchmark": handle_h4_benchmark_command,
    # ... mapped cleanly to single-purpose functions
}
```

### 2. Modular Subparser Registration
Break down `build_parser()` into distinct logical registration functions:
- `_register_core_commands(commands)`: `investigate`, `discover`, `learn`, `simulate`, `predict`, `inspect`, `present`
- `_register_demo_commands(commands)`: `demo` (with `-v`/`--verbose`, `--live`, `--auto`, `--delay`), `diagnose-run`, `h2-demo`, `h3-demo`, `h4-demo`
- `_register_snapshot_commands(commands)`: `snapshot`, `backup`, `restore`, `restore-snapshot`, `ingest-topology`
- `_register_learning_commands(commands)`: `validate-candidate`, `promote-knowledge`, `rollback-promotion`, H2/H3/H4 benchmark & generator commands

### 3. Streamlined `run_live_use_case_1()` Coordinator
```python
def run_live_use_case_1(auto: bool = False, delay: float = 0.8, verbose: bool = False) -> int:
    """Live execution of Use Case 1: Cross-Domain Service Outage."""
    # 1. Initialize Investigator with chosen monitor:
    #    - If verbose: attaches VerboseLiveMonitor (from verbose_presenter.py)
    #    - If compact: attaches CompactTableMonitor
    # 2. Run investigation over operational evidence
    # 3. Persist execution trace and return exit code
```

---

## Detailed Plan: `investigator.py` Modularization

Decompose `investigate()` and inner `assess()` into clean single-responsibility classes:
1. **`EvidenceNormalizer` (Phase 2.1)**: Canonical slug mapping, freshness time decay, and deduplication (`collapse`).
2. **`CausalDiGraphBuilder` (Phase 2.2)**: Traverses knowledge edges in `CanonicalKnowledge`, inverts dependencies (`consumer -> supplier` to `causal driver -> sink`), and builds the live `nx.DiGraph`.
3. **`CorrelationFunnelsEngine` (Phase 2.3)**: Evaluates the 9 multi-domain analytical funnels (*Operational Evidence*, *Service Dependency*, *Subscriber Journey*, *Change & Configuration*, *Traffic & Capacity*, *Control & Signaling*, *Resilience & Failover*, *Historical Pattern*, *Knowledge Gap*).
4. **`BlastRadiusAnalyzer` (Phase 2.4)**: Isolates the primary `impacted_service`, filters coincidental noise, partitions telemetry into abnormal vs healthy sets, and sets the total blast radius (`impacted`).
5. **`HypothesisGenerator` (Stage 3)**: Formulates candidate root entities from observed operational evidence and backward topological graph traversal (`nx.ancestors`), constructing unranked candidate hypothesis contracts.
6. **`SynthesisCoreAssessor` (Stage 4)**: Computes the 12-factor synthesized correlation vector, evaluates the Synthesis Core Equation, applies Popperian falsification penalties, and evaluates combinatorial dual-cause hypotheses.
7. **`ConvergenceRanker` (Stage 5)**: Ranks hypotheses by confidence, selects the winning root cause driver, isolates unexplained residuals, and determines the terminal state (`Terminal.EXPLAINED`, etc.).
8. **`GapAndResidualDetector` (Stage 5)**: Discovers unverified path adjacencies and localizes H2 knowledge gaps.
9. **`Investigator` (Facade)**: Orchestrates the pipeline and dispatches structured telemetry for each stage to `step_callback`.

---

## Complete End-to-End Telecom Pipeline

```
Stage 1: TELEMETRY INGESTION (NMS, EMS, Syslog, CRM, Change DB)
   │
   ▼
Stage 2: CORRELATION ENGINE (Multi-Dimensional Correlation)
   ├── Phase 2.1: Temporal & Identity Correlation (Normalization, Freshness & Collapse)
   ├── Phase 2.2: Topological Correlation (Graph Traversal & Causal DiGraph Assembly)
   ├── Phase 2.3: Cross-Domain Pathway Correlation (9 Multi-Domain Analytical Funnels)
   └── Phase 2.4: Service & Blast Radius Correlation (Damage Envelope & Noise Isolation)
   │
   ▼
Stage 3: HYPOTHESIS GENERATION (Candidate Formulation via Topology Ancestry & Evidence)
   │
   ▼
Stage 4: HYPOTHESIS TESTING (12-Factor Synthesis Core Evaluation)
   │
   ▼
Stage 5: CONVERGENCE & KNOWLEDGE GAP DETECTION
   │
   ▼
Stage 6: DOMAIN ATTRIBUTION & AFFECTED SERVICES
   │
   ▼
Stage 7: NEXT-BEST EVIDENCE & OPERATOR VALIDATION
   │
   ▼
Stage 8: KNOWLEDGE GRAPH PROMOTION (Smart Delta Link Upsert via MCP)
```

---

## Step-by-Step Scenario-Agnostic Terminal Display Designs (`--live -v`)

Every output is **100% dynamically derived** from live telemetry, graph objects, and mathematical evaluations with zero hardcoding.

---

### Stage 1: TELEMETRY INGESTION
```text
┌─ Stage 1: TELEMETRY INGESTION ────────────────────────────────────────┐
│ Loaded {raw_count} raw operational records from {len(sources)} independent sources          │
│                                                                        │
│ Sources:  {', '.join(f"{src} ({count})" for src, count in sources.items())}
│ Types:    {', '.join(f"{t} ({count})" for t, count in types.items())}
│ Window:   {min_time} → {max_time}  ({time_span_s:.0f}s span)               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 2: CORRELATION ENGINE

#### Phase 2.1: Temporal & Identity Correlation
```text
┌─ Stage 2.1: CORRELATION ENGINE ── Temporal & Identity Correlation ─────┐
│ Canonical slug normalization, timestamp alignment & deduplication     │
│                                                                        │
│ Canonicalization: {raw_count} raw → {normalized_count} canonical entities                      │
│ Freshness decay:  avg {avg_freshness:.2f} (max age: {max_age_h:.1f} hours)                       │
│ Deduplication:    {normalized_count} normalized → {collapsed_count} unified events ({dedup_pct:.0%})        │
└────────────────────────────────────────────────────────────────────────┘
```

#### Phase 2.2: Topological Correlation
```text
┌─ Stage 2.2: CORRELATION ENGINE ── Topological Correlation ────────────┐
│ Dynamic causal dependency traversal and DiGraph assembly              │
│                                                                        │
│ Graph Provider:      {provider_name} (CanonicalKnowledge)            │
│ Entities Traversed:  {len(traversed_entities)} canonical entities                                │
│ Relationships Found: {len(edges)} causal links                                │
│ Topology DiGraph:    {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges (consumer→supplier inverted)     │
│                                                                        │
│ Topological Causal Chains:                                             │
{formatted_topological_chains}
└────────────────────────────────────────────────────────────────────────┘
```

#### Phase 2.3: Cross-Domain Pathway Correlation
```text
┌─ Stage 2.3: CORRELATION ENGINE ── Cross-Domain Pathway Correlation ───┐
│ Evaluated operational telemetry across 9 multi-domain reasoning lenses │
│                                                                        │
│ Active Pathways: {active_funnels_count} of 9 funnels triggered                         │
│                                                                        │
│   {m_op} Operational Evidence        {status_op:<8} [{reason_op}]      │
│   {m_srv} Service Dependency          {status_srv:<8} [{reason_srv}]     │
│   {m_sub} Subscriber Journey          {status_sub:<8} [{reason_sub}]     │
│   {m_cfg} Change & Configuration      {status_cfg:<8} [{reason_cfg}]     │
│   {m_trf} Traffic & Capacity          {status_trf:<8} [{reason_trf}]     │
│   {m_sig} Control & Signaling         {status_sig:<8} [{reason_sig}]     │
│   {m_res} Resilience & Failover       {status_res:<8} [{reason_res}]     │
│   {m_his} Historical Pattern          {status_his:<8} [{reason_his}]     │
│   {m_gap} Knowledge Gap               {status_gap:<8} [{reason_gap}]     │
└────────────────────────────────────────────────────────────────────────┘
```

#### Phase 2.4: Service & Blast Radius Correlation
```text
┌─ Stage 2.4: CORRELATION ENGINE ── Service & Blast Radius Correlation ─┐
│ Synthesized pathway outputs into operational damage envelope           │
│                                                                        │
│ Abnormal Events:         {len(abnormal)} across {len(impacted)} entities                       │
│ Healthy Events:          {len(healthy)} (evaluated for negative falsification)         │
│ Direct Blast Radius:     {len(impacted)} degraded entities                               │
│ Primary Impacted Service:{impacted_service or 'NONE'} ({len(service_entities)} entities degraded)       │
│ Involved Domains:        {', '.join(detected_domains)}                │
│ Coincidental Filter:     {len(unrelated)} unrelated alarms filtered as background noise│
└────────────────────────────────────────────────────────────────────────┘
```

#### Stage 2 Payload: SYNTHESIZED CORRELATION EVIDENCE VECTOR (Optional Deep-Dive)
```text
[?] View SYNTHESIZED CORRELATION EVIDENCE VECTOR payload? [v=View / Enter=Proceed]: 
```

*If operator selects `v` (View):*
```text
┌─ Stage 2 Payload: SYNTHESIZED CORRELATION EVIDENCE VECTOR ────────────┐
│ Formatted Correlation Payload emitted to downstream Hypothesis Engine │
│                                                                        │
│   {                                                                    │
│     "temporal_precedence":          {temporal_precedence:.4f},  (Phase 2.1) │
│     "evidence_freshness":           {evidence_freshness:.4f},  (Phase 2.1) │
│     "source_reliability":           {source_reliability:.4f},  (Phase 2.1) │
│     "independent_telemetry":        {independent_telemetry:.4f},  (Phase 2.1/2.3) │
│     "upstream_position":            {upstream_position:.4f},  (Phase 2.2) │
│     "knowledge_confidence":         {knowledge_confidence:.4f},  (Phase 2.2) │
│     "change_relevance":             {change_relevance:.4f},  (Phase 2.3) │
│     "historical_support":           {historical_support:.4f},  (Phase 2.3) │
│     "symptom_likelihood_penalty":   {symptom_likelihood:.4f},  (Phase 2.3) │
│     "blast_radius_coverage":        {blast_radius_coverage:.4f},  (Phase 2.4) │
│     "service_dependency_relevance": {service_relevance:.4f},  (Phase 2.4) │
│     "negative_evidence":            {negative_evidence:.4f}   (Phase 2.4) │
│   }                                                                    │
│                                                                        │
│ Correlation Vector Summary:                                            │
│   • Active Dimensions Measured    : 12 / 12 factors                   │
│   • Telemetry Compression Ratio   : {raw_count} raw ➜ {len(abnormal)} abnormal ({(1 - len(abnormal)/raw_count)*100:.1f}% reduction)│
│   • Causal Envelope Bounded       : {len(impacted)} impacted nodes across {len(detected_domains)} domains    │
└────────────────────────────────────────────────────────────────────────┘
```

*If operator presses `Enter` (Proceed / Skip):*
```text
  [→] Correlation Vector: 12 factors synthesized | {raw_count} raw ➜ {len(abnormal)} abnormal | Bounded {len(impacted)} nodes. Proceeding...
```

---

### Stage 3: HYPOTHESIS GENERATION (Candidate Formulation via Topology Ancestry & Evidence)
```text
┌─ Stage 3: HYPOTHESIS GENERATION ──────────────────────────────────────┐
│ Formulated {len(roots)} candidate hypotheses from evidence & topological ancestors │
│                                                                        │
│ Candidate Pool Breakdown:                                              │
│   • Direct Evidence Entities : {len(direct_entities)} (observed alarms, changes, KPIs) │
│   • Upstream Graph Ancestors : {len(ancestor_entities)} (silent/upstream causal drivers)│
│                                                                        │
│ Candidate Root Entities:                                               │
│   1. H-001: {roots[0]} ──► Reachable: {len(reach_1)} nodes | Max Coverage: {cov_1:.0%} │
│   2. H-002: {roots[1]} ──► Reachable: {len(reach_2)} nodes | Max Coverage: {cov_2:.0%} │
│   ...                                                                  │
│                                                                        │
│ Status: CANDIDATE | Unranked (Awaiting 12-Factor Synthesis Evaluation) │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 4: HYPOTHESIS TESTING (12-Factor Synthesis Core Evaluation - Optional Deep-Dive)
```text
[?] View 12-FACTOR SYNTHESIS CORE mathematical breakdown? [v=View / Enter=Proceed]: 
```

*If operator selects `v` (View):*
```text
┌─ Stage 4: HYPOTHESIS TESTING (12-FACTOR SYNTHESIS CORE) ───────────────┐
│ Evaluating Candidate #{candidate_index}: {candidate_entity} ({candidate_display_name}) │
│                                                                        │
│ Synthesized Evidence Vector:                                           │
│   ├─ blast_radius_coverage        : {vector['blast_radius_coverage']:.2f}  (wt: +0.32) ➜ {+0.32*vector['blast_radius_coverage']:+.4f}│
│   ├─ independent_telemetry        : {vector['independent_telemetry']:.2f}  (wt: +0.18) ➜ {+0.18*vector['independent_telemetry']:+.4f}│
│   ├─ direct_telemetry_quality     : {direct_quality:.2f}  (wt: +0.15) ➜ {+0.15*direct_quality:+.4f}│
│   ├─ temporal_precedence          : {vector['temporal_precedence']:.2f}  (wt: +0.10) ➜ {+0.10*vector['temporal_precedence']:+.4f}│
│   ├─ upstream_position            : {vector['upstream_position']:.2f}  (wt: +0.08) ➜ {+0.08*vector['upstream_position']:+.4f}│
│   ├─ service_dependency_relevance : {vector['service_dependency_relevance']:.2f}  (wt: +0.05) ➜ {+0.05*vector['service_dependency_relevance']:+.4f}│
│   ├─ knowledge_confidence         : {vector['knowledge_confidence']:.2f}  (wt: +0.05) ➜ {+0.05*vector['knowledge_confidence']:+.4f}│
│   ├─ evidence_freshness           : {vector['evidence_freshness']:.2f}  (wt: +0.03) ➜ {+0.03*vector['evidence_freshness']:+.4f}│
│   ├─ source_reliability           : {vector['source_reliability']:.2f}  (wt: +0.02) ➜ {+0.02*vector['source_reliability']:+.4f}│
│   ├─ change_relevance             : {vector['change_relevance']:.2f}  (wt: +0.01) ➜ {+0.01*vector['change_relevance']:+.4f}│
│   ├─ historical_support           : {vector['historical_support']:.2f}  (wt: +0.01) ➜ {+0.01*vector['historical_support']:+.4f}│
│   ├─ negative_evidence_penalty    : {vector['negative_evidence']:.2f}  (wt: -0.45) ➜ {-0.45*vector['negative_evidence']:+.4f}│
│   ├─ symptom_likelihood_penalty   : {vector['symptom_likelihood_penalty']:.2f}  (wt: -0.20) ➜ {-0.20*vector['symptom_likelihood_penalty']:+.4f}│
│   └─ multi_cause_penalty          : {len(roots)-1}  (wt: -0.08) ➜ {-0.08*(len(roots)-1):+.4f}│
│                                                                        │
│ Computed Confidence Score : {score:.4f} ({score*100:.1f}%)                       │
│ Lifecycle State & Role    : {status.value} | {role.value}                      │
└────────────────────────────────────────────────────────────────────────┘
```

*If operator presses `Enter` (Proceed / Skip):*
```text
┌─ Stage 4: HYPOTHESIS TESTING (Summary) ────────────────────────────────┐
│ Evaluated {len(hypotheses)} candidate hypotheses against 12-factor synthesis core │
│                                                                        │
│   #1 H-001 ({h1.canonical_root_entity}) : Score {h1.hypothesis_confidence:.4f} [{h1.status.value} / {h1.causal_role.value}]
│   #2 H-002 ({h2.canonical_root_entity}) : Score {h2.hypothesis_confidence:.4f} [{h2.status.value} / {h2.causal_role.value}]
│                                                                        │
│ [Mathematical weights & Popperian breakdown skipped by operator]       │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 5: CONVERGENCE & KNOWLEDGE GAP DETECTION
```text
┌─ Stage 5: CONVERGENCE & KNOWLEDGE GAP DETECTION ──────────────────────┐
│ Convergence: Top Driver ➜ {best.canonical_root_entity} (Score: {best.hypothesis_confidence:.4f}) │
│                                                                        │
│ Ranked Hypothesis Queue:                                               │
│   ● H1: {h1.canonical_root_entity:<25} Score: {h1.hypothesis_confidence:.2f} | Coverage: {h1.explanation_coverage:.0%} (WINNING)│
│   ○ H2: {h2.canonical_root_entity:<25} Score: {h2.hypothesis_confidence:.2f} | Coverage: {h2.explanation_coverage:.0%} (COMPETING)│
│                                                                        │
│ Blast Radius Resolution:                                               │
│   • Explained Anomalies     : {len(explained)} / {len(abnormal)} ({best.explanation_coverage:.0%})                 │
│   • Unexplained Residuals   : {len(residual)} observations                         │
│   • Discovered Gaps (H2)    : {len(candidates)} unverified path adjacencies       │
│                                                                        │
│ Terminal Resolution State   : Terminal.{terminal.value}                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 6: DOMAIN ATTRIBUTION & AFFECTED SERVICES
```text
┌─ Stage 6: DOMAIN ATTRIBUTION & AFFECTED SERVICES ─────────────────────┐
│ Authoritative Primary Domain: {primary_domain} (Basis: ROOT CAUSAL DRIVER)│
│                                                                        │
│ Domain Classification:                                                 │
│   ● {primary_domain:<22} PRIMARY      (Root cause origin)             │
│   ● {secondary_domain:<22} CONTRIBUTING (Impacted transport layer)     │
│   ○ {leaf_domain:<22} AFFECTED     (Customer symptom sink)         │
│                                                                        │
│ Affected Customer Services:                                            │
│   • {impacted_service}: {len(service_entities)} entities degraded ({', '.join(service_entities)})│
│                                                                        │
│ Causal Propagation Chain:                                              │
│   {causal_propagation_chain_str}                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 7: NEXT-BEST EVIDENCE & OPERATOR VALIDATION
```text
┌─ Stage 7: NEXT-BEST EVIDENCE & OPERATOR VALIDATION ──────────────────┐
│ Next-Best Evidence Priority Queue:                                     │
{formatted_evidence_requests}
│                                                                        │
│ Validation Decision:                                                   │
│   • Validation Status : {validation_status} (Audit log: {audit_log_name})│
│   • Validated by Role : {validator_role}                              │
│   • Decision Record   : {validation_decision_yaml_path}                │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 8: KNOWLEDGE GRAPH PROMOTION (H3 CONTINUOUS LEARNING)
```text
┌─ Stage 8: KNOWLEDGE GRAPH PROMOTION ─────────────────────────────────┐
│ Smart Delta Link Upsert (PromotionEngine):                             │
│   • Candidate Input  : {candidate_yaml_file}                          │
│   • SME Gate         : {validation_yaml_file} (Status: ACCEPTED)      │
│   • 8 Guardrails     : PASSED (Canonical, Non-cyclic, Provenance-backed)│
│                                                                        │
│ Injected Edge into telecombrain:                                       │
│   ● {source_entity} ──[{promoted_relation}]──► {target_entity}       │
│                                                                        │
│ Rollback Journal: Recorded ID '{promotion_id}' for reversible rollback │
│ Live MCP Sync   : Successfully emitted add_link to gbrain MCP         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Documentation Updates in `docs/Correlation/correlation.md`

Update [`docs/Correlation/correlation.md`](file:///Users/adeelarshad/kagent/docs/Correlation/correlation.md) to document:
1. The 4 Dimensions of the Correlation Engine and how they feed into Hypothesis Generation & Testing.
2. The 12-factor synthesis vector formula and deterministic Popperian falsification penalties.
3. The knowledge promotion YAML contracts and smart delta link upsert vs full snapshot.
4. The CLI reference for `fikracore demo --live -v` and shortcut `fikracore --live -v`.

---

## Verification Plan

### Automated Tests
1. Run investigation regression test suite:
   ```bash
   pytest services/agents/src/engine_stack/engines/telecom_brain/tests/test_investigation.py
   ```
2. Validate Python syntax across all modified and newly created files:
   ```bash
   python3 -c "import ast; ast.parse(open('services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py').read()); ast.parse(open('services/agents/src/engine_stack/engines/telecom_brain/investigation/verbose_presenter.py').read()); ast.parse(open('services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py').read()); print('Syntax OK')"
   ```

### Manual Verification
1. Compact live table mode:
   ```bash
   ./fikracore demo 1 --auto --delay 0.0 --live
   ```
2. Verbose step-by-step live mode:
   ```bash
   ./fikracore demo 1 --auto --delay 0.0 --live -v
   ```
3. Shortcut CLI invocation:
   ```bash
   ./fikracore --live -v
   ```
