# FikraCore Step 5.2.1 — Domain Attribution & Zaki Context Consistency Fix

## Purpose

Step 5, Step 5.1, and Step 5.2 are already implemented and verified.

This document defines a **targeted corrective step only** for the inconsistency observed in scenario `H4-WI-36`, where the UI and Zaki disagree about the PRIMARY domain.

This fix must preserve all existing Step 5 / 5.1 / 5.2 behavior and must not introduce a new attribution engine or a new Zaki reasoning path.

## 1. Problem Statement

The current system can produce inconsistent operational interpretation across:

```text
Hypothesis Board
Domain Attribution
Affected Services
Zaki Copilot
```

The inconsistency may arise from:

```text
stale attribution
impact-vs-causality semantic mixing
Zaki independently deriving attribution
revision mismatch
entity-to-domain mapping error
attribution not recomputed after hypothesis changes
```

The goal is to make domain attribution and Zaki explanation contract-consistent, revision-consistent, and semantically explicit.

## 2. Non-Negotiable Rule

Zaki must never independently derive domain attribution.

Correct:

```text
backend domain_attribution
→ persisted
→ revision accepted
→ UI renders
→ Zaki explains same attribution
```

Forbidden:

```text
leading hypothesis
→ Zaki infers primary domain on its own
```

## 3. Scope

Build only:

```text
A. Domain attribution contract hardening
B. Attribution recomputation integrity
C. Revision consistency
D. Zaki grounding correction
E. Conflict detection
F. Regression tests
```

Do not redesign:

```text
Neural Reasoning Map
Hypothesis engine
Impact engine
Stage orchestration
Live reasoning architecture
Zaki UI
```

## 4. Authoritative Attribution Contract

Extend the existing attribution contract additively.

```ts
type DomainAttributionState = {
  scenario_id?: string
  intent_id?: string
  run_id: string

  revision: number
  sequence: number

  attribution_status:
    | "UNRESOLVED"
    | "PARTIAL"
    | "CONSISTENT"
    | "CONFLICT"

  domains: {
    domain_id?: string
    display_name: string

    role:
      | "PRIMARY"
      | "CONTRIBUTING"
      | "AFFECTED"
      | "INVOLVED"
      | "MONITOR_ONLY"
      | "NOT_RELEVANT"

    attribution_basis:
      | "CAUSAL"
      | "IMPACT"
      | "DEPENDENCY"
      | "VALIDATION"
      | "MIXED"

    confidence?: number
    reason: string

    supporting_hypothesis_ids?: string[]
    supporting_evidence_ids?: string[]
    supporting_pathway_ids?: string[]

    source_revision: number
  }[]
}
```

The frontend and Zaki must use this same object.

## 5. Separate Causal Attribution from Impact Attribution

Do not use the same score/role semantics for:

```text
who caused the issue
```

and:

```text
who is most affected
```

Example:

```text
IP Transport
role = PRIMARY
attribution_basis = CAUSAL

RAN
role = AFFECTED
attribution_basis = IMPACT

Mobile Core
role = AFFECTED
attribution_basis = IMPACT
```

Do not infer PRIMARY from the largest impact score.

## 6. Primary Domain Invariant

A PRIMARY domain must have:

```text
reason
supporting_hypothesis_ids
source_revision
```

Prefer also:

```text
supporting_evidence_ids
supporting_pathway_ids
```

A PRIMARY domain must never exist as a bare percentage with no explanation.

## 7. Attribution Recompute Trigger

Recompute domain attribution whenever any of the following materially changes:

```text
leading hypothesis
hypothesis ranking
hypothesis support state
root candidate
confirmed hypothesis
new contradicting evidence
knowledge gap resolution
validation result
```

Do not leave old domain attribution attached to a new leading hypothesis.

## 8. Stale Attribution Guard

Persist:

```text
attribution.source_revision
```

If:

```text
domain_attribution.revision < hypothesis_revision
```

then attribution is stale and must not be shown as authoritative.

Recommended:

```text
attribution_status = UNRESOLVED
```

until recomputation finishes.

## 9. Backend Consistency Check

Add an attribution consistency validator:

```python
validate_domain_attribution(run)
```

It should check:

```text
PRIMARY domain exists only when supported
PRIMARY domain reason is non-empty
supporting hypothesis IDs exist
supporting hypotheses are active/supported
source revision is current
causal basis is not derived from impact only
```

If inconsistency is detected:

```text
attribution_status = CONFLICT
```

