"use client";

import React, { useState, useCallback, useRef, useSyncExternalStore } from "react";
import "@/components/jarvis/jarvis.css";
import { JarvisHeader } from "@/components/jarvis/JarvisHeader";
import { CorrelationEngine } from "@/components/jarvis/CorrelationEngine";
import { FcspsLens } from "@/components/jarvis/FcspsLens";
import { NetworkOverview } from "@/components/jarvis/NetworkOverview";
import { MarkCognitiveWorld } from "@/components/mark-orb/MarkCognitiveWorld";
import { DigitalAssets } from "@/components/jarvis/DigitalAssets";
import { AiInsights } from "@/components/jarvis/AiInsights";
import { RecentAlerts } from "@/components/jarvis/RecentAlerts";
import { JarvisCommandBar } from "@/components/jarvis/JarvisCommandBar";
import { API_BASE } from "@/lib/api/config";
import { jarvisVoice } from "@/lib/voice";
import type { VoiceState } from "@/lib/voice";
import { presentationPayload, presentationRouteTrace, type MarkPresentation } from "@/lib/mark-presentation";
import type { MarkVisualState } from "@/lib/mark-capability-graph";
import { StorytellerVisualExplanation } from "@/components/features/agentic-qna-view/components/StorytellerVisualExplanation";
import { RTRJourneyOverlay } from "@/components/hud/RTRJourneyOverlay";
import type { RTRJourneyOverlayPresentation } from "@/lib/mark-presentation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Volume2, X, Copy, Check, Sparkles, ChevronLeft, ChevronRight, SlidersHorizontal, Pin, PinOff, Maximize2, Minimize2 } from "lucide-react";
import { MarkHudProvider, useMarkHud } from "@/lib/mark-hud-context";
import { resolveMarkFontFamily } from "@/lib/mark-hud-context";
import { MarkControlPanel } from "@/components/mark-orb/MarkControlPanel";
import { MarkShaderBackground } from "@/components/mark-orb/MarkShaderBackground";

const THEME_STORAGE_KEY = "jarvis_theme";
const THEME_CHANGE_EVENT = "jarvis-theme-change";

function getStoredThemeSnapshot(): boolean {
  if (typeof window === "undefined") return true;
  const saved = localStorage.getItem(THEME_STORAGE_KEY);
  return saved === null ? true : saved === "dark";
}

function subscribeToThemeChanges(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", callback);
  window.addEventListener(THEME_CHANGE_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(THEME_CHANGE_EVENT, callback);
  };
}

function useJarvisTheme(): boolean {
  return useSyncExternalStore(
    subscribeToThemeChanges,
    getStoredThemeSnapshot,
    () => true
  );
}

function normalizeMarkNodeId(id?: string | null): string | null {
  if (!id) return null;
  const map: Record<string, string> = {
    fcsps: "fcaps_learning",
    "digital-assets": "topology",
    network: "telemetry_evidence",
    predictions: "intent",
    knowledge: "knowledge_base",
  };
  return map[id] ?? id;
}

