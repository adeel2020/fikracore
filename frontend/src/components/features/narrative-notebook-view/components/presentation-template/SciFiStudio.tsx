"use client";

import React, { useRef, useState, useMemo, useEffect, useContext } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Grid, Html, OrbitControls, Ring, Line, Sphere } from "@react-three/drei";
import * as THREE from "three";
import { 
  Activity, 
  ShieldAlert, 
  PieChart, 
  Sparkles,
  RefreshCw,
  XCircle,
  Power,
  RotateCcw
} from "lucide-react";
import { cn } from "@/lib/utils";
import TalkingAvatar from "./TalkingAvatar";
import { AvatarProvider, useAvatar, AvatarContext } from "./AvatarContext";
import { AvatarControlPanel } from "./AvatarControlPanel";
// Import live telemetry widgets from the complaint dashboard features
import { WeeklyComplaintVolume, TelemetryCalendar, TopRoamingComplaints } from "@/components/features/complaint-dashboard-view/components/SpatialTrafficTrends";
import { EarlyWarningDiagnostics } from "@/components/features/complaint-dashboard-view/components/EarlyWarningDiagnostics";
import { TopComplaintCategories, TotalTicketDistribution, AvgQueueTime } from "@/components/features/complaint-dashboard-view/components/QueuePerformanceAnalytics";
import { TopReassignmentsQueue, TopRejectionReason, PercentageNocTickets } from "@/components/features/complaint-dashboard-view/components/CoreOperationalMetrics";
import { ComplaintDashboardView } from "@/components/features/complaint-dashboard-view/ComplaintDashboardView";
import HoloCard from "@/components/ui/HoloCard";



const GlassCard = ({ position, rotation, children, width = 3.2, height = 4.2, floatOffset = 0, visible = true }: any) => {
  const ref = useRef<THREE.Group>(null);
  const scaleRef = useRef(1);

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.getElapsedTime();
      
      // Smooth lerp scale for Hollywood projection materialize/dematerialize effect
      const targetScale = visible ? 1 : 0;
      scaleRef.current = THREE.MathUtils.lerp(scaleRef.current, targetScale, 0.12);
      ref.current.scale.setScalar(scaleRef.current);

      if (scaleRef.current > 0.01) {
        ref.current.position.y = position[1];
      }
    }
  });

  return (
    <group ref={ref} position={position} rotation={rotation}>
      <mesh>
        <planeGeometry args={[width, height]} />
        <meshPhysicalMaterial
          transmission={1}
          opacity={1}
          roughness={0.15}
          metalness={0.45}
          clearcoat={1}
          clearcoatRoughness={0.1}
          ior={1.5}
          thickness={0.5}
          color="#0B0F19"
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* 1px electric neon border */}
      <lineSegments>
        <edgesGeometry args={[new THREE.PlaneGeometry(width, height)]} />
        <lineBasicMaterial color="#00D2FF" linewidth={1} />
      </lineSegments>
      {children}
    </group>
  );
};

const CameraController = ({ 
  triggerTimeRef, 
  startPos, 
  targetPos, 
  startTarget, 
  targetTarget,
  resetTrigger
}: any) => {
  const { camera, controls } = useThree();

  useEffect(() => {
    if (resetTrigger > 0) {
      startPos.current.copy(camera.position);
      if (controls) {
        startTarget.current.copy((controls as any).target);
      } else {
        startTarget.current.set(0, 0, 0);
      }
      targetPos.current.set(0, 0, 9.6);
      targetTarget.current.set(0, 0, 0);
      triggerTimeRef.current = 0; // Trigger copy and lerp in frame loop
    }
  }, [resetTrigger, camera, controls, startPos, targetPos, targetTarget, triggerTimeRef]);
  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    
    // Responsive aspect ratio Z scale factor
    const aspect = state.size.width / state.size.height;
    const zoomFactor = aspect < 1.85 ? 1.85 / aspect : 1.0;
    
    // Initialize starting camera vectors on trigger
    if (triggerTimeRef.current === 0) {
      startPos.current.copy(state.camera.position);
      
      const controls = state.controls as any;
      if (controls) {
        startTarget.current.copy(controls.target);
      } else {
        startTarget.current.set(0, 0, 0);
      }
      
      triggerTimeRef.current = time;
    }
    
    if (triggerTimeRef.current > 0) {
      const elapsed = time - triggerTimeRef.current;
      const duration = 1.6; // Smooth 1.6-second camera sweep
      const progress = Math.min(elapsed / duration, 1.0);
      const t = progress * (2 - progress); // Ease-out quadratic
      
      const responsiveTargetPos = targetPos.current.clone();
      if (targetPos.current.z > 7.0) {
        responsiveTargetPos.z = targetPos.current.z * zoomFactor;
      }
      
      state.camera.position.lerpVectors(startPos.current, responsiveTargetPos, t);
      
      const controls = state.controls as any;
      if (controls) {
        controls.target.lerpVectors(startTarget.current, targetTarget.current, t);
        controls.update();
      }
      
      if (progress >= 1.0) {
        triggerTimeRef.current = -99;
      }
    } else {
      // Keep responsive Z adjustment active even when not in transition
      if (targetPos.current.z > 7.0) {
        state.camera.position.z = targetPos.current.z * zoomFactor;
      }
    }
  });

  return null;
};

