# FikraCore — Step 4.7 Knowledge Inventory & Coverage Validation

## Purpose

Step 4.7 validates that FikraCore can accurately inspect, summarize, and assess the live knowledge currently stored in `telecombrain`.

Step 4.5 proved that the live gbrain MCP integration works.

Step 4.6 proved that H1–H4 reasoning preserves parity when operational knowledge is accessed through the live gbrain MCP.

Step 4.7 answers the next operational question:

> **What does `telecombrain` actually know right now, how complete is that knowledge, and where are the important gaps?**

This step is read-only.

It does not modify `telecombrain`.

It does not replace H2 knowledge-gap reasoning.

Instead, it provides a systematic **knowledge inventory and coverage view** across the live brain.

---

# 1. Validation Question

Validate:

> Can FikraCore inspect the live `telecombrain` and produce an accurate, human-readable inventory of its entities, relationships, domains, knowledge states, coverage, sparse areas, stale areas, unresolved aliases, and structural gaps?

---

# 2. Relationship to Previous Steps

```text
H1 — Reason
H2 — Recognize the Unknown
H3 — Learn
H4 — Predict
        ↓
Step 4.5 — Live MCP Smoke
        ↓
Step 4.6 — Live MCP Parity
        ↓
Step 4.7 — Knowledge Inventory & Coverage Validation
        ↓
Step 5 — Unified Capability & Experience Layer
```

---

# 3. Why Step 4.7 Is Needed

The current command:

```bash
fikracore inspect knowledge
```

was found to return an MCP integration-health summary rather than an actual live knowledge inventory.

That output contains fields such as:

```text
checks_passed
parity_benchmark_status
hidden_truth_leakage
report_path
```

Those are useful integration metrics, but they do not answer:

```text
How many pages exist?
How many relationships exist?
Which domains are represented?
Which services are represented?
Which network functions are represented?
Which knowledge types dominate?
Where are the sparse areas?
Which entities are orphaned?
Which aliases do not resolve?
Which relationships are missing?
Which knowledge is stale?
```

Step 4.7 separates **integration health** from **knowledge inventory**.

---

# 4. Command Separation

Use:

```bash
fikracore inspect live-knowledge
```

for:

```text
MCP connectivity
MCP authentication
tool discovery
schema status
provider status
smoke-test status
parity status
```

Use:

```bash
fikracore inspect knowledge
```

for:

```text
live telecombrain inventory
coverage
distribution
knowledge health
```

Use:

```bash
fikracore inspect knowledge --gaps
```

for:

```text
coverage gaps
orphans
sparse areas
missing relationships
unresolved aliases
stale knowledge
```

---

# 5. Core Architecture

```text
Live gbrain MCP
      ↓
telecombrain
      ↓
Knowledge Inventory Collector
      ↓
Knowledge Coverage Analyzer
      ↓
Human-Readable Report
      ↓
CLI / Simulator UI / Mark-Zaki
```

---

# 6. Read-Only Rule

Step 4.7 must remain read-only.

Do not call:

```text
add_link
delete
overwrite
schema mutation
knowledge promotion
automatic repair
```

Step 4.7 may identify gaps and generate recommendations, but it must not change the brain automatically.

---

# 7. Required MCP Capabilities

Use live MCP tools such as:

```text
list_pages
schema_stats
schema_graph
search
query
get_page
get_links
get_backlinks
traverse_graph
get_active_schema_pack
```

Use the exact available tool names from the live MCP server.

Do not assume unsupported tools.

---

# 8. Primary CLI

Implement:

```bash
fikracore inspect knowledge
```

Expected output categories:

```text
brain identity
schema identity
total pages
total links
page-type distribution
link-type distribution
domain distribution
service distribution
network-function distribution
incident/ticket/evidence distribution
knowledge-state distribution
orphan count
unresolved alias count
stale knowledge count
coverage summary
```

---

# 9. Domain-Specific Inspection

Support:

```bash
fikracore inspect knowledge --domain "Mobile Core"
```

or:

```bash
fikracore inspect knowledge --domain mobile-core
```

Expected output:

```text
entities in domain
services in domain
network functions
incidents
tickets
evidence
hypotheses
relationships
knowledge states
coverage score
gaps
```

---

