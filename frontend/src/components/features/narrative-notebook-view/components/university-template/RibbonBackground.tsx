"use client";

import React, { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { Environment, Float } from "@react-three/drei";

// Suppress THREE.Clock deprecation warnings from browser console
if (typeof window !== "undefined") {
  const originalWarn = console.warn;
  console.warn = (...args) => {
    if (typeof args[0] === "string" && args[0].includes("THREE.Clock")) {
      return;
    }
    originalWarn.apply(console, args);
  };
}

function ContinuousRibbon() {
  const meshRef = useRef<THREE.Mesh>(null);
  const geoRef = useRef<THREE.PlaneGeometry>(null);

  // Procedurally generate the UAE Flag as a CanvasTexture
  const flagTexture = useMemo(() => {
    if (typeof document === 'undefined') return null;

    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 512;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    
    // Draw UAE Flag for a horizontal ribbon
    // The ribbon sweeps left to right. Left edge is Red.
    
    // Green band (Top 1/3)
    ctx.fillStyle = "#00732F";
    ctx.fillRect(0, 0, 2048, 171);
    
    // White band (Middle 1/3)
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 171, 2048, 170);
    
    // Black band (Bottom 1/3)
    ctx.fillStyle = "#111111"; // Slight off-black so it catches lighting
    ctx.fillRect(0, 341, 2048, 171);

    // Red vertical band (Left edge)
    ctx.fillStyle = "#FF0000";
    ctx.fillRect(0, 0, 400, 512);

    const texture = new THREE.CanvasTexture(canvas);
    // Ensure the texture maps smoothly without wrapping artifacts
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    texture.anisotropy = 16;
    texture.needsUpdate = true;
    return texture;
  }, []);

  useFrame((state) => {
    if (!geoRef.current) return;
    
    const time = state.clock.getElapsedTime();
    const position = geoRef.current.attributes.position;
    const uv = geoRef.current.attributes.uv;
    const count = position.count;
    
    for (let i = 0; i < count; i++) {
      const u = uv.getX(i);
      const v = uv.getY(i);
      
      const baseX = (u - 0.5) * 45; // Length of ribbon
      const baseY = (v - 0.5) * 6;  // Width of ribbon
      
      const uPi3Time = u * Math.PI * 3 - time * 1.5;
      
      // Wave mathematics to simulate a smooth, snaking silk ribbon
      const waveZ = Math.sin(uPi3Time) * 5;
      const waveY = Math.cos(u * Math.PI * 2 - time * 1.2) * 4;
      
      // Twist effect: rotating the cross-section
      const twist = Math.cos(uPi3Time);
      const cosTwist = Math.cos(twist);
      const sinTwist = Math.sin(twist);
      
      const twistY = baseY * cosTwist;
      const twistZ = baseY * sinTwist + waveZ * cosTwist;
      
      position.setXYZ(i, baseX, waveY + twistY, twistZ);
    }
    
    position.needsUpdate = true;
    geoRef.current.computeVertexNormals(); // Recalculate lighting for the sharp silk look
  });

  if (!flagTexture) return null;

  return (
    <Float speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
      <mesh ref={meshRef} position={[0, 0, -8]} rotation={[0, 0, Math.PI / 12]}>
        {/* Optimized resolution plane for smooth curves with minimal performance impact */}
        <planeGeometry ref={geoRef} args={[45, 6, 64, 8]} />
        <meshPhysicalMaterial 
          map={flagTexture} 
          side={THREE.DoubleSide} 
          roughness={0.1} 
          metalness={0.2}
          clearcoat={0.3}
          clearcoatRoughness={0.1}
          transparent
          opacity={0.9} // Vivid but slightly transparent so it blends behind the template
        />
      </mesh>
    </Float>
  );
}

export function RibbonBackground() {
  return (
    <Canvas 
      camera={{ position: [0, 0, 15], fov: 45 }} 
      gl={{ alpha: true, powerPreference: "high-performance" }}
      dpr={[1, 1.5]}
      style={{ pointerEvents: 'none', transform: "translate3d(0, 0, 0)", backfaceVisibility: "hidden" }}
    >
      <ambientLight intensity={1.5} />
      <directionalLight position={[10, 20, 15]} intensity={2.5} />
      <directionalLight position={[-10, -10, -10]} intensity={1} color="#ffffff" />
      <Suspense fallback={null}>
        {/* Environment map gives the silk ribbon beautiful glossy reflections */}
        <Environment preset="city" />
        <ContinuousRibbon />
      </Suspense>
    </Canvas>
  );
}
