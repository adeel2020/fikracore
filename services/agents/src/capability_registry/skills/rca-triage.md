---
id: rca-triage
title: RCA Triage
engine: telecom_brain
services:
  - incident_registry
  - correlation
  - telemetry_evidence
  - topology
  - intent
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

# RCA Triage

Use this skill when the user asks for root cause, likely cause, blast radius, or next investigation steps.

Start from confirmed evidence. Separate fact, inference, and hypothesis. Prefer the smallest hypothesis that explains alarm timing, KPI impact, topology relationship, service procedure failure, and intent violation.

Do not claim root cause is confirmed unless the incident record or evidence says it is confirmed. When evidence is missing, say exactly what is missing.

Use FCAPS explicitly:

- Fault: alarms, failures, link down, process crash, peer timeout
- Change request: recent deployment, config update, planned work, rollback, MOP execution
- Accounting: charging, quota, billing, mediation, usage-impact evidence
- Performance: latency, CPU, throughput, CSSR, attach success rate, packet loss
- Security: suspicious access, policy violation, attack signal, certificate or auth anomaly
