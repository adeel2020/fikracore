# Implementation Plan: Scenario-Agnostic Verbose Step-by-Step CLI (`fikracore --live -v`)

Refactor the correlation logic in `investigator.py` into modular blocks and implement clean, scenario-agnostic, step-wise box displays for `fikracore demo --live -v` (and `fikracore --live -v`). All outputs are **100% dynamically computed** from live telemetry, graph objects, and mathematical evaluations—with **zero hardcoding**.

---

## User Review Required

> [!IMPORTANT]
> - **100% Scenario-Agnostic**: Works across any scenario (`SCN-001`, `H2-SCN-001`, `H4-WI-001`, or external fixtures) by dynamically inspecting:
>   - Evidence objects (`event.source`, `event.evidence_type`, `event.event_time`, `event.polarity`, `event.service`, `event.domain`)
>   - NetworkX `DiGraph` (`nodes()`, `edges()`, `ancestors()`, `descendants()`)
>   - Candidate hypotheses and the 12-dimensional vector dictionary
>   - Knowledge gaps and residual anomaly lists
> - **Clean Visual Format**: Standardized rounded border boxes (`┌─ ... ─┐`, `│ ... │`, `└─ ... ─┘`) matching the operator terminal design.

---

## Complete Step-by-Step Execution Sequence & Output Formats

Below is the design for each stage's live output:

---

### Stage 1: EVIDENCE INGESTION & NORMALIZATION
```text
┌─ Stage 1: EVIDENCE INGESTION & NORMALIZATION ─────────────────────────┐
│ Loaded {raw_count} raw operational records from {len(sources)} independent sources          │
│                                                                        │
│ Sources:  {', '.join(f"{src} ({count})" for src, count in sources.items())}
│ Types:    {', '.join(f"{t} ({count})" for t, count in types.items())}
│ Window:   {min_time} → {max_time}  ({time_span_s:.0f}s span)               │
│                                                                        │
│ Canonicalization: {raw_count} raw → {normalized_count} canonical entities                      │
│ Freshness decay:  avg {avg_freshness:.2f} (max age: {max_age_h:.1f} hours)                       │
│ Deduplication:    {normalized_count} normalized → {collapsed_count} unified events ({dedup_pct:.0%})        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 2: KNOWLEDGE GRAPH TRAVERSAL
```text
┌─ Stage 2: KNOWLEDGE GRAPH TRAVERSAL ──────────────────────────────────┐
│ Queried {provider_name}                                       │
│                                                                        │
│ Entities traversed:  {len(traversed_entities)}                                                │
│ Edges collected:     {len(edges)} causal relationships                           │
│ Reads performed:     {reads_count}                                                 │
│ Knowledge gaps:      {len(gaps)} ({gap_status})                        │
│                                                                        │
│ Relationships discovered:                                              │
{formatted_relationships_list}
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 3: TOPOLOGY GRAPH ASSEMBLY
```text
┌─ Stage 3: TOPOLOGY GRAPH ASSEMBLY ────────────────────────────────────┐
│ Built directed causal graph from knowledge relationships              │
│                                                                        │
│ Nodes:     {graph.number_of_nodes()} (canonical entities with active telemetry)               │
│ Edges:     {graph.number_of_edges()} (forward causal dependencies)                            │
│ Direction: consumer → supplier inverted to driver → sink               │
│                                                                        │
│ Graph structure:                                                       │
{formatted_topological_chains}
└────────────────────────────────────────────────────────────────────────┘
```

---

### Stage 4: BLAST RADIUS ANALYSIS & REASONING FUNNELS
```text
┌─ Stage 4: BLAST RADIUS & CORRELATION LAYER ───────────────────────────┐
│ Partitioned {len(events)} events into operational categories                     │
│                                                                        │
│ Abnormal:    {len(abnormal)} events across {len(impacted)} entities                              │
│ Healthy:     {len(healthy)} events (checked for negative falsification)                │
│ Impacted:    {len(impacted)} entities (direct abnormal blast radius)                    │
│ Roots:       {len(impacted)} entities + {len(ancestors)} ancestors = {len(roots)} candidate roots          │
│                                                                        │
│ Impacted service: {impacted_service or 'NONE'} ({len(service_entities)} entities)                      │
│ Domains: {', '.join(detected_domains)}                          │
│                                                                        │
│ Reasoning Pathways (Correlation Funnels — Active & Dormant):           │
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

---

### Stage 5: HYPOTHESIS GENERATION (Candidate Formulation)
```text
┌─ Stage 5: HYPOTHESIS GENERATION ──────────────────────────────────────┐
│ Formulated {len(roots)} candidate hypotheses from topology ancestors          │
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

### Stage 6: HYPOTHESIS TESTING (12-Factor Synthesis Core Evaluation)
```text
┌─ Stage 6: HYPOTHESIS TESTING (12-FACTOR SYNTHESIS CORE) ───────────────┐
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

---

### Stage 7: CONVERGENCE & KNOWLEDGE GAP DETECTION
```text
┌─ Stage 7: CONVERGENCE & KNOWLEDGE GAP DETECTION ──────────────────────┐
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

### Stage 8: DOMAIN ATTRIBUTION & AFFECTED SERVICES
```text
┌─ Stage 8: DOMAIN ATTRIBUTION & AFFECTED SERVICES ─────────────────────┐
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

### Stage 9: NEXT-BEST EVIDENCE & OPERATOR VALIDATION
```text
┌─ Stage 9: NEXT-BEST EVIDENCE & OPERATOR VALIDATION ───────────────────┐
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

### Stage 10: KNOWLEDGE GRAPH PROMOTION (H3 CONTINUOUS LEARNING)
```text
┌─ Stage 10: KNOWLEDGE GRAPH PROMOTION ─────────────────────────────────┐
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

## Technical Implementation Plan

1. **`services/agents/src/engine_stack/engines/telecom_brain/investigation/investigator.py`**:
   - Refactor `investigate()` and `assess()` into clean modular helper classes:
     - `EvidenceNormalizer`
     - `CausalDiGraphBuilder`
     - `CorrelationLayer`
     - `HypothesisGenerator`
     - `SynthesisCoreAssessor`
     - `ConvergenceRanker`
     - `GapAndResidualDetector`
     - `DomainAttributionResolver`
   - Ensure `step_callback` receives rich, structured dynamic data for all 10 stages.
2. **`services/agents/src/engine_stack/engines/telecom_brain/investigation/cli.py`**:
   - Add `-v` / `--verbose` flag handling to `demo` subparser and top-level parser.
   - Implement `render_verbose_stage_card(stage_number, stage_title, lines)` with dynamic text measurements and clean border drawing.
   - Wire all 10 stages into `run_live_use_case_1(auto, delay, verbose)` using real dynamic objects from the run.
3. **`docs/Correlation/correlation.md`**:
   - Add the complete 10-stage lifecycle, the dynamic box formats, and the exact mathematical formulas.

---

## Verification Plan

### Automated Tests
1. `pytest services/agents/src/engine_stack/engines/telecom_brain/tests/test_investigation.py`
2. Python AST syntax validation on modified files.

### Manual Verification
1. Compact live execution: `./fikracore demo 1 --auto --delay 0.0 --live`
2. Verbose step-by-step execution: `./fikracore demo 1 --auto --delay 0.0 --live -v`
3. Scenario-agnostic invocation: `./fikracore --live -v`
