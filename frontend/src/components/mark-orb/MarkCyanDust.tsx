"use client";

import { useMemo } from "react";
import type { MarkVisualState } from "@/lib/mark-capability-graph";
import { useMarkHud } from "@/lib/mark-hud-context";

type DustParticle = {
  cx: string;
  cy: string;
  r: string;
  color: string;
  delay: string;
  duration: string;
  variant: number;
};

function seededRandom(seed: number) {
  const next = (seed * 9301 + 49297) % 233280;
  return [next / 233280, next] as const;
}

// 100% pure cyan spectrum - no white dust
const CYAN_DUST_COLORS = [
  "#00f0ff", // Intense electric cyan
  "#00e5ff", // Pure radiant cyan
  "#22d3ee", // Vivid bright cyan
  "#38bdf8", // Glowing cyber cyan
  "#67e8f9", // Crisp neon cyan
];

// Fallback constant
export const DUST_MAX_RADIUS = 115;

function makeDust(count: number, maxRadius: number, speed: number) {
  const dust: DustParticle[] = [];
  let seed = 142;
  const effectiveSpeed = Math.max(0.15, speed);

  for (let i = 0; i < count; i += 1) {
    const r1 = seededRandom(seed);
    seed = r1[1];
    const r2 = seededRandom(seed);
    seed = r2[1];
    const r3 = seededRandom(seed);
    seed = r3[1];
    const r4 = seededRandom(seed);
    seed = r4[1];

    const angle = r1[0] * Math.PI * 2;
    // Radius control: Math.pow(r2[0], 1.7) shapes density towards center while expanding to maxRadius
    const radius = Math.pow(r2[0], 1.7) * maxRadius;
    const cx = 450 + Math.cos(angle) * radius * (0.95 + r3[0] * 0.1);
    const cy = 450 + Math.sin(angle) * radius * (0.95 + r4[0] * 0.1);
    const size = 0.35 + r3[0] * 0.95;

    // Pick color strictly from the cyan spectrum
    const colorIndex = Math.floor(r4[0] * CYAN_DUST_COLORS.length);
    const color = CYAN_DUST_COLORS[colorIndex % CYAN_DUST_COLORS.length];

    // Smooth, slowed-down glittering durations scaled by speed setting
    const baseDuration = 2.4 + r3[0] * 2.6;
    const duration = (baseDuration / effectiveSpeed).toFixed(2) + "s";
    const delay = ((r1[0] * 4.0) / effectiveSpeed).toFixed(2) + "s";
    const variant = i % 4;

    dust.push({
      cx: cx.toFixed(2),
      cy: cy.toFixed(2),
      r: size.toFixed(2),
      color,
      delay,
      duration,
      variant,
    });
  }

  return dust;
}

function stateOpacity(state: MarkVisualState) {
  if (state === "processing" || state === "investigating") return 0.94;
  if (state === "speaking" || state === "learning") return 0.88;
  if (state === "listening") return 0.84;
  return 0.8;
}

export function MarkCyanDust({ state }: { state: MarkVisualState }) {
  const { settings } = useMarkHud();
  const radius = settings.dustRadius ?? 115;
  const speed = settings.dustSpeed ?? 1.0;
  const count = settings.dustCount ?? 780;
  const glow = settings.dustGlowIntensity ?? 1.0;
  const coreGlow = settings.dustCoreGlow ?? 1.0;

  const dust = useMemo(() => makeDust(count, radius, speed), [count, radius, speed]);

  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 900 900"
      className="absolute inset-0 h-full w-full pointer-events-none"
      style={{
        opacity: stateOpacity(state),
        transition: "opacity 500ms ease",
        mixBlendMode: "screen",
      }}
    >
      <defs>
        {/* Layered glowing cyan shine filter applied exclusively to the cyan dust */}
        <filter id="mark-cyan-dust-glow" x="-120%" y="-120%" width="340%" height="340%">
          <feGaussianBlur stdDeviation="1.6" in="SourceGraphic" result="blurNear" />
          <feGaussianBlur stdDeviation="3.4" in="SourceGraphic" result="blurFar" />
          <feFlood floodColor="#00f0ff" floodOpacity={0.85 * glow} result="cyanNearFlood" />
          <feComposite in="cyanNearFlood" in2="blurNear" operator="in" result="cyanGlowNear" />
          <feFlood floodColor="#00e5ff" floodOpacity={0.45 * glow} result="cyanFarFlood" />
          <feComposite in="cyanFarFlood" in2="blurFar" operator="in" result="cyanGlowFar" />
          <feMerge>
            <feMergeNode in="cyanGlowFar" />
            <feMergeNode in="cyanGlowNear" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <radialGradient id="mark-cyan-dust-core" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#00e5ff" stopOpacity={0.32 * coreGlow} />
          <stop offset="45%" stopColor="#00f0ff" stopOpacity={0.14 * coreGlow} />
          <stop offset="85%" stopColor="#0891b2" stopOpacity={0.03 * coreGlow} />
          <stop offset="100%" stopColor="#00e5ff" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="450" cy="450" r={radius} fill="url(#mark-cyan-dust-core)" />
      <g filter="url(#mark-cyan-dust-glow)">
        {dust.map((dot, index) => (
          <circle
            key={index}
            cx={dot.cx}
            cy={dot.cy}
            r={dot.r}
            fill={dot.color}
            className={`mark-cyan-dust mark-dust-twinkle-${dot.variant}`}
            style={{
              animationDuration: dot.duration,
              animationDelay: dot.delay,
            }}
          />
        ))}
      </g>
    </svg>
  );
}
