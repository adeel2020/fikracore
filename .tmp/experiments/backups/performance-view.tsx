"use client";

import { useEffect, useState, useRef, useCallback, useId, createContext, useContext } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  ComposedChart,
  Scatter,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Database,
  Gauge,
  GitBranch,
  Layers,
  Loader2,
  Network,
  Pause,
  Play,
  Radar,
  Search,
  Share2,
  Sparkles,
  SplitSquareHorizontal,
  TrendingUp,
  Zap,
} from "lucide-react";

// ─── Color Tokens ───────────────────────────────────────────────────────────
const C = {
  purple: "#A855F7",
  purpleSoft: "#C084FC",
  purpleDark: "#8B5CF6",
  blue: "#22D3EE",
  blueSoft: "#60A5FA",
  lime: "#CCFF00",
  magenta: "#FF00FF",
  cyan: "#00E5FF",
  orange: "#FB923C",
  orangeHot: "#FF6B35",
  yellow: "#FFE500",
  green: "#00FF87",
  greenGlow: "#10B981",
  pink: "#FF1493",
  red: "#FF4444",
  teal: "#2DD4BF",
  indigo: "#818CF8",
  rose: "#F43F5E",
  white: "#FFFFFF",
};

const iconStroke = { strokeWidth: 1.5 } as const;

// ─── Animation Context ──────────────────────────────────────────────────────
const AnimationContext = createContext<boolean>(true);

function useAnimationEnabled(): boolean {
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

// ─── Real-Time Mock Data Hooks ──────────────────────────────────────────────

function useRealtimeValue(base: number, variance: number, interval = 1800) {
  const [value, setValue] = useState(base);
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      const drift = (Math.random() - 0.5) * variance * 2;
      setValue((prev) => Math.max(0, Math.min(100, prev + drift)));
    }, interval);
    return () => clearInterval(t);
  }, [base, variance, interval, mounted, enabled]);
  return mounted ? value : base;
}

function useRealtimeArray(
  length: number,
  base: number,
  variance: number,
  interval = 2000
) {
  const [data, setData] = useState<number[]>(Array(length).fill(base));
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    setData(() =>
      Array.from({ length }, () => base + (Math.random() - 0.5) * variance)
    );
    const t = setInterval(() => {
      setData((prev) =>
        prev.map(() => base + (Math.random() - 0.5) * variance)
      );
    }, interval);
    return () => clearInterval(t);
  }, [length, base, variance, interval, mounted, enabled]);
  return data;
}

function useAgentCycle() {
  const phases = ["Planning", "Executing", "Verifying", "Complete"] as const;
  const [phase, setPhase] = useState(0);
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setPhase((p) => (p + 1) % phases.length);
    }, 2500);
    return () => clearInterval(t);
  }, [mounted, enabled]);
  return mounted ? phases[phase] : "Planning";
}

function useVectorData() {
  const [data, setData] = useState<{ index: number; score: number }[]>(
    Array.from({ length: 20 }, (_, i) => ({ index: i, score: 0.75 }))
  );
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    setData(() =>
      Array.from({ length: 20 }, (_, i) => ({
        index: i,
        score: Math.random() * 0.5 + 0.5,
      }))
    );
    const t = setInterval(() => {
      setData((prev) =>
        prev.map((d) => ({
          ...d,
          score: Math.max(
            0,
            Math.min(1, d.score + (Math.random() - 0.5) * 0.2)
          ),
        }))
      );
    }, 1500);
    return () => clearInterval(t);
  }, [mounted, enabled]);
  return data;
}

function useGraphHops() {
  const [hops, setHops] = useState({ "1-Hop": 35, "2-Hop": 22, "3-Hop": 12 });
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    setHops({
      "1-Hop": Math.floor(Math.random() * 40 + 20),
      "2-Hop": Math.floor(Math.random() * 30 + 15),
      "3-Hop": Math.floor(Math.random() * 20 + 5),
    });
    const t = setInterval(() => {
      setHops({
        "1-Hop": Math.floor(Math.random() * 40 + 20),
        "2-Hop": Math.floor(Math.random() * 30 + 15),
        "3-Hop": Math.floor(Math.random() * 20 + 5),
      });
    }, 3000);
    return () => clearInterval(t);
  }, [mounted, enabled]);
  return hops;
}

// ─── Shared Sub-Components ──────────────────────────────────────────────────

/** Glowing card wrapper */
function Panel({
  title,
  className,
  children,
  rightSlot,
}: {
  title?: string;
  className?: string;
  children: React.ReactNode;
  rightSlot?: React.ReactNode;
}) {
  return (
    <div
      className={`relative rounded-2xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl shadow-2xl ${
        className || ""
      }`}
    >
      {title && (
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-200">
            {title}
          </h3>
          {rightSlot}
        </div>
      )}
      {children}
    </div>
  );
}

