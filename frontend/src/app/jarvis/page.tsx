"use client";

import React, {
  useRef, useState, useEffect, useMemo, useCallback,
  createContext, useContext,
} from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Grid, Line } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import {
  Mic, Send, Terminal, Activity, Shield, Zap, Cpu, Globe,
  Volume2, ChevronRight, Monitor, Database, Wifi, Radio, Gauge,
  Network, BarChart3, Layers, Server, HardDrive, Lock,
} from "lucide-react";

// Global audio level for voice reactivity inside the 3D scene (prevents parent component state updates from causing Canvas unmount/flicker)
let globalAudioLevel = 0;
const globalSceneState = {
  phase: "complete",
  progress: 1,
  time: 0
};

function NeuralCore() {
  const coreRef = useRef<THREE.Group>(null);
  const brainRef = useRef<THREE.Mesh>(null);
  const wireRef = useRef<THREE.Points>(null);
  const cerebellumRef = useRef<THREE.Mesh>(null);
  const cerebellumPointsRef = useRef<THREE.Points>(null);
  const stemRef = useRef<THREE.Mesh>(null);
  const stemPointsRef = useRef<THREE.Points>(null);
  const thalamusRef = useRef<THREE.Mesh>(null);
  const smoothAudioRef = useRef(0);
  
  // Procedural Brain Geometry (Cerebrum) - realistic human brain shape
  const brainGeo = useMemo(() => {
    const g = new THREE.SphereGeometry(0.85, 64, 48);
    const pos = g.attributes.position;
    
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i);
      let y = pos.getY(i);
      let z = pos.getZ(i);
      
      // === SHAPE: Human brain is wider at back, narrower at front ===
      // Elongate along Z (front-to-back)
      z *= 1.35;
      
      // Frontal lobe narrows toward front
      if (z > 0) {
        const frontFactor = z / 1.15;
        x *= 1.0 - frontFactor * 0.35;
      }
      
      // Occipital lobe bulges at back
      if (z < -0.3) {
        const backFactor = (-z - 0.3) / 0.85;
        x *= 1.0 + backFactor * 0.2;
        y *= 1.0 + backFactor * 0.15;
      }
      
      // Temporal lobes bulge on sides (lower half)
      if (y < 0.1) {
        const sideBulge = Math.cos(z * 2.5) * 0.15;
        x *= 1.0 + sideBulge * (1.0 - Math.abs(y));
      }
      
      // Flatten bottom (brain sits in skull)
      if (y < -0.1) {
        y = -0.1 + (y + 0.1) * 0.7;
      }
      
      // Slight upward curve at back (cerebellum area)
      if (z < -0.5 && y < 0) {
        y += 0.1;
      }
      
      // === LONGITUDINAL FISSURE (split hemispheres) ===
      const gap = 0.04;
      if (x > 0) x += gap;
      else x -= gap;
      
      // === FOLDS: Central Sulcus (main divide front/back) ===
      const centralSulcus = Math.exp(-Math.pow((z - 0.05) * 6, 2)) * 0.12;
      
      // === FOLDS: Lateral Sulcus (Sylvian fissure - temporal divide) ===
      const lateralSulcus = Math.exp(-Math.pow((y + 0.15) * 8, 2)) * Math.exp(-Math.pow(z * 3, 2)) * 0.1;
      
      // === GYRI & SULCI (brain folds) ===
      // Primary folds following brain anatomy
      const f1 = Math.sin(x * 8.0 + z * 2.0) * Math.cos(y * 7.0) * 0.06;
      const f2 = Math.sin(y * 10.0 + x * 1.5) * Math.cos(z * 8.0) * 0.04;
      // Finer secondary folds
      const f3 = Math.sin(x * 18.0) * Math.sin(y * 18.0) * Math.sin(z * 18.0) * 0.018;
      // Gyri bumps (raised ridges)
      const gyri = (Math.sin(x * 12.0 + y * 4.0) * Math.cos(z * 10.0) + 1.0) * 0.015;
      
      const totalFold = f1 + f2 + f3 + gyri - centralSulcus - lateralSulcus;
      
      const len = Math.sqrt(x*x + y*y + z*z);
      const nx = x / len;
      const ny = y / len;
      const nz = z / len;
      
      pos.setXYZ(i, x + nx * totalFold, y + ny * totalFold, z + nz * totalFold);
    }
    
    pos.needsUpdate = true;
    g.computeVertexNormals();
    return g;
  }, []);

  // Cerebellum Geometry - denser, smaller, with its own folds
  const cerebellumGeo = useMemo(() => {
    const g = new THREE.SphereGeometry(0.28, 32, 16);
    const pos = g.attributes.position;
    
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i);
      let y = pos.getY(i);
      let z = pos.getZ(i);
      
      // Flatten and widen cerebellum
      x *= 1.4;
      y *= 0.65;
      z *= 0.9;
      
      // Cerebellum has tight parallel folds (folia)
      const folia = Math.sin(y * 40.0) * 0.015 + Math.sin(z * 35.0) * 0.01;
      
      const len = Math.sqrt(x*x + y*y + z*z);
      const nx = x / len;
      const ny = y / len;
      const nz = z / len;
      
      pos.setXYZ(i, x + nx * folia, y + ny * folia, z + nz * folia);
    }
    
    pos.needsUpdate = true;
    g.computeVertexNormals();
    return g;
  }, []);

  // Brain Stem Geometry - tapered cylinder
  const stemGeo = useMemo(() => {
    const g = new THREE.CylinderGeometry(0.06, 0.1, 0.7, 16, 8);
    const pos = g.attributes.position;
    
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i);
      let y = pos.getY(i);
      let z = pos.getZ(i);
      
      // Slight curve backward
      z -= y * 0.15;
      // Slight bulge for pons
      const ponsBulge = Math.exp(-Math.pow((y + 0.1) * 5, 2)) * 0.04;
      const len = Math.sqrt(x*x + z*z);
      if (len > 0) {
        x *= 1.0 + ponsBulge / len;
        z *= 1.0 + ponsBulge / len;
      }
      
      pos.setXYZ(i, x, y, z);
    }
    
    pos.needsUpdate = true;
    g.computeVertexNormals();
    return g;
  }, []);

  // Neural pathway fibers (arcuate fasciculus, etc.)
  const neuralPaths = useMemo(() => {
    const paths: THREE.Vector3[][] = [];
    
    // Arcuate fasciculus - connects Broca's and Wernicke's areas (curved fiber bundle)
    for (let i = 0; i < 8; i++) {
      const pts: THREE.Vector3[] = [];
      const offsetX = (i - 3.5) * 0.04;
      const offsetZ = (i - 3.5) * 0.02;
      for (let t = 0; t <= 20; t++) {
        const frac = t / 20;
        const angle = frac * Math.PI;
        const r = 0.75 + i * 0.02;
        const x = offsetX + Math.sin(angle) * r * 0.3;
        const y = 0.15 + Math.cos(angle) * 0.35;
        const z = offsetZ + (frac - 0.5) * 1.2;
        pts.push(new THREE.Vector3(x, y, z));
      }
      paths.push(pts);
    }
    
    // Corticospinal tract - vertical fibers from motor cortex down
    for (let i = 0; i < 6; i++) {
      const pts: THREE.Vector3[] = [];
      const offsetX = (i - 2.5) * 0.06;
      for (let t = 0; t <= 16; t++) {
        const frac = t / 16;
        const x = offsetX * (1.0 - frac * 0.5);
        const y = 0.6 - frac * 1.3;
        const z = -0.1 + frac * 0.15;
        pts.push(new THREE.Vector3(x, y, z));
      }
      paths.push(pts);
    }
    
    return paths;
  }, []);

  useFrame((_, d) => {
    if (!coreRef.current || !brainRef.current || !wireRef.current || !thalamusRef.current || !cerebellumRef.current || !cerebellumPointsRef.current || !stemRef.current || !stemPointsRef.current) return;
    const time = globalSceneState.time;
    
    smoothAudioRef.current = THREE.MathUtils.lerp(smoothAudioRef.current, globalAudioLevel, 0.12);
    
    // Slow elegant rotation of the entire brain group
    coreRef.current.rotation.y = time * 0.12;
    coreRef.current.rotation.x = Math.sin(time * 0.25) * 0.06;
    coreRef.current.rotation.z = Math.cos(time * 0.2) * 0.03;
    
    // Scale pulse to speech
    const brainScale = 1.0 + smoothAudioRef.current * 0.05;
    brainRef.current.scale.setScalar(brainScale);
    wireRef.current.scale.setScalar(brainScale * 1.002);
    
    // Cerebellum follows brain with slight delay feel
    const cbScale = brainScale * 0.98;
    cerebellumRef.current.scale.set(1.3 * cbScale, 0.7 * cbScale, 0.9 * cbScale);
    cerebellumPointsRef.current.scale.copy(cerebellumRef.current.scale);
    
    // Stem scale
    stemRef.current.scale.setScalar(brainScale);
    stemPointsRef.current.scale.setScalar(brainScale);
    
    // Thalamus core pulses to speech
    const thalamusPulse = 1.0 + Math.sin(time * 3.5) * 0.05 + smoothAudioRef.current * 0.3;
    thalamusRef.current.scale.setScalar(thalamusPulse);
  });
  
  return (
    <group ref={coreRef} position={[0, 0.15, 0]}>
      {/* 1. Cerebrum (Main Brain) Wireframe */}
      <mesh ref={brainRef} geometry={brainGeo}>
        <meshBasicMaterial
          color="#00f3ff"
          wireframe
          transparent
          opacity={0.45}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      
      {/* 2. Cerebrum Vertex Dots */}
      <points ref={wireRef} geometry={brainGeo}>
        <pointsMaterial
          color="#00f3ff"
          size={0.012}
          sizeAttenuation
          transparent
          opacity={0.7}
          blending={THREE.AdditiveBlending}
        />
      </points>
      
      {/* 3. Cerebellum Wireframe */}
      <mesh ref={cerebellumRef} geometry={cerebellumGeo} position={[0, -0.35, -0.55]}>
        <meshBasicMaterial
          color="#00f3ff"
          wireframe
          transparent
          opacity={0.42}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      
      {/* 4. Cerebellum Vertex Dots */}
      <points ref={cerebellumPointsRef} geometry={cerebellumGeo} position={[0, -0.35, -0.55]}>
        <pointsMaterial
          color="#00f3ff"
          size={0.01}
          sizeAttenuation
          transparent
          opacity={0.6}
          blending={THREE.AdditiveBlending}
        />
      </points>
      
      {/* 5. Brain Stem Wireframe */}
      <mesh ref={stemRef} geometry={stemGeo} position={[0, -0.65, -0.35]} rotation={[0, 0, 0]}>
        <meshBasicMaterial
          color="#00f3ff"
          wireframe
          transparent
          opacity={0.35}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      
      {/* 6. Brain Stem Vertex Dots */}
      <points ref={stemPointsRef} geometry={stemGeo} position={[0, -0.65, -0.35]}>
        <pointsMaterial
          color="#00f3ff"
          size={0.008}
          sizeAttenuation
          transparent
          opacity={0.5}
          blending={THREE.AdditiveBlending}
        />
      </points>
      
      {/* 7. Neural Pathway Fibers */}
      {neuralPaths.map((pts, i) => (
        <Line key={i} points={pts} color="#00f3ff" lineWidth={0.8} transparent opacity={0.2} blending={THREE.AdditiveBlending} />
      ))}
      
      {/* 8. Thalamus Glowing Core Node */}
      <mesh ref={thalamusRef} position={[0, 0, 0]}>
        <sphereGeometry args={[0.18, 24, 24]} />
        <meshBasicMaterial
          color="#00f3ff"
          transparent
          opacity={0.65}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
}

