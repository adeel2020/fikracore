export interface GbrainNode {
  id: string;
  slug: string;
  label: string;
  kind: "incident" | "network-function" | "procedure" | "hypothesis" | "evidence" | "remediation" | "kpi" | "service" | "rule";
  category: string;
  confidence?: number;
  description: string;
  compiled_truth?: string;
  frontmatter?: Record<string, any>;
}

export interface GbrainLink {
  source: string;
  target: string;
  relationship: string;
}

export interface GbrainWidget {
  id: string;
  title: string;
  type: string;
  confidence?: number;
  data: any;
}

export const GBRAIN_NODES: GbrainNode[] = [
  // Incidents
  {
    id: "incident-amf-overload",
    slug: "mobile-core/incidents/amf-overload-2026-08-09",
    label: "AMF-01 Overload & High Rejection",
    kind: "incident",
    category: "Incidents",
    confidence: 0.94,
    description: "Critical registration failure burst in Dubai Core DC-1 triggered by CPU saturation on AMF-01.",
    compiled_truth: `# AMF-01 Overload and High Registration Rejection

## Summary
Critical registration failure burst in Dubai Core DC-1 triggered by CPU saturation on AMF-01.

## Timeline
- **06:14:00Z** — RSR (Registration Success Rate) dropped below threshold to 94.7%.
- **06:22:15Z** — Correlated alarm candidate formed with 98% CPU saturation.
- **06:45:00Z** — Automated remediation added AMF-01 capacity.
- **07:05:00Z** — RSR recovered to 99.9%.`,
    frontmatter: {
      severity: "SEV-2",
      status: "resolved",
      started_at: "2026-08-09T06:14:00Z",
      resolved_at: "2026-08-09T07:05:00Z",
      correlation_key: "amf-core-overload-01",
      correlation_score: 0.94,
    },
  },
  {
    id: "incident-lte-attach",
    slug: "incidents/mobile-core/lte-attach-54db6ef325fbf758",
    label: "LTE Attach & S1-MME Degradation",
    kind: "incident",
    category: "Incidents",
    confidence: 0.91,
    description: "Intermittent LTE attach failures affecting 14,200 subscribers across Dubai North eNodeBs.",
    compiled_truth: `# LTE Attach Failure & S1-MME Path Degradation

## Summary
Intermittent LTE attach failures affecting 14,200 subscribers across Dubai North eNodeBs.

## Timeline
- **11:00:00Z** — 4G_Attach_SR KPI fell to 88.2%.
- **11:04:37Z** — High latency detected on S1-MME transport link.`,
    frontmatter: {
      severity: "SEV-1",
      status: "investigating",
      started_at: "2026-08-31T11:00:00Z",
      correlation_key: "lte-attach-54db6ef325fbf758",
      correlation_score: 0.91,
    },
  },

  // Network Functions (Twin / Topology Projection)
  {
    id: "nf-amf",
    slug: "network-functions/amf",
    label: "AMF-01 (Access & Mobility)",
    kind: "network-function",
    category: "Network Functions",
    confidence: 0.96,
    description: "Core 5GC control plane function handling registration, reachability, and mobility management.",
    compiled_truth: "AMF handles UE registration, connection management, NAS signaling, and mobility management in 5G Core.",
    frontmatter: { vendor: "Huawei", model: "iMaster USN9810", role: "5GC Control Plane", pool: "Dubai-DC1-Core" },
  },
  {
    id: "nf-upf",
    slug: "network-functions/upf",
    label: "UPF Core Pod 3",
    kind: "network-function",
    category: "Network Functions",
    confidence: 0.95,
    description: "Core 5GC user plane function performing packet routing, QoS enforcement, and uplink/downlink forwarding.",
    compiled_truth: "UPF handles packet routing and forwarding, data buffering, and QoS enforcement between gNodeB and Data Networks (DN).",
    frontmatter: { interface: "N3 / N4 / N6", throughput_capacity: "100 Gbps" },
  },
  {
    id: "nf-smf",
    slug: "network-functions/smf",
    label: "SMF-01 (Session Management)",
    kind: "network-function",
    category: "Network Functions",
    confidence: 0.92,
    description: "Core 5GC control plane function managing PDU session lifecycle, IP address allocation, and UPF selection.",
    compiled_truth: "SMF establishes, modifies, and releases PDU sessions, and controls UPF forwarding policies.",
    frontmatter: { protocol: "HTTP/2 SBI", interface: "N7 / N10 / N11" },
  },
  {
    id: "nf-gnb",
    slug: "network-functions/gnb",
    label: "gNodeB / RAN Site 42",
    kind: "network-function",
    category: "Network Functions",
    confidence: 0.88,
    description: "5G NR Radio Access Network base station providing radio connectivity to user equipment.",
    compiled_truth: "gNodeB connects mobile devices over NR-Uu interface and connects to AMF via N2 and UPF via N3.",
    frontmatter: { band: "n78 (3.5GHz)", technology: "5G SA / NSA" },
  },

  // Hypotheses
  {
    id: "hyp-amf-cpu",
    slug: "hyp/amf-cpu-sat",
    label: "AMF-01 CPU Saturation",
    kind: "hypothesis",
    category: "Hypotheses",
    confidence: 0.94,
    description: "AMF-01 worker processes reached 98% CPU utilization causing NAS buffer drops.",
    compiled_truth: "AMF-01 worker processes reached 98% CPU utilization causing NAS buffer drops.",
    frontmatter: { status: "confirmed", confidence: 0.94, root_cause_probability: "HIGH" },
  },
  {
    id: "hyp-s1-latency",
    slug: "hyp/s1-latency-congestion",
    label: "S1-MME Transport Latency",
    kind: "hypothesis",
    category: "Hypotheses",
    confidence: 0.89,
    description: "Backhaul fiber jitter causing SCTP heartbeat timeouts between eNodeB clusters and MME pool.",
    compiled_truth: "Backhaul link bufferbloat resulting in round-trip latency exceeding 180ms.",
    frontmatter: { status: "investigating", confidence: 0.89 },
  },

  // Evidence
  {
    id: "ev-cpu-98",
    slug: "ev/cpu-98",
    label: "Prometheus AMF CPU @ 98%",
    kind: "evidence",
    category: "Evidence",
    confidence: 0.99,
    description: "Prometheus metric node_cpu_seconds_total indicated sustained saturation on worker pods.",
    compiled_truth: "Prometheus metric node_cpu_seconds_total indicated sustained saturation.",
    frontmatter: { source: "prometheus/dc1-amf", observed_at: "2026-08-09T06:18:00Z", metric: "node_cpu_seconds_total" },
  },
  {
    id: "ev-nas-reject",
    slug: "ev/nas-reject",
    label: "NAS REG REJECT Cause #22",
    kind: "evidence",
    category: "Evidence",
    confidence: 0.97,
    description: "Packet traces captured repeated 5GMM Cause #22 (Congestion) returned to UEs.",
    compiled_truth: "Packet traces captured repeated 5GMM Cause #22 returned to UEs.",
    frontmatter: { source: "pcaps/sgi-core", observed_at: "2026-08-09T06:20:00Z", pcap_filter: "ngap.cause == 22" },
  },
  {
    id: "ev-rsr-breach",
    slug: "kpi-event/rsr-breach",
    label: "RSR Breach 94.7% (Threshold 98.5%)",
    kind: "evidence",
    category: "Evidence",
    confidence: 0.96,
    description: "Observed severe degradation in registration success rate across DC-1.",
    compiled_truth: "Observed severe degradation in registration success rate across DC-1.",
    frontmatter: { value: 94.7, unit: "percent", event_type: "alarm", threshold: "critical" },
  },

  // Remediation
  {
    id: "rem-scale-amf",
    slug: "rem/capacity",
    label: "Scale AMF Worker Pods (MOP)",
    kind: "remediation",
    category: "Remediation",
    confidence: 0.95,
    description: "Executed automated scaling playbook increasing AMF worker pods from 4 to 8.",
    compiled_truth: "Executed automated scaling playbook increasing AMF worker pods from 4 to 8.",
    frontmatter: { runbook: "MOP-AMF-AUTO-SCALE-04", target: "network-functions/amf", duration_seconds: 180 },
  },

  // KPI & Service Recovery
  {
    id: "rec-rsr",
    slug: "rec/rsr-recovered",
    label: "RSR Recovered to 99.9%",
    kind: "kpi",
    category: "KPIs & Intents",
    confidence: 0.99,
    description: "Telemetry confirms stable RSR above SLA threshold after scaling.",
    compiled_truth: "Telemetry confirms stable RSR above SLA threshold.",
    frontmatter: { value: 99.9, unit: "percent", observed_at: "2026-08-09T07:05:00Z" },
  },
  {
    id: "svc-ue-reg",
    slug: "services/ue-registration",
    label: "5G Initial UE Registration",
    kind: "service",
    category: "Services",
    confidence: 0.95,
    description: "End-to-end subscriber access service connecting UE to 5G Core.",
    compiled_truth: "End-to-end subscriber access service connecting UE to 5G Core.",
    frontmatter: { "3gpp_spec": "TS 23.502", procedure: "Registration Management" },
  },

  // Procedures & Mobile RTR Semantic Models
  {
    id: "proc-rtr-pipeline",
    slug: "telecom-brain/domains/mobile-core/roles/mobile-rtr/pipeline",
    label: "Mobile RTR Investigation Pipeline",
    kind: "procedure",
    category: "RTR Procedures",
    confidence: 0.95,
    description: "Multi-stage investigation pipeline with 7 checkpoint gates for Core RTR ticket triage.",
    compiled_truth: `# Mobile RTR Multi-Stage Investigation Pipeline
Stage 0: Ingestion & Frontline Precheck Validation Gate
Stage 1: Customer Location Discovery & Core Profile Audit
Stage 2: Multi-Domain Checklist for IT Profile & Subscriptions
Stage 3: Roaming Domain Specific Checklist
Stage 4: Active Troubleshooting & Device Recovery
Stage 5: Deeper Multi-Protocol Signaling Trace Diagnostics
Stage 6: Two-Tier Escalation Hierarchy & Disposition Lifecycle`,
    frontmatter: { engine: "telecom_brain", stages: 7, governance: "Read-only Core RTR" },
  },
  {
    id: "proc-findings-matrix",
    slug: "telecom-brain/domains/mobile-core/roles/mobile-rtr/concern-findings-matrix",
    label: "Concern vs Findings Matrix",
    kind: "procedure",
    category: "RTR Procedures",
    confidence: 0.94,
    description: "Reporting methodology mapping customer complaints to technical findings and MML actions.",
    compiled_truth: "Maps Provisioning (~70%), MNP Routing (~5%), VoLTE Drops, and Commercial FUP throttling.",
    frontmatter: { primary_volume: "Provisioning/Activation (~70%)" },
  },
  {
    id: "proc-huawei-mml",
    slug: "telecom-brain/domains/mobile-core/roles/mobile-rtr/huawei-mml-runbooks",
    label: "Huawei MML Runbooks",
    kind: "procedure",
    category: "RTR Procedures",
    confidence: 0.93,
    description: "Read-only audit vs IT provisioning remediation commands on iMaster NCE / LMT.",
    compiled_truth: "DSP SUBAPN, DSP UDM5GSUB, DSP PCFPOLICY, SET GPRSLOCK: UNLOCK.",
    frontmatter: { vendor: "Huawei", tool: "iMaster NCE / LMT" },
  },

  // CKG Core Abstractions
  {
    id: "ckg-voice-drops",
    slug: "ckg/intent_voice_drops",
    label: "Voice Call Drops (CKG Hub)",
    kind: "rule",
    category: "CKG Rules",
    confidence: 0.92,
    description: "CKG God Node: Voice Call Drops cluster connecting VoLTE Device Support, IMS Core, and RF SINR.",
    compiled_truth: "Central betweenness node bridging Core Switching IMS team and RAN RF coverage.",
    frontmatter: { edges_count: 5, centrality: 0.235, community: "Voice Call Drops Cluster" },
  },
  {
    id: "ckg-5g-speed",
    slug: "ckg/intent_slow_5g",
    label: "5G Speed Degradation (CKG Hub)",
    kind: "rule",
    category: "CKG Rules",
    confidence: 0.93,
    description: "CKG God Node: 5G Speed Degradation bridging UPF Packet Router, RAN RF noise, and 5G SIM.",
    compiled_truth: "Causal cluster linking cellular throughput degradation to UPF routing and Low SINR.",
    frontmatter: { edges_count: 5, centrality: 0.24, community: "5G Speed Degradation Cluster" },
  },
  {
    id: "ckg-esim-support",
    slug: "ckg/esim_support",
    label: "eSIM & Provisioning Support",
    kind: "rule",
    category: "CKG Rules",
    confidence: 0.95,
    description: "CKG Top God Node: 9 edges connecting SM-DP+ Server, Subscriber Mobile App, and Unified CRM.",
    compiled_truth: "Highest betweenness centrality (0.316) in CKG — primary cross-community bridge.",
    frontmatter: { edges_count: 9, centrality: 0.316, community: "eSIM & Provisioning Support Cluster" },
  },
];

