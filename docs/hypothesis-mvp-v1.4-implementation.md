# Hypothesis / Investigation MVP v1.4

Implementation: `services/agents/src/engine_stack/engines/telecom_brain/investigation/`.
This is Step 4: a CLI-first operational reasoning engine in the existing agent
service. The v1.4 prompt explicitly excludes a production simulator UI from this
step. No topology ingestion, new service, or second operational brain is added.

## Usage

Run from the repository root using its existing environment (Python 3.11+,
Pydantic 2, NetworkX 3, PyYAML). This matches the repository's Python requirement;
the prompt's preferred Python 3.12 is not made mandatory.

```bash
PYTHONPATH=services/agents/src .venv/bin/python -m engine_stack.engines.telecom_brain.investigation.cli investigate \
  services/agents/src/engine_stack/engines/telecom_brain/simulator/runs/RUN-SCN-001-L1-SEED-42001 \
  --output artifacts/hypothesis/live-scn-001.json
```

The live provider uses the configured gbrain MCP endpoint and reads credentials
from the existing environment configuration, including `backend/.env`. Tokens
are not included in output. It discovers tool contracts at connection time.
Transport errors fail explicitly; missing pages become knowledge gaps.

Use `--snapshot /absolute/path/to/snapshot.json` for an explicitly selected frozen
operational knowledge snapshot. Its required fields are `brain: "telecombrain"`,
`snapshot_version`, `pages`, and `relationships`. Pages have exact `slug`
identities. Relationships use `relationship_id`, `source`, `target`, `link_type`,
`state`, `confidence`, and optional `provenance`. This is a runtime/test adapter,
not a second production brain. Do not export the simulator world into it.

```bash
PYTHONPATH=services/agents/src .venv/bin/python scripts/benchmark_hypothesis_mvp.py
PYTHONPATH=services/agents/src .venv/bin/python -m engine_stack.engines.telecom_brain.investigation.cli validate-candidate \
  artifacts/hypothesis/benchmark/S4-investigation.json REL-001 \
  --decision validate --validator operator-name --reason "Independent path capture reviewed" \
  --output artifacts/hypothesis/decisions/REL-001-review.json
```

Validation creates an immutable local audit record containing the candidate,
supporting evidence, validator, decision, reason, and timestamp. It does not
publish an edge. Future promotion must consume that governance record through
a separately implemented knowledge-write workflow. Rejection uses
`--decision reject`.

`evaluate RESULT --expected-root CANONICAL_ID --output REPORT` invokes the
separate examiner; multiple roots can be supplied by repeating the option.
`--unknown-correct` evaluates an abstention case. Expected answers are never
arguments to `investigate`.

## Behavior

- Strict operational contracts accept the eight existing evidence streams and
  optional JSON/YAML source profiles. All 100 existing generated runs parse.
- Native source names, canonical identities, evidence IDs, event/ingestion
  timestamps, confidence, freshness, and observed/inferred state are preserved.
- Canonical-first reads reuse the existing mapping resolver. Missing canonical
  targets are recorded; surviving legacy physical pages remain readable.
  Exact operational aliases can resolve vendor names; fuzzy leaf-name merges
  are not used.
- Alarm flood reduction retains duplicate IDs. Coverage weights affected
  entities rather than alarm counts. Explicitly unrelated service evidence is
  recorded separately.
- Local directed reasoning uses operational dependency edges, reversing
  consumer-to-supplier dependencies for propagation. Undirected connectivity
  alone does not establish causal direction. Stale, rejected, and candidate
  topology are excluded from authoritative reasoning paths.
- Competing single-root and two-root explanations have explicit assumptions,
  twelve score dimensions, support, contradiction, missing evidence, relationship
  citations, and failed-assumption records. Scores are heuristic, not calibrated
  probabilities. Current explanation granularity is entity-level impairment.
- Negative evidence can falsify local-fault assumptions. A normal CPU metric
  does not refute a transport-path impairment. Missing expected alarms count
  against a hypothesis only when operational knowledge explicitly says
  monitoring coverage is complete.
- Residual impact and unknown observed-path adjacency trigger Discovery Mode.
  Relationship proposals remain CANDIDATE. The six terminal states distinguish
  explanation, partial explanation, insufficient evidence, conflict, unresolved
  evidence, and model insufficiency.
- At most two evidence requests are ranked using estimated information gain,
  cost, latency, risk, reliability, and availability. This MVP completes one
  evidence pass. To test new observations, rerun with the enlarged evidence set;
  it does not autonomously collect telemetry or execute remediation.
- Run output records mapping hash, provider identity, snapshot version/hash when
  available, page-content hashes, operational relationships used, input hashes,
  evidence, provenance, and diagnostic metrics.

## Boundary

The operational engine never imports its evaluator. Its input contract has no
world, scenario-definition, expected-answer, or `operational_graph_path` field.
File ingestion is confined to the designated operational directory and resolves
symlinks before access. Hidden directories and nested evaluator-label keys are
rejected. Snapshot adapters reject hidden-world document shapes.

These are structural application boundaries, not an operating-system sandbox
or a guarantee that arbitrary untrusted prose cannot contain an answer. Operational
fixture integrity remains Step 5's responsibility. The existing generator emits
some descriptive change/recovery fields referring to synthetic causality; these
fields are not projected into the evidence contract or used in scoring.

Existing Storyteller, ticket, correlation, learning, and asset readers/writers
are unchanged by this implementation. New investigation references use the
canonical resolver. No live page, story, ticket, schema, or topology was modified.

## Verification And Limits

The five-case harness uses actual SCN-001 operational evidence with independently
authored operational test knowledge and documented variations:

| Case | Variation | Result |
| --- | --- | --- |
| S1 | Local transport fault evidence | EXPLAINED |
| S2 | Transport-to-PS propagation | EXPLAINED |
| S3 | Duplicates, unrelated early alarm/change, reversed input order | EXPLAINED |
| S4 | Missing operational dependency | MODEL_INSUFFICIENT |
| S5 | Only one observation | INSUFFICIENT_EVIDENCE |

The small harness records Method B correct on 5/5 and the earliest-severe-alarm
baseline correct on 2/5. This is an authored regression set, not evidence of
statistically established superiority or full 100-scenario RCA accuracy.
Full Scenario Integrity Validation and the comprehensive Benchmark Evaluator
remain subsequent steps.

The read-only live SCN-001 investigation returned MODEL_INSUFFICIENT because
the synthetic entity IDs are absent from current telecombrain. This is an
explicit gap, not a successful live RCA. The provider's verified response
contract includes `isError` plus `error: "page_not_found"` for absent pages;
other errors remain failures.

Step 3.5's existing canonicalization dry-run is still BLOCK_MUTATION, with
customer-ticket regression anchors missing. The local compatibility layer is
usable, but this implementation does not claim the migration prerequisite or
live ticket-journey validation is complete.

Broader tests reproduce ten existing failures even with the new investigation
tests excluded: five shared gbrain transport-state tests, three Storyteller
spoken-output tests, and two provenance contract tests. They are outside this
change. See `artifacts/hypothesis/` for live contracts, live investigation,
benchmark output, and final verification report.
