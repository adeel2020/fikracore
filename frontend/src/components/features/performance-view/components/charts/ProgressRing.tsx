import React, { useId } from "react";

interface ProgressRingProps {
  value: number;
  color: string;
  size?: number;
  stroke?: number;
  label?: string;
  suffix?: string;
  icon?: React.ReactNode;
  glowIntensity?: number;
}

export const ProgressRing: React.FC<ProgressRingProps> = React.memo(({
  value,
  color,
  size = 130,
  stroke = 12,
  label,
  suffix = "%",
  icon,
  glowIntensity = 1,
}) => {
  const uid = useId();
  const id = `ring-${color.replace("#", "")}-${uid}`;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(100, Math.max(0, value)) / 100);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="absolute inset-0 -rotate-90">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity={0.95} />
            <stop offset="100%" stopColor={color} stopOpacity={0.55} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeOpacity={0.12}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{
            filter: `drop-shadow(0 0 ${8 * glowIntensity}px ${color}aa)`,
            transition: "stroke-dashoffset 1s ease",
          }}
        />
      </svg>
      <div className="relative z-10 flex flex-col items-center justify-center">
        {icon && (
          <div
            className="mb-1 flex h-6 w-6 items-center justify-center"
            style={{
              color,
              filter: `drop-shadow(0 0 ${4 * glowIntensity}px ${color}aa)`,
            }}
          >
            {icon}
          </div>
        )}
        <div
          className="text-3xl font-bold leading-none text-white"
          style={{ textShadow: `0 0 ${14 * glowIntensity}px ${color}80` }}
        >
          {Math.round(value)}
          {suffix}
        </div>
        {label && (
          <div className="mt-1 text-[11px] text-neutral-300">{label}</div>
        )}
      </div>
    </div>
  );
});

ProgressRing.displayName = "ProgressRing";