# 10. Type-Specific Inspection

Support:

```bash
fikracore inspect knowledge --type incident
fikracore inspect knowledge --type evidence
fikracore inspect knowledge --type domain-function
fikracore inspect knowledge --type ticket-journey
```

Expected:

```text
count
top entities
domain distribution
relationship distribution
coverage
```

---

# 11. Gap Inspection

Support:

```bash
fikracore inspect knowledge --gaps
```

Expected gap classes:

```text
ORPHAN_ENTITY
UNRESOLVED_ALIAS
MISSING_RELATIONSHIP
SPARSE_DOMAIN
SPARSE_SERVICE
STALE_KNOWLEDGE
CANDIDATE_ONLY_KNOWLEDGE
INFERRED_ONLY_KNOWLEDGE
UNVALIDATED_RELATIONSHIP
INCOMPLETE_CROSS_DOMAIN_COVERAGE
INCOMPLETE_SERVICE_MAPPING
```

---

# 12. Orphan Inspection

Support:

```bash
fikracore inspect knowledge --orphans
```

An orphan may be defined as:

```text
entity with no meaningful operational relationship
```

Do not classify schema-only or intentionally standalone metadata pages as operational orphans without explicit rules.

---

# 13. Coverage Inspection

Support:

```bash
fikracore inspect knowledge --coverage
```

Coverage should be reported by:

```text
domain
service
entity type
relationship type
knowledge state
```

Example:

```text
Mobile Core       HIGH
Transport         MEDIUM
IMS               MEDIUM
OCS               LOW
OSS/BSS           LOW
```

Coverage labels must be based on explicit measurable rules.

---

# 14. Coverage Scoring

Do not invent an opaque score.

Use a transparent formula.

Possible dimensions:

```text
entity coverage
relationship coverage
service mapping coverage
evidence coverage
validated knowledge coverage
cross-domain dependency coverage
```

Example:

```text
coverage_score =
  25% entity coverage
+ 25% relationship coverage
+ 20% service mapping coverage
+ 15% evidence coverage
+ 15% validated knowledge coverage
```

If a score is introduced, document the formula and denominators.

---

# 15. Knowledge States

Where supported, classify knowledge as:

```text
CONFIRMED
INFERRED
CANDIDATE
REJECTED
STALE
UNKNOWN
```

Do not assign a state if the underlying data does not support it.

If the live schema lacks explicit knowledge-state metadata, report:

```text
STATE_NOT_AVAILABLE
```

instead of guessing.

---

# 16. Human-Readable Naming

All operator-facing output must prefer human-readable names.

Examples:

```text
Transport Router-01
MPLS Edge Router-07
Data Center Gateway-01
User Plane Function-01
Packet Gateway-01
```

Canonical IDs should remain available in technical detail.

---

# 17. Human-Readable Relationships

Present:

```text
DEPENDS_ON → Depends on
ROUTES_THROUGH → Routes through
HOSTED_ON → Hosted on
SUPPORTS_SERVICE → Supports service
MONITORED_BY → Monitored by
FAILS_OVER_TO → Fails over to
```

Use the shared naming/presentation resolver.

---

# 18. Knowledge Inventory Data Model

Recommended internal result:

```json
{
  "brain": "telecombrain",
  "schema": {},
  "summary": {},
  "page_types": {},
  "link_types": {},
  "domains": {},
  "services": {},
  "entities": {},
  "knowledge_states": {},
  "coverage": {},
  "gaps": [],
  "provenance": {}
}
```

---

# 19. Summary Output

Recommended human-readable CLI summary:

```text
FikraCore Knowledge Inventory

Brain: telecombrain
Schema: mobile-core@0.1.0+2eea5e14

Pages: 132
Relationships: 248

Domains:
  Mobile Core        46 entities
  Transport          18 entities
  IMS                14 entities
  OCS                10 entities

Knowledge Types:
  Network Functions  38
  Services           21
  Incidents          17
  Evidence           26
  Hypotheses         12
  Tickets             8

Knowledge Health:
  Confirmed          79%
  Candidate           8%
  Stale               4%
  Orphans             3

Top Gaps:
  Transport ↔ Mobile Core dependency coverage
  IMS failover relationships
  OCS service-impact mapping
```

