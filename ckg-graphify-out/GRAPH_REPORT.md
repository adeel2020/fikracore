# Graph Report - .  (2026-06-11)

## Corpus Check
- 1 files · ~1,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 38 nodes · 57 edges · 7 communities (6 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Subscriber Mobile App Cluster|Subscriber Mobile App Cluster]]
- [[_COMMUNITY_Voice Call Drops Cluster|Voice Call Drops Cluster]]
- [[_COMMUNITY_Unified CRM System Cluster|Unified CRM System Cluster]]
- [[_COMMUNITY_5G Speed Degradation Cluster|5G Speed Degradation Cluster]]
- [[_COMMUNITY_eSIM & Provisioning Support Cluster|eSIM & Provisioning Support Cluster]]
- [[_COMMUNITY_Roaming Connection Fail Cluster|Roaming Connection Fail Cluster]]
- [[_COMMUNITY_Postpaid Corporate Cluster|Postpaid Corporate Cluster]]

## God Nodes (most connected - your core abstractions)
1. `eSIM & Provisioning Support` - 9 edges
2. `Unified CRM System` - 6 edges
3. `5G Speed Degradation` - 5 edges
4. `eSIM Activation Failure` - 5 edges
5. `Voice Call Drops` - 5 edges
6. `Roaming Connection Fail` - 5 edges
7. `SM-DP+ eSIM Server` - 5 edges
8. `Carrier Inter-Roaming Support` - 5 edges
9. `Subscriber Mobile App` - 5 edges
10. `5G Packet Router (UPF)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `5G Speed Degradation` --observed_on--> `Android App Client`  [EXTRACTED]
  backend/agent/causal_rules.yaml → backend/agent/causal_rules.yaml  _Bridges community 3 → community 0_
- `eSIM Activation Failure` --owned_by--> `eSIM & Provisioning Support`  [EXTRACTED]
  backend/agent/causal_rules.yaml → backend/agent/causal_rules.yaml  _Bridges community 0 → community 4_
- `eSIM Activation Failure` --requires--> `SIM Active Registry`  [EXTRACTED]
  backend/agent/causal_rules.yaml → backend/agent/causal_rules.yaml  _Bridges community 0 → community 1_
- `Voice Call Drops` --indicates--> `Low SINR (RF Noise)`  [EXTRACTED]
  backend/agent/causal_rules.yaml → backend/agent/causal_rules.yaml  _Bridges community 1 → community 3_
- `Voice Call Drops` --common_in--> `Prepaid Subscriber`  [EXTRACTED]
  backend/agent/causal_rules.yaml → backend/agent/causal_rules.yaml  _Bridges community 1 → community 2_

## Import Cycles
- None detected.

## Communities (7 total, 1 thin omitted)

### Community 0 - "Subscriber Mobile App Cluster"
Cohesion: 0.43
Nodes (7): Android App Client, iOS App Client, Subscriber Mobile App, eSIM Profile Mismatch, Caller Tune Activation & Cancellation, eSIM Activation Failure, SM-DP+ eSIM Server

### Community 1 - "Voice Call Drops Cluster"
Cohesion: 0.38
Nodes (7): Call Barring Management, Call Forwarding Activation, Voice Call Drops, Core Switching & IMS Team, VoLTE Device Support, SIM Active Registry, IMS VoLTE Signaling Core

### Community 2 - "Unified CRM System Cluster"
Cohesion: 0.40
Nodes (6): USSD Code Dial, Insufficient balance code, Billing Fallback, Cancel Amazon Prime Subscription, Unified CRM System, Prepaid Subscriber

### Community 3 - "5G Speed Degradation Cluster"
Cohesion: 0.53
Nodes (6): Low SINR (RF Noise), Network Fallback, 5G Speed Degradation, Radio Access Network (RAN) Team, 5G Provisioned SIM, 5G Packet Router (UPF)

### Community 4 - "eSIM & Provisioning Support Cluster"
Cohesion: 0.33
Nodes (6): Provisioning Fallback, Activate 12 Months Free Amazon Prime, Caller Number Presentation (CNAP), Do Not Call Registry (DNCR), eSIM Replacement & Multi-device Watch, eSIM & Provisioning Support

### Community 5 - "Roaming Connection Fail Cluster"
Cohesion: 0.70
Nodes (5): PLMN Forbidden Error, Roaming Connection Fail, Carrier Inter-Roaming Support, Roaming Agreement, VLR Roaming Gateway

## Knowledge Gaps
- **10 isolated node(s):** `Cancel Amazon Prime Subscription`, `Activate 12 Months Free Amazon Prime`, `Call Forwarding Activation`, `Caller Number Presentation (CNAP)`, `Do Not Call Registry (DNCR)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `eSIM & Provisioning Support` connect `eSIM & Provisioning Support Cluster` to `Subscriber Mobile App Cluster`, `Unified CRM System Cluster`?**
  _High betweenness centrality (0.316) - this node is a cross-community bridge._
- **Why does `Unified CRM System` connect `Unified CRM System Cluster` to `Subscriber Mobile App Cluster`, `eSIM & Provisioning Support Cluster`?**
  _High betweenness centrality (0.305) - this node is a cross-community bridge._
- **Why does `Voice Call Drops` connect `Voice Call Drops Cluster` to `Unified CRM System Cluster`, `5G Speed Degradation Cluster`?**
  _High betweenness centrality (0.235) - this node is a cross-community bridge._
- **What connects `Cancel Amazon Prime Subscription`, `Activate 12 Months Free Amazon Prime`, `Call Forwarding Activation` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._