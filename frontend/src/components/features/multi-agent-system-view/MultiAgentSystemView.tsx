"use client";

import React from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { MultiAgentSystem } from "@/components/ui/multi-agent-system";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, RotateCcw } from "lucide-react";
import { useMultiAgentSystem } from "./useMultiAgentSystem";

export function MultiAgentSystemView() {
  const { agents, isRunning, simulateExecution, resetAgents } = useMultiAgentSystem();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">
          Multi-Agent Orchestration
        </h1>
        <p className="text-neutral-400">
          Intelligent data analysis through coordinated specialist agents
        </p>
      </div>

      {/* Main Component Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Agent System */}
        <div className="lg:col-span-2">
          <GlassCard className="p-6">
            <MultiAgentSystem agents={agents} animated showDescriptions />
          </GlassCard>
        </div>

        {/* Control Panel */}
        <GlassCard className="p-6 h-fit space-y-4">
          <h2 className="text-lg font-semibold text-white">Execution Control</h2>

          <div className="space-y-2">
            <Button
              onClick={simulateExecution}
              disabled={isRunning}
              variant="default"
              size="default"
              className="w-full"
            >
              <Play className="w-4 h-4" />
              {isRunning ? "Running..." : "Start Execution"}
            </Button>
            <Button
              onClick={resetAgents}
              disabled={isRunning}
              variant="outline"
              size="default"
              className="w-full"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </Button>
          </div>

          {/* Status Summary */}
          <div className="pt-4 border-t border-white/10 space-y-3">
            <h3 className="text-sm font-semibold text-white">Summary</h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-white/5 p-3">
                <div className="text-xs text-neutral-400">Phase 1</div>
                <div className="text-sm font-semibold text-cyan-400">
                  Parallel Analysis
                </div>
              </div>
              <div className="rounded-lg bg-white/5 p-3">
                <div className="text-xs text-neutral-400">Phase 2</div>
                <div className="text-sm font-semibold text-cyan-400">
                  Synthesis
                </div>
              </div>
            </div>
          </div>

          {/* Architecture Info */}
          <div className="pt-4 border-t border-white/10 space-y-2">
            <h3 className="text-sm font-semibold text-white">Architecture</h3>
            <div className="text-xs space-y-1 text-neutral-400">
              <p>
                <Badge variant="neon" className="px-2 py-0.5">
                  Async
                </Badge>
                {" "}Business & Technical agents run concurrently
              </p>
              <p>
                <Badge variant="default" className="px-2 py-0.5">
                  Sequential
                </Badge>
                {" "}Visualization & Storyteller follow analysis
              </p>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Information Section */}
      <GlassCard className="p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Agent Roles</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div>
              <h3 className="font-semibold text-cyan-400 mb-1">
                Phase 1: Parallel Analysis
              </h3>
              <p className="text-sm text-neutral-400">
                Business Analyst and Technical Analyst agents execute
                concurrently to extract insights from different perspectives.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-cyan-400 mb-1">
                Business Analyst
              </h3>
              <p className="text-sm text-neutral-400">
                Identifies revenue trends, churn patterns, and executive-level
                business insights from the data.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-cyan-400 mb-1">
                Technical Analyst
              </h3>
              <p className="text-sm text-neutral-400">
                Analyzes system performance, infrastructure bottlenecks, and IT
                operational metrics.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <h3 className="font-semibold text-fuchsia-400 mb-1">
                Phase 2: Sequential Synthesis
              </h3>
              <p className="text-sm text-neutral-400">
                Visualization and Storyteller agents build upon parallel outputs
                to create comprehensive narratives.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-fuchsia-400 mb-1">
                Visualization Specialist
              </h3>
              <p className="text-sm text-neutral-400">
                Recommends optimal charts and visualizations to represent the
                insights discovered by analysis agents.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-lime-400 mb-1">
                Data Storyteller
              </h3>
              <p className="text-sm text-neutral-400">
                Synthesizes all insights into a cohesive, markdown-formatted
                narrative with actionable recommendations.
              </p>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
