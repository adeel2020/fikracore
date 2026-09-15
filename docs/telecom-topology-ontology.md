# telecombrain Topology Ontology

`telecombrain` is one knowledge space with semantic layers, not multiple brains.

## Semantic Layers

- Topology
- Operational Evidence
- Incidents
- Correlation
- Customer Tickets
- Storytelling
- Learning
- Procedures
- KPIs
- Assets

## Topology Classes

- Physical topology: sites, racks, power domains, fiber paths, radio sectors, appliances, and concrete deployed assets.
- Logical topology: protocol adjacencies, routing areas, bearer paths, roaming boundaries, slices, APNs/DNNs, and signaling/data-plane separations.
- Service topology: customer-facing and network services mapped to procedures, functions, KPIs, and intents.
- Cloud/NFVI topology: clusters, namespaces, hosts, VNFs/CNFs, storage, message buses, service meshes, and failover groups.
- Application dependency: control-plane and OSS/BSS applications, databases, caches, queues, APIs, and authentication/timing dependencies.
- Failure domain: blast-radius groupings such as site, availability zone, vendor release, shared transport, power, capacity pool, and maintenance window.
- External dependency: DNS, NTP/PTP, AAA, charging, roaming partners, internet exchanges, cloud regions, and third-party service providers.
- Operational observation: alarms, KPIs, logs, traces, tickets, changes, probes, synthetic checks, and operator notes.

## Relationship Preparation

Future topology ingestion may use relationships such as `depends-on`, `connected-to`, `routes-through`, `carried-by`, `hosted-on`, `runs-on`, `fails-over-to`, `supports-service`, and `part-of-failure-domain`, but this migration does not add relationship types blindly.
