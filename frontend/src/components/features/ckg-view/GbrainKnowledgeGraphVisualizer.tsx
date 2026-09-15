"use client";

import React, { useState, useMemo } from "react";
import {
  Brain,
  Network,
  GitBranch,
  ShieldCheck,
  Activity,
  ListChecks,
  Search,
  Sparkles,
  Layers,
  ChevronRight,
  Maximize2,
  ExternalLink,
  Cpu,
  Radio,
  FileText,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Info,
  Terminal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  GBRAIN_NODES,
  GBRAIN_LINKS,
  GBRAIN_VISUAL_EXPLANATION,
  GbrainNode,
} from "./gbrain-data";

export function GbrainKnowledgeGraphVisualizer() {
  const [activeTab, setActiveTab] = useState<"visual" | "force" | "matrix" | "timeline">("visual");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("incident-amf-overload");
  const [kindFilter, setKindFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const selectedNode = useMemo(
    () => GBRAIN_NODES.find((n) => n.id === selectedNodeId) || GBRAIN_NODES[0],
    [selectedNodeId]
  );

  const filteredNodes = useMemo(() => {
    return GBRAIN_NODES.filter((node) => {
      const matchesKind = kindFilter === "all" || node.kind === kindFilter;
      const matchesSearch =
        !searchQuery ||
        node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.category.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesKind && matchesSearch;
    });
  }, [kindFilter, searchQuery]);

  // Connected links for the selected node
  const connectedLinks = useMemo(() => {
    return GBRAIN_LINKS.filter(
      (l) => l.source === selectedNodeId || l.target === selectedNodeId
    );
  }, [selectedNodeId]);

  const causalWidget = useMemo(
    () => GBRAIN_VISUAL_EXPLANATION.widgets.find((w) => w.type === "causal_chain"),
    []
  );
  const evidenceWidget = useMemo(
    () => GBRAIN_VISUAL_EXPLANATION.widgets.find((w) => w.type === "evidence_confidence_matrix"),
    []
  );
  const timelineWidget = useMemo(
    () => GBRAIN_VISUAL_EXPLANATION.widgets.find((w) => w.type === "timeline"),
    []
  );
  const actionsWidget = useMemo(
    () => GBRAIN_VISUAL_EXPLANATION.widgets.find((w) => w.type === "next_action_tree"),
    []
  );

  // Node color helper
  const getNodeColor = (kind: string) => {
    switch (kind) {
      case "incident":
        return { bg: "bg-rose-500/20", border: "border-rose-400", text: "text-rose-400", fill: "#f43f5e" };
      case "network-function":
        return { bg: "bg-purple-500/20", border: "border-purple-400", text: "text-purple-400", fill: "#a855f7" };
      case "hypothesis":
        return { bg: "bg-amber-500/20", border: "border-amber-400", text: "text-amber-400", fill: "#f59e0b" };
      case "evidence":
        return { bg: "bg-emerald-500/20", border: "border-emerald-400", text: "text-emerald-400", fill: "#10b981" };
      case "remediation":
        return { bg: "bg-cyan-500/20", border: "border-cyan-400", text: "text-cyan-400", fill: "#06b6d4" };
      case "procedure":
        return { bg: "bg-blue-500/20", border: "border-blue-400", text: "text-blue-400", fill: "#3b82f6" };
      case "rule":
        return { bg: "bg-violet-500/20", border: "border-violet-400", text: "text-violet-400", fill: "#8b5cf6" };
      default:
        return { bg: "bg-cyan-500/20", border: "border-cyan-400", text: "text-cyan-400", fill: "#22d3ee" };
    }
  };

  // Node radius in radar
  const center = { x: 50, y: 50 };
  const plottedNodes = useMemo(() => {
    return filteredNodes.map((node, index) => {
      const total = Math.max(filteredNodes.length, 1);
      const angle = -Math.PI / 2 + (index / total) * Math.PI * 2;
      let radius = 36;
      if (node.kind === "incident") radius = 20;
      else if (node.kind === "network-function") radius = 28;
      else if (node.kind === "hypothesis") radius = 24;
      else if (node.kind === "evidence") radius = 40;
      else if (node.kind === "remediation") radius = 32;

      return {
        ...node,
        x: Number((center.x + Math.cos(angle) * radius).toFixed(2)),
        y: Number((center.y + Math.sin(angle) * radius).toFixed(2)),
      };
    });
  }, [filteredNodes]);

  return (
    <div className="flex h-full flex-col bg-[#050B14] text-slate-100 overflow-hidden font-sans">
      {/* Top Cockpit Header */}
      <header className="flex flex-wrap items-center justify-between border-b border-cyan-500/20 bg-[#071224]/90 px-5 py-3 backdrop-blur-md shrink-0 gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/15 border border-cyan-400/40 text-cyan-400 shadow-[0_0_15px_rgba(0,229,255,0.25)]">
            <Brain className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-wide text-white uppercase flex items-center gap-2">
                gbrain Knowledge Graph
                <span className="rounded-md border border-cyan-400/30 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-mono font-semibold text-cyan-300">
                  CKG v0.38
                </span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">
              Visual Explanation Service • Semantic Telecom Ontology & Causal Layer
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-black/40 p-1">
          <button
            onClick={() => setActiveTab("visual")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "visual"
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/50 shadow-[0_0_12px_rgba(0,229,255,0.2)]"
                : "text-slate-400 hover:text-white"
            )}
          >
            <Network className="h-3.5 w-3.5" />
            <span>Visual Explanation</span>
          </button>
          <button
            onClick={() => setActiveTab("force")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "force"
                ? "bg-purple-500/20 text-purple-300 border border-purple-400/50 shadow-[0_0_12px_rgba(168,85,247,0.2)]"
                : "text-slate-400 hover:text-white"
            )}
          >
            <GitBranch className="h-3.5 w-3.5" />
            <span>CKG Interactive</span>
          </button>
          <button
            onClick={() => setActiveTab("matrix")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "matrix"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-400/50 shadow-[0_0_12px_rgba(16,185,129,0.2)]"
                : "text-slate-400 hover:text-white"
            )}
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Evidence Matrix</span>
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              activeTab === "timeline"
                ? "bg-amber-500/20 text-amber-300 border border-amber-400/50 shadow-[0_0_12px_rgba(245,158,11,0.2)]"
                : "text-slate-400 hover:text-white"
            )}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Timeline</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left / Center Viewport */}
        <div className="flex-1 flex flex-col p-4 overflow-y-auto space-y-4">
          {activeTab === "visual" && (
            <>
              {/* Radar Graph Card with Visual Explanation Service Styling */}
              <div className="relative rounded-2xl border border-cyan-500/30 bg-[#071527]/90 p-4 shadow-[0_0_35px_rgba(0,229,255,0.12)] backdrop-blur-xl flex flex-col min-h-[460px]">
                {/* Radial Glow */}
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,200,255,0.18),transparent_65%)]" />

                {/* Filter and Status Bar */}
                <div className="relative z-10 flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-cyan-500/20">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1.5 font-mono text-xs font-bold uppercase tracking-wider text-cyan-300">
                      <Sparkles className="h-3.5 w-3.5 text-cyan-400 animate-spin" style={{ animationDuration: "12s" }} />
                      ORBITAL KNOWLEDGE RADAR
                    </span>
                    <span className="rounded bg-cyan-950/70 border border-cyan-500/40 px-2 py-0.5 font-mono text-[10px] text-cyan-300">
                      {filteredNodes.length} Semantic Nodes
                    </span>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex flex-wrap items-center gap-1 text-[10px]">
                    {[
                      { id: "all", label: "All" },
                      { id: "incident", label: "Incidents" },
                      { id: "network-function", label: "Twin (NFs)" },
                      { id: "hypothesis", label: "Hypotheses" },
                      { id: "evidence", label: "Evidence" },
                      { id: "remediation", label: "Remediations" },
                      { id: "procedure", label: "Procedures" },
                      { id: "rule", label: "CKG Rules" },
                    ].map((f) => (
                      <button
                        key={f.id}
                        onClick={() => setKindFilter(f.id)}
                        className={cn(
                          "px-2 py-0.5 rounded font-mono transition-colors",
                          kindFilter === f.id
                            ? "bg-cyan-500/30 text-cyan-200 border border-cyan-400/60 font-semibold"
                            : "bg-white/5 text-slate-400 hover:text-white border border-transparent"
                        )}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* SVG Orbital Radar Visualizer */}
                <div className="relative flex-1 flex items-center justify-center my-2 min-h-[320px]">
                  <svg className="h-full w-full max-h-[380px]" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                    {/* Concentric Radar Rings */}
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(34,211,238,0.12)" strokeDasharray="3 4" />
                    <circle cx="50" cy="50" r="32" fill="none" stroke="rgba(34,211,238,0.2)" strokeDasharray="4 5" />
                    <circle cx="50" cy="50" r="22" fill="none" stroke="rgba(59,130,246,0.25)" />
                    <circle cx="50" cy="50" r="12" fill="none" stroke="rgba(168,85,247,0.2)" strokeDasharray="2 3" />

                    {/* Radar Crosshairs */}
                    <line x1="8" y1="50" x2="92" y2="50" stroke="rgba(34,211,238,0.08)" strokeDasharray="2 3" />
                    <line x1="50" y1="8" x2="50" y2="92" stroke="rgba(34,211,238,0.08)" strokeDasharray="2 3" />

                    {/* Links */}
                    {plottedNodes.map((node) => {
                      const isConnected = connectedLinks.some(
                        (l) =>
                          (l.source === node.id && l.target === selectedNodeId) ||
                          (l.target === node.id && l.source === selectedNodeId)
                      );
                      const isTargeted = node.id === selectedNodeId || isConnected;

                      return (
                        <line
                          key={`ray-${node.id}`}
                          x1="50"
                          y1="50"
                          x2={node.x}
                          y2={node.y}
                          stroke={
                            isTargeted
                              ? "rgba(34,211,238,0.85)"
                              : hoveredNodeId === node.id
                              ? "rgba(168,85,247,0.7)"
                              : "rgba(96,165,250,0.22)"
                          }
                          strokeDasharray={isTargeted ? "none" : "2 3"}
                          strokeWidth={isTargeted ? 0.9 : 0.4}
                        />
                      );
                    })}

                    {/* Glowing Center Hub: gbrain Core */}
                    <circle cx="50" cy="50" r="7.5" fill="rgba(8,40,99,0.95)" stroke="rgba(34,211,238,0.9)" strokeWidth="1.2" />
                    <circle cx="50" cy="50" r="4.5" fill="rgba(34,211,238,0.7)" className="animate-ping" style={{ transformOrigin: "center" }} />
                    <text x="50" y="51.2" textAnchor="middle" fill="#ffffff" fontSize="2.8" fontWeight="bold" fontFamily="monospace">
                      GBRAIN
                    </text>

                    {/* Nodes along the orbits */}
                    {plottedNodes.map((node) => {
                      const isSelected = node.id === selectedNodeId;
                      const isHovered = node.id === hoveredNodeId;
                      const colors = getNodeColor(node.kind);

                      return (
                        <g
                          key={`node-${node.id}`}
                          onClick={() => setSelectedNodeId(node.id)}
                          onMouseEnter={() => setHoveredNodeId(node.id)}
                          onMouseLeave={() => setHoveredNodeId(null)}
                          className="cursor-pointer transition-transform duration-200"
                        >
                          {isSelected && (
                            <circle
                              cx={node.x}
                              cy={node.y}
                              r={5.5}
                              fill="none"
                              stroke="#00e5ff"
                              strokeWidth="0.8"
                              className="animate-pulse"
                            />
                          )}
                          <circle
                            cx={node.x}
                            cy={node.y}
                            r={node.kind === "incident" ? 4.4 : node.kind === "network-function" ? 3.8 : 3.2}
                            fill={colors.fill}
                            stroke={isSelected ? "#ffffff" : "rgba(255,255,255,0.7)"}
                            strokeWidth={isSelected ? 0.9 : 0.4}
                            opacity={isHovered || isSelected ? 1 : 0.85}
                          />
                        </g>
                      );
                    })}
                  </svg>
                </div>

                {/* Node Pills Row */}
                <div className="relative z-10 flex flex-wrap items-center justify-center gap-1.5 pt-2 border-t border-white/10 max-h-24 overflow-y-auto custom-scrollbar">
                  {filteredNodes.map((node) => {
                    const isSelected = node.id === selectedNodeId;
                    const colors = getNodeColor(node.kind);

                    return (
                      <button
                        key={`pill-${node.id}`}
                        onClick={() => setSelectedNodeId(node.id)}
                        className={cn(
                          "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium transition-all",
                          isSelected
                            ? "border-cyan-400 bg-cyan-950/90 text-cyan-200 shadow-[0_0_12px_rgba(0,229,255,0.3)] font-semibold"
                            : "border-white/10 bg-[#06111f]/90 text-slate-300 hover:border-cyan-400/40 hover:text-white"
                        )}
                      >
                        <span
                          className="h-1.5 w-1.5 rounded-full"
                          style={{ backgroundColor: colors.fill }}
                        />
                        <span className="truncate max-w-[130px]">{node.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Widget Layout: Causal Chain & Next Actions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Causal Chain Widget */}
                <div className="rounded-2xl border border-cyan-500/20 bg-[#071527]/80 p-4 shadow-lg">
                  <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 mb-3">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">
                      <GitBranch className="h-3.5 w-3.5 text-cyan-400" />
                      Causal Chain
                    </span>
                    <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-400/30 px-1.5 py-0.2 rounded">
                      Confidence 94%
                    </span>
                  </div>
                  <div className="space-y-2">
                    {causalWidget?.data?.steps?.map((step: any, idx: number) => (
                      <div
                        key={step.id}
                        className="flex items-start gap-2.5 rounded-xl border border-white/5 bg-black/30 p-2.5 hover:border-cyan-500/30 transition-colors"
                      >
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-cyan-500/20 border border-cyan-400/40 font-mono text-[10px] font-bold text-cyan-300">
                          {idx + 1}
                        </span>
                        <p className="text-xs text-slate-200 leading-snug">{step.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Next Best Actions Widget */}
                <div className="rounded-2xl border border-cyan-500/20 bg-[#071527]/80 p-4 shadow-lg">
                  <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 mb-3">
                    <span className="font-mono text-xs font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">
                      <ListChecks className="h-3.5 w-3.5 text-cyan-400" />
                      Next Best Actions
                    </span>
                    <span className="font-mono text-[10px] text-cyan-300 bg-cyan-950/60 border border-cyan-400/30 px-1.5 py-0.2 rounded">
                      RTR Runbooks
                    </span>
                  </div>
                  <div className="space-y-2">
                    {actionsWidget?.data?.actions?.map((act: any) => (
                      <div
                        key={act.id}
                        className="rounded-xl border border-white/5 bg-black/30 p-2.5 hover:border-cyan-500/30 transition-colors"
                      >
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="rounded bg-cyan-500/15 border border-cyan-400/30 px-1.5 py-0.5 text-[9px] font-mono font-bold text-cyan-300">
                            PRIORITY {act.priority}
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">
                            {act.action_type}
                          </span>
                        </div>
                        <p className="text-xs text-slate-200">{act.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* CKG Interactive Tab: Full Graphify Engine */}
          {activeTab === "force" && (
            <div className="relative flex-1 min-h-[600px] rounded-2xl border border-purple-500/30 bg-[#071527] overflow-hidden shadow-[0_0_35px_rgba(168,85,247,0.15)] flex flex-col">
              <div className="flex items-center justify-between p-3 border-b border-purple-500/20 bg-[#0a162b]">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4 text-purple-400" />
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-purple-300">
                    CKG Interactive Force Network (Graphify Engine)
                  </span>
                </div>
                <a
                  href="/ckg-view.html"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 rounded-md border border-purple-400/40 bg-purple-500/20 px-2 py-1 text-[11px] font-mono text-purple-200 hover:bg-purple-500/30 transition-colors"
                >
                  <ExternalLink className="h-3 w-3" />
                  <span>Open Fullscreen</span>
                </a>
              </div>
              <iframe
                src="/ckg-view.html"
                title="CKG Force Network"
                className="w-full flex-1 border-none bg-[#0f0f1a]"
              />
            </div>
          )}

          {/* Evidence Matrix Tab */}
          {activeTab === "matrix" && (
            <div className="rounded-2xl border border-emerald-500/30 bg-[#071527]/90 p-5 shadow-lg">
              <div className="flex items-center justify-between pb-3 border-b border-emerald-500/20 mb-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-emerald-400" />
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wider text-emerald-300 font-mono">
                      Evidence Confidence Matrix & FCAPS Lens
                    </h2>
                    <p className="text-xs text-slate-400">
                      Deterministic verification of telemetry claims against gbrain projections
                    </p>
                  </div>
                </div>
                <span className="rounded bg-emerald-950/70 border border-emerald-400/40 px-2 py-0.5 font-mono text-xs text-emerald-300">
                  Audit Grade: 100% Deterministic
                </span>
              </div>

              <div className="space-y-3">
                {evidenceWidget?.data?.rows?.map((row: any) => (
                  <div
                    key={row.claim_id}
                    className="rounded-xl border border-white/10 bg-black/30 p-3 hover:border-emerald-400/40 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="rounded-full border border-emerald-400/40 bg-emerald-400/15 px-2 py-0.5 text-[10px] font-mono font-semibold text-emerald-300">
                          {row.grade}
                        </span>
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {Math.round(row.confidence * 100)}% Confidence
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        {row.fcaps?.map((f: string) => (
                          <span
                            key={f}
                            className="rounded bg-cyan-950/80 border border-cyan-400/30 px-1.5 py-0.2 text-[9px] font-mono text-cyan-300 uppercase"
                          >
                            {f}
                          </span>
                        ))}
                      </div>
                    </div>
                    <p className="text-xs text-slate-200 leading-relaxed">{row.statement}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timeline Tab */}
          {activeTab === "timeline" && (
            <div className="rounded-2xl border border-amber-500/30 bg-[#071527]/90 p-5 shadow-lg">
              <div className="flex items-center justify-between pb-3 border-b border-amber-500/20 mb-4">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-amber-400" />
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wider text-amber-300 font-mono">
                      Operational Incident Timeline
                    </h2>
                    <p className="text-xs text-slate-400">
                      Chronological progression of alarms, correlation candidates, and recovery
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative grid gap-3 pl-4">
                <div className="absolute bottom-2 left-2 top-2 w-px bg-cyan-400/30" />
                {timelineWidget?.data?.events?.map((ev: any) => (
                  <div
                    key={ev.id}
                    className="relative rounded-xl border border-white/10 bg-black/30 p-3 hover:border-amber-400/40 transition-colors"
                  >
                    <div className="absolute -left-[14px] top-4 h-2.5 w-2.5 rounded-full bg-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.9)]" />
                    <div className="text-[10px] font-mono uppercase tracking-wider text-amber-300">
                      {ev.timestamp}
                    </div>
                    <div className="mt-1 text-xs text-slate-200">{ev.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar: Deep Node & gbrain Truth Inspector */}
        <aside className="w-80 lg:w-96 border-l border-cyan-500/20 bg-[#06111f]/95 p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar shrink-0">
          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search gbrain nodes..."
              className="w-full rounded-xl border border-white/10 bg-black/40 pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-400"
            />
          </div>

          {/* Node Profile Header */}
          <div className="rounded-xl border border-cyan-500/30 bg-black/40 p-3">
            <div className="flex items-center justify-between gap-2 mb-2">
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px] font-mono font-bold uppercase",
                  getNodeColor(selectedNode.kind).bg,
                  getNodeColor(selectedNode.kind).border,
                  getNodeColor(selectedNode.kind).text
                )}
              >
                {selectedNode.kind}
              </span>
              {selectedNode.confidence && (
                <span className="font-mono text-[10px] text-emerald-400">
                  {Math.round(selectedNode.confidence * 100)}% Conf
                </span>
              )}
            </div>

            <h3 className="text-sm font-bold text-white mb-1">{selectedNode.label}</h3>
            <p className="font-mono text-[10px] text-cyan-300/80 break-all mb-2">
              {selectedNode.slug}
            </p>
            <p className="text-xs text-slate-300 leading-relaxed">
              {selectedNode.description}
            </p>
          </div>

          {/* Connected Causal Links */}
          <div className="rounded-xl border border-white/10 bg-black/30 p-3">
            <h4 className="font-mono text-[11px] font-bold uppercase tracking-wider text-cyan-300 mb-2 flex items-center gap-1.5">
              <GitBranch className="h-3.5 w-3.5" />
              Connected Causal Links ({connectedLinks.length})
            </h4>
            {connectedLinks.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No direct edges attached.</p>
            ) : (
              <div className="space-y-1.5">
                {connectedLinks.map((link, idx) => {
                  const isOut = link.source === selectedNodeId;
                  const otherNodeId = isOut ? link.target : link.source;
                  const otherNode = GBRAIN_NODES.find((n) => n.id === otherNodeId);

                  return (
                    <button
                      key={idx}
                      onClick={() => setSelectedNodeId(otherNodeId)}
                      className="w-full text-left rounded-lg border border-white/5 bg-white/[0.03] p-2 hover:bg-white/[0.08] hover:border-cyan-400/30 transition-all flex items-center justify-between text-xs group"
                    >
                      <div className="min-w-0 pr-1">
                        <span className="text-[10px] font-mono text-cyan-400 block">
                          {isOut ? "→ " : "← "}
                          {link.relationship}
                        </span>
                        <span className="truncate block font-medium text-slate-200 group-hover:text-white">
                          {otherNode?.label || otherNodeId}
                        </span>
                      </div>
                      <ChevronRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-cyan-400 shrink-0" />
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Frontmatter Metadata */}
          {selectedNode.frontmatter && (
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <h4 className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-slate-400" />
                Frontmatter Metadata
              </h4>
              <div className="space-y-1 font-mono text-[11px]">
                {Object.entries(selectedNode.frontmatter).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-2 border-b border-white/5 pb-1">
                    <span className="text-slate-400">{k}</span>
                    <span className="text-cyan-300 truncate max-w-[160px]">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compiled Truth Viewer */}
          {selectedNode.compiled_truth && (
            <div className="rounded-xl border border-white/10 bg-black/30 p-3">
              <h4 className="font-mono text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-400" />
                Compiled Truth
              </h4>
              <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap bg-black/40 p-2.5 rounded-lg border border-white/5 leading-relaxed">
                {selectedNode.compiled_truth}
              </pre>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
