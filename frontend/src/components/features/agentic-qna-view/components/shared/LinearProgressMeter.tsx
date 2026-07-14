"use client";

import React from "react";
import { AnimatedNumber } from "./AnimatedNumber";

interface LinearProgressMeterProps {
  label: string;
  value: number;
  max: number;
  unit: string;
  color: string;
}

export function LinearProgressMeter({
  label,
  value,
  max,
  unit,
  color,
}: LinearProgressMeterProps) {
  const percentage = Math.min((value / max) * 100, 100);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
          {label}
        </span>
        <span className="text-sm font-semibold text-white font-mono">
          <AnimatedNumber value={value} /> / {max.toLocaleString()} {unit}
        </span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/5 border border-white/5 p-[1px]">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color}, ${color}dd)`,
          }}
        />
      </div>
    </div>
  );
}