Do not silently choose one side.

## 10. Hypothesis-to-Domain Mapping

Entity-to-domain mapping must be canonical.

Examples:

```text
IP/MPLS Edge Router-07
→ IP Transport

UPF-01
→ Mobile Core

IMS SBC
→ IMS / VoLTE

RAN gNodeB
→ RAN
```

Use canonical resolver / telecombrain relationships.

Do not use display-name substring matching if canonical mapping already exists.

## 11. No Impact-to-Causality Shortcut

Forbidden:

```text
highest impacted domain
→ PRIMARY
```

Allowed:

```text
supported causal hypothesis
+ canonical entity/domain ownership
+ evidence
+ dependency reasoning
→ PRIMARY
```

Impact may contribute context but must not alone define causal ownership.

## 12. Domain Attribution Matrix Semantics

If the UI shows a matrix/score, document what the score means.

Recommended:

```text
causal confidence
impact confidence
dependency relevance
validation confidence
```

Do not mix all into one unlabeled percentage.

If compatibility requires one score, add:

```text
score_basis
```

## 13. Zaki Grounding Rule

Zaki must answer attribution questions from:

```text
run.domain_attribution
```

only.

For:

```text
Why is RAN PRIMARY?
```

Zaki should inspect:

```text
role
attribution_basis
reason
supporting_hypothesis_ids
supporting_evidence_ids
revision
```

and explain exactly that state.

## 14. Zaki Must Not Re-Derive Attribution

Remove fallback logic such as:

```text
if "router" in hypothesis:
  primary = "IP Transport"
```

or semantic equivalents.

Zaki may explain backend attribution.

Zaki must not substitute its own attribution.

## 15. Zaki Conflict Response

If:

```text
domain_attribution.attribution_status = CONFLICT
```

Zaki should say:

```text
The current domain attribution conflicts with the active hypothesis state.

Leading hypothesis:
H1 — ...

Authoritative attribution:
...

This run requires attribution recomputation before a primary domain can be trusted.
```

Do not silently resolve the conflict in chat.

## 16. Zaki Revision Binding

Zaki request and response must carry:

```text
scenario_id / intent_id
run_id
revision
sequence
```

If the UI is on revision `N`, Zaki must answer from revision `N` or explicitly return a refresh/conflict response.

Do not silently answer from a newer or older revision.

## 17. Strong Revision Rule

Recommended:

```text
request revision == authoritative revision
→ answer

request revision < authoritative revision
→ return 409 STALE_REVISION

request revision > authoritative revision
→ return 409 INVALID_REVISION
```

Optionally support:

```text
allow_refresh=true
```

only if the UI then atomically refreshes before displaying the answer.

## 18. UI Revision Integrity

All of these surfaces must share the same accepted revision:

```text
Hypothesis Board
Domain Attribution
Affected Services
Zaki
Neural Reasoning Map
Validation
Learning
```

A mismatch should be detectable.

## 19. Attribution Conflict Indicator

If backend detects a conflict, UI should display:

```text
ATTRIBUTION CONFLICT
```

or:

```text
Recomputing Attribution
```

rather than showing a potentially wrong PRIMARY domain.

Do not hide inconsistency behind a normal green/confirmed state.

## 20. Scenario H4-WI-36 Acceptance Case

Use the exact problematic scenario as a regression case.

Expected invariant:

```text
If H1 is a Core Transport Router cause
and
the authoritative causal mapping resolves to IP Transport
```

then one of these must happen:

```text
A.
IP Transport = PRIMARY

or

B.
RAN = PRIMARY
but with an explicit backend reason and supporting hypothesis/evidence that justifies why RAN remains causal despite H1
```

Not allowed:

```text
UI says RAN PRIMARY
Zaki says IP Transport PRIMARY
with no conflict state
```

## 21. Snapshot Diagnostic Test

Inspect:

```text
scenario_id
run_id
revision
sequence

H1:
display_name
state
confidence

domain_attribution:
domain
role
attribution_basis
confidence
reason
supporting_hypothesis_ids
source_revision

impact:
affected_domains
affected_services

Zaki:
request revision
response revision
grounded_in
```

This should identify whether the inconsistency originates in:

```text
backend attribution
frontend rendering
stale state
Zaki grounding
```

## 22. Backend Tests

Add:

