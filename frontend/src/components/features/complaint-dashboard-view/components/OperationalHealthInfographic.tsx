"use client";

import React, { useState } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Activity, ShieldAlert, Wifi, Cpu, Layers, Disc } from "lucide-react";

interface MetricItem {
  label: string;
  value: string;
  trend: "up" | "down" | "stable";
  pct: string;
  color: string;
  sparkline: number[];
}

export function OperationalHealthInfographic() {
  const [activeTab, setActiveTab] = useState<"infrastructure" | "signal" | "load">("infrastructure");

  // Multi-variant dataset to show dynamic stats depending on the user's toggle
  const datasets = {
    infrastructure: {
      healthScore: 98.4,
      status: "Optimal",
      metrics: [
        { label: "DNS Resolution", value: "9.2 ms", trend: "down", pct: "-4.2%", color: "#00E5FF", sparkline: [12, 11, 10, 9.8, 9.5, 9.2] },
        { label: "Core Processing Load", value: "34.1%", trend: "stable", pct: "+0.1%", color: "#A78BFA", sparkline: [33.8, 34.0, 33.9, 34.2, 34.1, 34.1] },
        { label: "BGP Convergence Rate", value: "99.99%", trend: "up", pct: "+0.02%", color: "#34D399", sparkline: [99.8, 99.85, 99.9, 99.92, 99.95, 99.99] },
        { label: "API Gateway Latency", value: "18.5 ms", trend: "down", pct: "-1.8%", color: "#60A5FA", sparkline: [21, 20.2, 19.5, 19.1, 18.8, 18.5] },
      ] as MetricItem[]
    },
    signal: {
      healthScore: 94.8,
      status: "Steady",
      metrics: [
        { label: "Signal-to-Noise (SINR)", value: "22.4 dB", trend: "up", pct: "+1.2 dB", color: "#34D399", sparkline: [20.5, 21.0, 21.4, 21.8, 22.1, 22.4] },
        { label: "Jitter Frequency", value: "1.42 ms", trend: "down", pct: "-0.15ms", color: "#00E5FF", sparkline: [1.6, 1.55, 1.5, 1.48, 1.45, 1.42] },
        { label: "Packet Retransmission", value: "0.008%", trend: "down", pct: "-0.002%", color: "#60A5FA", sparkline: [0.012, 0.011, 0.009, 0.009, 0.008, 0.008] },
        { label: "VoLTE Session Setup Time", value: "1.18 s", trend: "down", pct: "-0.12s", color: "#F472B6", sparkline: [1.32, 1.28, 1.25, 1.22, 1.2, 1.18] },
      ] as MetricItem[]
    },
    load: {
      healthScore: 89.2,
      status: "High Capacity",
      metrics: [
        { label: "Active User Plane", value: "2.84M sessions", trend: "up", pct: "+11.4%", color: "#FB2B5E", sparkline: [2.5, 2.58, 2.65, 2.71, 2.78, 2.84] },
        { label: "Throughput (EGRESS)", value: "482 Gbps", trend: "up", pct: "+8.7%", color: "#00E5FF", sparkline: [440, 448, 455, 468, 474, 482] },
        { label: "Cell Congestion Index", value: "1.24%", trend: "up", pct: "+0.18%", color: "#FBBF24", sparkline: [1.02, 1.08, 1.12, 1.18, 1.21, 1.24] },
        { label: "S-GW Control Buffer", value: "42.8%", trend: "stable", pct: "+1.2%", color: "#A78BFA", sparkline: [41.2, 41.8, 42.1, 42.5, 42.6, 42.8] },
      ] as MetricItem[]
    }
  };

  const currentData = datasets[activeTab];

  // Helper to generate coordinates for sparkline SVG paths
  const generateSparklinePath = (points: number[]) => {
    const width = 80;
    const height = 24;
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min === 0 ? 1 : max - min;
    
    return points
      .map((val, idx) => {
        const x = (idx / (points.length - 1)) * width;
        const y = height - ((val - min) / range) * height;
        return `${idx === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  };

  return (
    <GlassCard id="operational-health-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      {/* Styles for dynamic gauges and sparkles */}
      <style>{`
        @keyframes rotateGauge {
          from { transform: rotate(-90deg); }
          to { transform: rotate(0deg); }
        }
        @keyframes pulseDot {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.2); }
        }
        .glowing-dot {
          animation: pulseDot 2s infinite ease-in-out;
        }
        .gauge-glowing {
          animation: rotateGauge 1.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          transform-origin: 50% 50%;
        }
      `}</style>

      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-bold text-white tracking-wider uppercase">System Health Index</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase tracking-widest">LIVE</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-white/5 p-0.5 rounded-lg my-2 gap-0.5">
        {(["infrastructure", "signal", "load"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 text-[9px] font-bold uppercase tracking-wider py-1.5 rounded-md transition-all ${
              activeTab === tab
                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Core Visualization & Gauge */}
      <div className="flex items-center gap-4 flex-1 my-1">
        {/* Neon Gauge */}
        <div className="relative w-28 h-28 flex-shrink-0 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            {/* Background ring */}
            <circle
              cx="50"
              cy="50"
              r="40"
              stroke="rgba(255, 255, 255, 0.05)"
              strokeWidth="6"
              fill="transparent"
            />
            {/* Progress ring */}
            <circle
              className="gauge-glowing"
              cx="50"
              cy="50"
              r="40"
              stroke={`url(#healthGradient-${activeTab})`}
              strokeWidth="6"
              fill="transparent"
              strokeDasharray={`${(currentData.healthScore / 100) * 251.2} 251.2`}
              strokeLinecap="round"
            />
            <defs>
              <linearGradient id={`healthGradient-infrastructure`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00E5FF" />
                <stop offset="100%" stopColor="#34D399" />
              </linearGradient>
              <linearGradient id={`healthGradient-signal`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#60A5FA" />
                <stop offset="100%" stopColor="#00E5FF" />
              </linearGradient>
              <linearGradient id={`healthGradient-load`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FBBF24" />
                <stop offset="100%" stopColor="#FB2B5E" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute flex flex-col items-center justify-center">
            <span className="text-[20px] font-mono font-black text-white leading-none">
              {currentData.healthScore}%
            </span>
            <span className="text-[8px] text-neutral-400 font-bold uppercase tracking-wider mt-1">
              {currentData.status}
            </span>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="flex-1 flex flex-col gap-2 justify-center">
          <div className="bg-white/[0.02] border border-white/5 rounded-lg p-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu size={12} className="text-purple-400" />
              <span className="text-[10px] text-neutral-300 font-medium">Telemetry Nodes</span>
            </div>
            <span className="text-[10px] font-mono text-white font-bold">128 / 128 Online</span>
          </div>
          <div className="bg-white/[0.02] border border-white/5 rounded-lg p-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers size={12} className="text-emerald-400" />
              <span className="text-[10px] text-neutral-300 font-medium">Ingress Queue Status</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 font-bold">Clear</span>
          </div>
          <div className="bg-white/[0.02] border border-white/5 rounded-lg p-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert size={12} className="text-cyan-400" />
              <span className="text-[10px] text-neutral-300 font-medium">Incident Signatures</span>
            </div>
            <span className="text-[10px] font-mono text-white font-bold">0 Active Severity-1</span>
          </div>
        </div>
      </div>

      {/* Grid Metrics List */}
      <div className="grid grid-cols-2 gap-2 border-t border-white/5 pt-2">
        {currentData.metrics.map((item, idx) => (
          <div 
            key={idx} 
            className="bg-white/[0.01] hover:bg-white/[0.03] border border-white/5 rounded-lg p-2 flex flex-col justify-between transition-colors h-[64px]"
          >
            <div className="flex items-start justify-between gap-1">
              <span className="text-[9px] text-neutral-400 font-semibold truncate flex-1 leading-tight">{item.label}</span>
              <span className={`text-[8px] font-mono font-bold leading-none ${
                item.trend === "down" ? "text-emerald-400" : item.trend === "up" ? "text-rose-400" : "text-neutral-400"
              }`}>
                {item.pct}
              </span>
            </div>
            <div className="flex items-end justify-between mt-1">
              <span className="text-[12px] font-mono font-bold text-white leading-none">{item.value}</span>
              
              {/* Animated SVG Sparkline */}
              <svg className="w-14 h-5 overflow-visible" viewBox="0 0 80 24">
                <path
                  d={generateSparklinePath(item.sparkline)}
                  fill="none"
                  stroke={item.color}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
