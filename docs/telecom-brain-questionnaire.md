# Telecom Brain Questionnaire

This questionnaire captures the useful questions Jarvis should be able to
answer about the telecom-brain work completed today.

## 1. Solution Overview

- What is the telecom brain we are building?
- What problem does this solution solve for mobile-core operations?
- What changed today in the solution?
- What is the end-to-end workflow from alarm ingestion to incident story?
- Which parts are deterministic and which parts may use LLMs later?
- What does "fixture-driven, intent-aware correlation" mean?
- Why is the design incident-agnostic?
- Does this support both intra-domain and inter-domain incidents?
- What is the difference between an alarm, a correlation cluster, and an incident?
- Why are not all alarms converted into incidents?
- How do we avoid missing important alarms?

## 2. Jarvis Integration

- How does Jarvis answer telecom-brain questions now?
- Which Jarvis route handles telecom-brain solution questions?
- What keywords route a question to the telecom-brain Jarvis engine?
- How does Jarvis answer questions from local design documents?
- How does Jarvis answer incident-specific questions?
- How does Jarvis call the deterministic storyteller?
- How does Jarvis list current incidents?
- When does Jarvis use gbrain search?
- What happens if gbrain is unavailable?
- What happens if a question is not covered by docs, incidents, or gbrain?
- How do I test Jarvis with the backend API?
- What is the curl command for `/api/jarvis/process`?

## 3. gbrain MCP

- Where is `GBRAIN_MCP_URL` configured?
- Where is `GBRAIN_MCP_TOKEN` configured?
- What is the correct local MCP URL?
- Why does `GET /mcp` return `405 Method Not Allowed`?
- What headers are required for direct MCP JSON-RPC calls?
- Why does MCP require `Accept: application/json, text/event-stream`?
- How do I fetch a gbrain page directly through MCP?
- How do I fetch links for a gbrain page directly through MCP?
- How does the backend talk to gbrain?
- Does the storyteller use gbrain over MCP or CLI?
- Does the correlation writer use gbrain over MCP or CLI?
- How do I verify that a page exists in gbrain?
- How do I verify that an incident has links in gbrain?

## 4. Namespaces

- What is the canonical incident namespace?
- Why do new incidents use `incidents/mobile-core/<id>`?
- Are old `mobile-core/incidents/<id>` slugs still supported?
- What is stored under `correlation/mobile-core/*`?
- What is stored under `storytelling/mobile-core/*`?
- What is stored under `learning/mobile-core/*`?
- What is stored under `assets/mobile-core/*`?
- What is stored under `knowledge/mobile-core/*`?
- What is stored under `domains/mobile-core/*`?
- What is stored under `grafana/*`?
- Why is Grafana evidence kept in a separate namespace?
- Why are correlation and storytelling separate namespaces?
- Why is knowledge separate from assets?
- Why should FCAPS not be a top-level namespace?
- Why should `signaling` not be modeled as a domain?

## 5. Mobile-Core Domain Model

- What is the mobile-core domain?
- What are the mobile-core network areas in this model?
- Where do CS, PS, IMS, LTE, 5GCN, VAS, and IoT fit?
- Where does signaling fit if it is not a domain?
- Where does LTE attach fit?
- Why is LTE attach a service procedure?
- Where does UE registration fit?
- Where does SGi throughput fit?
- Where do MME, HSS, SGW, PGW, AMF, SMF, UPF, P-CSCF, and S-CSCF fit?
- How are RAN and transport represented in inter-domain correlation?
- How do service procedures map to logical topology paths?
- How will physical topology be added later?

## 6. Correlation

- What is the correlation worker?
- What input does the correlation worker consume?
- What is an `AlarmEvent`?
- What is an `EvidenceEvent`?
- How are alarms normalized?
- Which fields are required for alarm normalization?
- How does the worker decide intra-domain versus inter-domain?
- How is the correlation score calculated?
- What reasons explain why alarms were grouped?
- How is intent violation used in scoring?
- What is a critical source alarm?
- What is a novel alarm signature?
- How does the worker avoid correlating unrelated alarms?
- How are unknown or novel alarms retained for review?
- How does correlation create or update an incident?
- How are correlation clusters stored in gbrain?
- How are correlation decisions stored in gbrain?
- How are correlation hypotheses stored in gbrain?
- How can I dry-run correlation without writing to gbrain?
- How can I write correlation output to gbrain?

## 7. Grafana LGTM Evidence

- How does Grafana LGTM fit into the solution?
- What evidence comes from Grafana alerts?
- What evidence comes from Prometheus metrics?
- What evidence comes from Loki logs?
- What evidence comes from Tempo traces?
- What should be stored under `grafana/alerts/*`?
- What should be stored under `grafana/metrics/*`?
- What should be stored under `grafana/logs/*`?
- What should be stored under `grafana/traces/*`?
- How is Grafana evidence linked to correlation hypotheses?
- How is Grafana evidence linked to incidents?
- How does the synthetic Grafana adapter work?
- How will the real Grafana MCP adapter work?
- What are the POC intents for Grafana evidence?
- How do CSSR, SGi throughput, and 4G attach SR map to service procedures?
- How do I test only the `4g_attach_sr` intent?

## 8. Storytelling

- What is the deterministic storyteller?
- Which API returns a rendered incident story?
- Which API returns the structured story object?
- What is the baseline story structure?
- Why did robotic summaries happen?
- How do we ensure rich stories are generated consistently?
- What sections should every incident story contain?
- Where does the story get impact data?
- Where does the story get timeline data?
- Where does the story get supporting evidence?
- Where does the story get correlation reasons?
- Why does the story say root cause is not confirmed?
- What conditions are required before root cause can be confirmed?
- How do follow-up questions use session state?
- How do we capture a reference story bundle?
- What files are saved in a story reference bundle?
- How can `story.json` explain how the story was built?

