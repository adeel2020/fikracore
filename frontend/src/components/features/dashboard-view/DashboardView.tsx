"use client";

import React from "react";
import {
  BarChart,
  Bar,
  Cell,
  LineChart,
  Line,
  PieChart,
  Pie,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Bot,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { CHART_COLORS } from "@/lib/chart-colors";

import {
  sparklineData,
  toolVolumeData,
  taskSuccessData,
  collabWavesData,
  agentSpecializationData,
  projectCostData,
} from "./types/dashboard.types";

import { MiniSparkline } from "./components/charts/MiniSparkline";
import { LatencyBarChart } from "./components/charts/LatencyBarChart";
import { VRAMHeatmap } from "./components/charts/VRAMHeatmap";
import { TaskProgressBar } from "./components/charts/TaskProgressBar";
import { ConcentricRings } from "./components/charts/ConcentricRings";
import { CustomTooltip } from "./components/charts/CustomTooltip";

const iconStroke = { strokeWidth: 1.5 } as const;

// ── Local Presentational Micro-Components ──────────────────────────────────────

const VRAMScale: React.FC = React.memo(() => {
  return (
    <div className="flex flex-col items-center gap-0.5 text-[9px] font-mono text-neutral-500">
      {[80, 60, 40, 20, 0].map((v) => (
        <span key={v} className="leading-none">{v}</span>
      ))}
    </div>
  );
});
VRAMScale.displayName = "VRAMScale";

const AvatarCircles: React.FC = React.memo(() => {
  const colors = [
    CHART_COLORS.neonMagenta,
    CHART_COLORS.neonCyan,
    CHART_COLORS.neonLime,
    CHART_COLORS.neonOrange,
    CHART_COLORS.neonBlue,
  ];
  return (
    <div className="flex -space-x-3">
      {colors.map((c, i) => (
        <div
          key={i}
          className="h-8 w-8 rounded-full border-2 border-black flex items-center justify-center text-[10px] font-bold"
          style={{ backgroundColor: c, color: '#000' }}
        >
          {String.fromCharCode(65 + i)}
        </div>
      ))}
    </div>
  );
});
AvatarCircles.displayName = "AvatarCircles";

const SpeedometerIcon: React.FC = React.memo(() => {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-emerald-400">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" opacity={0.3} />
      <path
        d="M12 12 L12 6"
        stroke={CHART_COLORS.neonGreen}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="12" r="2" fill={CHART_COLORS.neonGreen} />
      <path
        d="M12 4 A8 8 0 0 1 18 18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity={0.2}
      />
    </svg>
  );
});
SpeedometerIcon.displayName = "SpeedometerIcon";

// ── Main Dashboard View Component ─────────────────────────────────────────────