```text
test_domain_attribution_recomputes_when_leading_hypothesis_changes
test_primary_domain_requires_reason
test_primary_domain_requires_supporting_hypothesis
test_attribution_source_revision_matches_run_revision
test_stale_attribution_marked_unresolved
test_impact_score_does_not_assign_primary_domain
test_canonical_entity_to_domain_mapping
test_domain_attribution_conflict_detected
test_h4_wi_36_attribution_consistency
```

## 23. Zaki Tests

Add:

```text
test_zaki_uses_authoritative_domain_attribution
test_zaki_does_not_derive_domain_from_hypothesis_text
test_zaki_reports_attribution_conflict
test_zaki_revision_matches_ui_revision
test_zaki_rejects_stale_revision
test_zaki_rejects_future_revision
test_zaki_explains_primary_domain_reason
```

## 24. Frontend Tests

Add:

```text
test_domain_attribution_uses_current_revision
test_domain_attribution_conflict_indicator
test_primary_domain_reason_available
test_hypothesis_and_domain_attribution_revision_match
test_zaki_and_domain_attribution_revision_match
```

## 25. Regression Gate

Before implementation:

```text
run all Step 5 tests
run all Step 5.1 tests
run all Step 5.2 tests
record baseline
```

After implementation:

```text
all previous tests must remain green
```

Reject this fix if it breaks:

```text
simulation orchestration
live reasoning
hypothesis evolution
domain attribution
Zaki
source switching
replay
hidden truth isolation
```

## 26. Definition of Done

```text
[ ] Zaki no longer derives primary domain independently
[ ] UI and Zaki consume the same domain attribution object
[ ] causal attribution is separated from impact attribution
[ ] PRIMARY always has reason + supporting hypothesis
[ ] attribution recomputes when hypothesis state changes
[ ] stale attribution cannot appear as confirmed
[ ] attribution conflict is explicit
[ ] H4-WI-36 no longer produces contradictory UI/Zaki answers
[ ] Zaki and UI share exact revision context
[ ] canonical entity-to-domain mapping is used
[ ] all existing Step 5 / 5.1 / 5.2 tests remain green
```



## 27. Visual Clarity — Entity Name Typography & Color Semantics

This corrective step must also improve readability of operational entities across the investigation UI.

The attached reference style uses high-contrast **cyan** and **magenta** labels with a clean, legible font. Apply the same principle to FikraCore entity rendering without changing the existing overall visual identity.

### 27.1 Entity Names Must Be Visually Distinct

Operational entity names should be visually separated from surrounding explanatory text.

Examples:

```text
IP/MPLS Edge Router-07
AMF-01
UPF-01
Enterprise APN
RAN
IP Transport
Mobile Core
CR-7721
H1 — Core Transport Router Failure
Redundant MPLS Path Health Unknown
```

Use one of the two semantic highlight colors:

```text
CYAN
→ primary operational entities, services, domains, components, nodes

MAGENTA
→ identifiers, incident IDs, trace/file names, hypotheses, selected/high-attention entities
```

Do not color full paragraphs.

Only the operational entity token or short label should be highlighted.

### 27.2 Recommended Usage

Use **cyan** for:

```text
network elements
services
domains
reasoning pathway labels
validated operational facts
affected services
component names
canonical display names
```

Examples:

```text
AMF-01
IP Transport
Enterprise APN
Service Dependency
Mobile Core
```

Use **magenta** for:

```text
incident IDs
scenario IDs
intent IDs
hypothesis IDs/titles when selected
trace/pcap filenames
change IDs
ticket IDs
knowledge-gap identifiers when emphasized
```

Examples:

```text
H4-WI-36
INCIDENT-2026-08-09
CR-7721
DTMFsipinfo.pcap
H1 — Core Transport Router Failure
```

### 27.3 Human-Readable Name First

Continue the existing FikraCore naming rule:

```text
display_name first
opaque ID second
```

Example:

```text
IP/MPLS Edge Router-07
```

instead of:

```text
RTR-EDGE-07
```

Opaque IDs may appear in metadata or Deep Technical views only.

### 27.4 Clear Font Requirement

Use a clean, highly legible UI font for operational text.

Requirements:

```text
clear sans-serif or existing readable mono/sans stack
high x-height
strong character separation
avoid decorative sci-fi fonts for body text
avoid overly condensed fonts
avoid excessive letter spacing
```

For code-like identifiers and technical IDs, use the existing monospace stack if it is already clear.

For normal labels and summaries, use the existing primary sans-serif stack.

Do not introduce a new font family unless the current one is genuinely unreadable.

### 27.5 Weight & Contrast

Entity names should use:

