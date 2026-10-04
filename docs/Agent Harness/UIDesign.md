```text
# ZAKI — REFACTOR STORYTELLER VISUAL EXPLANATION ONLY

## CRITICAL SCOPE RESTRICTION

I want to modify ONLY this component:

~/FikraCore/frontend/src/components/features/agentic-qna-view/components/StorytellerVisualExplanation.tsx

Do NOT modify the existing Zaki Story / Storyteller response UI.

Do NOT modify the center Story content.

Do NOT refactor, resize, restructure, restyle, or otherwise alter the
existing Story component.

The existing Story is already working and must remain EXACTLY as it is.

The task is ONLY to redesign how `StorytellerVisualExplanation.tsx`
presents the visual/analytical information associated with that Story.

Think of this as:

    EXISTING STORY
         +
    NEW VISUAL EXPLANATION LAYOUT

NOT:

    redesign the entire response bubble.

---

# CURRENT EXPERIENCE

Currently the response contains the Zaki-generated Story and then
`StorytellerVisualExplanation.tsx` appears as a large visual explanation
section appended around/below the story.

I want to change ONLY the Visual Explanation presentation.

The Story itself must remain untouched.

---

# TARGET CONCEPT

The existing Story remains the CENTER / PRIMARY narrative.

The Visual Explanation should be reorganized into:

        LEFT VISUALS | EXISTING STORY | RIGHT VISUALS

BUT IMPORTANT:

The LEFT and RIGHT visual areas are part of
`StorytellerVisualExplanation.tsx`.

The CENTER STORY is NOT part of this refactor.

Do not create a new center column.

Do not wrap the existing Story component in a new layout.

Do not change its width, typography, spacing, content, rendering,
streaming behavior, or component implementation.

---

# VISUAL EXPLANATION STRUCTURE

The Visual Explanation should provide two side areas around the existing
Story.

## LEFT SIDE — EVIDENCE / REASONING

Display:

1. Evidence Matrix
2. Correlation Vector
3. Confidence Score
4. Ranked Hypotheses

Conceptually:

┌──────────────────────────┐
│ EVIDENCE & REASONING     │
│                          │
│ Evidence Matrix          │
│                          │
│ Correlation Vector       │
│                          │
│ Confidence Score         │
│                          │
│ Ranked Hypotheses        │
└──────────────────────────┘


## RIGHT SIDE — OPERATIONAL IMPACT

Display:

1. Domains Involved
2. Users Impacted
3. Services Impacted
4. Remediation Strategy

Conceptually:

┌──────────────────────────┐
│ OPERATIONAL IMPACT       │
│                          │
│ Domains Involved         │
│                          │
│ Users Impacted           │
│                          │
│ Services Impacted        │
│                          │
│ Remediation Strategy     │
└──────────────────────────┘


---

# VERY IMPORTANT — SIDE SPLITTERS

The visual explanation needs a sleek vertical splitter between the
LEFT visual area and the CENTER STORY, and another sleek vertical
splitter between the CENTER STORY and the RIGHT visual area.

However:

## THE SPLITTERS MUST ONLY SPLIT THE VISUAL SIDES.

They must NOT become a splitter for the Story itself.

Conceptually:

                    EXISTING STORY
                         │
                         │
     LEFT VISUAL        │        RIGHT VISUAL
                         │
          ┆             │             ┆
       splitter      EXISTING      splitter
                    STORY BOUNDARY

More explicitly:

┌──────────────────┆──────────────────────────────┆──────────────────┐
│                  ┆                              ┆                  │
│ LEFT VISUAL      ┆      EXISTING STORY          ┆ RIGHT VISUAL     │
│                  ┆      UNTOUCHED               ┆                  │
│                  ┆                              ┆                  │
└──────────────────┆──────────────────────────────┆──────────────────┘

The vertical splitters are ONLY visual boundaries.

They should NOT:

- resize the Story
- modify the Story DOM structure
- change Story width
- change Story typography
- change Story scrolling
- change Story streaming
- change Story rendering
- introduce a splitter inside the Story
- alter the existing Story component

If the implementation requires the existing Story to be aware of these
splitters, stop and find another approach.

---

# LOWER VISUAL EXPLANATION AREA

The following visual information should remain associated with the
Visual Explanation layer and should NOT be inserted into the Story:

## Chronology / Correlated Evidence

Display:

    Alarms
    Metrics
    KPIs
    Change Requests
    Traces / PCAP
    Logs

Concept:

CHRONOLOGY · CORRELATED EVIDENCE

    Alarm
      ↓
    Metric
      ↓
    KPI
      ↓
    Change Request
      ↓
    Trace
      ↓
    Log
      ↓
    Impact

This should use the same existing visual design language.

---

# ADDITIONAL VISUAL INSIGHT AREA

Also present:

- Blast Radius
- Causal Chain
- Remediation Status
- Knowledge Gap
- Pattern Recognition

These belong to the Visual Explanation UI.

They do NOT belong inside the Story.

---

# IMPORTANT CONTENT SEPARATION

The visual explanation should follow this conceptual division:

LEFT:

    WHY DO WE BELIEVE THIS?

    Evidence Matrix
    Correlation Vector
    Confidence
    Ranked Hypotheses


CENTER:

    WHAT IS ZAKI SAYING?

    EXISTING STORY — DO NOT TOUCH


RIGHT:

    WHAT DOES THIS MEAN OPERATIONALLY?

    Domains
    Users
    Services
    Remediation


BELOW / ASSOCIATED VISUAL EXPLANATION:

    HOW DID IT HAPPEN?

    Chronology
    Correlated Evidence
    Blast Radius
    Causal Chain
    Remediation Status
    Knowledge Gap
    Pattern Recognition

---

# DO NOT MOVE STORY CONTENT

Do NOT move any of these into the side panels:

- Incident Story
- Executive Summary
- RCA narrative
- Zaki narrative
- Story text
- Voice/story content
- Story streaming
- Story rendering
- Existing conversational response content

The Story remains exactly where it is today.

The Visual Explanation component should simply provide the surrounding
visual analytical context.

---

# DESIGN LANGUAGE

Use the SAME visual language already present in
`StorytellerVisualExplanation.tsx`.

Preserve:

- dark NOC theme
- cyan / teal accents
- blue surfaces
- subtle magenta analytical accents
- rounded panels
- thin borders
- subtle glow
- compact enterprise UI
- existing iconography
- existing spacing language where practical

Do not redesign the application.

This is a layout refactor of ONE existing component.

---

# EXECUTIVE TYPOGRAPHY IMPROVEMENT

Within `StorytellerVisualExplanation.tsx` only, improve the typography
of the visual explanation panels.

The visual explanation currently feels somewhat like a developer/
debugging console.

Make the visual panels more executive-readable.

Increase hierarchy for:

    Section titles
    KPI values
    Confidence
    Subscriber impact
    Service impact
    Domain names

Use:

- cleaner modern sans-serif
- stronger section hierarchy
- slightly larger important values
- comfortable line height
- less microscopic metadata
- less unnecessary uppercase text

Do NOT modify typography inside the existing Story.

Only the Visual Explanation typography should change.

---

# SIDE PANEL BEHAVIOR

The left and right visual areas should behave independently from the
Story.

If resizing/splitting is implemented:

    LEFT SIDE     → adjustable
    CENTER STORY  → unchanged
    RIGHT SIDE    → adjustable

The Story width should remain controlled by its existing implementation.

Do not introduce a global three-column resizable container around the
whole response.

---

# RESPONSIVE BEHAVIOR

Desktop:

    LEFT VISUALS | EXISTING STORY | RIGHT VISUALS

If the viewport becomes too narrow:

    Existing Story remains intact.

The side visual areas may:

- collapse
- stack
- become drawers
- become horizontally scrollable

But never break or restructure the existing Story.

---

# DATA MAPPING

Reuse the existing data already supplied to
`StorytellerVisualExplanation.tsx`.

Do not create duplicate backend models.

Map the visual sections to the existing contracts/data:

Evidence Matrix
    → HarnessEvidenceContract / evidence data

Correlation Vector
    → CausalPropagationContract / topology relationships

Confidence
    → HypothesisRankingContract

Ranked Hypotheses
    → HypothesisRankingContract

Domains
    → Incident / Operational Context

Users Impacted
    → ServiceImpactContract / BlastRadiusAssessmentContract

Services Impacted
    → ServiceImpactContract

Remediation Strategy
    → RemediationStrategyContract

Chronology
    → incident/evidence/task timeline

Blast Radius
    → BlastRadiusAssessmentContract

Causal Chain
    → CausalPropagationContract

Knowledge Gap
    → DiagnosticGapContract

Pattern Recognition
    → pattern / FikraCore knowledge

---

# SEMANTIC SAFETY

Preserve the distinction between:

    Observation
    Evidence
    Correlation
    Hypothesis
    Validated Cause
    Proposed Action
    Executed Action
    Outcome

For example:

    "Leading Hypothesis"
must NOT visually become:
    "Confirmed Root Cause"

Similarly:

    "Remediation Proposed"
must NOT appear as:
    "Remediation Executed"

Do not change the underlying semantics.

---

# EXISTING ACTION BUTTONS

Keep the existing visual explanation actions:

    Storyteller
    Blast Radius
    Causal Propagation Path
    Remediation Strategy

Do not remove them.

Do not move them into the Story.

They remain associated with the Visual Explanation layer.

---

# IMPLEMENTATION RULE

Before changing code:

1. Inspect the existing `StorytellerVisualExplanation.tsx`.
2. Understand its current props and data contracts.
3. Identify exactly what it currently renders.
4. Reuse its existing components/data wherever possible.
5. Refactor ONLY this component and any strictly local styling required
   for this component.

Do NOT modify unrelated components.

Do NOT modify the Story component.

Do NOT modify the response bubble architecture.

Do NOT modify backend contracts.

Do NOT modify Zaki reasoning logic.

Do NOT modify streaming logic.

Do NOT modify Story generation.

Do NOT modify voice/prosody behavior.

---

# FINAL VISUAL INTENT

The result should feel like:

                    ┌─────────────────────────────────┐
                    │         EXISTING ZAKI STORY     │
                    │                                 │
        ┌───────────┆─────────────────────────────────┆───────────┐
        │           ┆                                ┆           │
        │ EVIDENCE  ┆                                ┆ OPERATION │
        │ &         ┆       STORY REMAINS            ┆ AL IMPACT  │
        │ REASONING ┆       COMPLETELY               ┆           │
        │           ┆       UNTOUCHED                ┆ Domains    │
        │ Evidence  ┆                                ┆ Users      │
        │ Matrix    ┆                                ┆ Services   │
        │           ┆                                ┆ Remediation│
        │ Correlation┆                                ┆           │
        │ Confidence┆                                ┆           │
        │ Hypotheses┆                                ┆           │
        └───────────┆────────────────────────────────┆───────────┘
                    │                                │
                    └────────────────────────────────┘

             CHRONOLOGY · CORRELATED EVIDENCE

       Alarm → Metric → KPI → CR → Trace → Log → Impact

             OPERATIONAL INTELLIGENCE

       Blast Radius | Causal Chain | Remediation |
       Knowledge Gap | Pattern Recognition

The vertical `┆` lines are sleek visual splitters/boundaries.

THEY SPLIT ONLY THE VISUAL EXPLANATION SIDES.

THE CENTER STORY IS NOT TOUCHED.

---

# SUCCESS CRITERION

When I open a Zaki response:

- The existing Story looks and behaves exactly as before.
- The existing Story content is unchanged.
- The Story generation is unchanged.
- The Story streaming is unchanged.
- The Visual Explanation becomes much more useful.
- Evidence/reasoning is visually separated on the left.
- Operational impact is visually separated on the right.
- Chronology and deeper operational intelligence remain associated with
  the Visual Explanation.
- The whole thing visually feels like one premium executive NOC
  intelligence interface.

Again:

## ONLY MODIFY

`~/FikraCore/frontend/src/components/features/agentic-qna-view/components/StorytellerVisualExplanation.tsx`

## DO NOT MODIFY THE CENTER STORY.
```

