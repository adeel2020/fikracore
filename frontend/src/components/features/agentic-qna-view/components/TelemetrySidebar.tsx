"use client";

import React from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/utils";
import { TelemetryRing } from "./shared/TelemetryRing";
import { LinearProgressMeter } from "./shared/LinearProgressMeter";
import { SpeedometerGauge } from "./shared/SpeedometerGauge";
import { AnimatedNumber } from "./shared/AnimatedNumber";

interface TelemetrySidebarProps {
  telemetry: {
    memoryPct: number;
    cachePct: number;
    tokens: number;
    cost: number;
    throughput: number;
    latency: number;
    contextUsed: number;
    contextWindow: string;
  };
}

export function TelemetrySidebar({ telemetry }: TelemetrySidebarProps) {
  return (
    <GlassCard className="flex flex-col gap-6 p-6 h-full w-[360px] overflow-y-auto overflow-x-hidden scrollbar-none [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]" hover={false}>
      <div>
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Performance</h3>
        <p className="mt-1 text-xs text-neutral-400">Memory & cache utilization</p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <TelemetryRing label="Memory" value={telemetry.memoryPct} type="memory" />
          <TelemetryRing label="Cache" value={telemetry.cachePct} type="cache" />
        </div>
      </div>
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Token Usage</h3>
        <LinearProgressMeter
          label="Tokens Consumed"
          value={telemetry.tokens}
          max={50000}
          unit="tokens"
          color="#00E5FF"
        />
        <div className="rounded-xl border border-cyan-500/30 bg-black/40 p-4 transition-all duration-500 hover:border-cyan-500/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
              Estimated Cost
            </span>
            <span className="text-lg">💰</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400 transition-all duration-500">
            ${telemetry.cost.toFixed(4)}
            <span className="ml-1 text-xs text-neutral-400 font-sans font-normal">USD</span>
          </div>
        </div>
        <SpeedometerGauge
          label="Throughput"
          value={telemetry.throughput}
          max={100}
          unit=" T/s"
          color="#00FF88"
        />
      </div>
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Session Info</h3>
        <div className="space-y-3 text-xs">
          <div className="flex justify-between items-center text-neutral-400 border-b border-white/5 pb-2">
            <span>Context Window</span>
            <span className="font-semibold text-white font-mono">{telemetry.contextWindow}</span>
          </div>
          <div className="flex justify-between items-center text-neutral-400 border-b border-white/5 pb-2">
            <span className="flex items-center gap-1.5">
              Latency
              {telemetry.latency > 0 && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              )}
            </span>
            <span
              className={cn(
                "font-semibold font-mono transition-all duration-500",
                telemetry.latency > 0 ? "text-emerald-400" : "text-neutral-500"
              )}
            >
              {telemetry.latency > 0 ? `${telemetry.latency}ms` : "—"}
            </span>
          </div>
          <div className="flex justify-between items-center text-neutral-400 border-b border-white/5 pb-2">
            <span>Estimated Tokens</span>
            <span className="font-semibold text-white font-mono">
              <AnimatedNumber value={telemetry.contextUsed} /> / 50,000 tokens
            </span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