/** Circular progress ring with neon glow */
function ProgressRing({
  value,
  color,
  size = 130,
  stroke = 12,
  label,
  suffix = "%",
  icon,
  glowIntensity = 1,
}: {
  value: number;
  color: string;
  size?: number;
  stroke?: number;
  label?: string;
  suffix?: string;
  icon?: React.ReactNode;
  glowIntensity?: number;
}) {
  const uid = useId();
  const id = `ring-${color.replace("#", "")}-${uid}`;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(100, Math.max(0, value)) / 100);
  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity={0.95} />
            <stop offset="100%" stopColor={color} stopOpacity={0.55} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeOpacity={0.12}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{
            filter: `drop-shadow(0 0 ${8 * glowIntensity}px ${color}aa)`,
            transition: "stroke-dashoffset 1s ease",
          }}
        />
      </svg>
      <div className="relative z-10 flex flex-col items-center justify-center">
        {icon && (
          <div
            className="mb-1 flex h-6 w-6 items-center justify-center"
            style={{
              color,
              filter: `drop-shadow(0 0 ${4 * glowIntensity}px ${color}aa)`,
            }}
          >
            {icon}
          </div>
        )}
        <div
          className="text-3xl font-bold leading-none text-white"
          style={{ textShadow: `0 0 ${14 * glowIntensity}px ${color}80` }}
        >
          {Math.round(value)}
          {suffix}
        </div>
        {label && (
          <div className="mt-1 text-[11px] text-neutral-300">{label}</div>
        )}
      </div>
    </div>
  );
}

/** Mini badge with pulse glow */
function MetricBadge({
  label,
  value,
  color,
  icon,
  trend,
}: {
  label: string;
  value: string;
  color: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "stable";
}) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2">
      {icon && (
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{
            background: `${color}15`,
            color,
            boxShadow: `0 0 8px ${color}40`,
          }}
        >
          {icon}
        </div>
      )}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-neutral-400">
          {label}
        </div>
        <div
          className="text-sm font-bold"
          style={{
            color,
            textShadow: `0 0 8px ${color}60`,
          }}
        >
          {value}
          {trend === "up" && (
            <TrendingUp className="ml-1 inline h-3 w-3 text-green-400" />
          )}
          {trend === "down" && (
            <TrendingUp className="ml-1 inline h-3 w-3 rotate-180 text-red-400" />
          )}
        </div>
      </div>
    </div>
  );
}

// ─── MODULE A: AI Agency - Task Completions ─────────────────────────────────

