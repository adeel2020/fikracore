"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useFikraCore } from "@/lib/fikracore-context";
import { cn } from "@/lib/utils";

export type ReasoningCoreHUDMode =
  | "IDLE"
  | "OBSERVING"
  | "CORRELATING"
  | "SYNTHESIZING"
  | "TESTING"
  | "NEEDS_EVIDENCE"
  | "CONVERGING"
  | "VALIDATING"
  | "CONFIRMED"
  | "MODEL_INSUFFICIENT";

interface FikraCore3DOrbProps {
  size?: number;
  isHovered?: boolean;
  onHover?: (hovered: boolean) => void;
  onClick?: () => void;
  isLight?: boolean;
  mode?: ReasoningCoreHUDMode;
}

export function FikraCore3DOrb({
  size = 118,
  isHovered = false,
  onHover,
  onClick,
  isLight: propIsLight,
  mode = "CONVERGING",
}: FikraCore3DOrbProps) {
  let contextTheme: "dark" | "light" | undefined;
  try {
    const ctx = useFikraCore();
    contextTheme = ctx?.theme;
  } catch {
    // fallback if outside provider
  }
  const isLight = propIsLight ?? contextTheme === "light";

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [internalHover, setInternalHover] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  const activeHover = isHovered || internalHover;

  // Mounted guard: the SVG HUD rings contain trig-computed floating-point coordinates
  // (Math.sin/cos × radius) that produce last-digit FP divergence between Node.js (SSR)
  // and the browser V8 engine. suppressHydrationWarning only applies to the element it is
  // placed on, not its subtree — so we render the SVG overlay client-only.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  // The inner sphere diameter inside the glass casing
  const sphereSize = size;
  const orbRadius = sphereSize / 2; // 58px when size=116
  const r1 = orbRadius + 8; // 66px (8px clear gap from orb)
  const r2 = r1 + 7; // 73px (7px clear gap from Ring 1)
  const r3 = r2 + 7; // 80px (7px clear gap from Ring 2, aligns with socket chassis)
  const hudRadius = r3 + 6; // 86px
  const hudSize = hudRadius * 2; // 172px
  const center = hudRadius; // 86px

  // State flags for HUD behavior
  const isIdle = mode === "IDLE";
  const isCorrelating = mode === "CORRELATING" || mode === "OBSERVING";
  const isSynthesizing = mode === "SYNTHESIZING" || mode === "CONVERGING";
  const isNeedsEvidence = mode === "NEEDS_EVIDENCE";
  const isValidating = mode === "VALIDATING" || mode === "TESTING";
  const isConfirmed = mode === "CONFIRMED";

  // Micro calibration tick marks for Ring 1 (12 ticks at 30 deg intervals)
  const innerTicks = useMemo(() => {
    return Array.from({ length: 12 }, (_, i) => {
      const rad = (i * 30 * Math.PI) / 180;
      return {
        x1: center + (r1 - 2.5) * Math.cos(rad),
        y1: center + (r1 - 2.5) * Math.sin(rad),
        x2: center + (r1 + 2.5) * Math.cos(rad),
        y2: center + (r1 + 2.5) * Math.sin(rad),
      };
    });
  }, [center, r1]);

  // Precision calibration tick marks for Ring 2 (24 ticks at 15 deg intervals)
  const midTicks = useMemo(() => {
    return Array.from({ length: 24 }, (_, i) => {
      const rad = (i * 15 * Math.PI) / 180;
      return {
        x1: center + (r2 - 2.5) * Math.cos(rad),
        y1: center + (r2 - 2.5) * Math.sin(rad),
        x2: center + (r2 + 2.5) * Math.cos(rad),
        y2: center + (r2 + 2.5) * Math.sin(rad),
      };
    });
  }, [center, r2]);

  // Ordinal alignment ticks for Ring 3 (4 ticks at 45, 135, 225, 315 deg)
  const outerOrdinalTicks = useMemo(() => {
    return [45, 135, 225, 315].map((deg) => {
      const rad = (deg * Math.PI) / 180;
      return {
        x1: center + (r3 - 3.5) * Math.cos(rad),
        y1: center + (r3 - 3.5) * Math.sin(rad),
        x2: center + (r3 + 3.5) * Math.cos(rad),
        y2: center + (r3 + 3.5) * Math.sin(rad),
      };
    });
  }, [center, r3]);

  // 4 Cardinal Anchor Sockets on Outer Ring (N, S, E, W)
  const cardinalAnchors = useMemo(
    () => [
      { id: "north", x: center, y: center - r3 },
      { id: "south", x: center, y: center + r3 },
      { id: "east", x: center + r3, y: center },
      { id: "west", x: center - r3, y: center },
    ],
    [center, r3]
  );

  // Dedicated gap arc for Ring 2
  const gapArc = useMemo(() => {
    const rad1 = (-50 * Math.PI) / 180;
    const rad2 = (-15 * Math.PI) / 180;
    const radMid = (-32.5 * Math.PI) / 180;
    const x1 = center + r2 * Math.cos(rad1);
    const y1 = center + r2 * Math.sin(rad1);
    const x2 = center + r2 * Math.cos(rad2);
    const y2 = center + r2 * Math.sin(rad2);
    const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${r2} ${r2} 0 0 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`;
    const pipX = center + r2 * Math.cos(radMid);
    const pipY = center + r2 * Math.sin(radMid);
    const pipPoints = `${pipX.toFixed(1)},${(pipY - 2.5).toFixed(1)} ${(pipX + 2.5).toFixed(1)},${pipY.toFixed(1)} ${pipX.toFixed(1)},${(pipY + 2.5).toFixed(1)} ${(pipX - 2.5).toFixed(1)},${pipY.toFixed(1)}`;
    return { d, pipPoints };
  }, [center, r2]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Three.js Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
    camera.position.set(0, 0, 3.2);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }

    renderer.setSize(sphereSize, sphereSize);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // ─── 3D ROTATING CELESTIAL NEURAL CONSTELLATION GRAPH ───────────────────
    const neuralGroup = new THREE.Group();
    rootGroup.add(neuralGroup);

    const nodePoints: THREE.Vector3[] = [];
    const positions: number[] = [];
    const colors: number[] = [];

    const cyanColor = isLight ? new THREE.Color(0x0284c7) : new THREE.Color(0x00f0ff);
    const electricBlue = isLight ? new THREE.Color(0x0369a1) : new THREE.Color(0x38bdf8);
    const deepBlue = isLight ? new THREE.Color(0x1e3a8a) : new THREE.Color(0x1d4ed8);
    const violetColor = isLight ? new THREE.Color(0x6b21a8) : new THREE.Color(0xa855f7);
    const magentaColor = isLight ? new THREE.Color(0xbe185d) : new THREE.Color(0xec4899);

    // Distribute ~110 neural constellation nodes within a spherical volume
    const nodeCount = 110;
    const goldenRatio = (1 + Math.sqrt(5)) / 2;

    for (let i = 0; i < nodeCount; i++) {
      const theta = (2 * Math.PI * i) / goldenRatio;
      const phi = Math.acos(1 - (2 * (i + 0.5)) / nodeCount);
      // Vary radii between 0.38 and 0.88 for depth
      const r = 0.38 + 0.48 * Math.pow(Math.sin(i * 3.7), 2);

      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);

      const vec = new THREE.Vector3(x, y, z);
      nodePoints.push(vec);
      positions.push(x, y, z);

      // Color mapping matching reference image: cyan, violet, magenta, and blue sparks
      const col = new THREE.Color();
      const rand = Math.random();
      if (rand < 0.45) {
        col.copy(cyanColor);
      } else if (rand < 0.7) {
        col.copy(electricBlue);
      } else if (rand < 0.88) {
        col.copy(violetColor);
      } else {
        col.copy(magentaColor);
      }

      colors.push(col.r, col.g, col.b);
    }

    // Node Points Mesh
    const nodesGeo = new THREE.BufferGeometry();
    nodesGeo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    nodesGeo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

    const nodesMat = new THREE.PointsMaterial({
      size: 0.085,
      vertexColors: true,
      transparent: true,
      opacity: isLight ? 0.85 : 0.95,
      blending: isLight ? THREE.NormalBlending : THREE.AdditiveBlending,
    });
    const pointsMesh = new THREE.Points(nodesGeo, nodesMat);
    neuralGroup.add(pointsMesh);

    // Synaptic Connecting Filaments / Axon lines
    const linePositions: number[] = [];
    const lineColors: number[] = [];

    for (let i = 0; i < nodePoints.length; i++) {
      for (let j = i + 1; j < nodePoints.length; j++) {
        const dist = nodePoints[i].distanceTo(nodePoints[j]);
        if (dist < 0.36) {
          linePositions.push(nodePoints[i].x, nodePoints[i].y, nodePoints[i].z);
          linePositions.push(nodePoints[j].x, nodePoints[j].y, nodePoints[j].z);

          const alpha = Math.pow(1 - dist / 0.36, 1.4) * (isLight ? 0.4 : 0.7);
          lineColors.push(cyanColor.r * alpha, cyanColor.g * alpha, cyanColor.b * alpha);
          lineColors.push(deepBlue.r * alpha, deepBlue.g * alpha, deepBlue.b * alpha);
        }
      }
    }

    const linesGeo = new THREE.BufferGeometry();
    linesGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    linesGeo.setAttribute("color", new THREE.Float32BufferAttribute(lineColors, 3));

    const linesMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: isLight ? 0.45 : 0.65,
      blending: isLight ? THREE.NormalBlending : THREE.AdditiveBlending,
    });
    const linesMesh = new THREE.LineSegments(linesGeo, linesMat);
    neuralGroup.add(linesMesh);

    // Glowing Central Core Nucleus (Inner Energy Sphere)
    const nucleusGeo = new THREE.SphereGeometry(0.25, 16, 16);
    const nucleusMat = new THREE.MeshBasicMaterial({
      color: isLight ? 0x0284c7 : 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.2 : 0.25,
      blending: isLight ? THREE.NormalBlending : THREE.AdditiveBlending,
    });
    const nucleus = new THREE.Mesh(nucleusGeo, nucleusMat);
    neuralGroup.add(nucleus);

    // ─── Animation Loop ──────────────────────────────────────────────────────
    let animationFrameId: number;
    let clock = 0;
    let targetRotY = 0;
    let targetRotX = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      clock += 0.016;

      // 3D smooth continuous rotation of the constellation
      neuralGroup.rotation.y += activeHover ? 0.022 : 0.012;
      neuralGroup.rotation.x = Math.sin(clock * 0.4) * 0.08;
      neuralGroup.rotation.z = Math.cos(clock * 0.3) * 0.05;

      // Nucleus pulse
      nucleus.rotation.y -= 0.025;
      const pulseScale = 1.0 + Math.sin(clock * 2.8) * 0.08;
      nucleus.scale.set(pulseScale, pulseScale, pulseScale);

      // Smooth mouse tilt parallax
      rootGroup.rotation.y += (targetRotY - rootGroup.rotation.y) * 0.06;
      rootGroup.rotation.x += (targetRotX - rootGroup.rotation.x) * 0.06;

      renderer.render(scene, camera);
    };

    animate();

    const handleMouseMove = (e: MouseEvent) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      targetRotY = x * 0.6;
      targetRotX = -y * 0.6;
      setTilt({ x: -y * 10, y: x * 10 });
    };

    const handleMouseLeave = () => {
      targetRotY = 0;
      targetRotX = 0;
      setTilt({ x: 0, y: 0 });
    };

    const containerEl = containerRef.current;
    if (containerEl) {
      containerEl.addEventListener("mousemove", handleMouseMove);
      containerEl.addEventListener("mouseleave", handleMouseLeave);
    }

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (containerEl) {
        containerEl.removeEventListener("mousemove", handleMouseMove);
        containerEl.removeEventListener("mouseleave", handleMouseLeave);
      }
      nodesGeo.dispose();
      nodesMat.dispose();
      linesGeo.dispose();
      linesMat.dispose();
      nucleusGeo.dispose();
      nucleusMat.dispose();
      renderer.dispose();
    };
  }, [sphereSize, activeHover, isLight]);

  return (
    <div
      ref={containerRef}
      onMouseEnter={() => {
        setInternalHover(true);
        onHover?.(true);
      }}
      onMouseLeave={() => {
        setInternalHover(false);
        onHover?.(false);
      }}
      onClick={onClick}
      style={{
        width: hudSize,
        height: hudSize,
        transform: `perspective(700px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        transition: "transform 0.15s ease-out",
      }}
      className="relative flex items-center justify-center select-none cursor-pointer group shrink-0 rounded-full"
    >
      {/* ── 1. 3 CONCENTRIC HUD RINGS (Layered around the central Reasoning Core) ── */}
      {/* SSR renders an empty placeholder; client renders the full trig-computed ring overlay.
          This avoids floating-point hydration mismatches on <line> x1/y1/x2/y2 attributes
          (Math.sin/cos produces last-digit divergence between Node.js SSR and browser V8).
          suppressHydrationWarning only covers the element it is placed on, not its subtree. */}
      {!mounted ? (
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none z-20 overflow-visible"
          viewBox={`0 0 ${hudSize} ${hudSize}`}
        />
      ) : (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-20 overflow-visible"
        viewBox={`0 0 ${hudSize} ${hudSize}`}
      >
        <defs>
          <filter id="orb-hud-cyan-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="1.0" result="tightGlow" />
            <feGaussianBlur stdDeviation="2.2" result="softGlow" />
            <feMerge>
              <feMergeNode in="softGlow" opacity="0.4" />
              <feMergeNode in="tightGlow" opacity="0.85" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="orb-hud-amber-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="1.2" result="tightGlow" />
            <feGaussianBlur stdDeviation="2.6" result="softGlow" />
            <feMerge>
              <feMergeNode in="softGlow" opacity="0.45" />
              <feMergeNode in="tightGlow" opacity="0.9" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="orb-hud-emerald-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="1.2" result="tightGlow" />
            <feGaussianBlur stdDeviation="2.6" result="softGlow" />
            <feMerge>
              <feMergeNode in="softGlow" opacity="0.45" />
              <feMergeNode in="tightGlow" opacity="0.9" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <style>{`
            @keyframes orbHudSpinCW {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
            @keyframes orbHudSpinCCW {
              from { transform: rotate(360deg); }
              to { transform: rotate(0deg); }
            }
            @keyframes orbHudAmberPulse {
              0%, 100% { stroke-opacity: 0.55; stroke-width: 1.4px; }
              50% { stroke-opacity: 1.0; stroke-width: 2.2px; }
            }
            .animate-orb-amber-pulse {
              animation: orbHudAmberPulse 1.8s ease-in-out infinite;
            }
          `}</style>
        </defs>

        {/* ── RING 1: INNER ACTIVE-REASONING RING (rotates clockwise) ── */}
        <g
          style={{
            transformOrigin: `${center}px ${center}px`,
            animation: isConfirmed
              ? "orbHudSpinCW 150s linear infinite"
              : isIdle
              ? "orbHudSpinCW 120s linear infinite"
              : "orbHudSpinCW 50s linear infinite",
          }}
        >
          {/* Base thin track */}
          <circle
            cx={center}
            cy={center}
            r={r1}
            fill="none"
            stroke={
              isConfirmed
                ? "#10b981"
                : isCorrelating
                ? isLight ? "#0284c7" : "#00f0ff"
                : isLight ? "#94a3b8" : "#38bdf8"
            }
            strokeWidth="0.75"
            strokeDasharray="2 6"
            strokeOpacity={
              isIdle
                ? 0.22
                : isCorrelating
                ? 0.85
                : isConfirmed
                ? 0.75
                : 0.4
            }
          />
          {/* Segmented active reasoning arcs (4 sectors) */}
          <circle
            cx={center}
            cy={center}
            r={r1}
            fill="none"
            stroke={
              isConfirmed
                ? "#10b981"
                : isCorrelating
                ? isLight ? "#0284c7" : "#00f0ff"
                : isLight ? "#0369a1" : "#38bdf8"
            }
            strokeWidth={isCorrelating ? 1.5 : 0.9}
            strokeDasharray="34 19"
            strokeOpacity={
              isIdle
                ? 0.22
                : isCorrelating
                ? 0.95
                : isConfirmed
                ? 0.85
                : 0.5
            }
            filter={
              isCorrelating
                ? "url(#orb-hud-cyan-glow)"
                : isConfirmed
                ? "url(#orb-hud-emerald-glow)"
                : undefined
            }
          />
          {/* 12 micro active-reasoning tick marks */}
          {innerTicks.map((t, i) => (
            <line
              key={`inner-tick-${i}`}
              x1={t.x1}
              y1={t.y1}
              x2={t.x2}
              y2={t.y2}
              stroke={
                isConfirmed
                  ? "#10b981"
                  : isCorrelating
                  ? isLight ? "#0284c7" : "#00f0ff"
                  : isLight ? "#64748b" : "#475569"
              }
              strokeWidth="0.65"
              strokeOpacity={isIdle ? 0.2 : isCorrelating ? 0.9 : 0.45}
            />
          ))}
        </g>

        {/* ── RING 2: MIDDLE CONVERGENCE/SYNTHESIS RING (rotates counter-clockwise) ── */}
        <g
          style={{
            transformOrigin: `${center}px ${center}px`,
            animation: isConfirmed
              ? "orbHudSpinCCW 180s linear infinite"
              : isIdle
              ? "orbHudSpinCCW 140s linear infinite"
              : "orbHudSpinCCW 65s linear infinite",
          }}
        >
          {/* Base thin track */}
          <circle
            cx={center}
            cy={center}
            r={r2}
            fill="none"
            stroke={
              isConfirmed
                ? "#10b981"
                : isNeedsEvidence
                ? "#f59e0b"
                : isSynthesizing
                ? isLight ? "#0284c7" : "#00f0ff"
                : isLight ? "#94a3b8" : "#38bdf8"
            }
            strokeWidth="0.8"
            strokeDasharray="3 7"
            strokeOpacity={
              isIdle
                ? 0.2
                : isSynthesizing
                ? 0.8
                : 0.35
            }
          />
          {/* Segmented convergence arcs (4 quadrant sectors) */}
          <circle
            cx={center}
            cy={center}
            r={r2}
            fill="none"
            stroke={
              isConfirmed
                ? "#10b981"
                : isSynthesizing
                ? isLight ? "#0284c7" : "#00f0ff"
                : isLight ? "#0369a1" : "#00f0ff"
            }
            strokeWidth={isSynthesizing ? 1.6 : 0.9}
            strokeDasharray="46 17"
            strokeOpacity={
              isIdle
                ? 0.2
                : isSynthesizing
                ? 0.95
                : isConfirmed
                ? 0.85
                : 0.45
            }
            filter={
              isSynthesizing
                ? "url(#orb-hud-cyan-glow)"
                : isConfirmed
                ? "url(#orb-hud-emerald-glow)"
                : undefined
            }
          />
          {/* 24 precision calibration tick marks */}
          {midTicks.map((t, i) => (
            <line
              key={`mid-tick-${i}`}
              x1={t.x1}
              y1={t.y1}
              x2={t.x2}
              y2={t.y2}
              stroke={
                isConfirmed
                  ? "#10b981"
                  : isSynthesizing
                  ? isLight ? "#0284c7" : "#00f0ff"
                  : isLight ? "#64748b" : "#475569"
              }
              strokeWidth="0.6"
              strokeOpacity={isIdle ? 0.15 : isSynthesizing ? 0.8 : 0.35}
            />
          ))}
          {/* Dedicated Evidence/Gap Segment Arc */}
          <path
            d={gapArc.d}
            fill="none"
            stroke={
              isNeedsEvidence
                ? "#f59e0b"
                : isConfirmed
                ? "#10b981"
                : isLight ? "#0284c7" : "#00f0ff"
            }
            strokeWidth={isNeedsEvidence ? 1.8 : 1.0}
            strokeOpacity={isNeedsEvidence ? 1.0 : isIdle ? 0.2 : 0.5}
            filter={isNeedsEvidence ? "url(#orb-hud-amber-glow)" : undefined}
            className={isNeedsEvidence ? "animate-orb-amber-pulse" : undefined}
          />
          {/* Amber pip indicator when NEEDS_EVIDENCE */}
          {isNeedsEvidence && (
            <polygon
              points={gapArc.pipPoints}
              fill="#f59e0b"
              filter="url(#orb-hud-amber-glow)"
            />
          )}
        </g>

        {/* ── RING 3: OUTER INTERFACE/CONNECTION RING (mostly static, anchors sockets) ── */}
        <g>
          {/* Outer Socket Circular Track */}
          <circle
            cx={center}
            cy={center}
            r={r3}
            fill="none"
            stroke={
              isConfirmed
                ? "#10b981"
                : isValidating
                ? isLight ? "#0284c7" : "#00f0ff"
                : isLight ? "#0284c7" : "#00f0ff"
            }
            strokeWidth={isValidating ? 1.3 : 0.85}
            strokeDasharray="2 5"
            strokeOpacity={
              isIdle
                ? 0.22
                : isValidating
                ? 0.95
                : isConfirmed
                ? 0.85
                : isLight ? 0.35 : 0.3
            }
            filter={
              isValidating
                ? "url(#orb-hud-cyan-glow)"
                : isConfirmed
                ? "url(#orb-hud-emerald-glow)"
                : undefined
            }
          />
          {/* Ordinal alignment tick marks at 45, 135, 225, 315 deg */}
          {outerOrdinalTicks.map((t, i) => (
            <line
              key={`outer-tick-${i}`}
              x1={t.x1}
              y1={t.y1}
              x2={t.x2}
              y2={t.y2}
              stroke={
                isConfirmed
                  ? "#10b981"
                  : isValidating
                  ? isLight ? "#0284c7" : "#00f0ff"
                  : isLight ? "#64748b" : "#475569"
              }
              strokeWidth="0.9"
              strokeOpacity={
                isIdle
                  ? 0.2
                  : (isValidating || isConfirmed)
                  ? 0.9
                  : 0.5
              }
            />
          ))}
          {/* 4 Cardinal Anchor Sockets on Outer Ring (N, S, E, W) */}
          {cardinalAnchors.map((anc) => (
            <g key={`cardinal-anchor-${anc.id}`}>
              {/* Structural socket mounting collar */}
              <circle
                cx={anc.x}
                cy={anc.y}
                r={3.4}
                fill={isLight ? "#f8fafc" : "#020617"}
                stroke={
                  isConfirmed
                    ? "#10b981"
                    : isValidating
                    ? isLight ? "#0284c7" : "#00f0ff"
                    : isLight ? "#94a3b8" : "#334155"
                }
                strokeWidth="0.85"
                strokeOpacity={
                  isIdle
                    ? 0.25
                    : (isValidating || isConfirmed)
                    ? 0.9
                    : 0.6
                }
              />
              {/* Center optical indicator pin */}
              <circle
                cx={anc.x}
                cy={anc.y}
                r={1.3}
                fill={
                  isConfirmed
                    ? "#10b981"
                    : isValidating
                    ? "#ffffff"
                    : isLight ? "#0284c7" : "#38bdf8"
                }
                fillOpacity={
                  isIdle
                    ? 0.25
                    : (isValidating || isConfirmed)
                    ? 1.0
                    : 0.6
                }
                filter={
                  (isValidating || isConfirmed)
                    ? "url(#orb-hud-cyan-glow)"
                    : undefined
                }
              />
            </g>
          ))}
        </g>
      </svg>
      )}

      {/* ── 2. CENTRAL VOLUMETRIC GLOWING GLASS SPHERE ── */}
      <div
        style={{ width: sphereSize, height: sphereSize }}
        className="relative rounded-full flex items-center justify-center overflow-hidden z-10 transition-all duration-300 shadow-2xl"
      >
        {/* 3D Sphere Radial Atmosphere */}
        <div
          className="absolute inset-0 rounded-full pointer-events-none transition-all duration-300"
          style={{
            background: isLight
              ? "radial-gradient(circle at 48% 46%, rgba(255, 255, 255, 0.98) 0%, rgba(235, 248, 255, 0.95) 50%, rgba(214, 241, 253, 0.92) 85%, rgba(186, 230, 253, 0.9) 100%)"
              : "radial-gradient(circle at 48% 46%, rgba(4, 25, 60, 0.94) 0%, rgba(2, 12, 32, 0.98) 65%, rgba(1, 6, 18, 1) 100%)",
            boxShadow: isLight
              ? activeHover
                ? "inset 0 0 24px rgba(2, 132, 199, 0.45), inset 0 0 10px rgba(255,255,255,0.9), 0 0 35px rgba(2, 132, 199, 0.35)"
                : "inset 0 0 18px rgba(2, 132, 199, 0.3), inset 0 0 8px rgba(255,255,255,0.8), 0 0 24px rgba(2, 132, 199, 0.22)"
              : activeHover
              ? "inset 0 0 28px rgba(0,240,255,0.9), inset 0 0 10px rgba(255,255,255,0.8), 0 0 42px rgba(0,240,255,0.85)"
              : "inset 0 0 22px rgba(0,240,255,0.7), inset 0 0 6px rgba(255,255,255,0.6), 0 0 30px rgba(0,229,255,0.55)",
            border: isLight
              ? activeHover
                ? "2px solid rgba(2, 132, 199, 1)"
                : "1.8px solid rgba(2, 132, 199, 0.75)"
              : activeHover
              ? "2px solid rgba(0, 240, 255, 1)"
              : "1.8px solid rgba(0, 229, 255, 0.85)",
          }}
        />

        {/* 3D Curved Specular Glass Sheen */}
        <div
          className="absolute top-1 left-2.5 w-14 h-7 rounded-full pointer-events-none -rotate-[28deg] opacity-75"
          style={{
            background: isLight
              ? "radial-gradient(ellipse at center, rgba(255,255,255,0.95) 0%, rgba(186,230,253,0.5) 40%, rgba(255,255,255,0) 80%)"
              : "radial-gradient(ellipse at center, rgba(255,255,255,0.85) 0%, rgba(0,240,255,0.4) 40%, rgba(255,255,255,0) 80%)",
            filter: "blur(1.2px)",
          }}
        />

        {/* Three.js 3D Rotating Constellation Canvas */}
        <canvas
          ref={canvasRef}
          width={sphereSize}
          height={sphereSize}
          className="absolute inset-0 rounded-full pointer-events-none z-10"
        />

        {/* ── 2. FLOATING HUD TYPOGRAPHY (Matches master reference) ── */}
        <div className="relative z-30 flex flex-col items-center justify-center text-center px-1 pointer-events-none select-none">
          {/* "REASONING" */}
          <span
            className="text-[12px] font-sans font-black tracking-[0.22em] uppercase leading-none transition-colors"
            style={{
              color: isLight ? "#0f172a" : "#ffffff",
              textShadow: isLight
                ? "0 1px 2px rgba(255,255,255,0.9), 0 0 10px rgba(2,132,199,0.25)"
                : "0 0 8px rgba(0,240,255,0.9), 0 0 18px rgba(0,240,255,0.6), 0 2px 4px rgba(0,0,0,0.95)",
            }}
          >
            REASONING
          </span>

          {/* Glowing Center Horizontal Divider Line with Center Lens Bead */}
          <div className="relative flex items-center justify-center w-[74px] h-[3px] my-1">
            <div
              className="w-full h-[1.2px]"
              style={{
                background: isLight
                  ? "linear-gradient(90deg, transparent 0%, rgba(2,132,199,0.85) 50%, transparent 100%)"
                  : "linear-gradient(90deg, transparent 0%, rgba(0,240,255,0.85) 50%, transparent 100%)",
                boxShadow: isLight ? "0 0 4px rgba(2,132,199,0.5)" : "0 0 6px rgba(0,240,255,0.9)",
              }}
            />
            {/* Center Lens Bead / Flare */}
            <span
              className="absolute w-3 h-[2.5px] rounded-full"
              style={{
                backgroundColor: isLight ? "#0284c7" : "#e0f7ff",
                boxShadow: isLight ? "0 0 6px #0284c7" : "0 0 8px #00f0ff, 0 0 14px #00f0ff",
              }}
            />
          </div>

          {/* "CORE" */}
          <span
            className="text-[10px] font-sans font-black tracking-[0.32em] uppercase leading-none transition-colors"
            style={{
              color: isLight ? "#0284c7" : "#00f0ff",
              textShadow: isLight
                ? "0 1px 2px rgba(255,255,255,0.9), 0 0 10px rgba(2,132,199,0.35)"
                : "0 0 10px rgba(0,240,255,1), 0 0 22px rgba(0,240,255,0.7), 0 2px 4px rgba(0,0,0,0.95)",
            }}
          >
            CORE
          </span>

          {/* Active Reasoning State Badge */}
          <div
            className={cn(
              "mt-1 px-1.5 py-0.2 rounded-full border flex items-center gap-1 backdrop-blur-sm transition-all",
              isLight
                ? "border-cyan-500/30 bg-cyan-50 text-cyan-800"
                : "border-cyan-400/35 bg-[#03152d]/80 text-cyan-300"
            )}
          >
            <span className="h-1 w-1 rounded-full bg-cyan-400 animate-pulse shrink-0" />
            <span className="text-[6.5px] font-mono font-bold tracking-widest uppercase leading-none">
              {mode}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
