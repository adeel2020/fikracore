"use client";

import React from "react";
import type { LucideIcon } from "lucide-react";

interface HudOrbProps {
  id: string;
  label: string;
  icon: LucideIcon;
  positionStyle: React.CSSProperties;
  floatClass?: string;
  count?: string | number;
  statusColor?: string;
  isActive?: boolean;
  onClick?: () => void;
}

export function HudOrb({
  id,
  label,
  icon: Icon,
  positionStyle,
  floatClass = "hud-float-1",
  count,
  statusColor = "#0a66ff",
  isActive = false,
  onClick,
}: HudOrbProps) {
  return (
    <div
      className={`absolute z-20 flex flex-col items-center ${floatClass}`}
      style={positionStyle}
      onClick={onClick}
    >
      {/* Interactive Hologram Sphere */}
      <div
        className={`hud-orb group relative ${
          isActive ? "ring-2 ring-cyan-400 shadow-[0_0_35px_rgba(0,229,255,0.6)]" : ""
        }`}
        title={`Inspect ${label}`}
      >
        {/* Subtle glowing ring inside orb */}
        <div className="absolute inset-2 rounded-full border border-cyan-400/40 pointer-events-none" />

        {/* Central Icon */}
        <Icon
          className="h-7 w-7 text-[#0a66ff] dark:text-[#00e5ff] transition-transform duration-300 group-hover:scale-110 drop-shadow-[0_0_10px_rgba(0,229,255,0.7)]"
          strokeWidth={2}
        />

        {/* Optional Count / Status Badge */}
        {count !== undefined && (
          <span
            className="absolute -top-1 -right-1 text-[9.5px] font-black px-1.5 py-0.5 rounded-full bg-white dark:bg-slate-900 text-blue-700 dark:text-cyan-400 border border-blue-200 dark:border-cyan-500/40 shadow-sm"
          >
            {count}
          </span>
        )}
      </div>

      {/* Label Underneath with High-Contrast Pill Badge */}
      <div className="mt-2 text-center pointer-events-none">
        <span className="text-[10px] font-black uppercase tracking-wider text-[#082863] dark:text-cyan-300 block whitespace-nowrap px-2 py-0.5 rounded-md bg-white/90 dark:bg-slate-900/90 border border-blue-200/70 dark:border-cyan-500/40 shadow-sm">
          {label}
        </span>
      </div>
    </div>
  );
}
