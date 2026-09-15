"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import type { SynchronizedVisualHop } from "@/lib/mark-presentation";

export interface RTRJourneySyncState {
  activeHopIndex: number;
  activeHop: SynchronizedVisualHop | null;
  cometProgress: number; // 0 to 1 along bezier wire between active and next
  isCometActive: boolean;
  isPaused: boolean;
  seekToHop: (hopNumber: number) => void;
  togglePlayPause: () => void;
}

export function useRTRJourneySync(
  hops: SynchronizedVisualHop[],
  audioDurationMs = 24000,
  isPlaying = true
): RTRJourneySyncState {
  const [activeHopIndex, setActiveHopIndex] = useState<number>(0);
  const [cometProgress, setCometProgress] = useState<number>(0);
  const [isCometActive, setIsCometActive] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(!isPlaying);

  const startTimeRef = useRef<number | null>(null);
  const pausedTimeRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);

  const seekToHop = useCallback(
    (hopNumber: number) => {
      const targetIndex = hops.findIndex((h) => h.hop_number === hopNumber);
      if (targetIndex !== -1) {
        setActiveHopIndex(targetIndex);
        const targetOffset = hops[targetIndex].cue_start_offset_ms;
        startTimeRef.current = performance.now() - targetOffset;
        setCometProgress(0);
        setIsCometActive(false);
      }
    },
    [hops]
  );

  const togglePlayPause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  useEffect(() => {
    if (!hops.length || isPaused) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      return;
    }

    if (startTimeRef.current === null) {
      startTimeRef.current = performance.now();
    }

    const onFrame = (now: number) => {
      const elapsed = now - (startTimeRef.current ?? now);

      // Find which hop corresponds to current elapsed time
      let currentIdx = 0;
      for (let i = 0; i < hops.length; i++) {
        if (elapsed >= hops[i].cue_start_offset_ms) {
          currentIdx = i;
        } else {
          break;
        }
      }

      setActiveHopIndex(currentIdx);

      // Check if we are in the inter-hop pause window (when the photon comet glides)
      const currentHop = hops[currentIdx];
      const nextHop = hops[currentIdx + 1];

      if (nextHop) {
        const pauseStart = nextHop.cue_start_offset_ms - currentHop.pause_duration_ms;
        if (elapsed >= pauseStart && elapsed < nextHop.cue_start_offset_ms) {
          setIsCometActive(true);
          const ratio = (elapsed - pauseStart) / currentHop.pause_duration_ms;
          setCometProgress(Math.min(Math.max(ratio, 0), 1));
        } else {
          setIsCometActive(false);
          setCometProgress(0);
        }
      } else {
        setIsCometActive(false);
        setCometProgress(0);
      }

      if (elapsed < audioDurationMs) {
        animationFrameRef.current = requestAnimationFrame(onFrame);
      }
    };

    animationFrameRef.current = requestAnimationFrame(onFrame);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [hops, audioDurationMs, isPaused]);

  return {
    activeHopIndex,
    activeHop: hops[activeHopIndex] ?? null,
    cometProgress,
    isCometActive,
    isPaused,
    seekToHop,
    togglePlayPause,
  };
}
