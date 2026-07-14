import React from "react";
import { CHART_COLORS } from "@/lib/chart-colors";

export const ConcentricRings: React.FC = React.memo(() => {
  const rings = [
    { label: "Prompt Adherence", value: "5278", size: 120, color: CHART_COLORS.neonCyan },
    { label: "RAG Precision", value: "3.76", size: 90, color: CHART_COLORS.neonMagenta },
    { label: "Tool Correctness", value: "736", size: 60, color: CHART_COLORS.neonLime },
  ];

  return (
    <div className="relative flex items-center justify-center h-48">
      {/* Center callout */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className="text-center">
          <p className="text-2xl font-bold text-white" style={{ textShadow: `0 0 20px ${CHART_COLORS.neonCyan}60` }}>
            58%
          </p>
          <p className="text-[10px] text-neutral-400 mt-0.5">Monitor Hit Rate</p>
        </div>
      </div>

      {/* Rings */}
      <svg width="200" height="200" viewBox="0 0 200 200" className="absolute">
        {rings.map((ring, i) => {
          const radius = ring.size / 2;
          const circumference = 2 * Math.PI * radius;
          const offset = circumference * 0.58;
          return (
            <circle
              key={i}
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke={ring.color}
              strokeWidth="2"
              strokeDasharray={`${offset} ${circumference - offset}`}
              strokeLinecap="round"
              opacity={0.6}
              transform={`rotate(-90 100 100)`}
              style={{
                filter: `drop-shadow(0 0 4px ${ring.color})`,
              }}
            />
          );
        })}
      </svg>

      {/* Labels */}
      <div className="absolute inset-0">
        {rings.map((ring, i) => {
          const angle = (i * 120 - 60) * (Math.PI / 180);
          const radius = ring.size / 2 + 16;
          const x = 100 + radius * Math.cos(angle);
          const y = 100 + radius * Math.sin(angle);
          return (
            <div
              key={i}
              className="absolute text-[9px] text-neutral-400 leading-tight text-center pointer-events-none"
              style={{
                left: `${(x / 200) * 100}%`,
                top: `${(y / 200) * 100}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              <span style={{ color: ring.color }}>{ring.label}</span>
              <br />
              <span className="text-white font-semibold text-[11px]">{ring.value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
});

ConcentricRings.displayName = "ConcentricRings";