function TelemetryRings() {
  const grp = useRef<THREE.Group>(null);
  const ring1 = useRef<THREE.Group>(null);
  const ring2 = useRef<THREE.Group>(null);
  const ring3 = useRef<THREE.Group>(null);
  const ring4 = useRef<THREE.Group>(null);
  const smoothAudio = useRef(0);
  
  useFrame((_, d) => {
    if (!grp.current || !ring1.current || !ring2.current || !ring3.current || !ring4.current) return;
    const time = globalSceneState.time;
    smoothAudio.current = THREE.MathUtils.lerp(smoothAudio.current, globalAudioLevel, 0.15);
    
    // Slow overall rotation on Z
    grp.current.rotation.z = time * 0.03;
    
    // Ring 1 (Inner Segmented) - fast spin
    ring1.current.rotation.z += 0.015;
    ring1.current.scale.setScalar(1.0 + smoothAudio.current * 0.05);
    
    // Ring 2 (Dashed progress) - slow reverse spin
    ring2.current.rotation.z -= 0.005;
    ring2.current.scale.setScalar(1.0 + smoothAudio.current * 0.03);
    
    // Ring 3 (Outer brackets) - oscillating rotation
    ring3.current.rotation.z = Math.sin(time * 0.5) * 0.15;
    ring3.current.scale.setScalar(1.0 + smoothAudio.current * 0.08);
    
    // Ring 4 (Outer ticks & audio wave) - scale directly to audio
    ring4.current.scale.setScalar(1.0 + smoothAudio.current * 0.15);
    ring4.current.rotation.z += 0.002;
  });
  
  return (
    <group ref={grp} rotation={[-Math.PI / 2.2, 0, 0]}>
      {/* ── Ring 1: Inner Segmented Arcs ── */}
      <group ref={ring1}>
        <mesh>
          <ringGeometry args={[0.7, 0.73, 64, 1, 0, Math.PI * 0.6]} />
          <meshBasicMaterial color="#00f3ff" transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
        <mesh>
          <ringGeometry args={[0.7, 0.73, 64, 1, Math.PI, Math.PI * 0.6]} />
          <meshBasicMaterial color="#00f3ff" transparent opacity={0.4} side={THREE.DoubleSide} />
        </mesh>
        {/* Tiny inner telemetry dots */}
        {Array.from({ length: 4 }).map((_, i) => {
          const a = (i / 4) * Math.PI * 2;
          return (
            <mesh key={i} position={[Math.cos(a) * 0.6, Math.sin(a) * 0.6, 0]}>
              <ringGeometry args={[0.01, 0.02, 8]} />
              <meshBasicMaterial color="#00f3ff" transparent opacity={0.6} />
            </mesh>
          );
        })}
      </group>
      
      {/* ── Ring 2: Telemetry Tick Marks (Dashed Circular HUD) ── */}
      <group ref={ring2}>
        {Array.from({ length: 24 }).map((_, i) => {
          const a = (i / 24) * Math.PI * 2;
          const isGap = i % 4 === 0;
          if (isGap) return null;
          return (
            <mesh key={i} position={[Math.cos(a) * 1.15, Math.sin(a) * 1.15, 0]} rotation={[0, 0, a]}>
              <planeGeometry args={[0.08, 0.02]} />
              <meshBasicMaterial color="#00a8ff" transparent opacity={0.35} side={THREE.DoubleSide} />
            </mesh>
          );
        })}
        {/* Continuous thin reference ring */}
        <mesh>
          <ringGeometry args={[1.1, 1.105, 64]} />
          <meshBasicMaterial color="#00a8ff" transparent opacity={0.15} side={THREE.DoubleSide} />
        </mesh>
      </group>
      
      {/* ── Ring 3: Outer Bracket Sectors & Ticks ── */}
      <group ref={ring3}>
        <mesh>
          <ringGeometry args={[1.55, 1.57, 64, 1, 0, Math.PI * 0.35]} />
          <meshBasicMaterial color="#00ffcc" transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
        <mesh>
          <ringGeometry args={[1.55, 1.57, 64, 1, Math.PI * 0.8, Math.PI * 0.35]} />
          <meshBasicMaterial color="#00ffcc" transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
        <mesh>
          <ringGeometry args={[1.55, 1.57, 64, 1, Math.PI * 1.5, Math.PI * 0.35]} />
          <meshBasicMaterial color="#00ffcc" transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
        {/* Bracket corners / tick markers */}
        {Array.from({ length: 3 }).map((_, i) => {
          const a = (i / 3) * Math.PI * 2 + Math.PI / 6;
          return (
            <group key={i} position={[Math.cos(a) * 1.56, Math.sin(a) * 1.56, 0]} rotation={[0, 0, a]}>
              {/* Radial tick line protruding outward */}
              <mesh position={[0.05, 0, 0]}>
                <planeGeometry args={[0.1, 0.015]} />
                <meshBasicMaterial color="#00ffcc" transparent opacity={0.6} side={THREE.DoubleSide} />
              </mesh>
            </group>
          );
        })}
      </group>
      
      {/* ── Ring 4: Outer Dynamic Audio Waveform Ticks ── */}
      <group ref={ring4}>
        {Array.from({ length: 48 }).map((_, i) => {
          const a = (i / 48) * Math.PI * 2;
          return (
            <OrbitRingTick key={i} angle={a} index={i} radius={2.0} />
          );
        })}
        {/* Outer boundary thin circle */}
        <mesh>
          <ringGeometry args={[1.98, 1.99, 64]} />
          <meshBasicMaterial color="#00f3ff" transparent opacity={0.12} side={THREE.DoubleSide} />
        </mesh>
      </group>
    </group>
  );
}

