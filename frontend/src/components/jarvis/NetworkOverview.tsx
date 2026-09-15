"use client";

import React, { useState } from "react";
import {
  Globe2,
  Radio,
  Server,
  Zap,
  HardDrive,
  Cloud,
  CheckCircle2,
  Activity,
} from "lucide-react";

const DOMAINS = [
  { id: "5g", label: "5G Core", icon: Radio },
  { id: "ims", label: "IMS", icon: Server },
  { id: "vepc", label: "vEPC", icon: Zap },
  { id: "transport", label: "Transport", icon: HardDrive },
  { id: "cloud", label: "Cloud", icon: Cloud },
];

const GAUGES = [
  { label: "Availability", value: 99.8, color: "#10b981", track: "rgba(16,185,129,0.2)" },
  { label: "Utilization", value: 74, color: "#00e5ff", track: "rgba(0,229,255,0.2)" },
  { label: "Performance", value: 92, color: "#38bdf8", track: "rgba(56,189,248,0.2)" },
  { label: "SLA Compl.", value: 99.1, color: "#a855f7", track: "rgba(168,85,247,0.2)" },
];

const NETWORK_SLICES = [
  {
    name: "eMBB High-Throughput Slice",
    status: "HEALTHY",
    latency: "3.8ms",
    throughput: "24.2 Tbps",
    badge: "text-emerald-400 bg-emerald-950/60 border-emerald-500/40",
  },
  {
    name: "URLLC Mission-Critical Slice",
    status: "OPTIMAL",
    latency: "1.1ms",
    throughput: "2.8 Tbps",
    badge: "text-cyan-400 bg-cyan-950/60 border-cyan-500/40",
  },
  {
    name: "mMTC Smart Infrastructure",
    status: "DEGRADED",
    latency: "18.4ms",
    throughput: "1.4 Tbps",
    badge: "text-amber-400 bg-amber-950/60 border-amber-500/40",
  },
];

export function NetworkOverview() {
  const [selectedDomain, setSelectedDomain] = useState("5g");

  return (
    <div className="flex flex-col gap-3 h-full">
      {/* 1. Header */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <Globe2 className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              NETWORK OVERVIEW
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              5G Core • IMS • vEPC • IP Transport • Cloud
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-[9px] font-mono text-cyan-300">
          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
          <span>ALL OPERATIONAL</span>
        </div>
      </div>

      {/* 2. Domain Selector Row */}
      <div className="grid grid-cols-5 gap-1 shrink-0">
        {DOMAINS.map((domain) => {
          const Icon = domain.icon;
          const isSelected = selectedDomain === domain.id;
          return (
            <button
              key={domain.id}
              onClick={() => setSelectedDomain(domain.id)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-all cursor-pointer ${
                isSelected
                  ? "bg-cyan-500/15 border-cyan-400/50 text-[#00e5ff] shadow-[0_0_10px_rgba(0,229,255,0.2)]"
                  : "bg-[#030914]/70 border-cyan-500/20 text-slate-400 hover:text-cyan-200 hover:bg-white/5"
              }`}
            >
              <Icon className="w-3.5 h-3.5" strokeWidth={isSelected ? 2.4 : 1.8} />
              <span className="font-mono text-[8.5px] font-bold uppercase leading-tight">
                {domain.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* 3. Circular Progress Gauges */}
      <div className="grid grid-cols-4 gap-1.5 p-2 rounded-xl bg-[#030914]/80 border border-cyan-500/20 shrink-0">
        {GAUGES.map((g) => {
          const radius = 18;
          const circumference = 2 * Math.PI * radius;
          const offset = Number((circumference - (g.value / 100) * circumference).toFixed(1));

          return (
            <div key={g.label} className="flex flex-col items-center text-center">
              <div className="relative w-12 h-12 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 48 48">
                  <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="none"
                    stroke={g.track}
                    strokeWidth="3.5"
                  />
                  <circle
                    cx="24"
                    cy="24"
                    r={radius}
                    fill="none"
                    stroke={g.color}
                    strokeWidth="3.5"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    className="transition-all duration-700 ease-out"
                  />
                </svg>
                <span className="absolute font-mono text-[10.5px] font-bold text-white">
                  {Math.round(g.value)}%
                </span>
              </div>
              <span className="font-mono text-[8.5px] font-bold text-slate-300 mt-1 leading-tight">
                {g.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* 4. Active Network Slices Stream */}
      <div className="flex flex-col gap-1.5 flex-1 min-h-0">
        <div className="flex items-center justify-between px-0.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Network Slices Telemetry
          </span>
          <span className="font-mono text-[9px] text-cyan-400 font-semibold flex items-center gap-1">
            <Activity className="w-3 h-3" />
            3 Active
          </span>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto jarvis-scrollbar pr-1">
          {NETWORK_SLICES.map((slice) => (
            <div
              key={slice.name}
              className="p-2 rounded-lg bg-[#030914]/80 border border-cyan-500/20 hover:border-cyan-400/40 transition-all flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold text-slate-100">
                  {slice.name}
                </span>
                <span className={`px-1.5 py-0.2 rounded border font-mono text-[8px] font-bold ${slice.badge}`}>
                  {slice.status}
                </span>
              </div>
              <div className="flex items-center justify-between font-mono text-[8.5px] text-slate-400">
                <span>Latency: <strong className="text-cyan-300">{slice.latency}</strong></span>
                <span>Throughput: <strong className="text-cyan-300">{slice.throughput}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. KPI Summary Footer */}
      <div className="grid grid-cols-4 gap-1 p-2 rounded-xl bg-[#030914]/80 border border-cyan-500/20 text-center font-mono shrink-0">
        <div>
          <span className="text-xs font-bold text-[#00e5ff] block">1,248</span>
          <span className="text-[8px] text-slate-400 uppercase block">Sites</span>
        </div>
        <div>
          <span className="text-xs font-bold text-[#00e5ff] block">3,672</span>
          <span className="text-[8px] text-slate-400 uppercase block">Nodes</span>
        </div>
        <div>
          <span className="text-xs font-bold text-[#00e5ff] block">12.8M</span>
          <span className="text-[8px] text-slate-400 uppercase block">Subs</span>
        </div>
        <div>
          <span className="text-xs font-bold text-[#00e5ff] block">38.6T</span>
          <span className="text-[8px] text-slate-400 uppercase block">Tbps</span>
        </div>
      </div>
    </div>
  );
}