### The critical distinction I'd keep in the prompt

Your intended architecture is actually:

```text
             EXISTING RESPONSE / STORY
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   VISUAL SIDE      EXISTING STORY    VISUAL SIDE
   ───────────      ──────────────    ───────────
   Evidence         UNTOUCHED         Impact
   Reasoning                         Resolution
        │                                 │
        └────────────┬────────────────────┘
                     │
                     ▼
             VISUAL EXPLANATION
                Chronology
                Blast Radius
                Causal Chain
                Knowledge Gap
                Pattern
```

So **the splitter is a boundary of the visual explanation, not a splitter of the Story**. That's the point I'd make especially explicit to Claude because otherwise it may wrap the entire response bubble in a three-column resizable layout and inadvertently change your existing Story UI.


The important rule is:

> **Storyteller, Blast Radius, Causal Propagation, Remediation Strategy, and every new visual introduced in this component must consume the same `OperationalContextContract` for the current Zaki operational state.**

Here is the **updated section to add to the prompt**, or you can replace the previous **DATA MAPPING** section with this stronger version:

```text id="1r5x6a"
# 15. SINGLE OPERATIONAL CONTEXT — CRITICAL ARCHITECTURAL REQUIREMENT

ALL visual explanation views must operate against the SAME
`OperationalContextContract`.

There must be ONE authoritative operational context for the current
Zaki response / incident investigation.

Do NOT allow each visual component to independently reconstruct,
infer, or maintain its own operational context.

The following views MUST consume/reference the same
`OperationalContextContract`:

    Storyteller
    Blast Radius
    Causal Propagation
    Remediation Strategy
    Evidence Matrix
    Correlation Vector
    Confidence
    Ranked Hypotheses
    Domains Involved
    Users Impacted
    Services Impacted
    Chronology / Correlated Evidence
    Remediation Status
    Knowledge Gap
    Pattern Recognition
    Any other visual introduced by this refactor

Conceptually:

                    OperationalContextContract
                              │
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
          Storyteller     Blast Radius   Causal Propagation
               │              │              │
               └──────────────┼──────────────┘
                              │
                              ▼
                     Remediation Strategy
                              │
                              ▼
                    Visual Explanation Views
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
          Evidence         Impact          Knowledge
          Reasoning        Analysis        / Pattern
```