function OrbitRingTick({ angle, index, radius }: { angle: number; index: number; radius: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const smoothVal = useRef(0);
  
  useFrame(() => {
    if (!meshRef.current) return;
    smoothVal.current = THREE.MathUtils.lerp(smoothVal.current, globalAudioLevel, 0.15);
    
    // Wave ripple height: index-based offset + audio amplitude
    const wave = Math.sin(index * 0.5 + globalSceneState.time * 6.0) * 0.05;
    const height = 0.04 + smoothVal.current * 0.25 + Math.abs(wave) * (0.15 + smoothVal.current * 0.5);
    
    meshRef.current.scale.y = height * 10; // scale standard height
    meshRef.current.position.set(
      Math.cos(angle) * (radius + height * 0.5),
      Math.sin(angle) * (radius + height * 0.5),
      0
    );
  });
  
  return (
    <mesh ref={meshRef} rotation={[0, 0, angle]}>
      <planeGeometry args={[0.015, 0.1]} />
      <meshBasicMaterial color="#00f3ff" transparent opacity={0.4} side={THREE.DoubleSide} />
    </mesh>
  );
}

function KnowledgeNetwork() {
  const ptsRef = useRef<THREE.Points>(null);
  const matRef = useRef<THREE.PointsMaterial>(null);
  const N = 400;
  const [pos, spd] = useMemo(() => {
    const p = new Float32Array(N * 3), s = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      const th = Math.random() * Math.PI * 2;
      const ph = Math.acos(2 * Math.random() - 1);
      const Rd = 1.4 + Math.random() * 1.6;
      p[i * 3] = Rd * Math.sin(ph) * Math.cos(th);
      p[i * 3 + 1] = Rd * Math.cos(ph);
      p[i * 3 + 2] = Rd * Math.sin(ph) * Math.sin(th);
      s[i] = 0.15 + Math.random() * 0.45;
    }
    return [p, s];
  }, []);
  
  const smoothAudio = useRef(0);
  useFrame((_, d) => {
    if (!ptsRef.current) return;
    const time = globalSceneState.time;
    smoothAudio.current = THREE.MathUtils.lerp(smoothAudio.current, globalAudioLevel, 0.15);
    
    // Slow rotation
    ptsRef.current.rotation.y += 0.001;
    ptsRef.current.rotation.x = Math.sin(time * 0.05) * 0.05;
    
    if (matRef.current) {
      matRef.current.size = 0.015 + smoothAudio.current * 0.02;
    }
  });
  
  return (
    <points ref={ptsRef}>
      <bufferGeometry><bufferAttribute attach="attributes-position" args={[pos, 3]} /></bufferGeometry>
      <pointsMaterial ref={matRef} color="#00f3ff" size={0.015} transparent opacity={0.35} blending={THREE.AdditiveBlending} depthWrite={false} sizeAttenuation />
    </points>
  );
}

