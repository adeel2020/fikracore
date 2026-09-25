"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Pause,
  Square,
  Volume2,
  VolumeX,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { jarvisVoice } from "@/lib/voice";

interface MarkVoiceNarratorProps {
  spokenText: string;
  className?: string;
  autoPlay?: boolean;
}

export function MarkVoiceNarrator({
  spokenText,
  className,
  autoPlay = false,
}: MarkVoiceNarratorProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);

  const sentences = React.useMemo(() => {
    if (!spokenText) return [];
    return spokenText
      .split(/(?<=[.?!])\s+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }, [spokenText]);

  useEffect(() => {
    setIsMuted(jarvisVoice.getIsMuted());

    const timer = setInterval(() => {
      const speaking = jarvisVoice.getIsSpeaking();
      const paused = jarvisVoice.getIsPaused();
      setIsPlaying(speaking);
      setIsPaused(paused);
    }, 200);

    return () => clearInterval(timer);
  }, []);

  const handlePlay = () => {
    if (isPaused) {
      jarvisVoice.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    jarvisVoice.speak(spokenText, {
      onStart: () => {
        setIsPlaying(true);
        setIsPaused(false);
      },
      onEnd: () => {
        setIsPlaying(false);
        setIsPaused(false);
        setCurrentSentenceIndex(0);
      },
      onError: () => {
        setIsPlaying(false);
        setIsPaused(false);
      },
    });
  };

  const handlePause = () => {
    jarvisVoice.pause();
    setIsPaused(true);
    setIsPlaying(false);
  };

  const handleStop = () => {
    jarvisVoice.stop();
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentSentenceIndex(0);
  };

  const handleRepeat = () => {
    handleStop();
    handlePlay();
  };

  const toggleMute = () => {
    const next = !isMuted;
    setIsMuted(next);
    jarvisVoice.setMuted(next);
  };

  return (
    <div
      className={cn(
        "rounded-2xl border border-cyan-500/20 bg-slate-950/80 p-3 shadow-lg backdrop-blur-md transition-all text-xs",
        className
      )}
    >
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "h-6 w-6 rounded-lg border flex items-center justify-center transition-all",
              isPlaying
                ? "border-cyan-400 bg-cyan-500/20 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.4)]"
                : "border-white/10 bg-white/5 text-neutral-400"
            )}
          >
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <span className="font-semibold text-white tracking-wide">MARK Voice Narrator</span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1.5">
          {isPlaying && !isPaused ? (
            <button
              type="button"
              onClick={handlePause}
              title="Pause"
              className="p-1.5 rounded-lg bg-white/5 text-neutral-300 hover:text-white border border-white/10 hover:bg-white/10 transition cursor-pointer"
            >
              <Pause className="h-3.5 w-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handlePlay}
              title="Play Narration"
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 transition text-[11px] cursor-pointer"
            >
              <Play className="h-3 w-3 fill-current" />
              <span>{isPaused ? "Resume" : "Play"}</span>
            </button>
          )}

          {(isPlaying || isPaused) && (
            <button
              type="button"
              onClick={handleStop}
              title="Stop"
              className="p-1.5 rounded-lg bg-white/5 text-neutral-300 hover:text-white border border-white/10 hover:bg-white/10 transition cursor-pointer"
            >
              <Square className="h-3.5 w-3.5" />
            </button>
          )}

          <button
            type="button"
            onClick={handleRepeat}
            title="Repeat"
            className="p-1.5 rounded-lg bg-white/5 text-neutral-300 hover:text-white border border-white/10 hover:bg-white/10 transition cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>

          <button
            type="button"
            onClick={toggleMute}
            title={isMuted ? "Unmute" : "Mute"}
            className={cn(
              "p-1.5 rounded-lg transition border cursor-pointer",
              isMuted
                ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                : "bg-white/5 text-neutral-300 hover:text-white border-white/10"
            )}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Spoken Text Preview */}
      <p className="text-neutral-300 leading-relaxed text-xs italic">
        &ldquo;{spokenText}&rdquo;
      </p>
    </div>
  );
}

export default MarkVoiceNarrator;
