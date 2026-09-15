# FikraCore — Step 4.5 Live gbrain MCP Integration Smoke Test

## Purpose

This step validates that the already-tested FikraCore reasoning stack can correctly access the real `telecombrain` through the live gbrain MCP endpoint:

```text
http://localhost:3131/mcp
```

This is a **smoke test**, not a full reasoning benchmark.

The goal is to prove the live integration path works before running larger H1–H4 benchmark suites against MCP-backed knowledge.

---

# 1. Validation Question

Answer:

> Can FikraCore connect to the real gbrain MCP, resolve live `telecombrain` entities, traverse relationships, and use that live knowledge through the existing KnowledgeProvider without violating epistemic boundaries?

The smoke test should validate this chain:

```text
Live gbrain MCP
      ↓
MCP Client
      ↓
GbrainTelecomBrainProvider
      ↓
CanonicalResolver
      ↓
FikraCore Reasoning Stack
```

---

# 2. What This Step Does NOT Revalidate

This step does not invalidate or replace H1–H4.

H1–H4 remain valid for the simulator / frozen operational-knowledge path already tested.

This step validates only:

```text
live MCP connectivity
live telecombrain retrieval
canonical resolution
live graph traversal
provider integration
basic reasoning compatibility
```

---

# 3. Smoke-Test Philosophy

Do not start with the full benchmark.

Validate the dependency chain incrementally:

```text
MCP reachable
→ authentication works
→ MCP session works
→ tools are discoverable
→ known pages can be read
→ graph relations can be traversed
→ canonical aliases resolve
→ KnowledgeProvider consumes live data
→ reasoning consumes KnowledgeProvider correctly
```

If a failure occurs, this sequence makes the fault easy to isolate.

---

# 4. Preconditions

Before running the smoke test confirm:

```text
gbrain is running
MCP endpoint is listening on localhost:3131
telecombrain is the intended live brain
valid MCP token is available if authentication is enabled
FikraCore codebase is available
existing H1–H4 regression suite remains green
```

Expected MCP endpoint:

```text
http://localhost:3131/mcp
```

---

# 5. Important MCP Transport Note

The gbrain MCP endpoint is not expected to behave like a normal REST endpoint.

A request such as:

```bash
curl -i http://localhost:3131/mcp
```

may return:

```text
405 Method Not Allowed
```

This alone does **not** mean MCP is broken.

The MCP endpoint requires the supported MCP request/session flow.

---

# 6. Environment Variables

Use environment variables rather than hard-coding secrets.

Example:

```bash
export GBRAIN_MCP_URL="http://localhost:3131/mcp"
export GBRAIN_MCP_TOKEN="<your-token>"
```

Verify:

```bash
echo "$GBRAIN_MCP_URL"
```

Do not print the token into logs, reports, screenshots, or benchmark artifacts.

---

# 7. Smoke Test 1 — MCP Endpoint Reachability

Confirm the service is listening.

Example:

```bash
curl -i http://localhost:3131/mcp
```

Acceptable indication:

```text
HTTP response received from localhost:3131
```

A `405 Method Not Allowed` can still prove the endpoint is reachable.

Fail if:

```text
connection refused
timeout
DNS/network failure
```

---

# 8. Smoke Test 2 — MCP Authentication / Session

Use the same MCP client flow expected by the FikraCore provider.

Validate that:

```text
token is accepted
MCP session can be initialized
requests receive valid MCP responses
```

Do not treat an unauthenticated endpoint response as sufficient proof.

Expected result:

```text
MCP_AUTH = PASS
MCP_SESSION = PASS
```

---

# 9. Smoke Test 3 — Tool Discovery

Confirm that the live MCP exposes the tools required by FikraCore.

Expected tools include, where available:

```text
get_page
list_pages
search
query
get_links
get_backlinks
traverse_graph
get_active_schema_pack
list_schema_packs
schema_stats
schema_lint
schema_graph
schema_explain_type
```

Do not require administrative mutation tools for this smoke test.

The test is read-only.

---

# 10. Smoke Test 4 — Active Schema

Call:

```text
get_active_schema_pack
```

Record:

```text
active schema pack
page-type count
link-type count
source tier
```

Expected from the current environment, if unchanged:

```text
mobile-core@0.1.0+2eea5e14
```

Do not fail solely because the version changed.

Fail only if:

```text
schema cannot be retrieved
schema is invalid
required telecom types are unavailable
```

---

# 11. Smoke Test 5 — Read Known telecombrain Pages

