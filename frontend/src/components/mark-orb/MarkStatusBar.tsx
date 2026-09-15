"use client";

import type { MarkRouteTrace, MarkVisualState } from "@/lib/mark-capability-graph";
import "./mark-orb.css";

const GOLD = "#f5a623";
const GOLD_BRIGHT = "#ffd080";

function labelFor(state: MarkVisualState) {
  if (state === "listening") return "LISTENING";
  if (state === "processing") return "ANALYZING";
  if (state === "speaking") return "SPEAKING";
  if (state === "investigating") return "INVESTIGATING";
  if (state === "waiting_for_approval") return "APPROVAL REQUIRED";
  if (state === "learning") return "LEARNING";
  return "MARK READY";
}

function Waveform({ active, cx, cy, width = 170 }: { active: boolean; cx: number; cy: number; width?: number }) {
  const barCount = 28;
  const barW = 3;
  const gap = (width - barCount * barW) / (barCount - 1);

  return (
    <g>
      {Array.from({ length: barCount }, (_, i) => {
        const x = cx - width / 2 + i * (barW + gap);
        const baseH = 3 + Math.abs(Math.sin(i * 0.6)) * 5;
        const activeH = 8 + Math.abs(Math.sin(i * 0.8)) * 26;
        const h = active ? activeH : baseH;
        const fixedX = x.toFixed(3);
        const fixedY = (cy - h / 2).toFixed(3);
        const fixedH = h.toFixed(3);
        const originX = (x + barW / 2).toFixed(3);
        return (
          <rect
            key={i}
            x={fixedX}
            y={fixedY}
            width={barW}
            height={fixedH}
            rx={1.5}
            fill={GOLD}
            opacity={active ? 0.85 : 0.3}
            style={{
              transformOrigin: `${originX}px ${cy}px`,
              animation: active ? `markStatusBar ${0.55 + (i % 5) * 0.16}s ease-in-out ${(i % 7) * 0.07}s infinite alternate` : "none",
            }}
          />
        );
      })}
    </g>
  );
}

export function MarkStatusBar({ state, trace }: { state: MarkVisualState; trace?: MarkRouteTrace | null }) {
  void trace;
  const width = 520;
  const height = 132;
  const cx = width / 2;
  const cy = 64;
  const active = state !== "idle";

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 8,
        display: "flex",
        justifyContent: "center",
        zIndex: 18,
        pointerEvents: "none",
      }}
    >
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} fill="none">
        <defs>
          <filter id="mark-status-blur" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <line x1={cx - 168} y1={cy} x2={cx - 28} y2={cy} stroke={GOLD} strokeWidth="1" opacity={active ? 0.5 : 0.18} strokeDasharray="4 3" />
        <line x1={cx + 28} y1={cy} x2={cx + 168} y2={cy} stroke={GOLD} strokeWidth="1" opacity={active ? 0.5 : 0.18} strokeDasharray="4 3" />
        <Waveform active={active} cx={cx} cy={cy} />
        <circle cx={cx} cy={cy} r="20" stroke={GOLD} strokeWidth="1.5" strokeOpacity="0.7" fill="#030200" filter="url(#mark-status-blur)" />
        <circle cx={cx} cy={cy} r="6" fill={GOLD_BRIGHT} opacity="0.95" style={{ filter: `drop-shadow(0 0 10px ${GOLD})` }} />
        <text x={cx} y={cy + 42} textAnchor="middle" fill={GOLD} fontSize="12" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontWeight="600" letterSpacing="0.28em" opacity="0.85">
          {labelFor(state)}
        </text>
      </svg>
    </div>
  );
}
