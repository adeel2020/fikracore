import React from "react";

interface SpeedometerGaugeProps {
  value: number;
  unit: string;
  color: string;
  size?: number;
}

export const SpeedometerGauge: React.FC<SpeedometerGaugeProps> = React.memo(({
  value,
  unit,
  color,
  size = 160,
}) => {
  const pct = Math.min(1, value / 40);
  const stroke = 14;
  const r = (size - stroke) / 2;
  const startAngle = 135;
  const endAngle = 405;
  const sweep = endAngle - startAngle;
  const angle = startAngle + sweep * pct;

  const polar = (a: number) => {
    const rad = ((a - 90) * Math.PI) / 180;
    return { x: size / 2 + r * Math.cos(rad), y: size / 2 + r * Math.sin(rad) };
  };

  const describeArc = (start: number, end: number) => {
    const s = polar(start);
    const e = polar(end);
    const large = end - start <= 180 ? 0 : 1;
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y}`;
  };

  const id = `gauge-${color.replace("#", "")}`;
  const needleEnd = polar(angle);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="absolute inset-0">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity={0.6} />
            <stop offset="100%" stopColor={color} stopOpacity={1} />
          </linearGradient>
        </defs>
        <path
          d={describeArc(startAngle, endAngle)}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeOpacity={0.12}
          strokeLinecap="round"
        />
        <path
          d={describeArc(startAngle, angle)}
          fill="none"
          stroke={`url(#${id})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 8px ${color}aa)`,
            transition: "all 0.6s",
          }}
        />
        <line
          x1={size / 2}
          y1={size / 2}
          x2={needleEnd.x}
          y2={needleEnd.y}
          stroke={color}
          strokeWidth={2.5}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={5}
          fill={color}
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
      </svg>
      <div className="relative z-10 flex flex-col items-center">
        <div
          className="text-3xl font-bold text-white"
          style={{ textShadow: `0 0 14px ${color}80` }}
        >
          {value}
        </div>
        <div className="text-[11px] text-neutral-400">{unit}</div>
      </div>
    </div>
  );
});

SpeedometerGauge.displayName = "SpeedometerGauge";