// ─────────────────────────────────────────────
// SCENE
// ─────────────────────────────────────────────
function Scene3D() {
  useFrame((_, d) => {
    globalSceneState.time += d;
  });

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} color="#00f0ff" />
      <pointLight position={[-4, -4, -4]} intensity={0.4} color="#0066ff" />
      
      <NeuralCore />
      <TelemetryRings />
      <KnowledgeNetwork />
      
      <OrbitControls
        enablePan={false}
        enableZoom
        minDistance={2.0}
        maxDistance={7.0}
        maxPolarAngle={Math.PI}
        autoRotate
        autoRotateSpeed={0.3}
      />
    </>
  );
}

// ─────────────────────────────────────────────
// HOOKS
// ─────────────────────────────────────────────
const MemoScene = React.memo(function MemoScene() {
  return <Panel depth={5} glow className="absolute inset-0 w-full h-full">
    <Canvas style={{ width: "100%", height: "100%" }} camera={{ position: [0, 0, 4.5], fov: 50 }} dpr={[1, 1.5]} gl={{ antialias: true, alpha: true }}>
      <Scene3D />
    </Canvas>
  </Panel>;
});
const POWERS = [
  { id: "vox", label: "VOICE", icon: Volume2, desc: "Neural TTS/STT" },
  { id: "vis", label: "VISION", icon: Monitor, desc: "OCR & Analysis" },
  { id: "code", label: "CODE", icon: Terminal, desc: "Generate & Debug" },
  { id: "rag", label: "RAG", icon: Database, desc: "Retrieval Augmented" },
  { id: "kg", label: "K.GRAPH", icon: Globe, desc: "Neo4j Traversal" },
  { id: "mon", label: "MONITOR", icon: Activity, desc: "System Telemetry" },
  { id: "auto", label: "AUTOPILOT", icon: Cpu, desc: "Multi-Agent Ops" },
  { id: "sec", label: "SECURITY", icon: Shield, desc: "UAE Residency" },
];

