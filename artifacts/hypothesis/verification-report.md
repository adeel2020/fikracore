# v1.4 Verification Report

- New investigation suite: 30 passed, including operational ingestion of all
  100 generated runs.
- Combined TelecomBrain, Storyteller, and correlation suites: 284 passed,
  18 skipped, 10 failed. Full output: `verification.xml`.
- Control run excluding the new investigation tests: 254 passed, 18 skipped,
  the same 10 failures. No existing reader/writer implementation was changed.
- Scoped Ruff checks passed.
- Dependency lock resolved successfully from the local cache.
- Five-case catalog-based harness: S1, S2, S3 EXPLAINED; S4 MODEL_INSUFFICIENT;
  S5 INSUFFICIENT_EVIDENCE. Method B 5/5 versus baseline 2/5 on this small,
  explicitly authored regression set only.
- Read-only live MCP discovery and SCN-001 investigation succeeded. Live result
  is MODEL_INSUFFICIENT because synthetic entity identities are missing from
  operational telecombrain. No topology was populated to make the test pass.

## Existing Failures

Storyteller's `test_gbrain_client.py` has five failing transport tests caused by
shared cached transport state in the combined test run. Existing spoken-output
expectations fail in `test_golden_references.py`, `test_phase15_e2e_matrix.py`,
and `test_reasoning.py`. Two `test_provenance.py` expectations fail for extra
field flattening and claim-taxonomy capitalization.

These failures reproduce without the new tests. They remain unresolved rather
than being hidden, skipped, or changed to make the suite green.

## Readiness

The Step 4 CLI and deterministic test adapters are implemented. Full deployment
readiness is not claimed: the earlier Step 3.5 migration dry run remains
BLOCK_MUTATION, live customer-ticket anchors remain unverified, and the existing
regression failures above remain. Production UI, topology population, Scenario
Integrity Validation, and the full RCA benchmark are later work.
