# Mark UI APEX Visual Integration Implementation Plan

## Purpose

Enhance MarkUI by inheriting the strongest visual and interaction design logic
from the APEX-UI project while preserving Mark's actual architecture:

```text
Mark is one assistant.
Mark routes through engines.
Engines own services.
Services use connectors.
gbrain stores semantic context, not raw source data.
```

The goal is not to copy Apex's autonomous-agent model. The goal is to reuse the
cinematic orb, animated reasoning web, trace pulses, status bar, and HUD logic
as the visual grammar for Mark's real engine/service/connector/gbrain model.

## Source UI To Inherit From APEX-UI

APEX-UI source repository:

```text
/Users/adeelarshad/APEX-UI
```

Components to adapt:

```text
/Users/adeelarshad/APEX-UI/components/ShaderBackground.jsx
/Users/adeelarshad/APEX-UI/components/ApexOverviewPanel.tsx
/Users/adeelarshad/APEX-UI/components/ApexCore3D.jsx
/Users/adeelarshad/APEX-UI/components/ApexHeroOrb.tsx
/Users/adeelarshad/APEX-UI/components/ApexOrb.jsx
/Users/adeelarshad/APEX-UI/components/ReasoningWeb.jsx
/Users/adeelarshad/APEX-UI/components/OrbStatusBar.jsx
/Users/adeelarshad/APEX-UI/components/ApexWorld.tsx
/Users/adeelarshad/APEX-UI/components/apex-orb.css
```

Attribution requirement:

```text
ShaderBackground.jsx       MIT community component from 21st.dev.
ApexOverviewPanel.tsx      Contains the overview lamp panel, MIT community
                           component from 21st.dev.
```

Keep attribution in comments and add a Mark-side credits note if these are
copied or substantially adapted.

## Existing MarkUI Target Areas

Current MarkUI entry point:

```text
/Users/adeelarshad/kagent/frontend/src/app/jarvis/page.tsx
```

Current central HUD:

```text
/Users/adeelarshad/kagent/frontend/src/components/hud/CentralHud.tsx
/Users/adeelarshad/kagent/frontend/src/components/hud/TelecomBrain.tsx
/Users/adeelarshad/kagent/frontend/src/components/hud/HudOrb.tsx
/Users/adeelarshad/kagent/frontend/src/components/hud/OrbitalLinks.tsx
/Users/adeelarshad/kagent/frontend/src/components/hud/HudRing.tsx
/Users/adeelarshad/kagent/frontend/src/components/hud/BrainGlow.tsx
```

Current response and visual explanation surfaces:

```text
/Users/adeelarshad/kagent/frontend/src/components/features/agentic-qna-view/components/StorytellerVisualExplanation.tsx
/Users/adeelarshad/kagent/frontend/src/lib/mark-presentation.ts
/Users/adeelarshad/kagent/frontend/src/components/jarvis/JarvisCommandBar.tsx
/Users/adeelarshad/kagent/frontend/src/components/jarvis/OrbDetailModal.tsx
```

Relevant architecture references:

```text
/Users/adeelarshad/kagent/docs/telecom-brain-cognitive-operations-architecture.md
/Users/adeelarshad/kagent/docs/mark-enterprise-capability-registry.md
/Users/adeelarshad/kagent/docs/industry-grade-storyteller-visual-explanation-implementation-plan.md
```

## Correct Mental Model

The orbit hierarchy must represent Mark truthfully.

```text
Mark
 |
 +-- Telecom Brain Engine
 |    |
 |    +-- Correlation Service
 |    +-- Topology Service
 |    +-- Telemetry Evidence Service
 |    +-- Storytelling Service
 |    +-- Incident Registry Service
 |    +-- Intent Service
 |    +-- FCAPS Learning Service
 |
 +-- Knowledge Base Engine
 |
 +-- Automation Engine
 |
 +-- Collaboration Engine
 |
 +-- Calendar Engine
 |
 +-- Codex Engineering Engine
```

Do not place `Telecom Brain`, `Correlation`, `Topology`, `Storytelling`, and
`FCAPS Learning` as peer nodes in the same orbit. `Telecom Brain` is an engine.
Those telecom items are services inside that engine.

## gbrain Namespace Mapping

MarkUI should let the user see what part of gbrain or external evidence source
is involved in each service.

```text
Knowledge Base Engine
  -> knowledge/*
  -> assets/*
  -> Metadata DB
  -> Vector DB

Telecom Brain Engine
  -> domains/*
  -> incidents/*
  -> correlation/*
  -> storytelling/*
  -> learning/*

Topology Service
  -> twin/*
  -> Nautobot / Topology DB

Telemetry Evidence Service
  -> grafana/*
  -> Grafana LGTM

Correlation Service
  -> correlation/*
  -> incidents/*
  -> grafana/*
  -> twin/*
  -> domains/*

Storytelling Service
  -> storytelling/*
  -> incidents/*
  -> correlation/*
  -> evidence claims
  -> provenance

Incident Registry Service
  -> incidents/*
  -> lifecycle state
  -> canonical incident identity

Intent Service
  -> domains/*/intents/*
  -> service objective state
  -> KPI target relationships

FCAPS Learning Service
  -> learning/*
  -> assets/*
  -> proposed context improvements
```