The numbers above are illustrative only.

The implementation must use live MCP results.

---

# 20. Pagination Safety

Knowledge inventory must enumerate all pages, not only the first MCP response page.

If `list_pages` is paginated:

```text
follow next cursor
until no cursor remains
```

Do not treat the first page as the entire brain.

This is critical.

---

# 21. Link Counting

Do not double-count relationships.

Use stable identity such as:

```text
source
relationship type
target
```

If the same logical edge is returned via both:

```text
get_links
get_backlinks
```

count it once.

---

# 22. Domain Detection

Prefer explicit domain metadata or canonical paths.

Example:

```text
domains/mobile-core/...
domains/transport/...
domains/ims/...
```

Avoid inferring domains from free text if canonical metadata exists.

---

# 23. Service Detection

Use explicit service pages and relationships where available.

Examples:

```text
SUPPORTS_SERVICE
SERVES
DEPENDS_ON
```

Do not assume every network function corresponds to one service.

---

# 24. Cross-Domain Coverage

Measure known relationships across domain boundaries.

Examples:

```text
Mobile Core → Transport
Mobile Core → OCS
IMS → Transport
OSS/BSS → Mobile Core
Cloud/NFVI → Mobile Core
```

Report:

```text
known cross-domain links
sparse cross-domain boundaries
unlinked expected boundaries
```

Expected boundaries must come from the Reference Operator Model or explicit configuration, not generic assumptions.

---

# 25. Knowledge Density

Optional metric:

```text
relationships per entity
```

Use only as a descriptive metric.

Do not interpret high density automatically as high-quality knowledge.

---

# 26. Orphan Rules

An entity can be considered an operational orphan when:

```text
it has no meaningful incoming or outgoing operational relationship
```

Exclude:

```text
schema metadata
documentation-only pages
root index pages
intentionally standalone reference pages
```

---

# 27. Unresolved Alias Detection

Use the canonical resolver.

Track:

```text
alias
requested identity
resolution result
ambiguity
missing canonical target
```

Report:

```text
resolved aliases
ambiguous aliases
unresolved aliases
```

---

# 28. Stale Knowledge Detection

Where timestamps exist, define staleness explicitly.

Example:

```text
STALE if not validated or updated for > N days
```

The threshold must be configurable.

Do not hard-code a universal telecom staleness threshold.

---

# 29. Candidate Knowledge

Candidate knowledge should be listed separately from confirmed operational knowledge.

Example:

```text
Candidate Relationships: 12
Validated Relationships: 87
Rejected Relationships: 4
```

Do not include candidate knowledge in confirmed coverage without clear labeling.

---

# 30. Evidence Coverage

Measure whether operational entities/services have linked evidence such as:

```text
alarms
metrics
logs
traces
tickets
change records
```

Example:

```text
Mobile Core service evidence coverage: 82%
Transport service evidence coverage: 61%
```

Only calculate if denominators are explicitly defined.

---

# 31. Incident Knowledge

Summarize:

```text
incident count
incidents by domain
incidents by service
incidents with confirmed root cause
incidents with unresolved outcome
incidents linked to changes
incidents linked to evidence
```

---

# 32. Ticket Knowledge

Summarize:

```text
ticket-journey count
tickets by domain
tickets by service
tickets with incident correlation
tickets with provisioning evidence
tickets with resolution outcome
```

---

# 33. Hypothesis Knowledge

Summarize:

```text
hypotheses
supported hypotheses
rejected hypotheses
validated root causes
candidate patterns
```

Do not conflate historical hypotheses with current truth.

---

# 34. Learning Knowledge

For H3-related knowledge summarize:

```text
candidate learning units
validated learning units
promoted knowledge
rejected learning units
stale learned knowledge
reuse count
```

---

# 35. Service Topology Coverage

For each important service, where possible show:

```text
service
supporting domains
supporting functions
transport path
cloud/NFVI dependency
charging dependency
authentication dependency
monitoring dependency
```

Missing sections should be shown as gaps, not invented.

---

# 36. Knowledge Health Summary

Provide:

```text
Healthy
Needs Attention
Critical Gaps
```

with transparent reasons.

Example:

```text
Needs Attention:
Transport-to-Mobile-Core dependency coverage below threshold.
```

