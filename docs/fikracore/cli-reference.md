# FikraCore CLI Reference Guide

`fikracore` is the unified command-line tool for the FikraCore AI-native telecom intelligence platform. It exposes the entire Telecom Brain engine stack—causal reasoning, knowledge discovery, continuous learning, what-if prediction, and simulation benchmarking—through a unified command interface.

---

## 1. Architecture & Execution Model

The CLI routes all commands through the central **Unified Capability Registry** (`default_capability_registry`), ensuring parity across the CLI, REST APIs, and the Simulator UI:

```mermaid
flowchart TD
    CLI["`fikracore <subcommand>`"] --> Main["`main()` in `cli.py`"]
    Main --> Registry["Unified Capability Registry"]
    
    subgraph Capabilities["Conceptual Model Capabilities"]
        Registry --> CapH1["`investigate` (Understand / H1)"]
        Registry --> CapH2["`discover` (Discover / H2)"]
        Registry --> CapH3["`learn` (Learn / H3)"]
        Registry --> CapH4["`predict` (Anticipate / H4)"]
    end
    
    subgraph Operations["Orchestration & Verification"]
        Registry --> CapSim["`simulate`"]
        Registry --> CapInsp["`inspect`"]
        Registry --> CapBm["`benchmark` / `benchmark-parity`"]
        Registry --> CapRep["`report`"]
        Registry --> CapVal["`validate`"]
    end

    CapH1 --> Investigator["Investigator Engine (Causal Reasoning)"]
    CapH2 --> GapEngine["Boundary & Gap Analysis Engine"]
    CapH3 --> LearnEngine["SME Validation & Promotion Registry"]
    CapH4 --> WhatIfEngine["Forward Propagation & Blast Radius"]
    CapBm --> BenchmarkEngine["Automated Quality & Evaluation Suite"]
```

