import React from "react";
import { BrainCircuit, Zap, Search, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { Task, C, iconStroke } from "../types/telemetry.types";
import { ProgressRing } from "./charts/ProgressRing";

interface AIAgencyModuleProps {
  successRate: number;
  autoRate: number;
  humanRate: number;
  currentPhase: string;
  tasks: Task[];
}

/** Agent cycle stepper with glowing active state */
const AgentCycleStepper: React.FC<{ currentPhase: string }> = React.memo(({ currentPhase }) => {
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
});
AgentCycleStepper.displayName = "AgentCycleStepper";

/** Task delegation bar - auto vs human-in-the-loop */
const DelegationBar: React.FC<{ auto: number; human: number }> = React.memo(({ auto, human }) => {
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
});
DelegationBar.displayName = "DelegationBar";

/** In-progress agent task list with status indicators */
const InProgressTaskList: React.FC<{ tasks: Task[] }> = React.memo(({ tasks }) => {
  const statusColor = (s: Task["status"]) => {
    switch (s) {
      case "executing": return C.cyan;
      case "verifying": return C.yellow;
      case "planning": return C.purple;
      case "queued": return "#525252";
      case "complete": return C.green;
      default: return "#525252";
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
});
InProgressTaskList.displayName = "InProgressTaskList";

/** Compact metrics badge */
const MetricBadge: React.FC<{
  label: string;
  value: string;
  color: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "stable";
}> = React.memo(({ label, value, color, icon, trend }) => {
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
            <span className="ml-1 text-[10px] font-semibold text-green-400">↑</span>
          )}
          {trend === "down" && (
            <span className="ml-1 text-[10px] font-semibold text-red-400">↓</span>
          )}
        </div>
      </div>
    </div>
  );
});
MetricBadge.displayName = "MetricBadge";

export const AIAgencyModule: React.FC<AIAgencyModuleProps> = React.memo(({
  successRate,
  autoRate,
  humanRate,
  currentPhase,
  tasks,
}) => {
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
      <InProgressTaskList tasks={tasks} />

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
});

AIAgencyModule.displayName = "AIAgencyModule";
export { MetricBadge };
