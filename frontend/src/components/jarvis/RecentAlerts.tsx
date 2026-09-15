"use client";

import React from "react";
import { AlertCircle, ChevronRight, CheckCircle2, ShieldAlert } from "lucide-react";

interface AlertItem {
  id: string;
  code: string;
  severity: "CRITICAL" | "MAJOR" | "MINOR" | "INFO";
  title: string;
  node: string;
  time: string;
}

const ALERTS: AlertItem[] = [
  { id: "1", code: "ALT-9041", severity: "CRITICAL", title: "5GC AMF CPU Throttling at 94%", node: "AMF-Core-01", time: "10:41:22" },
  { id: "2", code: "ALT-9039", severity: "MAJOR", title: "IMS SIP Signaling Drop > 4%", node: "IMS-P-CSCF-03", time: "10:40:11" },
  { id: "3", code: "ALT-9038", severity: "MAJOR", title: "Optical Transport BER High", node: "DWDM-Trunk-North", time: "10:39:45" },
  { id: "4", code: "ALT-9035", severity: "MINOR", title: "Interconnect Peering Jitter", node: "BGP-Gateway-02", time: "10:38:33" },
  { id: "5", code: "ALT-9031", severity: "INFO", title: "Config Drift Re-synced", node: "UPF-Pod-Edge", time: "10:37:12" },
  { id: "6", code: "ALT-9029", severity: "INFO", title: "Certificate Auto-Renewed", node: "mTLS-Vault", time: "10:35:04" },
];

const SEVERITY_STYLES = {
  CRITICAL: "bg-rose-950/70 text-rose-400 border-rose-500/40",
  MAJOR: "bg-amber-950/70 text-amber-400 border-amber-500/40",
  MINOR: "bg-cyan-950/70 text-cyan-300 border-cyan-500/40",
  INFO: "bg-slate-900/80 text-slate-300 border-slate-700/50",
};

export function RecentAlerts({ onOpenAlerts }: { onOpenAlerts?: () => void }) {
  return (
    <div className="flex flex-col gap-3 h-full">
      {/* 1. Header */}
      <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-[#00e5ff] flex items-center justify-center border border-cyan-400/35 shadow-[0_0_10px_rgba(0,229,255,0.2)]">
            <AlertCircle className="w-4 h-4" strokeWidth={2.2} />
          </div>
          <div>
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-100 leading-tight">
              ACTIVE ALERTS
            </h3>
            <p className="font-mono text-[9px] text-cyan-400/70">
              Live Ingestion & Prioritization
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-rose-950/50 border border-rose-500/30 text-[9px] font-mono text-rose-300">
          <ShieldAlert className="w-3 h-3 text-rose-400" />
          <span>2 CRITICAL</span>
        </div>
      </div>

      {/* 2. Severity Summary Tiles */}
      <div className="grid grid-cols-4 gap-1.5 shrink-0">
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-rose-500/30 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-rose-400 block leading-tight">Critical</span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-rose-300 mt-0.5">1</span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-amber-500/30 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-amber-400 block leading-tight">Major</span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-amber-300 mt-0.5">2</span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-cyan-500/30 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-cyan-400 block leading-tight">Minor</span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-cyan-300 mt-0.5">1</span>
        </div>
        <div className="p-1.5 rounded-lg bg-[#030914]/80 border border-slate-700/50 flex flex-col items-center text-center">
          <span className="font-mono text-[8px] uppercase tracking-wider text-slate-400 block leading-tight">Info</span>
          <span className="font-mono text-xs sm:text-[13px] font-bold text-slate-300 mt-0.5">2</span>
        </div>
      </div>

      {/* 3. Alert Rows Feed */}
      <div className="flex flex-col gap-1.5 flex-1 min-h-0">
        <div className="flex items-center justify-between px-0.5">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-slate-300">
            Real-time Alarm Ledger
          </span>
          <span className="font-mono text-[9px] text-cyan-400">
            Filtered by Impact
          </span>
        </div>

        <div className="flex flex-col gap-1.5 overflow-y-auto jarvis-scrollbar pr-1">
          {ALERTS.map((alert) => (
            <div
              key={alert.id}
              className="p-2 rounded-lg bg-[#030914]/80 border border-cyan-500/20 hover:border-cyan-400/40 transition-all flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className={`px-1.5 py-0.2 rounded border font-mono text-[8px] font-bold ${SEVERITY_STYLES[alert.severity]}`}>
                    {alert.severity}
                  </span>
                  <span className="font-mono text-[10px] font-bold text-slate-100">
                    {alert.code}
                  </span>
                </div>
                <span className="font-mono text-[8.5px] text-slate-400">
                  {alert.time}
                </span>
              </div>
              <p className="font-mono text-[9px] text-slate-300 pl-0.5">
                {alert.title}
              </p>
              <span className="font-mono text-[8px] text-cyan-400/80 pl-0.5">
                Node: {alert.node}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-cyan-500/20 font-mono text-[9px] shrink-0">
        <span className="text-slate-400">
          Stream: <strong className="text-emerald-400">CONNECTORS LIVE</strong>
        </span>
        <button
          onClick={onOpenAlerts}
          className="flex items-center gap-1 font-bold text-[#00e5ff] hover:text-cyan-300 transition-colors cursor-pointer"
        >
          <span>Query Registry</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