## CONTEXT CONSISTENCY

If the OperationalContext contains:

```
context_id
context_version
scenario_id
run_id
active_incident_id
primary_domain
active_domains
visible_entities
visible_topology_subgraph
admitted_evidence_ids
active_knowledge_gaps
active_maintenance_windows
human_sme_role
operational_mode
active_incident_ids
active_delegations
pending_approvals
impact_summary
resilience_profiles
created_at
```

then all visualizations must derive their displayed information from
that same context.

Do not create independent context objects for:

```
Blast Radius
Causal Propagation
Remediation
Storyteller
Evidence Matrix
Pattern Recognition
```

They may have their own specialized contracts/data structures, but
those structures must be evaluated WITHIN the same operational context.

---

# CONTEXT IS THE SHARED RUNTIME ENVELOPE

Use this conceptual relationship:

```
    FikraCore
        │
        │ semantic truth
        ▼
OperationalContextContract
        │
        │ shared runtime context
        │
┌───────┼───────────────────────────────────────┐
│       │             │            │             │
▼       ▼             ▼            ▼             ▼
```

Story   Evidence     Blast Radius  Causal       Remediation
teller  Matrix                      Chain        Strategy
│       │             │            │             │
└───────┴─────────────┴────────────┴─────────────┘
│
▼
Same Incident View
│
▼
Zaki Response