export const GBRAIN_LINKS: GbrainLink[] = [
  // Causal Chain from Incident
  { source: "incident-amf-overload", target: "ev-rsr-breach", relationship: "detected-by" },
  { source: "ev-rsr-breach", target: "rec-rsr", relationship: "measures" },
  { source: "incident-amf-overload", target: "nf-amf", relationship: "involves" },
  { source: "incident-amf-overload", target: "nf-smf", relationship: "involves" },
  { source: "incident-amf-overload", target: "svc-ue-reg", relationship: "affects" },
  { source: "incident-amf-overload", target: "hyp-amf-cpu", relationship: "has-hypothesis" },
  { source: "hyp-amf-cpu", target: "ev-cpu-98", relationship: "supported-by" },
  { source: "hyp-amf-cpu", target: "ev-nas-reject", relationship: "supported-by" },
  { source: "incident-amf-overload", target: "rem-scale-amf", relationship: "has-remediation" },
  { source: "rem-scale-amf", target: "nf-amf", relationship: "targets" },
  { source: "rem-scale-amf", target: "rec-rsr", relationship: "verified-by" },

  // Network Topology
  { source: "nf-gnb", target: "nf-amf", relationship: "connected-to (N2)" },
  { source: "nf-gnb", target: "nf-upf", relationship: "connected-to (N3)" },
  { source: "nf-amf", target: "nf-smf", relationship: "connected-to (N11)" },
  { source: "nf-smf", target: "nf-upf", relationship: "connected-to (N4)" },

  // Procedures & Knowledge Links
  { source: "proc-rtr-pipeline", target: "proc-findings-matrix", relationship: "classifies-with" },
  { source: "proc-rtr-pipeline", target: "proc-huawei-mml", relationship: "executes-with" },
  { source: "proc-rtr-pipeline", target: "nf-amf", relationship: "audits" },
  { source: "proc-rtr-pipeline", target: "nf-smf", relationship: "audits" },
  { source: "proc-rtr-pipeline", target: "nf-upf", relationship: "audits" },

  // CKG Rules Integration
  { source: "ckg-5g-speed", target: "nf-upf", relationship: "routes-through" },
  { source: "ckg-esim-support", target: "proc-findings-matrix", relationship: "governs-profile" },
  { source: "ckg-voice-drops", target: "nf-amf", relationship: "signaling-impact" },
];