const FloatingGraph = ({ position, rotation, children, trigger, flyInStart, audioEnabled = true, activeTheme, heightPx = 200, onClose }: any) => {
  const ref = useRef<THREE.Group>(null);
  const prevTrigger = useRef<any>(undefined);
  const transitionTimeRef = useRef(-99);
  const hasSwappedRef = useRef(false);
  const [flickerOpacity, setFlickerOpacity] = useState(1.0);
  const flyInStartPos = useRef<[number, number, number]>(position);

  const playSciFiSound = () => {
    if (!audioEnabled || typeof window === "undefined") return;
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;
    try {
      const ctx = new AudioContextClass();
      const time = ctx.currentTime;
      
      // Laser / Hologram sweep sweep
      const osc1 = ctx.createOscillator();
      osc1.type = "sine";
      osc1.frequency.setValueAtTime(600, time);
      osc1.frequency.exponentialRampToValueAtTime(1800, time + 0.15);
      
      const osc2 = ctx.createOscillator();
      osc2.type = "square";
      osc2.frequency.setValueAtTime(200, time);
      osc2.frequency.exponentialRampToValueAtTime(1200, time + 0.12);
      
      const gain1 = ctx.createGain();
      gain1.gain.setValueAtTime(0.04, time);
      gain1.gain.exponentialRampToValueAtTime(0.001, time + 0.15);
      
      const gain2 = ctx.createGain();
      gain2.gain.setValueAtTime(0.015, time);
      gain2.gain.exponentialRampToValueAtTime(0.001, time + 0.12);
      
      osc1.connect(gain1);
      gain1.connect(ctx.destination);
      
      osc2.connect(gain2);
      gain2.connect(ctx.destination);
      
      osc1.start(time);
      osc1.stop(time + 0.16);
      
      osc2.start(time);
      osc2.stop(time + 0.13);
    } catch (e) {}
  };

  useFrame((state) => {
    if (ref.current) {
      const time = state.clock.getElapsedTime();
      
      // Trigger transition if trigger value changes
      if (trigger !== prevTrigger.current) {
        prevTrigger.current = trigger;
        transitionTimeRef.current = time;
        hasSwappedRef.current = false;
        
        if (flyInStart) {
          flyInStartPos.current = flyInStart;
        } else {
          flyInStartPos.current = [ref.current.position.x, ref.current.position.y, ref.current.position.z];
        }
      }

      const elapsed = time - transitionTimeRef.current;
      const duration = 1.2; // 1.2-second fly-in & flip transition

      let scaleFactor = 1.0;
      let flipRotation = 0.0;
      let currentOpacity = 1.0;
      
      let targetX = position[0];
      let targetY = position[1];
      let targetZ = position[2];

      if (transitionTimeRef.current > 0 && elapsed < duration) {
        const progress = elapsed / duration;
        
        // 1. Zoom
        scaleFactor = 1.0 + Math.sin(progress * Math.PI) * 0.22;
        
        // 2. Y-Rotation
        flipRotation = progress * Math.PI * 2.0;

        // 3. Flight path linear interpolation with ease-out cubic
        const t = 1 - Math.pow(1 - progress, 3);
        const curX = THREE.MathUtils.lerp(flyInStartPos.current[0], targetX, t);
        const curY = THREE.MathUtils.lerp(flyInStartPos.current[1], targetY, t);
        const curZ = THREE.MathUtils.lerp(flyInStartPos.current[2], targetZ, t);
        ref.current.position.set(curX, curY, curZ);

        // Sound on swap
        if (progress >= 0.25 && !hasSwappedRef.current) {
          hasSwappedRef.current = true;
          playSciFiSound();
        }

        // Flicker opacity
        if (progress >= 0.25 && progress < 0.60) {
          currentOpacity = Math.sin(time * 80.0) > 0.0 ? 1.0 : 0.15;
        }
      } else {
        // Continuous smooth slide towards target position when not in active transition
        ref.current.position.x = THREE.MathUtils.lerp(ref.current.position.x, targetX, 0.1);
        ref.current.position.y = THREE.MathUtils.lerp(ref.current.position.y, targetY, 0.1);
        ref.current.position.z = THREE.MathUtils.lerp(ref.current.position.z, targetZ, 0.1);
      }

      if (flickerOpacity !== currentOpacity) {
        setFlickerOpacity(currentOpacity);
      }

      ref.current.scale.setScalar(scaleFactor);
      ref.current.rotation.y = rotation[1] + flipRotation;
    }
  });

  return (
    <group ref={ref} position={position} rotation={rotation}>
      <Html center position={[0, 0, 0.1]}>
        <HoloCard 
          className="w-[280px] floating-telemetry-panel text-white transition-opacity duration-[30ms]" 
          style={{ opacity: flickerOpacity, height: `${heightPx}px` }}
          theme={activeTheme}
          onClose={onClose}
        >
          {children}
        </HoloCard>
      </Html>
    </group>
  );
};