Select a small set of known entities already present in `telecombrain`.

Suggested examples:

```text
domains/mobile-core/networks/lte/functions/mme-01

domains/mobile-core/networks/ps/functions/pgw-01

domains/transport/functions/sgi-edge-01

tickets/mobile-core/tt-984210
```

Use:

```text
get_page
```

Verify for each:

```text
page exists
type is populated
slug is correct
content is readable
no unexpected deletion state
```

Do not require every suggested slug if the live brain has evolved.

Use at least 3 known live entities.

---

# 12. Smoke Test 6 — Read Links

For at least one known entity, call:

```text
get_links
get_backlinks
```

Verify:

```text
links are returned
link targets exist
link types are meaningful
direction is preserved
```

Record at least one relationship path.

---

# 13. Smoke Test 7 — Graph Traversal

Use:

```text
traverse_graph
```

against a known entity.

Recommended:

```text
depth = 1 or 2
direction = both
```

Validate:

```text
starting entity resolves
neighbors are returned
relationship directions are preserved
no unexpected traversal errors
```

Do not start with deep traversal.

---

# 14. Smoke Test 8 — Canonical Resolution

Verify the FikraCore `CanonicalResolver` against live MCP-backed entities.

Test both:

```text
canonical slug
legacy / alias slug
```

Expected:

```text
requested slug
→ CanonicalResolver
→ canonical slug
→ MCP page
```

Example pattern:

```text
legacy:
mobile-core/network-functions/mme-01

canonical:
domains/mobile-core/networks/lte/functions/mme-01
```

Use actual mappings from the current resolver.

Do not invent aliases that are not present.

---

# 15. Smoke Test 9 — Live KnowledgeProvider

Instantiate the actual MCP-backed provider:

```text
GbrainTelecomBrainProvider
```

Verify the provider can:

```text
fetch entity
fetch relationships
traverse dependencies
return canonical entity representation
preserve provenance
```

The reasoning engine should not need to know whether knowledge came from:

```text
snapshot provider
or
live MCP provider
```

That abstraction is part of the architecture.

---

# 16. Smoke Test 10 — Provider Parity

Select one known entity and compare:

```text
snapshot/in-memory provider
vs
live MCP provider
```

Compare:

```text
canonical entity ID
display name
entity type
direct relationships
relationship direction
```

Differences are allowed if the live brain has newer knowledge.

Every difference must be explainable.

---

# 17. Smoke Test 11 — One H1 Live Investigation

Run one simple H1-style investigation using:

```text
KnowledgeProvider = live gbrain MCP
```

Do not use Hidden Truth as an input.

Validate that the engine can:

```text
retrieve relevant live knowledge
generate hypotheses
rank hypotheses
produce explanation/provenance
complete without provider-specific failure
```

This is a compatibility smoke test, not an H1 accuracy benchmark.

---

# 18. Smoke Test 12 — One H2 Live Knowledge-Gap Check

Run one controlled H2-style case against live MCP knowledge.

Validate that FikraCore can distinguish:

```text
known dependency
missing dependency
insufficient evidence
```

If the live brain lacks a relation required to explain observations, expected behavior may be:

```text
MODEL_INSUFFICIENT
```

Do not inject Hidden Truth into the MCP provider.

---

# 19. Smoke Test 13 — One H4 Live What-If

Use a known live entity and run one simple What-If.

Example human-facing command:

```bash
fikracore predict "MPLS Edge Router Failure"
```

or use another scenario that actually resolves against the current live `telecombrain`.

Validate:

```text
scenario resolves
entity resolves through live MCP
forward dependency traversal works
blast radius uses only live-known relationships
every propagation path has provenance
no unsupported path is invented
```

---

# 20. Smoke Test 14 — Mark / Zaki Grounding

For the same H1 or H4 run, verify Mark / Zaki consumes the same structured state.

Example question:

```text
Why is this service affected?
```

Expected:

```text
Mark / Zaki explanation
→ references current live investigation state
→ uses human-readable names
→ preserves canonical provenance
```

Forbidden:

```text
separate graph lookup that contradicts simulator state
invented dependency
Hidden Truth access
```

---

# 21. Smoke Test 15 — Hidden Truth Boundary

Explicitly verify:

```text
Hidden Truth
→ evaluator only
```

Inspect:

```text
MCP provider inputs
MCP request payloads
reasoning inputs
Mark / Zaki context
UI presentation state
```

Expected:

```text
0 Hidden Truth leakage
```

---

# 22. Suggested Smoke-Test CLI

