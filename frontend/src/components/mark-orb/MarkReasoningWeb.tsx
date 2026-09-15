"use client";

import {
  getEngineNodes,
  getTelecomServiceNodes,
  type MarkCapabilityNode,
  type MarkRouteTrace,
  type MarkVisualState,
} from "@/lib/mark-capability-graph";
import { useMarkHud } from "@/lib/mark-hud-context";
import "./mark-orb.css";

const CENTER = { x: 500, y: 360 };
const ENGINE_RADIUS_X = 390;
const ENGINE_RADIUS_Y = 252;
const SERVICE_RADIUS_X = 246;
const SERVICE_RADIUS_Y = 158;

type PlottedNode = MarkCapabilityNode & {
  x: number;
  y: number;
  radius: number;
};

function plot(nodes: MarkCapabilityNode[], rx: number, ry: number, start = -Math.PI / 2): PlottedNode[] {
  return nodes.map((node, index) => {
    const angle = start + (index / nodes.length) * Math.PI * 2;
    return {
      ...node,
      x: CENTER.x + Math.cos(angle) * rx,
      y: CENTER.y + Math.sin(angle) * ry,
      radius: node.kind === "engine" ? 16 : 10,
    };
  });
}

function activeIds(trace?: MarkRouteTrace | null, selectedNodeId?: string | null, expanded?: boolean) {
  const ids = new Set<string>();
  if (selectedNodeId) ids.add(selectedNodeId);
  if (trace?.activeEngineId) ids.add(trace.activeEngineId);
  trace?.activeServiceIds?.forEach((id) => ids.add(id));
  if (expanded) ids.add("telecom_brain");
  return ids;
}

function linePath(to: PlottedNode, bend = 0) {
  const mx = (CENTER.x + to.x) / 2;
  const my = (CENTER.y + to.y) / 2;
  const dx = to.x - CENTER.x;
  const dy = to.y - CENTER.y;
  const len = Math.hypot(dx, dy) || 1;
  return `M${CENTER.x} ${CENTER.y} Q${mx + (-dy / len) * bend} ${my + (dx / len) * bend} ${to.x} ${to.y}`;
}

function statusOpacity(state: MarkVisualState) {
  if (state === "idle") return 0.42;
  if (state === "waiting_for_approval") return 0.72;
  return 0.88;
}