const FluidFloor = ({ waveFrequency }: { waveFrequency: number }) => {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.getElapsedTime();
      materialRef.current.uniforms.uFrequency.value = waveFrequency;
    }
  });

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uFrequency: { value: 6.28 }
  }), []);

  return (
    <group position={[0, -2.5, 0]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[30, 30]} />
        <shaderMaterial
          ref={materialRef}
          vertexShader={`
            varying vec2 vUv;
            void main() {
              vUv = uv;
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `}
          fragmentShader={`
            uniform float uTime;
            uniform float uFrequency;
            varying vec2 vUv;

            // Continuous spectrum color blending
            vec3 getSpectrum(float t) {
              float val = clamp(t, 0.0, 0.999);
              float segment = val * 6.0;
              float f = fract(segment);
              int idx = int(floor(segment));
              
              vec3 c0 = vec3(1.0, 0.0, 0.0);    // Red
              vec3 c1 = vec3(1.0, 0.45, 0.0);   // Orange
              vec3 c2 = vec3(1.0, 0.95, 0.0);   // Yellow
              vec3 c3 = vec3(0.0, 1.0, 0.15);   // Green
              vec3 c4 = vec3(0.0, 0.55, 1.0);   // Blue
              vec3 c5 = vec3(0.45, 0.0, 1.0);   // Purple
              vec3 c6 = vec3(1.0, 0.0, 0.65);   // Magenta

              if (idx == 0) return mix(c0, c1, f);
              if (idx == 1) return mix(c1, c2, f);
              if (idx == 2) return mix(c2, c3, f);
              if (idx == 3) return mix(c3, c4, f);
              if (idx == 4) return mix(c4, c5, f);
              return mix(c5, c6, f);
            }

            // Traveling wave along vUv.y (front-to-back) with curved wiggles
            float getWave(vec2 p) {
              float flow = p.y - uTime * 0.22;
              float waveVal = sin(flow * uFrequency + sin(p.x * (uFrequency * 0.75)) * 0.6);
              return waveVal * 0.5 + 0.5; // normalize to 0.0 -> 1.0
            }

            void main() {
              // 1. Calculate traveling color wave
              float wave = getWave(vUv);
              
              // Highly saturated, ultra-vivid emissive rainbow colors
              vec3 fluidColor = getSpectrum(wave);
              
              // 2. Generate perfect mathematical vector diamond grid on the GPU
              float dotDensity = 135.0; // Denser, tighter packing
              vec2 grid = vUv * dotDensity;
              vec2 localUv = fract(grid) - vec2(0.5); // Local coords inside cell: -0.5 to 0.5
              
              // L1 Manhattan distance creates mathematically perfect vector diamonds
              float d = abs(localUv.x) + abs(localUv.y);
              
              // Halftone size fade: smaller max radius (0.32) so diamonds remain distinct with spacing
              float distToCenter = distance(vUv, vec2(0.5));
              float maxRadius = 0.32 * clamp(1.0 - distToCenter * 2.2, 0.0, 1.0);
              
              // Draw vector diamond with edge anti-aliasing (0.07 width)
              float diamondMask = smoothstep(maxRadius, maxRadius - 0.07, d);
              
              // 3. Make diamond dots glow at maximum intensity
              vec3 finalColor = fluidColor * diamondMask * 2.2;
              
              // Fade out edges radially and mask transparency by the diamond shapes
              float alpha = diamondMask * smoothstep(0.5, 0.12, distToCenter) * 0.9;
              
              gl_FragColor = vec4(finalColor, alpha);
            }
          `}
          uniforms={uniforms}
          transparent={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  );
};

const DataRing = ({ position, radius = 1, color = "#ff007f", speed = 1 }: any) => {
  const ref = useRef<THREE.Group>(null);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.z -= speed * 0.015;
    }
  });

  return (
    <group position={position} rotation={[-Math.PI / 2, 0, 0]} ref={ref}>
      <Ring args={[radius * 0.8, radius, 32, 1, 0, Math.PI * 1.5]}>
        <meshBasicMaterial color={color} side={THREE.DoubleSide} transparent opacity={0.6} />
      </Ring>
      <Ring args={[radius * 0.9, radius * 0.95, 32, 1, Math.PI * 1.6, Math.PI * 0.3]}>
        <meshBasicMaterial color="#00E5FF" side={THREE.DoubleSide} transparent opacity={0.6} />
      </Ring>
    </group>
  );
};

// Deterministic Fibonacci sphere lattice distribution to avoid Math.random() context conflicts
const NetworkNodes = ({ position = [0, 0, 0] }: any) => {
  const groupRef = useRef<THREE.Group>(null);

  const nodes = useMemo(() => {
    const pointsList = [];
    const count = 20;
    for (let i = 0; i < count; i++) {
      const y = 1 - (i / (count - 1)) * 2;
      const radius = Math.sqrt(1 - y * y);
      const theta = 2.399963 * i; // golden angle step in radians
      pointsList.push({
        position: new THREE.Vector3(
          Math.cos(theta) * radius * 3.5,
          y * 3.5,
          Math.sin(theta) * radius * 3.5
        ),
      });
    }
    return pointsList;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.getElapsedTime();
      groupRef.current.rotation.y = time * 0.04;
      groupRef.current.rotation.x = time * 0.015;
    }
  });

  return (
    <group ref={groupRef} position={position}>
      {/* 3D wireframe Icosahedron enclosing the node cluster */}
      <mesh>
        <icosahedronGeometry args={[4.2, 1]} />
        <meshBasicMaterial wireframe={true} color="#00E5FF" transparent opacity={0.12} />
      </mesh>

      {nodes.map((node, i) => (
        <Sphere key={i} args={[0.05, 16, 16]} position={node.position}>
          <meshBasicMaterial color="#00E5FF" />
        </Sphere>
      ))}

      {nodes.slice(0, 19).map((node, i) => (
        <Line
          key={`line-${i}`}
          points={[node.position, nodes[i + 1].position]}
          color="#ff007f"
          lineWidth={0.5}
          transparent
          opacity={0.15}
        />
      ))}
    </group>
  );
};

