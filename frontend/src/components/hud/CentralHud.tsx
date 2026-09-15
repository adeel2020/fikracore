"use client";

import React from "react";
import {
  Workflow,
  Eye,
  Database,
  Bot,
  TrendingUp,
  BookOpen,
} from "lucide-react";
import { BrainGlow } from "./BrainGlow";
import { HudRing } from "./HudRing";
import { TelecomBrain } from "./TelecomBrain";
import { HudOrb } from "./HudOrb";
import { OrbitalLinks } from "./OrbitalLinks";

interface CentralHudProps {
  selectedOrb?: string | null;
  onSelectOrb?: (orbId: string) => void;
}

export function CentralHud({ selectedOrb, onSelectOrb }: CentralHudProps) {
  return (
    <div className="relative w-full h-full min-h-0 max-h-[580px] flex items-center justify-center select-none">
      {/* 1. Ambient Holographic Background Glow */}
      <BrainGlow />

      {/* 2. Outer Orbital Planes & Rings */}
      <HudRing
        size="min(560px, 92%)"
        variant="outer-orbit"
        speed="slow"
        className="opacity-75"
      />

      <HudRing
        size="min(480px, 80%)"
        variant="ticks"
        speed="slow"
        reverse
        className="opacity-60"
      />

      {/* 3. Primary Rotating HUD Ring 01 (Clockwise) */}
      <HudRing
        size="min(420px, 70%)"
        variant="tech"
        speed="medium"
        className="opacity-80"
      />

      {/* 4. Secondary Rotating HUD Ring 02 (Counter-Clockwise) */}
      <HudRing
        size="min(340px, 58%)"
        variant="dashed"
        speed="medium"
        reverse
        className="opacity-70"
      />

      {/* 5. Concentric Inner Radar Guides */}
      <HudRing
        size="min(270px, 46%)"
        variant="concentric"
        className="opacity-50"
      />

      {/* 6. SVG Dynamic Connector Links */}
      <OrbitalLinks />

      {/* 7. Central Telecom Brain (Floating in the center) */}
      <div className="absolute z-20 flex items-center justify-center">
        <TelecomBrain />
      </div>

      {/* 8. Six Orbital Floating Hologram Modules */}
      {/* 1. CORRELATION (Top) */}
      <HudOrb
        id="correlation"
        label="CORRELATION"
        icon={Workflow}
        positionStyle={{ top: "3%", left: "calc(50% - 52px)" }}
        floatClass="hud-float-1"
        isActive={selectedOrb === "correlation"}
        onClick={() => onSelectOrb?.("correlation")}
      />

      {/* 2. FCSPS LENS (Upper Left) */}
      <HudOrb
        id="fcsps"
        label="FCSPS LENS"
        icon={Eye}
        positionStyle={{ top: "19%", left: "9%" }}
        floatClass="hud-float-2"
        isActive={selectedOrb === "fcsps"}
        onClick={() => onSelectOrb?.("fcsps")}
      />

      {/* 3. DIGITAL ASSETS (Upper Right) */}
      <HudOrb
        id="digital-assets"
        label="DIGITAL ASSETS"
        icon={Database}
        positionStyle={{ top: "19%", right: "9%" }}
        floatClass="hud-float-3"
        isActive={selectedOrb === "digital-assets"}
        onClick={() => onSelectOrb?.("digital-assets")}
      />

      {/* 4. AUTOMATION (Lower Left) */}
      <HudOrb
        id="automation"
        label="AUTOMATION"
        icon={Bot}
        positionStyle={{ bottom: "18%", left: "13%" }}
        floatClass="hud-float-4"
        isActive={selectedOrb === "automation"}
        onClick={() => onSelectOrb?.("automation")}
      />

      {/* 5. PREDICTIONS (Lower Right) */}
      <HudOrb
        id="predictions"
        label="PREDICTIONS"
        icon={TrendingUp}
        positionStyle={{ bottom: "18%", right: "13%" }}
        floatClass="hud-float-5"
        isActive={selectedOrb === "predictions"}
        onClick={() => onSelectOrb?.("predictions")}
      />

      {/* 6. KNOWLEDGE CORE (Bottom) */}
      <HudOrb
        id="knowledge"
        label="KNOWLEDGE CORE"
        icon={BookOpen}
        positionStyle={{ bottom: "3%", left: "calc(50% - 52px)" }}
        floatClass="hud-float-6"
        isActive={selectedOrb === "knowledge"}
        onClick={() => onSelectOrb?.("knowledge")}
      />
    </div>
  );
}
