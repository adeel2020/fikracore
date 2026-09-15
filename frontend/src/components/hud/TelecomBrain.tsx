"use client";

import React, { useState } from "react";
import Image from "next/image";

export function TelecomBrain() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div className="relative z-20 flex flex-col items-center select-none">
      {/* 3D Glass Platform Pedestal */}
      <div className="relative flex items-center justify-center">
        {/* Under-Platform Shadows & Floor Glows */}
        <div className="absolute -bottom-10 w-[280px] h-[52px] rounded-[100%] bg-cyan-400/40 blur-2xl pointer-events-none animate-pulse" />
        <div className="absolute -bottom-5 w-[220px] h-[34px] rounded-[100%] bg-[#0a66ff]/35 blur-lg pointer-events-none" />

        {/* Outer Circular Hologram Glass Stage */}
        <div
          className={`relative w-[220px] h-[220px] sm:w-[250px] sm:h-[250px] rounded-full backdrop-blur-2xl border flex items-center justify-center transition-transform duration-500 ease-out bg-white/75 dark:bg-slate-950/80 border-blue-200/90 dark:border-cyan-500/40 shadow-[0_28px_80px_rgba(37,99,235,0.25)] dark:shadow-[0_0_60px_rgba(0,229,255,0.35),inset_0_0_40px_rgba(14,165,233,0.3)] ${
            isHovered ? "scale-105" : ""
          }`}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {/* Inner concentric technical gyro rings */}
          <div className="absolute inset-2 rounded-full border border-cyan-300/60 dark:border-cyan-400/40 pointer-events-none" />
          <div className="absolute inset-5 rounded-full border border-dashed border-blue-400/70 dark:border-cyan-300/50 hud-spin-slow pointer-events-none" />
          <div className="absolute inset-9 rounded-full border border-blue-200/80 dark:border-cyan-500/30 pointer-events-none" />

          {/* Central Radial Light Aura */}
          <div className="absolute w-[190px] h-[190px] rounded-full bg-[radial-gradient(circle_at_50%_45%,rgba(0,229,255,0.45)_0%,rgba(9,105,255,0.25)_45%,transparent_75%)] blur-md pointer-events-none" />

          {/* EXACT 3D Volumetric Holographic Glowing Brain */}
          <div className="relative z-10 w-[195px] h-[145px] sm:w-[220px] sm:h-[160px] flex items-center justify-center animate-float pointer-events-none">
            <Image
              src="/images/jarvis-3d-brain.png"
              alt="JARVIS 3D Holographic Telecom Brain"
              width={260}
              height={190}
              priority
              className="w-full h-full object-contain filter drop-shadow-[0_0_24px_rgba(0,229,255,0.85)] drop-shadow-[0_12px_32px_rgba(9,105,255,0.6)] transition-transform duration-500 hover:scale-105"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