```

The UI must never produce a situation where:

    Storyteller says A

while:

    Blast Radius says B

or:

    Causal Propagation uses a different topology

or:

    Remediation Strategy uses a different incident state.

All must represent the same operational snapshot/version unless an
explicit version transition is being displayed.

---

# CONTEXT VERSION / SNAPSHOT CONSISTENCY

Where supported by the existing architecture, each visual should be
able to identify the context it was rendered from:

    context_id
    context_version

For example:

    OperationalContext
        ID: CTX-SCN001-001
        Version: 7

Then:

    Storyteller              → CTX-SCN001-001 / v7
    Evidence Matrix          → CTX-SCN001-001 / v7
    Blast Radius             → CTX-SCN001-001 / v7
    Causal Propagation       → CTX-SCN001-001 / v7
    Remediation Strategy     → CTX-SCN001-001 / v7

This prevents visual inconsistency caused by individual components
reading independently changing state.

If the application already has an existing context/version mechanism,
reuse it.

Do NOT introduce a new context management mechanism inside
`StorytellerVisualExplanation.tsx`.

---

# CONTRACT OWNERSHIP

The OperationalContextContract is NOT the semantic source of truth.

Remember the architecture:

    FikraCore
        ↓
    semantic truth / topology / relationships / validated knowledge

    OperationalContextContract
        ↓
    authorized runtime operational snapshot

    Zaki
        ↓
    cognitive interpretation / orchestration / explanation

    TaskEpisodeContract
        ↓
    cognitive work / reasoning / validation / action / outcome

Therefore:

OperationalContext tells the UI:

    "What operational world are we currently looking at?"

FikraCore provides:

    "What entities, relationships, topology and validated knowledge
     exist in that world?"

Specialized contracts provide:

    "What does this particular analytical view represent?"

Example:

    BlastRadiusAssessmentContract
        does NOT replace OperationalContext.

It evaluates blast radius WITHIN the current OperationalContext.

Likewise:

    CausalPropagationContract
        does NOT create its own topology.

It uses the topology/relationships available through the current
OperationalContext and FikraCore semantic references.

Likewise:

    RemediationStrategyContract
        does NOT create a separate incident context.

It evaluates remediation against the same active incident,
operational mode, authority, impact and evidence context.

---

# IMPORTANT: DO NOT DUPLICATE OPERATIONAL STATE

Do not introduce UI-local versions of:

    active_incident_id
    active_domains
    visible_entities
    evidence IDs
    operational mode
    maintenance windows
    impact scope
    authority
    topology scope
    knowledge gaps

If these already exist in `OperationalContextContract`, consume them.

Do not create:

    localIncident
    localTopology
    localEvidenceContext
    localOperationalContext
    localImpactContext

unless they are purely presentational derived values.

Derived UI state is acceptable.

Duplicated operational truth is NOT.

---

# SPECIALIZED CONTRACTS REMAIN SPECIALIZED

The requirement for one OperationalContext does NOT mean that every
visual must use the same contract.

Use the appropriate specialized contract while maintaining the same
operational context boundary.

For example:

    OperationalContextContract
             │
             ├── HarnessEvidenceContract
             │        └── Evidence Matrix
             │
             ├── HypothesisRankingContract
             │        ├── Confidence
             │        └── Ranked Hypotheses
             │
             ├── BlastRadiusAssessmentContract
             │        └── Blast Radius
             │
             ├── CausalPropagationContract
             │        └── Causal Chain
             │
             ├── ServiceImpactContract
             │        ├── Users Impacted
             │        └── Services Impacted
             │
             ├── RemediationStrategyContract
             │        └── Remediation Strategy
             │
             ├── DiagnosticGapContract
             │        └── Knowledge Gap
             │
             └── Pattern / FikraCore Knowledge
                      └── Pattern Recognition

All of them operate within:

        ONE OperationalContextContract
```