Add a dedicated command:

```bash
fikracore inspect mcp
```

or:

```bash
fikracore inspect live-knowledge
```

Recommended behavior:

```text
check endpoint
check auth/session
discover tools
read schema
read known entities
test links
test traversal
test canonical resolver
test KnowledgeProvider
report PASS / FAIL
```

For a deeper compatibility test:

```bash
fikracore inspect live-knowledge --reasoning
```

This may additionally run the selected H1/H2/H4 smoke cases.

---

# 23. Machine-Readable Result

Generate:

```text
artifacts/integration/mcp-smoke-test.json
```

Recommended structure:

```json
{
  "endpoint": "http://localhost:3131/mcp",
  "connectivity": "PASS",
  "authentication": "PASS",
  "session": "PASS",
  "tool_discovery": "PASS",
  "schema": "PASS",
  "page_read": "PASS",
  "links": "PASS",
  "traversal": "PASS",
  "canonical_resolution": "PASS",
  "knowledge_provider": "PASS",
  "provider_parity": "PASS",
  "h1_live_smoke": "PASS",
  "h2_live_smoke": "PASS",
  "h4_live_smoke": "PASS",
  "mark_zaki_grounding": "PASS",
  "hidden_truth_leakage": 0
}
```

---

# 24. Human-Readable Report

Generate:

```text
artifacts/integration/mcp-smoke-test.md
```

Suggested summary:

```text
Live gbrain MCP Integration

Endpoint: http://localhost:3131/mcp

Connectivity          PASS
Authentication        PASS
MCP Session           PASS
Tool Discovery        PASS
Schema Read           PASS
Known Page Read       PASS
Links / Backlinks     PASS
Graph Traversal       PASS
Canonical Resolution  PASS
Live KnowledgeProvider PASS
Provider Parity       PASS
H1 Live Smoke         PASS
H2 Live Smoke         PASS
H4 Live Smoke         PASS
Mark / Zaki Grounding PASS
Hidden Truth Leakage  0

Overall:
LIVE_MCP_SMOKE_SUPPORTED
```

---

# 25. Failure Classification

Use explicit failure categories:

```text
MCP_UNREACHABLE
MCP_AUTH_FAILED
MCP_SESSION_FAILED
MCP_TOOL_MISSING
SCHEMA_READ_FAILED
PAGE_NOT_FOUND
TRAVERSAL_FAILED
CANONICAL_RESOLUTION_FAILED
PROVIDER_FAILED
PROVIDER_PARITY_MISMATCH
REASONING_PROVIDER_ERROR
MARK_ZAKI_STATE_MISMATCH
HIDDEN_TRUTH_LEAKAGE
```

This prevents integration failures from being misclassified as reasoning failures.

---

# 26. Read-Only Safety

This smoke test must remain read-only.

Do not call:

```text
schema_apply_mutations
add_link
delete
overwrite
automatic promotion
```

No live `telecombrain` mutation is required.

---

# 27. Acceptance Gate

The smoke test is successful when:

```text
[ ] MCP endpoint is reachable
[ ] authentication/session works
[ ] required read tools are available
[ ] active schema is readable
[ ] known pages can be retrieved
[ ] links/backlinks can be retrieved
[ ] graph traversal succeeds
[ ] CanonicalResolver works with live entities
[ ] GbrainTelecomBrainProvider works
[ ] live/snapshot differences are explainable
[ ] one H1 live smoke test succeeds
[ ] one H2 live smoke test succeeds
[ ] one H4 live what-if succeeds
[ ] Mark / Zaki consumes the same live state
[ ] Hidden Truth leakage remains zero
```

---

# 28. Smoke-Test Decision

Classify:

```text
LIVE_MCP_SMOKE_SUPPORTED
LIVE_MCP_SMOKE_PARTIALLY_SUPPORTED
LIVE_MCP_SMOKE_NOT_SUPPORTED
```

This is an integration decision, not a replacement for H1–H4.

---

# 29. What Comes Next

If the smoke test passes:

```text
Smoke Test
    ↓
Selected live parity scenarios
    ↓
Full MCP-backed benchmark
    ↓
Step 5 unified experience
```

The next validation should compare the existing benchmark knowledge path against the real MCP-backed `telecombrain`.

---

# Final Principle

> **First prove the live knowledge path works. Then benchmark the reasoning stack through it.**

H1–H4 proved the reasoning architecture.

Step 4.5 proves that the same architecture can consume the real `telecombrain` through gbrain MCP.