Do not generate generic warnings with no evidence.

---

# 37. Technical vs Simple View

Support:

```bash
fikracore inspect knowledge
```

for concise operator-readable output.

Optionally support:

```bash
fikracore inspect knowledge --technical
```

for:

```text
canonical IDs
raw page types
raw link types
MCP tool provenance
timestamps
internal counters
```

---

# 38. JSON Output

Support:

```bash
fikracore inspect knowledge --json
```

Recommended artifact:

```text
artifacts/knowledge-inventory/knowledge-inventory.json
```

---

# 39. Markdown Report

Generate:

```text
artifacts/knowledge-inventory/knowledge-inventory.md
```

Include:

```text
executive summary
brain/schema identity
entity counts
relationship counts
domain distribution
service distribution
knowledge-state distribution
coverage
top gaps
orphans
unresolved aliases
stale knowledge
recommendations
```

---

# 40. Gap Artifact

Generate:

```text
artifacts/knowledge-inventory/knowledge-gaps.json
artifacts/knowledge-inventory/knowledge-gaps.md
```

---

# 41. Coverage Artifact

Generate:

```text
artifacts/knowledge-inventory/coverage-report.json
artifacts/knowledge-inventory/coverage-report.md
```

---

# 42. CLI Examples

```bash
fikracore inspect knowledge

fikracore inspect knowledge --domain mobile-core

fikracore inspect knowledge --type incident

fikracore inspect knowledge --gaps

fikracore inspect knowledge --orphans

fikracore inspect knowledge --coverage

fikracore inspect knowledge --json

fikracore inspect knowledge --technical
```

---

# 43. Mark / Zaki Integration

Mark / Zaki should be able to answer:

```text
What does FikraCore know about Mobile Core?
What services do you know?
How complete is Transport knowledge?
Where are the biggest knowledge gaps?
Do you know the path between Mobile Core and Transport?
Which knowledge is stale?
Which entities are unlinked?
What did you learn recently?
```

Answers must come from the same structured inventory state.

---

# 44. Simulator UI Readiness

Step 4.7 should prepare a structured payload suitable for a future Step 5 UI.

Suggested widgets:

```text
Knowledge Summary
Domain Coverage
Service Coverage
Knowledge States
Top Gaps
Orphans
Stale Knowledge
Cross-Domain Coverage
```

---

# 45. Do Not Confuse H2 and Step 4.7

H2 answers:

> Why can I not explain this specific observation?

Step 4.7 answers:

> What knowledge exists across the brain overall, and where is coverage weak?

They are complementary.

---

# 46. Integration with H2

Step 4.7 may reuse H2 gap classes where appropriate.

Example:

```text
MISSING_DEPENDENCY_EDGE
UNKNOWN_ENTITY
INCOMPLETE_TELEMETRY
```

But Step 4.7 should not force incident-specific H2 logic onto every inventory gap.

---

# 47. Reference Operator Comparison

Optionally compare `telecombrain` against the Reference Operator Model.

This can answer:

```text
Which expected domains are represented?
Which expected service chains are incomplete?
Which dependency classes are missing?
```

Important:

```text
Reference Operator Model ≠ Hidden Truth
```

This comparison is allowed only if the Reference Operator Model is used as an explicit coverage reference, not as an unseen truth source.

---

# 48. Knowledge Coverage States

Suggested labels:

```text
WELL_COVERED
PARTIALLY_COVERED
SPARSE
UNKNOWN
```

These should be based on documented rules.

---

# 49. Failure Classes

Use explicit failure classes:

```text
KNOWLEDGE_INVENTORY_MCP_FAILURE
KNOWLEDGE_INVENTORY_PAGINATION_FAILURE
KNOWLEDGE_INVENTORY_SCHEMA_FAILURE
KNOWLEDGE_INVENTORY_CANONICALIZATION_FAILURE
KNOWLEDGE_INVENTORY_LINK_COUNT_FAILURE
KNOWLEDGE_INVENTORY_ALIAS_FAILURE
KNOWLEDGE_INVENTORY_COVERAGE_FAILURE
```

---

# 50. Empty Brain Safety

Do not interpret MCP failure as:

```text
0 pages
```

Distinguish:

