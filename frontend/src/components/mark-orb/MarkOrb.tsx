"use client";

import type { MarkVisualState } from "@/lib/mark-capability-graph";
import { useMarkHud } from "@/lib/mark-hud-context";
import "./mark-orb.css";

const GOLD = "#f5a623";
const GOLD_BRIGHT = "#ffd080";
const CYAN = "#00e5ff";

function visualLabel(state: MarkVisualState) {
  if (state === "listening") return "LISTENING";
  if (state === "processing") return "ANALYZING";
  if (state === "speaking") return "SPEAKING";
  if (state === "investigating") return "INVESTIGATING";
  if (state === "waiting_for_approval") return "APPROVAL";
  if (state === "learning") return "LEARNING";
  return "READY";
}

function Waveform({ active, cx, cy, width = 220 }: { active: boolean; cx: number; cy: number; width?: number }) {
  const barCount = 28;
  const barW = 3;
  const gap = (width - barCount * barW) / (barCount - 1);

  return (
    <g>
      {Array.from({ length: barCount }, (_, i) => {
        const x = cx - width / 2 + i * (barW + gap);
        const baseH = 3 + Math.abs(Math.sin(i * 0.6)) * 5;
        const activeH = 8 + Math.abs(Math.sin(i * 0.8)) * 28;
        const h = active ? activeH : baseH;
        const fixedX = x.toFixed(3);
        const fixedY = (cy - h / 2).toFixed(3);
        const fixedH = h.toFixed(3);
        return (
          <rect
            key={i}
            x={fixedX}
            y={fixedY}
            width={barW}
            height={fixedH}
            rx={1.5}
            fill={GOLD}
            opacity={active ? 0.85 : 0.25}
            className={`mark-wavebar mark-wavebar-${i % 7}`}
          />
        );
      })}
    </g>
  );
}

function SoundWaves({ cx, cy, r }: { cx: number; cy: number; r: number }) {
  return (
    <g>
      {[0, 1, 2, 3].map((i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          stroke={GOLD}
          strokeWidth="0.8"
          fill="none"
          opacity="0.18"
          className={`mark-sound-wave mark-wave-${i}`}
        />
      ))}
    </g>
  );
}

