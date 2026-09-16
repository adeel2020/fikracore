# FikraCore: AI-Native Telecom Intelligence & Simulation Platform

FikraCore is an AI-native cognitive operations platform designed for Tier-1 telecommunications networks. It unifies causal root-cause analysis, operational knowledge discovery, continuous learning with human SME validation, and forward-looking what-if resilience prediction into a continuous Quality Flywheel.

---

## 1. Conceptual Model

FikraCore structures operational cognitive capabilities into four distinct, evolutionary stages:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   UNDERSTAND    │  ──>  │    DISCOVER     │  ──>  │      LEARN      │  ──>  │   ANTICIPATE    │
│   (Stage H1)    │       │   (Stage H2)    │       │   (Stage H3)    │       │   (Stage H4)    │
│                 │       │                 │       │                 │       │                 │
│ Incident Causal │       │ Knowledge Gap & │       │ SME Validation  │       │ Proactive Blast │
│  Investigation  │       │ Boundary Search │       │   & Promotion   │       │ Radius & What-If│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

| Stage | Capability Name | Purpose | Example Scenarios |
|---|---|---|---|
| **H1** | **Understand** | Rapidly diagnose outages, trace multi-hop causal chains, and rank hypotheses with confidence calibration. | `DEMO-001`, `SCN-001` |
| **H2** | **Discover** | Detect unmodeled dependencies, missing cross-domain telemetry, and operational graph boundaries. | `H2-GAP-001` |
| **H3** | **Learn** | Capture new operational rules, present them for human SME review, promote them into memory, or rollback. | `H3-LRN-001` |
| **H4** | **Anticipate** | Simulate what-if failure conditions across core and transport to estimate customer blast radius before failures hit production. | `H4-WI-001` to `H4-WI-040` |

---

## 2. Directory & Architecture Layout

```
kagent/
├── docs/
│   └── fikracore/
│       ├── README.md               # Overview and conceptual model (this document)
│       └── cli-reference.md        # Comprehensive CLI command reference & workflows
├── services/
│   └── agents/src/engine_stack/engines/telecom_brain/
│       ├── capabilities/           # Unified Capability Registry (investigate, discover, learn, predict, etc.)
│       ├── investigation/          # Causal engine, hypothesis ranker, CLI entrypoint (cli.py)
│       ├── simulator/              # Simulation orchestration, scenario catalog, run compiler
│       └── api/                    # FastAPI endpoints (capabilities, scenarios, YAML, topology)
└── frontend/
    └── src/
        ├── app/simulator/          # Next.js workspace views (investigate, discover, learn, predict, lab)
        └── lib/
            ├── fikracore-context.tsx # React global state, scenario registry & selection sync
            └── simulation-store.ts   # Simulation WebSocket / SSE client & REST bridge
```

---

## 3. Documentation Index

- [**CLI Reference Guide**](file:///Users/adeelarshad/kagent/docs/fikracore/cli-reference.md): Detailed usage, arguments, and practical examples for all `fikracore` subcommands (`investigate`, `discover`, `learn`, `predict`, `inspect`, `benchmark`, `simulate`, etc.).
- [**Simulator Lab Unified Scenario Library Plan**](file:///Users/adeelarshad/kagent/docs/fikracore-simulator-lab-unified-scenario-library-fix-plan.md): Specification for the unified scenario catalog and conceptual model naming.
- [**Cognitive Operations Architecture**](file:///Users/adeelarshad/kagent/docs/telecom-brain-cognitive-operations-architecture.md): Deep-dive into telecom graph ontology and reasoning models.
