"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  getCapabilityNode,
  getEngineNodes,
  getTelecomServiceNodes,
  type MarkCapabilityNode,
  type MarkRouteTrace,
  type MarkVisualState,
} from "@/lib/mark-capability-graph";
import { MarkCapabilityPanel } from "./MarkCapabilityPanel";
import { MarkHeroOrb } from "./MarkHeroOrb";
import { MarkOverviewPanel } from "./MarkOverviewPanel";
import { MarkReasoningWeb } from "./MarkReasoningWeb";
import { MarkShaderBackground } from "./MarkShaderBackground";
import { MarkStatusBar } from "./MarkStatusBar";
import { useMarkHud } from "@/lib/mark-hud-context";
import "./mark-orb.css";

function toVisualState(state?: MarkVisualState | null): MarkVisualState {
  return state ?? "idle";
}

export function MarkCognitiveWorld({
  state,
  trace,
  selectedNodeId,
  onSelectNode,
  onRunAction,
}: {
  state?: MarkVisualState | null;
  trace?: MarkRouteTrace | null;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string) => void;
  onRunAction?: (query: string) => void;
}) {
  const visualState = toVisualState(state);
  const [localSelected, setLocalSelected] = useState<string | null>(null);
  const [telecomExpanded, setTelecomExpanded] = useState(true);
  const [reduced, setReduced] = useState(false);
  const wakeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [tapState, setTapState] = useState<MarkVisualState | null>(null);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReduced(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  useEffect(() => () => {
    if (wakeTimer.current) clearTimeout(wakeTimer.current);
  }, []);

  const selected = selectedNodeId ?? localSelected ?? null;
  const highlighted = selected ?? trace?.activeServiceIds?.[0] ?? trace?.activeEngineId ?? null;
  const panelNode = getCapabilityNode(selected);
  const { settings } = useMarkHud();
  const renderedState = settings.stateOverride !== "auto" ? settings.stateOverride : (tapState ?? visualState);
  const effectiveTrace = useMemo<MarkRouteTrace>(() => {
    if (trace) return { ...trace, state: renderedState };
    return {
      state: renderedState,
      activeEngineId: highlighted && getCapabilityNode(highlighted)?.kind === "engine" ? highlighted : "telecom_brain",
      activeServiceIds: highlighted && getCapabilityNode(highlighted)?.kind === "service" ? [highlighted] : undefined,
      activeConnectorIds: highlighted ? getCapabilityNode(highlighted)?.connectors?.slice(0, 2) : ["gbrain"],
      activeNamespaces: highlighted ? getCapabilityNode(highlighted)?.namespaces?.slice(0, 2) : ["semantic graph"],
    };
  }, [highlighted, renderedState, trace]);

  const allSelectableNodes = [...getEngineNodes(), ...(telecomExpanded ? getTelecomServiceNodes() : [])];

  const handleSelect = (node: MarkCapabilityNode) => {
    setLocalSelected(node.id);
    if (node.id === "telecom_brain") setTelecomExpanded((value) => !value);
    onSelectNode?.(node.id);
  };

  const activateCore = () => {
    const next: MarkVisualState = renderedState === "idle" ? "listening" : renderedState === "listening" ? "processing" : renderedState === "processing" ? "speaking" : "idle";
    setTapState(next);
    if (wakeTimer.current) clearTimeout(wakeTimer.current);
    wakeTimer.current = setTimeout(() => setTapState(null), 4500);
  };

  return (
    <div data-testid="mark-cognitive-world" className="relative h-full min-h-[520px] w-full overflow-hidden text-slate-100">
      {!reduced && settings.showWaves && (
        <div aria-hidden="true" className="absolute inset-0 z-0">
          <MarkShaderBackground
            opacity={settings.waveOpacity}
            speedMultiplier={settings.waveSpeed}
            voiceActive={renderedState === "speaking" || renderedState === "processing" || renderedState === "investigating"}
            gold={renderedState === "learning" || renderedState === "waiting_for_approval"}
          />
        </div>
      )}
      <div
        aria-hidden="true"
        className="absolute inset-0 z-[1] pointer-events-none"
        style={{
          mixBlendMode: "screen",
          background: `radial-gradient(circle at 50% 48%, rgba(13,210,255,${
            renderedState === "speaking" ? 0.32 : renderedState === "processing" || renderedState === "investigating" ? 0.24 : 0.16
          }) 0%, rgba(13,170,228,0.08) 30%, rgba(8,17,31,0) 64%)`,
          transition: "background 0.6s ease",
        }}
      />

      <MarkOverviewPanel state={renderedState} trace={effectiveTrace} />

      <div className="absolute inset-0 z-[10] pointer-events-none">
        <MarkReasoningWeb
          state={renderedState}
          trace={effectiveTrace}
          selectedNodeId={selected}
          telecomExpanded={telecomExpanded}
          onSelectNode={handleSelect}
        />
      </div>

      {/* 3D Orb and Holographic Rings - Permanently Centered */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
          zIndex: 3,
        }}
      >
        <div
          style={{
            position: "relative",
            width: "min(780px, 78vw)",
            height: "min(680px, 80vh)",
            transform: `scale(${settings.orbScale ?? 1})`,
            transformOrigin: "center center",
            transition: "transform 300ms ease",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <MarkHeroOrb state={renderedState} />
        </div>
      </div>

      {/* Central Wake Core Trigger */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          pointerEvents: "none",
          zIndex: 4,
        }}
      >
        <button
          type="button"
          aria-label="Wake Mark core"
          onClick={activateCore}
          style={{
            width: 96,
            height: 96,
            borderRadius: "50%",
            backgroundColor: "transparent",
            cursor: "pointer",
            pointerEvents: "auto",
            border: "none",
          }}
        />
      </div>

      <nav className="sr-only" aria-label="Mark capability graph">
        <ul>
          {allSelectableNodes.map((node) => (
            <li key={node.id}>
              <button type="button" onClick={() => handleSelect(node)}>
                {node.label}: {node.role}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <MarkStatusBar state={renderedState} trace={effectiveTrace} />

      {panelNode && (
        <MarkCapabilityPanel
          node={panelNode}
          onClose={() => {
            setLocalSelected(null);
            onSelectNode?.("");
          }}
          onRunAction={onRunAction}
        />
      )}
    </div>
  );
}
