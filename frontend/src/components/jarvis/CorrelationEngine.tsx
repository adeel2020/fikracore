"use client";

import React, { useState } from "react";
import { Workflow, ShieldAlert, Cpu, Network, Lock, CheckCircle2 } from "lucide-react";

interface NodeItem {
  id: number;
  x: number;
  y: number;
  type: "alarm" | "performance" | "topology" | "security";
  label: string;
  count: number;
  sub: string;
}

const NODES: NodeItem[] = [
  { id: 0, x: 12, y: 34, type: "performance", label: "gNB_Latency_01", count: 18, sub: "RAN Edge Cell" },
  { id: 1, x: 28, y: 20, type: "topology", label: "UPF_Core_Pod3", count: 45, sub: "User Plane Function" },
  { id: 2, x: 48, y: 28, type: "performance", label: "AMF_Queue", count: 12, sub: "Access Mobility" },
  { id: 3, x: 68, y: 18, type: "topology", label: "SMF_Session_D", count: 24, sub: "Session Mgmt" },
  { id: 4, x: 86, y: 30, type: "alarm", label: "Optical_LOS", count: 6, sub: "DWDM Trunk Line" },
  { id: 5, x: 18, y: 64, type: "security", label: "DDoS_Anom_99", count: 3, sub: "Edge Firewall" },
  { id: 6, x: 36, y: 50, type: "performance", label: "BGP_RouteFlap", count: 32, sub: "Border Gateway" },
  { id: 7, x: 52, y: 56, type: "alarm", label: "Root_RCA_152", count: 152, sub: "Core Incident Root" },
  { id: 8, x: 72, y: 50, type: "topology", label: "NWDAF_Analytics", count: 64, sub: "Network Data Analytics" },
  { id: 9, x: 88, y: 64, type: "security", label: "Cert_Expiry_Edge", count: 2, sub: "mTLS Certificate" },
  { id: 10, x: 28, y: 84, type: "alarm", label: "Power_Degrade_Site2", count: 8, sub: "Substation PSU" },
  { id: 11, x: 46, y: 82, type: "performance", label: "Packet_Drop_Trunk", count: 89, sub: "Transport Queue" },
  { id: 12, x: 66, y: 80, type: "topology", label: "Slice_eMBB_Core", count: 110, sub: "SLA Slice #1" },
  { id: 13, x: 84, y: 82, type: "security", label: "ACL_Violation_GW", count: 5, sub: "Ingress Router" },
];

const EDGES: [number, number][] = [
  [0, 1], [0, 5], [0, 6],
  [1, 2], [1, 6],
  [2, 3], [2, 6], [2, 7],
  [3, 4], [3, 8],
  [4, 9],
  [5, 6], [5, 10],
  [6, 7], [6, 10], [6, 11],
  [7, 8], [7, 11], [7, 12],
  [8, 9], [8, 12],
  [9, 13],
  [10, 11],
  [11, 12],
  [12, 13],
];

const TYPE_CONFIG = {
  alarm: { stroke: "#ff385c", fill: "#ff385c", label: "Alarm", icon: ShieldAlert },
  performance: { stroke: "#00e5ff", fill: "#00e5ff", label: "Performance", icon: Cpu },
  topology: { stroke: "#a855f7", fill: "#a855f7", label: "Topology", icon: Network },
  security: { stroke: "#f97316", fill: "#f97316", label: "Security", icon: Lock },
};

const CORRELATED_INCIDENTS = [
  {
    id: "INC-152",
    title: "UPF Packet Drop ↔ Optical LOS",
    root: "Root Cause: Optical Trunk A Degradation",
    confidence: "94%",
    severity: "CRITICAL",
    badgeColor: "text-rose-400 bg-rose-950/60 border-rose-500/40",
  },
  {
    id: "INC-089",
    title: "AMF Session Spike ↔ Edge DDoS Anomaly",
    root: "Root Cause: Ingress ACL Policy Drift",
    confidence: "88%",
    severity: "MAJOR",
    badgeColor: "text-amber-400 bg-amber-950/60 border-amber-500/40",
  },
  {
    id: "INC-044",
    title: "BGP Route Flap ↔ NWDAF Latency Alert",
    root: "Root Cause: Inter-AS Peering Jitter",
    confidence: "82%",
    severity: "MINOR",
    badgeColor: "text-cyan-400 bg-cyan-950/60 border-cyan-500/40",
  },
];