```text
font-weight: 600–700
```

Supporting explanatory text should use:

```text
font-weight: 400–500
```

Recommended contrast pattern:

```text
Entity label:
bright cyan or magenta

Supporting sentence:
neutral light gray / white

Metadata:
muted gray
```

This produces the same clarity as the attached incident and trace-analyzer references.

### 27.6 Do Not Encode Meaning by Color Alone

Color is for readability and emphasis, not the only semantic signal.

Always retain text labels such as:

```text
PRIMARY
CONTRIBUTING
AFFECTED
CONFIRMED
CONFLICT
BLOCKED
```

Do not require the operator to infer meaning only from cyan/magenta.

### 27.7 Domain Attribution Panel

For Domain Attribution:

```text
Domain name
→ cyan

Role badge
→ existing semantic status color

Confidence / score
→ existing semantic color

Reason text
→ neutral light text
```

Example:

```text
IP Transport        PRIMARY
62%

Reason:
Leading supported hypothesis maps to IP Transport through canonical entity ownership.
```

If a conflict exists:

```text
ATTRIBUTION CONFLICT
```

must remain explicit and should not be hidden by decorative styling.

### 27.8 Zaki Responses

Zaki should render referenced operational entities with the same visual emphasis.

Example response:

```text
The authoritative primary domain is [IP Transport].

The leading hypothesis is [H1 — Core Transport Router Failure].

The affected domain is [Mobile Core].
```

Frontend rendering should style:

```text
IP Transport
Mobile Core
AMF-01
UPF-01
```

in cyan.

Style:

```text
H1 — Core Transport Router Failure
CR-7721
H4-WI-36
```

in magenta where appropriate.

Do not require the LLM to emit raw HTML/CSS.

The frontend should receive structured grounding/entity references and apply styles safely.

### 27.9 Structured Entity Highlighting

Preferred response metadata:

```ts
type HighlightedEntity = {
  id?: string
  display_name: string

  entity_type:
    | "NETWORK_ELEMENT"
    | "SERVICE"
    | "DOMAIN"
    | "HYPOTHESIS"
    | "INCIDENT"
    | "SCENARIO"
    | "INTENT"
    | "CHANGE"
    | "TICKET"
    | "TRACE"
    | "KNOWLEDGE_GAP"

  highlight:
    | "CYAN"
    | "MAGENTA"
}
```

Zaki responses may include:

```ts
entities: HighlightedEntity[]
```

The UI should match these structured entities against the rendered answer and apply safe highlighting.

Do not use unconstrained HTML generated by the model.

### 27.10 Neural Reasoning Map Labels

Apply the same typography rule to the Neural Reasoning Map.

Use clear, readable labels for:

```text
Evidence
Reasoning Pathways
Reasoning Core
Hypotheses
Domain Attribution
Affected Services
Validation
Learning
```

Entity names should remain crisp even at normal investigation zoom.

Avoid:

```text
tiny labels
thin low-contrast fonts
blurred glow over text
all-caps everywhere
excessive neon bloom
```

Glow should surround containers/conduits, not reduce text readability.

### 27.11 Accessibility / Readability

Maintain sufficient contrast on the dark background.

Verify:

```text
cyan entity text remains readable
magenta entity text remains readable
neutral body text remains readable
status badges remain distinguishable
```

Prefer clarity over decorative glow.

### 27.12 Visual Acceptance Tests

Add or extend frontend tests:

```text
test_entity_names_use_highlight_tokens
test_domain_names_render_with_entity_style
test_hypothesis_names_render_with_identifier_style
test_zaki_grounded_entities_receive_highlight_metadata
test_body_text_remains_neutral
test_color_not_only_status_indicator
```

### 27.13 Definition of Done — Visual Clarity

```text
[ ] entity names are visually distinct from surrounding text
[ ] cyan is used consistently for operational entities
[ ] magenta is used consistently for identifiers/high-attention entities
[ ] font remains clear and highly readable
[ ] body text is not over-colored
[ ] Zaki entity references use the same styling system
[ ] Neural Reasoning Map labels remain crisp
[ ] color is not the only semantic indicator
[ ] existing Step 5 / 5.1 / 5.2 behavior is unchanged
```


## Final Principle

> **There must be only one authoritative answer to "Which domain is primary?"**

> **The backend computes it. The UI renders it. Zaki explains it.**

> **If the system cannot reconcile attribution with the active hypothesis state, it must expose a conflict instead of inventing consistency.**
