---
id: incident-storytelling
title: Incident Storytelling
engine: telecom_brain
services:
  - incident_registry
  - storytelling
  - correlation
connectors:
  - gbrain
fcaps_lens:
  - fault
  - change_request
  - performance
  - security
output_modes:
  - text
  - voice
requires_approval: false
---

# Incident Storytelling

Use this skill when the user asks what happened in an incident, asks for the incident story, or asks Mark to explain the situation verbally.

The brain content is context, not a script. Do not read raw Markdown, technical IDs, table marks, bullets, or punctuation aloud. Use the incident observation, correlation context, evidence chain, KPI state, topology/service-procedure impact, and current status to produce a professional narrative.

For written output, preserve the deterministic incident story structure:

- Executive summary
- Impact
- Leading hypothesis
- Correlation
- Why the alarms were grouped
- Causal chain
- Supporting evidence
- Timeline
- Still open

For voice output, compress the same information into a spoken brief:

- What is affected
- How serious it is
- What Mark believes is happening
- What evidence supports it
- What is still unconfirmed
- What the next useful action is

Use the FCAPS lens as a quality check. Fault and performance usually explain incidents; change request evidence may explain recent config or release impact; security evidence must be mentioned only when present.