const AudioEngine = ({ isEnabled }: { isEnabled: boolean }) => {
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (!isEnabled) return;
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;

    audioCtxRef.current = new AudioContextClass();
    const ctx = audioCtxRef.current;

    // Ambient Hum
    const osc = ctx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = 55; // Low hum
    const gain = ctx.createGain();
    gain.gain.value = 0.05;
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();

    // Random data chirps
    const interval = setInterval(() => {
      const beepOsc = ctx.createOscillator();
      beepOsc.type = "square";
      beepOsc.frequency.value = 800 + Math.random() * 1200;
      
      const beepGain = ctx.createGain();
      beepGain.gain.setValueAtTime(0, ctx.currentTime);
      beepGain.gain.linearRampToValueAtTime(0.02, ctx.currentTime + 0.01);
      beepGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
      
      beepOsc.connect(beepGain);
      beepGain.connect(ctx.destination);
      
      beepOsc.start();
      beepOsc.stop(ctx.currentTime + 0.1);
    }, 2000);

    return () => {
      osc.stop();
      ctx.close();
      clearInterval(interval);
    };
  }, [isEnabled]);

  return null;
};

function SciFiStudioBody() {
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [showScreens, setShowScreens] = useState(true);
  const [studioDepth, setStudioDepth] = useState<number>(19); // Default back wall projection depth at 19m
  const [waveFrequency, setWaveFrequency] = useState<number>(6.28); // Dynamic floor color gradient flow frequency
  const [activeTheme, setActiveTheme] = useState<"emerald-cut" | "aquamarine" | "holographic" | "frosted" | "matte-clay">("emerald-cut"); // Dynamic holographic card styling themes
  
  const [canvasSize, setCanvasSize] = useState({ width: 1200, height: 800 });
  
  const avatarRef = useRef<any>(null);
  const { registerAvatar, gender, persona, isPlaying, setIsPlaying } = useAvatar();
  const avatarContextValue = useContext(AvatarContext);

  useEffect(() => {
    registerAvatar(avatarRef.current);
    return () => registerAvatar(null);
  }, [avatarRef.current, registerAvatar]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handleResize = () => {
      setCanvasSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    window.addEventListener("resize", handleResize);
    handleResize();
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  interface SlotGraph {
    id: string;
    key: number;
    spawnPos: [number, number, number];
  }
  
  // Initialize with all 6 widgets open per starting default state
  const [activeGraphs, setActiveGraphs] = useState<(SlotGraph | null)[]>(() => {
    const initial = Array(6).fill(null);
    initial[0] = { id: "queue_time", key: 1, spawnPos: [0, 0, -10] };
    initial[1] = { id: "noc_share", key: 1, spawnPos: [0, 0, -10] };
    initial[2] = { id: "rejection_reasons", key: 1, spawnPos: [0, 0, -10] };
    initial[3] = { id: "weekly_volume", key: 1, spawnPos: [0, 0, -10] };
    initial[4] = { id: "top_reassignments", key: 1, spawnPos: [0, 0, -10] };
    initial[5] = { id: "top_issues", key: 1, spawnPos: [0, 0, -10] };
    return initial;
  });
  const replaceIdx = useRef(0);

  // Refs for camera angle sweeping (defaulting to straight front view)
  const cameraTransitionRef = useRef(-99);
  const startCamPos = useRef(new THREE.Vector3());
  const targetCamPos = useRef(new THREE.Vector3(0, 0, 9.6));
  const startCamTarget = useRef(new THREE.Vector3());
  const targetCamTarget = useRef(new THREE.Vector3(0, 0, 0));
  
  const [resetTrigger, setResetTrigger] = useState(0);

  const resetView = () => {
    setStudioDepth(19);

    setActiveGraphs(() => {
      const initial = Array(6).fill(null);
      initial[0] = { id: "queue_time", key: 1, spawnPos: [0, 0, -10] };
      initial[1] = { id: "noc_share", key: 1, spawnPos: [0, 0, -10] };
      initial[2] = { id: "rejection_reasons", key: 1, spawnPos: [0, 0, -10] };
      initial[3] = { id: "weekly_volume", key: 1, spawnPos: [0, 0, -10] };
      initial[4] = { id: "top_reassignments", key: 1, spawnPos: [0, 0, -10] };
      initial[5] = { id: "top_issues", key: 1, spawnPos: [0, 0, -10] };
      return initial;
    });

    setResetTrigger(prev => prev + 1);
    targetCamPos.current.set(0, 0, 9.6);
    targetCamTarget.current.set(0, 0, 0);
    playRoutingChirp(900);
  };

  // Click handler to detect graph card clicks on the backdrop wall
  const handleDashboardClick = (e: React.MouseEvent) => {
    const card = (e.target as HTMLElement).closest("[id$='-card'], [id*='-card']");
    if (card) {
      const id = card.id;
      let widgetId = "";
      if (id.includes("reassignment")) widgetId = "top_reassignments";
      else if (id.includes("complaint") || id.includes("categories")) widgetId = "top_issues";
      else if (id.includes("rejection")) widgetId = "rejection_reasons";
      else if (id.includes("noc")) widgetId = "noc_share";
      else if (id.includes("weekly")) widgetId = "weekly_volume";
      else if (id.includes("warning")) widgetId = "early_warning";
      else if (id.includes("distribution")) widgetId = "ticket_dist";
      else if (id.includes("queue") || id.includes("time")) widgetId = "queue_time";
      else if (id.includes("calendar")) widgetId = "telemetry_calendar";
      else if (id.includes("roaming")) widgetId = "roaming";

      if (widgetId) {
        let startX = 0;
        let startY = 1.0 + (19 * 0.08); // height at studioDepth = 19
        if (widgetId === "top_reassignments" || widgetId === "top_issues" || widgetId === "weekly_volume" || widgetId === "early_warning") {
          startX = -3.5;
        } else if (widgetId === "rejection_reasons" || widgetId === "noc_share" || widgetId === "queue_time") {
          startX = 3.5;
        }

        // Assign to empty slot: check Right side first (0-2), then Left side (3-5)
        setActiveGraphs((prev) => {
          let updated = [...prev];
          const existingIdx = updated.findIndex(g => g?.id === widgetId);
          if (existingIdx !== -1) {
            const existing = updated[existingIdx]!;
            updated[existingIdx] = {
              ...existing,
              key: existing.key + 1,
              spawnPos: [startX, startY, -19]
            };
          } else {
            // Find first empty slot on the Right side (indices 0, 1, 2)
            let targetSlot = -1;
            for (let i = 0; i < 3; i++) {
              if (updated[i] === null) {
                targetSlot = i;
                break;
              }
            }
            // If right side is full, find first empty slot on the Left side (indices 3, 4, 5)
            if (targetSlot === -1) {
              for (let i = 3; i < 6; i++) {
                if (updated[i] === null) {
                  targetSlot = i;
                  break;
                }
              }
            }
            // If all 6 slots are covered, replace round-robin across all 6 slots
            if (targetSlot === -1) {
              targetSlot = replaceIdx.current;
              replaceIdx.current = (replaceIdx.current + 1) % 6;
            }

            updated[targetSlot] = {
              id: widgetId,
              key: Date.now(),
              spawnPos: [startX, startY, -19]
            };
          }
          return updated;
        });

        // 2. Adjust backdrop depth to 19m
        setStudioDepth(19);

        // 3. Center wide camera angle (no avatar shrinking, captures both sides cleanly without blocking backdrop)
        targetCamPos.current.set(0.0, 1.2, 8.2);
        targetCamTarget.current.set(0.0, 0.4, 0.0);
        cameraTransitionRef.current = 0; // Trigger initialization inside useFrame
      }
    }
  };

  const renderLeftWidgetContent = (id: string, graphKey: number) => {
    switch (id) {
      case "top_reassignments":
        return <TopReassignmentsQueue />;
      case "top_issues":
      default:
        return <TopComplaintCategories defaultShowReasons={false} onToggle={() => {
          setActiveGraphs(prev => prev.map(g => g && g.id === id ? { ...g, key: g.key + 1 } : g));
        }} />;
      case "rejection_reasons":
        return <TopRejectionReason />;
      case "noc_share":
        return <PercentageNocTickets />;
      case "weekly_volume":
        return <WeeklyComplaintVolume />;
      case "early_warning":
        return <EarlyWarningDiagnostics />;
      case "ticket_dist":
        return <TotalTicketDistribution />;
      case "queue_time":
        return <AvgQueueTime />;
      case "telemetry_calendar":
        return <TelemetryCalendar selectedDate={null} onSelectDate={() => {}} />;
      case "roaming":
        return <TopRoamingComplaints />;
    }
  };

  const getGraphHeightPx = (id: string) => {
    switch (id) {
      case "early_warning": return 350;
      case "ticket_dist": return 320;
      case "queue_time": return 280;
      case "telemetry_calendar": return 290;
      case "weekly_volume": return 230;
      case "top_reassignments": return 195;
      case "noc_share": return 190;
      case "roaming": return 160;
      case "rejection_reasons": return 195;
      case "top_issues":
      default:
        return 210;
    }
  };

  const getGraphHeightUnits = (id: string) => {
    return getGraphHeightPx(id) / 100;
  };


  const getDynamicLayouts = (graphs: (SlotGraph | null)[]) => {
    const layouts: { position: [number, number, number]; rotation: [number, number, number]; heightPx: number }[] = Array(6).fill({
      position: [0, 0, 0],
      rotation: [0, 0, 0],
      heightPx: 200
    });

    // Decouple gaps and placement spacing between Normal Mode (narrow) and Fullscreen Mode (wide)
    const isNormalMode = canvasSize.width < 1400;
    const gap = isNormalMode ? 0.38 : 0.58; 
    const xOffset = isNormalMode ? 6.6 : 6.6;

    // 1. Process Right side (indices 0, 1, 2)
    const rightActive = graphs.slice(0, 3)
      .map((g, idx) => ({ graph: g, originalIdx: idx }))
      .filter(item => item.graph !== null);

    if (rightActive.length > 0) {
      const totalH = rightActive.reduce((sum, item) => sum + getGraphHeightUnits(item.graph!.id), 0) + gap * (rightActive.length - 1);
      let curY = 0.0 - totalH / 2; // Symmetrically center the column around Y = 0
      rightActive.forEach((item) => {
        const hUnits = getGraphHeightUnits(item.graph!.id);
        const yCenter = curY + hUnits / 2;
        layouts[item.originalIdx] = {
          position: [xOffset, yCenter, 1.85], 
          rotation: [0, 0, 0],
          heightPx: getGraphHeightPx(item.graph!.id)
        };
        curY += hUnits + gap; // Forces equal spacing gaps
      });
    }

    // 2. Process Left side (indices 3, 4, 5)
    const leftActive = graphs.slice(3, 6)
      .map((g, idx) => ({ graph: g, originalIdx: idx + 3 }))
      .filter(item => item.graph !== null);

    if (leftActive.length > 0) {
      const totalH = leftActive.reduce((sum, item) => sum + getGraphHeightUnits(item.graph!.id), 0) + gap * (leftActive.length - 1);
      let curY = 0.0 - totalH / 2; // Symmetrically center the column around Y = 0
      leftActive.forEach((item) => {
        const hUnits = getGraphHeightUnits(item.graph!.id);
        const yCenter = curY + hUnits / 2;
        layouts[item.originalIdx] = {
          position: [-xOffset, yCenter, 1.85], 
          rotation: [0, 0, 0],
          heightPx: getGraphHeightPx(item.graph!.id)
        };
        curY += hUnits + gap; // Forces equal spacing gaps
      });
    }

    return layouts;
  };





  // High-frequency routing beep using Web Audio API
  const playRoutingChirp = (frequency = 1200) => {
    if (!audioEnabled || typeof window === "undefined") return;
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;

    try {
      const ctx = new AudioContextClass();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = "sine";
      osc.frequency.setValueAtTime(frequency, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(frequency * 1.6, ctx.currentTime + 0.08);
      
      gain.gain.setValueAtTime(0.025, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
    } catch (e) {}
  };



  return (
    <div className="w-full h-full relative bg-[#0B0F19] font-sans overflow-hidden">
      {/* Laser scanline and FUI CSS overrides */}
      <style>{`
        @keyframes scanDownFast {
          0% { top: 0%; opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
        .animate-scanDown {
          animation: scanDownFast 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .scifi-slider {
          -webkit-appearance: none;
          appearance: none;
          background: rgba(255, 255, 255, 0.12) !important;
          height: 4px !important;
          border-radius: 2px !important;
          outline: none;
        }
        .scifi-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 14px !important;
          height: 14px !important;
          border-radius: 50% !important;
          background: #ffffff !important;
          cursor: pointer;
          box-shadow: 0 0 8px rgba(255, 255, 255, 0.6) !important;
          transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .scifi-slider::-webkit-slider-thumb:hover {
          transform: scale(1.3) !important;
        }
        .scifi-override .recharts-responsive-container {
          background: transparent !important;
        }
        .scifi-override,
        .scifi-override *,
        .scifi-override div {
          scrollbar-width: none !important;
          -ms-overflow-style: none !important;
          user-select: none !important;
          -webkit-user-select: none !important;
        }
        .scifi-override *::-webkit-scrollbar {
          display: none !important;
          width: 0 !important;
          height: 0 !important;
        }
        .scifi-override [class*="overflow-y-auto"] {
          overflow-y: hidden !important;
        }
        .scifi-override [class*="overflow-auto"] {
          overflow: hidden !important;
        }
         .floating-telemetry-panel [id*="-card"],
         .floating-telemetry-panel [class*="glass-card"] {
           height: 100% !important;
           width: 100% !important;
           margin: 0 !important;
           padding: 0 !important; /* Eliminate duplicate padding to prevent extra margins */
           background: transparent !important;
           background-color: transparent !important;
           border: none !important;
           box-shadow: none !important;
         }
      `}</style>

      {/* Initialization Overlay */}
      {!audioEnabled && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-[#333334]/95 backdrop-blur-md">
          <button
            onClick={() => {
              try {
                const s = new Audio("/sounds/futuristic-ui-digital-click-davies-aguirre-1-00-00.mp3");
                s.volume = 0.5;
                s.play().catch(() => {});
              } catch (e) {}
              setAudioEnabled(true);
            }}
            className="group px-12 py-5 bg-[#252526]/50 border border-white/20 backdrop-blur-2xl rounded-full transition-all duration-150 active:translate-y-[2px] shadow-[inset_0_2px_4px_rgba(255,255,255,0.15),inset_0_-2px_4px_rgba(0,0,0,0.5),0_15px_30px_rgba(0,0,0,0.4)] active:shadow-[inset_0_1px_2px_rgba(255,255,255,0.15),inset_0_-1px_2px_rgba(0,0,0,0.5),0_5px_10px_rgba(0,0,0,0.5)] cursor-pointer select-none focus:outline-none"
          >
            <span 
              className="text-gray-300 font-sans font-medium tracking-widest text-xs uppercase transition-all duration-200 group-hover:text-white"
              style={{ textShadow: "0 1px 1px rgba(255, 255, 255, 0.2), 0 -1px 1px rgba(0,0,0,0.6)" }}
            >
              Initialize Studio
            </span>
          </button>
        </div>
      )}

      {/* Audio Engine */}
      <AudioEngine isEnabled={audioEnabled} />

      {/* Main 3D Canvas */}
      <Canvas
        camera={{ position: [0, 0, 9.6], fov: 65 }}
        gl={{ antialias: false, powerPreference: "high-performance" }}
        className="absolute inset-0"
        style={{ transform: "translate3d(0, 0, 0)", backfaceVisibility: "hidden" }}
      >
        {/* Endless deep vacuum fog - scales dynamically with depth */}
        <fog attach="fog" args={["#0B0F19", 5, studioDepth + 27]} />

        <ambientLight intensity={0.2} />
        <pointLight position={[0, 0, 2]} intensity={2} color="#7FFFD4" />
        <pointLight position={[2, 2, 2]} intensity={1.5} color="#7FFFD4" />

        <OrbitControls enableZoom={false} enablePan={false} />

        {/* 3D Halftone Floor with packed diamond dithered radial gradient and dynamic fragment shader fluid flow */}
        <FluidFloor waveFrequency={waveFrequency} />

        {/* Network Nodes Background - stays behind the background cinema screen */}
        <NetworkNodes position={[0, 1.0 + (studioDepth * 0.05), -(studioDepth + 12)]} />

        {/* Panoramic Command Deck (Cinema size backdrop, depth dynamically controlled by the slider) */}
        <Html center position={[0, 1.2 + (studioDepth * 0.09), -studioDepth]} distanceFactor={18.0}>
          <div 
            onClick={handleDashboardClick}
            className="w-[1450px] h-[920px] bg-[#0B0F19] rounded-3xl overflow-hidden border border-[#7FFFD4]/30 scifi-override text-white p-6 opacity-45 hover:opacity-95 transition-opacity duration-500 pointer-events-auto shadow-[0_0_50px_rgba(127,255,212,0.1)] cursor-pointer"
          >
            <div className="flex justify-between items-center mb-3 pb-1 border-b border-[#7FFFD4]/20 relative">
              <span className="text-[11px] uppercase font-mono tracking-widest text-[#7FFFD4]">Command Telemetry backdrop (Cinema Feed)</span>
              <div className="w-1.5 h-1.5 rounded-full bg-[#7FFFD4] animate-pulse" />
            </div>
            <div className="w-full h-full pointer-events-auto">
              <ComplaintDashboardView />
            </div>
          </div>
        </Html>

        <CameraController 
          triggerTimeRef={cameraTransitionRef}
          startPos={startCamPos}
          targetPos={targetCamPos}
          startTarget={startCamTarget}
          targetTarget={targetCamTarget}
          resetTrigger={resetTrigger}
        />

        {/* Central Pedestal Group - Ensures the avatar is always perfectly centered inside the ring */}
        <group position={[0, -2.5, 2.3]}>
          {/* DataRing flat on the floor of the pedestal */}
          <DataRing position={[0, 0, 0]} radius={1.1} speed={0.5} color="#7FFFD4" />

          {/* Central Holographic Avatar - Rendered relative to the group center */}
          <Html center position={[0, 1.8, 0]} distanceFactor={5.5}>
            <div className="w-[380px] h-[550px] pointer-events-auto relative select-none">
              {avatarContextValue ? (
                <AvatarContext.Provider value={avatarContextValue}>
                  <TalkingAvatar gender={gender} persona={persona} isPlaying={isPlaying} onSpeakingChange={setIsPlaying} accentColor="#7FFFD4" ref={avatarRef} />
                </AvatarContext.Provider>
              ) : (
                <TalkingAvatar gender={gender} persona={persona} isPlaying={isPlaying} onSpeakingChange={setIsPlaying} accentColor="#7FFFD4" ref={avatarRef} />
              )}
            </div>
          </Html>
        </group>


        {/* Bilateral Telemetry Graphs (Dynamic) - aligned vertically in fixed slots on both sides */}
        {(() => {
          const layouts = getDynamicLayouts(activeGraphs);
          return activeGraphs.map((graph, idx) => {
            if (!graph) return null;
            const layout = layouts[idx];
            return (
              <FloatingGraph 
                key={graph.id} // Fixed slots per key, no sliding or rolling shifts
                position={layout.position} 
                rotation={layout.rotation} 
                trigger={graph.key}
                flyInStart={graph.spawnPos}
                audioEnabled={audioEnabled}
                activeTheme={activeTheme}
                heightPx={layout.heightPx}
                onClose={() => {
                  setActiveGraphs(prev => prev.map(g => g && g.id === graph.id ? null : g));
                  playRoutingChirp(300);
                }}
              >
                {renderLeftWidgetContent(graph.id, graph.key)}
              </FloatingGraph>
            );
          });
        })()}

      </Canvas>

      
      {/* Control Panel (Footer UI) - styled as a clear Liquid Glass capsule dock */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-40 bg-white/10 border border-white/25 backdrop-blur-2xl rounded-full px-8 py-3.5 flex items-center gap-6 pointer-events-auto shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_15px_35px_rgba(0,0,0,0.3)] select-none">
        {/* Cinema Backdrop Depth Control (Z-Zoom Slider) */}
        <div className="flex items-center gap-2">
          <div className="flex flex-col min-w-[70px]">
            <span className="text-[8px] font-bold font-sans uppercase tracking-widest text-white/90 leading-none select-none">Back Wall</span>
            <span className="text-[8px] font-bold font-sans uppercase tracking-widest text-white/90 select-none">Depth</span>
          </div>
          <input 
            type="range" 
            min="9" 
            max="200" 
            value={studioDepth}
            onChange={(e) => {
              const val = parseInt(e.target.value);
              setStudioDepth(val);
              playRoutingChirp(600 + (val / 200) * 1000);
            }}
            className="w-24 h-1 scifi-slider cursor-pointer focus:outline-none"
            title="Adjust control room back wall projection depth"
          />
          <span className="text-white font-mono font-bold min-w-[32px] text-right text-[10px]">{studioDepth}m</span>
        </div>

        {/* Separator line */}
        <div className="w-[1px] h-4 bg-white/15" />

        {/* Gradient Delta Frequency Control Slider */}
        <div className="flex items-center gap-2">
          <div className="flex flex-col min-w-[70px]">
            <span className="text-[8px] font-bold font-sans uppercase tracking-widest text-white/90 leading-none select-none">Gradient</span>
            <span className="text-[8px] font-bold font-sans uppercase tracking-widest text-white/90 select-none">Delta</span>
          </div>
          <input 
            type="range" 
            min="2.0" 
            max="18.0" 
            step="0.1"
            value={waveFrequency}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setWaveFrequency(val);
              playRoutingChirp(400 + (val / 18.0) * 800);
            }}
            className="w-24 h-1 scifi-slider cursor-pointer focus:outline-none"
            title="Adjust floor color gradient waves frequency"
          />
          <span className="text-white font-mono font-bold min-w-[38px] text-right text-[10px]">{waveFrequency.toFixed(1)}Hz</span>
        </div>

        {/* Separator line */}
        <div className="w-[1px] h-4 bg-white/15" />

        {/* Theme Selector (Collapsed Dropdown) */}
        <div className="flex items-center gap-2">
          <span className="text-[8px] font-bold font-sans uppercase tracking-widest text-white/90 select-none">Theme</span>
          <select
            value={activeTheme}
            onChange={(e) => {
              const t = e.target.value as any;
              setActiveTheme(t);
              playRoutingChirp(700 + (t === "emerald-cut" ? 30 : t === "aquamarine" ? 60 : t === "holographic" ? 90 : t === "frosted" ? 120 : 150));
            }}
            className="bg-transparent border-none text-white text-[9px] font-bold font-sans uppercase tracking-wider outline-none cursor-pointer appearance-none -webkit-appearance-none text-left pointer-events-auto select-none py-0.5 hover:text-cyan-400 transition-colors"
          >
            <option value="emerald-cut" className="bg-[#121824] text-white">Emerald Cut</option>
            <option value="aquamarine" className="bg-[#121824] text-white">Aquamarine</option>
            <option value="holographic" className="bg-[#121824] text-white">Holographic</option>
            <option value="frosted" className="bg-[#121824] text-white">Frosted</option>
            <option value="matte-clay" className="bg-[#121824] text-white">Matte Clay</option>
          </select>
        </div>

        {/* Separator line */}
        <div className="w-[1px] h-4 bg-white/15" />

        {/* Reusable Speech Controls Panel (Flat & borderless inside footer) */}
        <AvatarControlPanel className="bg-transparent border-none p-0 shadow-none gap-4" />

        {/* Separator line */}
        <div className="w-[1px] h-4 bg-white/15" />

        {/* Reset Button */}
        <button
          onClick={resetView}
          className="px-3.5 py-1.5 text-[8px] font-bold font-sans uppercase tracking-wider rounded-full transition-all duration-300 bg-white/10 text-white border border-white/20 hover:bg-white/20 active:scale-95 pointer-events-auto cursor-pointer flex items-center gap-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]"
          title="Reset back wall depth, opened cards, and camera view"
        >
          <RotateCcw className="h-2.5 w-2.5" />
          Reset View
        </button>
      </div>

      {/* Scanline Overlay (CSS) */}
      <div className="absolute inset-0 pointer-events-none opacity-10 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px]" />
    </div>
  );
}

export default function SciFiStudio() {
  return (
    <AvatarProvider>
      <SciFiStudioBody />
    </AvatarProvider>
  );
}
