"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SpeedometerGaugeProps {
  label: string;
  value: number;
  max: number;
  unit: string;
  color: string;
}

export function SpeedometerGauge({
  label,
  value,
  max,
  unit,
  color,
}: SpeedometerGaugeProps) {
  const percentage = Math.min(value / max, 1);
  const rotation = percentage * 180 - 90;

  return (
    <div className="flex flex-col items-center gap-2 p-4 rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md transition-all duration-500 w-full">
      <div className="relative h-20 w-32">
        <svg className="h-20 w-32" viewBox="0 0 120 70">
          {/* Background arc */}
          <path
            d="M 10 60 A 50 50 0 0 1 110 60"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="5"
            strokeLinecap="round"
          />
          {/* Needle */}
          <line
            x1="60"
            y1="60"
            x2="60"
            y2="25"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            className="transition-transform duration-1000 ease-out"
            style={{
              transform: `rotate(${rotation}deg)`,
              transformOrigin: "60px 60px",
            }}
          />
          {/* Center dot */}
          <circle cx="60" cy="60" r="4.5" fill={color} />
        </svg>
        <span
          className={cn(
            "absolute inset-0 flex items-end justify-center pb-1 text-sm font-bold font-mono transition-all duration-500",
            value > 0 ? "animate-pulse text-cyan-400" : "text-neutral-500"
          )}
        >
          {value.toFixed(1)}
          {unit}
        </span>
      </div>
      <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
