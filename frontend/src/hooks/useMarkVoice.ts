"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  jarvisVoice,
  type VoiceState,
  type MarkVoiceSettings,
} from "@/lib/voice";
import { API_BASE } from "@/lib/api/config";
import type { MarkPresentation } from "@/lib/mark-presentation";

export interface UseMarkVoiceOptions {
  runId?: string;
  scenarioId?: string;
  simulationStatus?: string;
  onResponse?: (answer: string, spokenAnswer?: string, presentation?: MarkPresentation) => void;
  onTranscript?: (transcript: string) => void;
  onMessageSubmit?: (text: string) => Promise<string | { text: string; spokenText?: string } | void>;
  onError?: (err: unknown) => void;
}

export function useMarkVoice(options?: UseMarkVoiceOptions) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isLiveMode, setIsLiveMode] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>("");
  const [lastAnswer, setLastAnswer] = useState<string>("");
  const [lastSpokenAnswer, setLastSpokenAnswer] = useState<string>("");
  const [playbackRate, setPlaybackRateState] = useState<number>(() => {
    return jarvisVoice.getPlaybackRate ? jarvisVoice.getPlaybackRate() : 1.0;
  });

  const setPlaybackRate = useCallback((rate: number) => {
    jarvisVoice.setPlaybackRate(rate);
    setPlaybackRateState(rate);
  }, []);

  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Persistent session id across voice turns
  const sessionIdRef = useRef<string>(
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? `voice-session-${crypto.randomUUID().slice(0, 8)}`
      : `voice-session-${Date.now()}`
  );

  // Sync initial mute status
  useEffect(() => {
    setIsMuted(jarvisVoice.getIsMuted());
    setPlaybackRateState(jarvisVoice.getPlaybackRate ? jarvisVoice.getPlaybackRate() : 1.0);
  }, []);

  // Poll speaking/listening/paused states
  useEffect(() => {
    const timer = setInterval(() => {
      setIsSpeaking(jarvisVoice.getIsSpeaking());
      setIsListening(jarvisVoice.getIsListening());
      setIsPaused(jarvisVoice.getIsPaused());
    }, 200);
    return () => clearInterval(timer);
  }, []);

  const toggleLiveMode = useCallback(() => {
    jarvisVoice.prime();

    if (isLiveMode) {
      jarvisVoice.stopLiveMode();
      setIsLiveMode(false);
      setVoiceState("idle");
    } else {
      setIsLiveMode(true);
      jarvisVoice.startLiveMode(
        {
          onStateChange: (state) => {
            setVoiceState(state);
            setIsSpeaking(state === "speaking");
            setIsListening(state === "listening");
          },
          onTranscript: (text) => {
            setTranscript(text);
            optionsRef.current?.onTranscript?.(text);
          },
          onResponse: (answer, spokenAnswer, presentation) => {
            setLastAnswer(answer);
            const effectiveSpoken = spokenAnswer || answer;
            setLastSpokenAnswer(effectiveSpoken);
            optionsRef.current?.onResponse?.(answer, spokenAnswer, presentation);
          },
          onMessageSubmit: async (text: string) => {
            if (optionsRef.current?.onMessageSubmit) {
              const res = await optionsRef.current.onMessageSubmit(text);
              if (res) {
                if (typeof res === "string") {
                  setLastAnswer(res);
                  setLastSpokenAnswer(res);
                  return res;
                } else if (typeof res === "object" && res.text) {
                  setLastAnswer(res.text);
                  const spoken = res.spokenText || res.text;
                  setLastSpokenAnswer(spoken);
                  return spoken;
                }
              }
            }
            try {
              const payload = {
                query: text,
                message: text,
                session_id: sessionIdRef.current,
                run_id: optionsRef.current?.runId,
                scenario_id: optionsRef.current?.scenarioId || "SCN-001",
                simulation_status: optionsRef.current?.simulationStatus || "READY",
                workspace: "investigate",
                response_level: "engineer",
              };
              let res = await fetch(`${API_BASE}/api/v1/fikracore/zaki/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              });
              if (res.status === 409) {
                const livePayload = { ...payload, revision: undefined };
                res = await fetch(`${API_BASE}/api/v1/fikracore/zaki/chat`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(livePayload),
                });
              }
              if (!res.ok) {
                const err = `Backend error ${res.status}`;
                setLastAnswer(err);
                setLastSpokenAnswer(err);
                return err;
              }
              const data = await res.json();
              const reply =
                data.zaki_v2?.spoken_answer ||
                data.zaki_v2?.storyteller?.spoken_answer ||
                data.zaki_v2?.answer ||
                data.reply ||
                data.response?.content ||
                "Analysis complete.";

              setLastAnswer(data.zaki_v2?.answer || reply);
              const spoken = data.zaki_v2?.spoken_answer || data.zaki_v2?.storyteller?.spoken_answer || reply;
              setLastSpokenAnswer(spoken);
              optionsRef.current?.onResponse?.(reply, spoken, data.zaki_v2?.storyteller);
              return spoken;
            } catch (err: unknown) {
              console.warn("[useMarkVoice] Submit error:", err);
              const msg = err instanceof Error ? err.message : "Error connecting to backend";
              setLastAnswer(msg);
              setLastSpokenAnswer(msg);
              return msg;
            }
          },
          onError: (err) => {
            setVoiceState("idle");
            optionsRef.current?.onError?.(err);
          },
        },
        {
          runId: optionsRef.current?.runId,
          responseSpeechEngine: "neural",
        }
      );
    }
  }, [isLiveMode]);

  const speak = useCallback((text: string) => {
    if (!text.trim()) return;
    jarvisVoice.prime();
    setLastSpokenAnswer(text);
    setIsSpeaking(true);
    jarvisVoice.speak(text, {
      engine: "neural",
      onStart: () => setIsSpeaking(true),
      onEnd: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
  }, []);

  const pause = useCallback(() => {
    jarvisVoice.pause();
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    jarvisVoice.resume();
    setIsPaused(false);
  }, []);

  const stop = useCallback(() => {
    jarvisVoice.stop();
    setIsSpeaking(false);
    setIsPaused(false);
  }, []);

  const repeatLast = useCallback(() => {
    jarvisVoice.repeatLastAnswer("neural");
  }, []);

  const toggleMute = useCallback(() => {
    const next = !isMuted;
    setIsMuted(next);
    jarvisVoice.setMuted(next);
    if (!next) {
      jarvisVoice.speak("Zaki voice online.", { engine: "neural" });
    }
  }, [isMuted]);

  const updateVoiceSettings = useCallback((settings: Partial<MarkVoiceSettings>) => {
    jarvisVoice.setVoiceSettings(settings);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isLiveMode) {
        jarvisVoice.stopLiveMode();
      }
    };
  }, [isLiveMode]);

  return {
    voiceState,
    isLiveMode,
    isSpeaking,
    isListening,
    isPaused,
    isMuted,
    playbackRate,
    setPlaybackRate,
    transcript,
    lastAnswer,
    lastSpokenAnswer,
    toggleLiveMode,
    speak,
    pause,
    resume,
    stop,
    repeatLast,
    toggleMute,
    updateVoiceSettings,
  };
}

export const useZakiVoice = useMarkVoice;
export default useMarkVoice;
