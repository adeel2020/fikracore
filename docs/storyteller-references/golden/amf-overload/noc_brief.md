# NOC engineer brief — mobile-core/incidents/amf-overload-2026-08-09
**Lifecycle:** resolved  **Severity:** SEV-2

**Operational summary:**
incident mobile-core/incidents/amf-overload-2026-08-09 — severity SEV-2, root cause: AMF-01 CPU saturation from registration signaling burst, affected service: UE Registration Service, 1 remediation(s) applied, recovery observed

**Affected services/components:**
- UE Registration Service (affects)
- AMF-01 (Access and Mobility Management Function) (involves)
- SMF-01 (Session Management Function) (involves)

**Evidence to check:**
- AMF-01 CPU utilization pegged at 98%
- NAS REGISTRATION REJECT 'congestion' cause codes

**Immediate actions:**
- verify remediation: Scale out AMF-01 and throttle registration signaling
