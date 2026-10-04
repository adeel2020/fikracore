/**
 * SVG coordinate math, conduit definitions, and static catalog arrays for the
 * Neural Reasoning Canvas. All values are in the 1000×400 SVG viewBox.
 *
 * Extracted from page.tsx to isolate pure data from React rendering.
 */

import {
  AlertTriangle,
  Activity,
  FileText,
  GitBranch,
  Layers,
  Ticket,
  Users,
  Settings,
  Database,
  UserCheck,
  FileCode,
  BarChart3,
  Wifi,
  ShieldAlert,
  History,
  BookOpen,
  PhoneCall,
  Radio,
  Globe,
  Server,
  Cpu,
  Zap,
  Cloud,
  Network,
  Lock,
} from "lucide-react";
import type { EvidenceItem, PathwayItem, HypothesisItem, Conduit, HypValidationConduit, OperationalDomainDef } from "./types";

// ─── Evidence Category Definitions ──────────────────────────────────────────

export const EVIDENCE_LIST: EvidenceItem[] = [
  { id: "alarms", name: "Alarms", countLabel: "3 active", count: 3, icon: AlertTriangle, color: "#f43f5e", bgGlow: "rgba(244,63,94,0.3)", borderColor: "border-rose-500" },
  { id: "logs", name: "Logs", countLabel: "2 events", count: 2, icon: FileText, color: "#38bdf8", bgGlow: "rgba(56,189,248,0.3)", borderColor: "border-sky-400" },
  { id: "metrics", name: "Metrics", countLabel: "2 anomalies", count: 2, icon: Activity, color: "#34d399", bgGlow: "rgba(52,211,153,0.3)", borderColor: "border-emerald-400" },
  { id: "traces", name: "Traces", countLabel: "1 trace", count: 1, icon: GitBranch, color: "#c084fc", bgGlow: "rgba(192,132,252,0.3)", borderColor: "border-purple-400" },
  { id: "changes", name: "Changes", countLabel: "1 recent", count: 1, icon: Layers, color: "#fbbf24", bgGlow: "rgba(251,191,36,0.3)", borderColor: "border-amber-400" },
  { id: "tickets", name: "Tickets", countLabel: "1 customer", count: 1, icon: Ticket, color: "#60a5fa", bgGlow: "rgba(96,165,250,0.3)", borderColor: "border-blue-400" },
  { id: "users", name: "User Impact", countLabel: "Multiple reports", count: 4, icon: Users, color: "#f472b6", bgGlow: "rgba(244,114,182,0.3)", borderColor: "border-pink-400" },
];

// ─── Reasoning Pathways Definitions ──────────────────────────────────────────

export const PATHWAYS_LIST: PathwayItem[] = [
  { id: "operational", name: "Operational Evidence", icon: Settings, color: "#38bdf8", active: true, reason: "Raw alarms, telemetry anomalies and interface status admitted." },
  { id: "dependency", name: "Service Dependency", icon: Database, color: "#fbbf24", active: true, reason: "Three dependent services mapped to upstream router path." },
  { id: "subscriber", name: "Subscriber Journey", icon: UserCheck, color: "#c084fc", active: true, reason: "Customer ticket reports correlate with bearer degradation." },
  { id: "config", name: "Change & Configuration", icon: FileCode, color: "#fb923c", active: true, reason: "Policy change CR-7721 logged 2 hours prior to failure." },
  { id: "traffic", name: "Traffic & Capacity", icon: BarChart3, color: "#34d399", active: true, reason: "Throughput dropped by 65% across transport interfaces." },
  { id: "signaling", name: "Control & Signaling", icon: Wifi, color: "#22d3ee", active: true, reason: "BGP adjacency down on neighbor 10.10.1.2." },
  { id: "resilience", name: "Resilience & Failure", icon: ShieldAlert, color: "#14b8a6", active: true, reason: "Redundant link status and standby path failover state." },
  { id: "historical", name: "Historical Pattern", icon: History, color: "#f472b6", active: true, reason: "Matching BGP flap patterns from previous maintenance window." },
  { id: "enrichment", name: "Knowledge Enrichment", icon: BookOpen, color: "#818cf8", active: true, reason: "Knowledge graph query for Router-07 topology relationships." },
];

// ─── Cross Connections Map (Many-to-Many Evidence → Pathways) ────────────────

