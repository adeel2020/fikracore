"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export function ThreeBrainCanvas({
  width = 240,
  height = 200,
  interactive = true,
}: {
  width?: number;
  height?: number;
  interactive?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 0.4, 4.2);

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // 2. Brain Root Group
    const brainGroup = new THREE.Group();
    scene.add(brainGroup);

    // 3. Generate Volumetric Anatomical Brain Point Cloud & Connections
    const pointCountPerHemisphere = 900;
    const positions: number[] = [];
    const colors: number[] = [];
    const sizes: number[] = [];
    const nodeVectors: THREE.Vector3[] = [];

    const cyanColor = new THREE.Color(0x00e5ff);
    const blueColor = new THREE.Color(0x0969ff);
    const purpleColor = new THREE.Color(0x8b5cf6);
    const whiteColor = new THREE.Color(0xffffff);

    // Anatomical 3D Brain shape generation formula
    const generateHemisphere = (isLeft: boolean) => {
      const sign = isLeft ? -1 : 1;
      let added = 0;

      while (added < pointCountPerHemisphere) {
        // Parametric coordinates
        const u = Math.random() * Math.PI; // 0 to PI
        const v = Math.random() * 2 * Math.PI; // 0 to 2PI
        const rad = 0.4 + Math.random() * 0.6; // volume depth

        // Ellipsoid base for brain hemisphere
        let x = sign * (0.16 + 0.68 * rad * Math.sin(u) * Math.cos(v));
        let y = 0.72 * rad * Math.cos(u);
        let z = 0.88 * rad * Math.sin(u) * Math.sin(v);

        // Flatten medial side (fissure)
        if (Math.abs(x) < 0.12) {
          x = sign * (0.12 + Math.abs(x) * 0.2);
        }

        // Taper frontal lobe (anterior) and occipital lobe (posterior)
        if (z > 0.4) {
          x *= 0.88;
          y *= 0.85;
        } else if (z < -0.4) {
          x *= 0.82;
          y *= 0.78;
        }

        // Add temporal lobe bulge
        if (y < -0.1 && z > -0.2 && z < 0.3) {
          x += sign * 0.18;
          y -= 0.1;
        }

        // Organic Gyri / Sulci convolutions (Brain folds)
        const gyri =
          Math.sin(x * 12) * Math.cos(y * 12) * 0.08 +
          Math.sin(z * 14 + y * 8) * 0.06 +
          Math.cos(x * 16 + z * 10) * 0.04;

        x += gyri * (x / 0.8);
        y += gyri * (y / 0.8);
        z += gyri * (z / 0.8);

        // Add point
        positions.push(x, y, z);
        nodeVectors.push(new THREE.Vector3(x, y, z));

        // Color based on height and depth
        const colorMix = new THREE.Color();
        const depth = Math.sqrt(x * x + y * y + z * z);
        if (depth > 0.85) {
          // Surface photon synapse (Cyan/Electric Blue)
          colorMix.lerpColors(cyanColor, whiteColor, Math.random() * 0.35);
          sizes.push(4.5 + Math.random() * 3.5);
        } else if (y > 0.1) {
          // Superior parietal / frontal lobe
          colorMix.lerpColors(cyanColor, blueColor, Math.random());
          sizes.push(3.0 + Math.random() * 2.0);
        } else {
          // Deep core & cerebellum
          colorMix.lerpColors(blueColor, purpleColor, Math.random() * 0.7);
          sizes.push(2.5 + Math.random() * 2.0);
        }

        colors.push(colorMix.r, colorMix.g, colorMix.b);
        added++;
      }
    };

    generateHemisphere(true); // Left
    generateHemisphere(false); // Right

    // 4. Create Points Geometry & Material
    const pointsGeometry = new THREE.BufferGeometry();
    pointsGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    pointsGeometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));

    // Glow dot texture
    const canvas = document.createElement("canvas");
    canvas.width = 64;
    canvas.height = 64;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
      gradient.addColorStop(0.3, "rgba(0, 229, 255, 0.9)");
      gradient.addColorStop(0.6, "rgba(9, 105, 255, 0.4)");
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 64, 64);
    }
    const particleTexture = new THREE.CanvasTexture(canvas);

    const pointsMaterial = new THREE.PointsMaterial({
      size: 0.11,
      vertexColors: true,
      map: particleTexture,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    const brainPoints = new THREE.Points(pointsGeometry, pointsMaterial);
    brainGroup.add(brainPoints);

    // 5. Neural Fiber Tracts (Interconnecting Axons)
    const linePositions: number[] = [];
    const lineColors: number[] = [];
    const maxConnections = 650;
    let connectionsCount = 0;

    for (let i = 0; i < nodeVectors.length && connectionsCount < maxConnections; i += 2) {
      const v1 = nodeVectors[i];
      // Find nearby nodes
      for (let j = i + 1; j < nodeVectors.length; j += 3) {
        const v2 = nodeVectors[j];
        const dist = v1.distanceTo(v2);

        // Connect if close enough, or cross-corpus callosum
        const isCorpusBridge = Math.abs(v1.x) < 0.22 && Math.abs(v2.x) < 0.22 && v1.x * v2.x < 0 && dist < 0.45;
        if ((dist > 0.08 && dist < 0.24) || isCorpusBridge) {
          linePositions.push(v1.x, v1.y, v1.z);
          linePositions.push(v2.x, v2.y, v2.z);

          const alpha = isCorpusBridge ? 0.9 : 0.4;
          const lineColor = isCorpusBridge ? cyanColor : blueColor;
          lineColors.push(lineColor.r * alpha, lineColor.g * alpha, lineColor.b * alpha);
          lineColors.push(lineColor.r * alpha, lineColor.g * alpha, lineColor.b * alpha);

          connectionsCount++;
        }
      }
    }

    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3));
    lineGeometry.setAttribute("color", new THREE.Float32BufferAttribute(lineColors, 3));

    const lineMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      opacity: 0.7,
    });

    const brainLines = new THREE.LineSegments(lineGeometry, lineMaterial);
    brainGroup.add(brainLines);

    // 6. Glowing Synaptic Core Flare
    const coreLight = new THREE.PointLight(0x00e5ff, 2.5, 4);
    coreLight.position.set(0, 0, 0);
    brainGroup.add(coreLight);

    const blueBackLight = new THREE.PointLight(0x0969ff, 1.8, 5);
    blueBackLight.position.set(0, -0.4, 0.8);
    brainGroup.add(blueBackLight);

    // 7. Ambient Hologram Gyro Rings
    const ringGeo = new THREE.TorusGeometry(1.3, 0.008, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
    });
    const gyroRing1 = new THREE.Mesh(ringGeo, ringMat);
    gyroRing1.rotation.x = Math.PI * 0.45;
    brainGroup.add(gyroRing1);

    const ringGeo2 = new THREE.TorusGeometry(1.45, 0.006, 16, 100);
    const ringMat2 = new THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
    });
    const gyroRing2 = new THREE.Mesh(ringGeo2, ringMat2);
    gyroRing2.rotation.x = -Math.PI * 0.35;
    gyroRing2.rotation.y = Math.PI * 0.2;
    brainGroup.add(gyroRing2);

    // 8. Animation & Interaction Loop
    let targetRotationY = 0;
    let targetRotationX = 0;
    let isDragging = false;
    let previousMouseX = 0;
    let previousMouseY = 0;

    const onPointerDown = (e: MouseEvent | TouchEvent) => {
      if (!interactive) return;
      isDragging = true;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
      previousMouseX = clientX;
      previousMouseY = clientY;
    };

    const onPointerMove = (e: MouseEvent | TouchEvent) => {
      if (!interactive) return;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

      if (isDragging) {
        const deltaX = clientX - previousMouseX;
        const deltaY = clientY - previousMouseY;
        targetRotationY += deltaX * 0.008;
        targetRotationX += deltaY * 0.008;
        previousMouseX = clientX;
        previousMouseY = clientY;
      }
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const domEl = renderer.domElement;
    domEl.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);

    let animationFrameId: number;
    let clock = 0;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      clock += 0.016;

      // Continuous organic rotation + floating
      brainGroup.rotation.y += (targetRotationY + clock * 0.35 - brainGroup.rotation.y) * 0.05;
      brainGroup.rotation.x += (targetRotationX + Math.sin(clock * 0.8) * 0.08 - brainGroup.rotation.x) * 0.05;
      brainGroup.position.y = Math.sin(clock * 1.5) * 0.06;

      // Gyro rings subtle differential spin
      gyroRing1.rotation.z = clock * 0.2;
      gyroRing2.rotation.z = -clock * 0.15;

      // Pulsing core light
      coreLight.intensity = 2.0 + Math.sin(clock * 3.5) * 0.8;

      renderer.render(scene, camera);
    };

    animate();

    // 9. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      domEl.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);

      pointsGeometry.dispose();
      pointsMaterial.dispose();
      lineGeometry.dispose();
      lineMaterial.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      ringGeo2.dispose();
      ringMat2.dispose();
      particleTexture.dispose();
      renderer.dispose();

      if (container.contains(domEl)) {
        container.removeChild(domEl);
      }
    };
  }, [width, height, interactive]);

  return (
    <div
      ref={containerRef}
      className="relative flex items-center justify-center cursor-grab active:cursor-grabbing select-none"
      style={{ width, height }}
    />
  );
}