```text
EMPTY_VALID_BRAIN
MCP_REQUEST_FAILED
AUTH_FAILED
PAGINATION_FAILED
```

---

# 51. Provenance

Every aggregate should retain provenance to live MCP results.

Example:

```text
source = gbrain-mcp
brain = telecombrain
schema = mobile-core@...
retrieved_at = ...
```

Where useful, retain page/link source references.

---

# 52. Test Requirements

Add tests for at least:

```text
test_inspect_knowledge_uses_inventory_not_smoke_summary
test_inventory_paginates_all_pages
test_inventory_counts_pages_correctly
test_inventory_deduplicates_links
test_domain_distribution
test_type_distribution
test_orphan_detection
test_alias_resolution_summary
test_stale_knowledge_detection
test_candidate_vs_confirmed_separation
test_gap_summary
test_coverage_summary
test_json_output
test_mark_zaki_uses_inventory_state
test_mcp_failure_not_reported_as_empty_brain
```

---

# 53. Acceptance Gate

Step 4.7 is complete when:

```text
[ ] inspect knowledge returns actual live brain inventory
[ ] live-knowledge remains integration-health command
[ ] all pages are enumerated with pagination
[ ] all relevant relationships are counted without duplication
[ ] page types are summarized
[ ] link types are summarized
[ ] domains are summarized
[ ] services are summarized where supported
[ ] network functions are summarized
[ ] incidents/tickets/evidence/hypotheses are summarized
[ ] knowledge states are summarized where supported
[ ] orphans are identified
[ ] unresolved aliases are identified
[ ] stale knowledge is identified where timestamps support it
[ ] coverage is calculated using explicit rules
[ ] gaps are reported without inventing missing topology
[ ] Mark / Zaki can consume the same inventory state
[ ] JSON and Markdown artifacts are generated
[ ] no live brain mutation occurs
[ ] Hidden Truth leakage remains zero
[ ] regression suite remains green
```

---

# 54. Step 4.7 Decision

Classify:

```text
KNOWLEDGE_INVENTORY_SUPPORTED
KNOWLEDGE_INVENTORY_PARTIALLY_SUPPORTED
KNOWLEDGE_INVENTORY_NOT_SUPPORTED
```

---

# 55. Suggested Decision Logic

### KNOWLEDGE_INVENTORY_SUPPORTED

Use when:

```text
inventory accurately represents the complete live brain
pagination is complete
counts are reproducible
coverage logic is transparent
gaps are traceable
no mutation occurs
```

### KNOWLEDGE_INVENTORY_PARTIALLY_SUPPORTED

Use when:

```text
basic inventory works
but some coverage, stale-state, or alias analysis remains incomplete
```

### KNOWLEDGE_INVENTORY_NOT_SUPPORTED

Use when:

```text
inventory is incomplete
counts are unreliable
pagination fails
or integration-health data is still being mistaken for knowledge content
```

---

# 56. Final Report Questions

The Step 4.7 report must answer:

```text
1. How many pages are in telecombrain?
2. How many unique relationships exist?
3. Which page types dominate?
4. Which relationship types dominate?
5. Which domains are represented?
6. Which services are represented?
7. Which domains are sparse?
8. Which services are weakly mapped?
9. How many operational orphans exist?
10. How many aliases are unresolved or ambiguous?
11. Which knowledge is candidate/inferred/stale?
12. Where are the largest cross-domain coverage gaps?
13. Which entities lack supporting evidence?
14. Which incidents/tickets have weak correlation coverage?
15. Is the inventory complete enough to expose through Step 5 UI and Mark / Zaki?
```

---

# 57. Transition to Step 5

If Step 4.7 is supported:

```text
Validated H1–H4 reasoning
        +
Validated live MCP access
        +
Validated live reasoning parity
        +
Validated knowledge inventory
        ↓
Step 5 — Unified FikraCore Capability & Experience Layer
```

Step 5 can then expose:

```text
What FikraCore knows
What FikraCore does not know
Why FikraCore reached a conclusion
What FikraCore learned
What FikraCore predicts
```

through one consistent experience.

---

# Final Principle

> **Before exposing the brain everywhere, make the brain able to explain what it knows.**

Step 4.7 provides the inventory, coverage, and knowledge-health foundation required for a trustworthy Step 5 product experience.
