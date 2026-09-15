"use client";

import React from "react";

export function OrbitalLinks() {
  return (
    <svg
      viewBox="0 0 1000 720"
      className="absolute inset-0 w-full h-full pointer-events-none z-10"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="linkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#0969ff" stopOpacity="0.6" />
        </linearGradient>

        <filter id="linkGlow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* 1. Link to Top: Correlation */}
      <path
        d="M 500 320 L 500 115"
        className="hud-link"
      />

      {/* 2. Link to Upper Left: FCSPS Lens */}
      <path
        d="M 440 330 Q 300 280 195 205"
        className="hud-link"
      />

      {/* 3. Link to Upper Right: Digital Assets */}
      <path
        d="M 560 330 Q 700 280 805 205"
        className="hud-link"
      />

      {/* 4. Link to Lower Left: Automation */}
      <path
        d="M 440 390 Q 320 440 225 495"
        className="hud-link"
      />

      {/* 5. Link to Lower Right: Predictions */}
      <path
        d="M 560 390 Q 680 440 775 495"
        className="hud-link"
      />

      {/* 6. Link to Bottom: Knowledge Core */}
      <path
        d="M 500 420 L 500 570"
        className="hud-link"
      />

      {/* Pulse Anchor Nodes */}
      <circle cx="500" cy="115" r="3.5" fill="#00c8ff" />
      <circle cx="195" cy="205" r="3.5" fill="#00c8ff" />
      <circle cx="805" cy="205" r="3.5" fill="#00c8ff" />
      <circle cx="225" cy="495" r="3.5" fill="#00c8ff" />
      <circle cx="775" cy="495" r="3.5" fill="#00c8ff" />
      <circle cx="500" cy="570" r="3.5" fill="#00c8ff" />
    </svg>
  );
}