### Installation & Entrypoint
The CLI is configured in [`services/pyproject.toml`](file:///Users/adeelarshad/kagent/services/pyproject.toml):
```toml
[project.scripts]
fikracore = "engine_stack.engines.telecom_brain.investigation.cli:main"
```

To run in the services virtual environment:
```bash
# Using poetry
poetry run fikracore <command>

# Or directly via venv python
services/.venv/bin/fikracore <command>
```

---

## 2. Core Commands by Conceptual Stage

### Stage 1: Understand (`H1`) — `fikracore investigate`
Explains what happened and why during an incident by analyzing telemetry, topological dependencies, and symptoms.

#### Usage
```bash
fikracore investigate [run_directory] [--scenario SCENARIO_ID] [--snapshot PATH] [--output PATH]
```

#### Flags
| Flag | Type | Description |
|---|---|---|
| `run_directory` | Positional (Optional) | Path to historical simulation run directory |
| `--scenario` | String | Scenario ID (e.g. `SCN-001`, `DEMO-001`) |
| `--snapshot` | Path | Path to frozen telemetry snapshot |
| `--output` | Path | Output file to store JSON results (defaults to stdout) |

#### Examples
```bash
# Investigate scenario SCN-001
fikracore investigate --scenario SCN-001

# Investigate declarative transport demo
fikracore investigate --scenario DEMO-001

# Investigate a historical run folder and save results
fikracore investigate services/agents/src/engine_stack/engines/telecom_brain/simulator/runs/RUN-SCN-001-L1-SEED-42001 --output artifacts/investigation.json
```

---

### Stage 2: Discover (`H2`) — `fikracore discover`
Identifies unmodeled cross-domain boundaries, missing telemetry, and operational knowledge gaps.

#### Usage
```bash
fikracore discover [scenario] [--output PATH]
```

#### Flags
| Flag | Type | Description |
|---|---|---|
| `scenario` | Positional (Optional) | Target scenario ID (e.g. `H2-GAP-001`) |
| `--output` | Path | Path to save output report |

#### Companion Generation & Validation Commands
- **`generate-h2-scenarios`**: Synthesizes synthetic H2 boundary gap runs.
  ```bash
  fikracore generate-h2-scenarios --output-dir services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs
  ```
- **`validate-h2-scenarios`**: Checks manifest integrity and boundary definitions for H2 runs.
  ```bash
  fikracore validate-h2-scenarios --runs-dir services/agents/src/engine_stack/engines/telecom_brain/simulator/h2_runs
  ```
- **`run-h2-benchmark`**: Benchmarks H2 discovery precision/recall.
  ```bash
  fikracore run-h2-benchmark --output-dir artifacts/hypothesis/h2
  ```

---

### Stage 3: Learn (`H3`) — `fikracore learn`
Manages the lifecycle of newly discovered operational knowledge: inspection, human SME validation, safe promotion, and rollback.

#### Usage
```bash
fikracore learn [action] [target] [options]
```

#### Actions
- `inspect`: Inspect a candidate knowledge unit or promoted rule.
- `validate`: Record an SME validation decision.
- `promote`: Promote candidate knowledge into the active operational graph.
- `rollback`: Revert a previous promotion using its promotion ID.
- `generate`: Generate learning units from past incidents.

#### Flags
| Flag | Type | Description |
|---|---|---|
| `--candidate-file` | Path | Path to candidate knowledge JSON/YAML |
| `--validation-file` | Path | Path to signed SME validation decision |
| `--promotion-id` | String | Target promotion ID for rollback |
| `--units-dir` | Path | Base directory of learning units |
| `--dry-run` | Flag | Simulate promotion/rollback without mutating graph |
| `--output` | Path | Save execution output to file |

#### Examples
```bash
# Inspect learning unit H3-LRN-001
fikracore learn inspect H3-LRN-001

# Promote validated candidate knowledge into operational topology
fikracore learn promote --candidate-file candidate_ocs.json --validation-file validation_approval.json

# Roll back a promotion
fikracore learn rollback --promotion-id PROM-20260913-001
```

---

### Stage 4: Anticipate (`H4`) — `fikracore predict`
Simulates forward what-if failure conditions to compute blast radius, affected services, and propagation paths before failures hit production.

#### Usage
```bash
fikracore predict <scenario> [--runs-dir PATH]
```

#### Flags
| Flag | Type | Description |
|---|---|---|
| `scenario` | Positional | Scenario ID (`H4-WI-001`...`040`) or human-readable alias |
| `--runs-dir` | Path | Directory containing H4 what-if run profiles |

#### Example
```bash
# Predict downstream impact of MPLS edge router failure
fikracore predict H4-WI-001

# Predict user plane gateway collapse
fikracore predict H4-WI-003
```

---

## 3. Inspection & Knowledge Health Commands

### `fikracore inspect`
Deep inspection of operational topology, coverage, gaps, or live MCP integration.

```bash
# Inspect a specific scenario's topology
fikracore inspect SCN-001

# Inspect live MCP knowledge inventory
fikracore inspect live-knowledge

# Filter live knowledge by domain and show gaps/orphans
fikracore inspect live-knowledge --domain "Transport" --gaps --orphans

# View raw JSON coverage report
fikracore inspect DEMO-001 --coverage --json
```

### `fikracore mcp-smoke`
Runs the live gbrain Model Context Protocol (MCP) integration smoke test.

```bash
fikracore mcp-smoke --url http://localhost:3131/mcp --token <BEARER_TOKEN>
```

---

## 4. Benchmarking & Quality Flywheel

### `fikracore benchmark`
Executes automated calibration, validation, and regression suites.

```bash
# Benchmark H1 causal diagnosis accuracy
fikracore benchmark --stage h1

# Benchmark all conceptual stages (H1–H4)
fikracore benchmark --stage all

# Benchmark with a maximum of 20 runs
fikracore benchmark --stage all --max-runs 20

# Run with pre-validation
fikracore benchmark --stage h1 --validate-first
```

### `fikracore benchmark-parity`
Verifies reasoning parity between local synthetic simulation models and live MCP backend engines.

```bash
fikracore benchmark-parity --stage all --selected --output-dir artifacts/integration/mcp-parity
```

### `fikracore report`
Generates formatted benchmark reports in JSON or Markdown.

```bash
# Generate markdown report for H4 what-if resilience
fikracore report --stage h4 --format markdown

# Generate JSON report for H3 continuous learning
fikracore report --stage h3 --format json
```

---

## 5. Summary Reference Cheat Sheet

| Command | Capability | Primary Function |
|---|---|---|
| `fikracore investigate` | **Understand** (`H1`) | Root-cause analysis, causal path, confidence scores |
| `fikracore discover` | **Discover** (`H2`) | Knowledge gap, orphan, and boundary detection |
| `fikracore learn` | **Learn** (`H3`) | SME validation, promotion, and rollback |
| `fikracore predict` | **Anticipate** (`H4`) | Forward propagation & blast-radius what-if analysis |
| `fikracore simulate` | Simulation Runtime | Execute scenario lifecycle |
| `fikracore inspect` | Topology & Graph | View topology inventory, domain coverage, and gaps |
| `fikracore benchmark` | Quality Assurance | Execute regression and accuracy benchmarks |
| `fikracore benchmark-parity` | Parity Testing | Compare live MCP reasoning against synthetic runs |
| `fikracore mcp-smoke` | Connectivity | Smoke test live gbrain MCP endpoint |
| `fikracore report` | Documentation | Output benchmark evaluation reports (MD/JSON) |
