"use client";

import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import type {
  ClusteringDimension,
  SemanticPoint,
  TerritoryOffset,
  TooltipInfo,
  ViewMode,
} from "../types/semantic-cloud.types";
import { useScatterCanvas } from "./hooks/useScatterCanvas";
import { getDashboardFeed } from "../hooks/useDashboardFeedCache";

const DOT_PALETTE = [
  "#2F6BFF", "#FF4D6D", "#25C26E", "#FFB703",
  "#8B5CF6", "#06B6D4", "#E11D48", "#14B8A6",
  "#F97316", "#4F46E5", "#F43F5E", "#38BDF8",
];

function groupKey(point: SemanticPoint, dimension: ClusteringDimension): string {
  return dimension === "reason"
    ? point.reassignment_reason || "(unassigned)"
    : point.category || point.issue_category || "(uncategorized)";
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function formatPercentage(value?: number) {
  if (typeof value !== "number" || Number.isNaN(value)) return "0.0%";
  return `${(value * 100).toFixed(1)}%`;
}

const stateStyle: React.CSSProperties = {
  width: "100%",
  height: "100%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "rgba(255,255,255,0.66)",
  background: "#050505",
  fontFamily: "'Geist Mono', monospace",
  letterSpacing: "0.05em",
};

const GLOBAL_MIN_RADIUS = 8;
const FED_MIN_RADIUS = 2.5;
const MIN_SPACING = 0.6;
const DOT_RADIUS = 3;
const ANOMALY_RING_RADIUS = 8;
const HOVER_RING_RADIUS = 10;
const HIT_RADIUS = 6;
const FIT_PADDING = 40;
const MIN_SCALE = 0.08;
const MAX_SCALE = 500;
const MAX_EFFECTIVE_SCALE = 5;

export interface ZoomActions {
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
  getPalette: () => Map<string, string>;
  focusCluster: (key: string | null) => void;
  getFocusedCluster: () => string | null;
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function randomInCircle(radius: number, seed: number): [number, number] {
  const angle = seededRandom(seed * 2 + 1) * Math.PI * 2;
  const r = Math.sqrt(seededRandom(seed * 2 + 2)) * radius;
  return [Math.cos(angle) * r, Math.sin(angle) * r];
}

function computeClusterLayout(
  data: SemanticPoint[],
  clusteringDimension: ClusteringDimension,
  viewMode: ViewMode,
  territoryOffsets: TerritoryOffset[],
  semanticMode?: boolean,
): [number, number][] {
  if (semanticMode) {
    const territories = new Map(territoryOffsets.map((t) => [t.key, t]));
    const positions: [number, number][] = new Array(data.length);
    for (let i = 0; i < data.length; i++) {
      const point = data[i];
      if (viewMode === "federated") {
        const key = groupKey(point, clusteringDimension);
        const territory = territories.get(key);
        if (territory) {
          positions[i] = [
            (point.x - territory.centroid[0]) + territory.offset[0],
            (point.z - territory.centroid[2]) + territory.offset[1],
          ];
        } else {
          positions[i] = [point.x, point.z];
        }
      } else {
        positions[i] = [point.x, point.z];
      }
    }
    return positions;
  }

  const groups = new Map<string, number[]>();
  for (let i = 0; i < data.length; i++) {
    const key = groupKey(data[i], clusteringDimension);
    const bucket = groups.get(key);
    if (bucket) bucket.push(i);
    else groups.set(key, [i]);
  }

  if (viewMode === "global") {
    const total = data.length;
    const radius = Math.max(GLOBAL_MIN_RADIUS, Math.sqrt(total / Math.PI) * MIN_SPACING);
    const positions: [number, number][] = new Array(total);
    for (const [, indices] of groups) {
      for (const pi of indices) {
        positions[pi] = randomInCircle(radius, pi);
      }
    }
    return positions;
  }

  const territories = new Map(territoryOffsets.map((t) => [t.key, t]));
  const totalTerritories = territoryOffsets.length;
  const minChord = totalTerritories > 1
    ? 2 * 12 * Math.sin(Math.PI / totalTerritories)
    : 12;
  const maxClusterRadius = Math.max(FED_MIN_RADIUS, minChord * 0.35);

  const positions: [number, number][] = new Array(data.length);
  for (const [key, indices] of groups) {
    const territory = territories.get(key);
    const ox = territory?.offset[0] ?? 0;
    const oy = territory?.offset[1] ?? 0;
    const count = indices.length;
    const areaPerPoint = MIN_SPACING * MIN_SPACING;
    const neededRadius = Math.sqrt((count * areaPerPoint) / Math.PI);
    const radius = Math.min(maxClusterRadius, Math.max(FED_MIN_RADIUS, neededRadius));

    for (const pi of indices) {
      const [dx, dy] = randomInCircle(radius, pi + 1000);
      positions[pi] = [ox + dx, oy + dy];
    }
  }
  return positions;
}

function computeFitTransform(
  positions: [number, number][],
  vw: number,
  vh: number,
): { x: number; y: number; scale: number } {
  if (positions.length === 0 || vw === 0 || vh === 0) return { x: 0, y: 0, scale: 1 };
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const [x, y] of positions) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
  }
  const ww = maxX - minX || 1;
  const wh = maxY - minY || 1;
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const s = Math.min((vw - FIT_PADDING * 2) / ww, (vh - FIT_PADDING * 2) / wh);
  return { x: -(cx * s), y: -(cy * s), scale: Math.max(MIN_SCALE, s) };
}