/** Agent cycle stepper with glowing active state */
function AgentCycleStepper({ currentPhase }: { currentPhase: string }) {
  const phases = [
    { key: "Planning", icon: <BrainCircuit className="h-3.5 w-3.5" /> },
    { key: "Executing", icon: <Zap className="h-3.5 w-3.5" /> },
    { key: "Verifying", icon: <Search className="h-3.5 w-3.5" /> },
    { key: "Complete", icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
  ];
  const idx = phases.findIndex((p) => p.key === currentPhase);
  return (
    <div className="flex items-center gap-1">
      {phases.map((p, i) => {
        const active = i === idx;
        const done = i < idx;
        return (
          <div key={p.key} className="flex items-center gap-1">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full border transition-all duration-500 ${
                active
                  ? "border-cyan-400 scale-110"
                  : done
                  ? "border-green-500/60"
                  : "border-white/10"
              }`}
              style={
                active
                  ? {
                      background: `${C.cyan}20`,
                      boxShadow: `0 0 12px ${C.cyan}, 0 0 24px ${C.cyan}40`,
                    }
                  : done
                  ? {
                      background: `${C.green}15`,
                    }
                  : { background: "rgba(255,255,255,0.03)" }
              }
            >
              <div
                className={
                  active
                    ? "animate-pulse text-cyan-300"
                    : done
                    ? "text-green-400"
                    : "text-neutral-500"
                }
              >
                {p.icon}
              </div>
            </div>
            {i < phases.length - 1 && (
              <div
                className={`h-[2px] w-4 rounded transition-all duration-500 ${
                  done ? "bg-green-500/50" : active ? "bg-cyan-400/50" : "bg-white/5"
                }`}
                style={active ? { boxShadow: `0 0 6px ${C.cyan}` } : {}}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/** Task delegation bar - auto vs human-in-the-loop */
function DelegationBar({
  auto,
  human,
}: {
  auto: number;
  human: number;
}) {
  const total = auto + human || 1;
  return (
    <div className="mt-3">
      <div className="mb-1 flex items-center justify-between text-[10px] text-neutral-400">
        <span className="flex items-center gap-1">
          <Zap className="h-3 w-3 text-green-400" />
          Auto-Delegated
        </span>
        <span className="flex items-center gap-1">
          <AlertTriangle className="h-3 w-3 text-orange-400" />
          Human-in-Loop
        </span>
      </div>
      <div className="flex h-4 w-full overflow-hidden rounded-full border border-white/5">
        <div
          className="h-full transition-all duration-700"
          style={{
            width: `${(auto / total) * 100}%`,
            background: `linear-gradient(90deg, ${C.green}, ${C.cyan})`,
            boxShadow: `0 0 8px ${C.green}60`,
          }}
        />
        <div
          className="h-full transition-all duration-700"
          style={{
            width: `${(human / total) * 100}%`,
            background: `linear-gradient(90deg, ${C.orange}, ${C.orangeHot})`,
            boxShadow: `0 0 8px ${C.orangeHot}60`,
          }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] font-mono">
        <span style={{ color: C.green, textShadow: `0 0 4px ${C.green}60` }}>
          {Math.round((auto / total) * 100)}%
        </span>
        <span
          style={{ color: C.orange, textShadow: `0 0 4px ${C.orange}60` }}
        >
          {Math.round((human / total) * 100)}%
        </span>
      </div>
    </div>
  );
}

/** In-progress agent task list with status indicators */
function InProgressTaskList() {
  const [tasks, setTasks] = useState([
    { id: "T-1024", label: "Network Anomaly Diagnosis", status: "executing", progress: 68 },
    { id: "T-1025", label: "RAG Index Optimization", status: "verifying", progress: 91 },
    { id: "T-1026", label: "CKG Entity Resolution", status: "planning", progress: 12 },
    { id: "T-1027", label: "SLA Compliance Report", status: "queued", progress: 0 },
  ]);

  // Simulate progress updates
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setTasks((prev) =>
        prev.map((task) => {
          if (task.status === "executing") {
            const p = Math.min(100, task.progress + Math.floor(Math.random() * 8 + 2));
            return { ...task, progress: p, status: p >= 100 ? "complete" : "executing" };
          }
          if (task.status === "verifying") {
            const p = Math.min(100, task.progress + Math.floor(Math.random() * 4 + 1));
            return { ...task, progress: p, status: p >= 100 ? "complete" : "verifying" };
          }
          if (task.status === "planning" && Math.random() > 0.92) {
            return { ...task, status: "executing" as const };
          }
          return task;
        })
      );
    }, 2500);
    return () => clearInterval(t);
  }, [mounted, enabled]);
  const statusColor = (s: string) => {
    switch (s) {
      case "executing": return C.cyan;
      case "verifying": return C.yellow;
      case "planning": return C.purple;
      case "queued": return "#525252";
      case "complete": return C.green;
      default: return "#525252";
    }
  };

  const statusLabel = (s: string) => {
    switch (s) {
      case "executing": return "Executing";
      case "verifying": return "Verifying";
      case "planning": return "Planning";
      case "queued": return "Queued";
      case "complete": return "Complete";
      default: return s;
    }
  };

  return (
    <div className="mt-3 rounded-xl border border-white/5 bg-white/[0.015] p-2.5">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
          <Loader2 className="h-3 w-3 animate-spin" />
          In-Progress Tasks
        </div>
        <div className="text-[10px] font-mono text-neutral-500">
          {tasks.filter((t) => t.status !== "complete").length} active
        </div>
      </div>
      <div className="space-y-2">
        {tasks.slice(0, 4).map((task) => (
          <div key={task.id} className="flex items-center gap-2">
            {/* Status dot */}
            <div
              className="h-2 w-2 shrink-0 rounded-full"
              style={{
                background: statusColor(task.status),
                boxShadow: task.status !== "queued" && task.status !== "complete"
                  ? `0 0 6px ${statusColor(task.status)}`
                  : "none",
              }}
            />
            {/* Task ID + label */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-mono text-neutral-500">{task.id}</span>
                {task.status === "executing" && (
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ background: C.cyan }} />
                )}
              </div>
              <div className="truncate text-[10px] text-neutral-300">{task.label}</div>
            </div>
            {/* Progress bar + status */}
            <div className="flex items-center gap-2">
              <div className="h-2 w-16 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${task.progress}%`,
                    background: `linear-gradient(90deg, ${statusColor(task.status)}, ${statusColor(task.status)}cc)`,
                    boxShadow: `0 0 4px ${statusColor(task.status)}60`,
                  }}
                />
              </div>
              <div
                className="w-12 text-right text-[9px] font-mono"
                style={{ color: statusColor(task.status) }}
              >
                {task.status === "complete" ? "Done" : `${task.progress}%`}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** AI Agency - Main Component */
function AIAgencyModule() {
  const successRate = useRealtimeValue(87, 5, 2000);
  const autoRate = useRealtimeValue(72, 8, 2500);
  const humanRate = useRealtimeValue(28, 8, 2500);
  const currentPhase = useAgentCycle();

  return (
    <div className="flex flex-col gap-4">
      {/* Top: Radial gauge + Stepper side by side */}
      <div className="flex items-center gap-3">
        <ProgressRing
          value={successRate}
          color={C.cyan}
          size={110}
          stroke={10}
          label="Task Success"
          suffix="%"
          icon={<CheckCircle2 className="h-4 w-4" {...iconStroke} />}
          glowIntensity={1.5}
        />
        <div className="flex-1 space-y-2">
          <div className="text-[10px] uppercase tracking-wider text-neutral-400">
            Agent Cycle
          </div>
          <AgentCycleStepper currentPhase={currentPhase} />
          <div
            className="text-[11px] font-semibold tracking-wide animate-pulse"
            style={{ color: C.cyan, textShadow: `0 0 6px ${C.cyan}60` }}
          >
            {currentPhase}
          </div>
        </div>
      </div>

      {/* Bottom: Delegation bar */}
      <DelegationBar auto={autoRate} human={humanRate} />

      {/* In-progress task list */}
      <InProgressTaskList />

      {/* Compact metrics */}
      <div className="grid grid-cols-2 gap-2">
        <MetricBadge
          label="Tasks Completed"
          value="1,284"
          color={C.green}
          icon={<CheckCircle2 className="h-4 w-4" />}
          trend="up"
        />
        <MetricBadge
          label="Avg Cycle Time"
          value="2.4s"
          color={C.blue}
          icon={<Zap className="h-4 w-4" />}
          trend="down"
        />
      </div>
    </div>
  );
}

// ─── MODULE B: RAG Similarity Searches ──────────────────────────────────────

/** Production-grade vector embedding similarity spectrum chart */
function VectorDensityChart({ data }: { data: { index: number; score: number }[] }) {
  const sorted = [...data].sort((a, b) => a.score - b.score);
  const highConfCount = data.filter((d) => d.score >= 0.7).length;
  const lowConfCount = data.filter((d) => d.score >= 0.4 && d.score < 0.7).length;
  const fallbackCount = data.filter((d) => d.score < 0.4).length;

  return (
    <div>
      <div className="h-32 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 6, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="vector-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.purple} stopOpacity={0.85} />
                <stop offset="30%" stopColor={C.blue} stopOpacity={0.55} />
                <stop offset="70%" stopColor={C.cyan} stopOpacity={0.25} />
                <stop offset="100%" stopColor={C.cyan} stopOpacity={0} />
              </linearGradient>
              <linearGradient id="zone-high" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(0,255,135,0.08)" />
                <stop offset="100%" stopColor="rgba(0,255,135,0.02)" />
              </linearGradient>
              <linearGradient id="zone-mid" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(255,229,0,0.06)" />
                <stop offset="100%" stopColor="rgba(255,229,0,0.02)" />
              </linearGradient>
              <linearGradient id="zone-low" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="rgba(255,68,68,0.06)" />
                <stop offset="100%" stopColor="rgba(255,68,68,0.02)" />
              </linearGradient>
            </defs>
            <XAxis dataKey="index" hide axisLine={false} tickLine={false} />
            <YAxis hide domain={[0, 1]} axisLine={false} tickLine={false} />

            {/* Confetti scatter dots for higher realism */}
            {data.map((d, i) => (
              <circle
                key={i}
                cx={`${(d.index / data.length) * 100}%`}
                cy={`${(1 - d.score) * 100}%`}
                r={d.score > 0.7 ? 2 : d.score > 0.4 ? 1.2 : 0.8}
                fill={
                  d.score >= 0.7
                    ? C.green
                    : d.score >= 0.4
                    ? C.yellow
                    : C.red
                }
                fillOpacity={0.6}
                style={{
                  filter: `drop-shadow(0 0 ${
                    d.score >= 0.7 ? 4 : 2
                  }px ${
                    d.score >= 0.7
                      ? C.green
                      : d.score >= 0.4
                      ? C.yellow
                      : C.red
                  }80)`,
                }}
              />
            ))}

            {/* Zone fill: High confidence area (0.7 - 1.0) */}
            <Area
              type="monotone"
              dataKey={() => 1}
              stroke="none"
              fill="url(#zone-high)"
              stackId="zones"
            />
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke="none"
              fill="url(#zone-high)"
              stackId="zones"
            />

            {/* Zone fill: Medium confidence area (0.4 - 0.7) */}
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke="none"
              fill="url(#zone-mid)"
              stackId="zones"
            />
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke="none"
              fill="url(#zone-mid)"
              stackId="zones"
            />

            {/* Zone fill: Low confidence area (0 - 0.4) */}
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke="none"
              fill="url(#zone-low)"
              stackId="zones"
            />

            {/* Threshold lines */}
            <Area
              type="monotone"
              dataKey={() => 0.7}
              stroke={C.green}
              strokeWidth={1.2}
              strokeDasharray="4 3"
              fill="none"
              strokeOpacity={0.7}
            />
            <Area
              type="monotone"
              dataKey={() => 0.4}
              stroke={C.yellow}
              strokeWidth={0.8}
              strokeDasharray="3 3"
              fill="none"
              strokeOpacity={0.5}
            />

            {/* Main similarity curve */}
            <Area
              type="monotone"
              dataKey="score"
              stroke={C.purple}
              fill="url(#vector-grad)"
              strokeWidth={2}
              dot={false}
              style={{ filter: `drop-shadow(0 0 8px ${C.purple}80)` }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Embedded zone legend + counts */}
      <div className="mt-1 grid grid-cols-3 gap-1">
        <div className="rounded border border-green-500/20 bg-green-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-green-400">HIGH ≥0.70</div>
          <div className="text-xs font-bold text-green-300">{highConfCount}</div>
        </div>
        <div className="rounded border border-yellow-500/20 bg-yellow-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-yellow-400">MID 0.40–0.69</div>
          <div className="text-xs font-bold text-yellow-300">{lowConfCount}</div>
        </div>
        <div className="rounded border border-red-500/20 bg-red-500/5 px-2 py-1 text-center">
          <div className="text-[9px] font-mono text-red-400">LOW {"<"}0.40</div>
          <div className="text-xs font-bold text-red-300">{fallbackCount}</div>
        </div>
      </div>
    </div>
  );
}

/** Production Hit/Miss/Fallback radial indicator with precision arc */
function HitMissFallbackIndicator({ data }: { data: number[] }) {
  const [hit, miss, fallback] = data;
  const total = hit + miss + fallback || 1;
  const hitPct = (hit / total) * 100;
  const missPct = (miss / total) * 100;
  const fbPct = (fallback / total) * 100;

  // Precision metrics
  const precision = Math.round(hit / (hit + miss || 1) * 100);
  const recall = Math.round(hit / (hit + fallback || 1) * 100);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-neutral-400">
          Retrieval Precision
        </div>
        <div className="flex gap-2 text-[10px] font-mono">
          <span style={{ color: C.green, textShadow: `0 0 4px ${C.green}60` }}>
            P:{precision}%
          </span>
          <span style={{ color: C.blue, textShadow: `0 0 4px ${C.blue}60` }}>
            R:{recall}%
          </span>
        </div>
      </div>

      {/* Segmented bar with labels */}
      <div className="relative h-7 w-full">
        <div className="flex h-full w-full overflow-hidden rounded-lg border border-white/5 bg-white/[0.02]">
          <div
            className="flex items-center justify-center text-[9px] font-bold text-black transition-all duration-500"
            style={{
              width: `${hitPct}%`,
              background: `linear-gradient(135deg, #00FF87, #2DD4BF)`,
              boxShadow: `inset 0 0 12px ${C.green}40, 0 0 8px ${C.green}60`,
            }}
          >
            {hitPct > 12 ? `${Math.round(hitPct)}%` : ""}
          </div>
          <div
            className="flex items-center justify-center text-[9px] font-bold text-black transition-all duration-500"
            style={{
              width: `${missPct}%`,
              background: `linear-gradient(135deg, #FB923C, #FF6B35)`,
              boxShadow: `inset 0 0 12px ${C.orange}40`,
            }}
          >
            {missPct > 12 ? `${Math.round(missPct)}%` : ""}
          </div>
          <div
            className="flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
            style={{
              width: `${fbPct}%`,
              background: `linear-gradient(135deg, #FF4444, #F43F5E)`,
              boxShadow: `inset 0 0 12px ${C.red}40`,
            }}
          >
            {fbPct > 12 ? `${Math.round(fbPct)}%` : ""}
          </div>
        </div>

        {/* Micro tick markers on bar */}
        {[25, 50, 75].map((tick) => (
          <div
            key={tick}
            className="absolute top-0 h-full w-px bg-white/10"
            style={{ left: `${tick}%` }}
          />
        ))}
      </div>

      {/* Compact legend */}
      <div className="flex justify-between text-[9px]">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.green, boxShadow: `0 0 4px ${C.green}` }} />
          <span className="text-green-400">Top-K Hit ({Math.round(hitPct)}%)</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.orange, boxShadow: `0 0 4px ${C.orange}` }} />
          <span className="text-orange-400">Low Conf. ({Math.round(missPct)}%)</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full" style={{ background: C.red, boxShadow: `0 0 4px ${C.red}` }} />
          <span className="text-red-400">Fallback ({Math.round(fbPct)}%)</span>
        </span>
      </div>
    </div>
  );
}

