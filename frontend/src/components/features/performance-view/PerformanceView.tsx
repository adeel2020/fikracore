"use client";

import React, { useEffect, useState, createContext, useContext } from "react";
import {
  AreaChart,
  Area,
  YAxis,
  XAxis,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Activity,
  BarChart3,
  Cpu,
  Database,
  Gauge,
  Layers,
  Network,
  Pause,
  Play,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { C, iconStroke } from "./types/telemetry.types";
import {
  getThroughputData,
  getMemSparkData,
  getCacheSparkData,
  getQueryDistData,
} from "./hooks/useChartFormatters";
import { useTelemetryStream, useRealtimeValue } from "./hooks/useTelemetryStream";

import { GlassWidgetCard } from "./components/shared/GlassWidgetCard";
import { ProgressRing } from "./components/charts/ProgressRing";
import { SpeedometerGauge } from "./components/charts/SpeedometerGauge";
import { MiniSparkline } from "./components/charts/MiniSparkline";
import { AIAgencyModule } from "./components/AIAgencyModule";
import { RAGSimilarityModule } from "./components/RAGSimilarityModule";
import { CKGModule } from "./components/CKGModule";

// ─── Animation Context ──────────────────────────────────────────────────────
const AnimationContext = createContext<boolean>(true);

export function useAnimationEnabled(): boolean {
  return useContext(AnimationContext);
}

function AnimationProvider({ children }: { children: React.ReactNode }) {
  const [enabled, setEnabled] = useState(false);
  return (
    <AnimationContext.Provider value={enabled}>
      <div className={enabled ? "" : "animations-paused"}>
        {children}
      </div>
      {/* Animations toggle button — positioned fixed top-right */}
      <button
        onClick={() => setEnabled((prev) => !prev)}
        className="fixed top-4 right-4 z-50 flex items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider backdrop-blur-xl transition-all duration-300 hover:bg-white/[0.12]"
        style={{
          color: enabled ? C.cyan : C.orange,
          boxShadow: enabled
            ? `0 0 12px ${C.cyan}40`
            : `0 0 12px ${C.orange}40`,
        }}
      >
        {enabled ? (
          <>
            <Pause className="h-3 w-3" />
            <span>Pause Animations</span>
          </>
        ) : (
          <>
            <Play className="h-3 w-3" />
            <span>Resume Animations</span>
          </>
        )}
      </button>
    </AnimationContext.Provider>
  );
}

// ─── Brain Icon Glow ────────────────────────────────────────────────────────
const BrainIconGlow: React.FC = React.memo(() => {
  return (
    <div
      className="flex h-10 w-10 items-center justify-center"
      style={{
        filter: `drop-shadow(0 0 6px ${C.pink}) drop-shadow(0 0 12px ${C.purple})`,
      }}
    >
      <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
        <defs>
          <linearGradient id="brain-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={C.pink} />
            <stop offset="100%" stopColor={C.purple} />
          </linearGradient>
        </defs>
        <path
          d="M12 9c-3 0-5 2-5 5 0 1 .3 2 .8 2.7C5.6 17.5 4 19.6 4 22c0 2.5 1.7 4.5 4 4.5-.1.4-.1.8 0 1.2.4 2 2 3.3 4 3.3 1.3 0 2.4-.6 3.2-1.5.7.9 1.8 1.5 3 1.5h.4V8h-.6c-1.4 0-2.6.6-3.4 1.6C14.1 9.2 13.1 9 12 9z"
          fill="url(#brain-grad)"
        />
        <path
          d="M28 9c3 0 5 2 5 5 0 1-.3 2-.8 2.7C34.4 17.5 36 19.6 36 22c0 2.5-1.7 4.5-4 4.5.1.4.1.8 0 1.2-.4 2-2 3.3-4 3.3-1.3 0-2.4-.6-3.2-1.5-.7.9-1.8 1.5-3 1.5h-.4V8h.6c1.4 0 2.6.6 3.4 1.6.5-.4 1.5-.6 2.6-.6z"
          fill="url(#brain-grad)"
        />
        <line
          x1="20"
          y1="8"
          x2="20"
          y2="32"
          stroke="rgba(255,255,255,0.4)"
          strokeWidth="0.6"
        />
      </svg>
    </div>
  );
});
BrainIconGlow.displayName = "BrainIconGlow";

// ─── PERFORMANCE VIEW INNER ──────────────────────────────────────────────────
function PerformanceViewInner() {
  const enabled = useAnimationEnabled();
  
  // Connect to the unified telemetry stream
  const telemetry = useTelemetryStream(enabled);

  // Embedding latency variance, simulated specifically here to map directly to the submodule
  const latency = useRealtimeValue(24, 10, enabled, 1000);

  // Format data using pure helper functions
  const throughputData = getThroughputData(telemetry.throughput);
  const memSparkData = getMemSparkData(telemetry.systemLoad);
  const cacheSparkData = getCacheSparkData(telemetry.systemLoad);
  const queryDistData = getQueryDistData(telemetry.queryPieData, C);

  return (
    <div className="relative pb-10 space-y-4">
      {/* Inject global CSS to pause animations when .animations-paused is present */}
      <style>{`
        .animations-paused *,
        .animations-paused *::before,
        .animations-paused *::after {
          animation-play-state: paused !important;
        }
        .animations-paused * {
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `}</style>
      
      <div className="space-y-4">
        {/* ─── TOP ROW: Performance Rings + Throughput ───────────────────────── */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Performance Ring Panel */}
          <GlassWidgetCard
            title="SYSTEM PERFORMANCE"
            rightSlot={
              <Gauge className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <div className="flex items-center justify-around gap-4">
              <div className="flex flex-col items-center">
                <ProgressRing
                  value={telemetry.systemLoad}
                  color={C.purple}
                  size={140}
                  stroke={11}
                  label="Memory"
                  icon={<Cpu className="h-4 w-4" {...iconStroke} />}
                />
                <div className="mt-2 w-full">
                  <MiniSparkline data={memSparkData} color={C.purple} height={42} />
                </div>
              </div>
              <div className="flex flex-col items-center">
                <ProgressRing
                  value={Math.round(telemetry.systemLoad * 0.6)}
                  color={C.blue}
                  size={140}
                  stroke={11}
                  label="Cache"
                  icon={<Database className="h-4 w-4" {...iconStroke} />}
                />
                <div className="mt-2 w-full">
                  <MiniSparkline data={cacheSparkData} color={C.blue} height={42} />
                </div>
              </div>
            </div>
          </GlassWidgetCard>

          {/* Throughput Panel */}
          <GlassWidgetCard
            title="REQUESTS AND THROUGHPUT"
            rightSlot={
              <TrendingUp className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <div className="flex items-center gap-3">
              <SpeedometerGauge
                value={Math.round(telemetry.throughput * 10) / 10}
                unit="T/s"
                color={C.green}
                size={130}
              />
              <div className="flex-1">
                <div className="text-[10px] text-neutral-400">
                  Throughput History
                </div>
                <ResponsiveContainer width="100%" height={90}>
                  <AreaChart
                    data={throughputData}
                    margin={{ top: 4, right: 0, bottom: 0, left: 0 }}
                  >
                    <defs>
                      <linearGradient id="tp-grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={C.green} stopOpacity={0.6} />
                        <stop offset="100%" stopColor={C.green} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <YAxis hide domain={[0, 50]} />
                    <XAxis dataKey="h" hide />
                    <Area
                      type="monotone"
                      dataKey="v"
                      stroke={C.green}
                      fill="url(#tp-grad)"
                      strokeWidth={1.8}
                      dot={false}
                      style={{
                        filter: `drop-shadow(0 0 4px ${C.green}80)`,
                      }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
                <div className="mt-0.5 flex justify-between text-[9px] font-mono text-neutral-500">
                  <span>24h</span>
                  <span>Throughput History</span>
                  <span>24h</span>
                </div>
              </div>
            </div>
          </GlassWidgetCard>
        </div>

        {/* ─── MIDDLE ROW: 3 Infographic Modules ───────────────────────── */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Module A: AI Agency - Task Completions */}
          <GlassWidgetCard
            title="AI AGENCY - TASK COMPLETIONS"
            rightSlot={
              <Layers className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <AIAgencyModule
              successRate={telemetry.successRate}
              autoRate={telemetry.autoRate}
              humanRate={telemetry.humanRate}
              currentPhase={telemetry.currentPhase}
              tasks={telemetry.tasks}
            />
          </GlassWidgetCard>

          {/* Module B: RAG Similarity Searches */}
          <GlassWidgetCard
            title="RAG SIMILARITY SEARCHES"
            rightSlot={
              <Search className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <RAGSimilarityModule
              vectorData={telemetry.vectorData}
              hit={telemetry.hit}
              miss={telemetry.miss}
              fallback={telemetry.fallback}
              avgScore={telemetry.avgScore}
              latency={latency}
              waveform={telemetry.waveform}
            />
          </GlassWidgetCard>

          {/* Module C: CKG Context Retrievals */}
          <GlassWidgetCard
            title="CKG Context Retrieval Chain"
            rightSlot={
              <Network className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <CKGModule
              graphHops={telemetry.graphHops}
              weightData={telemetry.weightData}
              latencyData={telemetry.contextLatencyData}
              enabled={enabled}
            />
          </GlassWidgetCard>
        </div>

        {/* ─── BOTTOM ROW: 5 small stat cards ────────────────────────────── */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {/* Session Lifespan */}
          <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] text-neutral-300">
                Session Lifespan
              </span>
              <Activity
                className="h-3.5 w-3.5"
                style={{
                  color: C.purple,
                  filter: `drop-shadow(0 0 3px ${C.purple})`,
                }}
                {...iconStroke}
              />
            </div>
            <div className="mt-1 flex items-center gap-2">
              <div
                style={{ filter: `drop-shadow(0 0 4px ${C.purple})` }}
              >
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="9"
                    stroke={C.purple}
                    strokeWidth="1.5"
                  />
                  <path
                    d="M12 7v5l3 2"
                    stroke={C.purple}
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <div
                className="text-lg font-semibold"
                style={{
                  color: C.purple,
                  textShadow: `0 0 8px ${C.purple}80`,
                }}
              >
                {Math.floor(telemetry.sessionTime / 60)}h{" "}
                {Math.round(telemetry.sessionTime % 60)}m
              </div>
            </div>
          </div>

          {/* Active Requests */}
          <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] text-neutral-300">
                Active Requests
              </span>
              <BarChart3
                className="h-3.5 w-3.5"
                style={{
                  color: C.blue,
                  filter: `drop-shadow(0 0 3px ${C.blue})`,
                }}
                {...iconStroke}
              />
            </div>
            <div className="mt-1 flex items-center gap-2">
              <div
                className="flex gap-0.5"
                style={{ filter: `drop-shadow(0 0 3px ${C.blue})` }}
              >
                <span
                  className="h-5 w-1 rounded"
                  style={{ background: C.blue }}
                />
                <span
                  className="h-3.5 w-1 rounded"
                  style={{ background: C.blue, opacity: 0.7 }}
                />
                <span
                  className="h-5 w-1 rounded"
                  style={{ background: C.blue }}
                />
                <span
                  className="h-2.5 w-1 rounded"
                  style={{ background: C.blue, opacity: 0.5 }}
                />
              </div>
              <div
                className="text-lg font-semibold"
                style={{
                  color: C.blue,
                  textShadow: `0 0 8px ${C.blue}80`,
                }}
              >
                {Math.round(telemetry.activeRequests)}
              </div>
            </div>
          </div>

          {/* Model Health */}
          <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] text-neutral-300">
                Model Health
              </span>
              <span
                className="text-[10px] text-neutral-500"
                style={{
                  filter: `drop-shadow(0 0 3px ${C.green})`,
                }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle cx="12" cy="12" r="3" fill={C.green} />
                  <path
                    d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"
                    stroke={C.green}
                    strokeWidth="1.4"
                  />
                </svg>
              </span>
            </div>
            <div className="mt-1 flex items-center gap-2">
              <BrainIconGlow />
              <div
                className="text-sm font-semibold"
                style={{
                  color: C.green,
                  textShadow: `0 0 8px ${C.green}80`,
                }}
              >
                Health Score: {Math.round(telemetry.modelHealth)}/100
              </div>
            </div>
          </div>

          {/* Query Type Distribution */}
          <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] text-neutral-300">
                Query Type Distribution
              </span>
            </div>
            <div className="mt-1 flex items-center gap-3">
              <div className="h-12 w-12 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={queryDistData}
                      cx="50%"
                      cy="50%"
                      innerRadius={14}
                      outerRadius={22}
                      paddingAngle={2}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {queryDistData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={entry.color}
                          style={{
                            filter: `drop-shadow(0 0 3px ${entry.color}80)`,
                          }}
                        />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1 text-[10px] space-y-0.5">
                {queryDistData.map((q) => (
                  <div key={q.name} className="flex items-center gap-1.5">
                    <span
                      className="h-1.5 w-1.5 rounded-sm"
                      style={{
                        background: q.color,
                        boxShadow: `0 0 3px ${q.color}`,
                      }}
                    />
                    <span className="text-neutral-300">{q.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Concurrent Sessions */}
          <div className="relative rounded-2xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-[11px] text-neutral-300">
                Concurrent Sessions
              </span>
              <Sparkles
                className="h-3.5 w-3.5"
                style={{
                  color: C.yellow,
                  filter: `drop-shadow(0 0 3px ${C.yellow})`,
                }}
                {...iconStroke}
              />
            </div>
            <div className="mt-1 flex items-center gap-2">
              <div
                style={{
                  filter: `drop-shadow(0 0 4px ${C.yellow}80)`,
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <defs>
                    <linearGradient
                      id="sparkle-grad"
                      x1="0"
                      y1="0"
                      x2="1"
                      y2="1"
                    >
                      <stop offset="0%" stopColor="#ffffff" />
                      <stop offset="100%" stopColor="#cbd5e1" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M12 2 L13.5 9.5 L21 11 L13.5 12.5 L12 20 L10.5 12.5 L3 11 L10.5 9.5 Z"
                    fill="url(#sparkle-grad)"
                    style={{
                      filter: "drop-shadow(0 0 4px rgba(255,255,255,0.8))",
                    }}
                  />
                  <circle cx="19" cy="5" r="1" fill="#ffffff" />
                  <circle cx="5" cy="18" r="0.8" fill="#ffffff" />
                </svg>
              </div>
              <div
                className="text-lg font-semibold text-white"
                style={{
                  textShadow: `0 0 8px rgba(255,255,255,0.6)`,
                }}
              >
                {Math.round(telemetry.concurrentSessions)}
              </div>
            </div>
          </div>
        </div>

        {/* ─── Footer ──────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2 text-[11px] font-mono">
          <div
            className="flex items-center gap-2"
            style={{
              color: C.greenGlow,
              textShadow: `0 0 8px ${C.greenGlow}aa`,
            }}
          >
            <span
              className="h-1.5 w-1.5 animate-pulse rounded-full"
              style={{
                background: C.greenGlow,
                boxShadow: `0 0 6px ${C.greenGlow}`,
              }}
            />
            <span className="uppercase tracking-wider">
              SYSTEM HEALTHY | REAL-TIME TELEMETRY STREAMING
            </span>
          </div>
          <div className="text-neutral-500">
            Live Data • Updated in Real-Time
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── PERFORMANCE VIEW ────────────────────────────────────────────────────────
export function PerformanceView() {
  return (
    <AnimationProvider>
      <PerformanceViewInner />
    </AnimationProvider>
  );
}
