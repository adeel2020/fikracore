"use client";

import React, { useEffect, useState } from "react";
import type { MarkPresentation } from "@/lib/mark-presentation";
import {
  Mic,
  Send,
  Workflow,
  ShieldCheck,
  Camera,
  Settings,
  FileText,
  Plus,
  Loader2,
  Volume2,
  VolumeX,
  Radio,
} from "lucide-react";
import { jarvisVoice, MARK_PLAYBACK_RATES, MARK_VOICE_TONES, DEFAULT_VOICE_SETTINGS } from "@/lib/voice";
import type { MarkVoiceMode, MarkVoiceSettings, VoiceState } from "@/lib/voice";

interface JarvisCommandBarProps {
  onSendMessage: (query: string) => Promise<string | void> | void;
  onVoiceResponse?: (answer: string, spokenAnswer?: string, presentation?: MarkPresentation) => void;
  onVoiceStateChange?: (state: VoiceState) => void;
  onVoiceTranscript?: (text: string) => void;
  isLoading?: boolean;
  statusText?: string;
  isSpeaking?: boolean;
}

const QUICK_ACTIONS = [
  { id: "rca", label: "Run RCA", sub: "Incident Mgr", icon: Workflow, query: "What is the root cause of recent mobile core incidents?" },
  { id: "health", label: "Incident Queue", sub: "Registry", icon: ShieldCheck, query: "List all current incidents from the registry" },
  { id: "impact", label: "Blast Radius", sub: "Subscribers", icon: Camera, query: "What is the end-to-end workflow from alarm ingestion to incident story?" },
  { id: "validation", label: "FCAPS Review", sub: "Cognitive Lens", icon: Settings, query: "How does FCAPS serve as a cognitive lens for telecom operations?" },
  { id: "report", label: "Story Report", sub: "Storyteller", icon: FileText, query: "How does the deterministic storyteller work with gbrain MCP?" },
];