export function CorrelationEngine() {
  const [selectedNode, setSelectedNode] = useState<NodeItem>(NODES[7]);

  const selectedConfig = TYPE_CONFIG[selectedNode.type];
  const SelectedIcon = selectedConfig.icon;

  return (
    <div className="flex flex-col gap-2.5 h-full">
      {/* 1. Header Card */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <Workflow className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              CORRELATION ENGINE
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              Real-time Event RCA & Topology Graph
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-[9px] font-mono text-cyan-300">
          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
          <span>99.4% ACCURACY</span>
        </div>
      </div>

      {/* 2. Top Metric Cards (4-Grid) */}
      <div className="grid grid-cols-4 gap-1.5 shrink-0">
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-cyan-500/20 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-slate-400 block leading-tight">
            Total Events
          </span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-white mt-0.5">
            18,290
          </span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-cyan-500/20 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-cyan-400/80 block leading-tight">
            Correlated
          </span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-[#00e5ff] mt-0.5">
            3,456
          </span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-cyan-500/20 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-rose-400/80 block leading-tight">
            Active RCA
          </span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-rose-400 mt-0.5">
            152
          </span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-cyan-500/20 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-emerald-400/80 block leading-tight">
            MTTR Gain
          </span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-emerald-400 mt-0.5">
            -42%
          </span>
        </div>
      </div>

      {/* 3. Interactive Topology Graph Canvas */}
      <div className="relative h-[190px] w-full rounded-xl bg-[#020712]/90 border border-cyan-500/30 overflow-hidden flex items-center justify-center shadow-inner shrink-0">
        {/* Fine background grid */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: "linear-gradient(to right, #00e5ff 1px, transparent 1px), linear-gradient(to bottom, #00e5ff 1px, transparent 1px)",
            backgroundSize: "20px 20px",
          }}
        />

        <svg viewBox="0 0 100 100" className="w-full h-full relative z-10 p-2">
          <defs>
            <radialGradient id="clusterGlow" cx="52%" cy="56%" r="50%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.85" />
              <stop offset="50%" stopColor="#00e5ff" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#00e5ff" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Central incident energy cloud */}
          <circle cx="52" cy="56" r="19" fill="url(#clusterGlow)" />

          {/* Topology Edges */}
          {EDGES.map(([src, dst], idx) => (
            <line
              key={idx}
              x1={NODES[src].x}
              y1={NODES[src].y}
              x2={NODES[dst].x}
              y2={NODES[dst].y}
              stroke="#00e5ff"
              strokeWidth="0.65"
              strokeOpacity="0.65"
            />
          ))}

          {/* Topology Nodes */}
          {NODES.map((node) => {
            const isSelected = selectedNode.id === node.id;
            const isCentral = node.id === 7;
            const cfg = TYPE_CONFIG[node.type];
            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform hover:scale-125"
                onClick={() => setSelectedNode(node)}
              >
                {isCentral && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="6.5"
                    fill="none"
                    stroke="#ff385c"
                    strokeWidth="0.8"
                    strokeDasharray="2 2"
                    className="hud-spin-slow"
                  />
                )}
                {isSelected && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="5.5"
                    fill="none"
                    stroke="#00e5ff"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                    className="hud-spin-slow"
                  />
                )}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 3.2 : isCentral ? 3.0 : 2.0}
                  fill="#061224"
                  stroke={cfg.stroke}
                  strokeWidth={isSelected ? 1.8 : 1.2}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={isSelected ? 1.4 : 0.9}
                  fill={cfg.fill}
                />
              </g>
            );
          })}
        </svg>

        {/* Selected Node HUD Badge */}
        <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-1 rounded bg-[#040c18]/90 border border-cyan-500/40 shadow-md backdrop-blur-md">
          <SelectedIcon className="w-3 h-3 text-cyan-400" />
          <div className="font-mono text-[9px] leading-tight">
            <span className="font-bold text-white block">{selectedNode.label}</span>
            <span className="text-cyan-400/80 text-[8px]">{selectedNode.sub} • {selectedNode.count} events</span>
          </div>
        </div>
      </div>

      {/* 4. Active Correlated Incident Chains */}
      <div className="flex flex-col gap-1.5 flex-1 min-h-0">
        <div className="flex items-center justify-between px-0.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Correlated Incident Clusters
          </span>
          <span className="font-mono text-[9px] text-cyan-400 font-semibold">
            3 High-Priority
          </span>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto jarvis-scrollbar pr-1">
          {CORRELATED_INCIDENTS.map((inc) => (
            <div
              key={inc.id}
              className="p-2 rounded-lg bg-[#030914]/80 border border-cyan-500/20 hover:border-cyan-400/50 hover:bg-cyan-950/20 transition-all flex flex-col gap-0.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className={`px-1.5 py-0.2 rounded border font-mono text-[8px] font-bold ${inc.badgeColor}`}>
                    {inc.id}
                  </span>
                  <span className="font-mono text-[10px] font-bold text-slate-100">
                    {inc.title}
                  </span>
                </div>
                <span className="font-mono text-[9px] font-semibold text-cyan-400">
                  {inc.confidence}
                </span>
              </div>
              <p className="font-mono text-[8.5px] text-slate-400 pl-1">
                {inc.root}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Severity Legend Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-cyan-500/20 font-mono text-[8.5px] font-bold text-slate-300 shrink-0">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_6px_#f43f5e]" />
          ALARM
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]" />
          PERFORMANCE
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-purple-400 shadow-[0_0_6px_#a855f7]" />
          TOPOLOGY
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-orange-400 shadow-[0_0_6px_#f97316]" />
          SECURITY
        </span>
      </div>
    </div>
  );
}
