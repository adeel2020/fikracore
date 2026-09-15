"use client";

import React from "react";
import { Database, ChevronRight, CheckCircle2, Layers, Server, ShieldCheck } from "lucide-react";

const ASSET_ITEMS = [
  { label: "5G Core NFs", count: "2,548", dotColor: "bg-[#00e5ff]", pct: "38%" },
  { label: "K8s Pods / Nodes", count: "4,321", dotColor: "bg-[#38bdf8]", pct: "28%" },
  { label: "Slice Profiles", count: "2,105", dotColor: "bg-[#818cf8]", pct: "16%" },
  { label: "Playbooks & Policies", count: "1,254", dotColor: "bg-[#a855f7]", pct: "10%" },
  { label: "Documentation & KG", count: "2,318", dotColor: "bg-[#f59e0b]", pct: "8%" },
];

const RECENT_CHANGES = [
  { name: "UPF-Edge-DubaiNorth", type: "VNF Update", status: "VERIFIED", time: "3m ago" },
  { name: "AMF-Control-Slice01", type: "Config Drift", status: "REMEDIATED", time: "14m ago" },
  { name: "SMF-Session-Anchor", type: "Policy Rollout", status: "IN_SYNC", time: "28m ago" },
];

export function DigitalAssets({ onOpenModal }: { onOpenModal?: () => void }) {
  return (
    <div className="flex flex-col gap-3 h-full">
      {/* 1. Header */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <Database className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              DIGITAL ASSETS
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              Inventory • Services • Configurations
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-[9px] font-mono text-cyan-300">
          <CheckCircle2 className="w-3 h-3 text-cyan-400" />
          <span>IN SYNC</span>
        </div>
      </div>

      {/* 2. Donut & Asset Distribution */}
      <div className="grid grid-cols-[105px_1fr] gap-3 p-2.5 rounded-xl bg-[#030914]/80 border border-cyan-500/20 items-center shrink-0">
        {/* Conic Donut */}
        <div
          className="relative w-[95px] h-[95px] mx-auto rounded-full flex items-center justify-center p-2.5 shadow-[0_0_15px_rgba(0,229,255,0.15)]"
          style={{
            background:
              "conic-gradient(#00e5ff 0% 38%, #38bdf8 38% 66%, #818cf8 66% 82%, #a855f7 82% 92%, #f59e0b 92% 100%)",
          }}
        >
          <div className="w-full h-full rounded-full bg-[#030914] flex flex-col items-center justify-center text-center font-mono border border-cyan-500/30">
            <span className="text-xs sm:text-[13px] font-bold text-white leading-none">
              12,546
            </span>
            <span className="text-[7.5px] text-slate-400 uppercase mt-0.5">
              Total Assets
            </span>
          </div>
        </div>

        {/* Asset Items List */}
        <div className="flex flex-col gap-1 font-mono text-[9px]">
          {ASSET_ITEMS.map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 truncate">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${item.dotColor}`} />
                <span className="text-slate-300 truncate">{item.label}</span>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <span className="font-bold text-white">{item.count}</span>
                <span className="text-slate-500 text-[8px]">({item.pct})</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Recent Asset Lifecycle Changes */}
      <div className="flex flex-col gap-1.5 flex-1 min-h-0">
        <div className="flex items-center justify-between px-0.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Asset Drift & Changes
          </span>
          <span className="font-mono text-[9px] text-cyan-400">
            Realtime Audit
          </span>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto jarvis-scrollbar pr-1">
          {RECENT_CHANGES.map((change) => (
            <div
              key={change.name}
              className="p-2 rounded-lg bg-[#030914]/80 border border-cyan-500/20 hover:border-cyan-400/40 transition-all flex flex-col gap-0.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold text-slate-100">
                  {change.name}
                </span>
                <span className="px-1.5 py-0.2 rounded border font-mono text-[8px] font-bold text-emerald-400 bg-emerald-950/60 border-emerald-500/40">
                  {change.status}
                </span>
              </div>
              <div className="flex items-center justify-between font-mono text-[8.5px] text-slate-400">
                <span>Type: <strong className="text-cyan-300">{change.type}</strong></span>
                <span>{change.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Footer Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-cyan-500/20 font-mono text-[9px] shrink-0">
        <span className="text-slate-400">
          Last Synced: <strong className="text-cyan-300">Just now</strong>
        </span>
        <button
          onClick={onOpenModal}
          className="flex items-center gap-1 font-bold text-[#00e5ff] hover:text-cyan-300 transition-colors cursor-pointer"
        >
          <span>Inventory Details</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
