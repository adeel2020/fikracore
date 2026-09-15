"use client";

import React from "react";

export function BrainGlow() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-center">
      {/* Primary Cyan/Blue Core Flare */}
      <div
        className="absolute w-[440px] h-[440px] rounded-full"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(0, 200, 255, 0.22) 0%, rgba(9, 105, 255, 0.14) 40%, rgba(139, 92, 246, 0.06) 65%, transparent 80%)",
          filter: "blur(28px)",
        }}
      />

      {/* Secondary Soft Ambient Aura */}
      <div
        className="absolute w-[620px] h-[620px] rounded-full"
        style={{
          background:
            "radial-gradient(circle at 50% 50%, rgba(219, 234, 254, 0.45) 0%, rgba(239, 246, 255, 0.25) 50%, transparent 75%)",
          filter: "blur(40px)",
        }}
      />

      {/* Inner Horizon Floor Ellipse */}
      <div
        className="absolute top-[54%] w-[580px] h-[160px] rounded-[100%]"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(6, 182, 212, 0.22) 0%, rgba(37, 99, 235, 0.12) 50%, transparent 70%)",
          filter: "blur(18px)",
          transform: "translateY(-50%)",
        }}
      />
    </div>
  );
}