## 9. Incident APIs

- How do I list all incidents?
- How do I fetch one incident from the registry?
- How do I fetch lifecycle audit for an incident?
- How do I ask a question about one incident?
- How do I request only evidence for an incident?
- How do I request only timeline for an incident?
- How do I request executive summary for an incident?
- How do I test canonical incident slugs?
- How do I test legacy incident aliases?
- Why does a canonical URL contain `/api/incidents/incidents/mobile-core/...`?
- What does incident status mean?
- What does incident score mean?
- What does incident scope mean?
- What does `intent_status` mean?

## 10. FCAPS As A Lens

- Where exactly is FCAPS used in this solution?
- Why is FCAPS a learning lens and not a folder hierarchy?
- How are alarms mapped to Fault?
- How are KPI breaches mapped to Performance?
- How are change records mapped to Change / Configuration?
- How are subscriber-volume or session-volume gaps mapped to Accounting?
- How are anomaly or threat signals mapped to Security?
- How does FCAPS enrich incidents?
- How does FCAPS enrich evidence?
- How does FCAPS enrich assets?
- How does FCAPS enrich learning notes?
- How does FCAPS help identify missing evidence?
- What does an FCAPS review contain?
- How does FCAPS help improve playbooks and runbooks?
- How does FCAPS help browse prebuilt knowledge?

## 11. Learning Loop

- What is the pivot of learning?
- Is learning built only around intent?
- Can new intents be discovered through learning?
- What is a learning note?
- When is a learning note created?
- What does `asset_gap` mean?
- What proposed assets can come from a learning note?
- How does learning improve context over time?
- How does learning avoid silently changing trusted assets?
- What is the review flow before learning becomes trusted knowledge?
- What happens when there are no existing assets for a new incident?
- How are repeated incidents converted into reusable patterns?
- How do operator decisions feed back into learning?

## 12. Assets, Knowledge, Playbooks, And Runbooks

- What is an asset in this solution?
- Are assets a source of context or a destination of learning?
- What is the difference between knowledge and assets?
- What is a playbook?
- What is a runbook?
- How is a playbook different from a runbook?
- Can one playbook link to many runbooks?
- When should we create a new playbook?
- When should we create a new runbook?
- What is a Grafana query asset?
- What is a dashboard panel asset?
- What is a correlation rule asset?
- What is a change request template?
- How do assets get proposed from learning notes?
- How do assets become approved trusted context?

## 13. Change / Configuration

- Why is FCAPS-C Change / Configuration and not just configuration?
- Where do change requests fit?
- Where do change templates fit?
- How can a change request be linked to an incident?
- How can a missing change feed affect correlation confidence?
- How can planned maintenance suppress or explain alarms?
- How can post-change KPI recovery validate a change?
- What change fields should be ingested later?
- How should emergency changes be represented?

## 14. Topology And Digital Twin

- Where should actual topology live?
- Why should Nautobot or a topology DB be the topology authority?
- What does gbrain store if topology lives outside it?
- What is a topology projection?
- What is the difference between topology, twin, and semantic layer?
- Where does the digital twin fit?
- Why use a digital twin if topology already exists?
- How does the twin support correlation?
- How does the twin support storytelling?
- How does the twin support learning?
- How do logical topology fixtures work before physical topology is available?
- What open-source tools can support topology discovery?
- What should be discovered from SNMP, LLDP, CDP, NETCONF, or inventory APIs?
- How should discovered topology be validated before use?

## 15. Scalability

- Is this design scalable to millions of alarms per day?
- Which parts are hot path and which parts are semantic path?
- Should raw alarms all be written to gbrain?
- Where should high-volume raw alarms live?
- What should be summarized into gbrain?
- How should correlation workers be partitioned?
- Why is an outbox needed between correlation and gbrain writes?
- How should duplicate alarms be handled?
- How should incident merge and split work?
- How should the system handle late-arriving evidence?
- How should correlation state be checkpointed?
- How should rate limits be handled for gbrain and Grafana MCP?

## 16. Local Operations

- How do I start gbrain MCP locally?
- How do I start the backend locally?
- How do I check backend health?
- How do I check that MCP is listening?
- How do I dry-run all synthetic correlation fixtures?
- How do I write synthetic correlation output to gbrain?
- How do I generate a story from the backend?
- How do I capture a story reference bundle?
- How do I run focused backend tests?
- How do I run frontend TypeScript validation?
- How do I refresh graphify after code changes?

## 17. Troubleshooting

- Why am I getting `405 Method Not Allowed` from MCP?
- Why am I getting `Missing Authorization header`?
- Why am I getting `Invalid Authorization header format`?
- Why am I getting `Not Acceptable: Client must accept both application/json and text/event-stream`?
- Why does `curl` fail from sandbox but work with local escalation?
- Why does the backend say incident not found?
- Why does `get_page failed` happen for a slug?
- Why does an incident story lack root cause?
- Why is the story short or robotic?
- Why does the incident list show legacy incidents?
- Why is port `8000` already in use?
- Why is the `uvicorn` console script using a bad interpreter?

## 18. Review And Governance

- What should be reviewed before accepting a new learning note?
- Who approves proposed playbooks and runbooks?
- Who approves change templates?
- How do we track evidence provenance?
- How do we keep story output explainable?
- How do we prevent accidental schema drift?
- How do we validate new domains or network areas?
- How do we validate new service procedures?
- How do we know when a candidate incident should be promoted?
- How do we know when a correlation should be suppressed?
- How do we measure whether the telecom brain is learning correctly?