And I would add this **very explicit acceptance criterion** at the end:

```text id="d9q2vl"
# ARCHITECTURAL ACCEPTANCE TEST

Before considering the implementation complete, verify:

1. Storyteller uses the current OperationalContext.

2. Blast Radius uses the same OperationalContext.

3. Causal Propagation uses the same OperationalContext.

4. Remediation Strategy uses the same OperationalContext.

5. Evidence Matrix uses the same OperationalContext.

6. Correlation Vector uses the same OperationalContext.

7. Hypotheses / Confidence use the same operational snapshot.

8. Domains, Users and Services use the same operational snapshot.

9. Chronology uses the same incident/context timeline.

10. Knowledge Gap uses the same active knowledge-gap state.

11. Pattern Recognition uses the same operational scope and FikraCore
    semantic context.

12. No visual component creates a competing operational context.

13. No UI-local operational truth is introduced.

14. Existing Story component remains untouched.

15. Only `StorytellerVisualExplanation.tsx` is modified unless a
    strictly necessary local style dependency already belongs to this
    component.

The final UI must represent ONE operational reality viewed through
multiple analytical lenses — not multiple independently constructed
realities.
```

That last sentence is the **core architectural principle**:

> **One Operational Context → multiple analytical lenses.**

So your `Storyteller`, `Blast Radius`, `Causal Propagation`, `Remediation Strategy`, and the new Evidence/Impact/Knowledge visuals are **not separate worlds**. They are different projections of the **same operational context**, grounded by FikraCore and interpreted by Zaki.