function useLiveMetrics() {
  const [m, setM] = useState({ cpu: 0, mem: 0, disk: 0, net: 0, lat: 0, qps: 0 });
  useEffect(() => {
    const id = setInterval(() => setM({
      cpu: Math.round(20 + Math.random() * 35), mem: Math.round(40 + Math.random() * 30),
      disk: Math.round(15 + Math.random() * 25), net: Math.round(30 + Math.random() * 50),
      lat: Math.round(12 + Math.random() * 25), qps: Math.round(40 + Math.random() * 60),
    }), 1200);
    return () => clearInterval(id);
  }, []);
  return m;
}

function useEventLog() {
  const [logs, setLogs] = useState<string[]>([
    "SYSTEM: Grid calibration complete",
    "SYSTEM: Neural interface synchronized",
    "SYSTEM: All superpowers nominal",
  ]);
  useEffect(() => {
    const events = ["HOLOGRAM: Phase lock acquired", "TELEMETRY: CPU threshold nominal", "NETWORK: Link quality 98%",
      "SECURITY: Encryption handshake verified", "NEUROSOL: Sync pulse acknowledged", "DATABASE: Query latency within bounds",
      "VOICE: Synthesis model loaded", "KNOWLEDGE: Graph traversal ready"];
    const id = setInterval(() => { setLogs(p => [...p.slice(-19), `${events[Math.floor(Math.random() * events.length)]}`]); }, 2800);
    return () => clearInterval(id);
  }, []);
  return logs;
}

// ─────────────────────────────────────────────
// UI COMPONENTS
// ─────────────────────────────────────────────
function Panel({ children, className = "", depth = 3, glow = false }: { children: React.ReactNode; className?: string; depth?: number; glow?: boolean }) {
  const d = depth * 8, s = depth * 4;
  const hasPos = /\b(absolute|relative|fixed|sticky)\b/.test(className);
  const posClass = hasPos ? "" : "relative";
  return <div className={`${posClass} bg-white/[0.03] backdrop-blur-xl border border-white/[0.06] rounded-2xl overflow-hidden ${glow ? 'shadow-[0_0_30px_rgba(0,240,255,0.06)]' : ''} ${className}`}
    style={{ boxShadow: `0 ${d}px ${d * 3}px rgba(0,0,0,0.5), 0 ${s}px ${s * 2}px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.08), inset 0 -1px 0 rgba(0,0,0,0.3)` }}>
    {children}
  </div>;
}

function GaugeArc({ pct, size = 44, label, sub }: { pct: number; size?: number; label: string; sub?: string }) {
  const r = size / 2 - 4, circ = 2 * Math.PI * r, dash = pct / 100 * circ;
  return <div className="flex flex-col items-center gap-0.5">
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={3} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="url(#gauge-grad)" strokeWidth={3} strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round" style={{ transition: "stroke-dasharray 0.5s ease" }} />
      <defs><linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#0a8cff" /><stop offset="100%" stopColor="#00f0ff" /></linearGradient></defs>
    </svg>
    <span className="text-[9px] font-mono font-bold text-cyan-300 mt-0.5">{pct}%</span>
    <span className="text-[7px] text-white/30 tracking-wider uppercase mt-0.5">{label}</span>
    {sub && <span className="text-[6px] text-white/20">{sub}</span>}
  </div>;
}

function DataBar({ label, value, max = 100, color = "cyan" }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(value / max * 100, 100);
  const c = color === "cyan" ? "bg-cyan-400 shadow-[0_0_8px_rgba(0,240,255,0.3)]" : color === "emerald" ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.3)]" : color === "blue" ? "bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.3)]" : "bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.3)]";
  return <div className="flex items-center gap-2">
    <span className="text-[8px] text-white/30 tracking-wider min-w-[48px] font-mono">{label}</span>
    <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
      <div className={`h-full rounded-full transition-all duration-700 ease-out ${c}`} style={{ width: `${pct}%` }} />
    </div>
    <span className="text-[9px] font-mono text-white/50 min-w-[32px] text-right">{value}</span>
  </div>;
}

