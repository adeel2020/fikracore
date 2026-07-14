"use client";

import React from "react";
import { ArrowLeftRight, AlertOctagon, PieChart as PieIcon, Activity } from "lucide-react";
import { useLocalStorageData } from "@/lib/useLocalStorageData";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ComposedChart,
  XAxis,
  YAxis,
  Bar,
  Line
} from "recharts";
import { GlassCard } from "@/components/ui/glass-card";

const COLORS = {
  cyan: "#00E5FF",
  blue: "#60A5FA",
  pink: "#F472B6",
  magenta: "#FB2B5E",
  amber: "#FBBF24",
  green: "#34D399",
  purple: "#A78BFA",
  gray: "#1E3456"
};

const NOC_COLORS = [
  COLORS.cyan,
  COLORS.blue,
  COLORS.pink,
  COLORS.magenta,
  COLORS.amber,
  COLORS.green,
  COLORS.purple
];

export function TopReassignmentsQueue() {
  const rawData = useLocalStorageData("Reassignments_Rejections", []);

  const reassignments = rawData
    .filter((r: any) => r.Metric_Type === "Reassignment")
    .map((r: any, idx: number) => ({
      name: r.name || r.Name || "",
      value: Number(r.value || r.Tickets_Count || 0),
      color: idx === 0 ? "from-[#4FACFE] to-[#FFA800]" :
             idx === 1 ? "from-[#4FACFE] to-[#F355DA]" :
             idx === 2 ? "from-[#F355DA] to-[#FF0844]" :
             idx === 3 ? "from-[#FF0844] to-[#FFA800]" :
             "from-[#FFA800] to-[#00F5A0]"
    }));

  const totalReassignments = reassignments.reduce((acc: number, curr: any) => acc + curr.value, 0);

  const reassignmentsWithPct = reassignments.map((item: any) => ({
    ...item,
    pct: totalReassignments > 0 ? Math.round((item.value / totalReassignments) * 100) : 0
  }));

  return (
    <GlassCard id="reassignments-card" className="p-4 flex flex-col justify-between h-[200px]" hover={true}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Top Reassignments</span>
        <ArrowLeftRight className="h-4 w-4 text-cyan-400" />
      </div>
      {reassignmentsWithPct.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <div className="flex-1 flex flex-col justify-center gap-1.5">
          {reassignmentsWithPct.map((item, idx) => (
            <div key={idx} className="space-y-0.5">
              <div className="flex justify-between text-[10px] leading-tight">
                <span className="text-neutral-300 font-medium">{item.name}</span>
                <span className="font-semibold text-white">{item.pct}% ({item.value})</span>
              </div>
              <div className="w-full bg-[#1A2333] h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${item.color}`}
                  style={{ width: `${item.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
}

export function TopRejectionReason() {
  const rawData = useLocalStorageData("Reassignments_Rejections", []);
  const [showResolutions, setShowResolutions] = React.useState(false);

  const activeMetricType = showResolutions ? "Resolution_Reason" : "Rejection_Reason";

  const items = rawData
    .filter((r: any) => r.Metric_Type === activeMetricType)
    .map((r: any, idx: number) => ({
      name: r.name || r.Name || "",
      count: Number(r.count || r.value || r.Tickets_Count || 0),
      color: idx === 0 ? "from-[#FFA800] to-[#00F5A0]" :
             idx === 1 ? "from-[#4FACFE] to-[#F355DA]" :
             idx === 2 ? "from-[#F355DA] to-[#FF0844]" :
             idx === 3 ? "from-[#FF0844] to-[#FFA800]" :
             "from-[#FFA800] to-[#00F5A0]"
    }));

  const totalCount = items.reduce((acc: number, curr: any) => acc + curr.count, 0);

  const itemsWithPct = items.map((item: any) => ({
    ...item,
    pct: totalCount > 0 ? Math.round((item.count / totalCount) * 100) : 0
  }));

  return (
    <GlassCard id="rejection-reason-card" className="p-4 flex flex-col justify-between h-[200px]" hover={true}>
      <div className="flex items-center justify-between mb-2 border-b border-[#242F41]/45 pb-1">
        <span className="text-[10px] font-semibold text-neutral-400 tracking-wider uppercase">
          {showResolutions ? "Top Resolution" : "Top Rejection"}
        </span>
        <div className="flex items-center gap-2">
          {/* Sleek Segment toggle control */}
          <div className="flex items-center bg-[#131926]/90 border border-[#1E3456] rounded-full p-0.5 select-none shrink-0 scale-90 origin-right">
            <button
              onClick={() => setShowResolutions(false)}
              className={`text-[8px] px-2 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${!showResolutions ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
            >
              Reject
            </button>
            <button
              onClick={() => setShowResolutions(true)}
              className={`text-[8px] px-2 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${showResolutions ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
            >
              Resolve
            </button>
          </div>
          <AlertOctagon className="h-3 w-3 text-pink-500 shrink-0" />
        </div>
      </div>
      {itemsWithPct.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <div className="flex-1 flex flex-col justify-center gap-1.5">
          {itemsWithPct.map((item, idx) => (
            <div key={idx} className="space-y-0.5">
              <div className="flex justify-between text-[10px] leading-tight">
                <span className="text-neutral-300 font-medium truncate w-[100px]">{item.name}</span>
                <span className="text-[9px] text-neutral-400 font-mono">{item.pct}% ({item.count})</span>
              </div>
              <div className="w-full bg-[#1A2333] h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${item.color}`}
                  style={{ width: `${item.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
}

export function PercentageNocTickets() {
  const rawData = useLocalStorageData("NOC_Tickets_Distribution", []);

  const formattedData = rawData.map((r: any) => ({
    name: r.Queue || r.name || "",
    value: Number(r.Value || r.value || 0),
    pct: Number(r.Percentage || r.pct || 0)
  }));

  const totalTickets = formattedData.reduce((acc, curr) => acc + curr.value, 0);

  const dataWithPct = formattedData.map(r => ({
    ...r,
    pct: r.pct || (totalTickets > 0 ? Math.round((r.value / totalTickets) * 100) : 0)
  }));

  return (
    <GlassCard id="noc-tickets-card" className="p-4 flex flex-col justify-between h-[200px]" hover={false}>
      <style>{`
        @keyframes pulse60 { 
          from { transform: rotate(0deg) translate3d(0,0,0); }
          to { transform: rotate(360deg) translate3d(0,0,0); } 
        } 
        .wheel-wrapper:hover .wheel-spin { 
          animation-play-state: paused; 
        }
        .wheel-spin {
          will-change: transform;
          transform: rotate(0deg) translate3d(0,0,0);
          backface-visibility: hidden;
        }
      `}</style>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-white tracking-wider uppercase">NOC Ticket Share</span>
        <PieIcon className="h-4 w-4 text-cyan-400" />
      </div>
      {dataWithPct.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
          <div className="flex-1 flex items-center justify-between gap-0 overflow-hidden">
          <div className="w-[130px] h-[130px] shrink-0 relative wheel-wrapper -ml-2">
            <div className="wheel-spin" style={{ animation: "pulse60 32s linear infinite" }}>
            <PieChart width={130} height={130}>
              <Pie
                data={[...dataWithPct].reverse()}
                innerRadius={38}
                outerRadius={55}
                paddingAngle={2}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
                isAnimationActive={false}
              >
                {[...dataWithPct].reverse().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={NOC_COLORS[index % NOC_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
            </div>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-base font-bold leading-none text-white">{totalTickets}</span>
              <span className="text-[7px] text-neutral-500 uppercase mt-0.5 font-semibold">Tickets</span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto max-h-[150px] custom-scrollbar pl-0.5 pr-0.5 py-0.5 flex flex-col gap-0.5 text-[8px]">
            {dataWithPct.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between gap-0.5">
                <div className="flex items-center gap-1 truncate">
                  <div
                    className="w-1 h-1 rounded-full shrink-0"
                    style={{ backgroundColor: NOC_COLORS[idx % NOC_COLORS.length] }}
                  />
                  <span className="text-neutral-300 font-semibold truncate">{item.name}</span>
                </div>
                <span className="font-mono text-neutral-400 shrink-0">{item.pct}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassCard>
  );
}

export function TroubleTicketsHandled30Days() {
  const data = useLocalStorageData("Trouble_Tickets_30d", []);

  const formattedData = data.map((r: any) => ({
    date: r.Date || r.date || "",
    resolved: Number(r.Resolved || r.resolved || 0),
    reassigned: Number(r.Reassigned || r.reassigned || 0),
    rejected: Number(r.Rejected || r.rejected || 0),
    rate: Number(r.SLA_Compliance_Rate_Pct || r.rate || 0)
  }));

  return (
    <GlassCard id="trouble-tickets-card" className="p-4 flex flex-col justify-between h-[350px]" hover={true}>
      <div className="flex items-center justify-between mb-3 border-b border-[#242F41]/45 pb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-neutral-400 tracking-wider uppercase">Trouble Tickets Handled (30 Days)</span>
          <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-[8px] text-cyan-400 border border-cyan-500/30 uppercase tracking-wider font-bold">NOC Queues</span>
        </div>
        <Activity className="h-4 w-4 text-cyan-400" />
      </div>
      {formattedData.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-[10px] text-neutral-500">No data uploaded</div>
      ) : (
        <>
          <div className="flex-1 w-full min-h-[160px] mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={formattedData} margin={{ top: 5, right: -5, left: -20, bottom: 5 }}>
                <XAxis dataKey="date" stroke="#4b5563" fontSize={7} tickLine={false} angle={-45} textAnchor="end" height={50} interval={0} />
                <YAxis yAxisId="left" stroke="#4b5563" fontSize={8} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke="#4b5563" fontSize={8} tickLine={false} domain={[80, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "rgba(19, 25, 38, 0.95)",
                    borderColor: "#242F41",
                    borderRadius: "8px",
                    fontSize: "10px",
                    color: "white"
                  }}
                />
                <Bar yAxisId="left" dataKey="resolved" stackId="tt" fill={COLORS.cyan} name="Resolved" barSize={8} radius={[0, 0, 0, 0]} isAnimationActive={false} />
                <Bar yAxisId="left" dataKey="reassigned" stackId="tt" fill={COLORS.amber} name="Reassigned" barSize={8} radius={[0, 0, 0, 0]} isAnimationActive={false} />
                <Bar yAxisId="left" dataKey="rejected" stackId="tt" fill={COLORS.magenta} name="Rejected" barSize={8} radius={[2, 2, 0, 0]} isAnimationActive={false} />
                <Line yAxisId="right" type="monotone" dataKey="rate" stroke="white" strokeWidth={2} name="SLA %" dot={{ r: 2 }} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center items-center gap-4 text-[9px] border-t border-[#242F41]/45 pt-2">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-[#00F2FE]" />
              <span className="text-neutral-400">Resolved</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-[#FFA800]" />
              <span className="text-neutral-400">Reassigned</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-[#FF0844]" />
              <span className="text-neutral-400">Rejected</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-white" />
              <span className="text-neutral-400">SLA %</span>
            </div>
          </div>
        </>
      )}
    </GlassCard>
  );
}
