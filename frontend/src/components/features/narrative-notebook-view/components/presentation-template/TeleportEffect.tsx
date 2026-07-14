"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";

/**
 * TeleportEffect — Star Trek-style sci-fi materialization effect.
 * 
 * Uses a Canvas 2D particle system + CSS-driven holographic rings + volumetric
 * beam overlay. The effect plays when `isActive` is true and auto-dissolves
 * after the avatar has loaded (controlled via `onComplete`).
 */

interface TeleportEffectProps {
  isActive: boolean;
  /** "in" = materialize, "out" = dematerialize */
  mode?: "in" | "out";
  accentColor?: string;
  onComplete?: () => void;
  /** Reports materialization progress 0→1 (bottom→top body reveal) */
  onProgress?: (progress: number) => void;
  /** Duration in ms for the full materialization sequence */
  duration?: number;
  offsetX?: number;
}

// ─── Sci-fi glyph alphabet for the ring inscriptions ──────────────
const GLYPHS = "ΔΩΨΞΦΛΠΣζξφψωδ⊕⊗⊞⊟⌬⌲⍟◈◇⬡⬢⎔⏣⏥⏦⏧⟐⟡⟢⟣⧫⧬⬟⬠";

// ─── Particle class ───────────────────────────────────────────────
class Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  size: number;
  brightness: number;
  type: "dust" | "sparkle" | "quantum";

  constructor(canvasW: number, canvasH: number, centerX: number, baseY: number, revealY?: number) {
    this.type = Math.random() < 0.3 ? "sparkle" : Math.random() < 0.5 ? "quantum" : "dust";
    
    // Particles spawn concentrated around the reveal edge
    const spread = canvasW * 0.3;
    this.x = centerX + (Math.random() - 0.5) * spread;
    
    if (revealY !== undefined) {
      // 70% of particles cluster tightly around the reveal edge
      // 30% scatter below it for trailing dust
      if (Math.random() < 0.7) {
        this.y = revealY + (Math.random() - 0.5) * canvasH * 0.08;
      } else {
        this.y = revealY + Math.random() * canvasH * 0.15;
      }
    } else {
      this.y = baseY - Math.random() * canvasH * 0.15;
    }
    
    this.vx = (Math.random() - 0.5) * 1.2;
    this.vy = -(0.3 + Math.random() * 2.0); // Rise upward
    this.maxLife = 40 + Math.random() * 80;
    this.life = this.maxLife;
    this.size = this.type === "sparkle" ? 1.5 + Math.random() * 3.5 : 0.5 + Math.random() * 2.5;
    this.brightness = 0.5 + Math.random() * 0.5;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.vx *= 0.98;
    this.vy *= 0.995;
    this.life--;
    // Slight horizontal drift
    this.vx += (Math.random() - 0.5) * 0.15;
  }

  get alpha() {
    const ratio = this.life / this.maxLife;
    if (ratio > 0.8) return ((1 - ratio) / 0.2) * this.brightness;
    return ratio * this.brightness;
  }

  get alive() {
    return this.life > 0;
  }
}

