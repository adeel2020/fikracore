---
id: alarm-correlation
title: Intent-Aware Alarm Correlation
engine: telecom_brain
services:
  - correlation
  - topology
  - telemetry_evidence
  - intent
  - incident_registry
connectors:
  - gbrain
  - grafana
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

# Intent-Aware Alarm Correlation

Use this skill when alarms need to be grouped into intra-domain or inter-domain incident candidates.

Do not correlate every alarm blindly. Score alarms using time window, topology proximity, service procedure relationship, shared affected intent, KPI breach, ticket evidence, severity, and novelty.

Do not drop important unknown alarms. If an alarm has a novel signature, high severity, shared service impact, or independent operational evidence, retain it for review even if the intent mapping is incomplete.

Use these categories:

- Intra-domain incident: evidence mostly belongs inside one mobile-core network area such as LTE, 5GC, IMS, vEPC, CS, PS, VAS, or IoT.
- Inter-domain incident: evidence crosses mobile core, RAN, transport, cloud, or external dependency boundaries.

The output must include why alarms were grouped and why other nearby alarms were ignored or retained for review.
