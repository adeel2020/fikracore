"use client";

import React from "react";

interface HudRingProps {
  size?: number | string;
  className?: string;
  speed?: "slow" | "medium" | "fast";
  reverse?: boolean;
  variant?: "dashed" | "tech" | "ticks" | "concentric" | "outer-orbit";
}

export function HudRing({
  size = 500,
  className = "",
  speed = "slow",
  reverse = false,
  variant = "tech",
}: HudRingProps) {
  const durationClass =
    speed === "fast"
      ? "hud-spin-fast"
      : speed === "medium"
      ? "hud-spin-medium"
      : "hud-spin-slow";

  const directionClass = reverse ? "hud-spin-reverse" : "";

  if (variant === "dashed") {
    return (
      <svg
        viewBox="0 0 500 500"
        className={`absolute pointer-events-none ${durationClass} ${directionClass} ${className}`}
        style={{ width: size, height: size }}
      >
        <circle
          cx="250"
          cy="250"
          r="230"
          fill="none"
          stroke="#38bdf8"
          strokeWidth="1.5"
          strokeDasharray="8 14"
          strokeOpacity="0.45"
        />
        <circle
          cx="250"
          cy="250"
          r="242"
          fill="none"
          stroke="#0284c7"
          strokeWidth="1"
          strokeDasharray="4 26"
          strokeOpacity="0.3"
        />
      </svg>
    );
  }

  if (variant === "ticks") {
    const ticks = Array.from({ length: 48 });
    return (
      <svg
        viewBox="0 0 500 500"
        className={`absolute pointer-events-none ${durationClass} ${directionClass} ${className}`}
        style={{ width: size, height: size }}
      >
        {ticks.map((_, i) => (
          <line
            key={i}
            x1="250"
            y1={i % 4 === 0 ? "18" : "26"}
            x2="250"
            y2="34"
            transform={`rotate(${i * 7.5} 250 250)`}
            stroke="#0ea5e9"
            strokeWidth={i % 4 === 0 ? "1.8" : "1"}
            strokeOpacity={i % 4 === 0 ? "0.6" : "0.3"}
          />
        ))}
      </svg>
    );
  }

  if (variant === "concentric") {
    return (
      <svg
        viewBox="0 0 500 500"
        className={`absolute pointer-events-none ${className}`}
        style={{ width: size, height: size }}
      >
        <circle
          cx="250"
          cy="250"
          r="210"
          fill="none"
          stroke="#60a5fa"
          strokeWidth="1"
          strokeOpacity="0.22"
        />
        <circle
          cx="250"
          cy="250"
          r="160"
          fill="none"
          stroke="#38bdf8"
          strokeWidth="1"
          strokeOpacity="0.28"
        />
        <circle
          cx="250"
          cy="250"
          r="110"
          fill="none"
          stroke="#818cf8"
          strokeWidth="1.2"
          strokeOpacity="0.32"
        />
      </svg>
    );
  }

  if (variant === "outer-orbit") {
    return (
      <svg
        viewBox="0 0 600 600"
        className={`absolute pointer-events-none ${durationClass} ${directionClass} ${className}`}
        style={{ width: size, height: size }}
      >
        <circle
          cx="300"
          cy="300"
          r="285"
          fill="none"
          stroke="#93c5fd"
          strokeWidth="1.2"
          strokeDasharray="12 18"
          strokeOpacity="0.4"
        />
        <circle
          cx="300"
          cy="300"
          r="265"
          fill="none"
          stroke="#38bdf8"
          strokeWidth="0.8"
          strokeOpacity="0.25"
        />
        {/* 4 Cardinal cross markers */}
        <circle cx="300" cy="15" r="3.5" fill="#0284c7" />
        <circle cx="585" cy="300" r="3.5" fill="#0284c7" />
        <circle cx="300" cy="585" r="3.5" fill="#0284c7" />
        <circle cx="15" cy="300" r="3.5" fill="#0284c7" />
      </svg>
    );
  }

  // Default: tech ring with arcs, notches, and glowing points
  return (
    <svg
      viewBox="0 0 500 500"
      className={`absolute pointer-events-none ${durationClass} ${directionClass} ${className}`}
      style={{ width: size, height: size }}
    >
      <defs>
        <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.75" />
          <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.65" />
        </linearGradient>
      </defs>

      {/* Main segmented arc */}
      <circle
        cx="250"
        cy="250"
        r="210"
        fill="none"
        stroke="url(#ringGrad)"
        strokeWidth="1.8"
        strokeDasharray="160 30 90 20 220 40"
        strokeLinecap="round"
      />

      {/* Outer corner notches */}
      <path
        d="M 250 25 A 225 225 0 0 1 290 29"
        fill="none"
        stroke="#0284c7"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M 250 475 A 225 225 0 0 1 210 471"
        fill="none"
        stroke="#0284c7"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M 25 250 A 225 225 0 0 1 29 210"
        fill="none"
        stroke="#0284c7"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M 475 250 A 225 225 0 0 1 471 290"
        fill="none"
        stroke="#0284c7"
        strokeWidth="3"
        strokeLinecap="round"
      />

      {/* Small satellite tracking dots */}
      <circle cx="250" cy="40" r="3" fill="#38bdf8" />
      <circle cx="250" cy="460" r="3" fill="#818cf8" />
      <circle cx="40" cy="250" r="3" fill="#38bdf8" />
      <circle cx="460" cy="250" r="3" fill="#a855f7" />
    </svg>
  );
}