## Desired UI Hierarchy

Use three visual layers around the center.

```text
CENTER
  Mark Core

INNER ORBIT
  Peer engines:
    Telecom Brain
    Knowledge Base
    Automation
    Collaboration
    Calendar
    Codex

EXPANDED SUB-ORBIT
  When Telecom Brain is selected:
    Correlation
    Topology
    Telemetry Evidence
    Storytelling
    Incident Registry
    Intent
    FCAPS Learning

TRACE LAYER
  Runtime path:
    Mark -> Engine -> Service -> Connector -> gbrain namespace
```

## APEX Component Adaptation Plan

### 1. Shader Background

Source:

```text
/Users/adeelarshad/APEX-UI/components/ShaderBackground.jsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkShaderBackground.tsx
```

Adaptation:

```text
Reuse the WebGL plasma wave backdrop.
Drive voice intensity from Mark voice/loading state.
Keep cyan/gold cross-fade behavior.
Add reduced-motion fallback.
Preserve 21st.dev MIT attribution.
```

Usage:

```text
JarvisPage background layer behind the Mark center stage.
```

### 2. Overview Lamp Panel

Source:

```text
/Users/adeelarshad/APEX-UI/components/ApexOverviewPanel.tsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkOverviewPanel.tsx
```

Adaptation:

```text
Reuse the glowing filament HUD interaction.
Remove Apex weather/social behavior.
Replace tiles with Mark operational entries:
  connector health
  current incident
  last route trace
  gbrain namespace browser
  capability registry
Preserve 21st.dev MIT attribution for the lamp panel design.
```

### 3. Central Particle Core

Source:

```text
/Users/adeelarshad/APEX-UI/components/ApexCore3D.jsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkCore3D.tsx
```

Adaptation:

```text
Reuse the Three.js particle core and defensive error boundary.
Rename Apex-specific language to Mark.
Drive particle radius, boil speed, glow, and messenger particles from:
  idle
  listening
  processing
  speaking
  investigating
  waiting_for_approval
  learning
```

### 4. Orb Frame And Hero Shell

Sources:

```text
/Users/adeelarshad/APEX-UI/components/ApexOrb.jsx
/Users/adeelarshad/APEX-UI/components/ApexHeroOrb.tsx
/Users/adeelarshad/APEX-UI/components/apex-orb.css
```

Destinations:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkOrb.tsx
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkHeroOrb.tsx
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/mark-orb.css
```

Adaptation:

```text
Reuse the SVG ring, waveform bars, sound-wave rings, glow, and animation timing.
Replace labels:
  APEX -> MARK
  STANDBY -> READY
  PROCESSING -> ANALYZING
Add Mark-only states:
  INVESTIGATING
  APPROVAL
  LEARNING
Retain prefers-reduced-motion behavior.
```

### 5. Reasoning Web

Source:

```text
/Users/adeelarshad/APEX-UI/components/ReasoningWeb.jsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkReasoningWeb.tsx
```

Adaptation:

```text
Reuse imperative SVG graph drawing and animated trace pulses.
Replace Apex roster with typed Mark capability graph data.
Support two graph modes:
  engine mode
  telecom service mode
Support a runtime route trace:
  Mark -> Engine -> Service -> Connector -> Namespace
Keep an accessible equivalent list of real buttons.
Avoid duplicated roster metadata.
```

### 6. Status Bar

Source:

```text
/Users/adeelarshad/APEX-UI/components/OrbStatusBar.jsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkStatusBar.tsx
```

Adaptation:

```text
Reuse equalizer and bottom state strip.
Show current Mark state.
Show active engine/service.
Show live voice status.
Show current route trace in compact form.
Hide long hints on small screens.
```

### 7. World Composition

Source:

```text
/Users/adeelarshad/APEX-UI/components/ApexWorld.tsx
```

Destination:

```text
/Users/adeelarshad/kagent/frontend/src/components/mark-orb/MarkCognitiveWorld.tsx
```

Adaptation:

```text
Use APEX layer ordering:
  base background
  shader background
  light cast
  reasoning web
  central orb
  tap/listen target
  status bar
  selected detail panel
```

## Shared Data Model

Create one source of truth:

```text
/Users/adeelarshad/kagent/frontend/src/lib/mark-capability-graph.ts
```

Suggested type shape:

```ts
export type MarkCapabilityKind =
  | "engine"
  | "service"
  | "connector"
  | "namespace";

