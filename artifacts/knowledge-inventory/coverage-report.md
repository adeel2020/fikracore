# FikraCore Knowledge Coverage & Topology Report

- **Overall Coverage Score**: **`68.5%` (PARTIALLY_COVERED)**
- **Formula**: `25% entity_cov + 25% rel_cov + 20% service_cov + 15% evidence_cov + 15% validated_cov`
- **Timestamp**: `2026-09-19T19:57:53.537115+00:00`

## 1. Domain Coverage Matrix

| Domain | Entity Cov | Rel Cov | Service Cov | Evidence Cov | Validated Cov | Composite Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Domain Operations** | 100.0% | 91.7% | 100.0% | 0.0% | 70.8% | **78.5%** | `WELL_COVERED` |
| **Mobile Core** | 100.0% | 99.0% | 0.0% | 50.0% | 82.4% | **69.6%** | `PARTIALLY_COVERED` |
| **RAN** | 10.0% | 100.0% | 100.0% | 0.0% | 100.0% | **62.5%** | `PARTIALLY_COVERED` |
| **Transport** | 13.3% | 100.0% | 100.0% | 0.0% | 100.0% | **63.3%** | `PARTIALLY_COVERED` |
| **Other** | 20.0% | 0.0% | 100.0% | 0.0% | 0.0% | **25.0%** | `SPARSE` |

## 2. Cross-Domain Dependency Coverage (§24)

| Source Domain | Target Domain | Known Links | Status |
| :--- | :--- | :--- | :--- |
| **Mobile Core** | **Transport** | 4 | `SPARSE` |
| **Mobile Core** | **OCS** | 0 | `UNLINKED` |
| **IMS** | **Transport** | 0 | `UNLINKED` |
| **Mobile Core** | **RAN** | 4 | `SPARSE` |
| **Mobile Core** | **IMS** | 0 | `UNLINKED` |

## 3. Telemetry & Observability Layer Instrumentation

- **Overall Instrumentation Coverage**: **`100.0%` (INSTRUMENTED)**
- **Total Telemetry Artifacts**: `46` (Logs: 4, Metrics: 21, Traces: 1, Alerts: 14)
- **Monitored Network Functions / Services**: `78`
- **Active Telemetry Linkages**: `0`

## 4. Service Topology Completeness (§35)

| Service | Domain | Functions Mapped | Transport Path | Charging | Monitoring | Completeness |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LTE Attach** | Mobile Core | 0 | No | No | No | **25.0%** |
| **SGI Data** | Mobile Core | 0 | No | No | No | **25.0%** |
| **Voice Call Setup** | Mobile Core | 0 | No | No | No | **25.0%** |
| **UE Registration** | Mobile Core | 0 | No | No | No | **25.0%** |
| **Site Power** | Mobile Core | 0 | No | No | No | **25.0%** |
| **UE Registration Service** | Mobile Core | 0 | No | No | No | **25.0%** |

---
*Generated automatically by FikraCore Step 4.7 Knowledge Coverage Harness.*