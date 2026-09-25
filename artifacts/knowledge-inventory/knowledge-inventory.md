# FikraCore Knowledge Inventory Report

- **Brain Identity**: `telecombrain`
- **Schema Identity**: `mobile-core@0.1.0+2eea5e14`
- **Retrieved At**: `2026-09-24T18:22:23.504609+00:00`
- **Total Pages**: `117`
- **Total Unique Relationships**: `76`
- **Overall Health Status**: **`Needs Attention`**
- **Overall Coverage Score**: **`57.8%` (PARTIALLY_COVERED)**

## 1. Executive Summary

Telecombrain currently contains **117 pages** across **9 domains** and **76 unique operational relationships**.
The dominant operational domain is **Mobile Core** with **25 entities**.
There are **25 operational orphans**, **0 unresolved aliases**, and **0 stale knowledge records**.

## 2. Domain Distribution

| Domain | Entities | Services | Network Functions | Incidents | Relationships | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mobile Core** | 25 | 5 | 20 | 0 | 28 | `PARTIALLY_COVERED` |
| **Other** | 2 | 2 | 0 | 0 | 2 | `PARTIALLY_COVERED` |
| **IMS** | 10 | 2 | 8 | 0 | 6 | `PARTIALLY_COVERED` |
| **OSS/BSS** | 21 | 7 | 14 | 0 | 19 | `PARTIALLY_COVERED` |
| **OCS** | 8 | 3 | 5 | 0 | 6 | `PARTIALLY_COVERED` |
| **Cross-Domain Operations** | 14 | 2 | 3 | 0 | 3 | `PARTIALLY_COVERED` |
| **Transport** | 19 | 4 | 15 | 0 | 21 | `PARTIALLY_COVERED` |
| **Cloud/NFVI** | 11 | 0 | 11 | 0 | 5 | `PARTIALLY_COVERED` |
| **RAN** | 7 | 0 | 7 | 0 | 21 | `PARTIALLY_COVERED` |

## 3. Knowledge Type Breakdown

| Knowledge Type | Count | Percentage |
| :--- | :--- | :--- |
| `network-function` | 83 | 70.9% |
| `service` | 25 | 21.4% |
| `concept` | 9 | 7.7% |

## 4. Knowledge States & Epistemic Segregation

| State | Count | Percentage |
| :--- | :--- | :--- |
| **`CONFIRMED`** | 117 | 100.0% |
| **`INFERRED`** | 0 | 0.0% |
| **`CANDIDATE`** | 0 | 0.0% |
| **`STALE`** | 0 | 0.0% |
| **`STATE_NOT_AVAILABLE`** | 0 | 0.0% |

## 5. Prioritized Operational Gaps

1. **[LOW] ORPHAN_ENTITY** (`ext:vas:001`): Operational entity 'Third Party VAS Gateway' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'ext:vas:001' into the operational graph.
2. **[LOW] ORPHAN_ENTITY** (`infra:dc:a`): Operational entity 'DC-A Facility' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:dc:a' into the operational graph.
3. **[LOW] ORPHAN_ENTITY** (`infra:dc:b`): Operational entity 'DC-B Facility' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:dc:b' into the operational graph.
4. **[LOW] ORPHAN_ENTITY** (`infra:power:a`): Operational entity 'DC-A Power Feed A' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:power:a' into the operational graph.
5. **[LOW] ORPHAN_ENTITY** (`infra:cool:a`): Operational entity 'DC-A Cooling Plant' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:cool:a' into the operational graph.
6. **[LOW] ORPHAN_ENTITY** (`infra:nfvi:a`): Operational entity 'NFVI Cluster A' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:nfvi:a' into the operational graph.
7. **[LOW] ORPHAN_ENTITY** (`infra:db:subs-a`): Operational entity 'Subscriber DB Cluster A' (network-function) has no incoming or outgoing topology relationships.
   - *Recommendation*: Add dependency or service link to connect 'infra:db:subs-a' into the operational graph.

---
*Generated automatically by FikraCore Step 4.7 Knowledge Inventory Harness.*