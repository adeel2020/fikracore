"use client";

import React, { useState } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { 
  MessageSquare, 
  Settings, 
  Lightbulb, 
  Briefcase, 
  PieChart, 
  ArrowRight, 
  ChevronRight, 
  TrendingUp, 
  Compass, 
  Clock, 
  Activity 
} from "lucide-react";

// ==========================================
// 1. STEP FLOWER PROCESS INFOGRAPHIC
// ==========================================
export function StepFlowerProcess() {
  const [activeStep, setActiveStep] = useState<number | null>(null);

  const steps = [
    {
      id: 1,
      title: "Step 01",
      subtitle: "Ingress Protocol",
      desc: "Telemetry packets ingested via edge user-plane interfaces.",
      icon: <MessageSquare className="w-5 h-5 text-cyan-400" />,
      color: "#00E5FF",
      angle: 0,
      x: 200,
      y: 110
    },
    {
      id: 2,
      title: "Step 02",
      subtitle: "Analysis Pipeline",
      desc: "AI engine extracts multi-variant incident signatures.",
      icon: <Settings className="w-5 h-5 text-emerald-400" />,
      color: "#34D399",
      angle: 72,
      x: 285,
      y: 172
    },
    {
      id: 3,
      title: "Step 03",
      subtitle: "Semantic Routing",
      desc: "Adjacency matching groups complaints into domains.",
      icon: <Lightbulb className="w-5 h-5 text-amber-400" />,
      color: "#FBBF24",
      angle: 144,
      x: 253,
      y: 273
    },
    {
      id: 4,
      title: "Step 04",
      subtitle: "SLA Containment",
      desc: "Preemptive tickets dispatched to mitigate breaches.",
      icon: <Briefcase className="w-5 h-5 text-rose-400" />,
      color: "#FB2B5E",
      angle: 216,
      x: 147,
      y: 273
    },
    {
      id: 5,
      title: "Step 05",
      subtitle: "Telemetry Archive",
      desc: "Closed loops stored in graph databases for vector memory.",
      icon: <PieChart className="w-5 h-5 text-purple-400" />,
      color: "#A78BFA",
      angle: 288,
      x: 115,
      y: 172
    }
  ];

  const currentStep = activeStep !== null ? steps[activeStep] : null;

  return (
    <GlassCard id="step-flower-card" className="p-4 w-[410px] h-[360px] flex flex-col justify-between" hover={false}>
      <style>{`
        @keyframes petalPulse {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 2px rgba(255,255,255,0.05)); }
          50% { transform: scale(1.05); filter: drop-shadow(0 0 8px var(--petal-glow)); }
        }
        .petal-animated {
          transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        .petal-animated:hover {
          transform: scale(1.1);
          filter: drop-shadow(0 0 12px var(--petal-glow));
          z-index: 20;
        }
        .flower-pulse-center {
          animation: centerPulse 3s infinite ease-in-out;
        }
        @keyframes centerPulse {
          0%, 100% { box-shadow: 0 0 10px rgba(0, 229, 255, 0.1); }
          50% { box-shadow: 0 0 25px rgba(0, 229, 255, 0.3); }
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
          5-Step Process Flower
        </span>
        <span className="text-[10px] text-neutral-400 font-mono">Interactive Nodes</span>
      </div>

      {/* Flower Canvas */}
      <div className="relative flex-1 flex items-center justify-center min-h-0">
        <svg className="w-64 h-64" viewBox="0 0 400 400">
          {/* Connecting Lines */}
          <circle cx="200" cy="200" r="90" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="4" strokeDasharray="6 4" />
          
          {/* Step Petals */}
          {steps.map((step, idx) => {
            const isActive = activeStep === idx;
            return (
              <g 
                key={step.id} 
                className="cursor-pointer petal-animated"
                style={{ "--petal-glow": step.color } as React.CSSProperties}
                onMouseEnter={() => setActiveStep(idx)}
                onMouseLeave={() => setActiveStep(null)}
              >
                {/* Petal Outer Glow Circle */}
                <circle 
                  cx={step.x} 
                  cy={step.y} 
                  r="45" 
                  fill={isActive ? `${step.color}25` : "rgba(255, 255, 255, 0.02)"} 
                  stroke={isActive ? step.color : "rgba(255, 255, 255, 0.1)"} 
                  strokeWidth="2.5" 
                />
                
                {/* Tiny Step Label inside */}
                <text 
                  x={step.x} 
                  y={step.y + 24} 
                  fill="rgba(255, 255, 255, 0.5)" 
                  fontSize="8" 
                  fontWeight="bold" 
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {step.title}
                </text>
              </g>
            );
          })}

          {/* Central Core Disk */}
          <circle 
            cx="200" 
            cy="200" 
            r="50" 
            fill="#0F172A" 
            stroke={currentStep ? currentStep.color : "rgba(255, 255, 255, 0.15)"} 
            strokeWidth="3.5"
            className="transition-colors duration-300"
          />
        </svg>

        {/* Central Core HTML Text Overlay */}
        <div className="absolute w-24 h-24 rounded-full flex flex-col items-center justify-center text-center pointer-events-none p-2">
          {currentStep ? (
            <div className="animate-in fade-in zoom-in duration-200">
              <div className="flex justify-center mb-1">{currentStep.icon}</div>
              <span className="text-[9px] font-bold text-white uppercase tracking-widest">{currentStep.title}</span>
            </div>
          ) : (
            <div className="animate-in fade-in duration-300">
              <span className="text-[10px] font-black bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent uppercase tracking-wider">
                Infographic
              </span>
              <div className="text-[7px] text-neutral-400 font-bold uppercase mt-1">Hover Petals</div>
            </div>
          )}
        </div>

        {/* Floating Icons positioned on top of the circles */}
        {steps.map((step, idx) => (
          <div 
            key={step.id}
            className="absolute pointer-events-none flex items-center justify-center w-8 h-8 rounded-full"
            style={{
              left: `calc(50% + ${(step.x - 200) * 0.72}px - 16px)`,
              top: `calc(50% + ${(step.y - 200) * 0.72}px - 16px)`
            }}
          >
            {step.icon}
          </div>
        ))}
      </div>

      {/* Description Panel */}
      <div className="bg-white/[0.02] border border-white/5 rounded-xl p-2.5 h-16 flex items-center transition-all duration-300">
        {currentStep ? (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 w-full">
            <div className="flex justify-between items-baseline mb-0.5">
              <h4 className="text-[11px] font-bold text-white tracking-wide uppercase">{currentStep.subtitle}</h4>
              <span className="text-[8px] font-bold px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${currentStep.color}15`, color: currentStep.color }}>
                Active
              </span>
            </div>
            <p className="text-[9.5px] text-neutral-400 leading-normal line-clamp-2">{currentStep.desc}</p>
          </div>
        ) : (
          <div className="text-center w-full py-1">
            <p className="text-[10.5px] text-neutral-500 font-medium italic">Hover over any step to explore operational vectors.</p>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

// ==========================================
// 2. CHEVRON OPTIONS CARDS INFOGRAPHIC
// ==========================================
export function ChevronOptionsList() {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const options = [
    {
      id: "01",
      title: "Data Stream Optimization",
      desc: "Compacts high-frequency telemetry headers at target edge clusters.",
      color: "from-cyan-500 to-blue-500",
      accent: "#06B6D4"
    },
    {
      id: "02",
      title: "Proactive Priority Enforcer",
      desc: "Escalates anomalous ticket indexes before SLA warning periods.",
      color: "from-emerald-500 to-teal-500",
      accent: "#10B981"
    },
    {
      id: "03",
      title: "SLA Rejection Classifier",
      desc: "Filters duplicate user complaints using NLP cluster sweeps.",
      color: "from-amber-500 to-orange-500",
      accent: "#F59E0B"
    },
    {
      id: "04",
      title: "Multi-Zone Load Balancer",
      desc: "Re-routes ingress pathways across redundant spatial pipelines.",
      color: "from-rose-500 to-purple-500",
      accent: "#EC4899"
    }
  ];

  return (
    <GlassCard id="chevron-options-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      <style>{`
        @keyframes chevronSlide {
          0% { transform: translateX(-4px); opacity: 0.3; }
          50% { transform: translateX(2px); opacity: 1; }
          100% { transform: translateX(-4px); opacity: 0.3; }
        }
        .chevron-active span {
          animation: chevronSlide 1s infinite ease-in-out;
        }
        .chevron-active span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .chevron-active span:nth-child(3) {
          animation-delay: 0.4s;
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <ChevronRight className="h-4 w-4 text-cyan-400" />
          Chevron Action Options
        </span>
        <span className="text-[10px] text-neutral-400 font-mono">Operations Deck</span>
      </div>

      {/* Stacked Options */}
      <div className="flex-1 flex flex-col gap-2.5 my-3 justify-center">
        {options.map((opt, idx) => {
          const isHovered = hoveredIdx === idx;
          return (
            <div
              key={opt.id}
              className={`relative flex items-center rounded-xl border p-2 transition-all duration-300 cursor-pointer overflow-hidden ${
                isHovered 
                  ? "bg-white/[0.04] border-white/15 translate-x-1" 
                  : "bg-white/[0.01] border-white/5"
              }`}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Colored side indicator */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b ${opt.color}`} />
              
              {/* Option Number Box with Left Chevron Styling */}
              <div className="flex items-center gap-2 flex-shrink-0 ml-1.5 mr-3">
                <div 
                  className={`w-9 h-9 rounded-lg flex flex-col items-center justify-center font-black text-sm relative transition-all duration-300 ${
                    isHovered 
                      ? "text-white shadow-[0_0_8px_rgba(255,255,255,0.1)]" 
                      : "text-neutral-400"
                  }`}
                  style={{ backgroundColor: isHovered ? opt.accent : "rgba(255,255,255,0.03)" }}
                >
                  <span className="text-[8px] font-bold opacity-60 leading-none">OPT</span>
                  <span className="leading-none">{opt.id}</span>
                </div>
                
                {/* Chevron Icons */}
                <div className={`flex gap-0.5 text-xs font-bold ${isHovered ? "chevron-active" : "opacity-35"}`} style={{ color: opt.accent }}>
                  <span>&gt;</span>
                  <span>&gt;</span>
                  <span>&gt;</span>
                </div>
              </div>

              {/* Text Area */}
              <div className="flex-1 min-w-0 pr-2">
                <h4 className={`text-[10.5px] font-bold tracking-wide uppercase transition-colors duration-200 ${isHovered ? "text-white" : "text-neutral-300"}`}>
                  {opt.title}
                </h4>
                <p className="text-[9.5px] text-neutral-400 truncate mt-0.5">
                  {opt.desc}
                </p>
              </div>

              {/* Action Button trigger */}
              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center border transition-all duration-300 mr-1 ${
                isHovered 
                  ? "bg-white/10 border-white/20 text-white scale-110" 
                  : "bg-transparent border-white/5 text-neutral-500"
              }`}>
                <ArrowRight size={10} className={`transition-transform duration-300 ${isHovered ? "translate-x-0.5" : ""}`} />
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

// ==========================================
// 3. LEAF STEP LIST INFOGRAPHIC
// ==========================================
export function LeafStepList() {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const leaves = [
    {
      id: "A",
      title: "Data A",
      metric: "75%",
      icon: <Compass className="w-4 h-4" />,
      desc: "Telemetry sync rate.",
      color: "from-cyan-400 to-blue-500",
      glow: "rgba(6, 182, 212, 0.4)"
    },
    {
      id: "B",
      title: "Data B",
      metric: "88%",
      icon: <Settings className="w-4 h-4" />,
      desc: "Thread scheduling index.",
      color: "from-purple-400 to-indigo-500",
      glow: "rgba(167, 139, 250, 0.4)"
    },
    {
      id: "C",
      title: "Data C",
      metric: "92%",
      icon: <PieChart className="w-4 h-4" />,
      desc: "Cache hit accuracy.",
      color: "from-rose-400 to-pink-500",
      glow: "rgba(244, 114, 182, 0.4)"
    },
    {
      id: "D",
      title: "Data D",
      metric: "64%",
      icon: <Lightbulb className="w-4 h-4" />,
      desc: "Anomaly trigger sweep.",
      color: "from-amber-400 to-orange-500",
      glow: "rgba(251, 191, 36, 0.4)"
    },
    {
      id: "E",
      title: "Data E",
      metric: "99%",
      icon: <Activity className="w-4 h-4" />,
      desc: "Core pipeline uptime.",
      color: "from-emerald-400 to-teal-500",
      glow: "rgba(52, 211, 153, 0.4)"
    }
  ];

  return (
    <GlassCard id="leaf-step-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Leaf Step Diagnostics
        </span>
        <span className="text-[10px] text-neutral-400 font-mono">Leaf Matrices</span>
      </div>

      {/* Leaf Grid Row */}
      <div className="flex-1 flex items-center justify-between gap-1.5 my-3">
        {leaves.map((leaf, idx) => {
          const isHovered = hoveredIdx === idx;
          return (
            <div
              key={leaf.id}
              className={`flex-1 flex flex-col items-center justify-between py-4 px-1 h-56 transition-all duration-300 cursor-pointer ${
                isHovered ? "-translate-y-2" : ""
              }`}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{
                borderRadius: "20px 20px 20px 0px", // Leaf shape
                background: isHovered ? "rgba(255, 255, 255, 0.05)" : "rgba(255, 255, 255, 0.015)",
                border: isHovered ? "1px solid rgba(255, 255, 255, 0.15)" : "1px solid rgba(255, 255, 255, 0.04)",
                boxShadow: isHovered ? `0 10px 20px ${leaf.glow}` : "none"
              }}
            >
              {/* Circular Icon bubble */}
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isHovered ? "scale-110 shadow-lg text-white" : "text-neutral-400"
                }`}
                style={{
                  background: isHovered 
                    ? `linear-gradient(135deg, ${leaf.glow.replace('0.4', '0.8')}, ${leaf.glow.replace('0.4', '0.2')})` 
                    : "rgba(255, 255, 255, 0.03)"
                }}
              >
                {leaf.icon}
              </div>

              {/* Value and Title */}
              <div className="text-center my-2">
                <span className="text-[16px] font-mono font-black text-white block leading-none tracking-tight">
                  {leaf.metric}
                </span>
                <span className="text-[8px] text-neutral-400 font-bold uppercase tracking-wider block mt-1">
                  {leaf.title}
                </span>
              </div>

              {/* Leaf Desc (only visible on hover or compact view) */}
              <div className="w-full px-1.5 text-center mt-auto">
                <p className={`text-[7.5px] leading-normal transition-all duration-300 ${
                  isHovered ? "text-neutral-300" : "text-neutral-500 opacity-60"
                }`}>
                  {leaf.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

// ==========================================
// 4. STATS RING METERS INFOGRAPHIC
// ==========================================
export function StatsRingMeters() {
  const [hoveredMeter, setHoveredMeter] = useState<number | null>(null);

  const meters = [
    {
      id: 1,
      label: "DATA A",
      value: 75,
      desc: "Core Bandwidth Load",
      color: "#00E5FF",
      dashArray: "188.4",
      icon: <TrendingUp className="w-4 h-4 text-cyan-400" />
    },
    {
      id: 2,
      label: "DATA B",
      value: 50,
      desc: "Incident Clean Rate",
      color: "#EC4899",
      dashArray: "188.4",
      icon: <Activity className="w-4 h-4 text-pink-400" />
    },
    {
      id: 3,
      label: "DATA C",
      value: 40,
      desc: "Vector Memory Load",
      color: "#FBBF24",
      dashArray: "188.4",
      icon: <Clock className="w-4 h-4 text-amber-400" />
    }
  ];

  return (
    <GlassCard id="stats-ring-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      <style>{`
        @keyframes ringSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .meter-spin-hover:hover .dashed-tracker {
          animation: ringSpin 15s linear infinite;
          transform-origin: 50% 50%;
        }
      `}</style>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <Activity className="h-4 w-4 text-cyan-400" />
          Radial Stats Rings
        </span>
        <span className="text-[10px] text-neutral-400 font-mono">Dotted Meters</span>
      </div>

      {/* Rings Layout */}
      <div className="flex-1 flex items-center justify-around gap-2 my-2">
        {meters.map((meter, idx) => {
          const isHovered = hoveredMeter === idx;
          const strokeDashoffset = parseFloat(meter.dashArray) - (parseFloat(meter.dashArray) * meter.value) / 100;
          
          return (
            <div
              key={meter.id}
              className="flex flex-col items-center cursor-pointer meter-spin-hover"
              onMouseEnter={() => setHoveredMeter(idx)}
              onMouseLeave={() => setHoveredMeter(null)}
            >
              {/* Circle Wrapper */}
              <div className="relative w-24 h-24 flex items-center justify-center transition-transform duration-300 hover:scale-105">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
                  {/* Outer Dotted ring guide */}
                  <circle
                    className="dashed-tracker"
                    cx="40"
                    cy="40"
                    r="34"
                    stroke="rgba(255, 255, 255, 0.05)"
                    strokeWidth="1.5"
                    strokeDasharray="4 2"
                    fill="transparent"
                  />
                  {/* Outer Active Progress Ring */}
                  <circle
                    cx="40"
                    cy="40"
                    r="30"
                    stroke={isHovered ? meter.color : `${meter.color}95`}
                    strokeWidth="4"
                    strokeDasharray={meter.dashArray}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-1000 ease-out"
                  />
                  {/* Dotted indicator (Ring from attached image) */}
                  <circle
                    cx="40"
                    cy="40"
                    r="26"
                    stroke={`${meter.color}20`}
                    strokeWidth="1"
                    strokeDasharray="2 3"
                    fill="transparent"
                  />
                </svg>
                
                {/* Center text values */}
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-[16px] font-mono font-black text-white leading-none">
                    {meter.value}%
                  </span>
                  <span className="text-[7.5px] text-neutral-400 font-extrabold uppercase mt-1 tracking-widest">
                    {meter.label}
                  </span>
                </div>
              </div>

              {/* Title label */}
              <div className="text-center mt-3 max-w-[110px]">
                <h5 className={`text-[10px] font-bold uppercase transition-colors duration-200 ${
                  isHovered ? "text-white" : "text-neutral-300"
                }`}>
                  {meter.label}
                </h5>
                <p className="text-[8px] text-neutral-500 mt-0.5 line-clamp-1">{meter.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      <div className="bg-white/[0.02] border border-white/5 rounded-xl p-2 flex items-center justify-between text-xs">
        <span className="text-[10px] text-neutral-400 font-semibold uppercase">Aggregated Flow Accuracy</span>
        <span className="font-mono text-emerald-400 font-bold uppercase tracking-wider">99.85% Optimal</span>
      </div>
    </GlassCard>
  );
}

// ==========================================
// 5. ARROW BAR LIST INFOGRAPHIC
// ==========================================
export function ArrowBarList() {
  const [activeBar, setActiveBar] = useState<number | null>(null);

  const bars = [
    { id: 1, label: "DATA 01", val15: 45, val20: 82, color: "from-cyan-500 to-teal-400", hex: "#00E5FF" },
    { id: 2, label: "DATA 02", val15: 35, val20: 95, color: "from-amber-500 to-orange-400", hex: "#FBBF24" },
    { id: 3, label: "DATA 03", val15: 60, val20: 75, color: "from-rose-500 to-pink-400", hex: "#FB2B5E" },
    { id: 4, label: "DATA 04", val15: 20, val20: 68, color: "from-purple-500 to-indigo-400", hex: "#A78BFA" },
    { id: 5, label: "DATA 05", val15: 55, val20: 90, color: "from-emerald-500 to-teal-400", hex: "#34D399" }
  ];

  return (
    <GlassCard id="arrow-bar-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <TrendingUp className="h-4 w-4 text-cyan-400" />
          Arrow Bar Comparison
        </span>
        <div className="flex items-center gap-3 text-[9px] font-bold text-neutral-400">
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-white/30" /> 2015
          </div>
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" /> 2020
          </div>
        </div>
      </div>

      {/* Stacked Arrow Bars */}
      <div className="flex-1 flex flex-col gap-2.5 my-3 justify-center">
        {bars.map((bar, idx) => {
          const isActive = activeBar === idx;
          return (
            <div
              key={bar.id}
              className="flex items-center gap-2 cursor-pointer"
              onMouseEnter={() => setActiveBar(idx)}
              onMouseLeave={() => setActiveBar(null)}
            >
              {/* Arrow Head Label */}
              <div 
                className={`w-14 py-1.5 text-center text-[9px] font-black rounded-lg transition-all duration-300 ${
                  isActive ? "text-white" : "text-neutral-400 bg-white/5 border border-white/5"
                }`}
                style={{ 
                  backgroundColor: isActive ? bar.hex : "rgba(255, 255, 255, 0.02)",
                  boxShadow: isActive ? `0 0 10px ${bar.hex}40` : "none"
                }}
              >
                {bar.label}
              </div>

              {/* Progress arrow track */}
              <div className="flex-1 h-5 bg-white/[0.02] border border-white/5 rounded-md relative overflow-hidden">
                {/* 2015 value bar */}
                <div 
                  className="absolute left-0 top-0 bottom-0 bg-white/10 transition-all duration-1000 ease-out"
                  style={{ 
                    width: `${bar.val15}%`,
                    clipPath: "polygon(0% 0%, calc(100% - 6px) 0%, 100% 50%, calc(100% - 6px) 100%, 0% 100%)"
                  }}
                />
                
                {/* 2020 active value bar */}
                <div 
                  className={`absolute left-0 top-0 bottom-0 bg-gradient-to-r ${bar.color} transition-all duration-1000 ease-out`}
                  style={{ 
                    width: `${bar.val20}%`,
                    clipPath: "polygon(0% 0%, calc(100% - 6px) 0%, 100% 50%, calc(100% - 6px) 100%, 0% 100%)"
                  }}
                />

                {/* Values overlay text */}
                <div className="absolute inset-0 flex items-center justify-between px-2 text-[8px] font-mono font-bold text-white pointer-events-none">
                  <span>{bar.val15}%</span>
                  <span className="bg-black/40 px-1 rounded">{bar.val20}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}

// ==========================================
// 6. TIMELINE STEMS INFOGRAPHIC
// ==========================================
export function TimelineStems() {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const timeline = [
    {
      id: 1,
      year: "2018",
      title: "Seed Phase",
      height: 35, // Stem height in percent
      desc: "Initial AI routing prototypes deployed.",
      color: "rgba(6, 182, 212, 1)",
      hexColor: "#06B6D4"
    },
    {
      id: 2,
      year: "2019",
      title: "Adjacency Maps",
      height: 60,
      desc: "Semantic connectivity engine optimized to O(1) searches.",
      color: "rgba(167, 139, 250, 1)",
      hexColor: "#A78BFA"
    },
    {
      id: 3,
      year: "2020",
      title: "Telemetry Scale",
      height: 45,
      desc: "Added distributed multi-variant warning nodes.",
      color: "rgba(244, 114, 182, 1)",
      hexColor: "#F472B6"
    },
    {
      id: 4,
      year: "2021",
      title: "SLA Automations",
      height: 75,
      desc: "Automated routing triggers reach sub-second execution.",
      color: "rgba(52, 211, 153, 1)",
      hexColor: "#34D399"
    }
  ];

  return (
    <GlassCard id="timeline-stems-card" className="p-4 w-[410px] h-[340px] flex flex-col justify-between" hover={false}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <span className="text-xs font-bold text-white tracking-wider uppercase flex items-center gap-1.5">
          <Clock className="h-4 w-4 text-cyan-400" />
          Timeline Stems
        </span>
        <span className="text-[10px] text-neutral-400 font-mono">Sequential Milestones</span>
      </div>

      {/* Timeline stems container */}
      <div className="flex-1 flex items-end justify-between px-3 h-44 my-2 relative">
        {/* Horizontal base timeline wire */}
        <div className="absolute bottom-6 left-6 right-6 h-0.5 bg-white/10" />

        {timeline.map((item, idx) => {
          const isHovered = hoveredIdx === idx;
          return (
            <div
              key={item.id}
              className="flex flex-col items-center cursor-pointer relative group flex-1"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              {/* Year Bubble */}
              <div 
                className={`w-11 h-11 rounded-full flex items-center justify-center font-mono font-black text-[11px] transition-all duration-300 z-10 ${
                  isHovered 
                    ? "scale-115 text-white shadow-[0_0_12px_rgba(255,255,255,0.2)]" 
                    : "text-neutral-400 bg-white/5 border border-white/10"
                }`}
                style={{ 
                  backgroundColor: isHovered ? item.hexColor : "rgba(255, 255, 255, 0.02)",
                  transform: isHovered ? `translateY(-${item.height}px) scale(1.15)` : `translateY(-${item.height}px)`
                }}
              >
                {item.year}
              </div>

              {/* Vertical stem line */}
              <div 
                className="absolute w-0.5 bg-white/10 bottom-6 transition-all duration-300 origin-bottom"
                style={{
                  height: `${item.height}px`,
                  backgroundColor: isHovered ? item.hexColor : "rgba(255, 255, 255, 0.15)",
                  boxShadow: isHovered ? `0 0 8px ${item.hexColor}` : "none"
                }}
              />

              {/* Step indicator node on timeline */}
              <div 
                className={`absolute bottom-[18px] w-2.5 h-2.5 rounded-full transition-all duration-300 z-10 border-2 border-[#090D16] ${
                  isHovered ? "scale-125" : ""
                }`}
                style={{ backgroundColor: isHovered ? item.hexColor : "rgba(255, 255, 255, 0.3)" }}
              />

              {/* Label bottom */}
              <div className="absolute -bottom-1 text-center w-full">
                <span className={`text-[8.5px] font-black uppercase tracking-wider block transition-colors duration-200 ${
                  isHovered ? "text-white" : "text-neutral-400"
                }`}>
                  {item.title}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Floating Milestone Narrative Details */}
      <div className="bg-white/[0.02] border border-white/5 rounded-xl p-2.5 h-14 flex items-center transition-all duration-300">
        {hoveredIdx !== null ? (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300 w-full">
            <h5 className="text-[10px] font-bold text-white uppercase tracking-wider mb-0.5 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: timeline[hoveredIdx].hexColor }} />
              {timeline[hoveredIdx].year} — {timeline[hoveredIdx].title}
            </h5>
            <p className="text-[9px] text-neutral-400 leading-normal line-clamp-1">{timeline[hoveredIdx].desc}</p>
          </div>
        ) : (
          <div className="text-center w-full py-1">
            <p className="text-[10px] text-neutral-500 font-medium italic">Hover milestone bubbles to trace chronological progress.</p>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