export const EVIDENCE_TO_PATHWAY_CONDUITS: Conduit[] = [
  // Alarms (0)
  { fromIdx: 0, toIdx: 0, color: "#f43f5e", reason: "Alarms provide primary operational evidence of BGP failure." },
  { fromIdx: 0, toIdx: 1, color: "#f43f5e", reason: "Alarms correlate with downstream service dependency paths." },
  { fromIdx: 0, toIdx: 3, color: "#f43f5e", reason: "Alarms coincide with recent policy configuration update." },
  { fromIdx: 0, toIdx: 6, color: "#f43f5e", reason: "Alarms indicate resilience & redundancy failover state." },

  // Logs (1)
  { fromIdx: 1, toIdx: 0, color: "#38bdf8", reason: "BGP session down logs substantiate operational state." },
  { fromIdx: 1, toIdx: 2, color: "#38bdf8", reason: "Logs detail session disconnect impact on subscriber sessions." },
  { fromIdx: 1, toIdx: 5, color: "#38bdf8", reason: "Session state logs directly inform control & signaling." },

  // Metrics (2)
  { fromIdx: 2, toIdx: 4, color: "#34d399", reason: "Throughput drop metric activates traffic & capacity pathway." },
  { fromIdx: 2, toIdx: 1, color: "#34d399", reason: "Traffic drops map to dependent service degradation." },
  { fromIdx: 2, toIdx: 0, color: "#34d399", reason: "High CPU metric on Router-07 signals operational stress." },
  { fromIdx: 2, toIdx: 7, color: "#34d399", reason: "Telemetry drop aligns with historical anomaly profile." },

  // Traces (3)
  { fromIdx: 3, toIdx: 5, color: "#c084fc", reason: "Path trace timeout identifies signaling plane breakdown." },
  { fromIdx: 3, toIdx: 2, color: "#c084fc", reason: "Trace confirms user packets failing on primary MPLS path." },
  { fromIdx: 3, toIdx: 8, color: "#c084fc", reason: "Path trace queries knowledge graph topology." },

  // Changes (4)
  { fromIdx: 4, toIdx: 3, color: "#fbbf24", reason: "Policy change 2h ago linked to change & config pathway." },
  { fromIdx: 4, toIdx: 1, color: "#fbbf24", reason: "Configuration alters route export to dependent services." },
  { fromIdx: 4, toIdx: 8, color: "#fbbf24", reason: "Policy diff feeds knowledge enrichment rules." },

  // Tickets (5)
  { fromIdx: 5, toIdx: 2, color: "#60a5fa", reason: "Customer complaint ticket validates subscriber journey impact." },
  { fromIdx: 5, toIdx: 1, color: "#60a5fa", reason: "Enterprise APN unreachable ticket links to service dependency." },

  // User Impact (6)
  { fromIdx: 6, toIdx: 2, color: "#f472b6", reason: "Multiple user impact reports confirm wide subscriber effect." },
  { fromIdx: 6, toIdx: 4, color: "#f472b6", reason: "User volume impact maps to traffic degradation scale." },
  { fromIdx: 6, toIdx: 6, color: "#f472b6", reason: "Wide user impact triggers resilience assessment." },
];

// ─── Hypotheses → Validation & Learning Conduits ────────────────────────────

export const HYP_TO_VALIDATION_CONDUITS: HypValidationConduit[] = [
  // H1 (fromIdx: 0) -> Root Cause (targetY: 68)
  { fromIdx: 0, targetY: 68, color: "#10b981", strokeWidth: 2.0, pulse: true },
  // H1 -> Scoped Domain 1 (targetY: 122)
  { fromIdx: 0, targetY: 122, color: "#10b981", strokeWidth: 1.6, pulse: false },
  // H1 -> Scoped Domain 2 (targetY: 152)
  { fromIdx: 0, targetY: 152, color: "#c084fc", strokeWidth: 1.6, pulse: false },
  // H1 -> Scoped Domain 3 (targetY: 182)
  { fromIdx: 0, targetY: 182, color: "#f43f5e", strokeWidth: 1.5, pulse: false },
  // H1 -> Affected Service 1 (targetY: 250)
  { fromIdx: 0, targetY: 250, color: "#f43f5e", strokeWidth: 2.0, pulse: true },
  // H1 -> Affected Service 2 (targetY: 276)
  { fromIdx: 0, targetY: 276, color: "#fbbf24", strokeWidth: 1.5, pulse: false },
  // H1 -> Affected Service 3 (targetY: 302)
  { fromIdx: 0, targetY: 302, color: "#fbbf24", strokeWidth: 1.5, pulse: false },
  // H2 (fromIdx: 1) -> Scoped Domain 2 (targetY: 152)
  { fromIdx: 1, targetY: 152, color: "#38bdf8", strokeWidth: 1.5, pulse: false },
  // H3 (fromIdx: 2) -> Scoped Domain 3 (targetY: 182)
  { fromIdx: 2, targetY: 182, color: "#22d3ee", strokeWidth: 1.5, pulse: false },
];

// ─── Causal Reasoning Relationships ──────────────────────────────────────────