export const GBRAIN_VISUAL_EXPLANATION = {
  incident_id: "mobile-core/incidents/amf-overload-2026-08-09",
  audience: "noc_lead",
  summary: "AMF-01 CPU saturation led to high 5G registration rejection Cause #22. Automated scaling MOP doubled worker pods, fully restoring RSR to 99.9%.",
  widgets: [
    {
      id: "visual-domain-impact",
      title: "Domain and service impact",
      type: "domain_impact_map",
      confidence: 0.94,
      data: {
        nodes: GBRAIN_NODES.map((n) => ({ id: n.id, label: n.label, kind: n.kind })),
        links: GBRAIN_LINKS,
      },
    },
    {
      id: "visual-causal-chain",
      title: "Causal chain",
      type: "causal_chain",
      confidence: 0.94,
      data: {
        steps: [
          { id: "step-1", label: "Registration traffic surge on Dubai Core DC-1" },
          { id: "step-2", label: "AMF-01 CPU pegged at 98% with worker thread queue overflow" },
          { id: "step-3", label: "5G NAS REGISTRATION REJECT messages emitted with Cause #22 (Congestion)" },
          { id: "step-4", label: "RSR breached critical SLA threshold dropping to 94.7%" },
          { id: "step-5", label: "Automated scaling playbook triggered: AMF worker pods scaled from 4 to 8" },
          { id: "step-6", label: "Registration success rate recovered to 99.9% with normalized CPU (<45%)" },
        ],
      },
    },
    {
      id: "visual-evidence-matrix",
      title: "Evidence confidence matrix",
      type: "evidence_confidence_matrix",
      confidence: 0.96,
      data: {
        rows: [
          {
            claim_id: "claim-cpu-sat",
            statement: "Prometheus node_cpu_seconds_total confirmed sustained 98% CPU utilization across all AMF-01 instances",
            grade: "SUPPORTED",
            confidence: 0.99,
            fcaps: ["fault", "performance"],
          },
          {
            claim_id: "claim-nas-reject",
            statement: "OSIX signaling probe captured 4,120 bursts of 5GMM Cause #22 (Congestion) to incoming UEs",
            grade: "HIGH_CONFIDENCE",
            confidence: 0.97,
            fcaps: ["fault"],
          },
          {
            claim_id: "claim-rsr-drop",
            statement: "Mimir KPI metric kagent_5g_rsr_ratio dropped to 94.7% at 06:14:00Z",
            grade: "SUPPORTED",
            confidence: 0.96,
            fcaps: ["performance"],
          },
          {
            claim_id: "claim-mop-scale",
            statement: "Remediation MOP-AMF-AUTO-SCALE-04 executed cleanly in 180s without pod crashback",
            grade: "VERIFIED",
            confidence: 0.95,
            fcaps: ["change"],
          },
        ],
      },
    },
    {
      id: "visual-timeline",
      title: "Incident timeline",
      type: "timeline",
      confidence: 0.94,
      data: {
        events: [
          { id: "t1", timestamp: "06:14:00Z", label: "RSR dropped below 98.5% threshold to 94.7% in DC-1" },
          { id: "t2", timestamp: "06:18:00Z", label: "Prometheus alert: amf_worker_cpu_saturation_critical (98%)" },
          { id: "t3", timestamp: "06:20:00Z", label: "OSIX captured NAS 5GMM Cause #22 congestion rejects" },
          { id: "t4", timestamp: "06:22:15Z", label: "gbrain correlation worker formed candidate 'amf-core-overload-01' (score 0.94)" },
          { id: "t5", timestamp: "06:45:00Z", label: "Auto-remediation initiated: Scale AMF worker pods from 4 to 8" },
          { id: "t6", timestamp: "07:05:00Z", label: "RSR recovered to 99.9%; AMF-01 CPU stabilized at 42%" },
        ],
      },
    },
    {
      id: "visual-next-actions",
      title: "Next best actions",
      type: "next_action_tree",
      confidence: 0.92,
      data: {
        actions: [
          {
            id: "act-1",
            priority: 1,
            label: "Execute Huawei MML: DSP UDM5GSUB and CHK 5GSUBALIGN to audit slice registration stability",
            action_type: "runbook_execution",
            requires_approval: false,
          },
          {
            id: "act-2",
            priority: 2,
            label: "Review OLA/AOLA compliance on RTR_Mobile_Core queue for affected morning shift tickets",
            action_type: "sla_audit",
            requires_approval: false,
          },
          {
            id: "act-3",
            priority: 3,
            label: "Adjust AMF pod horizontal autoscaler lower threshold to trigger at 80% CPU rather than 95%",
            action_type: "policy_change",
            requires_approval: true,
          },
        ],
        questions: [
          "Did the registration storm coincide with a mass radio handover or cell-tower outage?",
          "Should the AMF worker replica count remain at 8 or scale down after peak hour?",
        ],
      },
    },
  ],
};