function JarvisPageContent() {
  const { settings } = useMarkHud();
  const [activeTab, setActiveTab] = useState("correlation");
  const [selectedOrb, setSelectedOrb] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isVoiceVisualActive, setIsVoiceVisualActive] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const isDarkMode = useJarvisTheme();
  const [lastQuery, setLastQuery] = useState<string | null>(null);
  const [activeReply, setActiveReply] = useState<string | null>(null);
  const [activeSpokenReply, setActiveSpokenReply] = useState<string | null>(null);
  const [presentation, setPresentation] = useState<MarkPresentation | undefined>();
  const [rtrJourney, setRtrJourney] = useState<RTRJourneyOverlayPresentation | null>(null);
  const [copied, setCopied] = useState(false);
  const [statusText, setStatusText] = useState(
    "MARK online. Realtime voice assistant directing 5G Core operations."
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [controlPanelOpen, setControlPanelOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Streaming text and autonomous floating card state
  const [isStreaming, setIsStreaming] = useState(false);
  const [manualFlyOverride, setManualFlyOverride] = useState<"lower-center" | "middle-right" | null>(null);
  const [isVisualPinned, setIsVisualPinned] = useState(false);
  const [isVisualFading, setIsVisualFading] = useState(false);
  const visualHoldTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const visualFadeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamGenRef = useRef(0);
  const textScrollRef = useRef<HTMLDivElement>(null);

  const clearVisualTimers = useCallback(() => {
    if (visualHoldTimerRef.current) {
      clearTimeout(visualHoldTimerRef.current);
      visualHoldTimerRef.current = null;
    }
    if (visualFadeTimerRef.current) {
      clearTimeout(visualFadeTimerRef.current);
      visualFadeTimerRef.current = null;
    }
    setIsVisualFading(false);
  }, []);

  const scheduleVisualDismissal = useCallback(() => {
    clearVisualTimers();
    if (isVisualPinned) return;

    // Visual stays visible for 15 seconds after speaking/reading ends, then fades away over 2 seconds
    visualHoldTimerRef.current = setTimeout(() => {
      setIsVisualFading(true);
      visualFadeTimerRef.current = setTimeout(() => {
        setIsVoiceVisualActive(false);
        setIsVisualFading(false);
        visualFadeTimerRef.current = null;
      }, 2000); // 2-second fade-away transition
      visualHoldTimerRef.current = null;
    }, 15000); // 15 seconds hold
  }, [clearVisualTimers, isVisualPinned]);

  React.useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => {
      document.removeEventListener("fullscreenchange", onFsChange);
      clearVisualTimers();
    };
  }, [clearVisualTimers]);

  const markVisualState: MarkVisualState = isSpeaking
    ? "speaking"
    : isLoading || voiceState === "processing"
    ? "processing"
    : voiceState === "listening"
    ? "listening"
    : presentation?.narrative?.next_actions?.some((action) => action.requires_approval)
    ? "waiting_for_approval"
    : isVoiceVisualActive && presentation
    ? "investigating"
    : activeReply && presentation?.narrative?.claims?.some((claim) => claim.fcaps?.length)
    ? "learning"
    : "idle";

  const markRouteTrace = presentationRouteTrace(markVisualState, presentation);

  // Compute dynamic autonomous flight position:
  // Compact responses stay at "lower-center". Large responses fly to "middle-right".
  const responseLength = activeReply?.length || 0;
  const isLargeResponse = responseLength > 240 || (activeReply ? activeReply.split("\n\n").length > 2 : false);
  const cardPosition = manualFlyOverride || (isLargeResponse ? "middle-right" : "lower-center");

  // Auto-scroll to latest streaming text
  React.useEffect(() => {
    if (textScrollRef.current) {
      textScrollRef.current.scrollTop = textScrollRef.current.scrollHeight;
    }
  }, [activeReply, isStreaming]);

  // Handle auto-dismiss of independent visual stage once reading finishes
  React.useEffect(() => {
    if (isSpeaking) {
      clearVisualTimers();
      if (presentation) {
        setIsVoiceVisualActive(true);
      }
    } else {
      // Voice stopped or reading finished: stay for 15s then fade away over 2s
      if (!isVisualPinned && isVoiceVisualActive && !isVisualFading) {
        scheduleVisualDismissal();
      }
    }
  }, [isSpeaking, isVisualPinned, isVoiceVisualActive, isVisualFading, presentation, clearVisualTimers, scheduleVisualDismissal]);

  const streamResponseText = useCallback(
    async (text: string, onComplete?: () => void) => {
      const gen = ++streamGenRef.current;
      setIsStreaming(true);
      setActiveReply("");

      // Match words + spaces or newlines
      const tokens = text.match(/\S+\s*|\n+/g) || [text];
      let current = "";

      for (let i = 0; i < tokens.length; i++) {
        if (streamGenRef.current !== gen) return; // cancelled by new query
        current += tokens[i];
        setActiveReply(current);

        if (textScrollRef.current) {
          textScrollRef.current.scrollTop = textScrollRef.current.scrollHeight;
        }

        const token = tokens[i];
        const delay = token.includes("\n") ? 30 : tokens.length > 80 ? 12 : 18;
        await new Promise((r) => setTimeout(r, delay));
      }

      if (streamGenRef.current === gen) {
        setIsStreaming(false);
        onComplete?.();
      }
    },
    []
  );

  const sendingRef = useRef(false);
  const lastSubmissionRef = useRef<{ query: string; time: number }>({ query: "", time: 0 });

  const toggleTheme = () => {
    const next = !getStoredThemeSnapshot();
    localStorage.setItem(THEME_STORAGE_KEY, next ? "dark" : "light");
    window.dispatchEvent(new Event(THEME_CHANGE_EVENT));
  };

  const handleSendMessage = useCallback(
    async (query: string, speakAloud: boolean = true): Promise<string> => {
      const trimmed = query.trim();
      if (!trimmed) return "";

      const now = Date.now();
      if (sendingRef.current) {
        console.warn("[MARK] Request already in flight, skipping duplicate submission:", trimmed);
        return "";
      }
      if (
        lastSubmissionRef.current.query.toLowerCase() === trimmed.toLowerCase() &&
        now - lastSubmissionRef.current.time < 1500
      ) {
        console.warn("[MARK] Duplicate request debounced:", trimmed);
        return "";
      }

      sendingRef.current = true;
      lastSubmissionRef.current = { query: trimmed, time: now };

      // Prime browser audio immediately on synchronous user click
      jarvisVoice.prime();

      // Cancel any existing timers and dismiss visual immediately before new conversation starts
      clearVisualTimers();
      setIsVoiceVisualActive(false);
      setIsVisualFading(false);

      setIsLoading(true);
      setIsStreaming(true);
      setPresentation(undefined);
      setIsSpeaking(false);
      setLastQuery(trimmed);
      setStatusText(`MARK analyzing: "${trimmed}"...`);
      setActiveReply("");
      setManualFlyOverride(null);

      let finalReply = "";
      let spokenReply = "";

      try {
        const res = await fetch(`${API_BASE}/api/jarvis/process`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "mark_incident_session", message: trimmed }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Backend returned status ${res.status}`);
        }

        const data = await res.json();
        finalReply = data.reply || `Analysis complete for: ${trimmed}`;
        spokenReply = data.spoken_reply || "";
        const pres = { narrative: data.narrative, visual_explanation: data.visual_explanation };
        setPresentation(pres);

        if (data.rtr_journey) {
          setRtrJourney(data.rtr_journey);
        } else {
          setRtrJourney(null);
        }

        if (data.narrative || data.visual_explanation) {
          setIsVoiceVisualActive(true);
          setIsVisualFading(false);
        }

        // Start voice speech concurrently with text streaming
        if (speakAloud && finalReply && !finalReply.startsWith("Connection error") && !jarvisVoice.getIsLiveMode()) {
          jarvisVoice.speak(spokenReply || finalReply, {
            onStart: () => {
              setIsSpeaking(true);
              clearVisualTimers();
              setIsVoiceVisualActive(true);
              setIsVisualFading(false);
            },
            onEnd: () => {
              setIsSpeaking(false);
              scheduleVisualDismissal();
            },
            onError: () => {
              setIsSpeaking(false);
              scheduleVisualDismissal();
            },
          });
        }

        // Real-time progressive streaming of reply text
        await streamResponseText(finalReply, () => {
          setStatusText("MARK response rendered.");
          if (!isSpeaking) {
            scheduleVisualDismissal();
          }
        });
      } catch (err: unknown) {
        if (!finalReply) {
          const message = err instanceof Error ? err.message : "Failed to fetch";
          finalReply = `Connection error reaching backend at ${API_BASE}: ${message}`;
          setActiveReply(finalReply);
        }
      } finally {
        sendingRef.current = false;
        setIsStreaming(false);
        setActiveReply(finalReply);
        setActiveSpokenReply(spokenReply || null);
        setStatusText("MARK response rendered.");
        setIsLoading(false);
      }
      return jarvisVoice.getIsLiveMode() ? spokenReply || finalReply : finalReply;
    },
    [clearVisualTimers, scheduleVisualDismissal, streamResponseText, isSpeaking]
  );

  const handleCopy = () => {
    if (!activeReply) return;
    navigator.clipboard.writeText(activeReply);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReplayVoice = () => {
    if (!activeReply) return;
    clearVisualTimers();
    setIsVoiceVisualActive(true);
    setIsVisualFading(false);
    jarvisVoice.speak(activeSpokenReply || activeReply, {
      onStart: () => {
        setIsSpeaking(true);
        clearVisualTimers();
        setIsVoiceVisualActive(true);
        setIsVisualFading(false);
      },
      onEnd: () => {
        setIsSpeaking(false);
        scheduleVisualDismissal();
      },
      onError: () => {
        setIsSpeaking(false);
        scheduleVisualDismissal();
      },
    });
  };

  const handleVoiceResponse = useCallback(
    (answer: string, spokenAnswer?: string, visual?: MarkPresentation) => {
      if (!answer.trim()) return;
      // Before new conversation starts or on incoming response, clear visual timers
      clearVisualTimers();
      setActiveSpokenReply(spokenAnswer?.trim() || null);
      setPresentation(visual);
      if (visual?.narrative || visual?.visual_explanation) {
        setIsVoiceVisualActive(true);
        setIsVisualFading(false);
      }
      setStatusText("MARK streaming response...");
      setIsLoading(false);

      // Realtime progressive token streaming for voice responses
      streamResponseText(answer, () => {
        setStatusText("MARK response rendered.");
        if (!isSpeaking) {
          scheduleVisualDismissal();
        }
      });
    },
    [clearVisualTimers, streamResponseText, scheduleVisualDismissal, isSpeaking]
  );

  const handleVoiceState = useCallback(
    (state: VoiceState) => {
      setVoiceState(state);
      const speaking = state === "speaking";
      setIsSpeaking(speaking);
      if (speaking) {
        clearVisualTimers();
        setIsVoiceVisualActive(true);
        setIsVisualFading(false);
      }
      // Note: do not dismiss on "idle" or "listening" here - scheduleVisualDismissal manages the 15s timer!
      setIsLoading(state === "processing");
    },
    [clearVisualTimers]
  );

  const handleTabSelect = (tabId: string) => {
    setActiveTab(tabId);
    setSelectedOrb(tabId);
  };

  return (
    <div
      ref={containerRef}
      className={`mark-ui-shell relative w-full h-full flex flex-col justify-between overflow-hidden p-2.5 sm:p-3 transition-colors duration-300 ${
        isFullscreen ? "rounded-none border-0" : "rounded-xl border"
      } ${
        isDarkMode
          ? "dark jarvis-dark bg-[#04080f] text-slate-100 border-cyan-500/20 shadow-[0_0_50px_rgba(0,0,0,0.8)]"
          : "bg-[#07111f] text-slate-100 border-cyan-500/20 shadow-[0_0_45px_rgba(10,102,255,0.18)]"
      }`}
      style={{
        "--mark-ui-font": resolveMarkFontFamily(settings),
        "--mark-ui-font-scale": settings.fontScale,
      } as React.CSSProperties}
    >
      {/* 1. Global Holographic Deep Radial Gradient (Covers whole screen behind all components) */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          background:
            "radial-gradient(ellipse 95% 88% at 50% 48%, #122c43 0%, #0c1d30 38%, #07111f 72%, #050b14 100%)",
        }}
      />

      {/* 2. Global Full-Screen Plasma Wave Shader (Sweeps across entire viewport behind all UI) */}
      {settings.showWaves && (
        <div aria-hidden="true" className="absolute inset-0 pointer-events-none z-0">
          <MarkShaderBackground
            opacity={settings.waveOpacity}
            speedMultiplier={settings.waveSpeed}
            voiceActive={markVisualState === "speaking" || markVisualState === "processing" || markVisualState === "investigating"}
            gold={markVisualState === "learning" || markVisualState === "waiting_for_approval"}
          />
        </div>
      )}

      {/* 3. Global Cyan Screen Halo Glow */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          mixBlendMode: "screen",
          background: `radial-gradient(circle at 50% 50%, rgba(13,210,255,${
            markVisualState === "speaking" ? 0.28 : markVisualState === "processing" || markVisualState === "investigating" ? 0.22 : 0.14
          }) 0%, rgba(13,170,228,0.06) 38%, rgba(8,17,31,0) 68%)`,
          transition: "background 0.6s ease",
        }}
      />

      {/* 4. Background Starfield / Particle Matrix */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40 transition-opacity duration-300 z-0"
        style={{
          backgroundImage:
            "radial-gradient(#00e5ff 0.65px, transparent 0.65px), radial-gradient(#f5a623 0.55px, transparent 0.55px)",
          backgroundSize: "34px 34px, 89px 89px",
          backgroundPosition: "0 0, 21px 13px",
        }}
      />

      {/* 1. Header Navigation Bar */}
      <div className="relative z-20 shrink-0 mb-2">
        <JarvisHeader
          activeTab={activeTab}
          onSelectTab={handleTabSelect}
          isDarkMode={isDarkMode}
          onToggleTheme={toggleTheme}
          onOpenSearch={() => handleSendMessage("List all current active incidents from the registry", false)}
          onOpenSettings={() => setControlPanelOpen(true)}
          onOpenChat={() => {
            if (!activeReply) {
              handleSendMessage("What is the telecom brain we are building?", false);
            }
          }}
        />
      </div>

      {/* 2. Main Stage Area: 100% Full Stage for Mark with Floating Overlay */}
      <div className="relative z-10 flex-1 min-h-0 flex flex-col w-full h-full items-stretch overflow-hidden">
        {/* Central Mark HUD Stage (100% width and height, permanently centered) */}
        <div className="flex-1 flex flex-col justify-between items-center h-full min-h-0 relative px-1 sm:px-2 w-full">
          {/* Header Banner Text */}
          <div className="w-full flex items-center justify-center shrink-0 pt-0.5 px-2 select-none">
            <p className="font-mono text-[11px] sm:text-xs font-bold uppercase tracking-[0.14em] text-cyan-400 drop-shadow-[0_0_8px_rgba(0,229,255,0.35)] text-center">
              MARK TELECOM BRAIN.{" "}
              <span className={isDarkMode ? "text-slate-200" : "text-[#082863]"}>
                INCIDENT OPERATIONS COMMANDER.
              </span>
            </p>
          </div>

          {/* Holographic HUD Center Stage */}
          <div className="flex-1 w-full min-h-0 relative flex items-center justify-center">
            {/* Dedicated full-width/height canvas container for Mark Cognitive World */}
            <div className="w-full h-full relative flex items-center justify-center">
              <MarkCognitiveWorld
                state={markVisualState}
                trace={markRouteTrace}
                selectedNodeId={normalizeMarkNodeId(selectedOrb)}
                onSelectNode={(nodeId) => {
                  if (nodeId) handleTabSelect(nodeId);
                  else setSelectedOrb(null);
                }}
                onRunAction={(actionText) => handleSendMessage(actionText, true)}
              />
            </div>

            {/* 1. Autonomous Floating MARK Dialogue Response Card */}
            {activeReply && (
              <div
                style={{ position: "absolute" }}
                className={`!absolute z-50 flex flex-col p-3.5 rounded-xl border border-cyan-500/40 bg-[#050B14]/95 text-slate-100 backdrop-blur-2xl mark-flight-card ${
                  cardPosition === "middle-right" ? "pos-middle-right" : "pos-lower-center"
                } ${isStreaming ? "mark-floating-active border-cyan-400/80" : ""}`}
              >
                {/* Header */}
                <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 mb-2 shrink-0">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-cyan-500/15 text-cyan-400 flex items-center justify-center border border-cyan-400/40">
                      <Sparkles className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-bold uppercase tracking-wider text-white">
                        MARK
                      </span>
                      <span className="font-mono text-[10px] font-medium text-cyan-400 uppercase tracking-wider">
                        • INCIDENT MANAGER
                      </span>
                      {isStreaming && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-cyan-950/70 border border-cyan-400/50 text-[8.5px] font-mono text-cyan-300 font-semibold ml-1 animate-pulse">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                          STREAMING
                        </span>
                      )}
                      {activeReply.toLowerCase().includes("error") && (
                        <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-950/60 border border-rose-500/40 text-[8.5px] font-mono text-rose-300 font-semibold ml-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
                          VOICE OFFLINE
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Manual Floating Flight Toggle */}
                    <button
                      onClick={() => setManualFlyOverride(cardPosition === "middle-right" ? "lower-center" : "middle-right")}
                      className="p-1 rounded bg-white/5 hover:bg-white/15 text-cyan-400 hover:text-white border border-cyan-500/30 text-[10px] font-mono flex items-center gap-1 px-1.5 cursor-pointer transition-colors"
                      title={cardPosition === "middle-right" ? "Dock to Lower Center" : "Fly to Middle Right"}
                    >
                      {cardPosition === "middle-right" ? (
                        <>
                          <Minimize2 className="w-3 h-3" />
                          <span className="hidden sm:inline">Dock Center</span>
                        </>
                      ) : (
                        <>
                          <Maximize2 className="w-3 h-3" />
                          <span className="hidden sm:inline">Float Right</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleReplayVoice}
                      className="p-1 rounded bg-cyan-950/60 hover:bg-cyan-900/80 text-[#00e5ff] border border-cyan-500/40 text-[10px] font-mono font-bold flex items-center gap-1 px-2 cursor-pointer transition-colors"
                      title="Replay Voice Audio"
                    >
                      <Volume2 className="w-3 h-3" />
                      <span>{isSpeaking ? "Speaking..." : "Replay Voice"}</span>
                    </button>
                    <button
                      onClick={handleCopy}
                      className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px] font-mono flex items-center gap-1 px-1.5 cursor-pointer transition-colors"
                      title="Copy Answer"
                    >
                      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    </button>
                    <button
                      onClick={() => {
                        streamGenRef.current++;
                        jarvisVoice.stop();
                        setIsStreaming(false);
                        clearVisualTimers();
                        setIsVoiceVisualActive(false);
                        setActiveReply(null);
                      }}
                      className="p-1 rounded bg-white/5 hover:bg-white/15 text-slate-400 hover:text-white border border-transparent transition-colors cursor-pointer"
                      title="Dismiss"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Question */}
                {lastQuery && (
                  <p className="font-mono text-[10px] font-bold text-cyan-400/90 mb-1.5 truncate shrink-0">
                    Q: &ldquo;{lastQuery}&rdquo;
                  </p>
                )}

                {/* Streamable & Auto-scrolling Answer Content */}
                <div
                  ref={textScrollRef}
                  className="flex-1 overflow-y-auto jarvis-scrollbar font-mono text-xs leading-relaxed text-slate-200 font-normal pr-1 select-text min-h-0 scroll-smooth"
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{activeReply}</ReactMarkdown>
                  {isStreaming && (
                    <span className="inline-block w-1.5 h-3.5 bg-cyan-400 ml-1 animate-pulse align-middle" />
                  )}
                </div>
              </div>
            )}

            {/* Mobile Core RTR Ticket Journey Overlay (Low Opacity Glassmorphic Layer) */}
            {rtrJourney && (
              <RTRJourneyOverlay
                presentation={rtrJourney}
                onClose={() => setRtrJourney(null)}
              />
            )}

            {/* 2. Independent Detached Response Visuals Stage (Floats Separately & Auto-Dismisses After 15s with 2s Fade) */}
            {activeReply && presentation && (isVoiceVisualActive || isVisualPinned || isSpeaking) && (
              <div
                style={{ position: "absolute" }}
                className={`!absolute z-40 flex flex-col p-3 rounded-xl border border-cyan-400/40 bg-[#050B14]/92 text-slate-100 backdrop-blur-2xl shadow-[0_16px_45px_rgba(0,0,0,0.85),0_0_30px_rgba(0,229,255,0.2)] mark-visual-stage ${
                  isVisualFading ? "fading" : "animate-in fade-in zoom-in-95 duration-300"
                } ${
                  cardPosition === "middle-right"
                    ? "top-3 left-4 w-[min(460px,calc(100vw-480px))] max-h-[58vh]"
                    : "top-3 left-1/2 -translate-x-1/2 w-[min(620px,calc(100vw-32px))] max-h-[42vh]"
                }`}
              >
                {/* Visual Stage Header */}
                <div className="flex items-center justify-between pb-1.5 border-b border-cyan-500/20 mb-2 shrink-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      OPERATIONAL VISUAL EXPLANATION
                    </span>
                    {isSpeaking && (
                      <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-400/40 text-[8px] font-mono text-emerald-300 font-bold">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                        READING LIVE
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Pin / Keep Open Toggle */}
                    <button
                      onClick={() => {
                        const nextPinned = !isVisualPinned;
                        setIsVisualPinned(nextPinned);
                        if (nextPinned) {
                          clearVisualTimers();
                        } else {
                          scheduleVisualDismissal();
                        }
                      }}
                      className={`p-1 rounded text-[9px] font-mono font-bold flex items-center gap-1 px-2 cursor-pointer transition-all border ${
                        isVisualPinned
                          ? "bg-cyan-500/25 text-[#00e5ff] border-cyan-400/60 shadow-[0_0_10px_rgba(0,229,255,0.25)]"
                          : "bg-white/5 text-slate-400 hover:text-white border-transparent"
                      }`}
                      title={isVisualPinned ? "Pinned: Stays visible permanently" : "Auto-fade: Fades after 15s (Click to Pin)"}
                    >
                      {isVisualPinned ? <Pin className="w-3 h-3 text-cyan-400 fill-cyan-400/40" /> : <PinOff className="w-3 h-3 text-slate-400" />}
                      <span>{isVisualPinned ? "Pinned" : "Auto-Fade"}</span>
                    </button>
                    {/* Close Button */}
                    <button
                      onClick={() => {
                        clearVisualTimers();
                        setIsVoiceVisualActive(false);
                        setIsVisualPinned(false);
                      }}
                      className="p-1 rounded bg-white/5 hover:bg-white/15 text-slate-400 hover:text-white transition-colors cursor-pointer"
                      title="Close Visuals"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Visual Widgets Content */}
                <div className="flex-1 overflow-y-auto jarvis-scrollbar pr-0.5 min-h-0">
                  <StorytellerVisualExplanation
                    key={activeReply}
                    payload={presentationPayload(activeReply, activeSpokenReply || undefined, presentation)}
                    speaking={isSpeaking}
                  />
                </div>
              </div>
            )}
          </div>

          {/* MARK Interactive Command Bar with Voice */}
          <div className="w-full max-w-5xl shrink-0 mt-1 z-20">
            <JarvisCommandBar
              onSendMessage={handleSendMessage}
              onVoiceResponse={handleVoiceResponse}
              onVoiceStateChange={handleVoiceState}
              onVoiceTranscript={setLastQuery}
              isLoading={isLoading}
              statusText={statusText}
              isSpeaking={isSpeaking}
            />
          </div>
        </div>

        {/* Floating Minimizable Overlay Panel (Displays OVER the page without affecting Mark fitting) */}
        {sidebarOpen ? (
          <aside className="absolute right-2 top-8 bottom-16 z-40 w-[420px] max-w-[92vw] flex flex-col gap-2.5 p-3.5 bg-[#050B14]/95 backdrop-blur-2xl rounded-2xl border border-cyan-500/35 shadow-[-16px_16px_50px_rgba(0,0,0,0.85)] animate-in slide-in-from-right duration-200">
            {/* Overlay Header with minimize button */}
            <div className="flex items-center justify-between pb-2 border-b border-cyan-500/20 shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-md bg-cyan-500/15 text-cyan-400 flex items-center justify-center border border-cyan-400/30">
                  <SlidersHorizontal className="w-3 h-3" />
                </div>
                <span className="font-mono text-[11px] font-bold uppercase tracking-[0.14em] text-[#00e5ff] flex items-center gap-1.5">
                  TELEMETRY & OPERATIONS
                </span>
                <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/50 border border-emerald-500/30 text-[8.5px] font-mono text-emerald-400 font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  LIVE
                </span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-1 rounded-md bg-cyan-950/40 hover:bg-cyan-900/60 text-cyan-400 hover:text-white border border-cyan-500/30 transition-all cursor-pointer"
                title="Minimize Overlay"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Segmented quick switcher pills */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-[#030812] border border-cyan-500/25 shrink-0 overflow-x-auto jarvis-scrollbar">
              {[
                { id: "correlation", label: "Correlation" },
                { id: "fcsps", label: "FCAPS" },
                { id: "network", label: "Network" },
                { id: "digital-assets", label: "Assets" },
                { id: "alerts", label: "Alerts" },
                { id: "insights", label: "AI" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabSelect(tab.id)}
                  className={`flex-1 py-1.5 px-1 font-mono text-[9px] font-bold uppercase tracking-wider rounded-lg transition-all text-center cursor-pointer whitespace-nowrap ${
                    activeTab === tab.id
                      ? "bg-cyan-500/20 text-[#00e5ff] border border-cyan-400/50 shadow-[0_0_12px_rgba(0,229,255,0.25)]"
                      : "text-slate-400 hover:text-cyan-300 hover:bg-white/5 border border-transparent"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Active Telemetry Module in full height */}
            <div className="flex-1 min-h-0 overflow-y-auto jarvis-scrollbar pr-0.5">
              {activeTab === "correlation" && <CorrelationEngine />}
              {activeTab === "fcsps" && <FcspsLens />}
              {activeTab === "network" && <NetworkOverview />}
              {activeTab === "digital-assets" && <DigitalAssets onOpenModal={() => handleTabSelect("digital-assets")} />}
              {activeTab === "alerts" && (
                <RecentAlerts onOpenAlerts={() => handleSendMessage("List all current active incidents from the registry", false)} />
              )}
              {activeTab === "insights" && <AiInsights />}
              {!["correlation", "fcsps", "network", "digital-assets", "alerts", "insights"].includes(activeTab) && (
                <CorrelationEngine />
              )}
            </div>
          </aside>
        ) : (
          /* Modern Sci-Fi Telemetry Dock Handle: Floating edge trigger with live beacon */
          <button
            onClick={() => setSidebarOpen(true)}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-40 flex flex-col items-center gap-2.5 py-4 px-2 rounded-l-xl bg-[#030814]/92 hover:bg-[#061224]/95 backdrop-blur-2xl border-y border-l border-cyan-500/35 hover:border-cyan-400/80 text-cyan-400 shadow-[-10px_0_30px_rgba(0,0,0,0.7),0_0_18px_rgba(0,229,255,0.15)] hover:shadow-[0_0_28px_rgba(0,229,255,0.35)] transition-all duration-300 cursor-pointer group hover:-translate-x-1"
            title="Open Telemetry & Operations Overlay"
            aria-label="Open Telemetry & Operations Overlay"
          >
            {/* Live Operational Beacon LED */}
            <span className="relative flex h-2 w-2 items-center justify-center">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400 shadow-[0_0_6px_#34d399]" />
            </span>

            {/* Sliding Chevron Indicator */}
            <div className="w-5 h-5 rounded-md bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center group-hover:bg-cyan-500/25 group-hover:border-cyan-400 transition-all shadow-sm">
              <ChevronLeft className="w-3.5 h-3.5 text-cyan-400 group-hover:-translate-x-0.5 transition-transform" />
            </div>

            {/* Futuristic Vertical Monospace Label */}
            <span className="[writing-mode:vertical-rl] font-mono text-[9.5px] font-black uppercase tracking-[0.24em] text-cyan-200/70 group-hover:text-[#00e5ff] transition-colors py-1 select-none">
              TELEMETRY
            </span>

            {/* Mini Cyber Level Indicator Pips */}
            <div className="flex flex-col gap-0.5 opacity-60 group-hover:opacity-100 transition-opacity">
              <span className="w-1 h-1 rounded-full bg-cyan-400/80 shadow-[0_0_4px_rgba(0,229,255,0.8)]" />
              <span className="w-1 h-1 rounded-full bg-cyan-400/50" />
              <span className="w-1 h-1 rounded-full bg-cyan-400/30" />
            </div>
          </button>
        )}
      </div>

      {/* Real-time HUD Parameters Control Panel Modal */}
      <MarkControlPanel isOpen={controlPanelOpen} onClose={() => setControlPanelOpen(false)} />
    </div>
  );
}

export default function JarvisPage() {
  return (
    <MarkHudProvider>
      <JarvisPageContent />
    </MarkHudProvider>
  );
}
