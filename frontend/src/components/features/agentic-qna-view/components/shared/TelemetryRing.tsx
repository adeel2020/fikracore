"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface TelemetryRingProps {
  label: string;
  value: number;
  type: "memory" | "cache";
}

export function TelemetryRing({ label, value, type }: TelemetryRingProps) {
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (value / 100) * circumference;

  let colorClass = "text-cyan-500 stroke-cyan-500";
  let bgClass = "bg-cyan-500/5";

  if (type === "memory" && value > 80) {
    colorClass = "text-rose-500 stroke-rose-500";
    bgClass = "bg-rose-500/5";
  } else if (type === "cache" && value > 50) {
    colorClass = "text-emerald-500 stroke-emerald-500";
    bgClass = "bg-emerald-500/5";
  } else {
    colorClass = "text-cyan-500 stroke-cyan-500";
    bgClass = "bg-cyan-500/5";
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center gap-2 p-3 rounded-2xl border border-white/5 backdrop-blur-md transition-all duration-500",
        bgClass
      )}
    >
      <div className="relative h-24 w-24">
        <svg className="h-24 w-24 -rotate-90" viewBox="0 0 96 96">
          <circle
            cx="48"
            cy="48"
            r="36"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="6"
          />
          <circle
            cx="48"
            cy="48"
            r="36"
            fill="none"
            className={cn("transition-all duration-700 ease-out", colorClass)}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <span
          className={cn(
            "absolute inset-0 flex items-center justify-center text-lg font-bold font-mono transition-colors duration-500",
            colorClass
          )}
        >
          {value}%
        </span>
      </div>
      <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
