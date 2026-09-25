"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Mic,
  MicOff,
  RotateCcw,
  Pause,
  Play,
  Square,
  Volume2,
  VolumeX,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { jarvisVoice, type VoiceState } from "@/lib/voice";
import { API_BASE } from "@/lib/api/config";

export interface ZakiSpeechVisualizerProps {
  runId?: string;
  className?: string;
  onTranscript?: (text: string) => void;
  onResponse?: (answer: string, spoken?: string) => void;
  onMessageSubmit?: (text: string) => Promise<string | void>;
}

export function ZakiSpeechVisualizer({
  runId,
  className,
  onTranscript,
  onResponse,
  onMessageSubmit,
}: ZakiSpeechVisualizerProps) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isLiveMode, setIsLiveMode] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const animFrameRef = useRef<number | null>(null);

  // Sync state from jarvisVoice singleton
  useEffect(() => {
    setIsMuted(jarvisVoice.getIsMuted());

    const timer = setInterval(() => {
      const speaking = jarvisVoice.getIsSpeaking();
      const paused = jarvisVoice.getIsPaused();
      const live = jarvisVoice.getIsLiveMode();

      setIsSpeaking(speaking);
      setIsPaused(paused);
      setIsLiveMode(live);

      if (speaking) {
        setVoiceState("speaking");
      } else if (live) {
        setVoiceState("listening");
      } else {
        setVoiceState("idle");
      }
    }, 150);

    return () => clearInterval(timer);
  }, []);

  // Audio animation generator when speaking or listening
  useEffect(() => {
    let phase = 0;
    const updateLevels = () => {
      phase += 0.12;
      if (isSpeaking && !isPaused) {
        // Natural speech modulation wave
        const base = Math.sin(phase) * 0.4 + 0.6;
        const jitter = Math.sin(phase * 2.7) * 0.2 + Math.cos(phase * 4.3) * 0.15;
        setAudioLevel(Math.max(0.15, Math.min(1.0, base + jitter)));
      } else if (voiceState === "listening") {
        // Subtle ambient listening pulse
        const ambient = Math.sin(phase * 0.8) * 0.25 + 0.35;
        setAudioLevel(ambient);
      } else {
        setAudioLevel(0);
      }
      animFrameRef.current = requestAnimationFrame(updateLevels);
    };

    animFrameRef.current = requestAnimationFrame(updateLevels);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isSpeaking, isPaused, voiceState]);

  const toggleVoiceMode = () => {
    jarvisVoice.prime();
    if (isLiveMode) {
      jarvisVoice.stopLiveMode();
      setIsLiveMode(false);
      setVoiceState("idle");
      setIsSpeaking(false);
    } else {
      setIsLiveMode(true);
      setVoiceState("listening");
      jarvisVoice.startLiveMode(
        {
          onStateChange: (state) => {
            setVoiceState(state);
            setIsSpeaking(state === "speaking");
          },
          onTranscript: (t) => onTranscript?.(t),
          onResponse: (a, s) => {
            onResponse?.(a, s);
          },
          onMessageSubmit: async (text: string) => {
            if (onMessageSubmit) {
              const res = await onMessageSubmit(text);
              if (res) return res;
            }
            try {
              const payload = {
                query: text,
                message: text,
                run_id: runId,
                scenario_id: runId || "SCN-001",
                workspace: "investigate",
                response_level: "engineer",
              };
              const res = await fetch(`${API_BASE}/api/v1/fikracore/zaki/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              if (!res.ok) return "Backend communication error.";
              const data = await res.json();
              const reply =
                data.zaki_v2?.storyteller?.spoken_answer ||
                data.zaki_v2?.storyteller?.answer ||
                data.zaki_v2?.answer ||
                data.reply ||
                "Analysis complete.";
              onResponse?.(reply, reply);
              return reply;
            } catch (err) {
              return "Unable to connect to intelligence engine.";
            }
          },
          onError: () => {
            setVoiceState("idle");
            setIsLiveMode(false);
          },
        },
        { runId }
      );
    }
  };

  const handlePauseResume = () => {
    if (isPaused) {
      jarvisVoice.resume();
      setIsPaused(false);
    } else {
      jarvisVoice.pause();
      setIsPaused(true);
    }
  };

  const handleStop = () => {
    jarvisVoice.stop();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  const handleRepeat = () => {
    jarvisVoice.repeatLastAnswer();
  };

  const handleToggleMute = () => {
    const next = !isMuted;
    setIsMuted(next);
    jarvisVoice.setMuted(next);
  };

  // Status text matching user's design image
  const statusLabel = isPaused
    ? "P A U S E D"
    : isSpeaking
    ? "S P E A K I N G"
    : voiceState === "listening" || isLiveMode
    ? "L I S T E N I N G"
    : voiceState === "processing"
    ? "T H I N K I N G"
    : "S T A N D B Y";

  // Calculate 9 symmetrical bars on left and right
  const barMultipliers = [0.25, 0.45, 0.75, 1.0, 0.85, 0.65, 0.45, 0.3, 0.15];

  return (
    <div
      className={cn(
        "relative w-full overflow-hidden border-b border-white/10 bg-[#06101e]/90 px-4 py-3 select-none flex flex-col items-center justify-center transition-all",
        className
      )}
    >
      {/* Background ambient constellation glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-slate-950/40 to-transparent pointer-events-none" />

      {/* Symmetrical Speech Activity Visualizer */}
      <div className="relative w-full max-w-[340px] flex items-center justify-center my-1">
        {/* Horizontal dashed guide line */}
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 border-t border-dashed border-amber-500/30 pointer-events-none" />

        {/* Left Waveform Bars (mirrored) */}
        <div className="relative z-10 flex items-center gap-[3px] pr-2">
          {barMultipliers
            .slice()
            .reverse()
            .map((mult, idx) => {
              const active = isSpeaking || voiceState === "listening";
              const height = active ? Math.max(3, Math.round(mult * audioLevel * 32)) : 3;
              return (
                <span
                  key={`left-${idx}`}
                  className={cn(
                    "w-[3px] rounded-full transition-all duration-75",
                    active
                      ? "bg-amber-400 drop-shadow-[0_0_6px_rgba(245,158,11,0.8)]"
                      : "bg-amber-500/30"
                  )}
                  style={{ height: `${height}px` }}
                />
              );
            })}
        </div>

        {/* Central Aperture Lens Orb */}
        <div className="relative z-20 flex items-center justify-center mx-1">
          {/* Outer purple halo ring */}
          <div
            className={cn(
              "absolute h-14 w-14 rounded-full transition-all duration-300 pointer-events-none",
              isSpeaking || isLiveMode
                ? "bg-purple-500/30 blur-md scale-110 animate-pulse"
                : "bg-purple-500/10 blur-sm"
            )}
          />

          {/* Secondary purple inner ring */}
          <div className="absolute h-10 w-10 rounded-full border border-purple-400/40 bg-purple-900/30 pointer-events-none" />

          {/* Central dark disc with glowing amber border */}
          <button
            type="button"
            onClick={toggleVoiceMode}
            title={isLiveMode ? "Disconnect voice" : "Tap to speak (Full Duplex)"}
            className={cn(
              "relative h-8 w-8 rounded-full bg-slate-950 border-2 transition-all flex items-center justify-center cursor-pointer shadow-lg hover:scale-105 active:scale-95",
              isSpeaking
                ? "border-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.8)]"
                : isLiveMode
                ? "border-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.6)]"
                : "border-amber-500/60 hover:border-amber-400 hover:shadow-[0_0_10px_rgba(245,158,11,0.4)]"
            )}
          >
            {/* Inner amber pupil core */}
            <span
              className={cn(
                "rounded-full transition-all duration-200",
                isSpeaking
                  ? "h-3.5 w-3.5 bg-amber-300 shadow-[0_0_10px_#fbbf24] scale-110"
                  : isLiveMode
                  ? "h-3 w-3 bg-amber-400 shadow-[0_0_8px_#f59e0b] animate-ping"
                  : "h-2.5 w-2.5 bg-amber-400/80"
              )}
            />
          </button>
        </div>

        {/* Right Waveform Bars */}
        <div className="relative z-10 flex items-center gap-[3px] pl-2">
          {barMultipliers.map((mult, idx) => {
            const active = isSpeaking || voiceState === "listening";
            const height = active ? Math.max(3, Math.round(mult * audioLevel * 32)) : 3;
            return (
              <span
                key={`right-${idx}`}
                className={cn(
                  "w-[3px] rounded-full transition-all duration-75",
                  active
                    ? "bg-amber-400 drop-shadow-[0_0_6px_rgba(245,158,11,0.8)]"
                    : "bg-amber-500/30"
                )}
                style={{ height: `${height}px` }}
              />
            );
          })}
        </div>
      </div>

      {/* Glowing Status Typography */}
      <div className="relative z-10 mt-1.5 flex items-center justify-center gap-3">
        <span className="font-mono text-[11px] font-extrabold tracking-[0.28em] text-amber-400 drop-shadow-[0_0_8px_rgba(245,158,11,0.7)] uppercase">
          {statusLabel}
        </span>

        {/* Inline Quick Playback Controls (when speaking or paused) */}
        {(isSpeaking || isPaused) && (
          <div className="flex items-center gap-1 animate-in fade-in duration-150">
            <button
              type="button"
              onClick={handlePauseResume}
              title={isPaused ? "Resume" : "Pause"}
              className="p-1 rounded text-amber-400/80 hover:text-amber-200 transition hover:bg-amber-500/10 cursor-pointer"
            >
              {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
            </button>
            <button
              type="button"
              onClick={handleStop}
              title="Stop"
              className="p-1 rounded text-amber-400/80 hover:text-amber-200 transition hover:bg-amber-500/10 cursor-pointer"
            >
              <Square className="h-3 w-3" />
            </button>
            <button
              type="button"
              onClick={handleRepeat}
              title="Repeat"
              className="p-1 rounded text-amber-400/80 hover:text-amber-200 transition hover:bg-amber-500/10 cursor-pointer"
            >
              <RotateCcw className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ZakiSpeechVisualizer;