export const PATHWAYS_TO_HYPS: Record<number, number[]> = {
  0: [0],
  1: [0, 1],
  2: [1],
  3: [0, 3],
  4: [1, 2],
  5: [1, 3],
  6: [0],
  7: [0, 3],
  8: [0, 2, 3],
};

export const HYP_TO_PATHWAYS: Record<number, number[]> = {
  0: [0, 1, 3, 6, 7, 8],
  1: [1, 2, 4, 5],
  2: [4, 8],
  3: [3, 5, 7, 8],
};

// ─── SVG Coordinate Math (viewBox 1000×400) ──────────────────────────────────

/** Exact vertical centers of the 7 Evidence items (Col 1) */
export const evidenceY = [44, 96, 148, 200, 252, 304, 356];

/** Exact vertical centers of the 9 Pathway items (Col 2) */
export const pathwayY = [51, 90, 128, 166, 204, 243, 281, 320, 359];

/** Exact vertical centers of the 4 Hypothesis cards (Col 4) */
export const hypY = [70, 150, 230, 310];

/** Exact center of visible cyan intake socket inside Pathway pill */
export const pathwayDotX = 217;

/** Exact center of visible cyan dispatch socket on Pathway pill right edge */
export const pathwayOutDotX = 360;

/** Exact center of visible cyan intake socket on Hypothesis card left edge */
export const hypInDotX = 555;

/** Exact center of visible cyan dispatch socket on Hypothesis card right edge */
export const hypOutDotX = 735;

/** Exact center of visible cyan intake socket on Validation card left edge */
export const valInDotX = 780;

/** Validation intake target definitions matching HYP_TO_VALIDATION_CONDUITS */
export const VALIDATION_INTAKE_TARGETS = [
  { id: "root-cause", y: 68, label: "Root Cause Attribution" },
  { id: "domain-0", y: 122, label: "Primary Telecom Domain" },
  { id: "domain-1", y: 152, label: "Contributing Telecom Domain" },
  { id: "domain-2", y: 182, label: "Affected Telecom Domain" },
  { id: "svc-0", y: 250, label: "Affected Service (Primary)" },
  { id: "svc-1", y: 276, label: "Affected Service (Secondary)" },
  { id: "svc-2", y: 302, label: "Affected Service (Tertiary)" },
];

/** Rim attachment points on outer perimeter of Reasoning Core HUD (center cx=450, cy=200, r=80) */
export const synthInRimPoints = [
  { x: 389, y: 149 }, // p0 Operational Evidence (angle -40 deg)
  { x: 381, y: 160 }, // p1 Service Dependency (angle -30 deg)
  { x: 375, y: 173 }, // p2 Subscriber Journey (angle -20 deg)
  { x: 371, y: 186 }, // p3 Change & Configuration (angle -10 deg)
  { x: 370, y: 200 }, // p4 Traffic & Capacity (angle 0 deg, middle)
  { x: 371, y: 214 }, // p5 Control & Signaling (angle +10 deg)
  { x: 375, y: 227 }, // p6 Resilience & Failure (angle +20 deg)
  { x: 381, y: 240 }, // p7 Historical Pattern (angle +30 deg)
  { x: 389, y: 251 }, // p8 Knowledge Enrichment (angle +40 deg)
];

/** Synthesis output rim points from Reasoning Core to Hypothesis cards */
export const synthOutRimPoints = [
  { x: 516, y: 154 }, // to H1 (target y=70, angle -35 deg)
  { x: 528, y: 183 }, // to H2 (target y=150, angle -12 deg)
  { x: 528, y: 217 }, // to H3 (target y=230, angle +12 deg)
  { x: 516, y: 246 }, // to H4 (target y=310, angle +35 deg)
];

// ─── Static Hypothesis Fallbacks ─────────────────────────────────────────────

export const HYPOTHESES_LIST: HypothesisItem[] = [
  { id: "H1", code: "H1", name: "MPLS Edge Router-07 Failure", confidence: 68, delta: "+7%", deltaIsPos: true, status: "LEADING", color: "#34d399", progressColor: "bg-emerald-400" },
  { id: "H2", code: "H2", name: "SGW Overload", confidence: 28, delta: "-5%", deltaIsPos: false, status: "COMPETING", color: "#60a5fa", progressColor: "bg-blue-400" },
  { id: "H3", code: "H3", name: "DNS Latency Issue", confidence: 18, delta: "+2%", deltaIsPos: true, status: "COMPETING", color: "#22d3ee", progressColor: "bg-cyan-400" },
  { id: "H4", code: "H4", name: "Policy Misconfiguration", confidence: 12, delta: "-1%", deltaIsPos: false, status: "COMPETING", color: "#c084fc", progressColor: "bg-purple-400" },
];