export type MarkCapabilityNode = {
  id: string;
  label: string;
  kind: MarkCapabilityKind;
  parentId?: string;
  color: string;
  icon: string;
  status?: "online" | "standby" | "degraded" | "requires_approval";
  role: string;
  handles: string[];
  namespaces?: string[];
  connectors?: string[];
  actions?: string[];
};

export type MarkRouteTrace = {
  state: MarkVisualState;
  activeEngineId?: string;
  activeServiceIds?: string[];
  activeConnectorIds?: string[];
  activeNamespaces?: string[];
  claimIds?: string[];
};
```

Initial engine nodes:

```text
telecom_brain
knowledge_base
automation
collaboration
calendar
codex_engineering
```

Initial Telecom Brain service nodes:

```text
correlation
topology
telemetry_evidence
storytelling
incident_registry
intent
fcaps_learning
```

Initial connector nodes:

```text
gbrain
grafana_lgtm
nautobot
metadata_db
vector_db
gmail
whatsapp
teams
office
google_calendar
codex
```

Initial namespace nodes:

```text
knowledge/*
assets/*
domains/*
twin/*
grafana/*
correlation/*
incidents/*
storytelling/*
learning/*
```

## Runtime State Mapping

Map existing MarkUI state to visual state:

```text
input focused / live voice listening
  -> listening

isLoading true
  -> processing

Storyteller visual explanation open
  -> investigating

jarvisVoice speaking
  -> speaking

next action requires approval
  -> waiting_for_approval

learning note / asset proposal present
  -> learning

no active turn
  -> idle
```

## Route Trace Mapping

Expand the current `presentationOrb()` idea into a richer route trace.

Current file:

```text
/Users/adeelarshad/kagent/frontend/src/lib/mark-presentation.ts
```

Target behavior:

```text
visual_explanation.primary_widget contains "topology"
  -> Telecom Brain
  -> Topology
  -> gbrain/twin/*
  -> Nautobot if provenance mentions topology authority

primary_widget contains "evidence", "kpi", "timeline"
  -> Telecom Brain
  -> Telemetry Evidence
  -> Grafana LGTM
  -> grafana/*

primary_widget contains "correlation", "causal"
  -> Telecom Brain
  -> Correlation
  -> correlation/*

payload intent is story
  -> Telecom Brain
  -> Storytelling
  -> storytelling/*

narrative contains next_actions
  -> Automation

narrative or visual contains FCAPS tags
  -> Telecom Brain
  -> FCAPS Learning
```

## Node Detail Panel Model

Replace static modal copy in:

```text
/Users/adeelarshad/kagent/frontend/src/components/jarvis/OrbDetailModal.tsx
```

With capability graph-backed detail panels.

Each node panel should show:

```text
role
status
parent engine/service
connected namespaces
connected connectors
available actions
approval requirement
recent route trace
```

Example:

```text
Telemetry Evidence Service
  Parent: Telecom Brain Engine
  Connectors: Grafana LGTM
  Namespaces: grafana/*
  Handles: metrics, logs, traces, alerts, dashboards
  Actions: inspect evidence, fetch KPI history, list dashboards
```

## Storyteller Visual Integration

Existing component:

```text
/Users/adeelarshad/kagent/frontend/src/components/features/agentic-qna-view/components/StorytellerVisualExplanation.tsx
```

Enhancement:

```text
When a visual widget is selected:
  highlight matching Mark graph path
  highlight supporting services
  highlight connectors and gbrain namespaces
  show claim IDs and provenance in the detail panel

When the investigation workspace opens:
  freeze the current route trace
  keep Mark orb in investigating state
  allow switching between evidence, topology, timeline, actions, and claims
```

## Learning Loop Visibility

MarkUI should show learning explicitly after incident work.

Visual flow:

```text
Incident explained
  -> learning note created
  -> asset gap identified
  -> proposed playbook/runbook/query/dashboard update
  -> waiting for review
  -> approved into assets/*
```

Important rule:

```text
Learning must not silently mutate trusted assets.
```

UI representation:

```text
Learning node pulses amber.
Asset proposal appears as review-required.
Approval-required actions use the waiting_for_approval visual state.
```

## Implementation Phases

### Phase 1: Data Model And Truthful Orbit

Deliverables:

```text
mark-capability-graph.ts
MarkCognitiveWorld.tsx skeleton
MarkReasoningWeb.tsx first pass
CentralHud.tsx switched to new world component
engine orbit with six peer engines
Telecom Brain expandable service sub-orbit
```

Acceptance:

```text
Telecom Brain is not shown as a peer of its own services.
The UI can select engine nodes and telecom service nodes.
All node labels and detail content come from one shared config.
The accessible button list matches the visible graph.
```

### Phase 2: APEX Visual Port

Deliverables:

```text
MarkShaderBackground.tsx
MarkCore3D.tsx
MarkOrb.tsx
MarkHeroOrb.tsx
MarkStatusBar.tsx
mark-orb.css
MarkOverviewPanel.tsx
```

Acceptance:

```text
The Mark center stage inherits APEX's layered visual system.
Reduced motion disables shader/particle-heavy motion.
The UI does not include Apex branding, weather, social links, or generic agent roster.
21st.dev attribution is preserved for the two MIT community components.
```

### Phase 3: Real State Wiring

Deliverables:

```text
Map JarvisPage loading state to Mark visual state.
Map JarvisCommandBar live voice state to Mark visual state.
Map storyteller visual payload to route trace.
Map selected widget to active graph path.
```

Acceptance:

```text
Mark core changes visual state during listening, processing, speaking, and investigation.
The graph lights the correct engine/service route for storyteller responses.
The status bar names the active engine/service.
```

### Phase 4: Connector And Namespace Awareness

Deliverables:

```text
Fetch connector status from /api/jarvis/connectors/status.
Fetch recent traces from /api/jarvis/connectors/traces.
Render connector health in MarkOverviewPanel.
Render namespace links in node detail panel.
```

Acceptance:

```text
gbrain, Grafana, Nautobot, and other connectors have visible status.
Recent MCP trace entries can be inspected from the HUD.
Connector failures appear as degraded nodes, not silent UI state.
```

### Phase 5: Investigation And Learning UX

Deliverables:

```text
Claim-to-route highlighting.
Provenance side panel.
Learning note / asset proposal strip.
Approval-required action state.
```

Acceptance:

```text
An incident story can visually explain its evidence path.
The user can see what was inferred, what was confirmed, and what is missing.
Learning proposals remain review-gated.
```

### Phase 6: Polish And Verification

Deliverables:

```text
Responsive desktop and mobile layout checks.
Keyboard navigation for all graph nodes.
Reduced-motion verification.
Canvas nonblank checks for shader and 3D core.
Focused frontend tests for route mapping.
```

Acceptance:

```text
npm run build passes for frontend.
The central canvas renders nonblank on desktop and mobile.
No labels overlap in common viewports.
All graph functionality has keyboard-accessible equivalents.
```

## Suggested File Layout

```text
frontend/src/components/mark-orb/
  MarkCognitiveWorld.tsx
  MarkReasoningWeb.tsx
  MarkHeroOrb.tsx
  MarkOrb.tsx
  MarkCore3D.tsx
  MarkShaderBackground.tsx
  MarkOverviewPanel.tsx
  MarkStatusBar.tsx
  MarkCapabilityPanel.tsx
  mark-orb.css

frontend/src/lib/
  mark-capability-graph.ts
  mark-visual-state.ts
  mark-route-trace.ts
```

## Risks And Mitigations

### Risk: Semantic Flattening

Problem:

```text
Telecom Brain services could accidentally be presented as peer engines.
```

Mitigation:

```text
Use typed graph nodes with parentId.
Render only engine nodes in the default orbit.
Render telecom services only in Telecom Brain expanded mode.
```

### Risk: Duplicated Roster Data

Problem:

```text
APEX-UI duplicates roster information between ApexWorld and ReasoningWeb.
```

Mitigation:

```text
MarkUI must use one shared capability graph config.
All visible graph, accessible controls, panels, and route traces read from it.
```

### Risk: Decorative Graph Without Operational Meaning

Problem:

```text
The graph could look impressive but fail to explain real Mark routing.
```

Mitigation:

```text
Every active trace must map to an engine, service, connector, namespace, or claim.
No purely invented operational nodes.
```

### Risk: Performance

Problem:

```text
Shader + Three.js + dashboard panels may be expensive.
```

Mitigation:

```text
Respect prefers-reduced-motion.
Avoid multiple WebGL canvases.
Pause or throttle decorative rendering during heavy response streaming.
Keep fallback SVG/CSS rendering for low-power devices.
```

### Risk: Attribution Loss

Problem:

```text
21st.dev MIT component attribution could be lost during migration.
```

Mitigation:

```text
Keep source comments in adapted files.
Add a MarkUI credits section or docs note.
```

## Final Target Experience

The final MarkUI should feel like this:

```text
The user speaks or types to Mark.
The Mark core wakes.
The correct engine lights up.
If Telecom Brain is involved, its internal service sub-orbit expands.
The route trace pulses through service, connector, and gbrain namespace.
The response card renders written answer, spoken brief, and visual explanation.
The investigation panel explains claims, evidence, topology, timeline, actions,
and provenance.
If learning is produced, the UI shows it as a reviewable improvement path,
not as an invisible mutation of trusted assets.
```

