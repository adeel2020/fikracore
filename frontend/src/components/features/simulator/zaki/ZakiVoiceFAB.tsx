"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  RotateCcw,
  Pause,
  Play,
  Square,
  Sparkles,
  ChevronUp,
  ChevronDown,
  Activity,
  Radio,
  Send,
  Bot,
  FastForward,
  HelpCircle,
  ShieldAlert,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useMarkVoice } from "@/hooks/useMarkVoice";
import { jarvisVoice } from "@/lib/voice";

export interface ZakiChatMessage {
  id: string;
  sender: "user" | "zaki";
  text: string;
  spokenText?: string;
  isStreaming?: boolean;
  streamedLength?: number;
  timestamp?: string;
}

export interface ZakiVoiceFABProps {
  runId?: string;
  scenarioId?: string;
  simulationStatus?: string;
  className?: string;
  onMessageSubmit?: (text: string) => Promise<string | void>;
  onResponse?: (answer: string, spoken?: string) => void;
}

const QUICK_PROMPTS = [
  { label: "Root Cause", icon: ShieldAlert, prompt: "What is the confirmed root cause of this incident?" },
  { label: "Blast Radius", icon: Zap, prompt: "What is the blast radius and which downstream nodes are impacted?" },
  { label: "Next Action", icon: HelpCircle, prompt: "What is the recommended next action for remediation?" },
  { label: "Flash Story", icon: Sparkles, prompt: "Summarize the active simulation stage and live flash narration." },
];