interface Canvas2DProps {
  data: SemanticPoint[];
  territoryOffsets: TerritoryOffset[];
  viewMode: ViewMode;
  clusteringDimension: ClusteringDimension;
  semanticMode: boolean;
  is3DMode: boolean;
  focusedCluster: string | null;
  onTooltip: (info: TooltipInfo | null) => void;
  onPaletteChange?: (palette: Map<string, string>) => void;
}

const Canvas2D = forwardRef<ZoomActions, Canvas2DProps>(function Canvas2D({
  data,
  territoryOffsets,
  viewMode,
  clusteringDimension,
  semanticMode,
  is3DMode,
  focusedCluster,
  onTooltip,
  onPaletteChange,
}, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef(0);
  const currentRef = useRef<[number, number][]>([]);
  const transformRef = useRef({ x: 0, y: 0, scale: 1 });
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const hoveredRef = useRef<number | null>(null);
  const isPanning = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });
  const yawRef = useRef(0);
  const pitchRef = useRef(0);
  const fitScaleRef = useRef(1);
  const focusedRef = useRef<string | null>(null);

  const circlePositions = useMemo(
    () => computeClusterLayout(data, clusteringDimension, viewMode, territoryOffsets, semanticMode),
    [data, clusteringDimension, viewMode, territoryOffsets, semanticMode],
  );

  const paletteMap = useMemo(() => {
    const map = new Map<string, string>();
    data.forEach((point) => {
      const key = groupKey(point, clusteringDimension);
      if (!map.has(key)) {
        map.set(key, DOT_PALETTE[map.size % DOT_PALETTE.length]);
      }
    });
    return map;
  }, [data, clusteringDimension]);

  useEffect(() => {
    if (paletteMap.size > 0 && onPaletteChange) {
      onPaletteChange(paletteMap);
    }
  }, [paletteMap, onPaletteChange]);

  const colorArray = useMemo(() => {
    const colors = new Float32Array(data.length * 3);
    data.forEach((point, index) => {
      const key = groupKey(point, clusteringDimension);
      const { r, g, b } = hexToRgb(paletteMap.get(key)!);
      colors[index * 3] = r / 255;
      colors[index * 3 + 1] = g / 255;
      colors[index * 3 + 2] = b / 255;
    });
    return colors;
  }, [data, clusteringDimension, paletteMap]);

  const queueCorrelation = useMemo(() => {
    const counts = new Map<string, Map<string, number>>();
    data.forEach((point) => {
      const key = groupKey(point, clusteringDimension);
      const queue = point.ticket_queue || "(unassigned)";
      if (!counts.has(key)) counts.set(key, new Map());
      const qm = counts.get(key)!;
      qm.set(queue, (qm.get(queue) ?? 0) + 1);
    });
    const result = new Map<string, { queue: string; pct: string }[]>();
    counts.forEach((qm, key) => {
      const total = Array.from(qm.values()).reduce((s, v) => s + v, 0) || 1;
      result.set(
        key,
        Array.from(qm.entries())
          .sort((a, b) => b[1] - a[1])
          .map(([queue, count]) => ({ queue, pct: `${((count / total) * 100).toFixed(0)}%` })),
      );
    });
    return result;
  }, [data, clusteringDimension]);

  const fitCanvas = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const vw = container.clientWidth;
    const vh = container.clientHeight;
    if (vw === 0 || vh === 0 || circlePositions.length === 0) return;
    const fit = computeFitTransform(circlePositions, vw, vh);
    fitScaleRef.current = fit.scale;
    transformRef.current = fit;
    setTransform(fit);
  }, [circlePositions]);

  useImperativeHandle(ref, () => ({
    zoomIn: () => {
      const t = transformRef.current;
      const maxAllowed = Math.max(MAX_SCALE, fitScaleRef.current * MAX_EFFECTIVE_SCALE);
      t.scale = Math.min(maxAllowed, t.scale * 1.5);
      setTransform({ x: t.x, y: t.y, scale: t.scale });
    },
    zoomOut: () => {
      const t = transformRef.current;
      t.scale = Math.max(MIN_SCALE, t.scale / 1.5);
      setTransform({ x: t.x, y: t.y, scale: t.scale });
    },
    fit: () => fitCanvas(),
    getPalette: () => paletteMap,
    focusCluster: (key: string | null) => { focusedRef.current = key; },
    getFocusedCluster: () => focusedRef.current,
  }), [fitCanvas, paletteMap]);

  useEffect(() => {
    currentRef.current = circlePositions.map((p) => [p[0], p[1]]);
    fitCanvas();
  }, [circlePositions, fitCanvas]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animating = true;

    const resize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;
      const dpr = devicePixelRatio || 1;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    const draw = () => {
      if (!animating) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }
      const dpr = devicePixelRatio || 1;
      const t = transformRef.current;

      ctx.save();
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, w, h);

      ctx.save();
      ctx.translate(w / 2 + t.x, h / 2 + t.y);
      ctx.scale(t.scale, t.scale);

      const focused = focusedRef.current;
      const cur = currentRef.current;

      if (is3DMode) {
        const c = ctx!;
        const yaw = yawRef.current;
        const pitch = pitchRef.current;
        const cosY = Math.cos(yaw);
        const sinY = Math.sin(yaw);
        const cosP = Math.cos(pitch);
        const sinP = Math.sin(pitch);

        interface ScreenPt { x: number; y: number; depth: number; idx: number }
        const pts: ScreenPt[] = [];
        const territories = new Map(territoryOffsets.map((t2) => [t2.key, t2]));

        for (let i = 0; i < data.length; i++) {
          const point = data[i];
          let sx = point.x;
          let sy = point.y || 0;
          let sz = point.z;

          if (viewMode === "federated") {
            const key = groupKey(point, clusteringDimension);
            const territory = territories.get(key);
            if (territory) {
              sx = (sx - territory.centroid[0]) + territory.offset[0];
              sy = (sy - territory.centroid[1]) + territory.offset[2];
              sz = (sz - territory.centroid[2]) + territory.offset[1];
            }
          }

          const rx = sx * cosY + sy * sinY * sinP + sz * sinY * cosP;
          const ry = sy * cosP - sz * sinP;
          const depth = -sx * sinY + sy * cosY * sinP + sz * cosY * cosP;

          pts.push({ x: rx, y: ry, depth, idx: i });
        }

        if (!focused) {
          pts.sort((a, b) => a.depth - b.depth);
        }

        for (let pi = 0; pi < pts.length; pi++) {
          const p = focused ? pts[pi] : pts[pi];
          const i = p.idx;
          const ri = colorArray[i * 3] * 255;
          const gi = colorArray[i * 3 + 1] * 255;
          const bi = colorArray[i * 3 + 2] * 255;

          if (focused) {
            const key = groupKey(data[i], clusteringDimension);
            if (key !== focused) {
              c.globalAlpha = 0.06;
            }
          }

          c.beginPath();
          c.arc(p.x, p.y, DOT_RADIUS / t.scale, 0, Math.PI * 2);
          c.fillStyle = `rgb(${ri | 0},${gi | 0},${bi | 0})`;
          c.fill();

          if (data[i].is_anomaly) {
            const pulse = 1 + Math.sin(Date.now() * 0.0022) * 0.06;
            c.beginPath();
            c.arc(p.x, p.y, (ANOMALY_RING_RADIUS * pulse) / t.scale, 0, Math.PI * 2);
            c.strokeStyle = `rgb(${ri | 0},${gi | 0},${bi | 0})`;
            c.lineWidth = 1.2 / t.scale;
            c.stroke();
          }

          c.globalAlpha = 1;
        }

        if (hoveredRef.current !== null) {
          const hp = pts.find((p) => p.idx === hoveredRef.current);
          if (hp) {
            c.beginPath();
            c.arc(hp.x, hp.y, HOVER_RING_RADIUS / t.scale, 0, Math.PI * 2);
            c.strokeStyle = "rgba(255,255,255,0.6)";
            c.lineWidth = 1.5 / t.scale;
            c.stroke();
          }
        }

        function drawAxes(originX: number, originY: number) {
          const axisArr = [
            { dir: [1, 0, 0] as const, label: "Sem X", color: "#FF6B6B" },
            { dir: [0, 1, 0] as const, label: "Sem Y", color: "#51CF66" },
            { dir: [0, 0, 1] as const, label: "Sem Z", color: "#4DABF7" },
          ];
          for (const a of axisArr) {
            const [dx, dy, dz] = a.dir;
            const arrLen = 4;
            const endX = originX + (dx * cosY + dy * sinY * sinP + dz * sinY * cosP) * arrLen;
            const endY = originY + (dy * cosP - dz * sinP) * arrLen;
            c.beginPath();
            c.moveTo(originX, originY);
            c.lineTo(endX, endY);
            c.strokeStyle = a.color;
            c.lineWidth = 1.5 / t.scale;
            c.stroke();

            const headSize = 0.35;
            const angle = Math.atan2(endY - originY, endX - originX);
            c.beginPath();
            c.moveTo(endX, endY);
            c.lineTo(
              endX - headSize * Math.cos(angle - 0.5),
              endY - headSize * Math.sin(angle - 0.5),
            );
            c.lineTo(
              endX - headSize * Math.cos(angle + 0.5),
              endY - headSize * Math.sin(angle + 0.5),
            );
            c.closePath();
            c.fillStyle = a.color;
            c.fill();

            c.font = `${9 / t.scale}px 'Geist Mono', monospace`;
            c.fillStyle = a.color;
            c.textAlign = "center";
            c.fillText(a.label, endX, endY - 6 / t.scale);
          }
        }

        drawAxes(0, 0);

        if (viewMode === "federated") {
          for (const territory of territoryOffsets) {
            const cx = territory.offset[0];
            const cy = territory.offset[2];
            const cz = territory.offset[1];
            const rcx = cx * cosY + cy * sinY * sinP + cz * sinY * cosP;
            const rcy = cy * cosP - cz * sinP;
            const labelAlpha = focused && focused !== territory.key ? 0.15 : 0.85;
            c.font = `${10 / t.scale}px 'Geist Mono', monospace`;
            c.textAlign = "center";
            c.textBaseline = "bottom";
            const tw = c.measureText(territory.label).width;
            const lx = rcx;
            const ly = rcy - 14 / t.scale;
            const pad = 4 / t.scale;
            c.fillStyle = `rgba(0,0,0,${0.55 * labelAlpha})`;
            c.beginPath();
            c.roundRect(lx - tw / 2 - pad, ly - 10 / t.scale, tw + pad * 2, 12 / t.scale, 2 / t.scale);
            c.fill();
            c.fillStyle = `rgba(255,255,255,${labelAlpha})`;
            c.fillText(territory.label, lx, ly + 2 / t.scale);
          }
          if (focused) {
            const territory = territoryOffsets.find((t2) => t2.key === focused);
            if (territory) {
              const cx = territory.offset[0];
              const cy = territory.offset[2];
              const cz = territory.offset[1];
              const rcx = cx * cosY + cy * sinY * sinP + cz * sinY * cosP;
              const rcy = cy * cosP - cz * sinP;
              drawAxes(rcx, rcy);
            }
          }
        }
      } else {
        for (let i = 0; i < data.length; i++) {
          const c = cur[i];
          const target = circlePositions[i];
          if (!c || !target) continue;
          c[0] += (target[0] - c[0]) * 0.1;
          c[1] += (target[1] - c[1]) * 0.1;
        }

        for (let i = 0; i < data.length; i++) {
          const pos = cur[i];
          if (!pos) continue;
          const ri = colorArray[i * 3] * 255;
          const gi = colorArray[i * 3 + 1] * 255;
          const bi = colorArray[i * 3 + 2] * 255;

          if (focused) {
            const key = groupKey(data[i], clusteringDimension);
            if (key !== focused) ctx.globalAlpha = 0.06;
          }

          ctx.beginPath();
          ctx.arc(pos[0], pos[1], DOT_RADIUS / t.scale, 0, Math.PI * 2);
          ctx.fillStyle = `rgb(${ri | 0},${gi | 0},${bi | 0})`;
          ctx.fill();

          if (data[i].is_anomaly) {
            const pulse = 1 + Math.sin(Date.now() * 0.0022) * 0.06;
            ctx.beginPath();
            ctx.arc(pos[0], pos[1], (ANOMALY_RING_RADIUS * pulse) / t.scale, 0, Math.PI * 2);
            ctx.strokeStyle = `rgb(${ri | 0},${gi | 0},${bi | 0})`;
            ctx.lineWidth = 1.2 / t.scale;
            ctx.stroke();
          }

          ctx.globalAlpha = 1;
        }

        if (hoveredRef.current !== null && cur[hoveredRef.current]) {
          const pos = cur[hoveredRef.current];
          ctx.beginPath();
          ctx.arc(pos[0], pos[1], HOVER_RING_RADIUS / t.scale, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(255,255,255,0.6)";
          ctx.lineWidth = 1.5 / t.scale;
          ctx.stroke();
        }

        if (viewMode === "federated" && !is3DMode) {
          for (const territory of territoryOffsets) {
            const ox = territory.offset[0];
            const oy = territory.offset[1];
            ctx.globalAlpha = focused && focused !== territory.key ? 0.06 : 1;
            ctx.font = `${11 / t.scale}px 'Geist Mono', monospace`;
            ctx.textAlign = "center";
            ctx.fillStyle = "rgba(255,255,255,0.75)";
            ctx.fillText(territory.label, ox, oy - 10 / t.scale);

            const ax = territory.axis[0];
            const ay = territory.axis[2];
            const arrowLen = 3.1;
            ctx.beginPath();
            ctx.moveTo(ox, oy);
            ctx.lineTo(ox + ax * arrowLen, oy + ay * arrowLen);
            ctx.strokeStyle = "rgba(138,180,255,0.45)";
            ctx.lineWidth = 1.2 / t.scale;
            ctx.stroke();

            const tipX = ox + ax * arrowLen;
            const tipY = oy + ay * arrowLen;
            const headSize = 0.35;
            const angle = Math.atan2(ay, ax);
            ctx.beginPath();
            ctx.moveTo(tipX, tipY);
            ctx.lineTo(
              tipX - headSize * Math.cos(angle - 0.5),
              tipY - headSize * Math.sin(angle - 0.5),
            );
            ctx.lineTo(
              tipX - headSize * Math.cos(angle + 0.5),
              tipY - headSize * Math.sin(angle + 0.5),
            );
            ctx.closePath();
            ctx.fillStyle = "rgba(138,180,255,0.45)";
            ctx.fill();
            ctx.globalAlpha = 1;
          }
        }
      }

      ctx.restore();
      ctx.restore();

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);

    return () => {
      animating = false;
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, [data, circlePositions, colorArray, viewMode, territoryOffsets, is3DMode, focusedCluster, clusteringDimension]);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      const container = containerRef.current;
      if (!container || isPanning.current) return;
      const rect = container.getBoundingClientRect();
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      let closest = -1;
      let closestDist = HIT_RADIUS;
      const t = transformRef.current;
      const territories = new Map(territoryOffsets.map((t2) => [t2.key, t2]));

      if (is3DMode) {
        const yaw = yawRef.current;
        const pitch = pitchRef.current;
        const cosY = Math.cos(yaw);
        const sinY = Math.sin(yaw);
        const cosP = Math.cos(pitch);
        const sinP = Math.sin(pitch);

        for (let i = 0; i < data.length; i++) {
          const point = data[i];
          let sx3 = point.x;
          let sy3 = point.y || 0;
          let sz3 = point.z;
          if (viewMode === "federated") {
            const key = groupKey(point, clusteringDimension);
            const territory = territories.get(key);
            if (territory) {
              sx3 = (sx3 - territory.centroid[0]) + territory.offset[0];
              sy3 = (sy3 - territory.centroid[1]) + territory.offset[2];
              sz3 = (sz3 - territory.centroid[2]) + territory.offset[1];
            }
          }
          const rx = sx3 * cosY + sy3 * sinY * sinP + sz3 * sinY * cosP;
          const ry = sy3 * cosP - sz3 * sinP;
          const px = rx * t.scale + container.clientWidth / 2 + t.x;
          const py = ry * t.scale + container.clientHeight / 2 + t.y;
          const d = Math.hypot(px - sx, py - sy);
          if (d < closestDist) {
            closestDist = d;
            closest = i;
          }
        }
      } else {
        for (let i = 0; i < data.length; i++) {
          const pos = currentRef.current[i];
          if (!pos) continue;
          const px = pos[0] * t.scale + container.clientWidth / 2 + t.x;
          const py = pos[1] * t.scale + container.clientHeight / 2 + t.y;
          const d = Math.hypot(px - sx, py - sy);
          if (d < closestDist) {
            closestDist = d;
            closest = i;
          }
        }
      }

      const prevClosest = hoveredRef.current;
      hoveredRef.current = closest;
      setHoveredIndex(closest);

      if (closest !== prevClosest) {
        if (closest >= 0) {
          const point = data[closest];
          const key = groupKey(point, clusteringDimension);
          const pos = currentRef.current[closest];
          onTooltip({
            ticketId: point.id,
            reason: point.reassignment_reason || "(unassigned)",
            queue: point.ticket_queue || "(unassigned)",
            issue: point.category || point.issue_category || "(uncategorized)",
            centrality: point.centrality ?? point.opacity_score ?? 0,
            coordinates: [pos?.[0] ?? 0, pos?.[1] ?? 0, 0],
            eigenvectors: point.eigenvectors ?? [],
            queueCorrelation: queueCorrelation.get(key) ?? [],
          });
        } else {
          onTooltip(null);
        }
      }
    },
    [data, onTooltip, clusteringDimension, queueCorrelation, is3DMode, viewMode, territoryOffsets],
  );

  const handlePointerLeave = useCallback(() => {
    hoveredRef.current = null;
    setHoveredIndex(null);
    onTooltip(null);
  }, [onTooltip]);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isPanning.current = true;
    const t = transformRef.current;
    panStart.current = { x: e.clientX - t.x, y: e.clientY - t.y };
    yawRef.current; // capture for closure
  }, []);

  const handlePointerUp = useCallback(() => {
    isPanning.current = false;
  }, []);

  const handlePointerMovePan = useCallback(
    (e: React.PointerEvent) => {
      if (!isPanning.current) return;
      const t = transformRef.current;
      if (is3DMode) {
        const dx = e.clientX - (panStart.current.x + t.x);
        const dy = e.clientY - (panStart.current.y + t.y);
        const sens = 0.01;
        yawRef.current += dx * sens;
        pitchRef.current += dy * sens;
        panStart.current = { x: e.clientX - t.x, y: e.clientY - t.y };
      } else {
        t.x = e.clientX - panStart.current.x;
        t.y = e.clientY - panStart.current.y;
        setTransform({ x: t.x, y: t.y, scale: t.scale });
      }
    },
    [is3DMode],
  );

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.92 : 1 / 0.92;
    const t = transformRef.current;
    const maxAllowed = Math.max(MAX_SCALE, fitScaleRef.current * MAX_EFFECTIVE_SCALE);
    t.scale = Math.min(maxAllowed, Math.max(MIN_SCALE, t.scale * delta));
    setTransform({ x: t.x, y: t.y, scale: t.scale });
  }, []);

  const colorIndex = hoveredIndex !== null ? hoveredIndex : -1;
  const hoverColor =
    colorIndex >= 0
      ? `rgb(${colorArray[colorIndex * 3] * 255 | 0},${colorArray[colorIndex * 3 + 1] * 255 | 0},${colorArray[colorIndex * 3 + 2] * 255 | 0})`
      : undefined;

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", position: "relative", overflow: "hidden", background: "#050505" }}
      onWheel={handleWheel}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMovePan}
      onPointerLeave={handlePointerUp}
    >
      <canvas
        ref={canvasRef}
        style={{ display: "block", width: "100%", height: "100%", cursor: isPanning.current ? "grabbing" : "grab" }}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
      />

      {hoveredIndex !== null && hoverColor && (
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 20,
            padding: "10px 14px",
            borderRadius: 12,
            background: "rgba(8, 8, 10, 0.72)",
            border: "1px solid rgba(255,255,255,0.10)",
            boxShadow: "0 22px 60px rgba(0,0,0,0.42)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            fontFamily: "'Geist Mono', 'SF Mono', monospace",
            fontSize: 10,
            color: "rgba(255,255,255,0.74)",
            pointerEvents: "none",
            whiteSpace: "nowrap",
          }}
        >
          <div style={{ color: hoverColor, fontSize: 11, fontWeight: 700, marginBottom: 2 }}>
            {data[hoveredIndex].category || data[hoveredIndex].issue_category || "point"}
            {data[hoveredIndex].is_anomaly ? " ⚡" : ""}
          </div>
          <div style={{ color: "rgba(255,255,255,0.65)" }}>{data[hoveredIndex].id}</div>
          <div>centrality {formatPercentage(data[hoveredIndex].centrality ?? data[hoveredIndex].opacity_score ?? 0)}</div>
          <div>reason {data[hoveredIndex].reassignment_reason || "(unassigned)"}</div>
        </div>
      )}
    </div>
  );
});

