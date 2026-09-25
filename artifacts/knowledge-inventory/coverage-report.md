# FikraCore Knowledge Coverage & Topology Report

- **Overall Coverage Score**: **`57.8%` (PARTIALLY_COVERED)**
- **Formula**: `25% entity_cov + 25% rel_cov + 20% service_cov + 15% evidence_cov + 15% validated_cov`
- **Timestamp**: `2026-09-24T18:22:23.504609+00:00`

## 1. Domain Coverage Matrix

| Domain | Entity Cov | Rel Cov | Service Cov | Evidence Cov | Validated Cov | Composite Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mobile Core** | 83.3% | 80.0% | 0.0% | 0.0% | 100.0% | **55.8%** | `PARTIALLY_COVERED` |
| **Other** | 20.0% | 100.0% | 0.0% | 0.0% | 100.0% | **45.0%** | `PARTIALLY_COVERED` |
| **IMS** | 83.3% | 60.0% | 0.0% | 0.0% | 100.0% | **50.8%** | `PARTIALLY_COVERED` |
| **OSS/BSS** | 100.0% | 90.5% | 0.0% | 0.0% | 100.0% | **62.6%** | `PARTIALLY_COVERED` |
| **OCS** | 80.0% | 62.5% | 0.0% | 0.0% | 100.0% | **50.6%** | `PARTIALLY_COVERED` |
| **Cross-Domain Operations** | 100.0% | 28.6% | 0.0% | 0.0% | 100.0% | **47.1%** | `PARTIALLY_COVERED` |
| **Transport** | 100.0% | 94.7% | 0.0% | 0.0% | 100.0% | **63.7%** | `PARTIALLY_COVERED` |
| **Cloud/NFVI** | 100.0% | 27.3% | 100.0% | 0.0% | 100.0% | **66.8%** | `PARTIALLY_COVERED` |
| **RAN** | 35.0% | 85.7% | 100.0% | 0.0% | 100.0% | **65.2%** | `PARTIALLY_COVERED` |

## 2. Cross-Domain Dependency Coverage (§24)

| Source Domain | Target Domain | Known Links | Status |
| :--- | :--- | :--- | :--- |
| **Mobile Core** | **Transport** | 2 | `SPARSE` |
| **Mobile Core** | **OCS** | 3 | `SPARSE` |
| **IMS** | **Transport** | 1 | `SPARSE` |
| **Mobile Core** | **RAN** | 11 | `CONNECTED` |
| **Mobile Core** | **IMS** | 0 | `UNLINKED` |

## 3. Telemetry & Observability Layer Instrumentation

- **Overall Instrumentation Coverage**: **`3.7%` (PARTIALLY_INSTRUMENTED)**
- **Total Telemetry Artifacts**: `0` (Logs: 0, Metrics: 0, Traces: 0, Alerts: 0)
- **Monitored Network Functions / Services**: `4`
- **Active Telemetry Linkages**: `0`

## 4. Service Topology Completeness (§35)

| Service | Domain | Functions Mapped | Transport Path | Charging | Monitoring | Completeness |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **3G Mobile Data** | Mobile Core | 0 | No | No | No | **25.0%** |
| **LTE Mobile Data** | Mobile Core | 0 | No | No | No | **25.0%** |
| **5G NSA Mobile Data** | Mobile Core | 0 | No | No | No | **25.0%** |
| **5G SA Mobile Data** | Mobile Core | 0 | No | No | No | **25.0%** |
| **3G Voice** | Other | 0 | No | No | No | **25.0%** |
| **VoLTE** | Mobile Core | 0 | No | No | No | **25.0%** |
| **Mobile IMS Voice** | IMS | 0 | No | No | No | **25.0%** |
| **Fixed IMS Voice** | IMS | 0 | Yes | No | No | **50.0%** |
| **Mobile Originated SMS** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **Mobile Terminated SMS** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **Enterprise SMS via ESME** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **USSD** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **Prepaid Recharge** | OCS | 0 | No | No | No | **25.0%** |
| **Prepaid Balance Inquiry** | OCS | 0 | No | No | No | **25.0%** |
| **Online Charging for Data** | OCS | 0 | No | No | No | **25.0%** |
| **Roaming Data** | Cross-Domain Operations | 0 | No | No | No | **25.0%** |
| **Roaming Voice** | Cross-Domain Operations | 0 | No | No | No | **25.0%** |
| **Subscriber Provisioning** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **SIM and Service Activation** | Other | 0 | No | No | No | **25.0%** |
| **GPON Broadband** | Transport | 0 | Yes | No | No | **50.0%** |
| **Fixed Broadband Authentication** | Transport | 0 | Yes | No | No | **50.0%** |
| **Enterprise MPLS VPN** | Transport | 0 | Yes | No | No | **50.0%** |
| **Internet Peering Service** | Transport | 0 | Yes | No | No | **50.0%** |
| **VAS Short-Code Service** | OSS/BSS | 0 | No | No | No | **25.0%** |
| **OSS to Network Management Connectivity** | OSS/BSS | 0 | No | No | No | **25.0%** |

---
*Generated automatically by FikraCore Step 4.7 Knowledge Coverage Harness.*