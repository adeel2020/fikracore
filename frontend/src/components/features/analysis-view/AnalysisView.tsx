"use client";

import React from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { useAnalysis, CrosstabData, HeatmapCell } from "./useAnalysis";
import {
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  LabelList
} from "recharts";
import { TrendingUp, Activity, AlertCircle } from "lucide-react";

const CustomTooltip = ({ active, payload, activeKeys = [], colors = [] }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const stdDevVal = data.stdDevUpper - data.mean;
    return (
      <div className="bg-[#131926]/95 border border-[#1E3456] rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs text-white max-w-[240px]">
        <div className="font-semibold text-neutral-300 border-b border-neutral-700/60 pb-1.5 mb-2 text-[13px]">
          {data.month} Ticket Trend
        </div>
        <div className="space-y-1.5">
          <div className="flex justify-between gap-4">
            <span className="text-neutral-400 font-semibold">Total Tickets:</span>
            <span className="font-bold text-cyan-400">{data.count}</span>
          </div>
          <div className="flex justify-between gap-4 text-[10px]">
            <span className="text-neutral-400">Mean (μ):</span>
            <span className="font-semibold text-emerald-400">{data.mean}</span>
          </div>
          <div className="flex justify-between gap-4 text-[10px]">
            <span className="text-neutral-400">StdDev (σ):</span>
            <span className="font-semibold text-purple-400">±{stdDevVal.toFixed(1)}</span>
          </div>
          
          {/* Active Category Breakdown */}
          {activeKeys.length > 0 && (
            <div className="border-t border-neutral-800/80 pt-1.5 mt-1.5 space-y-1">
              <div className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider mb-1">
                Category Breakdown (Pins)
              </div>
              {activeKeys.map((key: string, idx: number) => (
                <div key={key} className="flex justify-between gap-4 text-[10px]">
                  <span className="text-neutral-400 flex items-center gap-1.5 truncate max-w-[130px]" title={key}>
                    <span
                      className="inline-block w-1.5 h-1.5 rounded-sm shrink-0"
                      style={{ backgroundColor: colors[idx] }}
                    />
                    {key}:
                  </span>
                  <span className="font-medium text-neutral-200">{data[key] || 0}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-between gap-4 pt-1.5 border-t border-neutral-800/80 mt-1.5 text-[10px]">
            <span className="text-neutral-400">Deviation:</span>
            <span className={`font-semibold ${Number(data.deviation) >= 0 ? "text-rose-400" : "text-cyan-400"}`}>
              {data.deviation}
            </span>
          </div>
          <div className="flex justify-between gap-4 text-[10px]">
            <span className="text-neutral-400">Z-Score:</span>
            <span className={`font-bold px-1 rounded text-[9px] ${Math.abs(Number(data.zScore)) > 1.0 ? "bg-rose-500/20 text-rose-300" : "bg-neutral-800 text-neutral-300"}`}>
              {data.zScore}
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

const CustomDeltaTooltip = ({ active, payload, activeKeys = [], colors = [] }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#131926]/95 border border-[#1E3456] rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs text-white max-w-[280px]">
        <div className="font-semibold text-neutral-300 border-b border-neutral-700/60 pb-1.5 mb-2 text-[11px] uppercase tracking-wider">
          {data.month} MoM Deltas
        </div>
        <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
          {activeKeys.map((key: string, idx: number) => {
            const deltaVal = data[`${key}_deltaAbs`] || 0;
            const deltaPct = data[`${key}_deltaPct`] || 0;
            const count = data[key] || 0;
            const isPositive = deltaVal > 0;
            const isNegative = deltaVal < 0;

            let changeText = "0 (0%)";
            let colorClass = "text-neutral-400";
            if (isPositive) {
              changeText = `+${deltaVal} (+${deltaPct}%)`;
              colorClass = "text-rose-400";
            } else if (isNegative) {
              changeText = `${deltaVal} (${deltaPct}%)`;
              colorClass = "text-emerald-400";
            }

            return (
              <div key={key} className="space-y-0.5 border-b border-neutral-800/40 pb-1 last:border-b-0 last:pb-0">
                <div className="flex items-center gap-1.5 text-[10px] font-bold text-neutral-300 truncate" title={key}>
                  <span className="w-1.5 h-1.5 rounded-sm shrink-0" style={{ backgroundColor: colors[idx] }} />
                  {key}
                </div>
                <div className="flex justify-between text-[9px] text-neutral-400 pl-3">
                  <span>Count: <strong className="text-neutral-200">{count}</strong></span>
                  <span className={colorClass}>{changeText}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

interface MonthlyTrendChartProps {
  monthlyTrendData: { month: string; count: number; [key: string]: any }[];
  mean: number;
  stdDev: number;
  loading: boolean;
  topIssuesList: string[];
  topReasonsList: string[];
}

const MonthlyTrendChart = React.memo(function MonthlyTrendChart({
  monthlyTrendData,
  mean,
  stdDev,
  loading,
  topIssuesList,
  topReasonsList
}: MonthlyTrendChartProps) {
  const [showReasonDeltas, setShowReasonDeltas] = React.useState(false);

  const activeKeys = showReasonDeltas ? topReasonsList : topIssuesList;
  const colors = ["#06b6d4", "#f59e0b", "#8b5cf6", "#ec4899", "#3b82f6"];

  const chartData = React.useMemo(() => {
    return monthlyTrendData.map((d) => {
      const dev = d.count - mean;
      const z = stdDev > 0 ? dev / stdDev : 0;
      const point: any = {
        month: d.month,
        count: d.count,
        mean: Math.round(mean * 10) / 10,
        stdDevUpper: Math.round((mean + stdDev) * 10) / 10,
        stdDevLower: Math.max(0, Math.round((mean - stdDev) * 10) / 10),
        zScore: z.toFixed(2),
        deviation: dev > 0 ? `+${dev.toFixed(1)}` : dev.toFixed(1)
      };

      // Copy dynamic properties (e.g. counts and deltas)
      Object.keys(d).forEach(k => {
        if (k !== "month" && k !== "count") {
          point[k] = d[k];
        }
      });

      return point;
    });
  }, [monthlyTrendData, mean, stdDev]);

  const mappedData = React.useMemo(() => {
    return chartData.map(d => {
      const point = { ...d };
      activeKeys.forEach(key => {
        const deltaVal = d[`${key}_deltaAbs`] || 0;
        const deltaPct = d[`${key}_deltaPct`] || 0;
        const isPositive = deltaVal > 0;
        const isNegative = deltaVal < 0;

        let labelText = "";
        if (isPositive) {
          labelText = `+${deltaVal} (+${deltaPct}%)`;
        } else if (isNegative) {
          labelText = `${deltaVal} (${deltaPct}%)`;
        } else {
          labelText = "0 (0%)";
        }
        point[`${key}_labelText`] = labelText;
      });
      return point;
    });
  }, [chartData, activeKeys]);

  if (loading) {
    return (
      <div className="h-[280px] flex items-center justify-center text-neutral-400">
        Analyzing statistical trends...
      </div>
    );
  }

  const cv = mean > 0 ? (stdDev / mean) * 100 : 0;
  let volatilityLabel = "Low";
  let volatilityColor = "bg-emerald-500/20 text-emerald-400 border-emerald-500/35";
  if (cv >= 30) {
    volatilityLabel = "High";
    volatilityColor = "bg-rose-500/20 text-rose-400 border-rose-500/35";
  } else if (cv >= 15) {
    volatilityLabel = "Moderate";
    volatilityColor = "bg-amber-500/20 text-amber-400 border-amber-500/35";
  }

  const normalRangeText = `${Math.max(0, Math.round(mean - stdDev))} - ${Math.round(mean + stdDev)}`;

  const renderCustomBarLabel = (props: any) => {
    const { x, y, width, value } = props;
    if (!value || value === "0 (0%)" || value === "0") return null;
    
    const isNegative = String(value).includes("-");
    const labelColor = isNegative ? "#00E5A3" : "#E040FB"; // green for reduction, magenta for increase
    
    const angle = isNegative ? 45 : -45;
    const yOffset = isNegative ? y + 8 : y - 6;

    return (
      <text
        x={x + width / 2}
        y={yOffset}
        fill={labelColor}
        fontSize={7}
        fontWeight="bold"
        textAnchor="start"
        transform={`rotate(${angle}, ${x + width / 2}, ${yOffset})`}
      >
        {value}
      </text>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 items-stretch w-full">
      {/* Statistical Dashboard / Chart Area */}
      <div className="flex-1 min-w-0 flex flex-col justify-between">
        <div>
          <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-[#00E5A3]" />
              <span className="text-sm font-bold tracking-wider text-neutral-200 uppercase">
                Ticket Volume Monthly Trend & MoM Change
              </span>
            </div>
            
            <div className="flex flex-wrap items-center gap-4">
              {/* Sleek Segment toggle control */}
              <div className="flex items-center bg-[#131926]/90 border border-[#1E3456] rounded-full p-0.5 select-none shrink-0 scale-90 origin-right">
                <button
                  onClick={() => setShowReasonDeltas(false)}
                  className={`text-[8px] px-2.5 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${!showReasonDeltas ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
                >
                  Top Issues
                </button>
                <button
                  onClick={() => setShowReasonDeltas(true)}
                  className={`text-[8px] px-2.5 py-0.5 rounded-full transition-all uppercase tracking-wider font-bold ${showReasonDeltas ? "bg-cyan-500 text-neutral-900 shadow-sm" : "text-neutral-400 hover:text-neutral-200"}`}
                >
                  Reassignment Reason
                </button>
              </div>

              {/* Custom Legends */}
              <div className="text-[9px] text-neutral-400 flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-1">
                  <span className="inline-block w-2.5 h-1.5 bg-[#10b981] rounded-sm" />
                  <span>Mean (μ)</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block w-2.5 h-2 bg-[#8b5cf6]/30 rounded-sm" />
                  <span>1σ SD Band</span>
                </div>
                {activeKeys.map((key, idx) => (
                  <div key={key} className="flex items-center gap-1 border-l border-neutral-700/60 pl-2">
                    <span
                      className="inline-block w-1.5 h-1.5 rounded-sm"
                      style={{ backgroundColor: colors[idx] }}
                    />
                    <span>{key}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Main Trend Line Chart */}
          <div className="h-[210px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={mappedData}
                syncId="trend_sync"
                margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00E5A3" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#00E5A3" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorSd" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.08} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.01} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E3456" opacity={0.2} />
                <XAxis
                  dataKey="month"
                  tick={false}
                  axisLine={{ stroke: "#1E3456" }}
                />
                <YAxis
                  stroke="#9ca3af"
                  fontSize={10}
                  tickLine={false}
                  axisLine={{ stroke: "#1E3456" }}
                />
                <Tooltip content={<CustomTooltip activeKeys={activeKeys} colors={colors} />} />
                
                <Area
                  name="Normal Range (±1 SD)"
                  type="monotone"
                  dataKey={["stdDevLower", "stdDevUpper"] as any}
                  stroke="none"
                  fill="url(#colorSd)"
                  isAnimationActive={false}
                />
                
                <ReferenceLine
                  y={mean + stdDev}
                  stroke="#8b5cf6"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                  label={{
                    value: `+1 SD (${Math.round(mean + stdDev)})`,
                    fill: "#a78bfa",
                    fontSize: 9,
                    position: "insideBottomRight",
                    offset: 8
                  }}
                />
                <ReferenceLine
                  y={Math.max(0, mean - stdDev)}
                  stroke="#8b5cf6"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                  label={{
                    value: `-1 SD (${Math.max(0, Math.round(mean - stdDev))})`,
                    fill: "#a78bfa",
                    fontSize: 9,
                    position: "insideTopRight",
                    offset: 8
                  }}
                />
                <ReferenceLine
                  y={mean}
                  stroke="#10b981"
                  strokeWidth={1.5}
                  label={{
                    value: `Mean (μ = ${Math.round(mean)})`,
                    fill: "#34d399",
                    fontSize: 10,
                    position: "insideTopLeft",
                    offset: 5
                  }}
                />
                
                {/* Dynamic Category Pins */}
                {activeKeys.map((key, idx) => (
                  <Bar
                    key={key}
                    dataKey={key}
                    barSize={3}
                    fill={colors[idx]}
                    radius={[1.5, 1.5, 0, 0]}
                    opacity={0.85}
                  />
                ))}

                <Area
                  name="Actual Count"
                  type="monotone"
                  dataKey="count"
                  stroke="#00E5A3"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorCount)"
                  activeDot={{ r: 6, strokeWidth: 0, fill: "#00E5A3" }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Separator and label for delta change chart */}
        <div className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider mt-3 mb-1 border-t border-[#1E3456]/40 pt-2 flex items-center justify-between">
          <span>MoM Performance Deltas ({showReasonDeltas ? "Reassignment Reasons" : "Top Issues"})</span>
          <span className="text-[8px] font-normal text-neutral-500 normal-case">Magenta = Increase (Unfavorable) · Green = Decrease (Favorable)</span>
        </div>

        {/* Bottom Delta Change Chart */}
        <div className="h-[180px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={mappedData}
              syncId="trend_sync"
              margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1E3456" opacity={0.15} />
              <XAxis
                dataKey="month"
                stroke="#9ca3af"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: "#1E3456" }}
              />
              <YAxis
                stroke="#9ca3af"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: "#1E3456" }}
              />
              <Tooltip content={<CustomDeltaTooltip activeKeys={activeKeys} colors={colors} />} />
              
              {/* Baseline Axis y=0 */}
              <ReferenceLine y={0} stroke="#1E3456" strokeWidth={1.5} />
              
              {/* Dynamic Grouped Delta Bars */}
              {activeKeys.map((key, idx) => (
                <Bar key={key} dataKey={`${key}_deltaAbs`} barSize={8}>
                  {mappedData.map((entry, index) => {
                    const deltaVal = entry[`${key}_deltaAbs`] || 0;
                    const isPositive = deltaVal > 0;
                    return (
                      <Cell
                        key={`cell-${index}-${idx}`}
                        fill={isPositive ? "#E040FB" : "#00E5A3"} // Magenta for increase, Green for decrease
                      />
                    );
                  })}
                  <LabelList dataKey={`${key}_labelText`} content={renderCustomBarLabel} />
                </Bar>
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Statistical Sidebar Panel */}
      <div className="w-full lg:w-[260px] flex flex-col gap-4 border-t lg:border-t-0 lg:border-l border-[#1E3456]/50 pt-4 lg:pt-0 lg:pl-6 shrink-0 justify-between">
        <div>
          <h4 className="text-xs font-semibold tracking-wider text-neutral-400 uppercase mb-3 flex items-center gap-1.5">
            <Activity className="h-4.5 w-4.5 text-cyan-400" />
            Statistical Analysis
          </h4>
          <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
            <div className="bg-white/[0.03] border border-[#1E3456]/40 rounded-xl p-3">
              <span className="block text-[10px] text-neutral-400 font-medium">Monthly Mean (μ)</span>
              <span className="text-lg font-bold text-emerald-400">{Math.round(mean)} <span className="text-xs font-normal text-neutral-400">tickets</span></span>
            </div>
            <div className="bg-white/[0.03] border border-[#1E3456]/40 rounded-xl p-3">
              <span className="block text-[10px] text-neutral-400 font-medium">Std Deviation (σ)</span>
              <span className="text-lg font-bold text-purple-400">±{stdDev.toFixed(1)}</span>
            </div>
            <div className="bg-white/[0.03] border border-[#1E3456]/40 rounded-xl p-3">
              <span className="block text-[10px] text-neutral-400 font-medium">Normal Range (1σ)</span>
              <span className="text-base font-bold text-neutral-200">{normalRangeText}</span>
            </div>
            <div className="bg-white/[0.03] border border-[#1E3456]/40 rounded-xl p-3">
              <span className="block text-[10px] text-neutral-400 font-medium">Volatility (CV)</span>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-base font-bold text-neutral-200">{cv.toFixed(1)}%</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${volatilityColor}`}>
                  {volatilityLabel}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-[#8b5cf6]/5 border border-[#8b5cf6]/20 rounded-xl p-3 text-[10px] text-neutral-400 leading-relaxed mt-4 lg:mt-0 flex gap-2 items-start">
          <AlertCircle className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" />
          <div>
            The sleek vertical bars (pins) at the bottom show category peaks. Standard deviation bands analyze abnormal ticket surges or reductions.
          </div>
        </div>
      </div>
    </div>
  );
});

type NormType = "maxVal" | "quadratic" | "logMinMax" | "minMax";

function crosstabPct(intensity: number, values: HeatmapCell[], norm: NormType): number {
  const maxVal = Math.max(...values.map(v => v.value), 0.1);
  const minVal = Math.min(...values.map(v => v.value), 0);
  switch (norm) {
    case "maxVal":
      return (intensity / maxVal) * 100;
    case "quadratic":
      return Math.pow(intensity / maxVal, 2) * 100;
    case "logMinMax": {
      const logVals = values.map(v => Math.log(v.value + 1));
      const minLog = Math.min(...logVals);
      const range = Math.max(...logVals) - minLog || 1;
      return ((Math.log(intensity + 1) - minLog) / range) * 100;
    }
    case "minMax": {
      const range = maxVal - minVal || 1;
      return ((intensity - minVal) / range) * 100;
    }
  }
}

function CrosstabHeatmap({ data, title, norm }: { data: CrosstabData; title: string; norm: NormType }) {
  const { rowLabels, colLabels, values } = data;

  if (rowLabels.length === 0 || colLabels.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-neutral-500">
        No data available
      </div>
    );
  }

  return (
    <div>
      <div className="flex gap-2">
        <div className="flex flex-col justify-end">
          <div className="h-8 w-24" />
          {rowLabels.map((label, i) => (
            <div
              key={`row-label-${i}`}
              className="flex items-center justify-end h-20 w-24 pr-2 text-xs text-neutral-400 font-medium"
            >
              <span className="truncate">{label}</span>
            </div>
          ))}
        </div>

        <div>
          <div className="flex gap-2 mb-2">
            {colLabels.map((label, j) => (
              <div
                key={`col-label-${j}`}
                className="flex items-center justify-center h-8 w-20 text-xs text-neutral-400 font-medium"
              >
                <span className="truncate">{label}</span>
              </div>
            ))}
          </div>

          <div className="flex flex-col gap-2">
            {Array.from({ length: rowLabels.length }).map((_, rowIdx) => (
              <div key={`row-${rowIdx}`} className="flex gap-2">
                {values
                  .filter((cell) => cell.row === rowIdx)
                  .sort((a, b) => a.col - b.col)
                  .map((cell) => {
                    const intensity = cell.value;
                    const pct = crosstabPct(intensity, values, norm);
                    const hue = pct <= 10 ? 50 : 50 + ((pct - 10) / 90) * 250;
                    const textColor = pct > 55 ? "text-white" : "text-neutral-900";
                    return (
                      <div
                        key={`cell-${cell.row}-${cell.col}`}
                        className="group relative"
                        title={`${rowLabels[cell.row]} → ${colLabels[cell.col]}: ${cell.count} tickets (${cell.value}%)`}
                      >
                        <div
                          className={`aspect-square w-20 h-20 rounded-md transition-transform hover:scale-110 cursor-pointer flex items-center justify-center ${textColor} text-[10px] font-bold`}
                          style={{
                            background: `hsla(${hue}, 85%, 55%, 0.9)`,
                            boxShadow: `0 0 ${Math.max(12, pct / 3)}px hsla(${hue}, 90%, 60%, 0.7)`,
                          }}
                        >
                          {(cell.value / 100).toFixed(2)}
                        </div>
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-black/80 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                          {(cell.value / 100).toFixed(2)} ({cell.count} tickets)
                        </div>
                      </div>
                    );
                  })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const NORM_OPTIONS: { value: NormType; label: string; desc: string }[] = [
  { value: "maxVal", label: "Linear (maxVal)", desc: "True ticket share — e.g. if CS Queue sends 40% of reassignments to a target, that cell shows 0.40. Best to compare absolute dominance across Queues (CS, PS, VAS) and Issues (Data Bundle, MNP, VoLTE, Roaming, eSIM)." },
  { value: "quadratic", label: "Quadratic", desc: "Amplifies the top driver — e.g. if 'Multi SIM not allowed' or 'Bundle not active' is the #1 reassignment reason, it glows hot while smaller reasons fade. Use to spot which Issue or Queue dominates reassignments and rejections." },
  { value: "logMinMax", label: "Log + Min-Max", desc: "Reveals patterns in smaller Queues (e.g. IN, RAN, EI, IREG) or rare Issues without being washed out by giants like CS Queue or Data Bundle. Best when a few categories dominate but you still need to compare the tail." },
  { value: "minMax", label: "Min-Max", desc: "Maximizes contrast between every row and column — e.g. highlights small differences between Rejection Reasons like 'Knowledge Gap (PP)' vs 'Missing Info' vs 'Coverage'. Use when data is tightly clustered." },
];

export function AnalysisView() {
  const { 
    queueVsReassigned, 
    issuesVsReassigned, 
    queueVsIssues, 
    issuesVsReasons,
    monthlyTrendData, 
    mean, 
    stdDev, 
    loading,
    topIssuesList,
    topReasonsList
  } = useAnalysis();
  const [norm, setNorm] = React.useState<NormType>("quadratic");

  return (
    <div className="flex flex-col gap-6 w-full max-w-[1600px] mx-auto p-4">
      {/* Monthly Trend Section on Top */}
      <GlassCard className="p-6 w-full" hover={false}>
        <MonthlyTrendChart
          monthlyTrendData={monthlyTrendData}
          mean={mean}
          stdDev={stdDev}
          loading={loading}
          topIssuesList={topIssuesList || []}
          topReasonsList={topReasonsList || []}
        />
      </GlassCard>

      {/* Heatmaps Section Below */}
      <div className="flex gap-6 items-start">
        <div className="flex flex-wrap gap-6 flex-1">
          <GlassCard className="p-6 w-full lg:w-auto shrink-0" hover={false}>
            <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-neutral-400 text-center">
              TOP ISSUES → Reassigned Queues
            </p>
            {loading ? (
              <div className="flex items-center justify-center py-12 text-neutral-400">
                Loading correlation data...
              </div>
            ) : issuesVsReassigned ? (
              <CrosstabHeatmap data={issuesVsReassigned} title="Issues → Reassignment" norm={norm} />
            ) : (
              <div className="flex items-center justify-center py-12 text-neutral-500">
                No data available
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6 w-full lg:w-auto shrink-0" hover={false}>
            <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-neutral-400 text-center">
              SOC Queues → Reassigned Queues
            </p>
            {loading ? (
              <div className="flex items-center justify-center py-12 text-neutral-400">
                Loading correlation data...
              </div>
            ) : queueVsReassigned ? (
              <CrosstabHeatmap data={queueVsReassigned} title="Queue → Reassignment" norm={norm} />
            ) : (
              <div className="flex items-center justify-center py-12 text-neutral-500">
                No data available
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6 w-full lg:w-auto shrink-0" hover={false}>
            <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-neutral-400 text-center">
              ISSUE VS SOC Queues
            </p>
            {loading ? (
              <div className="flex items-center justify-center py-12 text-neutral-400">
                Loading correlation data...
              </div>
            ) : queueVsIssues ? (
              <CrosstabHeatmap data={queueVsIssues} title="Issue vs Queue" norm={norm} />
            ) : (
              <div className="flex items-center justify-center py-12 text-neutral-500">
                No data available
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6 w-full lg:w-auto shrink-0" hover={false}>
            <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-neutral-400 text-center">
              TOP ISSUE VS REASSIGNMENT REASON
            </p>
            {loading ? (
              <div className="flex items-center justify-center py-12 text-neutral-400">
                Loading correlation data...
              </div>
            ) : issuesVsReasons ? (
              <CrosstabHeatmap data={issuesVsReasons} title="Issues vs Reasons" norm={norm} />
            ) : (
              <div className="flex items-center justify-center py-12 text-neutral-500">
                No data available
              </div>
            )}
          </GlassCard>
        </div>

        {/* Normalization Panel */}
        <GlassCard className="p-4 w-56 shrink-0" hover={false}>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            Normalization
          </p>
          <div className="flex flex-col gap-2">
            {NORM_OPTIONS.map(opt => (
              <div key={opt.value} className="group relative">
                <button
                  onClick={() => setNorm(opt.value)}
                  className={`w-full text-xs text-left px-3 py-2 rounded-lg transition-colors ${
                    norm === opt.value
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-neutral-400 hover:text-neutral-200 hover:bg-white/5 border border-transparent"
                  }`}
                >
                  {opt.label}
                </button>
                <div className="absolute right-full top-0 mr-3 w-56 p-3 bg-[#131926] border border-[#1E3456] rounded-xl text-[10px] text-neutral-300 leading-relaxed shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all pointer-events-none z-20">
                  {opt.desc}
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