export function DashboardView() {
  return (
    <div className="relative pb-12 space-y-4">
      {/* ── HEADER ── */}
      <GlassCard className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/30 to-purple-600/30 border border-cyan-500/30">
              <Bot className="h-5 w-5 text-cyan-400" {...iconStroke} />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-[0.2em] text-white uppercase">
                Agent Ops
              </h1>
              <p className="text-[10px] text-neutral-500 tracking-wider">
                Global Workload Performance
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-[11px] text-neutral-500">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live</span>
            </div>
            <span className="text-[11px] font-mono text-neutral-500 tracking-wider">
              March 2026
            </span>
          </div>
        </div>
      </GlassCard>

      {/* ── TOP ROW: 4 KPI Cards ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Active Agents */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
                Active Agents
              </p>
              <p
                className="mt-1 text-3xl font-bold text-white"
                style={{ textShadow: `0 0 24px ${CHART_COLORS.neonPurple}60` }}
              >
                73
              </p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-purple-500/20 border border-purple-500/30">
              <Bot className="h-4 w-4 text-purple-400" {...iconStroke} />
            </div>
          </div>
          <div className="mt-2">
            <MiniSparkline data={sparklineData} color={CHART_COLORS.neonPurple} />
          </div>
          <p className="mt-0.5 text-[10px] text-neutral-500 font-mono">
            Feb 23 – Mar 01, 2026
          </p>
        </GlassCard>

        {/* Card 2: Project Rollouts */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
                Use Case Rollouts
              </p>
              <p
                className="mt-1 text-3xl font-bold text-white"
                style={{ textShadow: `0 0 24px ${CHART_COLORS.neonMagenta}60` }}
              >
                36
              </p>
            </div>
            <AvatarCircles />
          </div>
          <p className="mt-3 text-[11px] text-neutral-400">
            Across <span className="text-white font-semibold">12</span> Teams
          </p>
          <p className="mt-0.5 text-[10px] text-neutral-500">
            <span className="text-emerald-400">+8</span> this month
          </p>
        </GlassCard>

        {/* Card 3: Inference Cost Cap */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
                Inference Cost Cap
              </p>
              <p
                className="mt-1 text-3xl font-bold text-white"
                style={{ textShadow: `0 0 24px ${CHART_COLORS.neonCyan}60` }}
              >
                75%
              </p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/20 border border-cyan-500/30">
              <DollarSign className="h-4 w-4 text-cyan-400" {...iconStroke} />
            </div>
          </div>
          <div className="mt-3 space-y-1">
            <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: "75%",
                  background: `linear-gradient(90deg, ${CHART_COLORS.neonCyan}, ${CHART_COLORS.neonMagenta})`,
                  boxShadow: `0 0 12px ${CHART_COLORS.neonCyan}60`,
                }}
              />
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-neutral-500">Daily Cap</span>
              <span className="text-cyan-400 font-semibold">Total $11,250</span>
            </div>
          </div>
        </GlassCard>

        {/* Card 4: Avg Latency */}
        <GlassCard className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500">
                Avg Latency
              </p>
              <p
                className="mt-1 text-3xl font-bold text-white"
                style={{ textShadow: `0 0 24px ${CHART_COLORS.neonGreen}60` }}
              >
                2,985
              </p>
            </div>
            <SpeedometerIcon />
          </div>
          <div className="mt-2">
            <LatencyBarChart />
          </div>
          <p className="mt-0.5 text-[10px] text-neutral-500">
            <span className="text-amber-400 font-medium">p95</span> Latency{" "}
            <span className="text-white">4,120ms</span>
          </p>
        </GlassCard>
      </div>

      {/* ── MIDDLE ROW: 4 Columns ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Column 1: VRAM */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-3">
            VRAM Utilization
          </p>
          <p className="text-xs text-neutral-400 mb-2">
            50% of <span className="text-white">80GB</span> Allocated
          </p>
          <div className="flex gap-2">
            <VRAMScale />
            <div className="flex-1">
              <VRAMHeatmap />
            </div>
          </div>
        </GlassCard>

        {/* Column 2: Tool Volume */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Tool Volume
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-3">February 1 – 28</p>
          <p className="text-2xl font-bold text-white">2,936</p>
          <p className="text-[11px] text-neutral-400 mb-1">Tool Invocations per month</p>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
            <TrendingUp className="h-3 w-3" />
            +24%
          </span>
          <div className="mt-3 h-24">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={toolVolumeData} margin={{ top: 0, right: 0, bottom: 0, left: -10 }}>
                <Bar dataKey="v" fill={CHART_COLORS.electricBlue} opacity={0.7} radius={[2, 2, 0, 0]} />
                <Tooltip content={<CustomTooltip />} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Column 3: Task Success Rate */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Task Success Rate
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-4">March 2026</p>
          <div className="space-y-4">
            {taskSuccessData.map((d) => (
              <TaskProgressBar key={d.name} label={d.name} value={d.value} color={d.color} />
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[10px]">
            <span className="text-neutral-500">Overall</span>
            <span className="text-white font-bold text-sm" style={{ textShadow: `0 0 12px ${CHART_COLORS.neonLime}60` }}>
              91%
            </span>
          </div>
        </GlassCard>

        {/* Column 4: Collaboration Waves */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Collaboration Waves
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-3">March 2026</p>
          <div className="flex gap-4 mb-3">
            <div>
              <p className="text-lg font-bold text-white">1,529</p>
              <p className="text-[10px] text-neutral-400">Collaborators Active</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">763</p>
              <p className="text-[10px] text-neutral-400">Commits / Day</p>
            </div>
          </div>
          <div className="h-20">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={collabWavesData} margin={{ top: 0, right: 0, bottom: 0, left: -10 }}>
                <Line
                  type="monotone"
                  dataKey="collaborators"
                  stroke={CHART_COLORS.neonCyan}
                  strokeWidth={1.5}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="commits"
                  stroke={CHART_COLORS.neonMagenta}
                  strokeWidth={1.5}
                  dot={false}
                />
                <Tooltip content={<CustomTooltip />} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* ── BOTTOM ROW: 3 Analysis Panels ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Panel 1: Agent Specialization Pie */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Agent Specialization
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-2">March 2026</p>
          <div className="flex items-center justify-center h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={agentSpecializationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={2}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {agentSpecializationData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.color}
                      style={{ filter: `drop-shadow(0 0 6px ${entry.color}60)` }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1">
            {agentSpecializationData.map((d) => (
              <div key={d.name} className="flex items-center gap-2 text-[10px]">
                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-neutral-400 truncate">{d.name}</span>
                <span className="text-white font-semibold ml-auto">{d.value}%</span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Panel 2: Context Purity Rings */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Progress
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-2">Context Purity Rings</p>
          <ConcentricRings />
        </GlassCard>

        {/* Panel 3: Project Cost Donut */}
        <GlassCard className="p-4">
          <p className="text-[10px] font-medium uppercase tracking-widest text-neutral-500 mb-1">
            Project Cost Monitor
          </p>
          <p className="text-[10px] text-neutral-500 font-mono mb-2">March 2026</p>
          <div className="flex items-center justify-center h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={projectCostData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={1}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {projectCostData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.color}
                      style={{ filter: `drop-shadow(0 0 6px ${entry.color}60)` }}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Center metric overlay */}
          <div className="text-center -mt-2 mb-2">
            <p className="text-2xl font-bold text-white" style={{ textShadow: `0 0 20px ${CHART_COLORS.neonMagenta}60` }}>
              $362M
            </p>
            <p className="text-[10px] text-neutral-500">Total Compute Cost</p>
          </div>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            {projectCostData.map((d) => (
              <div key={d.name} className="flex items-center gap-2 text-[10px]">
                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-neutral-400 truncate">{d.name}</span>
                <span className="text-white font-semibold ml-auto">{d.value}%</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
