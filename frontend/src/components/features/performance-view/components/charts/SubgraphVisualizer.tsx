import React, { useState, useEffect } from "react";

interface SubgraphVisualizerProps {
  enabled: boolean;
}

export const SubgraphVisualizer: React.FC<SubgraphVisualizerProps> = React.memo(({ enabled }) => {
  // 1. 13 Exact coordinates for a 6-Pointed Star + Center Hub
  const starSlots = [
    { x: 130, y: 100 }, // 0: Center Hub
    { x: 130, y: 14 },  // 1: Outer Top Point
    { x: 152, y: 63 },  // 2: Inner Top Right Valley
    { x: 205, y: 57 },  // 3: Outer Upper Right Point
    { x: 173, y: 100 }, // 4: Inner Right Valley
    { x: 205, y: 143 }, // 5: Outer Lower Right Point
    { x: 152, y: 137 }, // 6: Inner Bottom Right Valley
    { x: 130, y: 186 }, // 7: Outer Bottom Point
    { x: 109, y: 137 }, // 8: Inner Bottom Left Valley
    { x: 56, y: 143 },  // 9: Outer Lower Left Point
    { x: 87, y: 100 },  // 10: Inner Left Valley
    { x: 56, y: 57 },   // 11: Outer Upper Left Point
    { x: 109, y: 63 }   // 12: Inner Top Left Valley
  ];

  // 2. Expanded dataset with 13 distinct node colors
  const baseNodes = [
    { id: 0, color: "#FF4444" },  // Red
    { id: 1, color: "#FF6B35" },  // Orange
    { id: 2, color: "#FBBF24" },  // Amber
    { id: 3, color: "#A3E635" },  // Lime
    { id: 4, color: "#22D3EE" },  // Cyan
    { id: 5, color: "#3B82F6" },  // Blue
    { id: 6, color: "#818CF8" },  // Indigo
    { id: 7, color: "#A855F7" },  // Purple
    { id: 8, color: "#D946EF" },  // Fuchsia
    { id: 9, color: "#FB7185" },  // Rose
    { id: 10, color: "#00FF87" }, // Mint
    { id: 11, color: "#2DD4BF" }, // Teal
    { id: 12, color: "#F43F5E" }  // Crimson
  ];

  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    // Shift positions across all 13 slots every 2.5 seconds
    const interval = setInterval(() => {
      setOffset((prevOffset) => (prevOffset + 1) % 13);
    }, 2500);
    return () => clearInterval(interval);
  }, [enabled]);

  const currentNodes = baseNodes.map((node, i) => {
    const currentSlot = starSlots[(i + offset) % 13];
    return { ...node, x: currentSlot.x, y: currentSlot.y };
  });

  const animStyle = { transition: "all 1.2s cubic-bezier(0.4, 0, 0.2, 1)" };

  return (
    <svg viewBox="0 0 260 200" className="w-full" style={{ height: 200, maxHeight: 200 }}>
      <defs>
        <pattern id="ckg-grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="260" height="200" fill="url(#ckg-grid)" rx="8" />

      {/* Render Nodes */}
      {currentNodes.map((node) => (
        <g key={`node-${node.id}`}>
          {/* Subtle Outer Glow */}
          <circle cx={node.x} cy={node.y} r={9} fill={node.color} fillOpacity={0.15} style={animStyle} />
          {/* Solid Inner Dot */}
          <circle cx={node.x} cy={node.y} r={4.5} fill={node.color} stroke="rgba(255,255,255,0.2)" strokeWidth={1} style={animStyle} />
        </g>
      ))}
    </svg>
  );
});

SubgraphVisualizer.displayName = "SubgraphVisualizer";