export function MarkReasoningWeb({
  state,
  trace,
  selectedNodeId,
  telecomExpanded,
  onSelectNode,
}: {
  state: MarkVisualState;
  trace?: MarkRouteTrace | null;
  selectedNodeId?: string | null;
  telecomExpanded: boolean;
  onSelectNode?: (node: MarkCapabilityNode) => void;
}) {
  const { settings } = useMarkHud();
  const engineNodes = plot(getEngineNodes(), ENGINE_RADIUS_X, ENGINE_RADIUS_Y, -Math.PI / 2);
  const serviceNodes = telecomExpanded ? plot(getTelecomServiceNodes(), SERVICE_RADIUS_X, SERVICE_RADIUS_Y, -Math.PI / 2.15) : [];
  const hot = activeIds(trace, selectedNodeId, telecomExpanded);

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <svg
        aria-hidden="true"
        viewBox="0 0 1000 720"
        preserveAspectRatio="xMidYMid meet"
        style={{ width: "100%", height: "100%", overflow: "visible" }}
      >
        <defs>
          <filter id="mark-rw-glow" x="-90%" y="-90%" width="280%" height="280%">
            <feGaussianBlur stdDeviation="3.2" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="mark-rw-cyan" x1="0%" x2="100%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.2" />
          </linearGradient>
        </defs>

        <circle cx={CENTER.x} cy={CENTER.y} r="154" fill="none" stroke="#1b5f78" strokeDasharray="1 8" strokeOpacity="0.32" />
        <circle cx={CENTER.x} cy={CENTER.y} r="228" fill="none" stroke="#22566b" strokeDasharray="2 12" strokeOpacity="0.26" />
        <ellipse cx={CENTER.x} cy={CENTER.y} rx={ENGINE_RADIUS_X} ry={ENGINE_RADIUS_Y} fill="none" stroke="#1b5f78" strokeDasharray="3 12" strokeOpacity="0.36" />
        {telecomExpanded && (
          <ellipse cx={CENTER.x} cy={CENTER.y} rx={SERVICE_RADIUS_X} ry={SERVICE_RADIUS_Y} fill="none" stroke="#f5a623" strokeDasharray="2 10" strokeOpacity="0.32" />
        )}

        {[...engineNodes, ...serviceNodes].map((node, index) => {
          const isHot = hot.has(node.id);
          const stroke = isHot ? node.color : node.kind === "engine" ? "#22566b" : "#3b5363";
          return (
            <g key={`${node.id}-spoke`}>
              <path
                d={linePath(node, index % 2 ? 18 : -18)}
                fill="none"
                stroke={stroke}
                strokeWidth={isHot ? 1.7 : 1}
                strokeOpacity={isHot ? 0.86 : statusOpacity(state) * (settings.webLineOpacity / 0.45)}
                strokeDasharray={isHot ? "none" : "4 7"}
                filter={isHot ? "url(#mark-rw-glow)" : undefined}
              />
              {isHot && (
                <circle r="2.3" fill={node.color} filter="url(#mark-rw-glow)">
                  <animateMotion dur="1.55s" repeatCount="indefinite" path={linePath(node, index % 2 ? 18 : -18)} />
                </circle>
              )}
            </g>
          );
        })}

        {telecomExpanded &&
          serviceNodes.map((node, index) => {
            const next = serviceNodes[(index + 1) % serviceNodes.length];
            return (
              <line
                key={`${node.id}-mesh`}
                x1={node.x}
                y1={node.y}
                x2={next.x}
                y2={next.y}
                stroke="#143f4f"
                strokeWidth="1"
                strokeOpacity="0.42"
              />
            );
          })}

        {engineNodes.map((node) => {
          const isHot = hot.has(node.id);
          const isTelecom = node.id === "telecom_brain";
          // For telecom_brain at the top, place label ABOVE the orb so it is outside the HUD
          const textY = isTelecom ? node.y - node.radius - 14 : node.y + node.radius + 20;

          return (
            <g
              key={node.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelectNode?.(node);
              }}
              className="cursor-pointer select-none group"
              style={{ pointerEvents: "auto" }}
              role="button"
              tabIndex={0}
              aria-label={`Inspect ${node.label}`}
            >
              <title>{`Inspect ${node.label}`}</title>
              {/* Invisible generous hit target ensuring 100% pixel-perfect clicks on this node */}
              <circle cx={node.x} cy={node.y} r={node.radius + 20} fill="transparent" className="cursor-pointer" />
              {/* Outer soft glow */}
              <circle
                cx={node.x}
                cy={node.y}
                r={node.radius + 10}
                fill={node.color}
                opacity={isHot ? 0.36 : 0.18}
                filter="url(#mark-rw-glow)"
                className={isHot ? "mark-node-hot" : "group-hover:opacity-35 transition-opacity"}
              />
              {/* Luminous orb shell */}
              <circle
                cx={node.x}
                cy={node.y}
                r={node.radius}
                fill="rgba(5, 15, 26, 0.94)"
                stroke={isHot ? node.color : `${node.color}99`}
                strokeWidth={isHot ? 2.6 : 1.8}
                filter="url(#mark-rw-glow)"
                className="group-hover:stroke-white transition-colors"
              />
              {/* Central glowing core dot */}
              <circle
                cx={node.x}
                cy={node.y}
                r={isHot ? 6 : 4.5}
                fill={node.color}
                opacity={isHot ? 1.0 : 0.85}
              />
              {isTelecom && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.radius + 15}
                  fill="none"
                  stroke="#f5a623"
                  strokeDasharray="3 5"
                  strokeOpacity={telecomExpanded ? 0.65 : 0.3}
                />
              )}
              {/* Engine Name Label - ALWAYS PLACED OUTSIDE THE HUD */}
              {settings.showEngineLabels && (
                <text
                  x={node.x}
                  y={textY}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="700"
                  fill={isHot ? "#ffffff" : "#cbe7f7"}
                  fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
                  letterSpacing="0.08em"
                  className="group-hover:fill-cyan-300 transition-colors pointer-events-none"
                >
                  {node.shortLabel.toUpperCase()}
                </text>
              )}
            </g>
          );
        })}

        {serviceNodes.map((node) => {
          const isHot = hot.has(node.id);
          return (
            <g
              key={node.id}
              onClick={(e) => {
                e.stopPropagation();
                onSelectNode?.(node);
              }}
              className="cursor-pointer select-none group"
              style={{ pointerEvents: "auto" }}
              role="button"
              tabIndex={0}
              aria-label={`Inspect ${node.label}`}
            >
              <title>{`Inspect ${node.label}`}</title>
              {/* Invisible generous hit target */}
              <circle cx={node.x} cy={node.y} r={node.radius + 14} fill="transparent" className="cursor-pointer" />
              <circle
                cx={node.x}
                cy={node.y}
                r={node.radius + 8}
                fill={node.color}
                opacity={isHot ? 0.28 : 0.14}
                filter="url(#mark-rw-glow)"
                className={isHot ? "mark-node-hot" : "group-hover:opacity-30 transition-opacity"}
              />
              <circle
                cx={node.x}
                cy={node.y}
                r={node.radius}
                fill="rgba(4, 11, 20, 0.92)"
                stroke={isHot ? node.color : `${node.color}88`}
                strokeWidth={isHot ? 2.2 : 1.4}
                className="group-hover:stroke-white transition-colors"
              />
              <circle
                cx={node.x}
                cy={node.y}
                r={3}
                fill={node.color}
                opacity={isHot ? 1 : 0.75}
              />
              <text
                x={node.x}
                y={node.y - node.radius - 8}
                textAnchor="middle"
                fontSize="10"
                fontWeight="600"
                fill={isHot ? "#ffffff" : "#a8ccdf"}
                fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
                letterSpacing="0.04em"
                className="group-hover:fill-cyan-300 transition-colors pointer-events-none"
              >
                {node.shortLabel.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
