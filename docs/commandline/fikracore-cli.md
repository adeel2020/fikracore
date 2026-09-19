usage: fikracore [-h] <command> ...

FikraCore — Telecom Reasoning, Learning & Resilience Platform

options:
  -h, --help            show this help message and exit

available commands:

[1mCore Operations & Investigation:[0m
  investigate           Explain what happened and why (root cause & causal
                        chain)
  discover              Identify missing or insufficient operational knowledge
                        gaps
  learn                 Validate, promote, inspect and manage learned
                        knowledge units
  simulate              Execute simulator scenario runs and advance state
  predict               Proactive forward what-if failure simulation and blast
                        radius
  inspect               Inspect scenario operational topology, manifest, or
                        live MCP knowledge
  present               Generate UI standard presentation model for scenario

[1mShowcase Demos:[0m
  diagnose-run          [Demo 1] Diagnose root cause, causal path & blast
                        radius for an H1 run
  h2-demo               [Demo 2a] Interactive 7-step H2 knowledge gap
                        discovery & evidence probe
  h3-demo               [Demo 2b] Interactive 7-step H3 knowledge curation,
                        promotion & reuse
  h4-demo               [Demo 3] Interactive H4 proactive resilience what-if
                        simulation

[1mKnowledge Governance & Promotion:[0m
  validate-candidate    Record SME decision for candidate relationship
  promote-knowledge     Execute governed knowledge promotion into graph
  rollback-promotion    Roll back a previous knowledge promotion

[1mBenchmarking & Validation:[0m
  validate              Validate scenarios, learning units and artifacts
  benchmark             Run H1–H4 and integration benchmarks
  report                Generate benchmark and analysis reports
  evaluate              Examiner truth evaluation (isolated from investigator)
  diagnose-benchmark    Diagnose failure taxonomy across benchmark runs

[1mStage Generators & Diagnostics (H2, H3, H4):[0m
  generate-h2-scenarios
                        Generate synthetic H2 scenario runs
  validate-h2-scenarios
                        Validate H2 scenarios against schema and contracts
  run-h2-benchmark      Execute H2 benchmark across all H2 scenario runs
  diagnose-h2-run       Inspect diagnostics for a specific H2 run
  h2-report             Print H2 aggregate benchmark report
  generate-h3-learning-units
                        Generate synthetic H3 learning units
  validate-h3-learning-units
                        Validate H3 learning units and manifests
  run-h3-benchmark      Execute H3 learning benchmark
  h3-report             Print H3 aggregate benchmark report
  generate-h4-scenarios
                        Generate synthetic H4 resilience scenarios
  validate-h4-scenarios
                        Validate H4 resilience scenario runs
  run-h4-benchmark      Execute H4 resilience benchmark
  h4-report             Print H4 aggregate benchmark report

[1mLive MCP Integration & Parity:[0m
  mcp-smoke             Run live gbrain MCP integration smoke test
  benchmark-parity      Run live MCP parity & benchmark validation
  inspect-parity        Inspect live MCP parity for a specific scenario

[1mQuick Showcase & Usage Tips:[0m
  1. Cross-Domain Root Cause (H1):
     fikracore diagnose-run RUN-SCN-001-L1-SEED-42001

  2. Gap Discovery & Curated Learning (H2 → H3):
     fikracore h2-demo RUN-H2-SCN-001-K1-SEED-52002
     fikracore h3-demo H3-LU-001

  3. Proactive Resilience What-If (H4):
     fikracore h4-demo H4-WI-001

  4. Interactive Scenario Inspection:
     fikracore inspect H4-WI-001 --coverage
     fikracore predict H4-WI-001

Run 'fikracore <command> -h' for detailed options on any command.
