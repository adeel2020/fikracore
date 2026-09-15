"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export function ThreeNeuralSphere({
  width = 110,
  height = 110,
}: {
  width?: number;
  height?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 50);
    camera.position.set(0, 0, 3.2);

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    // Generate 3D Neural Sphere Nodes & Lattice
    const nodeCount = 65;
    const positions: number[] = [];
    const colors: number[] = [];
    const vectors: THREE.Vector3[] = [];

    const cyanColor = new THREE.Color(0x00e5ff);
    const blueColor = new THREE.Color(0x0969ff);
    const purpleColor = new THREE.Color(0x8b5cf6);

    const phi = Math.PI * (3 - Math.sqrt(5)); // Golden spiral angle

    for (let i = 0; i < nodeCount; i++) {
      const y = 1 - (i / (nodeCount - 1)) * 2; // y goes from 1 to -1
      const radius = Math.sqrt(1 - y * y); // radius at y
      const theta = phi * i;

      const x = Math.cos(theta) * radius;
      const z = Math.sin(theta) * radius;

      // Organic variation
      const scale = 0.95 + (Math.random() - 0.5) * 0.15;
      const v = new THREE.Vector3(x * scale, y * scale, z * scale);
      positions.push(v.x, v.y, v.z);
      vectors.push(v);

      const colorMix = new THREE.Color();
      if (y > 0.3) colorMix.lerpColors(cyanColor, blueColor, Math.random());
      else colorMix.lerpColors(blueColor, purpleColor, Math.random());
      colors.push(colorMix.r, colorMix.g, colorMix.b);
    }

    const pointsGeo = new THREE.BufferGeometry();
    pointsGeo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    pointsGeo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

    const pointsMat = new THREE.PointsMaterial({
      size: 0.12,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
    });
    const pointsMesh = new THREE.Points(pointsGeo, pointsMat);
    group.add(pointsMesh);

    // Lattice Lines
    const linePositions: number[] = [];
    const lineColors: number[] = [];

    for (let i = 0; i < vectors.length; i++) {
      for (let j = i + 1; j < vectors.length; j++) {
        const dist = vectors[i].distanceTo(vectors[j]);
        if (dist < 0.65) {
          linePositions.push(vectors[i].x, vectors[i].y, vectors[i].z);
          linePositions.push(vectors[j].x, vectors[j].y, vectors[j].z);

          const alpha = 1 - dist / 0.65;
          lineColors.push(cyanColor.r * alpha, cyanColor.g * alpha, cyanColor.b * alpha);
          lineColors.push(blueColor.r * alpha, blueColor.g * alpha, blueColor.b * alpha);
        }
      }
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    lineGeo.setAttribute("color", new THREE.Float32BufferAttribute(lineColors, 3));

    const lineMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending,
    });
    const lineMesh = new THREE.LineSegments(lineGeo, lineMat);
    group.add(lineMesh);

    // Animation Loop
    let animationFrameId: number;
    let clock = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      clock += 0.016;

      group.rotation.y = clock * 0.45;
      group.rotation.x = Math.sin(clock * 0.6) * 0.2;

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      pointsGeo.dispose();
      pointsMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [width, height]);

  return <div ref={containerRef} style={{ width, height }} className="select-none pointer-events-none" />;
}
