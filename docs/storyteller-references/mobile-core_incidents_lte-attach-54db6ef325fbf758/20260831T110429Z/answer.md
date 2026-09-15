# Incident story — mobile-core/incidents/lte-attach-54db6ef325fbf758
**Status:** open  **Severity:** SEV-1

incident mobile-core/incidents/lte-attach-54db6ef325fbf758 — SEV-1 open inter-domain correlation impacting LTE Attach across mobile-core-control-plane, ran, signaling; score 95; intent violated; leading hypothesis: Inter-Domain alarm correlation impacting LTE Attach across mobile-core-control-plane, ran, signaling

**Impact:**
- Service: LTE Attach
- Component: mme-01 (mme, mobile-core-control-plane)
- Component: enodeb-17 (enodeb, ran)
- Component: hss-01 (hss, signaling)

**Leading hypothesis:** Inter-Domain alarm correlation impacting LTE Attach across mobile-core-control-plane, ran, signaling (status: plausible)

**Correlation:** inter-domain; domains: mobile-core-control-plane, ran, signaling; score: 95; intent: violated

**Why these alarms were grouped:**
- multiple alarms in the correlation window
- shared affected service
- KPI breach supports service impact
- independent operational evidence
- service intent is violated
- critical source alarm
- novel alarm signature retained for review

**Causal chain:**
- KPI degradation: 4G Attach SR breached for lte-attach. (CORRELATION)
- Hypothesis: Inter-Domain alarm correlation impacting LTE Attach across mobile-core-control-plane, ran, signaling (HYPOTHESIS)
- Evidence: Alarm DIAMETER_ULR_TIMEOUTS_HIGH observed on hss-01. (EVIDENCE)
- Evidence: Alarm ATTACH_REJECT_RATE_HIGH observed on mme-01. (EVIDENCE)
- Evidence: Alarm S1AP_INITIAL_UE_MSG_DROP observed on enodeb-17. (EVIDENCE)
- Evidence: MME attach reject logs increased (EVIDENCE)
- Evidence: 4G Attach SR dropped below intent target (EVIDENCE)

**Supporting evidence:**
- Alarm DIAMETER_ULR_TIMEOUTS_HIGH observed on hss-01.
- Alarm ATTACH_REJECT_RATE_HIGH observed on mme-01.
- Alarm S1AP_INITIAL_UE_MSG_DROP observed on enodeb-17.
- MME attach reject logs increased
- 4G Attach SR dropped below intent target

**Timeline:**
- **2026-08-31T08:20:00+00:00** - Critical mobile-core-control-plane alarm ATTACH_REJECT_RATE_HIGH on mme-01
- **2026-08-31T08:21:00+00:00** - Major signaling alarm DIAMETER_ULR_TIMEOUTS_HIGH on hss-01
- **2026-08-31T08:22:00+00:00** - MME attach reject logs increased
- **2026-08-31T08:23:00+00:00** - Major ran alarm S1AP_INITIAL_UE_MSG_DROP on enodeb-17
- **2026-08-31T08:25:00+00:00** - 4G Attach SR dropped below intent target

**Still open:**
- root cause is not confirmed
- no remediation recorded
- no recovery observed