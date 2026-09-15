"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import type { RTRJourneyOverlayPresentation, SynchronizedVisualHop } from "@/lib/mark-presentation";
import { useRTRJourneySync } from "@/hooks/useRTRJourneySync";

interface RTRJourneyOverlayProps {
  presentation: RTRJourneyOverlayPresentation;
  onClose?: () => void;
}

export const RTRJourneyOverlay: React.FC<RTRJourneyOverlayProps> = ({ presentation, onClose }) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [selectedHop, setSelectedHop] = useState<SynchronizedVisualHop | null>(null);

  const { activeHopIndex, activeHop, cometProgress, isCometActive, seekToHop } = useRTRJourneySync(
    presentation.hops,
    26000,
    true
  );

  // Active or clicked detail
  const inspectingHop = selectedHop || activeHop || presentation.hops[0];

  // Minimized Floating HUD Chip View
  if (isMinimized) {
    return (
      <div
        className="fixed top-20 right-8 z-50 flex items-center gap-3 px-4 py-2 rounded-full border border-purple-500/30 bg-[#0a0c10]/80 backdrop-blur-md shadow-2xl cursor-pointer hover:border-purple-400 transition-all animate-in fade-in duration-300"
        onClick={() => setIsMinimized(false)}
      >
        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
        <span className="text-xs font-mono font-medium text-slate-200">
          {presentation.ticket_token} • {presentation.hops.length} Hops
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30">
          OLA Breached in {presentation.delinquent_queue || "HPSA"}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </div>
    );
  }

  return (
    <div
      className="absolute inset-0 z-40 pointer-events-auto flex flex-col justify-between p-6 rounded-2xl bg-[#0a0c10]/65 backdrop-blur-[12px] border border-slate-800/60 shadow-2xl overflow-hidden transition-all duration-300 animate-in fade-in zoom-in-95"
    >
      {/* 1. SEMANTIC REACTIVE AMBIENT GLOW LAYER */}
      <div
        className={`absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full blur-[100px] pointer-events-none transition-colors duration-1000 ${
          activeHop?.sla_status === "BREACHED"
            ? "bg-rose-600/15"
            : activeHop?.sla_status === "AT_RISK"
            ? "bg-amber-600/15"
            : "bg-cyan-600/10"
        }`}
      />

      {/* 2. TOP SLA GOVERNANCE & CONTROL STRIP */}
      <div className="relative z-10 flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="px-3 py-1 rounded-md bg-purple-500/10 border border-purple-500/30 text-purple-300 font-mono text-xs flex items-center gap-2">
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Mobile Core RTR Ticket Journey</span>
          </div>
          <span className="font-mono text-sm font-semibold text-slate-200 tracking-wider">
            {presentation.ticket_token}
          </span>
          <span className="text-xs text-slate-400 font-mono">
            [Sub: {presentation.subscriber_token}]
          </span>
        </div>

        {/* SLA Governance Badges */}
        <div className="flex items-center gap-3">
          {/* AOLA Badge */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-lg font-mono text-xs border ${
              presentation.aola_achieved
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-rose-500/10 border-rose-500/30 text-rose-400"
            }`}
          >
            <span>AOLA:</span>
            <span className="font-bold">{presentation.aola_rtr_hours}h / 2.0h</span>
            <span>({presentation.aola_achieved ? "Achieved" : "Breached"})</span>
          </div>

          {/* OLA Badge */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-lg font-mono text-xs border ${
              presentation.ola_achieved
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-rose-500/10 border-rose-500/30 text-rose-400"
            }`}
          >
            <span>OLA:</span>
            <span className="font-bold">{presentation.ola_noc_hours}h / 6.0h</span>
            <span>
              ({presentation.ola_achieved ? "Achieved" : `Breached in ${presentation.delinquent_queue || "HPSA"}`})
            </span>
          </div>

          {/* Minimize / Close Controls */}
          <div className="flex items-center gap-1.5 ml-2">
            <button
              onClick={() => setIsMinimized(true)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
              title="Minimize to HUD Pill"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                title="Close Overlay"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3. CENTER: CHRONOLOGICAL FLUID BEZIER RAIL & STATIONS */}
      <div className="relative z-10 my-auto py-8">
        <div className="relative flex items-center justify-between max-w-4xl mx-auto px-6">
          {/* SVG Connecting Rail with Photon Comet */}
          <svg
            className="absolute left-10 right-10 top-1/2 -translate-y-1/2 w-[calc(100%-80px)] h-8 pointer-events-none"
            style={{ zIndex: 0 }}
          >
            <line
              x1="0%"
              y1="50%"
              x2="100%"
              y2="50%"
              stroke="rgba(71, 85, 105, 0.4)"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            {/* Photon Comet Pulse */}
            {isCometActive && (
              <circle
                cx={`${cometProgress * 100}%`}
                cy="50%"
                r="5"
                fill="#E879F9"
                className="filter drop-shadow-[0_0_8px_#C084FC]"
              />
            )}
          </svg>

          {/* Hop Stations */}
          {presentation.hops.map((hop, idx) => {
            const isActive = idx === activeHopIndex;
            const isPast = idx < activeHopIndex;
            const isBreached = hop.sla_status === "BREACHED";

            return (
              <div key={hop.hop_number} className="relative z-10 flex flex-col items-center">
                {/* Vaulted Ping-Pong Return Arc (if bounced) */}
                {hop.is_bounced_back_to_rtr && (
                  <div className="absolute -top-7 px-2 py-0.5 rounded-full text-[10px] font-mono tracking-tight bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse whitespace-nowrap">
                    ↩ Bounced (Touch #2)
                  </div>
                )}

                {/* Station Pill */}
                <button
                  onClick={() => {
                    seekToHop(hop.hop_number);
                    setSelectedHop(hop);
                  }}
                  className={`relative flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-200 text-left cursor-pointer hover:scale-105 active:scale-95 ${
                    isActive
                      ? "bg-slate-900/95 border-purple-500 ring-2 ring-purple-500/30 shadow-[0_0_20px_rgba(192,132,252,0.25)]"
                      : isPast
                      ? "bg-slate-950/70 border-slate-700/60 opacity-85 hover:opacity-100"
                      : "bg-slate-950/40 border-slate-800/40 opacity-40 hover:opacity-75"
                  }`}
                >
                  {/* Status Indicator Icon */}
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold ${
                      isBreached
                        ? "bg-rose-500/20 text-rose-400 border border-rose-500/40"
                        : isPast
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                        : isActive
                        ? "bg-purple-500 text-white animate-pulse"
                        : "bg-slate-800 text-slate-500"
                    }`}
                  >
                    {hop.hop_number}
                  </div>

                  {/* Queue Name & Dwell Barcode */}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-slate-100 font-mono">
                        {hop.assigned_queue}
                      </span>
                      {isBreached && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400">
                          delayed
                        </span>
                      )}
                    </div>

                    {/* 2px Micro-Segmented Dwell Barcode */}
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <div className="w-16 h-1 rounded-full bg-slate-800 overflow-hidden flex">
                        <div
                          className="h-full bg-emerald-400"
                          style={{
                            width: `${Math.min(
                              (hop.active_triage_hours / (hop.time_spent_hours || 1)) * 100,
                              100
                            )}%`,
                          }}
                          title={`Active: ${hop.active_triage_hours}h`}
                        />
                        <div
                          className={`h-full ${isBreached ? "bg-rose-500" : "bg-amber-400"}`}
                          style={{
                            width: `${Math.min(
                              (hop.idle_waiting_hours / (hop.time_spent_hours || 1)) * 100,
                              100
                            )}%`,
                          }}
                          title={`Idle wait: ${hop.idle_waiting_hours}h`}
                        />
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {hop.time_spent_hours}h
                      </span>
                    </div>
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. BOTTOM SPOKEN TRANSCRIPT & DIAGNOSTIC DRAWER */}
      <div className="relative z-10 pt-4 border-t border-slate-800/80 grid grid-cols-3 gap-6">
        {/* Spoken Narration Stream */}
        <div className="col-span-2 bg-slate-950/60 border border-slate-800/60 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-xs font-mono text-purple-300 mb-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
            <span>Mark Spoken Narration (Current Step {activeHopIndex + 1} of {presentation.hops.length})</span>
          </div>
          <p className="text-sm font-medium text-slate-200 leading-relaxed font-sans">
            &ldquo;{activeHop?.spoken_cue_text || presentation.spoken_script}&rdquo;
          </p>
        </div>

        {/* Selected Hop Diagnostic Card */}
        <div className="bg-slate-950/60 border border-slate-800/60 p-3.5 rounded-xl font-mono text-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="font-semibold text-slate-200">
              Step {inspectingHop.hop_number}: {inspectingHop.assigned_queue}
            </span>
            <span className="text-[10px] text-slate-500">{inspectingHop.time_spent_hours} hrs total</span>
          </div>
          <div className="space-y-1.5 text-slate-300 text-[11px]">
            <div>
              <span className="text-slate-500">Action: </span>
              <span>{inspectingHop.action_taken}</span>
            </div>
            {inspectingHop.finding_code && (
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500">Finding: </span>
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-amber-300 border border-slate-700">
                  {inspectingHop.finding_code}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