interface ScatterCanvasProps {
  refreshKey?: number;
  viewMode: ViewMode;
  clusteringDimension: ClusteringDimension;
  semanticMode: boolean;
  is3DMode: boolean;
  focusedCluster: string | null;
  onFocusCluster: (key: string | null) => void;
  onPaletteChange?: (palette: Map<string, string>) => void;
}

const ScatterCanvas = forwardRef<ZoomActions, ScatterCanvasProps>(function ScatterCanvas({
  refreshKey = 0,
  viewMode,
  clusteringDimension,
  semanticMode,
  is3DMode,
  focusedCluster,
  onFocusCluster,
  onPaletteChange,
}, ref) {
  const { data, territoryOffsets, loading, error } = useScatterCanvas(
    refreshKey,
    viewMode,
    clusteringDimension,
  );
  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);

  const canvasRef = useRef<ZoomActions>(null);

  useImperativeHandle(ref, () => ({
    zoomIn: () => canvasRef.current?.zoomIn(),
    zoomOut: () => canvasRef.current?.zoomOut(),
    fit: () => canvasRef.current?.fit(),
    getPalette: () => canvasRef.current?.getPalette() ?? new Map(),
    focusCluster: (key: string | null) => {
      canvasRef.current?.focusCluster(key);
      onFocusCluster(key);
    },
    getFocusedCluster: () => canvasRef.current?.getFocusedCluster() ?? null,
  }), [onFocusCluster]);

  if (loading && data.length === 0) {
    return <div style={stateStyle}>loading spatial coordinates...</div>;
  }

  if (error) {
    return <div style={{ ...stateStyle, padding: 28, textAlign: "center", lineHeight: 1.7 }}>{error}</div>;
  }

  if (data.length === 0) {
    return <div style={stateStyle}>no data available</div>;
  }

  const isGlobalConvergence = viewMode === "global" && !semanticMode;

  return (
    <div style={{ display: "flex", width: "100%", height: "100%", background: "#050505", overflow: "hidden" }}>
      <div style={{ flex: isGlobalConvergence ? "1 1 50%" : "1 1 100%", height: "100%", position: "relative", minWidth: 0 }}>
        <Canvas2D
          ref={canvasRef}
          data={data}
          territoryOffsets={territoryOffsets}
          viewMode={viewMode}
          clusteringDimension={clusteringDimension}
          semanticMode={semanticMode}
          is3DMode={is3DMode}
          focusedCluster={focusedCluster}
          onTooltip={setTooltip}
          onPaletteChange={onPaletteChange}
        />

        {tooltip && (
          <div
            style={{
              position: "absolute",
              left: 16,
              bottom: 16,
              zIndex: 20,
              padding: "10px 12px",
              borderRadius: 12,
              background: "rgba(8, 8, 10, 0.70)",
              border: "1px solid rgba(255,255,255,0.10)",
              backdropFilter: "blur(16px)",
              WebkitBackdropFilter: "blur(16px)",
              fontFamily: "'Geist Mono', monospace",
              fontSize: 10,
              color: "rgba(255,255,255,0.74)",
              pointerEvents: "none",
            }}
          >
            <div style={{ color: "#FFFFFF", fontSize: 11, marginBottom: 4 }}>{tooltip.ticketId}</div>
            <div>centrality {formatPercentage(tooltip.centrality)}</div>
            <div>reason {tooltip.reason}</div>
            <div>category {tooltip.issue}</div>
          </div>
        )}
      </div>

      {isGlobalConvergence && (
        <div style={{
          width: "50%",
          height: "100%",
          borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#050505",
          boxSizing: "border-box",
          zIndex: 10,
          position: "relative",
          overflow: "hidden"
        }}>
          <EigenVectorSpace3D refreshKey={refreshKey} />
        </div>
      )}
    </div>
  );
});