/** Embedding latency with live oscilloscope-style waveform */
function EmbeddingLatencyPanel() {
  const latency = useRealtimeValue(24, 10, 1000);
  const [waveform, setWaveform] = useState<number[]>(
    Array.from({ length: 30 }, () => 25)
  );
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    setWaveform(Array.from({ length: 30 }, () => Math.random() * 40 + 10));
    const t = setInterval(() => {
      setWaveform((prev) => [
        ...prev.slice(1),
        Math.random() * 40 + 10,
      ]);
    }, 300);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  const maxWf = Math.max(...waveform, 1);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-neutral-400">
            Embedding Latency
          </div>
          <div className="flex items-baseline gap-1">
            <div
              className="text-2xl font-bold"
              style={{
                color: C.purple,
                textShadow: `0 0 12px ${C.purple}80`,
              }}
            >
              {Math.round(latency)}
            </div>
            <span className="text-sm text-neutral-400">ms</span>
            <span className="ml-2 text-[10px] text-neutral-500">p50: {Math.round(latency * 0.85)}ms</span>
          </div>
        </div>
        {/* Oscilloscope waveform */}
        <div className="flex h-10 w-20 items-end gap-[1px]">
          {waveform.slice(0, 20).map((d, i) => {
            const h = Math.max(2, (d / maxWf) * 100);
            const isPeak = d > maxWf * 0.8;
            return (
              <div
                key={i}
                className="w-[3px] rounded-t transition-all duration-150"
                style={{
                  height: `${h}%`,
                  background: isPeak
                    ? `linear-gradient(to top, ${C.pink}, ${C.red})`
                    : `linear-gradient(to top, ${C.purple}, ${C.blue})`,
                  boxShadow: isPeak
                    ? `0 0 6px ${C.pink}80`
                    : `0 0 3px ${C.purple}60`,
                  opacity: 0.6 + (d / maxWf) * 0.4,
                }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

/** RAG Similarity - Production Main Component */
function RAGSimilarityModule() {
  const vectorData = useVectorData();
  const hit = useRealtimeValue(65, 8, 1500);
  const miss = useRealtimeValue(22, 6, 1500);
  const fallback = useRealtimeValue(13, 4, 1500);
  const avgScore = useRealtimeValue(74, 5, 2000);

  return (
    <div className="flex flex-col gap-3">
      {/* Vector density chart with zone overlays */}
      <div>
        <div className="mb-1 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
            <Radar className="h-3 w-3" />
            Embedding Cosine Similarity
          </div>
          <div
            className="text-[10px] font-mono"
            style={{ color: C.teal, textShadow: `0 0 4px ${C.teal}60` }}
          >
            μ={(avgScore / 100).toFixed(2)}
          </div>
        </div>
        <VectorDensityChart data={vectorData} />
      </div>

      {/* Hit/Miss/Fallback with precision metrics */}
      <HitMissFallbackIndicator data={[hit, miss, fallback]} />

      {/* Embedding latency with oscilloscope */}
      <EmbeddingLatencyPanel />

      {/* Compact stats matrix */}
      <div className="grid grid-cols-3 gap-2">
        <MetricBadge
          label="Avg Similarity"
          value={`${Math.round(avgScore)}%`}
          color={C.teal}
          icon={<Search className="h-3.5 w-3.5" />}
          trend="up"
        />
        <MetricBadge
          label="Index Size"
          value="12.4K"
          color={C.indigo}
          icon={<Database className="h-3.5 w-3.5" />}
        />
        <MetricBadge
          label="Chunk Count"
          value="3.2K"
          color={C.cyan}
          icon={<Layers className="h-3.5 w-3.5" />}
        />
      </div>
    </div>
  );
}

// ─── MODULE C: CKG Context Retrievals ───────────────────────────────────────

/** Minimalist CKG static graph visualization */
export default function SubgraphVisualizer() {
  // 1. 13 Exact coordinates for a 6-Pointed Star + Center Hub
  const starSlots = [
    { x: 130, y: 100 }, // 0: Center Hub
    { x: 130, y: 14 },  // 1: Outer Top Point
    { x: 152, y: 63 },  // 2: Inner Top Right Valley
    { x: 205, y: 57 },  // 3: Outer Upper Right Point
    { x: 173, y: 100 }, // 4: Inner Right Valley
    { x: 205, y: 143 }, // 5: Outer Lower Right Point
    { x: 152, y: 137 }, // 6: Inner Bottom Right Valley
    { x: 130, y: 186 }, // 7: Outer Bottom Point
    { x: 109, y: 137 }, // 8: Inner Bottom Left Valley
    { x: 56, y: 143 },  // 9: Outer Lower Left Point
    { x: 87, y: 100 },  // 10: Inner Left Valley
    { x: 56, y: 57 },   // 11: Outer Upper Left Point
    { x: 109, y: 63 }   // 12: Inner Top Left Valley
  ];

  // 2. Expanded dataset with 13 distinct node colors
  const baseNodes = [
    { id: 0, color: "#FF4444" },  // Red
    { id: 1, color: "#FF6B35" },  // Orange
    { id: 2, color: "#FBBF24" },  // Amber
    { id: 3, color: "#A3E635" },  // Lime
    { id: 4, color: "#22D3EE" },  // Cyan
    { id: 5, color: "#3B82F6" },  // Blue
    { id: 6, color: "#818CF8" },  // Indigo
    { id: 7, color: "#A855F7" },  // Purple
    { id: 8, color: "#D946EF" },  // Fuchsia
    { id: 9, color: "#FB7185" },  // Rose
    { id: 10, color: "#00FF87" }, // Mint
    { id: 11, color: "#2DD4BF" }, // Teal
    { id: 12, color: "#F43F5E" }  // Crimson
  ];

  const [offset, setOffset] = useState(0);
  const enabled = useAnimationEnabled();

  useEffect(() => {
    if (!enabled) return;
    // Shift positions across all 13 slots every 2.5 seconds
    const interval = setInterval(() => {
      setOffset((prevOffset) => (prevOffset + 1) % 13);
    }, 2500);
    return () => clearInterval(interval);
  }, [enabled]);

  const currentNodes = baseNodes.map((node, i) => {
    // Math ensures a flawless carousel loop around all 13 coordinates
    const currentSlot = starSlots[(i + offset) % 13];
    return { ...node, x: currentSlot.x, y: currentSlot.y };
  });

  const getNode = (id: number) => currentNodes.find((n) => n.id === id)!;
  const animStyle = { transition: "all 1.2s cubic-bezier(0.4, 0, 0.2, 1)" };

  return (
    <svg viewBox="0 0 260 200" className="w-full" style={{ height: 200, maxHeight: 200 }}>
      <defs>
        <pattern id="ckg-grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="260" height="200" fill="url(#ckg-grid)" rx="8" />

      {/* Render Links */}
      {/* {links.map((link, i) => {
        const sourceId = link.s !== undefined ? link.s : link[0];
        const targetId = link.t !== undefined ? link.t : link[1];

        const source = getNode(sourceId as number);
        const target = getNode(targetId as number);
        
        if (!source || !target) return null;

        return (
          <g key={`link-${i}`}>
            <line
              x1={source.x} y1={source.y} x2={target.x} y2={target.y}
              stroke="rgba(0, 229, 255, 0.15)"
              strokeWidth={1}
              style={animStyle}
            />
          </g>
        );
      })} */}

      {/* Render Nodes */}
      {currentNodes.map((node) => (
        <g key={`node-${node.id}`}>
          {/* Subtle Outer Glow */}
          <circle cx={node.x} cy={node.y} r={9} fill={node.color} fillOpacity={0.15} style={animStyle} />
          {/* Solid Inner Dot */}
          <circle cx={node.x} cy={node.y} r={4.5} fill={node.color} stroke="rgba(255,255,255,0.2)" strokeWidth={1} style={animStyle} />
        </g>
      ))}
    </svg>
  );
}

/** Graph Hops distribution bars */
function GraphHopsBars({
  hops,
}: {
  hops: { "1-Hop": number; "2-Hop": number; "3-Hop": number };
}) {
  const maxVal = Math.max(hops["1-Hop"], hops["2-Hop"], hops["3-Hop"], 1);

  const items: { key: string; value: number; color: string }[] = [
    { key: "1-Hop", value: hops["1-Hop"], color: "#00FF87" },
    { key: "2-Hop", value: hops["2-Hop"], color: "#22D3EE" },
    { key: "3-Hop", value: hops["3-Hop"], color: "#A855F7" },
  ];

  return (
    <div className="space-y-1.5">
      <div className="text-[10px] uppercase tracking-wider text-neutral-400">
        Sub-Graph Depth
      </div>
      {items.map((item) => (
        <div key={item.key} className="flex items-center gap-2">
          <span className="w-10 text-[10px] font-mono text-neutral-300">
            {item.key}
          </span>
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${(item.value / maxVal) * 100}%`,
                background: `linear-gradient(90deg, ${item.color}, ${item.color}cc)`,
                boxShadow: `0 0 6px ${item.color}60`,
              }}
            />
          </div>
          <span
            className="w-8 text-right text-[10px] font-mono"
            style={{ color: item.color, textShadow: `0 0 4px ${item.color}60` }}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

/** Context extraction latency mini line chart */
function ContextLatencyChart() {
  const [data, setData] = useState<{ t: number; v: number }[]>(
    Array.from({ length: 20 }, (_, i) => ({ t: i, v: 65 }))
  );
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setData((prev) => [
        ...prev.slice(1),
        { t: prev.length, v: 40 + Math.random() * 50 },
      ]);
    }, 1200);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-wider text-neutral-400">
          Context Extraction Latency
        </div>
        <div
          className="text-xs font-bold"
          style={{ color: C.blue, textShadow: `0 0 6px ${C.blue}60` }}
        >
          {Math.round(data[data.length - 1]?.v || 0)}
          <span className="ml-1 text-neutral-400">ms</span>
        </div>
      </div>
      <div className="h-12 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 2, right: 2, bottom: 0, left: 2 }}>
            <defs>
              <linearGradient id="ctx-latency-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.blue} stopOpacity={0.5} />
                <stop offset="100%" stopColor={C.blue} stopOpacity={0} />
              </linearGradient>
            </defs>
            <YAxis hide domain={[0, 120]} />
            <XAxis hide dataKey="t" />
            <Line
              type="monotone"
              dataKey="v"
              stroke={C.blue}
              strokeWidth={1.5}
              dot={false}
              style={{ filter: `drop-shadow(0 0 4px ${C.blue}80)` }}
            />
            <Area
              type="monotone"
              dataKey="v"
              fill="url(#ctx-latency-grad)"
              stroke="none"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/** CKG - Main Component */
function CKGModule() {
  const graphHops = useGraphHops();
  const [weightData, setWeightData] = useState<{ name: string; weight: number }[]>(
    Array.from({ length: 6 }, (_, i) => ({ name: `R${i + 1}`, weight: 50 }))
  );
  const [mounted, setMounted] = useState(false);
  const enabled = useAnimationEnabled();
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!mounted || !enabled) return;
    setWeightData(
      Array.from({ length: 6 }, (_, i) => ({
        name: `R${i + 1}`,
        weight: Math.random() * 100,
      }))
    );
    const t = setInterval(() => {
      setWeightData((prev) =>
        prev.map((d) => ({
          ...d,
          weight: Math.max(5, Math.min(100, d.weight + (Math.random() - 0.5) * 20)),
        }))
      );
    }, 2000);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return (
    <div className="flex flex-col gap-4">
      {/* Subgraph visualization */}
      <div>
        <div className="mb-1 flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
          <Share2 className="h-3 w-3" />
          Entity-Relation Subgraph
        </div>
        <SubgraphVisualizer />
      </div>

      {/* Graph hops */}
      <GraphHopsBars hops={graphHops} />

      {/* Context latency */}
      <ContextLatencyChart />

      {/* Entity relation weights */}
      <div>
        <div className="mb-1 flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-neutral-400">
          <GitBranch className="h-3 w-3" />
          Relation Weight Distribution
        </div>
        <div className="h-14 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weightData} margin={{ top: 0, right: 2, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="name"
                tick={{
                  fill: "#737373",
                  fontSize: 9,
                  fontFamily: "var(--font-geist-mono)",
                }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis hide domain={[0, 100]} />
              <Bar
                dataKey="weight"
                radius={[2, 2, 0, 0]}
                style={{ filter: `drop-shadow(0 0 4px ${C.cyan}60)` }}
              >
                {weightData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={
                      [C.cyan, C.purple, C.green, C.orange, C.blue, C.pink][i]
                    }
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-1 flex justify-between text-[9px] font-mono text-neutral-500">
          <span>Relation IDs</span>
          <span style={{ color: C.cyan, textShadow: `0 0 4px ${C.cyan}60` }}>
            Weights
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Speedometer Gauge (retained from original) ────────────────────────────

function SpeedometerGauge({
  value,
  unit,
  color,
  size = 160,
}: {
  value: number;
  unit: string;
  color: string;
  size?: number;
}) {
  const pct = Math.min(1, value / 40);
  const stroke = 14;
  const r = (size - stroke) / 2;
  const startAngle = 135;
  const endAngle = 405;
  const sweep = endAngle - startAngle;
  const angle = startAngle + sweep * pct;
  const polar = (a: number) => {
    const rad = ((a - 90) * Math.PI) / 180;
    return { x: size / 2 + r * Math.cos(rad), y: size / 2 + r * Math.sin(rad) };
  };
  const describeArc = (start: number, end: number) => {
    const s = polar(start);
    const e = polar(end);
    const large = end - start <= 180 ? 0 : 1;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  };
  const id = `gauge-${color.replace("#", "")}`;
  const needleEnd = polar(angle);
  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="absolute inset-0">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity={0.6} />
            <stop offset="100%" stopColor={color} stopOpacity={1} />
          </linearGradient>
        </defs>
        <path
          d={describeArc(startAngle, endAngle)}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeOpacity={0.12}
          strokeLinecap="round"
        />
        <path
          d={describeArc(startAngle, angle)}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 8px ${color}aa)`,
            transition: "all 0.6s",
          }}
        />
        <line
          x1={size / 2}
          y1={size / 2}
          x2={needleEnd.x}
          y2={needleEnd.y}
          stroke={color}
          strokeWidth={2.5}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={5}
          fill={color}
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
      </svg>
      <div className="relative z-10 flex flex-col items-center">
        <div
          className="text-3xl font-bold text-white"
          style={{ textShadow: `0 0 14px ${color}80` }}
        >
          {value}
        </div>
        <div className="text-[11px] text-neutral-400">{unit}</div>
      </div>
    </div>
  );
}

// ─── Mini Sparkline (retained) ────────────────────────────────────────────

function MiniSparkline({
  data,
  color,
  height = 50,
}: {
  data: { d: string; v: number }[];
  color: string;
  height?: number;
}) {
  const id = `spark-${color.replace("#", "")}`;
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.45} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <YAxis hide domain={[0, 100]} />
          <XAxis
            dataKey="d"
            tick={{
              fill: "#737373",
              fontSize: 9,
              fontFamily: "var(--font-geist-mono)",
            }}
            axisLine={false}
            tickLine={false}
            interval={0}
          />
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            fill={`url(#${id})`}
            strokeWidth={1.5}
            dot={false}
            style={{ filter: `drop-shadow(0 0 3px ${color}80)` }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Brain Icon Glow (retained) ─────────────────────────────────────────

function BrainIconGlow() {
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
}

// ─── MAIN EXPORTED VIEW ────────────────────────────────────────────────────

export function PerformanceView() {
  return (
    <AnimationProvider>
      <PerformanceViewInner />
    </AnimationProvider>
  );
}

function PerformanceViewInner() {
  // Active system metrics with real-time simulation
  const systemLoad = useRealtimeValue(42, 8, 1500);
  const activeRequests = useRealtimeValue(7, 3, 1200);
  const throughput = useRealtimeValue(25.4, 4, 1800);
  const sessionTime = useRealtimeValue(168, 5, 3000);
  const modelHealth = useRealtimeValue(96, 3, 2000);
  const concurrentSessions = useRealtimeValue(15, 2, 2500);
  const queryPieData = useRealtimeArray(3, 40, 15, 2000);

  const queryDistData = [
    { name: "Knowledge-RAG", value: Math.max(10, queryPieData[0]), color: C.green },
    { name: "Action", value: Math.max(5, queryPieData[1]), color: C.blue },
    { name: "Creative", value: Math.max(3, queryPieData[2]), color: C.orange },
  ];

  const throughputData = [
    { h: "0", v: 12 },
    { h: "2", v: 18 },
    { h: "4", v: 14 },
    { h: "6", v: 22 },
    { h: "8", v: 28 },
    { h: "10", v: 24 },
    { h: "12", v: 32 },
    { h: "14", v: 38 },
    { h: "16", v: 30 },
    { h: "18", v: throughput },
    { h: "20", v: 28 },
    { h: "22", v: 22 },
    { h: "24", v: 25 },
  ];

  const memSparkData = [
    { d: "Sun", v: 40 },
    { d: "Mon", v: 55 },
    { d: "Tue", v: systemLoad },
    { d: "Wed", v: 60 },
    { d: "Thu", v: 80 },
    { d: "Fri", v: 72 },
    { d: "Sat", v: 65 },
  ];

  const cacheSparkData = [
    { d: "Sun", v: 30 },
    { d: "Mon", v: 35 },
    { d: "Tue", v: 50 },
    { d: "Wed", v: 45 },
    { d: "Thu", v: systemLoad * 0.6 },
    { d: "Fri", v: 55 },
    { d: "Sat", v: 42 },
  ];

  const enabled = useAnimationEnabled();

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
          <Panel
            title="SYSTEM PERFORMANCE"
            rightSlot={
              <Gauge className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <div className="flex items-center justify-around gap-4">
              <div className="flex flex-col items-center">
                <ProgressRing
                  value={systemLoad}
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
                  value={Math.round(systemLoad * 0.6)}
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
          </Panel>

          {/* Throughput Panel */}
          <Panel
            title="REQUESTS AND THROUGHPUT"
            rightSlot={
              <TrendingUp className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <div className="flex items-center gap-3">
              <SpeedometerGauge
                value={Math.round(throughput * 10) / 10}
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
          </Panel>
        </div>

        {/* ─── MIDDLE ROW: 3 New Infographic Modules ───────────────────────── */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Module A: AI Agency - Task Completions */}
          <Panel
            title="AI AGENCY - TASK COMPLETIONS"
            rightSlot={
              <Layers className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <AIAgencyModule />
          </Panel>

          {/* Module B: RAG Similarity Searches */}
          <Panel
            title="RAG SIMILARITY SEARCHES"
            rightSlot={
              <Search className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <RAGSimilarityModule />
          </Panel>

          {/* Module C: CKG Context Retrievals */}
          <Panel
            title="CKG Context Retrieval Chain"
            rightSlot={
              <Network className="h-3.5 w-3.5 text-neutral-500" {...iconStroke} />
            }
          >
            <CKGModule />
          </Panel>
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
                {Math.floor(sessionTime / 60)}h{" "}
                {Math.round(sessionTime % 60)}m
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
                {Math.round(activeRequests)}
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
                Health Score: {Math.round(modelHealth)}/100
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
                {Math.round(concurrentSessions)}
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
