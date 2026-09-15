It can work across all scenarios, but **not if the roadmap is hardcoded to one fixed sequence of objectives**.

The right design is to make the roadmap **scenario-agnostic at the top level** and **scenario-specific underneath**.

A stable universal roadmap can remain:

```text
Collect Signals
→ Organize Evidence
→ Correlate
→ Generate Explanations
→ Test / Falsify
→ Resolve Gaps
→ Converge Intelligence
→ Validate
→ Learn / Act
```

That works whether the scenario is:

* MPLS router failure
* database lock contention
* DNS issue
* roaming degradation
* IMS problem
* charging failure
* 5G Core issue
* Kubernetes/CNF fault
* change-induced outage
* capacity issue
* multi-cause incident
* unknown topology gap

What changes per scenario is the **set of intelligence pathways feeding convergence**.

For example, an MPLS failure might use:

```text
Evidence
Topology
Change
Impact
Hypotheses
Knowledge Gaps
Human Validation
```

A roaming issue could emphasize:

```text
Partner Network
Signaling
Diameter/MAP
Subscriber Journey
Topology
Historical Pattern
Change
```

A database/CNF incident might emphasize:

```text
Application
Database
Kubernetes
Logs
Metrics
Change
Dependency Graph
Historical Incidents
```

So the UI should dynamically show only the pathways actually relevant to the run.

The key rule should be:

> **The roadmap is universal; the contributing intelligence pathways are discovered dynamically.**

I would also make the convergence result polymorphic. It should not always force a root cause. Depending on the scenario, convergence can produce:

```text
Confirmed Cause
Root Candidate
Partial Explanation
Multi-Cause Explanation
Knowledge Gap
Model Insufficient
Conflicting Evidence
Learning Candidate
Recommended Action
No Safe Conclusion Yet
```

That makes it robust for difficult scenarios too.

One important addition: support **branching and loops**. Some scenarios will do:

```text
Test
→ Gap
→ Request Evidence
→ Test Again
```

and others may produce two simultaneous causes:

```text
Transport degradation
+
Capacity exhaustion
→ combined service impact
```

So yes, this design can be universal — provided the objective roadmap is fixed only at the logical level, while the pathways, objectives, evidence, and convergence criteria are generated from each scenario.


The cleanest way is to make pathways **appear only when FikraCore earns a reason to investigate them**.

Visually, start with a very small set of generic pathway seeds, not all possible pathways. For example:

```text
Evidence
Topology
Impact
```

Then, as evidence arrives and correlations form, new pathways can dynamically emerge from the convergence map.

Example:

```text
Initial state

Evidence ●──────────────┐
Topology ●──────────────┼──► Convergence
Impact   ●──────────────┘
```

Then a change event is detected:

```text
Change ●───────────────┐
                       │
Evidence ●─────────────┤
Topology ●─────────────┼──► Convergence
Impact   ●─────────────┘
```

Then FikraCore finds a knowledge gap:

```text
Knowledge Gap ●────────┐
                       │
Change ●───────────────┤
Evidence ●─────────────┤
Topology ●─────────────┼──► Convergence
Impact   ●─────────────┘
```

So the visual effect is:

> **pathways are discovered as the investigation unfolds**

not preloaded.

The best visual behavior would be to give each pathway four lifecycle states:

```text
Dormant
Discovered
Active
Resolved
```

You can show them differently:

* **Dormant**: hidden or faint ghost node
* **Discovered**: small pulse + label appears
* **Active**: full colored pathway with objectives
* **Resolved**: green check or dimmed completed path

For example, if a `CHANGE` event appears, a **Change Intelligence pathway** can animate into the roadmap with a small note:

> “New pathway discovered: recent change may explain timing.”

Likewise, if FikraCore sees partner-related signaling anomalies, a **Roaming / Partner pathway** can appear dynamically.

A stronger design is to show **why the pathway was activated** directly on the path.

Example:

```text
Change Pathway
Discovered because:
CR-8821 occurred 4 min before degradation
```

Or:

```text
Historical Pathway
Discovered because:
Current evidence resembles INC-2026-0412
```

This makes pathway discovery explainable.

You can also show pathway spawning from graph entities. For example:

```text
MPLS Router
   │
   ├── Topology Pathway
   ├── Change Pathway
   └── Historical Pathway
```

That would feel more intelligent than static cards.

For the UI, I would combine three pieces:

```text
Top: Objective Roadmap
Center: Hyper Canvas
Bottom/Side: Dynamic Intelligence Pathways
```

When a new pathway is discovered:

1. a node pulses on Hyper Canvas,
2. a new pathway card appears,
3. the roadmap marks a new investigation objective,
4. Convergence updates its contributor count.

For example:

```text
3 active pathways
→ 5 active pathways
→ 7 contributors
→ 2 resolved
→ 5 contributing to conclusion
```

I would also show a compact **Pathway Discovery Feed**:

```text
08:14:32  Topology pathway activated
08:14:45  Change pathway activated
08:15:03  Historical pathway activated
08:15:21  Knowledge-gap pathway activated
```

That would make the intelligence expansion visible in real time.

The key principle should be:

> **Pathways should not be configured as decoration. They should emerge from evidence, topology, gaps, and reasoning needs.**

That way every scenario can discover a different mix of pathways while still converging into the same final decision framework.