export function JarvisCommandBar({
  onSendMessage,
  onVoiceResponse,
  onVoiceStateChange,
  onVoiceTranscript,
  isLoading = false,
  statusText = "ZAKI ready. Realtime voice assistant online.",
  isSpeaking = false,
}: JarvisCommandBarProps) {
  const [input, setInput] = useState("");
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [isMuted, setIsMuted] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState<MarkVoiceSettings>(DEFAULT_VOICE_SETTINGS);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  useEffect(() => () => jarvisVoice.stopLiveMode(), []);

  useEffect(() => {
    setIsMuted(jarvisVoice.getIsMuted());
    const backendVoiceSettings = { ...jarvisVoice.getVoiceSettings(), mode: "backend" as const };
    jarvisVoice.setVoiceSettings(backendVoiceSettings);
    setVoiceSettings(backendVoiceSettings);
  }, []);

  useEffect(() => {
    const loadVoices = () => setAvailableVoices(jarvisVoice.getAvailableVoices());
    loadVoices();

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.addEventListener?.("voiceschanged", loadVoices);
      window.speechSynthesis.onvoiceschanged = loadVoices;
      return () => {
        window.speechSynthesis.removeEventListener?.("voiceschanged", loadVoices);
        if (window.speechSynthesis.onvoiceschanged === loadVoices) {
          window.speechSynthesis.onvoiceschanged = null;
        }
      };
    }
    return undefined;
  }, []);

  const updateVoiceSettings = (patch: Partial<MarkVoiceSettings>) => {
    const next = { ...voiceSettings, ...patch };
    setVoiceSettings(next);
    jarvisVoice.setVoiceSettings(next);

    if (patch.mode && isLiveMode) {
      jarvisVoice.stopLiveMode();
      setIsLiveMode(false);
      setVoiceState("idle");
      onVoiceStateChange?.("idle");
    }
  };

  const toggleLiveVoiceMode = () => {
    jarvisVoice.prime();

    if (isLiveMode) {
      jarvisVoice.stopLiveMode();
      setIsLiveMode(false);
      setVoiceState("idle");
      onVoiceStateChange?.("idle");
    } else {
      const serverVoiceSettings = { ...jarvisVoice.getVoiceSettings(), mode: "backend" as const };
      jarvisVoice.setVoiceSettings(serverVoiceSettings);
      setVoiceSettings(serverVoiceSettings);
      setIsLiveMode(true);
      jarvisVoice.startLiveMode({
        onStateChange: (state) => { setVoiceState(state); onVoiceStateChange?.(state); },
        onTranscript: (text) => { setInput(text); onVoiceTranscript?.(text); },
        onResponse: (answer, spokenAnswer, presentation) => onVoiceResponse?.(answer, spokenAnswer, presentation),
        onMessageSubmit: async (text) => {
          const res = await onSendMessage(text);
          return res || "";
        },
        onError: (err) => {
          setIsLiveMode(false);
          setVoiceState("idle");
          onVoiceStateChange?.("idle");
          const message =
            typeof err === "object" && err !== null && "message" in err
              ? String((err as { message?: unknown }).message || "Live voice error")
              : "Live voice error";
          onVoiceResponse?.(`ZAKI live voice error: ${message}`);
        },
      }, { responseSpeechEngine: "neural", allowBrowserFallback: false });
    }
  };

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    jarvisVoice.prime();
    onSendMessage(input.trim());
    setInput("");
  };

  const handleQuickAction = (query: string) => {
    jarvisVoice.prime();
    onSendMessage(query);
  };

  const toggleMute = () => {
    const next = !isMuted;
    setIsMuted(next);
    jarvisVoice.setMuted(next);
    if (!next) {
      jarvisVoice.speak("Zaki voice online.", { engine: "neural" });
    }
  };

  return (
    <div className="w-full flex flex-col items-center gap-1.5 select-none">
      {/* 1. Primary Command Input Pill Bar */}
      <div
        className={`jarvis-card w-full max-w-[760px] p-1.5 flex flex-col gap-1.5 transition-all duration-300 ${
          isLiveMode
            ? "border-cyan-400 shadow-[0_0_30px_rgba(0,229,255,0.35)] ring-1 ring-cyan-400/50"
            : "shadow-[0_14px_45px_rgba(10,102,255,0.12)]"
        }`}
      >
        <form data-testid="mark-command-form" onSubmit={handleSubmit} className="flex items-center gap-1.5">
          {/* Left Brain Icon / Voice Mute Toggle */}
          <button
            type="button"
            onClick={toggleMute}
            className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 shadow-sm transition-all cursor-pointer ${
              isMuted
                ? "bg-slate-200 dark:bg-slate-800 text-slate-400 border border-slate-300 dark:border-slate-700"
                : "bg-blue-50 dark:bg-cyan-950/60 text-[#0a66ff] dark:text-[#00e5ff] border border-blue-200/80 dark:border-cyan-500/40"
            }`}
            title={isMuted ? "Click to unmute Zaki Voice" : "Zaki Voice Active (Click to mute)"}
          >
            {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5 animate-pulse" />}
          </button>

          {/* Text Input Field */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isLiveMode
                ? voiceState === "listening"
                  ? "Listening... speak naturally to Zaki..."
                  : voiceState === "processing"
                  ? "Zaki is analyzing your question..."
                  : "Zaki is speaking response..."
                : "Ask Zaki anything... (e.g. What is the root cause of recent incidents?)"
            }
            className="flex-1 min-w-0 bg-transparent font-mono text-[12px] font-semibold text-slate-100 placeholder:text-slate-500 focus:outline-none px-1.5 tracking-normal"
          />

          {/* Realtime Audio Waveform Graphic */}
          <div className="hidden sm:flex items-center gap-0.5 h-5 px-1">
            {[0.3, 0.7, 0.5, 1.0, 0.4, 0.9, 0.3, 0.8, 1.0, 0.6, 0.4, 0.8, 0.5, 0.3].map((h, i) => (
              <span
                key={i}
                className="w-0.5 bg-[#00e5ff] rounded-full audio-bar"
                style={{
                  height: `${h * 14}px`,
                  animationDelay: `${i * 0.08}s`,
                  opacity: isLiveMode || voiceState === "listening" || isSpeaking || isLoading ? 1 : 0.35,
                }}
              />
            ))}
          </div>

          {/* Realtime Live Continuous Voice Toggle */}
          <button
            type="button"
            onClick={toggleLiveVoiceMode}
            className={`px-2.5 h-7 rounded-full flex items-center gap-1.5 transition-all font-mono text-[10px] font-bold uppercase tracking-wider cursor-pointer ${
              isLiveMode
                ? "bg-rose-500 text-white animate-pulse shadow-[0_0_20px_rgba(244,63,94,0.7)]"
                : "bg-cyan-500/15 text-[#00e5ff] hover:bg-cyan-500/25 border border-cyan-400/40"
            }`}
            title={isLiveMode ? "Turn off Live Voice Mode" : "Start Hands-Free Realtime Voice Conversation"}
          >
            {isLiveMode ? (
              <>
                <Radio className="w-3 h-3 animate-spin" />
                <span className="hidden md:inline">Live Mode</span>
              </>
            ) : (
              <>
                <Mic className="w-3 h-3" />
                <span className="hidden md:inline">Live Voice</span>
              </>
            )}
          </button>

          {/* Send Trigger Button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="w-7 h-7 rounded-full bg-[#0a66ff] dark:bg-[#00e5ff] text-white dark:text-slate-950 flex items-center justify-center shrink-0 shadow-[0_4px_14px_rgba(10,102,255,0.35)] hover:bg-blue-600 dark:hover:bg-cyan-300 disabled:opacity-40 transition-all cursor-pointer"
          >
            {isLoading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Send className="w-3 h-3" strokeWidth={2.2} />
            )}
          </button>
        </form>

        {/* Live Reasoning / Speech Status Indicator */}
        <div className="flex items-center justify-between px-1.5 text-[9px] font-mono font-medium text-slate-400 truncate">
          <div className="flex items-center gap-1.5 truncate">
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                voiceState === "speaking" || isSpeaking
                  ? "bg-cyan-400 animate-ping"
                  : isLiveMode || voiceState === "listening"
                  ? "bg-rose-500 animate-ping"
                  : "bg-emerald-400 animate-pulse"
              }`}
            />
            <span className="truncate text-cyan-200/80">
              {isLiveMode
                ? voiceState === "listening"
                  ? "Zaki is listening... Speak anytime."
                : voiceState === "processing"
                ? "Zaki is analyzing operational telemetry..."
                : "Zaki is speaking..."
              : statusText}
            </span>
          </div>
          <button
            type="button"
            onClick={() => jarvisVoice.testVoice()}
            className="hidden sm:inline-block h-5 rounded border border-cyan-500/35 bg-cyan-950/40 px-2 font-mono text-[8.5px] font-bold uppercase tracking-wider text-[#00e5ff] transition-colors hover:bg-cyan-900/60 cursor-pointer"
            title="Click to test voice audio output"
          >
            Test Voice
          </button>
        </div>

        <div className="grid grid-cols-2 gap-1 px-1.5 sm:grid-cols-5">
          <label className="flex min-w-0 items-center gap-1 rounded border border-cyan-500/20 bg-slate-950/45 px-1.5">
            <span className="font-mono text-[7px] font-bold uppercase tracking-wider text-cyan-400/70">Eng</span>
            <select
              value={voiceSettings.mode}
              onChange={(e) => updateVoiceSettings({ mode: e.target.value as MarkVoiceMode })}
              className="h-5 min-w-0 flex-1 bg-transparent font-mono text-[8.5px] font-semibold uppercase tracking-normal text-cyan-100 outline-none"
              title="Voice engine"
            >
              <option value="backend">Realtime</option>
              <option value="browser">Browser Demo</option>
            </select>
          </label>

          <label className="flex min-w-0 items-center gap-1 rounded border border-cyan-500/20 bg-slate-950/45 px-1.5">
            <span className="font-mono text-[7px] font-bold uppercase tracking-wider text-cyan-400/70">Voice</span>
            <select
              value={voiceSettings.voiceURI}
              onChange={(e) => updateVoiceSettings({ voiceURI: e.target.value })}
              className="h-5 min-w-0 flex-1 truncate bg-transparent font-mono text-[8.5px] font-semibold tracking-normal text-cyan-100 outline-none"
              title="Browser voice"
            >
              <option value="auto">Auto Best</option>
              {availableVoices.map((voice) => (
                <option key={voice.voiceURI} value={voice.voiceURI}>
                  {voice.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-w-0 items-center gap-1 rounded border border-cyan-500/20 bg-slate-950/45 px-1.5">
            <span className="font-mono text-[7px] font-bold uppercase tracking-wider text-cyan-400/70">Tone</span>
            <select
              value={voiceSettings.tone}
              onChange={(e) => updateVoiceSettings({ tone: e.target.value as MarkVoiceSettings["tone"] })}
              className="h-5 min-w-0 flex-1 bg-transparent font-mono text-[8.5px] font-semibold uppercase tracking-normal text-cyan-100 outline-none"
              title="Speaking tone"
            >
              {MARK_VOICE_TONES.map((tone) => (
                <option key={tone.id} value={tone.id}>
                  {tone.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-w-0 items-center gap-1 rounded border border-cyan-500/20 bg-slate-950/45 px-1.5">
            <span className="font-mono text-[7px] font-bold uppercase tracking-wider text-cyan-400/70">Speed</span>
            <select
              value={voiceSettings.playbackRate}
              onChange={(e) => updateVoiceSettings({ playbackRate: Number(e.target.value) })}
              className="h-5 min-w-0 flex-1 bg-transparent font-mono text-[8.5px] font-semibold uppercase tracking-normal text-cyan-100 outline-none"
              title="Voice playback speed"
            >
              {MARK_PLAYBACK_RATES.map((rate) => (
                <option key={rate} value={rate}>
                  {rate}x
                </option>
              ))}
            </select>
          </label>

          {/* Auto-Correct STT Domain Normalization Toggle */}
          <button
            type="button"
            onClick={() => updateVoiceSettings({ autoCorrect: !voiceSettings.autoCorrect })}
            className={`flex min-w-0 items-center justify-between gap-1 rounded border px-1.5 h-5 font-mono text-[8.5px] font-bold uppercase tracking-wider transition-all cursor-pointer select-none col-span-2 sm:col-span-1 ${
              voiceSettings.autoCorrect
                ? "border-cyan-400/60 bg-cyan-950/50 text-[#00e5ff] shadow-[0_0_10px_rgba(0,229,255,0.2)]"
                : "border-slate-800 bg-slate-950/40 text-slate-500 hover:text-slate-400"
            }`}
            title="Auto-Correct telecom acronyms (AMF, SMF, UPF, FCAPS, gNodeB) in speech recognition"
          >
            <span className="text-[7px] text-cyan-400/70">Auto-Fix</span>
            <span className={`px-1 py-0.2 rounded text-[8px] ${voiceSettings.autoCorrect ? "bg-cyan-500/20 text-[#00e5ff]" : "bg-white/5 text-slate-500"}`}>
              {voiceSettings.autoCorrect ? "ON" : "OFF"}
            </span>
          </button>
        </div>
      </div>

      {/* 2. Quick Action Buttons Row */}
      <div className="w-full max-w-[760px] grid grid-cols-3 gap-1.5 sm:grid-cols-6">
        {QUICK_ACTIONS.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.id}
              onClick={() => handleQuickAction(action.query)}
              className="jarvis-card px-1 py-1.5 flex flex-col items-center justify-center text-center hover:-translate-y-0.5 transition-all cursor-pointer group"
            >
              <Icon className="w-3.5 h-3.5 text-cyan-400 group-hover:text-cyan-200 group-hover:scale-110 transition-transform mb-0.5" strokeWidth={2} />
              <span className="font-mono text-[8.5px] font-bold tracking-tight text-slate-100 group-hover:text-cyan-300 block leading-tight uppercase">
                {action.label}
              </span>
              <span className="font-mono text-[7px] tracking-wider text-cyan-400/60 group-hover:text-cyan-400/90 block mt-0.5 uppercase">
                {action.sub}
              </span>
            </button>
          );
        })}

        {/* Add Custom Action Button */}
        <button
          onClick={() => handleQuickAction("Check whether any approved operational playbooks or runbooks are present for current incident triage")}
          className="jarvis-card px-1 py-1.5 flex flex-col items-center justify-center text-center border-dashed transition-all cursor-pointer group hover:-translate-y-0.5"
        >
          <div className="w-3.5 h-3.5 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform mb-0.5 border border-cyan-400/40">
            <Plus className="w-2.5 h-2.5" strokeWidth={2.4} />
          </div>
          <span className="font-mono text-[8.5px] font-bold tracking-tight text-slate-100 group-hover:text-cyan-300 block leading-tight uppercase">
            Commands
          </span>
          <span className="font-mono text-[7px] tracking-wider text-cyan-400/60 block mt-0.5 uppercase">
            Custom
          </span>
        </button>
      </div>
    </div>
  );
}
