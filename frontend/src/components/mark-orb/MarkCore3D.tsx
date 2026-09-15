"use client";

import React, { useMemo, useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import * as THREE from "three";
import type { MarkVisualState } from "@/lib/mark-capability-graph";

const PARTICLE_COUNT = 6600;
const CYAN = "#00e5ff";

function normalizeState(state: MarkVisualState) {
  if (state === "listening") return { radius: 0.28, speed: 2.2, wave: 0.04 };
  if (state === "processing") return { radius: 0.32, speed: 2.6, wave: 0.05 };
  if (state === "speaking") return { radius: 0.30, speed: 3.0, wave: 0.06 };
  if (state === "investigating") return { radius: 0.32, speed: 2.3, wave: 0.05 };
  if (state === "waiting_for_approval") return { radius: 0.24, speed: 1.5, wave: 0.03 };
  if (state === "learning") return { radius: 0.28, speed: 2.1, wave: 0.04 };
  return { radius: 0.24, speed: 0.95, wave: 0.02 };
}

function makeSprite() {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (!ctx) return new THREE.Texture();
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.2, "rgba(180,248,255,0.95)");
  gradient.addColorStop(0.48, "rgba(0,229,255,0.65)");
  gradient.addColorStop(0.78, "rgba(0,229,255,0.18)");
  gradient.addColorStop(1, "rgba(0,229,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(canvas);
}

function seededRandom(seed: number) {
  const next = (seed * 9301 + 49297) % 233280;
  return [next / 233280, next] as const;
}

function ParticleCore({ state }: { state: MarkVisualState }) {
  const group = useRef<THREE.Group>(null);
  const points = useRef<THREE.Points>(null);
  const targetRadius = useRef(0.24);
  const sprite = useMemo(() => makeSprite(), []);
  const [geometry] = useState(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(PARTICLE_COUNT * 3), 3));
    return geo;
  });

  const data = useMemo(() => {
    const dir = new Float32Array(PARTICLE_COUNT * 3);
    const inner = new Float32Array(PARTICLE_COUNT);
    const phase = new Float32Array(PARTICLE_COUNT);
    const speed = new Float32Array(PARTICLE_COUNT);
    let seed = 31;

    for (let i = 0; i < PARTICLE_COUNT; i += 1) {
      const r1 = seededRandom(seed);
      seed = r1[1];
      const r2 = seededRandom(seed);
      seed = r2[1];
      const r3 = seededRandom(seed);
      seed = r3[1];
      const r4 = seededRandom(seed);
      seed = r4[1];
      const r5 = seededRandom(seed);
      seed = r5[1];
      const theta = r1[0] * Math.PI * 2;
      const phi = Math.acos(2 * r2[0] - 1);
      dir[i * 3] = Math.sin(phi) * Math.cos(theta);
      dir[i * 3 + 1] = Math.sin(phi) * Math.sin(theta);
      dir[i * 3 + 2] = Math.cos(phi);

      // 90% tightly clustered at the center nucleus, 10% gentle inner wisp
      if (i < PARTICLE_COUNT * 0.9) {
        inner[i] = 0.02 + Math.pow(r3[0], 2.2) * 0.34;
      } else {
        inner[i] = 0.12 + Math.pow(r3[0], 1.4) * 0.32;
      }

      phase[i] = r4[0] * Math.PI * 2;
      speed[i] = 0.7 + r5[0] * 1.7;
    }

    return { dir, inner, phase, speed };
  }, []);

  useFrame((frame, dt) => {
    const profile = normalizeState(state);
    const d = Math.min(dt, 0.06);
    targetRadius.current = THREE.MathUtils.lerp(targetRadius.current, profile.radius, 0.05);

    const t = frame.clock.elapsedTime;
    const radius = targetRadius.current;
    const { dir, inner, phase, speed } = data;
    const positionAttribute = points.current?.geometry.attributes.position as THREE.BufferAttribute | undefined;
    const positions = positionAttribute?.array as Float32Array | undefined;
    if (!positions) return;

    for (let i = 0; i < PARTICLE_COUNT; i += 1) {
      let r = inner[i] * radius + Math.sin(t * speed[i] * profile.speed + phase[i]) * (0.01 + profile.wave * 0.04);
      if (state === "speaking") r += Math.sin(inner[i] * 5.5 - t * 5) * 0.03;
      // Clustered tightly at center - never scattered outward
      r = Math.min(r, 0.38);
      positions[i * 3] = dir[i * 3] * r;
      positions[i * 3 + 1] = dir[i * 3 + 1] * r;
      positions[i * 3 + 2] = dir[i * 3 + 2] * r;
    }

    if (points.current) {
      points.current.geometry.attributes.position.needsUpdate = true;
      const material = points.current.material as THREE.PointsMaterial;
      material.size = state === "idle" ? 0.036 : 0.042;
      material.opacity = state === "idle" ? 0.95 : 1.0;
    }

    if (group.current) {
      group.current.rotation.x = 0.28;
      group.current.rotation.y += d * (0.08 + profile.speed * 0.05);
      group.current.rotation.z = Math.sin(t * 0.12) * 0.08;
    }
  });

  return (
    <group ref={group} scale={0.34}>
      <points ref={points} geometry={geometry}>
        <pointsMaterial
          map={sprite}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          color={CYAN}
          size={0.036}
          opacity={0.95}
        />
      </points>
    </group>
  );
}

class MarkOrbBoundary extends React.Component<{ children: React.ReactNode }, { dead: boolean }> {
  private tries = 0;
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { dead: false };
  }

  static getDerivedStateFromError() {
    return { dead: true };
  }

  componentDidCatch(error: unknown) {
    console.warn("[mark-orb] 3D core crashed; hiding decorative canvas", error);
    clearTimeout(this.timer);
    if (this.tries < 3) {
      this.tries += 1;
      this.timer = setTimeout(() => this.setState({ dead: false }), 8000);
    }
  }

  componentWillUnmount() {
    clearTimeout(this.timer);
  }

  render() {
    return this.state.dead ? null : this.props.children;
  }
}

export function MarkCore3D({ state }: { state: MarkVisualState }) {
  return (
    <MarkOrbBoundary>
      <Canvas
        camera={{ position: [0, 0, 4.8], fov: 42 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        dpr={[1, 1.6]}
        style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      >
        <ambientLight intensity={0.28} />
        <ParticleCore state={state} />
        <EffectComposer>
          <Bloom
            intensity={1.8}
            luminanceThreshold={0.12}
            luminanceSmoothing={0.8}
            mipmapBlur
            radius={0.65}
          />
        </EffectComposer>
      </Canvas>
    </MarkOrbBoundary>
  );
}