export function MarkOrb({
  state = "idle",
  variant = "frame",
}: {
  state?: MarkVisualState;
  variant?: "frame" | "full";
}) {
  const frameOnly = variant === "frame";
  const { settings } = useMarkHud();
  const width = 900;
  const height = 520;
  const cx = width / 2;
  const cy = frameOnly ? height / 2 : height / 2 - 20;
  const r = 155;
  const outer = [178, 194, 212, 230, 250];
  const active = state !== "idle";
  const approval = state === "waiting_for_approval";
  const learning = state === "learning";
  const cyanOpacity = state === "investigating" || state === "processing" ? 0.48 : 0.32;

  return (
    <div className="mark-orb-wrap" data-state={state} style={{ width, height }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} fill="none" aria-hidden="true">
        <defs>
          <radialGradient id="markRingFill" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={GOLD} stopOpacity="0" />
            <stop offset="70%" stopColor={GOLD} stopOpacity="0.04" />
            <stop offset="88%" stopColor={GOLD} stopOpacity={approval ? "0.22" : "0.18"} />
            <stop offset="100%" stopColor={GOLD_BRIGHT} stopOpacity={learning ? "0.7" : "0.5"} />
          </radialGradient>
          <radialGradient id="markAmbientBg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={CYAN} stopOpacity={cyanOpacity} />
            <stop offset="35%" stopColor={CYAN} stopOpacity={cyanOpacity * 0.6} />
            <stop offset="65%" stopColor={GOLD} stopOpacity={active ? "0.08" : "0.03"} />
            <stop offset="100%" stopColor={GOLD} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="markCenterDustGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.4" />
            <stop offset="28%" stopColor="#00e5ff" stopOpacity="0.25" />
            <stop offset="65%" stopColor="#00b4d8" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#00e5ff" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="markDepthDisc" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#050b14" stopOpacity="0.80" />
            <stop offset="68%" stopColor="#050b14" stopOpacity="0.55" />
            <stop offset="90%" stopColor="#050b14" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#050b14" stopOpacity="0" />
          </radialGradient>
          <filter id="markRingBlur" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="7" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="markTextGlow" x="-30%" y="-80%" width="160%" height="260%">
            <feGaussianBlur stdDeviation="5" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <ellipse cx={cx} cy={cy} rx={r + 130} ry={r + 90} fill="url(#markAmbientBg)" className="mark-ambient" />
        <circle cx={cx} cy={cy} r={r} fill="url(#markDepthDisc)" />
        <circle cx={cx} cy={cy} r={r * 0.38} fill="url(#markCenterDustGlow)" className="mark-ambient" />

        {outer.map((radius, i) => (
          <circle
            key={radius}
            cx={cx}
            cy={cy}
            r={radius}
            stroke={i < 2 ? GOLD : CYAN}
            strokeWidth={i === 0 ? 0.8 : 0.4}
            strokeOpacity={0.16 - i * 0.02}
            fill="none"
            strokeDasharray={i % 2 ? "3 7" : "none"}
          />
        ))}

        <line x1={cx} y1={cy - outer[4] - 10} x2={cx} y2={cy - outer[4] + 10} stroke={GOLD} strokeWidth="1" opacity="0.32" />
        <line x1={cx} y1={cy + outer[4] - 10} x2={cx} y2={cy + outer[4] + 10} stroke={GOLD} strokeWidth="1" opacity="0.32" />
        <line x1={cx - outer[4] - 10} y1={cy} x2={cx - outer[4] + 10} y2={cy} stroke={CYAN} strokeWidth="1" opacity="0.24" />
        <line x1={cx + outer[4] - 10} y1={cy} x2={cx + outer[4] + 10} y2={cy} stroke={CYAN} strokeWidth="1" opacity="0.24" />

        {settings.showSoundWaves && <SoundWaves cx={cx} cy={cy} r={r} />}

        {(state === "processing" || state === "investigating" || state === "learning") && (
          <circle
            cx={cx}
            cy={cy}
            r={r + 22}
            stroke={learning ? "#fbbf24" : CYAN}
            strokeWidth="1"
            strokeOpacity="0.48"
            strokeDasharray="8 14"
            fill="none"
            className="mark-orbit-cw"
            style={{ transformOrigin: `${cx}px ${cy}px` }}
          />
        )}

        <circle cx={cx} cy={cy} r={r} fill="url(#markRingFill)" className="mark-ring-breathe" />
        <circle cx={cx} cy={cy} r={r} stroke={GOLD} strokeWidth="18" strokeOpacity="0.08" fill="none" filter="url(#markRingBlur)" className="mark-ring-glow" />
        <circle cx={cx} cy={cy} r={r} stroke={GOLD} strokeWidth="6" strokeOpacity="0.4" fill="none" filter="url(#markRingBlur)" />
        <circle cx={cx} cy={cy} r={r} stroke={GOLD_BRIGHT} strokeWidth="2.5" strokeOpacity="0.95" fill="none" className="mark-ring-bright" />
        <circle cx={cx} cy={cy} r={r * 0.58} stroke={GOLD} strokeWidth="1.5" strokeOpacity={active ? 0.45 : 0.15} fill="none" strokeDasharray="55 25" className="mark-orbit-cw" style={{ transformOrigin: `${cx}px ${cy}px` }} />
        <circle cx={cx} cy={cy} r={r * 0.35} stroke={CYAN} strokeWidth="1" strokeOpacity={active ? 0.32 : 0.12} fill="none" strokeDasharray="28 18" className="mark-orbit-ccw" style={{ transformOrigin: `${cx}px ${cy}px` }} />

        {!frameOnly && (
          <g>
            <line x1={cx - r - 90} y1={cy} x2={cx - r + 15} y2={cy} stroke={GOLD} strokeWidth="1" opacity={active ? 0.55 : 0.15} strokeDasharray="4 3" />
            <line x1={cx + r - 15} y1={cy} x2={cx + r + 90} y2={cy} stroke={GOLD} strokeWidth="1" opacity={active ? 0.55 : 0.15} strokeDasharray="4 3" />
            <Waveform active={active} cx={cx} cy={cy} width={200} />
            <circle cx={cx} cy={cy} r={20} stroke={GOLD} strokeWidth="1.5" strokeOpacity="0.7" fill="#030200" filter="url(#markRingBlur)" />
            <circle cx={cx} cy={cy} r={6} fill={GOLD_BRIGHT} opacity="0.95" style={{ filter: `drop-shadow(0 0 10px ${GOLD})` }} />
            <text x={cx} y={cy + r * 0.52} textAnchor="middle" fill={GOLD} fontSize="12" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace" fontWeight="400" letterSpacing="0.28em" opacity="0.65" filter="url(#markTextGlow)">
              {visualLabel(state)}
            </text>
            {[0, 1, 2].map((i) => (
              <circle key={i} cx={cx + (i - 1) * 12} cy={cy + r * 0.52 + 18} r="2.5" fill={GOLD} className={`mark-dot-blink mark-blink-${i}`} />
            ))}
          </g>
        )}
      </svg>
    </div>
  );
}
