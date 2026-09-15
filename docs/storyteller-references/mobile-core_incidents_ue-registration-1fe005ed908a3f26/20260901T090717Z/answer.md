# Incident story — mobile-core/incidents/ue-registration-1fe005ed908a3f26
**Status:** open  **Severity:** SEV-1

incident mobile-core/incidents/ue-registration-1fe005ed908a3f26 — SEV-1 open inter-domain correlation impacting UE Registration across mobile-core, ran, transport; score 95; intent violated; leading hypothesis: Inter-Domain alarm correlation impacting UE Registration across mobile-core, ran, transport

**Impact:**
- Service: UE Registration
- Component: core-amf-01 (amf, mobile-core)
- Component: ran-gnodeb-17 (gnodeb, ran)
- Component: transport-agg-sw-03 (aggregation-switch, transport)

**Leading hypothesis:** Inter-Domain alarm correlation impacting UE Registration across mobile-core, ran, transport (status: plausible)

**Correlation:** inter-domain; domains: mobile-core, ran, transport; score: 95; intent: violated

**Why these alarms were grouped:**
- multiple alarms in the correlation window
- shared affected service
- KPI breach supports service impact
- independent operational evidence
- service intent is violated
- critical source alarm
- novel alarm signature retained for review

**Causal chain:**
- KPI degradation: service KPI breached for ue-registration. (CORRELATION)
- Hypothesis: Inter-Domain alarm correlation impacting UE Registration across mobile-core, ran, transport (HYPOTHESIS)
- Evidence: Alarm LINK_DOWN observed on ran-gnodeb-17. (EVIDENCE)
- Evidence: Alarm INTERFACE_ERRORS observed on transport-agg-sw-03. (EVIDENCE)
- Evidence: Alarm CPU_HIGH observed on core-amf-01. (EVIDENCE)
- Evidence: KPI breach for ue-registration (EVIDENCE)
- Evidence: TICKET observation for ue-registration (EVIDENCE)

**Supporting evidence:**
- Alarm LINK_DOWN observed on ran-gnodeb-17.
- Alarm INTERFACE_ERRORS observed on transport-agg-sw-03.
- Alarm CPU_HIGH observed on core-amf-01.
- KPI breach for ue-registration
- TICKET observation for ue-registration

**Timeline:**
- **2026-08-28T10:00:00+00:00** - Critical ran alarm LINK_DOWN on ran-gnodeb-17
- **2026-08-28T10:02:00+00:00** - Major transport alarm INTERFACE_ERRORS on transport-agg-sw-03
- **2026-08-28T10:04:00+00:00** - Major mobile-core alarm CPU_HIGH on core-amf-01
- **2026-08-28T10:05:00+00:00** - KPI breach for ue-registration
- **2026-08-28T10:06:00+00:00** - TICKET observation for ue-registration

**Still open:**
- root cause is not confirmed
- no remediation recorded
- no recovery observed