export default function TeleportEffect({
  isActive,
  mode = "in",
  accentColor = "#00E5FF",
  onComplete,
  onProgress,
  duration = 3500,
  offsetX = 0,
}: TeleportEffectProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const particlesRef = useRef<Particle[]>([]);
  const startTimeRef = useRef(0);
  const revealRef = useRef(0);
  const [phase, setPhase] = useState<"idle" | "materializing" | "dissolving" | "done">("idle");
  const [opacity, setOpacity] = useState(0);

  // Parse accent color to RGB
  const parseColor = useCallback((hex: string) => {
    const h = hex.replace("#", "");
    const r = parseInt(h.substring(0, 2), 16) || 0;
    const g = parseInt(h.substring(2, 4), 16) || 229;
    const b = parseInt(h.substring(4, 6), 16) || 255;
    return { r, g, b };
  }, []);

  // ─── Main canvas animation loop ────────────────────────────────
  const animate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Dynamically resize canvas drawing buffer to match parent container's layout dimensions (unscaled offsets)
    const parent = canvas.parentElement;
    if (parent) {
      const layoutW = parent.offsetWidth;
      const layoutH = parent.offsetHeight;
      if (layoutW > 0 && layoutH > 0) {
        const targetW = layoutW * Math.min(window.devicePixelRatio, 2);
        const targetH = layoutH * Math.min(window.devicePixelRatio, 2);
        if (canvas.width !== targetW || canvas.height !== targetH) {
          canvas.width = targetW;
          canvas.height = targetH;
        }
      }
    }

    const w = canvas.width;
    const h = canvas.height;
    if (w === 0 || h === 0) {
      // Defer animation frame if canvas is not styled/rendered yet
      animFrameRef.current = requestAnimationFrame(animate);
      return;
    }

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const centerX = (w / 2) + (offsetX * dpr);
    const baseY = h * 0.92;
    const elapsed = Date.now() - startTimeRef.current;
    const progress = Math.min(elapsed / duration, 1);
    const { r, g, b } = parseColor(accentColor);

    // ── Clear ──
    ctx.clearRect(0, 0, w, h);

    // ── Global effect opacity (fade in → hold → fade out) ──
    let effectAlpha: number;
    if (progress < 0.15) {
      effectAlpha = progress / 0.15; // Fade in
    } else if (progress < 0.7) {
      effectAlpha = 1; // Hold
    } else {
      effectAlpha = 1 - (progress - 0.7) / 0.3; // Fade out
    }
    effectAlpha = Math.max(0, Math.min(1, effectAlpha));

    // ── 2. Holographic rings ──
    if (effectAlpha > 0) {
      const ringCount = 5;
      const time = elapsed * 0.001;

      ctx.save();
      ctx.globalCompositeOperation = "screen";

      for (let i = 0; i < ringCount; i++) {
        let ringProgress = (progress * 3 + i * 0.2) % 1;
        // Materialize = downward rings. Dematerialize = upward rings.
        if (mode === "in") {
          ringProgress = 1 - ringProgress;
        }
        const ringY = baseY - ringProgress * h * 0.75;
        const ringRadiusX = w * 0.22 * (1 - ringProgress * 0.4);
        const ringRadiusY = ringRadiusX * 0.35;
        const rotation = time * (0.8 + i * 0.3) * (i % 2 === 0 ? 1 : -1);
        const ringAlpha = effectAlpha * (1 - ringProgress) * 0.8;

        if (ringAlpha <= 0) continue;

        ctx.save();
        ctx.translate(centerX, ringY);
        ctx.rotate(rotation * 0.1);

        // Outer glow ring (thinner)
        ctx.beginPath();
        ctx.ellipse(0, 0, ringRadiusX + 2, ringRadiusY + 2, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${ringAlpha * 0.25})`;
        ctx.lineWidth = 4;
        ctx.stroke();

        // Main ring (thinner)
        ctx.beginPath();
        ctx.ellipse(0, 0, ringRadiusX, ringRadiusY, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${ringAlpha * 0.8})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Inner ring
        ctx.beginPath();
        ctx.ellipse(0, 0, ringRadiusX * 0.92, ringRadiusY * 0.92, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${ringAlpha * 0.5})`;
        ctx.lineWidth = 1.0;
        ctx.stroke();

        // Sci-fi glyphs around the ring
        const glyphCount = 12 + i * 4;
        ctx.font = `${7 + i}px monospace`;
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${ringAlpha * 0.8})`;
        for (let j = 0; j < glyphCount; j++) {
          const angle = (j / glyphCount) * Math.PI * 2 + time * (0.5 + i * 0.2);
          const gx = Math.cos(angle) * ringRadiusX * 0.96;
          const gy = Math.sin(angle) * ringRadiusY * 0.96;
          const glyph = GLYPHS[(j + i * 7 + Math.floor(time * 2)) % GLYPHS.length];
          ctx.fillText(glyph, gx - 3, gy + 3);
        }

        // Rotating bright segment on the ring
        const segAngle = time * 2 + i;
        const segLen = 0.4;
        ctx.beginPath();
        ctx.ellipse(0, 0, ringRadiusX, ringRadiusY, 0, segAngle, segAngle + segLen);
        ctx.strokeStyle = `rgba(255, 255, 255, ${ringAlpha * 0.9})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        ctx.restore();
      }
      ctx.restore();
    }

    // ── 3. Particles — concentrated at the reveal edge ──
    // revealProgress: 0 = feet, 1 = top of head
    // Ease-in-out curve for a slow, dramatic build
    const rawReveal = Math.min(1, progress / 0.95); // reaches 1 at 95% of duration
    let revealProgress = rawReveal < 0.5
      ? 2 * rawReveal * rawReveal              // ease-in first half (slow start)
      : 1 - Math.pow(-2 * rawReveal + 2, 2) / 2; // ease-out second half
      
    // Invert progress if dematerializing (mode === "out")
    if (mode === "out") {
      revealProgress = 1 - revealProgress;
    }

    let revealY: number;
    if (mode === "in") {
      // Materialize: Mask sweeps DOWNWARD from head to feet.
      // revealProgress 0 -> 1 means revealY moves from Head (baseY - h*0.85) to Feet (baseY)
      revealY = (baseY - h * 0.85) + revealProgress * h * 0.85;
    } else {
      // Dematerialize: Mask sweeps UPWARD from feet to head.
      // revealProgress 1 -> 0 means revealY moves from Feet (baseY) to Head (baseY - h*0.85)
      revealY = baseY - (1 - revealProgress) * h * 0.85;
    }
    
    revealRef.current = revealProgress;
    onProgress?.(revealProgress);

    // Spawn particles at the reveal edge
    if (progress < 0.9) {
      const spawnRate = Math.floor(14 * effectAlpha);
      for (let i = 0; i < spawnRate; i++) {
        particlesRef.current.push(new Particle(w, h, centerX, baseY, revealY));
      }
    }

    // Update & draw particles
    ctx.save();
    ctx.globalCompositeOperation = "screen";
    particlesRef.current = particlesRef.current.filter((p) => {
      p.update();
      if (!p.alive) return false;

      const alpha = p.alpha * effectAlpha;
      if (alpha <= 0) return true;

      if (p.type === "sparkle") {
        // Diamond sparkle
        const flicker = 0.5 + Math.sin(Date.now() * 0.02 + p.x) * 0.5;
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha * flicker})`;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(Math.PI / 4);
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      } else if (p.type === "quantum") {
        // Tiny glowing circle with halo
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.15})`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 0.6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
        ctx.fill();
      } else {
        // Dust mote
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.7})`;
        ctx.fill();
      }

      return true;
    });
    ctx.restore();

    // ── 4. Ground glow / radial flash ──
    if (effectAlpha > 0) {
      const groundGrad = ctx.createRadialGradient(
        centerX, baseY, 0,
        centerX, baseY, w * 0.35
      );
      groundGrad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${0.35 * effectAlpha})`);
      groundGrad.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, ${0.08 * effectAlpha})`);
      groundGrad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

      ctx.save();
      ctx.globalCompositeOperation = "screen";
      ctx.fillStyle = groundGrad;
      ctx.fillRect(0, baseY - h * 0.15, w, h * 0.25);
      ctx.restore();
    }

    // ── 5. Top lens flare / energy burst ──
    if (progress < 0.3 && effectAlpha > 0) {
      const flareAlpha = (1 - progress / 0.3) * effectAlpha;
      const flareGrad = ctx.createRadialGradient(centerX, 0, 0, centerX, 0, w * 0.4);
      flareGrad.addColorStop(0, `rgba(255, 255, 255, ${0.6 * flareAlpha})`);
      flareGrad.addColorStop(0.3, `rgba(${r}, ${g}, ${b}, ${0.2 * flareAlpha})`);
      flareGrad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);

      ctx.save();
      ctx.globalCompositeOperation = "screen";
      ctx.fillStyle = flareGrad;
      ctx.fillRect(0, 0, w, h * 0.4);
      ctx.restore();
    }

    // ── Continue or finish ──
    if (progress >= 1) {
      setPhase("done");
      setOpacity(0);
      onProgress?.(mode === "out" ? 0 : 1);
      onComplete?.();
      return;
    }

    setOpacity(effectAlpha);
    animFrameRef.current = requestAnimationFrame(animate);
  }, [accentColor, duration, onComplete, onProgress, parseColor]);

  // ─── Start / stop lifecycle ─────────────────────────────────────
  useEffect(() => {
    if (!isActive) {
      setPhase("idle");
      setOpacity(0);
      particlesRef.current = [];
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    setPhase("materializing");
    startTimeRef.current = Date.now();
    particlesRef.current = [];



    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isActive, animate]);

  return (
    <div
      className={`absolute inset-0 pointer-events-none z-50 transition-opacity duration-300 ${(phase === "done" || phase === "idle") ? "opacity-0" : ""}`}
      style={{ opacity: (phase === "done" || phase === "idle") ? 0 : opacity }}
    >
      {/* Canvas particle / ring / beam layer */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ mixBlendMode: "screen" }}
      />

      {/* CSS holographic scan lines */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ opacity: opacity * 0.3 }}
      >
        <div
          className="absolute w-full"
          style={{
            height: "2px",
            background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
            animation: `${mode === "in" ? "scanDown" : "scanUp"} 1.2s linear infinite`,
            boxShadow: `0 0 20px 4px ${accentColor}40`,
          }}
        />
        <div
          className="absolute w-full"
          style={{
            height: "1px",
            background: `linear-gradient(90deg, transparent, ${accentColor}80, transparent)`,
            animation: `${mode === "in" ? "scanDown" : "scanUp"} 0.9s linear 0.4s infinite`,
          }}
        />
      </div>

      {/* Keyframe styles */}
      <style>{`
        @keyframes scanUp {
          0% { top: 100%; }
          100% { top: -2px; }
        }
        @keyframes scanDown {
          0% { top: -2px; }
          100% { top: 100%; }
        }
      `}</style>
    </div>
  );
}
