# Storyteller Baseline Structure

This is the deterministic baseline for incident storytelling. Every incident
story should render the same section shape when the underlying gbrain evidence
contains the relevant facts.

The human-readable story is useful for operators. The structured JSON is useful
for explaining how the story was built.

## Required Story Shape

The default `story` answer should contain these sections, in this order:

1. Title
   - `# Incident story - <incident_id>`

2. State
   - `Status`
   - `Severity`

3. One-line incident brief
   - Incident id
   - Severity and status
   - Incident scope, such as `intra-domain` or `inter-domain`
   - Affected service or component
   - Correlation score when available
   - Intent state when available
   - Confirmed root cause or leading hypothesis

4. Impact
   - Affected services
   - Involved components / network functions

5. Root cause or leading hypothesis
   - Confirmed root cause when available
   - Otherwise the leading hypothesis and its assessment status

6. Correlation
   - Scope: `intra-domain`, `inter-domain`, or `unclassified`
   - Contributing domains
   - Correlation score
   - Intent status

7. Why these alarms were grouped
   - Deterministic correlation reasons
   - No-miss / novelty reason when a signal is retained for review

8. Causal chain
   - Ordered claims with claim classification
   - Common claim types: `CORRELATION`, `OBSERVATION`, `HYPOTHESIS`,
     `EVIDENCE`, `CONFIRMED_ROOT_CAUSE`, `FACT`

9. Supporting evidence
   - Alarm evidence
   - KPI evidence
   - Ticket, log, trace, or change evidence when available

10. Timeline
    - Timestamped alarm/evidence/recovery sequence

11. Remediation
    - Actions taken, if known

12. Recovery
    - Recovery verification, if known

13. Still open
    - Missing root cause confirmation
    - Missing remediation
    - Missing recovery
    - Other unresolved investigation gaps

## Reference Artifacts

For every important story, store both files:

- `answer.md`: the deterministic operator-facing story.
- `response.json`: the full `/ask` response, including `story`, `intent`, and
  provenance-backed facts.

The `story` object inside `response.json` is the build trace. It contains:

- `impact`: services and involved components.
- `hypotheses`: ranked hypotheses plus supporting evidence.
- `causal_chain`: ordered claim-classified reasoning steps.
- `correlation_metadata`: score, scope, domains, intent state, and grouping
  reasons.
- `timeline`: facts parsed from the incident page.
- `unresolved_questions`: deterministic gaps that remain open.

## Capture Command

Use the helper script to capture a reference bundle:

```bash
scripts/capture_story_reference.sh \
  mobile-core/incidents/ue-registration-1fe005ed908a3f26
```

By default, bundles are stored under:

```text
docs/storyteller-references/<safe-incident-id>/<timestamp>/
```

Each bundle contains:

- `answer.md`
- `response.json`
- `story.json`
- `command.txt`

Use `answer.md` as the readable baseline and `story.json` to inspect how each
section was built from gbrain facts.