// ─────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────
export default function JarvisPage() {
  const [msg, setMsg] = useState<{ s: "jarvis" | "user"; t: string; ts: string }[]>([{ s: "jarvis", t: "Initializing systems. Stand by...", ts: "00:00" }]);
  const [inp, setInp] = useState("");
  const [notice, setNotice] = useState("Acquiring neural lock...");
  const [rec, setRec] = useState(false);
  const [voiceOn, setVoiceOn] = useState(false);
  const [stage, setStage] = useState(0);
  const [hyd, setHyd] = useState(false);
  const recRef = useRef<any>(null);
  const synRef = useRef<SpeechSynthesis | null>(null);
  const cRef = useRef<HTMLDivElement>(null);
  const [gst, setGst] = useState("--:--:-- GST");
  const met = useLiveMetrics();
  const logs = useEventLog();
  const [barHeights, setBarHeights] = useState<number[]>(Array.from({ length: 30 }, () => 30));
  const [latStr, setLatStr] = useState("--ms");

  useEffect(() => { setHyd(true); }, []);
  useEffect(() => { const t = () => setGst(new Date().toLocaleTimeString("en-US", { hour12: false, timeZone: "Asia/Dubai" }) + " GST"); t(); const id = setInterval(t, 1e3); return () => clearInterval(id); }, []);

  useEffect(() => {
    if (!hyd) return;
    const id = setInterval(() => {
      setBarHeights(Array.from({ length: 30 }, (_, i) => Math.round(20 + Math.sin(i * 0.8 + Date.now() * 0.002) * 15 + Math.random() * 25)));
      setLatStr(`${Math.round(12 + Math.random() * 25)}ms`);
    }, 1500);
    return () => clearInterval(id);
  }, [hyd]);

  const LABELS = ["GRID CALIBRATION", "PLATFORM SYNC", "SKELETAL FRAME", "PARTICLE IGNITION", "HOLO RESOLUTION", "VOICE LINK", "SYSTEMS ONLINE"];
  useEffect(() => { const id = setInterval(() => setStage(p => { if (p < LABELS.length - 1) { setNotice(LABELS[p + 1]); return p + 1; } clearInterval(id); setNotice("All systems nominal."); return p; }), 2200); return () => clearInterval(id); }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    synRef.current = window.speechSynthesis;
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SR) { const r = new SR(); r.continuous = false; r.interimResults = true; r.lang = "en-US"; r.onstart = () => setRec(true); r.onend = () => setRec(false); r.onresult = (e: any) => { const t = e.results[e.results.length - 1][0].transcript; setInp(t); if (e.results[e.results.length - 1].isFinal) sendMsg(t); }; recRef.current = r; }
  }, []);
  useEffect(() => { if (cRef.current) cRef.current.scrollTop = cRef.current.scrollHeight; }, [msg]);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const id = setInterval(() => {
      if (!rec) {
        globalAudioLevel = 0;
        return;
      }
      globalAudioLevel = 0.3 + Math.random() * 0.7;
    }, 100);
    return () => clearInterval(id);
  }, [rec]);

  const spk = useCallback((t: string) => {
    if (!synRef.current || !voiceOn) return;
    synRef.current.cancel();
    const u = new SpeechSynthesisUtterance(t.replace(/[*#\[\]`]/g, ""));
    u.rate = 0.95;
    u.pitch = 0.85;
    const v = synRef.current.getVoices(), p = v.find(x => x.name.includes("Google UK") || x.name.includes("Daniel") || x.name.includes("Samantha"));
    if (p) u.voice = p;
    u.onstart = () => {
      setNotice("Synthesizing voice...");
      const simInterval = setInterval(() => {
        if (synRef.current?.speaking) {
          globalAudioLevel = 0.2 + Math.random() * 0.8;
        } else {
          globalAudioLevel = 0;
          clearInterval(simInterval);
        }
      }, 50);
    };
    u.onend = () => {
      setNotice("Awaiting command.");
      globalAudioLevel = 0;
    };
    synRef.current.speak(u);
  }, [voiceOn]);

  const sendMsg = useCallback(async (txt?: string) => {
    const q = (txt || inp).trim(); if (!q) return; setInp("");
    const ts = new Date(), tsS = `${String(ts.getHours()).padStart(2, "0")}:${String(ts.getMinutes()).padStart(2, "0")}`;
    setMsg(p => [...p, { s: "user", t: q, ts: tsS }]); setNotice("Processing...");
    try { const r = await fetch("http://localhost:8000/jarvis/query", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: q, session_id: "jarvis_ui" }) }); const d = await r.json(), rp = d.response || "Complete."; const rts = new Date(), rtsS = `${String(rts.getHours()).padStart(2, "0")}:${String(rts.getMinutes()).padStart(2, "0")}`; setMsg(p => [...p, { s: "jarvis", t: rp, ts: rtsS }]); spk(rp); } catch { const rtsS = `${String(new Date().getHours()).padStart(2, "0")}:${String(new Date().getMinutes()).padStart(2, "0")}`; setMsg(p => [...p, { s: "jarvis", t: "Local diagnostics active. Backend offline.", ts: rtsS }]); spk("Local diagnostics active."); }
  }, [inp, spk]);

  return (
    <div className="relative w-full h-[calc(100vh-88px)] bg-[#05080f] overflow-hidden flex flex-col rounded-2xl border border-white/5 shadow-2xl">

      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Crect width='40' height='40' fill='none' stroke='%2300f0ff' stroke-width='0.3'/%3E%3C/svg%3E")`, backgroundSize: "40px 40px" }} />

      {/* ── MAIN CONTAINER ── */}
      <div className="relative z-10 w-full flex-1 flex flex-col min-h-0">

        {/* ═══ TOP BAR ═══ */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-white/[0.05] bg-black/30 backdrop-blur-2xl shrink-0"
          style={{ boxShadow: "0 4px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-4">
            <div className="relative w-9 h-9 flex items-center justify-center">
              <div className="absolute inset-0 border border-dashed border-cyan-500/40 rounded-full animate-spin" style={{ animationDuration: "8s" }} />
              <div className="absolute inset-1 border border-dashed border-cyan-500/20 rounded-full animate-spin" style={{ animationDuration: "6s", animationDirection: "reverse" }} />
              <div className="w-2.5 h-2.5 bg-cyan-400 rounded-full shadow-[0_0_16px_rgba(0,240,255,0.7)]" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-[0.25em] text-cyan-300 font-mono drop-shadow-[0_0_8px_rgba(0,240,255,0.3)]">J.A.R.V.I.S.</h1>
              <p className="text-[8px] text-cyan-500/50 tracking-[0.3em] uppercase">SOVEREIGN INTELLIGENCE v3.0</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            <div className="flex flex-col items-end"><span className="text-[8px] text-white/20 tracking-[0.2em] uppercase">Status</span><div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)] animate-pulse" /><span className="text-[11px] font-mono font-bold tracking-wider text-emerald-400">ONLINE</span></div></div>
            <div className="flex flex-col items-end"><span className="text-[8px] text-white/20 tracking-[0.2em] uppercase">Residency</span><div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(0,240,255,0.5)] animate-pulse" /><span className="text-[11px] font-mono font-bold tracking-wider text-cyan-400">UAE</span></div></div>
            <button onClick={() => setVoiceOn(!voiceOn)} className={`px-3 py-1.5 rounded-lg border text-[10px] font-mono tracking-wider transition-all cursor-pointer flex items-center gap-1.5 ${voiceOn ? "border-cyan-500/30 text-cyan-400 bg-cyan-500/10 shadow-[0_0_12px_rgba(0,240,255,0.1)]" : "border-white/[0.06] text-white/30 hover:border-white/20"}`}><Volume2 className="w-3 h-3" />{voiceOn ? "VOICE ON" : "VOICE OFF"}</button>
          </div>
        </header>

        {/* ═══ MAIN 3-PANEL LAYOUT ═══ */}
        <div className="flex-1 flex gap-4 p-4 min-h-0">

          {/* ── LEFT COLUMN ── */}
          <div className="w-[280px] flex flex-col gap-4 shrink-0">
            <Panel depth={3} className="flex flex-col gap-0.5 p-3 flex-1 min-h-0">
              <div className="text-[8px] text-white/15 tracking-[0.2em] uppercase mb-1.5 flex items-center gap-1.5"><Layers className="w-3 h-3 text-cyan-500/40" /> SUPERPOWERS</div>
              <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin space-y-1">
                {POWERS.map(p => {
                  const Icon = p.icon;
                  return <div key={p.id} className="group flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/[0.03] hover:border hover:border-cyan-500/10 transition-all cursor-pointer border border-transparent">
                    <div className="w-7 h-7 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-center justify-center shrink-0"><Icon className="w-3.5 h-3.5 text-cyan-400/80" /></div>
                    <div className="min-w-0 flex-1"><div className="flex items-center gap-1.5"><span className="text-[10px] font-semibold text-white/70 tracking-wider uppercase">{p.label}</span><span className="w-1 h-1 rounded-full bg-emerald-400/80 shadow-[0_0_4px_rgba(52,211,153,0.3)] shrink-0" /></div><div className="text-[7px] text-white/20 tracking-wider">{p.desc}</div></div>
                  </div>;
                })}
              </div>
            </Panel>
            <Panel depth={4} className="p-3 flex-1 min-h-0 flex flex-col">
              <div className="text-[8px] text-white/15 tracking-[0.2em] uppercase mb-1.5 flex items-center gap-1.5"><Radio className="w-3 h-3 text-cyan-500/40" /> EVENT LOG</div>
              <div className="flex-1 overflow-y-auto scrollbar-thin space-y-1">
                {logs.map((l, i) => <div key={i} className="text-[7px] text-white/25 font-mono leading-relaxed border-l border-white/[0.04] pl-2 mb-0.5 hover:text-white/40 transition-colors">{l}</div>)}
              </div>
            </Panel>
          </div>

          {/* ── CENTER: 3D Scene ── */}
          <main className="flex-1 min-h-0 relative">
            <MemoScene />
            <div className="absolute bottom-3 left-3 right-3 flex justify-between pointer-events-none">
              <div className="flex gap-3"><span className="text-[8px] text-white/20 font-mono tracking-wider">FPS: 60</span><span className="text-[8px] text-white/20 font-mono tracking-wider">LAT: {latStr}</span></div>
              <span className="text-[8px] text-cyan-500/25 font-mono tracking-wider">NEUROSOL SYNC: LOCKED</span>
            </div>
            <div className="absolute top-3 left-3 right-3">
              <div className="text-[8px] text-cyan-400/50 font-mono tracking-wider">{notice}</div>
            </div>
          </main>

          {/* ── RIGHT COLUMN ── */}
          <div className="w-[320px] flex flex-col gap-4 shrink-0">
            <Panel depth={3} className="p-3 shrink-0">
              <div className="text-[8px] text-white/15 tracking-[0.2em] uppercase mb-2 flex items-center gap-1.5"><Gauge className="w-3 h-3 text-cyan-500/40" /> SYSTEM METRICS</div>
              <div className="flex justify-around">
                <GaugeArc pct={met.cpu} label="CPU" />
                <GaugeArc pct={met.mem} label="MEM" />
                <GaugeArc pct={met.disk} label="DISK" />
                <GaugeArc pct={met.net} label="NET" />
              </div>
            </Panel>
            <Panel depth={4} className="p-3 flex-1 min-h-0 flex flex-col justify-between">
              <div className="text-[8px] text-white/15 tracking-[0.2em] uppercase mb-2 flex items-center gap-1.5"><BarChart3 className="w-3 h-3 text-cyan-500/40" /> RESOURCE UTILIZATION</div>
              <div className="flex-1 flex flex-col justify-between mt-2">
                <div className="space-y-2">
                  <DataBar label="CPU" value={met.cpu} />
                  <DataBar label="MEM" value={met.mem} color="emerald" />
                  <DataBar label="DISK" value={met.disk} color="blue" />
                  <DataBar label="NET" value={met.net} color="purple" />
                </div>
                <div className="mt-2 pt-2 border-t border-white/[0.04] space-y-1">
                  <div className="flex justify-between text-[8px] font-mono"><span className="text-white/20">QUERIES/S</span><span className="text-cyan-400/60">{met.qps}</span></div>
                  <div className="flex justify-between text-[8px] font-mono"><span className="text-white/20">LATENCY</span><span className="text-cyan-400/60">{met.lat}ms</span></div>
                  <div className="flex justify-between text-[8px] font-mono"><span className="text-white/20">POWERS ACTIVE</span><span className="text-emerald-400/60">8/8</span></div>
                </div>
              </div>
            </Panel>
            <Panel depth={5} className="p-3 h-[100px] shrink-0">
              <div className="text-[8px] text-white/15 tracking-[0.2em] uppercase mb-1.5 flex items-center gap-1.5"><Network className="w-3 h-3 text-cyan-500/40" /> THROUGHPUT</div>
              <div className="flex items-end gap-[2px] h-[52px]">
                {barHeights.map((h, i) => <div key={i} className="flex-1 bg-gradient-to-t from-cyan-500/20 to-cyan-400/40 rounded-t-sm" style={{ height: `${h}%`, transition: "height 0.5s ease" }} />)}
              </div>
            </Panel>
          </div>
        </div>

        {/* ═══ CHAT BAR ═══ */}
        <div className="px-4 pb-4 shrink-0">
          <Panel depth={6} className="flex items-center gap-3 px-4 py-3">
            <button onClick={() => recRef.current?.start()} className={`w-9 h-9 rounded-xl border flex items-center justify-center transition-all shrink-0 cursor-pointer ${rec ? "bg-red-500/20 border-red-500/50 animate-pulse shadow-[0_0_16px_rgba(239,68,68,0.2)]" : "border-white/[0.08] hover:border-cyan-500/30 text-white/40 hover:text-cyan-400"}`}><Mic className="w-4 h-4" /></button>
            <div ref={cRef} className="flex-1 max-h-[60px] overflow-y-auto flex items-center gap-2 scrollbar-thin">
              {msg.slice(-3).map((m, i) => <div key={i} className={`text-[10px] px-2 py-1 rounded-md whitespace-nowrap ${m.s === "jarvis" ? "bg-cyan-500/10 border border-cyan-500/10 text-cyan-300/80" : "bg-blue-500/10 border border-blue-500/10 text-blue-300/80"}`}>{m.t.slice(0, 40)}{m.t.length > 40 ? "..." : ""}</div>)}
            </div>
            <input value={inp} onChange={e => setInp(e.target.value)} onKeyDown={e => e.key === "Enter" && sendMsg()} placeholder="Command query..." className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white/80 placeholder-white/20 outline-none focus:border-cyan-500/30 transition-colors font-mono" />
            <button onClick={() => sendMsg()} className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center hover:bg-cyan-500/20 hover:shadow-[0_0_16px_rgba(0,240,255,0.15)] transition-all cursor-pointer shrink-0"><Send className="w-4 h-4 text-cyan-400" /></button>
          </Panel>
        </div>

        {/* ═══ STATUS BAR ═══ */}
        <footer className="flex items-center justify-between px-6 py-2 border-t border-white/[0.04] bg-black/30 backdrop-blur-2xl shrink-0"
          style={{ boxShadow: "0 -4px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)" }}>
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)] animate-pulse" /><span className="text-[8px] text-emerald-400/60 font-mono tracking-wider">CORE NOMINAL</span></div>
            <div className="text-[8px] text-white/20 font-mono tracking-wider flex items-center gap-1"><Shield className="w-3 h-3 text-cyan-500/30" />SECURITY: MAXIMUM</div>
            <div className="text-[8px] text-white/20 font-mono tracking-wider">QPS: {met.qps}</div>
          </div>
          <div className="flex items-center gap-5">
            <span className="text-[8px] text-cyan-500/25 font-mono tracking-wider flex items-center gap-1"><Wifi className="w-3 h-3" />NEUROSOL ACTIVE</span>
            <span className="text-[8px] text-cyan-400/30 font-mono tracking-wider">🇦🇪 UAE DATA RESIDENCY</span>
            <span className="text-[8px] text-white/20 font-mono">{gst}</span>
          </div>
        </footer>

      </div>
    </div>
  );
}
