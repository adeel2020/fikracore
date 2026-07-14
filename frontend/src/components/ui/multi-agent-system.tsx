"use client";

import React, { useState, useEffect } from "react";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { Badge } from "./badge";
import {
  Bot,
  TrendingUp,
  Cpu,
  BarChart3,
  BookOpen,
  ChevronRight,
  Zap,
} from "lucide-react";

export type AgentStatus = "idle" | "active" | "complete";

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  icon: React.ReactNode;
  status: AgentStatus;
  color: string;
}

interface MultiAgentSystemProps {
  agents?: Agent[];
  animated?: boolean;
  showDescriptions?: boolean;
  compact?: boolean;
}

const defaultAgents: Agent[] = [
  {
    id: "business",
    name: "Business Analyst",
    role: "Revenue & Churn Insights",
    description: "Identifies business trends and revenue patterns",
    icon: <TrendingUp className="w-5 h-5" />,
    status: "idle",
    color: "cyan",
  },
  {
    id: "technical",
    name: "Technical Analyst",
    role: "Systems & Infrastructure",
    description: "Analyzes system failures and IT bottlenecks",
    icon: <Cpu className="w-5 h-5" />,
    status: "idle",
    color: "blue",
  },
  {
    id: "visualization",
    name: "Visualization Specialist",
    role: "Chart Recommendations",
    description: "Recommends optimal visualizations",
    icon: <BarChart3 className="w-5 h-5" />,
    status: "idle",
    color: "fuchsia",
  },
  {
    id: "storyteller",
    name: "Data Storyteller",
    role: "Narrative Synthesis",
    description: "Creates unified data-driven narratives",
    icon: <BookOpen className="w-5 h-5" />,
    status: "idle",
    color: "lime",
  },
];

const statusColors = {
  idle: "border-white/10 bg-white/5 text-neutral-400",
  active:
    "border-cyan-500/50 bg-cyan-500/10 text-cyan-400 shadow-[0_0_12px_rgba(0,229,255,0.5)]",
  complete:
    "border-lime-400/50 bg-lime-400/10 text-lime-300 shadow-[0_0_12px_rgba(204,255,0,0.3)]",
};

const statusLabels = {
  idle: "Ready",
  active: "Processing",
  complete: "Complete",
};

export function MultiAgentSystem({
  agents = defaultAgents,
  animated = true,
  showDescriptions = true,
  compact = false,
}: MultiAgentSystemProps) {
  const [displayAgents, setDisplayAgents] = useState(agents);

  useEffect(() => {
    setDisplayAgents(agents);
  }, [agents]);

  const isParallel = displayAgents
    .slice(0, 2)
    .every((a) => a.status === "active" || a.status === "complete");

  return (
    <div
      className={cn(
        "w-full space-y-4",
        compact ? "space-y-2" : "space-y-4"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-2">
        <Bot className="w-4 h-4 text-cyan-400" />
        <span className="text-sm font-semibold text-white">
          Multi-Agent System
        </span>
        <Badge variant="neon" className="ml-auto text-xs">
          {displayAgents.filter((a) => a.status === "active").length} active
        </Badge>
      </div>

      {/* Agents Container */}
      <div className="space-y-3">
        {/* Phase 1: Parallel Agents (Business + Technical) */}
        <div className="grid grid-cols-2 gap-3">
          {displayAgents.slice(0, 2).map((agent) => (
            <div key={agent.id}>
              <AgentCard
                agent={agent}
                compact={compact}
                showDescription={showDescriptions}
                animated={animated}
              />
            </div>
          ))}
        </div>

        {/* Connection Arrow (if parallel execution) */}
        {isParallel && animated && (
          <div className="flex justify-center py-1">
            <div className="flex items-center gap-1 text-cyan-400/50">
              <div className="text-xs font-medium">Sequential →</div>
              <ChevronRight className="w-4 h-4 animate-pulse" />
            </div>
          </div>
        )}

        {/* Phase 2: Sequential Agents (Visualization + Storyteller) */}
        <div className="grid grid-cols-2 gap-3">
          {displayAgents.slice(2, 4).map((agent) => (
            <div key={agent.id}>
              <AgentCard
                agent={agent}
                compact={compact}
                showDescription={showDescriptions}
                animated={animated}
                dependsOn={isParallel}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Stats Footer */}
      {!compact && (
        <div className={cn(glassSurfaceStatic, "rounded-lg p-3")}>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-xs text-neutral-400 mb-1">Ready</div>
              <div className="text-lg font-semibold text-cyan-400">
                {displayAgents.filter((a) => a.status === "idle").length}
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-400 mb-1">Active</div>
              <div className="text-lg font-semibold text-cyan-400">
                {displayAgents.filter((a) => a.status === "active").length}
              </div>
            </div>
            <div>
              <div className="text-xs text-neutral-400 mb-1">Complete</div>
              <div className="text-lg font-semibold text-lime-300">
                {displayAgents.filter((a) => a.status === "complete").length}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface AgentCardProps {
  agent: Agent;
  compact?: boolean;
  showDescription?: boolean;
  animated?: boolean;
  dependsOn?: boolean;
}

function AgentCard({
  agent,
  compact = false,
  showDescription = true,
  animated = true,
  dependsOn = false,
}: AgentCardProps) {
  return (
    <div
      className={cn(
        glassSurfaceStatic,
        "rounded-lg p-3 transition-all duration-300",
        agent.status === "active" &&
          "border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_16px_rgba(0,229,255,0.3)]",
        agent.status === "complete" &&
          "border-lime-400/50 bg-lime-400/10 shadow-[0_0_16px_rgba(204,255,0,0.2)]",
        dependsOn && agent.status === "idle" && "opacity-50"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className={cn(
            "flex-shrink-0 p-2 rounded-lg transition-all duration-300",
            agent.status === "idle" && "bg-white/5 text-neutral-400",
            agent.status === "active" &&
              "bg-cyan-500/20 text-cyan-400 animate-pulse",
            agent.status === "complete" && "bg-lime-400/20 text-lime-300"
          )}
        >
          {agent.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-white truncate">
                {agent.name}
              </h3>
              <p className="text-xs text-neutral-400 truncate">
                {agent.role}
              </p>
            </div>
            <Badge
              variant={
                agent.status === "active"
                  ? "default"
                  : agent.status === "complete"
                    ? "alert"
                    : "muted"
              }
              className={cn(
                "text-xs px-2 py-0.5 flex-shrink-0 whitespace-nowrap",
                agent.status === "active" && animated && "animate-pulse"
              )}
            >
              {statusLabels[agent.status]}
            </Badge>
          </div>

          {!compact && showDescription && (
            <p className="text-xs text-neutral-500 mt-1 truncate">
              {agent.description}
            </p>
          )}
        </div>
      </div>

      {/* Status Indicator Line */}
      {agent.status === "active" && animated && (
        <div className="mt-2 h-0.5 bg-gradient-to-r from-cyan-500/50 to-transparent rounded-full animate-pulse" />
      )}
    </div>
  );
}
