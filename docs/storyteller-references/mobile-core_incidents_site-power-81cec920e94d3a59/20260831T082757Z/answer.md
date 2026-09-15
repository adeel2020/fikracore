# Incident story — mobile-core/incidents/site-power-81cec920e94d3a59
**Status:** candidate  **Severity:** SEV-1

incident mobile-core/incidents/site-power-81cec920e94d3a59 — SEV-1 candidate intra-domain correlation impacting Site Power across power; score 30; intent not_matched; leading hypothesis: Intra-Domain alarm correlation impacting Site Power across power

**Impact:**
- Service: Site Power
- Component: power-ups-77 (ups, power)

**Leading hypothesis:** Intra-Domain alarm correlation impacting Site Power across power (status: plausible)

**Correlation:** intra-domain; domains: power; score: 30; intent: not_matched

**Why these alarms were grouped:**
- shared affected service
- critical source alarm
- novel alarm signature retained for review

**Causal chain:**
- Hypothesis: Intra-Domain alarm correlation impacting Site Power across power (HYPOTHESIS)
- Evidence: Alarm BATTERY_LOW observed on power-ups-77. (EVIDENCE)

**Supporting evidence:**
- Alarm BATTERY_LOW observed on power-ups-77.

**Timeline:**
- **2026-08-28T10:03:00+00:00** - Critical power alarm BATTERY_LOW on power-ups-77

**Still open:**
- root cause is not confirmed
- no remediation recorded
- no recovery observed