export function ZakiVoiceFAB({
  runId,
  scenarioId,
  simulationStatus,
  className,
  onMessageSubmit,
  onResponse,
}: ZakiVoiceFABProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputText, setInputText] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState<ZakiChatMessage[]>([
    {
      id: "zaki-welcome",
      sender: "zaki",
      text: "Zaki Copilot active. Monitoring live simulation telemetry, causal graph, and blast radius. How can I assist with this incident?",
      isStreaming: false,
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const streamingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Scroll to bottom helper
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Cleanup streaming timer on unmount
  useEffect(() => {
    return () => {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current);
        streamingTimerRef.current = null;
      }
    };
  }, []);

  // Progressively stream text token-by-token / chunk-by-chunk
  const startStreaming = useCallback((messageId: string, fullText: string) => {
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current);
      streamingTimerRef.current = null;
    }

    let currentLength = 0;
    const totalLength = fullText.length;
    // Dynamic step size: ~2 to 5 characters every 18ms (~120-250 chars/sec)
    const stepSize = Math.max(2, Math.floor(totalLength / 70));

    streamingTimerRef.current = setInterval(() => {
      currentLength += stepSize;
      if (currentLength >= totalLength) {
        currentLength = totalLength;
        if (streamingTimerRef.current) {
          clearInterval(streamingTimerRef.current);
          streamingTimerRef.current = null;
        }
      }

      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id !== messageId) return msg;
          const isDone = currentLength >= totalLength;
          return {
            ...msg,
            streamedLength: currentLength,
            isStreaming: !isDone,
          };
        })
      );
    }, 18);
  }, []);

  // Skip streaming immediately
  const skipStreaming = useCallback((messageId: string) => {
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current);
      streamingTimerRef.current = null;
    }
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, streamedLength: msg.text.length, isStreaming: false }
          : msg
      )
    );
  }, []);

  // Voice hook integration
  const {
    voiceState,
    isLiveMode,
    isSpeaking,
    isListening,
    isPaused,
    isMuted,
    transcript,
    lastSpokenAnswer,
    toggleLiveMode,
    pause,
    resume,
    stop,
    repeatLast,
    toggleMute,
  } = useMarkVoice({
    runId,
    scenarioId,
    simulationStatus,
    onMessageSubmit,
    onResponse: (answer, spoken) => {
      onResponse?.(answer, spoken);
    },
  });

  // Whenever a new spoken answer arrives from voice hook, stream it if it's not already in messages
  useEffect(() => {
    if (!lastSpokenAnswer) return;
    const exists = messages.some((m) => m.text === lastSpokenAnswer);
    if (!exists) {
      const assistantId = `zaki-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          sender: "zaki",
          text: lastSpokenAnswer,
          isStreaming: true,
          streamedLength: 0,
        },
      ]);
      startStreaming(assistantId, lastSpokenAnswer);
    }
  }, [lastSpokenAnswer, messages, startStreaming]);

  // Handle user submitting message (typed or prompt clicked)
  const handleSendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isThinking) return;

    const userMsgId = `user-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: "user",
        text: trimmed,
      },
    ]);
    setInputText("");
    setIsThinking(true);

    try {
      let reply: string | void = undefined;
      if (onMessageSubmit) {
        reply = await onMessageSubmit(trimmed);
      }

      const answerText = reply || "Analysis received. Simulation telemetry synchronized.";
      const assistantId = `zaki-${Date.now()}`;

      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          sender: "zaki",
          text: answerText,
          isStreaming: true,
          streamedLength: 0,
        },
      ]);

      startStreaming(assistantId, answerText);

      // Auto-narrate response if not muted
      if (!isMuted && typeof window !== "undefined") {
        jarvisVoice.speak(answerText);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Error contacting Zaki copilot backend.";
      setMessages((prev) => [
        ...prev,
        {
          id: `zaki-err-${Date.now()}`,
          sender: "zaki",
          text: `⚠️ ${errorMsg}`,
          isStreaming: false,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking, scrollToBottom]);

  const getStatusLabel = () => {
    if (isPaused) return "Paused";
    if (voiceState === "listening" || isListening) return "Listening...";
    if (voiceState === "processing" || isThinking) return "Analyzing...";
    if (voiceState === "speaking" || isSpeaking) return "Speaking...";
    if (isLiveMode) return "Duplex Active";
    return "Zaki Voice Copilot";
  };

  const getOrbRingColor = () => {
    if (isSpeaking) return "border-cyan-400 bg-cyan-500/20 shadow-cyan-400/40";
    if (isListening) return "border-emerald-400 bg-emerald-500/20 shadow-emerald-400/40";
    if (voiceState === "processing" || isThinking) return "border-purple-400 bg-purple-500/20 shadow-purple-400/40";
    if (isLiveMode) return "border-cyan-400/60 bg-cyan-950/60";
    return "border-white/15 bg-slate-900/80 hover:border-cyan-400/40";
  };

  // Helper to render text with bold/badges
  const renderMessageContent = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*|\b(?:SCN|RUN|PE-RTR|UPF|AMF|SMF|GNB)-[A-Z0-9-]+\b|🎙️\s*"[^"]+")/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={i} className="font-semibold text-cyan-200">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (/^(?:SCN|RUN|PE-RTR|UPF|AMF|SMF|GNB)-[A-Z0-9-]+$/i.test(part)) {
        return (
          <span key={i} className="font-mono text-[11px] font-bold text-fuchsia-300 bg-fuchsia-950/60 border border-fuchsia-500/30 px-1 py-0.5 rounded">
            {part}
          </span>
        );
      }
      if (part.startsWith("🎙️")) {
        return (
          <span key={i} className="font-medium text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-1.5 py-0.5 rounded italic block my-1">
            {part}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  // ---------------------------------------------------------------------------
  // Collapsed Floating Button View (Positioned on the Right)
  // ---------------------------------------------------------------------------
  if (!isExpanded) {
    return (
      <div className={cn("fixed bottom-6 right-6 z-50 transition-all duration-300", className)}>
        <button
          type="button"
          onClick={() => {
            setIsExpanded(true);
            if (!isLiveMode) toggleLiveMode();
          }}
          className={cn(
            "flex items-center gap-3 rounded-full px-4 py-2.5 text-xs font-medium text-white shadow-2xl backdrop-blur-xl border transition-all hover:scale-105 cursor-pointer",
            isLiveMode
              ? "border-cyan-400/60 bg-slate-950/90 shadow-[0_0_25px_rgba(6,182,212,0.35)]"
              : "border-white/15 bg-slate-900/85 hover:border-cyan-500/30 shadow-black/50"
          )}
        >
          {/* Animated Core Orb */}
          <div className="relative flex items-center justify-center">
            <div
              className={cn(
                "h-7 w-7 rounded-full border flex items-center justify-center transition-all",
                getOrbRingColor()
              )}
            >
              {isMuted ? (
                <MicOff className="h-3.5 w-3.5 text-rose-400" />
              ) : isSpeaking ? (
                <Radio className="h-3.5 w-3.5 text-cyan-300 animate-pulse" />
              ) : (
                <Mic className="h-3.5 w-3.5 text-cyan-300" />
              )}
            </div>
            {isLiveMode && (
              <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
            )}
          </div>

          <div className="text-left">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white text-xs tracking-wide">ZAKI</span>
              {isLiveMode && (
                <span className="rounded-full bg-cyan-500/20 px-1.5 py-0.2 text-[9px] font-mono text-cyan-300 uppercase">
                  LIVE
                </span>
              )}
            </div>
            <p className="text-[10px] text-neutral-400 leading-none mt-0.5">{getStatusLabel()}</p>
          </div>

          <ChevronUp className="h-3.5 w-3.5 text-neutral-400 ml-1" />
        </button>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Expanded Unified Voice & Chat Copilot Card (Positioned on the Right)
  // ---------------------------------------------------------------------------
  return (
    <div
      className={cn(
        "fixed bottom-6 right-6 z-50 w-[420px] sm:w-[460px] h-[600px] max-h-[calc(100vh-2.5rem)] rounded-2xl border border-cyan-500/30 bg-slate-950/95 shadow-[0_20px_60px_rgba(0,0,0,0.85),0_0_35px_rgba(6,182,212,0.18)] backdrop-blur-2xl text-xs text-neutral-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 bg-white/[0.03]">
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              "h-8 w-8 rounded-xl border flex items-center justify-center transition-all",
              getOrbRingColor()
            )}
          >
            <Sparkles className="h-4 w-4 text-cyan-300" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h4 className="font-bold text-white tracking-wide">ZAKI Voice Copilot</h4>
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-[9px] font-mono font-bold uppercase",
                  isLiveMode ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30" : "bg-white/10 text-neutral-400"
                )}
              >
                {isLiveMode ? "Full-Duplex" : "Standby"}
              </span>
            </div>
            <p className="text-[10px] text-neutral-400">{getStatusLabel()}</p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(false)}
          className="rounded-lg p-1.5 text-neutral-400 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
          title="Minimize"
        >
          <ChevronDown className="h-4 w-4" />
        </button>
      </div>

      {/* Waveform indicator when listening/speaking */}
      {isLiveMode && (
        <div className="flex items-center justify-center gap-1 py-1.5 bg-cyan-950/20 border-b border-cyan-500/10">
          {[4, 10, 16, 8, 14, 20, 12, 6, 18, 10, 4].map((h, i) => (
            <span
              key={i}
              className={cn(
                "w-1 rounded-full transition-all duration-150",
                isSpeaking
                  ? "bg-cyan-400 animate-pulse"
                  : isListening
                  ? "bg-emerald-400 animate-pulse"
                  : "bg-white/20"
              )}
              style={{
                height: isSpeaking || isListening ? `${h}px` : "4px",
                animationDelay: `${i * 60}ms`,
              }}
            />
          ))}
          <span className="text-[10px] font-mono text-cyan-300 ml-2">
            {isSpeaking ? "Voice Out" : isListening ? "Voice In" : "Duplex Ready"}
          </span>
        </div>
      )}

      {/* Chat Messages Stream Area */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-3.5 space-y-3">
        {/* Live operator speech transcript if actively speaking */}
        {isListening && transcript && (
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-2.5 animate-pulse">
            <span className="text-[10px] font-mono text-emerald-300 uppercase block mb-1">
              🎙️ Listening to you:
            </span>
            <p className="text-neutral-100 text-xs italic">&ldquo;{transcript}&rdquo;</p>
          </div>
        )}

        {messages.map((msg) => {
          const isUser = msg.sender === "user";
          const displayText = msg.isStreaming
            ? msg.text.slice(0, msg.streamedLength || 0)
            : msg.text;

          return (
            <div
              key={msg.id}
              className={cn("flex flex-col w-full", isUser ? "items-end" : "items-start")}
            >
              <div className="flex items-center gap-1.5 mb-1 px-1">
                {!isUser ? (
                  <>
                    <Bot className="h-3 w-3 text-cyan-400" />
                    <span className="text-[10px] font-bold text-cyan-300 uppercase">Zaki</span>
                  </>
                ) : (
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase">You</span>
                )}
              </div>

              <div
                onClick={() => msg.isStreaming && skipStreaming(msg.id)}
                className={cn(
                  "rounded-2xl px-3.5 py-2.5 text-xs max-w-[90%] leading-relaxed transition-all shadow-md",
                  isUser
                    ? "bg-cyan-500/20 border border-cyan-400/30 text-white rounded-tr-sm"
                    : "bg-white/[0.04] border border-white/10 text-neutral-100 rounded-tl-sm hover:border-cyan-500/30 cursor-pointer"
                )}
                title={msg.isStreaming ? "Click to reveal immediately" : undefined}
              >
                <div>
                  {renderMessageContent(displayText)}
                  {msg.isStreaming && (
                    <span className="inline-block w-1.5 h-3.5 bg-cyan-400 ml-1 animate-pulse align-middle" />
                  )}
                </div>

                {/* Helper action line if streaming or completed */}
                {!isUser && (
                  <div className="mt-2 pt-1 border-t border-white/5 flex items-center justify-between text-[10px] text-neutral-400">
                    {msg.isStreaming ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          skipStreaming(msg.id);
                        }}
                        className="flex items-center gap-1 text-cyan-400 hover:text-cyan-200 cursor-pointer"
                      >
                        <FastForward className="h-2.5 w-2.5" />
                        <span>Skip stream</span>
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          jarvisVoice.speak(msg.text);
                        }}
                        className="flex items-center gap-1 text-neutral-400 hover:text-cyan-300 cursor-pointer"
                      >
                        <Volume2 className="h-2.5 w-2.5" />
                        <span>Narrate</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isThinking && (
          <div className="flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-950/30 px-3 py-2 text-cyan-200 text-xs animate-pulse">
            <Activity className="h-3.5 w-3.5 text-cyan-300 animate-spin" />
            <span>Zaki is correlating active telemetry and causal graph...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompts */}
      <div className="px-3 py-1.5 bg-white/[0.02] border-t border-white/5 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {QUICK_PROMPTS.map((qp) => {
          const Icon = qp.icon;
          return (
            <button
              key={qp.label}
              type="button"
              onClick={() => handleSendMessage(qp.prompt)}
              disabled={isThinking}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px] font-semibold text-neutral-300 bg-white/[0.04] border border-white/10 hover:border-cyan-400/40 hover:bg-cyan-500/10 hover:text-cyan-200 shrink-0 transition-colors cursor-pointer disabled:opacity-50"
            >
              <Icon className="h-3 w-3 text-cyan-400" />
              <span>{qp.label}</span>
            </button>
          );
        })}
      </div>

      {/* Input Chat Box */}
      <div className="border-t border-white/10 p-2.5 bg-white/[0.02]">
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(inputText);
          }}
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask Zaki or speak naturally..."
            disabled={isThinking}
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-neutral-500 focus:outline-none focus:border-cyan-400/60"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isThinking}
            className="rounded-xl bg-cyan-500/20 border border-cyan-400/30 hover:bg-cyan-500/30 text-cyan-300 p-2 transition-all disabled:opacity-40 cursor-pointer"
            title="Send query"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>

      {/* Audio & Duplex Action Controls */}
      <div className="border-t border-white/10 px-4 py-2 bg-white/[0.02] flex items-center justify-between">
        {/* Toggle Live Mode */}
        <button
          type="button"
          onClick={toggleLiveMode}
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all cursor-pointer",
            isLiveMode
              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30"
              : "bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 shadow-md"
          )}
        >
          {isLiveMode ? (
            <>
              <Square className="h-3 w-3 fill-current" />
              <span>Disconnect</span>
            </>
          ) : (
            <>
              <Mic className="h-3 w-3" />
              <span>Connect Voice</span>
            </>
          )}
        </button>

        {/* Audio Controls */}
        <div className="flex items-center gap-1">
          {isSpeaking && (
            <button
              type="button"
              onClick={isPaused ? resume : pause}
              title={isPaused ? "Resume voice" : "Pause voice"}
              className="rounded-lg p-1.5 bg-white/5 text-neutral-300 hover:text-white border border-white/10 cursor-pointer"
            >
              {isPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            </button>
          )}

          {isSpeaking && (
            <button
              type="button"
              onClick={stop}
              title="Stop speaking"
              className="rounded-lg p-1.5 bg-white/5 text-neutral-300 hover:text-white border border-white/10 cursor-pointer"
            >
              <Square className="h-3.5 w-3.5" />
            </button>
          )}

          {lastSpokenAnswer && (
            <button
              type="button"
              onClick={repeatLast}
              title="Repeat last response"
              className="rounded-lg p-1.5 bg-white/5 text-neutral-300 hover:text-white border border-white/10 cursor-pointer"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}

          <button
            type="button"
            onClick={toggleMute}
            title={isMuted ? "Unmute" : "Mute"}
            className={cn(
              "rounded-lg p-1.5 transition-colors border cursor-pointer",
              isMuted
                ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                : "bg-white/5 text-neutral-300 hover:text-white border-white/10"
            )}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ZakiVoiceFAB;
