"use client";
 
import React from "react";
import { AlertCircle, ChevronUp } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { useLocalStorageData } from "@/lib/useLocalStorageData";

export function EarlyWarningDiagnostics() {
  const warningCards = useLocalStorageData<any[]>("Early_Warning_Cards", []);

  return (
    <GlassCard className="p-4 flex flex-col h-[410px]" hover={true}>
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#242F41]/45 shrink-0">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase mr-1">Early Warning Dashboard ({warningCards.length})</span>
          <span className="px-1.5 py-0.5 rounded bg-[#FFA800]/10 text-[#FFA800] border-[#FFA800]/25 text-[8px] font-mono tracking-wider font-bold">
            Monitor: Last 4 Hours (00:04:00)
          </span>
        </div>
        <ChevronUp className="h-4 w-4 text-neutral-500 hover:text-white cursor-pointer" />
      </div>

      <div className="w-full h-[340px]">
        {warningCards.length === 0 ? (
          <div className="grid grid-cols-6 auto-rows-auto gap-2 w-full h-full">
            <div className="col-span-2 row-span-2 rounded-xl border border-cyan-500/10 bg-cyan-500/5 h-[140px]" />
            <div className="col-span-2 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-2 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[65px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
            <div className="col-span-1 rounded-xl border border-neutral-800 bg-neutral-900/20 h-[50px]" />
          </div>
        ) : (
          <div className="grid grid-cols-6 auto-rows-auto gap-2 w-full h-full">
            {warningCards.map((card: any) => {
              let span = "col-span-1";
              if (card.id === 1) span = "col-span-2 row-span-2";
              else if (card.id === 2 || card.id === 5) span = "col-span-2";

              return (
                <div
                  key={card.id}
                  className={`p-2.5 rounded-xl border flex flex-col justify-between transition-all duration-300 group relative cursor-help ${card.className} ${span}`}
                >
                  <div className="flex items-center justify-between gap-1.5 shrink-0">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <div className={`w-8 h-8 rounded-full border flex items-center justify-center font-bold text-[9px] relative shrink-0 ${card.badgeColor}`}>
                        {card.initials}
                        <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-emerald-500 border border-[#131926] shadow-lg " />
                      </div>
                      <span className="text-[9px] font-extrabold tracking-tight text-white truncate max-w-[120px]">
                        {card.queue}
                      </span>
                    </div>
                  </div>

                  <span className={`text-[8.5px] font-extrabold tracking-wide uppercase mt-2 shrink-0 ${card.catColor}`}>
                    {card.category}
                  </span>

                  <span className="text-[8px] text-neutral-400 mt-1 leading-normal font-medium flex-1 overflow-hidden line-clamp-3">
                    {card.details}
                  </span>

                  <div className="absolute bottom-[105%] left-1/2 -translate-x-1/2 mb-1 w-56 p-2.5 rounded-lg bg-[#131926]/95 border border-cyan-500/40 text-neutral-200 text-[8px] leading-relaxed shadow-2xl opacity-0 scale-95 pointer-events-none group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 z-50">
                    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 w-2 h-2 rotate-45 bg-[#131926] border-r border-b border-cyan-500/40" />
                    <div className="font-extrabold text-white mb-1 border-b border-neutral-700/40 pb-1 flex items-center justify-between">
                      <span>{card.queue}</span>
                      <span className="px-1 py-0.2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-[7px] uppercase tracking-wider font-mono">Telemetry Alert</span>
                    </div>
                    <div className="font-semibold text-cyan-300 mb-0.5 uppercase tracking-wide text-[7.5px]">{card.category}</div>
                    <div className="text-neutral-300 font-medium leading-normal">{card.details}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </GlassCard>
  );
}
