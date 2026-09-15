"use client";

import React from "react";
import { History, EyeOff } from "lucide-react";

export interface ZakiReplayBadgeProps {
  position?: number;
  totalStages?: number;
}

export function ZakiReplayBadge({
  position = 0,
  totalStages = 5,
}: ZakiReplayBadgeProps) {
  return (
    <div
      className="mx-3 my-1.5 px-2.5 py-1.5 rounded-md bg-purple-950/30 border border-purple-500/30 text-purple-200 flex items-center justify-between text-xs"
      data-testid="zaki-replay-badge"
    >
      <div className="flex items-center gap-1.5">
        <History className="w-3.5 h-3.5 text-purple-400" />
        <span className="font-semibold tracking-wide text-[11px] uppercase font-mono text-purple-300">
          Replay Mode (Step {position + 1}/{totalStages})
        </span>
      </div>

      <div className="flex items-center gap-1 text-[10px] font-mono text-purple-400/80">
        <EyeOff className="w-3 h-3" />
        <span>Zero Lookahead Enforced</span>
      </div>
    </div>
  );
}