export const HYPOTHESIS_COLORS = ["#34d399", "#60a5fa", "#22d3ee", "#c084fc"];
export const HYPOTHESIS_PROGRESS = ["bg-emerald-400", "bg-blue-400", "bg-cyan-400", "bg-purple-400"];

// ─── 14 Operational Telecom Domains ──────────────────────────────────────────

export const OPERATIONAL_DOMAINS_CATALOG: OperationalDomainDef[] = [
  { id: "ran", name: "RAN", shortName: "RAN", category: "Access", icon: Wifi, color: "#f43f5e", subtext: "gNodeB / CU-DU / Fronthaul" },
  { id: "mobile_core", name: "Mobile Core", shortName: "Mobile Core", category: "Core", icon: Server, color: "#a855f7", subtext: "EPC / 5GC / AMF / UPF / SMF" },
  { id: "ims_voice", name: "IMS / VoLTE", shortName: "IMS/VoLTE", category: "Voice", icon: PhoneCall, color: "#14b8a6", subtext: "VoNR / P-CSCF / S-CSCF" },
  { id: "transport", name: "IP Transport", shortName: "IP Transport", category: "Transport", icon: Radio, color: "#10b981", subtext: "IP/MPLS / Backhaul / SRv6" },
  { id: "roaming", name: "Roaming", shortName: "Roaming", category: "Interconnect", icon: Globe, color: "#06b6d4", subtext: "IPX / DEA / Roaming Hubs" },
  { id: "charging", name: "Charging", shortName: "Charging", category: "BSS", icon: Database, color: "#eab308", subtext: "OCS / CHF / Billing Mediation" },
  { id: "policy_subscriber", name: "Policy & Subscriber Data", shortName: "Policy/Data", category: "Core", icon: UserCheck, color: "#6366f1", subtext: "PCF / PCRF / UDM / HSS" },
  { id: "oss_bss", name: "OSS / BSS", shortName: "OSS/BSS", category: "Operations", icon: Activity, color: "#8b5cf6", subtext: "Assurance / NMS / Telemetry" },
  { id: "cloud_k8s", name: "Cloud / NFVI / Kubernetes", shortName: "Cloud/K8s", category: "Platform", icon: Cpu, color: "#3b82f6", subtext: "K8s CNI / OpenStack / SR-IOV" },
  { id: "vas", name: "VAS", shortName: "VAS", category: "Services", icon: Zap, color: "#f59e0b", subtext: "SMSC / USSD / Value Services" },
  { id: "enterprise", name: "Enterprise Services", shortName: "Enterprise", category: "Services", icon: Cloud, color: "#ec4899", subtext: "Dedicated APNs / L3VPN / Private 5G" },
  { id: "iot", name: "IoT", shortName: "IoT", category: "Services", icon: Network, color: "#10b981", subtext: "NB-IoT / MTC / IoT Gateways" },
  { id: "security", name: "Security", shortName: "Security", category: "Security", icon: ShieldAlert, color: "#ef4444", subtext: "Gi-LAN / Firewalls / HSM / SEGW" },
  { id: "external_partner", name: "External / Partner Networks", shortName: "Partner Net", category: "External", icon: GitBranch, color: "#0284c7", subtext: "Tier-1 Transit / Peering / IXP" },
];

/** Backwards compatibility alias */
export const TELECOM_DOMAINS_CATALOG = OPERATIONAL_DOMAINS_CATALOG;

// ─── Service Impacts ──────────────────────────────────────────────────────────

export const SERVICE_IMPACTS = [
  { name: "Enterprise APN", impact: "-55%", level: "Severe", color: "text-rose-400", badgeBg: "bg-rose-500/20 text-rose-300 border-rose-500/30" },
  { name: "Internet Services", impact: "-42%", level: "Degraded", color: "text-amber-400", badgeBg: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
  { name: "VPN Services", impact: "-38%", level: "Degraded", color: "text-amber-400", badgeBg: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
  { name: "Voice (VoLTE)", impact: "+0%", level: "Normal", color: "text-emerald-400", badgeBg: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
];

// ─── Investigation Timeline ───────────────────────────────────────────────────

export const TIMELINE_EVENTS = [
  { time: "08:54", title: "Incident detected", subtitle: "MPLS Edge Router-07 down", isHighlight: false },
  { time: "08:55", title: "Multi-domain correlation", subtitle: "Related services identified", isHighlight: false },
  { time: "08:56", title: "Knowledge gap detected", subtitle: "Redundant path health unknown", isHighlight: true },
  { time: "08:57", title: "Requesting additional evidence", subtitle: "MPLS path status across domains", isHighlight: false },
];

// ─── Icon helpers ─────────────────────────────────────────────────────────────

export { Lock, Cloud, Globe, Radio } from "lucide-react";