function EigenVectorSpace3D({ refreshKey }: { refreshKey: number }) {
  const [angleX] = useState(0.42);
  const [angleY, setAngleY] = useState(0.5);
  const [unfilteredData, setUnfilteredData] = useState<SemanticPoint[]>([]);
  const [autoRotate, setAutoRotate] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getDashboardFeed(refreshKey)
      .then((payload) => {
        if (!cancelled && payload.ui_cloud_data) {
          setUnfilteredData(payload.ui_cloud_data);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  useEffect(() => {
    if (!autoRotate) return;
    let frameId: number;
    const animate = () => {
      setAngleY((prev) => (prev + 0.004) % (Math.PI * 2));
      frameId = requestAnimationFrame(animate);
    };
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [autoRotate]);

  const project = (x: number, y: number, z: number): [number, number, number] => {
    const cosY = Math.cos(angleY);
    const sinY = Math.sin(angleY);
    const x1 = x * cosY - z * sinY;
    const z1 = x * sinY + z * cosY;

    const cosX = Math.cos(angleX);
    const sinX = Math.sin(angleX);
    const y2 = y * cosX - z1 * sinX;
    const z2 = y * sinX + z1 * cosX;

    const scale = 175;
    return [260 + x1 * scale, 260 - y2 * scale, z2];
  };

  const origin = project(0, 0, 0);
  const axis0_end = project(1.3, 0, 0);
  const axis1_end = project(0, 1.3, 0);
  const axis2_end = project(0, 0, 1.3);

  // Guide Cube vertices
  const cubeCoords = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1]
  ];
  const cube = cubeCoords.map(([cx, cy, cz]) => project(cx * 1.05, cy * 1.05, cz * 1.05));

  const samplePoints = useMemo(() => {
    if (!unfilteredData || unfilteredData.length === 0) return [];
    
    let maxAbs = 0.001;
    for (const pt of unfilteredData) {
      maxAbs = Math.max(maxAbs, Math.abs(pt.x), Math.abs(pt.y), Math.abs(pt.z));
    }

    const step = Math.max(1, Math.floor(unfilteredData.length / 280));
    const list: any[] = [];
    for (let i = 0; i < unfilteredData.length; i += step) {
      if (list.length >= 280) break;
      const pt = unfilteredData[i];
      const nx = pt.x / maxAbs;
      const ny = pt.y / maxAbs;
      const nz = pt.z / maxAbs;
      const proj = project(nx * 0.95, ny * 0.95, nz * 0.95);

      let color = "#3B82F6";
      let glowColor = "rgba(59, 130, 246, 0.6)";
      if (pt.color_axis === 1) {
        color = "#10B981";
        glowColor = "rgba(16, 185, 129, 0.6)";
      } else if (pt.color_axis === 2) {
        color = "#EF4444";
        glowColor = "rgba(239, 68, 68, 0.6)";
      }

      list.push({
        x: proj[0],
        y: proj[1],
        depth: proj[2],
        color,
        glowColor,
        isAnomaly: pt.is_anomaly
      });
    }
    return list;
  }, [unfilteredData, angleY]);

  return (
    <div style={{
      position: "relative",
      width: 520,
      height: 520,
      background: "radial-gradient(circle at center, rgba(10, 10, 16, 0.45) 0%, rgba(3, 3, 5, 0.98) 85%)",
      borderRadius: "50%",
      border: "1px solid rgba(255, 255, 255, 0.06)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      overflow: "visible",
      boxShadow: "inset 0 0 80px rgba(0,0,0,0.9), 0 25px 90px rgba(0,0,0,0.85)",
    }}>
      {/* HUD Scanner Scanlines Effect */}
      <div style={{
        position: "absolute",
        inset: 0,
        borderRadius: "50%",
        pointerEvents: "none",
        background: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.04), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.04))",
        backgroundSize: "100% 4px, 6px 100%",
        opacity: 0.8,
      }} />

      <svg width="520" height="520" style={{ pointerEvents: "none", overflow: "visible" }}>
        <defs>
          {/* Neon Glow Filters */}
          <filter id="glow-blue" filterUnits="userSpaceOnUse" x="0" y="0" width="520" height="520">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-green" filterUnits="userSpaceOnUse" x="0" y="0" width="520" height="520">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-red" filterUnits="userSpaceOnUse" x="0" y="0" width="520" height="520">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Gradients */}
          <linearGradient id="grad-blue" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1E40AF" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
          <linearGradient id="grad-green" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#065F46" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>
          <linearGradient id="grad-red" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#991B1B" />
            <stop offset="100%" stopColor="#EF4444" />
          </linearGradient>

          {/* Arrow markers */}
          <marker id="arrow0" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#3B82F6" />
          </marker>
          <marker id="arrow1" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#10B981" />
          </marker>
          <marker id="arrow2" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="#EF4444" />
          </marker>
        </defs>

        {/* Outer Circular Telemetry Compass Grid */}
        <circle cx="260" cy="260" r="230" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1.5" />
        <circle cx="260" cy="260" r="200" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="1" strokeDasharray="5,8" />
        <circle cx="260" cy="260" r="160" fill="none" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="0.75" />
        <circle cx="260" cy="260" r="100" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="0.5" strokeDasharray="3,10" />

        {/* Outer Tick Marks */}
        {Array.from({ length: 12 }).map((_, i) => {
          const angle = (i * Math.PI) / 6;
          const x1 = 260 + Math.cos(angle) * 230;
          const y1 = 260 + Math.sin(angle) * 230;
          const x2 = 260 + Math.cos(angle) * 224;
          const y2 = 260 + Math.sin(angle) * 224;
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1" />;
        })}

        {/* Guide Cube - Face 1 (bottom) */}
        <line x1={cube[0][0]} y1={cube[0][1]} x2={cube[1][0]} y2={cube[1][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[1][0]} y1={cube[1][1]} x2={cube[2][0]} y2={cube[2][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[2][0]} y1={cube[2][1]} x2={cube[3][0]} y2={cube[3][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[3][0]} y1={cube[3][1]} x2={cube[0][0]} y2={cube[0][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />

        {/* Guide Cube - Face 2 (top) */}
        <line x1={cube[4][0]} y1={cube[4][1]} x2={cube[5][0]} y2={cube[5][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[5][0]} y1={cube[5][1]} x2={cube[6][0]} y2={cube[6][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[6][0]} y1={cube[6][1]} x2={cube[7][0]} y2={cube[7][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[7][0]} y1={cube[7][1]} x2={cube[4][0]} y2={cube[4][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />

        {/* Guide Cube - Pillars */}
        <line x1={cube[0][0]} y1={cube[0][1]} x2={cube[4][0]} y2={cube[4][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[1][0]} y1={cube[1][1]} x2={cube[5][0]} y2={cube[5][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[2][0]} y1={cube[2][1]} x2={cube[6][0]} y2={cube[6][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />
        <line x1={cube[3][0]} y1={cube[3][1]} x2={cube[7][0]} y2={cube[7][1]} stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.75" strokeDasharray="3,3" />

        {/* Glowing Guide Planes */}
        <polygon points={`${origin[0]},${origin[1]} ${axis0_end[0]},${axis0_end[1]} ${axis1_end[0]},${axis1_end[1]}`} fill="rgba(37, 194, 110, 0.015)" />
        <polygon points={`${origin[0]},${origin[1]} ${axis0_end[0]},${axis0_end[1]} ${axis2_end[0]},${axis2_end[1]}`} fill="rgba(47, 107, 255, 0.015)" />

        {/* Dotted HUD Line Callouts from Arrow tips to HUD cards */}
        <line x1={axis0_end[0]} y1={axis0_end[1]} x2={axis0_end[0] + (axis0_end[0] > 260 ? 12 : -212)} y2={axis0_end[1]} stroke="#3B82F6" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
        <line x1={axis1_end[0]} y1={axis1_end[1]} x2={axis1_end[0] + (axis1_end[0] > 260 ? 12 : -212)} y2={axis1_end[1]} stroke="#10B981" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
        <line x1={axis2_end[0]} y1={axis2_end[1]} x2={axis2_end[0] + (axis2_end[0] > 260 ? 12 : -212)} y2={axis2_end[1]} stroke="#EF4444" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />

        {/* Core Glowing Axis Vectors */}
        <line x1={origin[0]} y1={origin[1]} x2={axis0_end[0]} y2={axis0_end[1]} stroke="#3B82F6" strokeWidth="2.5" markerEnd="url(#arrow0)" filter="url(#glow-blue)" />
        <line x1={origin[0]} y1={origin[1]} x2={axis1_end[0]} y2={axis1_end[1]} stroke="#10B981" strokeWidth="2.5" markerEnd="url(#arrow1)" filter="url(#glow-green)" />
        <line x1={origin[0]} y1={origin[1]} x2={axis2_end[0]} y2={axis2_end[1]} stroke="#EF4444" strokeWidth="2.5" markerEnd="url(#arrow2)" filter="url(#glow-red)" />

        {/* Ambient Origin Node */}
        <circle cx={origin[0]} cy={origin[1]} r="4" fill="#FFFFFF" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="2.5" />

        {/* Shaded Glowing Coordinates Data points */}
        {samplePoints.map((pt, idx) => (
          <g key={idx}>
            {pt.isAnomaly && (
              <circle
                cx={pt.x}
                cy={pt.y}
                r={6}
                fill="none"
                stroke={pt.color}
                opacity={0.3}
                strokeWidth="1"
                className="animate-ping"
              />
            )}
            <circle
              cx={pt.x}
              cy={pt.y}
              r={pt.isAnomaly ? 4 : 2}
              fill={pt.color}
              opacity={pt.depth > 0 ? 0.95 : 0.4}
              stroke={pt.isAnomaly ? "#FFFFFF" : "none"}
              strokeWidth={pt.isAnomaly ? 0.75 : 0}
              style={{
                filter: `drop-shadow(0 0 4px ${pt.glowColor})`,
                transition: "opacity 160ms ease"
              }}
            />
          </g>
        ))}

        {/* HUD Description Cards for Axis Labels */}
        {/* AXIS 0 Label HUD Card */}
        <g transform={`translate(${axis0_end[0] + (axis0_end[0] > 260 ? 12 : -212)}, ${axis0_end[1] - 12})`}>
          <rect width="200" height="24" rx="4" ry="4" fill="rgba(8, 8, 14, 0.9)" stroke="#3B82F6" strokeWidth="1" />
          <line x1="0" y1="0" x2="0" y2="24" stroke="#FFFFFF" strokeWidth="1.5" />
          <text x="10" y="15" fill="#93C5FD" fontSize="8" fontFamily="'Geist Mono', monospace" fontWeight="bold">
            AXIS 0: DOMESTIC CORE (64.3% • 2,313)
          </text>
        </g>

        {/* AXIS 1 Label HUD Card */}
        <g transform={`translate(${axis1_end[0] + (axis1_end[0] > 260 ? 12 : -212)}, ${axis1_end[1] - 12})`}>
          <rect width="200" height="24" rx="4" ry="4" fill="rgba(8, 8, 14, 0.9)" stroke="#10B981" strokeWidth="1" />
          <line x1="0" y1="0" x2="0" y2="24" stroke="#FFFFFF" strokeWidth="1.5" />
          <text x="10" y="15" fill="#6EE7B7" fontSize="8" fontFamily="'Geist Mono', monospace" fontWeight="bold">
            AXIS 1: ESCALATIONS (20.8% • 748)
          </text>
        </g>

        {/* AXIS 2 Label HUD Card */}
        <g transform={`translate(${axis2_end[0] + (axis2_end[0] > 260 ? 12 : -212)}, ${axis2_end[1] - 12})`}>
          <rect width="200" height="24" rx="4" ry="4" fill="rgba(8, 8, 14, 0.9)" stroke="#EF4444" strokeWidth="1" />
          <line x1="0" y1="0" x2="0" y2="24" stroke="#FFFFFF" strokeWidth="1.5" />
          <text x="10" y="15" fill="#FCA5A5" fontSize="8" fontFamily="'Geist Mono', monospace" fontWeight="bold">
            AXIS 2: ROAMING (14.9% • 536)
          </text>
        </g>
      </svg>

      {/* Futuristic Compass Controls & Telemetry Data HUD */}
      <div style={{
        position: "absolute",
        bottom: 24,
        left: 24,
        display: "flex",
        flexDirection: "column",
        gap: 4,
        fontFamily: "'Geist Mono', monospace",
        fontSize: 8,
        color: "rgba(255,255,255,0.4)",
        letterSpacing: "0.08em",
        background: "rgba(8, 8, 10, 0.65)",
        border: "1px solid rgba(255,255,255,0.06)",
        padding: "8px 12px",
        borderRadius: 8,
        backdropFilter: "blur(6px)",
      }}>
        <div style={{ color: "#FFFFFF", fontWeight: "bold", fontSize: 9, marginBottom: 2 }}>OPERATIONAL EIGEN SPACE</div>
        <div>VECTORS ACTIVE: 3</div>
        <div>SAMPLED DENSITY: 280 PTS</div>
        <div>STEREOSCOPIC GUIDE: WIREFRAME CUBE</div>
      </div>

      <div style={{
        position: "absolute",
        bottom: 24,
        right: 24,
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: 8,
        fontFamily: "'Geist Mono', monospace",
        color: "rgba(255,255,255,0.5)",
        letterSpacing: "0.08em",
        background: "rgba(8, 8, 10, 0.65)",
        border: "1px solid rgba(255,255,255,0.06)",
        padding: "6px 12px",
        borderRadius: 8,
        backdropFilter: "blur(6px)",
        pointerEvents: "auto",
        cursor: "pointer",
        transition: "all 140ms ease"
      }} onClick={() => setAutoRotate(!autoRotate)}>
        <span style={{
          display: "inline-block",
          width: 5,
          height: 5,
          borderRadius: "50%",
          background: autoRotate ? "#10B981" : "#EF4444",
          boxShadow: autoRotate ? "0 0 6px #10B981" : "0 0 6px #EF4444"
        }} />
        <span>{autoRotate ? "AUTO-ORBIT: ON" : "ORBIT LOCKED"}</span>
      </div>
    </div>
  );
}

export default ScatterCanvas;
