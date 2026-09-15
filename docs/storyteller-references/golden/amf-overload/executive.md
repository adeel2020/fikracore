# Executive summary — mobile-core/incidents/amf-overload-2026-08-09
**Status:** resolved  **Severity:** SEV-2

incident mobile-core/incidents/amf-overload-2026-08-09 — severity SEV-2, root cause: AMF-01 CPU saturation from registration signaling burst, affected service: UE Registration Service, 1 remediation(s) applied, recovery observed
**Root cause (confirmed):** AMF-01 CPU saturation from registration signaling burst
**Impacted:** UE Registration Service, AMF-01 (Access and Mobility Management Function), SMF-01 (Session Management Function)
**Evidence:** AMF-01 CPU utilization pegged at 98%; NAS REGISTRATION REJECT 'congestion' cause codes
**Actions taken:** Scale out AMF-01 and throttle registration signaling
