"use client";

import React, { useState } from "react";
import { Clock, Info, Activity, Gauge } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { useLocalStorageData, useGlobalLocalStorageData } from "@/lib/useLocalStorageData";



export function AvgQueueTime() {
  const avgTimes = useLocalStorageData<any[]>("NOC_Queue_Times", []);

  return (
    <GlassCard id="avg-queue-times-card" className="p-4 flex flex-col justify-between h-[300px]" hover={true}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Avg Time Spent in Queues</span>
          <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-[8px] text-amber-400 border border-amber-500/30 uppercase tracking-wider font-bold">
            SLA: 2 Hrs
          </span>
        </div>
        <Clock className="h-4 w-4 text-cyan-400" />
      </div>
      {avgTimes.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
          <table className="w-full text-left border-collapse text-[10px]">
            <thead>
              <tr className="border-b border-[#242F41] text-neutral-500 pb-1 font-semibold uppercase tracking-wider">
                <th className="pb-1.5 font-semibold">NOC Queue</th>
                <th className="pb-1.5 font-semibold text-center">Closed</th>
                <th className="pb-1.5 font-semibold text-center">Total</th>
                <th className="pb-1.5 font-semibold text-center">Avg Time</th>
                <th className="pb-1.5 font-semibold text-right">SLA %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#242F41]/35">
              {avgTimes.map((q, idx) => {
                const avgMinutes = parseInt(q.avg);
                const isOverSla = avgMinutes > 120;
                return (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-1.5 text-white font-medium">{q.name}</td>
                    <td className="py-1.5 text-center font-mono text-neutral-400">{q.closed}</td>
                    <td className="py-1.5 text-center font-mono text-neutral-400">{q.total}</td>
                    <td className={`py-1.5 text-center font-mono font-semibold ${isOverSla ? "text-[#FF0844]" : "text-cyan-400"}`}>
                      {q.avg}
                    </td>
                    <td className="py-1.5 text-right font-mono font-medium text-neutral-300">
                      <span className={q.compliance < 75 ? "text-amber-400" : "text-emerald-400"}>
                        {q.compliance}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </GlassCard>
  );
}

export function TotalTicketDistribution() {
  const [hoveredMonth, setHoveredMonth] = useState<string | null>(null);
  const monthlyDist = useLocalStorageData<any[]>("Monthly_Distribution", []);
  const globalDist = useGlobalLocalStorageData("Monthly_Distribution", []);

  const maxTickets = Math.max(...globalDist.map((d: any) => (d.blue || 0) + (d.brown || 0)), 1);

  return (
    <GlassCard id="ticket-distribution-card" className="p-4 flex flex-col justify-between h-[370px] relative overflow-visible" hover={true}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Monthly Distribution</span>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span className="text-[8px] text-neutral-400 font-semibold uppercase">BLUE</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-pink-500" />
            <span className="text-[8px] text-neutral-400 font-semibold uppercase">BROWN</span>
          </div>
          <Info className="h-3.5 w-3.5 text-neutral-500 cursor-pointer" />
        </div>
      </div>

      {monthlyDist.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <div className="flex-1 flex flex-col gap-1.5 justify-center py-1 relative">
          {/* Vertical Trend indicator line at 300 mark */}
          <div className="absolute inset-0 grid grid-cols-12 gap-3 pointer-events-none z-10">
            <div className="col-span-1" />
            <div className="col-span-11 relative h-full">
              <div className="absolute top-0 bottom-0 left-[60%] border-r border-dashed border-amber-500/55 flex flex-col justify-between items-center">
                <span className="text-[7px] text-amber-400 font-extrabold bg-[#0B0F19] px-1 py-0.5 rounded border border-[#FFA800]/25 shadow-lg select-none -translate-y-1.5">300</span>
                <span className="text-[7px] text-amber-400 font-extrabold bg-[#0B0F19] px-1 py-0.5 rounded border border-[#FFA800]/25 shadow-lg select-none translate-y-1.5">300</span>
              </div>
            </div>
          </div>

          {monthlyDist.map((item, idx) => {
            const totalTickets = (item.blue || 0) + (item.brown || 0);
            const barWidthPct = (totalTickets / maxTickets) * 100;
            const bluePct = totalTickets > 0 ? (item.blue / totalTickets) * 100 : 0;
            const brownPct = totalTickets > 0 ? (item.brown / totalTickets) * 100 : 0;
            return (
              <div
                key={idx}
                className="grid grid-cols-12 gap-3 items-center relative z-0 h-[18px]"
                onMouseEnter={() => setHoveredMonth(item.month)}
                onMouseLeave={() => setHoveredMonth(null)}
              >
                <div className="col-span-1 text-[10px] font-bold text-neutral-300">
                  {item.month}
                </div>

                <div className="col-span-8 relative h-full flex items-center">
                  <div
                    className="bg-[#1A2333]/70 h-3 rounded-full overflow-hidden flex cursor-pointer hover:opacity-85 transition-all"
                    style={{ width: `${barWidthPct}%` }}
                  >
                    <div
                      className="h-full bg-cyan-400"
                      style={{ width: `${bluePct}%`, boxShadow: "0 0 8px rgba(0,229,255,0.6)" }}
                      title={`BLUE: ${item.blue} tickets (${Math.round(bluePct)}%)`}
                    />
                    <div
                      className="h-full bg-pink-500"
                      style={{ width: `${brownPct}%`, boxShadow: "0 0 8px rgba(244,114,182,0.6)" }}
                      title={`BROWN: ${item.brown} tickets (${Math.round(brownPct)}%)`}
                    />
                  </div>
                </div>

                <div className="col-span-3 text-right text-[9px] font-bold text-white font-mono whitespace-nowrap">
                  {totalTickets} tkts : {Math.round(totalTickets / 4)}/wk
                </div>

                {hoveredMonth === item.month && (
                  <div className="absolute left-[50%] bottom-5 w-[195px] p-2 bg-[#131926]/95 border border-cyan-500/55 rounded-lg text-[9px] text-white shadow-xl z-20 pointer-events-none transition-all duration-300">
                    <p className="font-bold text-cyan-400 uppercase tracking-wider">{item.month} Details</p>
                    <p className="text-neutral-300 mt-0.5">
                      <span className="font-bold text-white">{item.blue}</span> BLUE · <span className="font-bold text-pink-400">{item.brown}</span> BROWN
                    </p>
                    <p className="text-neutral-500 mt-1 font-medium border-t border-[#242F41]/65 pt-1">
                      {totalTickets} total · {Math.round(totalTickets / 4)}/wk avg
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </GlassCard>
  );
}

export function TopComplaintCategories({ defaultShowReasons = false, onToggle }: { defaultShowReasons?: boolean; onToggle?: (reasons: boolean) => void }) {
  const issueCats = useLocalStorageData<any[]>("First_Response_Issues", []);
  const reassignmentReasons = useLocalStorageData<any[]>("Reassignment_Reasons", []);
  const [showReasons, setShowReasons] = useState(defaultShowReasons);

  const activeData = showReasons ? reassignmentReasons : issueCats;

  const sortedData = [...activeData].sort((a, b) => {
    const aVal = a.count || parseInt(a.tickets) || 0;
    const bVal = b.count || parseInt(b.tickets) || 0;
    return bVal - aVal;
  });

  const totalCount = sortedData.reduce((acc, it) => acc + (it.count || parseInt(it.tickets) || 0), 0);

  return (
    <GlassCard id="top-complaint-categories-card" className="p-4 flex flex-col justify-between h-[200px]" hover={true}>
      <div className="flex items-center justify-between mb-2 border-b border-[#242F41]/45 pb-1">
        <span className="text-[10px] font-semibold text-neutral-400 tracking-wider uppercase">
          {showReasons ? "Top Reasons" : "Top Issues"}
        </span>
        <div className="flex items-center gap-2">
          {/* Sleek Segment toggle control */}
          <div className="flex items-center bg-[#131926]/90 border border-[#1E3456] rounded-full p-0.5 select-none shrink-0 scale-90 origin-right">
            <button
              onClick={() => {
                setShowReasons(false);
                onToggle?.(false);
              }}
              className={`text-[8px] px-2 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${!showReasons ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
            >
              Issues
            </button>
            <button
              onClick={() => {
                setShowReasons(true);
                onToggle?.(true);
              }}
              className={`text-[8px] px-2 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${showReasons ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
            >
              Reasons
            </button>
          </div>
          <Activity className="h-3 w-3 text-cyan-400 shrink-0" />
        </div>
      </div>
      {sortedData.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <div className="flex-1 overflow-y-auto pr-1.5 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-cyan-500/20 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-cyan-500/40 transition-colors">
          <div className="flex flex-col gap-1.5 py-1">
            {sortedData.map((it, idx) => {
              const count = it.count || parseInt(it.tickets) || 0;
              const share = it.share || 0;
              return (
                <div key={idx} className="space-y-0.5">
                  <div className="flex justify-between items-center text-[9px] gap-2">
                    <span className="text-neutral-300 font-medium truncate flex-1" title={it.name}>
                      {it.name}
                    </span>
                    <span className="font-mono text-[9px] text-white font-semibold shrink-0">
                      {share}% ({count})
                    </span>
                  </div>
                  
                  <div className="bg-[#1A2333] h-1.5 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full bg-gradient-to-r ${
                        idx === 0 ? "from-[#00F2FE] to-[#00F5A0]" :
                        idx === 1 ? "from-[#4FACFE] to-[#F355DA]" :
                        idx === 2 ? "from-[#F355DA] to-[#FF0844]" :
                        idx === 3 ? "from-[#FF0844] to-[#FFA800]" :
                        "from-[#FFA800] to-[#00F5A0]"
                      }`}
                      style={{ width: `${totalCount > 0 ? (count / totalCount) * 100 : 0}%` }}
                      title={`${share}% (${count} tickets)`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </GlassCard>
  );
}

const vaporKeyframes = `
@keyframes vapor-rise {
  0%   { transform: translate3d(0, 0, 0) scale(1); opacity: 0.7; }
  50%  { transform: translate3d(0, -30px, 0) scale(1.8); opacity: 0.3; }
  100% { transform: translate3d(0, -60px, 0) scale(2.5); opacity: 0; }
}
@keyframes vapor-drift {
  0%   { margin-left: 0; }
  50%  { margin-left: 4px; }
  100% { margin-left: -3px; }
}
`;

function VaporBubbles({ pct, color }: { pct: number; color: string }) {
  const bubbleColors: Record<string, string> = {
    "from-[#FF0844] to-[#00F5A0]": "rgba(0,245,160,0.6)",
    "from-[#4FACFE] to-[#F355DA]": "rgba(79,172,254,0.5)",
    "from-[#FF0844] to-[#FFA800]": "rgba(255,168,0,0.5)",
  };
  const fill = bubbleColors[color] || "rgba(0,245,160,0.5)";

  if (pct < 5) return null;
  const count = Math.min(5, Math.max(2, Math.floor(pct / 20)));

  return (
    <>
      <style>{vaporKeyframes}</style>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="absolute rounded-full pointer-events-none"
          style={{
            width: `${4 + i * 2}px`,
            height: `${4 + i * 2}px`,
            background: fill,
            bottom: `${pct + 2}%`,
            left: `${30 + i * 12}%`,
            animation: `vapor-rise ${1.5 + i * 0.3}s ease-out infinite`,
            animationDelay: `${i * 0.4}s`,
            willChange: "transform",
            transform: "translate3d(0, 0, 0)",
            backfaceVisibility: "hidden"
          }}
        />
      ))}
    </>
  );
}

export function SloMeterBar() {
  const avgTimes = useLocalStorageData<any[]>("NOC_Queue_Times", []);

  const avgMinutes = avgTimes.length > 0
    ? avgTimes.reduce((acc: number, q: any) => acc + (parseInt(q.avg) || 0), 0) / avgTimes.length
    : 0;

  const slaMax = 120;
  const usedPct = Math.min(100, Math.round((avgMinutes / slaMax) * 100));
  const achievedPct = avgMinutes <= slaMax ? 100 : Math.round((slaMax / avgMinutes) * 100);

  const barColor = "from-[#00F5A0] to-[#FF0844]";

  const label = achievedPct >= 100 ? "On Track" : achievedPct >= 80 ? "At Risk" : "Critical";

  return (
    <GlassCard id="slo-meter-card" className="p-4 flex flex-col justify-between h-[200px] group" hover={true}>
      <style>{vaporKeyframes}</style>
      <div className="flex items-center justify-center mb-1 shrink-0 gap-1">
        <Gauge className="h-3 w-3 text-cyan-400" />
        <span className="text-[9px] font-semibold text-neutral-400 tracking-wider uppercase">SLA</span>
      </div>
      <div className="flex-1 flex items-end justify-center pb-1 relative">
        <div className="relative w-8 bg-[#1A2333] rounded-full h-full flex flex-col items-center justify-end cursor-help">
          <div
            className={`absolute bottom-0 w-full rounded-full bg-gradient-to-t ${barColor} transition-all duration-500`}
            style={{ height: `${usedPct}%` }}
          />
          <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
            <span className="text-[10px] font-extrabold text-white leading-none">{avgMinutes.toFixed(0)}</span>
            <span className="text-[6px] text-white uppercase tracking-wider">mins</span>
            <span className="text-[7px] font-bold text-white mt-0.5">{(avgMinutes / 60).toFixed(1)}h</span>
          </div>
          <VaporBubbles pct={usedPct} color={barColor} />
        </div>

        {/* Hover tooltip: queue-by-queue breakdown */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 w-52 p-2.5 rounded-lg bg-[#131926]/95 border border-cyan-500/40 text-neutral-200 text-[8px] leading-relaxed shadow-2xl opacity-0 scale-95 pointer-events-none group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 z-50">
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2 h-2 rotate-45 bg-[#131926] border-l border-t border-cyan-500/40" />
          <div className="font-extrabold text-white mb-1.5 border-b border-neutral-700/40 pb-1 text-[9px] text-center">Queue SLA Breakdown</div>
          {avgTimes.map((q: any, i: number) => {
            const avgMin = parseInt(q.avg) || 0;
            const overSla = avgMin > 120;
            return (
              <div key={i} className="flex items-center justify-between py-0.5">
                <span className="text-neutral-300 font-medium truncate w-[90px]">{q.name}</span>
                <span className={`font-mono font-bold ${overSla ? "text-red-400" : "text-emerald-400"}`}>
                  {q.avg}
                </span>
                <span className={`font-mono ${(q.compliance || 0) < 75 ? "text-amber-400" : "text-neutral-400"}`}>
                  {q.compliance}%
                </span>
              </div>
            );
          })}
          <div className="mt-1.5 pt-1 border-t border-neutral-700/40 flex justify-between text-[7px] text-neutral-500">
            <span>SLA Target: 2 hrs</span>
            <span className="font-bold text-white">Avg: {(avgMinutes / 60).toFixed(1)}h</span>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-center text-[7px] text-neutral-500 border-t border-[#242F41]/35 pt-1 shrink-0 gap-2">
        <span className={achievedPct >= 100 ? "text-cyan-400 font-bold" : "text-neutral-500"}>{achievedPct}% achieved</span>
        <span className={`font-bold ${
          achievedPct >= 100 ? "text-cyan-400" : achievedPct >= 80 ? "text-amber-400" : "text-red-400"
        }`}>{label}</span>
      </div>
    </GlassCard>
  );
}
