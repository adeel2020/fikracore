# FikraCore Knowledge Inventory Report

- **Brain Identity**: `telecombrain`
- **Schema Identity**: `mobile-core@0.1.0+2eea5e14`
- **Retrieved At**: `2026-09-19T19:57:53.537115+00:00`
- **Total Pages**: `132`
- **Total Unique Relationships**: `190`
- **Overall Health Status**: **`Healthy`**
- **Overall Coverage Score**: **`68.5%` (PARTIALLY_COVERED)**

## 1. Executive Summary

Telecombrain currently contains **132 pages** across **5 domains** and **190 unique operational relationships**.
The dominant operational domain is **Mobile Core** with **102 entities**.
There are **2 operational orphans**, **0 unresolved aliases**, and **15 stale knowledge records**.

## 2. Domain Distribution

| Domain | Entities | Services | Network Functions | Incidents | Relationships | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Domain Operations** | 24 | 0 | 0 | 8 | 135 | `WELL_COVERED` |
| **Mobile Core** | 102 | 6 | 21 | 0 | 158 | `PARTIALLY_COVERED` |
| **RAN** | 2 | 0 | 2 | 0 | 6 | `PARTIALLY_COVERED` |
| **Transport** | 2 | 0 | 2 | 0 | 6 | `PARTIALLY_COVERED` |
| **Other** | 2 | 0 | 0 | 0 | 0 | `SPARSE` |

## 3. Knowledge Type Breakdown

| Knowledge Type | Count | Percentage |
| :--- | :--- | :--- |
| `evidence` | 25 | 18.9% |
| `network-function` | 16 | 12.1% |
| `hypothesis` | 10 | 7.6% |
| `kpi-event` | 9 | 6.8% |
| `domain-function` | 9 | 6.8% |
| `incident` | 8 | 6.1% |
| `kpi` | 8 | 6.1% |
| `concept` | 7 | 5.3% |
| `service` | 6 | 4.5% |
| `learning-note` | 3 | 2.3% |
| `query-asset` | 3 | 2.3% |
| `playbook` | 3 | 2.3% |
| `story-run` | 3 | 2.3% |
| `story` | 3 | 2.3% |
| `service-procedure` | 3 | 2.3% |
| `correlation-decision` | 3 | 2.3% |
| `correlation-cluster` | 3 | 2.3% |
| `incident-alias` | 3 | 2.3% |
| `note` | 2 | 1.5% |
| `ticket-journey` | 1 | 0.8% |
| `procedure` | 1 | 0.8% |
| `observation` | 1 | 0.8% |
| `remediation` | 1 | 0.8% |
| `symptom` | 1 | 0.8% |

## 4. Knowledge States & Epistemic Segregation

| State | Count | Percentage |
| :--- | :--- | :--- |
| **`CONFIRMED`** | 105 | 79.5% |
| **`INFERRED`** | 3 | 2.3% |
| **`CANDIDATE`** | 9 | 6.8% |
| **`STALE`** | 15 | 11.4% |
| **`STATE_NOT_AVAILABLE`** | 0 | 0.0% |

## 5. Prioritized Operational Gaps

1. **[LOW] ORPHAN_ENTITY** (`mobile-core/incidents/sgi-throughput-drop`): Operational entity 'Sgi Throughput Drop' (incident) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'mobile-core/incidents/sgi-throughput-drop' into the operational graph.
2. **[LOW] ORPHAN_ENTITY** (`tickets/mobile-core/tt-984210`): Operational entity 'Trouble Ticket TT-984210 Journey' (ticket-journey) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'tickets/mobile-core/tt-984210' into the operational graph.
3. **[MEDIUM] SPARSE_DOMAIN** (`RAN`): Domain 'RAN' has sparse representation (2 entities).
   - *Recommendation*: Ingest topology and service definitions for domain 'RAN'.
4. **[MEDIUM] SPARSE_DOMAIN** (`Transport`): Domain 'Transport' has sparse representation (2 entities).
   - *Recommendation*: Ingest topology and service definitions for domain 'Transport'.
5. **[HIGH] INCOMPLETE_CROSS_DOMAIN_COVERAGE** (`Mobile Core ↔ Transport`): Direct operational transport conduit missing between 'Mobile Core' and 'Transport'.
   - *Recommendation*: Define direct transport routing and inter-domain links connecting Mobile Core functions to Transport.
6. **[HIGH] INCOMPLETE_CROSS_DOMAIN_COVERAGE** (`Mobile Core ↔ OCS`): Direct operational transport conduit missing between 'Mobile Core' and 'OCS'.
   - *Recommendation*: Define direct transport routing and inter-domain links connecting Mobile Core functions to OCS.
7. **[HIGH] INCOMPLETE_CROSS_DOMAIN_COVERAGE** (`IMS ↔ Transport`): Direct operational transport conduit missing between 'IMS' and 'Transport'.
   - *Recommendation*: Define direct transport routing and inter-domain links connecting IMS functions to Transport.

---
*Generated automatically by FikraCore Step 4.7 Knowledge Inventory Harness.*