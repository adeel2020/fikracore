"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import type { MarkVisualState } from "@/lib/mark-capability-graph";
import { MarkCyanDust } from "./MarkCyanDust";
import { MarkOrb } from "./MarkOrb";
import "./mark-orb.css";

const MarkCore3D = dynamic(() => import("./MarkCore3D").then((mod) => mod.MarkCore3D), { ssr: false });

const STAGE_WIDTH = 900;
const STAGE_HEIGHT = 900;

export function MarkHeroOrb({
  state,
  interactive = false,
  onActivate,
}: {
  state: MarkVisualState;
  interactive?: boolean;
  onActivate?: () => void;
}) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.6);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReducedMotion(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;

    const measure = () => {
      setScale(Math.min(1.65, el.clientWidth / 500, el.clientHeight / 480));
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={boxRef}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      aria-label={interactive ? "Mark core" : undefined}
      aria-hidden={interactive ? undefined : true}
      onClick={interactive ? onActivate : undefined}
      onKeyDown={
        interactive
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onActivate?.();
              }
            }
          : undefined
      }
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        cursor: interactive ? "pointer" : "default",
        borderRadius: "50%",
        userSelect: "none",
      }}
    >
      <div
        data-mark-stage
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: STAGE_WIDTH,
          height: STAGE_HEIGHT,
          transform: `translate(-50%, -50%) scale(${scale})`,
          transformOrigin: "center center",
        }}
      >
        <div style={{ position: "absolute", left: 0, top: (STAGE_HEIGHT - 520) / 2, pointerEvents: "none" }}>
          <MarkOrb state={state} variant="frame" />
        </div>
        <MarkCyanDust state={state} />
        {!reducedMotion && <MarkCore3D state={state} />}
      </div>
    </div>
  );
}
