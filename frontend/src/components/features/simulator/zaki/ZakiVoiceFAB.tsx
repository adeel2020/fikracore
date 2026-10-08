"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Square,
  Sparkles,
  ChevronUp,
  ChevronDown,
  Activity,
  Radio,
  Send,
  Bot,
  User,
  FastForward,
  HelpCircle,
  ShieldAlert,
  Zap,
  Maximize2,
  Minimize2,
  Loader2,
  Copy,
  Check,
  Brain,
  Network,
  FileText,
  ShieldCheck,
  BookOpen,
  ThumbsUp,
  ThumbsDown,
  Info,
  Trash2,
  Palette,
  Plus,
  Paperclip,
  X,
  Terminal,
  AtSign,
} from "lucide-react";

export type ZakiSkin = "glass-morphic" | "liquid-glass" | "white";

export interface AttachedFileItem {
  id: string;
  name: string;
  size: string;
  type: string;
}

export const SKILLS_CATALOG = [
  { trigger: "/diagnose", label: "/diagnose", description: "Deep root-cause analysis on telemetry & topology", icon: "🔍" },
  { trigger: "/mitigate", label: "/mitigate", description: "Trigger automated containment & remediation playbook", icon: "🛠️" },
  { trigger: "/correlate", label: "/correlate", description: "Correlate multi-domain signals across FCAPS streams", icon: "⛓️" },
  { trigger: "/blast-radius", label: "/blast-radius", description: "Calculate blast radius and subscriber degradation", icon: "🌐" },
  { trigger: "/telecom-graph", label: "/telecom-graph", description: "Launch interactive telecom knowledge graph explorer", icon: "📊" },
  { trigger: "/trace-analyzer", label: "/trace-analyzer", description: "Analyze PCAP network trace call flow with Mermaid diagram", icon: "📡" },
  { trigger: "/summarize", label: "/summarize", description: "Generate concise executive incident briefing story", icon: "📋" },
];

export const ENTITIES_CATALOG = [
  { trigger: "@PE-RTR-21", label: "@PE-RTR-21", description: "Provider Edge Router • Transport Domain", category: "Network Node" },
  { trigger: "@UPF-003", label: "@UPF-003", description: "User Plane Function • 5G Core Domain", category: "5G Function" },
  { trigger: "@CORE-K8S-A", label: "@CORE-K8S-A", description: "Core Kubernetes Cluster A Primary", category: "Infra Cluster" },
  { trigger: "@RTR-07", label: "@RTR-07", description: "Core BGP Router • Transport Tier 1", category: "Network Node" },
  { trigger: "@SCN-004", label: "@SCN-004", description: "BGP Route Flapping Cascade Scenario", category: "Incident" },
  { trigger: "@trace-004.pcap", label: "@trace-004.pcap", description: "Packet Capture • 48.2 MB Wireshark Trace", category: "Trace File" },
  { trigger: "@telemetry_kpis.csv", label: "@telemetry_kpis.csv", description: "10-Second Interval Metrics Stream", category: "Telemetry Data" },
  { trigger: "@alarms_fcaps.log", label: "@alarms_fcaps.log", description: "Active Fault & Alarm Traps Log", category: "Log File" },
];

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMarkVoice } from "@/hooks/useMarkVoice";
import { jarvisVoice } from "@/lib/voice";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/api/qna";
import {
  StorytellerLeftPanel,
  StorytellerRightPanel,
  VerticalSplitter,
} from "@/components/features/agentic-qna-view/components/StorytellerVisualExplanation";

export const OPERATIONAL_ACTION_CHIPS = [
  {
    icon: <BookOpen className="h-4 w-4 text-cyan-400" />,
    title: "Storyteller",
    prompt: "Provide an incident brief covering degraded services, active alerts, and impact scope.",
    tag: "Storyteller",
  },
  {
    icon: <Zap className="h-4 w-4 text-amber-400" />,
    title: "Blast Radius",
    prompt: "What is the operational blast radius and which downstream core and RAN nodes are affected?",
    tag: "Blast Radius",
  },
  {
    icon: <Network className="h-4 w-4 text-rose-400" />,
    title: "Causal Propagation Path",
    prompt: "Trace the cross-domain causal propagation path from the root trigger to user-plane drops.",
    tag: "Causal Path",
  },
  {
    icon: <ShieldCheck className="h-4 w-4 text-emerald-400" />,
    title: "Remediation Strategy",
    prompt: "What is the recommended remediation strategy and rollback verification procedure?",
    tag: "Remediation",
  },
];

export interface ZakiChatMessage {
  id: string;
  sender: "user" | "zaki";
  text: string;
  spokenText?: string;
  isStreaming?: boolean;
  streamedLength?: number;
  timestamp?: string;
  storyteller?: ChatMessage["storyteller"];
  latencyMs?: number;
}

export type ZakiSubmitReply =
  | string
  | {
      text: string;
      spokenText?: string;
      storyteller?: ChatMessage["storyteller"] | null;
      latencyMs?: number;
    };

const MARKDOWN_PLUGINS = [remarkGfm];

const isNerToken = (str: string): boolean => {
  const trimmed = str.trim();
  return (
    /^(?:IP:[A-Z0-9:]+|UPF-\d+|GNB-[A-Z0-9-]+|IMS-[A-Z0-9-]+|PE-RTR-\d+|RTR-\d+|INFRA:[A-Z0-9:-]+|CORE-K8S-[A-Z0-9-]+|CORE-KUBERNETES-[A-Z0-9-]+|EVT-[A-Z0-9-]+|SCN-\d+|VRF-N3-\d+|CRM-TICKET-\d+|[A-Z][A-Z0-9]+-(?:[A-Z0-9]+-?)+)$/i.test(trimmed) ||
    /^(?:INFRA K8S Core-A|User Plane Function-\d+|Customer Ticket-\d+|CORE-KUBERNETES-CLUSTER-A|RTR-\d+|VRF-N3-\d+|CRM-TICKET-\d+)$/i.test(trimmed)
  );
};

function formatProseChildren(nodes: React.ReactNode, skin: ZakiSkin = "glass-morphic"): React.ReactNode {
  const isWhite = skin === "white";
  return React.Children.map(nodes, (node) => {
    if (typeof node !== "string") return node;
    const cleaned = node.replace(/Network entity\s+([A-Z0-9:-]+)/g, "$1");
    const tokenRegex = /(──►|→|\*(?:observation)\*|\((?:status:\s*[a-z]+)\)|\b(?:IP:[A-Z0-9:]+|UPF-\d+|GNB-[A-Z0-9-]+|IMS-[A-Z0-9-]+|PE-RTR-\d+|RTR-\d+|INFRA:[A-Z0-9:-]+|CORE-K8S-[A-Z0-9-]+|CORE-KUBERNETES-[A-Z0-9-]+|EVT-[A-Z0-9-]+|SCN-\d+|VRF-N3-\d+|CRM-TICKET-\d+|[A-Z][A-Z0-9]+-(?:[A-Z0-9]+-?)+)\b|[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b)/g;

    const parts = cleaned.split(tokenRegex);
    if (parts.length <= 1) return node;

    return parts.map((part, k) => {
      if (!part) return null;
      if (part === "──►" || part === "→") {
        return (
          <span key={`arr-${k}`} className={cn("font-bold px-1 select-none", isWhite ? "text-cyan-700" : "text-cyan-400")}>
            {part}
          </span>
        );
      }
      if (part === "*(observation)*" || part === "(observation)") {
        return (
          <span key={`obs-${k}`} className={cn("text-xs italic font-normal", isWhite ? "text-slate-500" : "text-slate-500")}>
            *(observation)*
          </span>
        );
      }
      if (/^\(status:\s*[a-z]+\)$/i.test(part)) {
        return (
          <span key={`st-${k}`} className={cn("text-xs italic font-mono", isWhite ? "text-slate-500" : "text-slate-400")}>
            {part}
          </span>
        );
      }
      if (isNerToken(part)) {
        return (
          <span
            key={`ner-${k}`}
            className={cn("[font-family:Consolas,Monaco,'Courier_New',monospace] font-bold tracking-tight", isWhite ? "text-fuchsia-700" : "text-fuchsia-400 font-semibold")}
          >
            {part}
          </span>
        );
      }
      if (
        /[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b/i.test(
          part
        )
      ) {
        return (
          <span key={`met-${k}`} className={cn("font-mono font-bold", isWhite ? "text-cyan-800" : "text-cyan-400")}>
            {part}
          </span>
        );
      }
      return <span key={`txt-${k}`}>{part}</span>;
    });
  });
}

function getMarkdownComponents(skin: ZakiSkin = "glass-morphic") {
  const isWhite = skin === "white";
  return {
    h1: ({ children }: any) => (
      <h1 className={cn("text-base font-bold tracking-tight mt-3 mb-2 pb-1 border-b flex items-center gap-2", isWhite ? "text-slate-900 border-slate-200" : "text-white border-cyan-800/40")}>
        {children}
      </h1>
    ),
    h2: ({ children }: any) => (
      <h2 className={cn("text-sm font-semibold tracking-tight mt-2.5 mb-1.5", isWhite ? "text-slate-800" : "text-slate-100")}>
        {children}
      </h2>
    ),
    h3: ({ children }: any) => (
      <h3 className={cn("text-xs font-bold uppercase tracking-wider mt-3 mb-1.5 flex items-center gap-1.5 select-none", isWhite ? "text-cyan-800" : "text-cyan-400")}>
        {children}
      </h3>
    ),
    p: ({ children }: any) => (
      <p className={cn("mb-2 last:mb-0 leading-relaxed font-medium", isWhite ? "text-slate-800" : "text-slate-200")}>
        {formatProseChildren(children, skin)}
      </p>
    ),
    ul: ({ children }: any) => (
      <ul className="space-y-1 mb-2 list-none pl-0">{children}</ul>
    ),
    ol: ({ children }: any) => (
      <ol className="list-decimal pl-4 space-y-1 mb-2">{children}</ol>
    ),
    li: ({ children }: any) => (
      <li className={cn("leading-relaxed font-medium flex items-start gap-1.5 my-0.5", isWhite ? "text-slate-800" : "text-slate-200")}>
        <span className={cn("select-none mt-0.5", isWhite ? "text-cyan-700" : "text-cyan-400")}>•</span>
        <span className="flex-1">{formatProseChildren(children, skin)}</span>
      </li>
    ),
    strong: ({ children }: any) => {
      const rawText = React.Children.toArray(children)
        .map((c) => (typeof c === "string" ? c : ""))
        .join("")
        .trim();

      const isFieldLabel =
        /^(?:Incident ID|Status|Severity|Impact|Service|Component|Leading hypothesis|Correlation|Causal chain|Supporting evidence|Remediation|Still open|Mitigation strategy|Mandatory Prechecks|Domains|Blast radius):?$/i.test(
          rawText
        ) || rawText.endsWith(":");

      if (isFieldLabel) {
        return (
          <span className={cn("font-medium mr-1 select-none", isWhite ? "text-slate-500" : "text-slate-400")}>
            {children}
          </span>
        );
      }

      if (isNerToken(rawText)) {
        return (
          <span className={cn("[font-family:Consolas,Monaco,'Courier_New',monospace] font-bold tracking-tight", isWhite ? "text-fuchsia-700" : "text-fuchsia-400 font-semibold")}>
            {children}
          </span>
        );
      }

      if (
        /[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b(?:\s*(?:subscribers|users|sessions|calls))?|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b/i.test(
          rawText
        )
      ) {
        return <strong className={cn("font-mono font-bold", isWhite ? "text-cyan-800" : "text-cyan-400")}>{children}</strong>;
      }

      const isDomain = /transport|core|ran|ims|database|security|cloud|optical|router/i.test(rawText);
      if (isDomain) {
        return <strong className={cn("font-semibold", isWhite ? "text-cyan-700" : "text-cyan-300")}>{children}</strong>;
      }

      return <strong className={cn("font-semibold", isWhite ? "text-slate-900" : "text-slate-100")}>{children}</strong>;
    },
    code: ({ children }: any) => {
      const rawText = React.Children.toArray(children)
        .map((c) => (typeof c === "string" ? c : ""))
        .join("")
        .trim();

      if (
        isNerToken(rawText) ||
        /^[A-Z0-9]+(?:-[A-Z0-9]+)+$/i.test(rawText) ||
        /^SCN-\d+$/i.test(rawText)
      ) {
        return (
          <code className={cn("[font-family:Consolas,Monaco,'Courier_New',monospace] font-bold tracking-tight", isWhite ? "text-fuchsia-700" : "text-fuchsia-400 font-semibold")}>
            {children}
          </code>
        );
      }

      if (
        /^(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION|\d+(?:\.\d+)?%?)$/i.test(
          rawText
        )
      ) {
        return (
          <code className={cn("inline-flex items-center px-1.5 py-0.5 rounded font-mono text-xs font-bold tracking-tight shadow-sm", isWhite ? "text-cyan-800 bg-cyan-100 border border-cyan-300" : "text-cyan-400 bg-cyan-950/40 border border-cyan-800/40")}>
            {children}
          </code>
        );
      }

      return (
        <code className={cn("inline-flex items-center px-1.5 py-0.5 rounded [font-family:Consolas,Monaco,'Courier_New',monospace] text-xs", isWhite ? "text-slate-800 bg-slate-100 border border-slate-300" : "text-slate-300 bg-white/5 border border-white/10")}>
          {children}
        </code>
      );
    },
    blockquote: ({ children }: any) => (
      <div className={cn("my-2.5 px-3.5 py-2 rounded-xl border text-xs flex flex-wrap items-center gap-2 shadow-sm font-medium", isWhite ? "bg-slate-100/90 border-cyan-600/30 text-slate-800" : "bg-slate-950/80 border-cyan-500/20 text-slate-200")}>
        {formatProseChildren(children, skin)}
      </div>
    ),
  };
}

function renderMessageContent(text: string, skin: ZakiSkin = "glass-morphic") {
  const isWhite = skin === "white";
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\b(?:SCN|RUN|PE-RTR|UPF|AMF|SMF|GNB|NRF|PCF|UDM|UDR|N3|N4|N6|SGi)-[A-Z0-9-]+\b|🎙️\s*"[^"]+")/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const inner = part.slice(2, -2).trim();
      const isFieldLabel =
        /^(?:Incident ID|Status|Severity|Impact|Service|Component|Leading hypothesis|Correlation|Causal chain|Supporting evidence|Remediation|Still open|Mitigation strategy|Mandatory Prechecks|Domains|Blast radius):?$/i.test(
          inner
        ) || inner.endsWith(":");

      if (isFieldLabel) {
        return (
          <span key={i} className={cn("font-medium mr-1 select-none", isWhite ? "text-slate-500" : "text-slate-400")}>
            {inner}
          </span>
        );
      }
      if (isNerToken(inner)) {
        return (
          <span
            key={i}
            className={cn("[font-family:Consolas,Monaco,'Courier_New',monospace] font-bold tracking-tight", isWhite ? "text-fuchsia-700" : "text-fuchsia-400 font-semibold")}
          >
            {inner}
          </span>
        );
      }
      if (/[-+]?\d+(?:\.\d+)?%|\b\d{1,3}(?:,\d{3})+\b|\b(?:PAUSED|MAJOR|CRITICAL|ACTIVE|NOMINAL|DIVERGENT|CAUTION)\b/i.test(inner)) {
        return <strong key={i} className={cn("font-mono font-bold", isWhite ? "text-cyan-800" : "text-cyan-400")}>{inner}</strong>;
      }
      return (
        <strong key={i} className={cn("font-semibold", isWhite ? "text-slate-900" : "text-slate-100")}>
          {inner}
        </strong>
      );
    }
    if (isNerToken(part)) {
      return (
        <span
          key={i}
          className={cn("[font-family:Consolas,Monaco,'Courier_New',monospace] font-bold tracking-tight", isWhite ? "text-fuchsia-700" : "text-fuchsia-400 font-semibold")}
        >
          {part}
        </span>
      );
    }
    if (part.startsWith("🎙️")) {
      return (
        <span key={i} className={cn("font-medium border px-1.5 py-0.5 rounded italic block my-1", isWhite ? "text-cyan-800 bg-cyan-50 border-cyan-300" : "text-cyan-300 bg-cyan-950/60 border-cyan-500/30")}>
          {part}
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

const getActionBtnClass = (isWhite: boolean) =>
  cn(
    "transition-colors p-1 rounded cursor-pointer focus:outline-none flex items-center justify-center select-none",
    isWhite
      ? "text-slate-500 hover:text-cyan-800 hover:bg-slate-100"
      : "text-neutral-500/60 hover:text-cyan-400 hover:bg-white/5"
  );

const MessageBubble = React.memo(function MessageBubble({
  msg,
  isFullWindow,
  copiedId,
  onCopyText,
  onSkipStreaming,
  onClear,
  skin = "glass-morphic",
}: {
  msg: ZakiChatMessage;
  isFullWindow: boolean;
  copiedId: string | null;
  onCopyText: (id: string, text: string) => void;
  onSkipStreaming: (id: string) => void;
  onClear: (id: string) => void;
  skin?: ZakiSkin;
}) {
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const isUser = msg.sender === "user";
  const isWhite = skin === "white";
  const isLiquid = skin === "liquid-glass";
  const btnClass = getActionBtnClass(isWhite);

  const displayText = msg.isStreaming
    ? msg.text.slice(0, msg.streamedLength || 0)
    : msg.text;
  // Deterministic briefs make no LLM call, so token usage is an estimate (~4 chars/token).
  const estimatedTokens = Math.ceil((msg.text?.length || 0) / 4);

  const bubbleContent = (
    <div
      onClick={() => msg.isStreaming && onSkipStreaming(msg.id)}
      className={cn(
        "flex flex-col text-xs leading-relaxed transition-all shadow-md group",
        isUser
          ? isWhite
            ? "rounded-2xl rounded-tr-sm border border-cyan-400 bg-cyan-50/95 p-3.5 text-slate-900 max-w-[85%] shadow-sm"
            : isLiquid
            ? "rounded-2xl rounded-tr-sm border border-cyan-400/40 bg-gradient-to-br from-cyan-500/25 to-blue-600/15 p-3.5 text-white max-w-[85%] backdrop-blur-xl shadow-[0_4px_20px_rgba(6,182,212,0.2)]"
            : "rounded-2xl rounded-tr-sm border border-cyan-500/30 bg-cyan-500/10 p-3.5 text-white max-w-[85%]"
          : isWhite
          ? "rounded-2xl rounded-tl-sm border border-slate-200 bg-white/95 p-3.5 text-slate-900 hover:border-cyan-400/50 max-w-[90%] shadow-sm"
          : isLiquid
          ? "rounded-2xl rounded-tl-sm border border-cyan-500/30 bg-[#081736]/80 p-3.5 text-neutral-100 hover:border-cyan-400/50 backdrop-blur-2xl max-w-[90%] shadow-[0_8px_32px_rgba(0,0,0,0.37)]"
          : "rounded-2xl rounded-tl-sm border border-white/10 bg-white/[0.04] p-3.5 text-neutral-100 hover:border-cyan-500/30 backdrop-blur-md max-w-[90%]"
      )}
      title={msg.isStreaming ? "Click to reveal immediately" : undefined}
    >
      <div className={cn("flex items-center justify-between mb-1 pb-1 text-[10px]", isWhite ? "border-b border-slate-200" : "border-b border-white/5")}>
        <span className={cn("font-bold uppercase tracking-wider font-mono", isWhite ? "text-cyan-800" : isUser ? "text-cyan-300" : "text-cyan-400")}>
          {isUser ? "Operator" : "ZAKI Reasoning"}
        </span>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onCopyText(msg.id, msg.text);
            }}
            className={cn("p-1 rounded transition-colors", isWhite ? "hover:bg-slate-100 text-slate-500 hover:text-slate-800" : "hover:bg-white/10 text-neutral-400 hover:text-white")}
            title="Copy message"
          >
            {copiedId === msg.id ? (
              <Check className="h-3 w-3 text-emerald-400" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </button>
        </div>
      </div>

      <div className={cn("text-xs leading-relaxed", isWhite ? "text-slate-800" : "text-slate-200")}>
        {isUser ? (
          renderMessageContent(displayText, skin)
        ) : (
          <ReactMarkdown
            remarkPlugins={MARKDOWN_PLUGINS}
            components={getMarkdownComponents(skin)}
          >
            {displayText}
          </ReactMarkdown>
        )}
        {msg.isStreaming && (
          <span className={cn("inline-block w-1.5 h-3.5 ml-1 animate-pulse align-middle", isWhite ? "bg-cyan-600" : "bg-cyan-400")} />
        )}
      </div>

      {/* Assistant Message Actions (Copy / Like / Dislike / Info / Clear + Narrate / Skip stream) */}
      {!isUser && (
        <div className={cn("mt-2.5 pt-1.5 flex flex-col text-[10px]", isWhite ? "border-t border-slate-200 text-slate-600" : "border-t border-white/5 text-neutral-400")}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 select-none">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onCopyText(msg.id, msg.text);
                }}
                className={btnClass}
                title="Copy to clipboard"
              >
                {copiedId === msg.id ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFeedback(feedback === "up" ? null : "up");
                }}
                className={cn(btnClass, feedback === "up" && "!text-emerald-500 font-bold")}
                title="Thumbs up"
              >
                <ThumbsUp className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setFeedback(feedback === "down" ? null : "down");
                }}
                className={cn(btnClass, feedback === "down" && "!text-rose-500 font-bold")}
                title="Thumbs down"
              >
                <ThumbsDown className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowInfo(!showInfo);
                }}
                className={cn(btnClass, showInfo && (isWhite ? "!text-cyan-800" : "!text-cyan-400"))}
                title="Generation statistics"
              >
                <Info className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onClear(msg.id);
                }}
                className={cn(btnClass, "hover:!text-rose-500")}
                title="Clear this message"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>

            {msg.isStreaming ? (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onSkipStreaming(msg.id);
                }}
                className={cn("flex items-center gap-1 cursor-pointer font-medium", isWhite ? "text-cyan-700 hover:text-cyan-900" : "text-cyan-400 hover:text-cyan-200")}
              >
                <FastForward className="h-2.5 w-2.5" />
                <span>Skip stream</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  jarvisVoice.speak(msg.spokenText || msg.text, { engine: "neural" });
                }}
                className={cn("flex items-center gap-1 cursor-pointer transition-colors", isWhite ? "text-slate-600 hover:text-cyan-800" : "text-neutral-400 hover:text-cyan-300")}
              >
                <Volume2 className="h-3 w-3" />
                <span>Narrate</span>
              </button>
            )}
          </div>

          {showInfo && (
            <div className={cn("mt-1.5 p-2 rounded-lg border text-[10px] font-mono flex items-center gap-3 select-none", isWhite ? "bg-slate-100 border-slate-200 text-slate-700" : "bg-white/[0.03] border-white/5 text-neutral-400")}>
              <div>
                <span className={isWhite ? "text-slate-500" : "text-neutral-500"}>tokens (est.):</span>{" "}
                <span className={isWhite ? "text-fuchsia-700 font-bold" : "text-pink-400 font-medium"}>{estimatedTokens}</span>
              </div>
              {msg.latencyMs != null && (
                <>
                  <div className={cn("h-2 w-[1px]", isWhite ? "bg-slate-300" : "bg-white/10")} />
                  <div>
                    <span className={isWhite ? "text-slate-500" : "text-neutral-500"}>latency:</span>{" "}
                    <span className={isWhite ? "text-emerald-700 font-bold" : "text-emerald-400 font-medium"}>{(msg.latencyMs / 1000).toFixed(2)}s</span>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div
      className={cn("flex w-full items-start gap-2.5", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <div className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border shadow-sm mt-0.5",
          isWhite
            ? "border-cyan-600/40 bg-cyan-100 text-cyan-800"
            : "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
        )}>
          <Bot className="h-4 w-4" />
        </div>
      )}

      {bubbleContent}

      {isUser && (
        <div className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border mt-0.5",
          isWhite
            ? "border-slate-300 bg-slate-100 text-slate-700"
            : "border-white/10 bg-white/5 text-neutral-400"
        )}>
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
});

/* ══════════════════════════════════════════════════════════════════════
   MEMOIZED PROMPT COMPOSER: ISOLATES TYPING STATE (120FPS LAG-FREE)
   3X HEIGHT MULTI-LINE TEXTAREA + GEMINI-STYLE ACTIONS
   ══════════════════════════════════════════════════════════════════════ */

interface ZakiPromptComposerProps {
  onSendMessage: (text: string, files?: AttachedFileItem[]) => void;
  isThinking: boolean;
  stop: () => void;
  voiceTranscript: string | null;
  onClearVoiceTranscript: () => void;
  isLiveMode: boolean;
  toggleLiveMode: () => void;
  isMuted: boolean;
  isSpeaking: boolean;
  toggleMute: () => void;
  isWhiteSkin: boolean;
  isFullWindow: boolean;
  hasOperationalContext: boolean;
  scenarioId?: string;
}

const ZakiPromptComposer = React.memo(function ZakiPromptComposer({
  onSendMessage,
  isThinking,
  stop,
  voiceTranscript,
  onClearVoiceTranscript,
  isLiveMode,
  toggleLiveMode,
  isMuted,
  isSpeaking,
  toggleMute,
  isWhiteSkin,
  isFullWindow,
  hasOperationalContext,
  scenarioId,
}: ZakiPromptComposerProps) {
  const [inputText, setInputText] = useState("");
  const visibleInputText = voiceTranscript ?? inputText;
  const [attachedFiles, setAttachedFiles] = useState<AttachedFileItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Autocomplete state for '/' skills and '@' entity tags
  const [autocompleteMode, setAutocompleteMode] = useState<"/" | "@" | null>(null);
  const [autocompleteQuery, setAutocompleteQuery] = useState("");
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(0);

  const autocompleteItems = useMemo(() => {
    if (autocompleteMode === "/") {
      return SKILLS_CATALOG.filter(
        (s) =>
          s.trigger.toLowerCase().includes(autocompleteQuery) ||
          s.description.toLowerCase().includes(autocompleteQuery)
      );
    }
    if (autocompleteMode === "@") {
      return ENTITIES_CATALOG.filter(
        (e) =>
          e.trigger.toLowerCase().includes(autocompleteQuery) ||
          e.description.toLowerCase().includes(autocompleteQuery)
      );
    }
    return [];
  }, [autocompleteMode, autocompleteQuery]);

  const handleInputChange = (value: string) => {
    onClearVoiceTranscript();
    setInputText(value);
    const lastWord = value.split(/\s+/).pop() || "";
    if (lastWord.startsWith("/")) {
      setAutocompleteMode("/");
      setAutocompleteQuery(lastWord.slice(1).toLowerCase());
      setSelectedAutocompleteIndex(0);
    } else if (lastWord.startsWith("@")) {
      setAutocompleteMode("@");
      setAutocompleteQuery(lastWord.slice(1).toLowerCase());
      setSelectedAutocompleteIndex(0);
    } else {
      setAutocompleteMode(null);
      setAutocompleteQuery("");
    }
  };

  const insertAutocomplete = (token: string) => {
    const words = visibleInputText.split(/\s+/);
    words.pop();
    const updated = [...words, token, ""].join(" ");
    onClearVoiceTranscript();
    setInputText(updated);
    setAutocompleteMode(null);
    textareaRef.current?.focus();
  };

  const openAutocomplete = (mode: "/" | "@") => {
    setAutocompleteMode(mode);
    setAutocompleteQuery("");
    setSelectedAutocompleteIndex(0);
    setInputText(visibleInputText ? `${visibleInputText.trim()} ${mode}` : mode);
    onClearVoiceTranscript();
    textareaRef.current?.focus();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const newItems: AttachedFileItem[] = Array.from(files).map((f) => ({
      id: `file-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name: f.name,
      size: f.size > 1024 * 1024 ? `${(f.size / (1024 * 1024)).toFixed(1)} MB` : `${Math.ceil(f.size / 1024)} KB`,
      type: f.name.endsWith(".pcap") || f.name.endsWith(".pcapng") ? "pcap" : f.type || "file",
    }));
    setAttachedFiles((prev) => [...prev, ...newItems]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeAttachedFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleSubmit = () => {
    const trimmed = visibleInputText.trim();
    if ((!trimmed && attachedFiles.length === 0) || isThinking) return;
    onSendMessage(trimmed, attachedFiles);
    onClearVoiceTranscript();
    setInputText("");
    setAttachedFiles([]);
    setAutocompleteMode(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (autocompleteMode && autocompleteItems.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedAutocompleteIndex((prev) => (prev + 1) % autocompleteItems.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedAutocompleteIndex((prev) => (prev - 1 + autocompleteItems.length) % autocompleteItems.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        const selected = autocompleteItems[selectedAutocompleteIndex];
        if (selected) {
          insertAutocomplete(selected.trigger);
        }
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setAutocompleteMode(null);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={cn("p-3 shrink-0 transition-colors relative", isWhiteSkin ? "border-t border-slate-200 bg-slate-50/90" : "border-t border-white/10 bg-white/[0.02]")}>
      <div className={cn("relative", isFullWindow && "max-w-[1560px] mx-auto w-full")}>

        {/* Autocomplete Popup Menu */}
        {autocompleteMode && autocompleteItems.length > 0 && (
          <div className={cn(
            "absolute bottom-full left-0 mb-2 w-full max-w-md rounded-xl border shadow-2xl backdrop-blur-2xl z-50 overflow-hidden animate-fade-in",
            isWhiteSkin
              ? "bg-white/98 border-slate-300 text-slate-900 shadow-slate-300/50"
              : "bg-[#09152e]/98 border-cyan-500/30 text-white shadow-[0_0_30px_rgba(0,0,0,0.85)]"
          )}>
            <div className={cn(
              "flex items-center justify-between px-3 py-1.5 border-b text-[10px] font-mono",
              isWhiteSkin ? "border-slate-200 bg-slate-50 text-slate-500" : "border-white/10 bg-black/40 text-neutral-400"
            )}>
              <span className="flex items-center gap-1 font-bold uppercase tracking-wider">
                {autocompleteMode === "/" ? (
                  <>
                    <Terminal className="h-3 w-3 text-cyan-400" /> Operational Skills Catalog
                  </>
                ) : (
                  <>
                    <AtSign className="h-3 w-3 text-fuchsia-400" /> Tag Network Entities & Files
                  </>
                )}
              </span>
              <span className="text-[9px]">↑↓ navigate • ↵ tab insert • esc close</span>
            </div>

            <div className="max-h-52 overflow-y-auto p-1 space-y-0.5">
              {autocompleteItems.map((item, idx) => {
                const isSelected = idx === selectedAutocompleteIndex;
                return (
                  <button
                    key={idx}
                    type="button"
                    onMouseEnter={() => setSelectedAutocompleteIndex(idx)}
                    onClick={() => insertAutocomplete(item.trigger)}
                    className={cn(
                      "w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between transition-all cursor-pointer font-sans",
                      isSelected
                        ? isWhiteSkin
                          ? "bg-cyan-50 text-cyan-900 font-medium border border-cyan-200"
                          : "bg-cyan-500/20 text-cyan-200 border border-cyan-500/40 shadow-sm"
                        : isWhiteSkin
                        ? "hover:bg-slate-100 text-slate-700"
                        : "hover:bg-white/5 text-neutral-300"
                    )}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="shrink-0 text-sm">{(item as any).icon || (autocompleteMode === "/" ? "⚡" : "🏷️")}</span>
                      <div className="min-w-0">
                        <span className={cn(
                          "font-mono font-bold text-xs tracking-tight",
                          autocompleteMode === "/"
                            ? (isWhiteSkin ? "text-cyan-800" : "text-cyan-400")
                            : (isWhiteSkin ? "text-fuchsia-700 font-bold" : "text-fuchsia-400")
                        )}>
                          {item.label}
                        </span>
                        <p className={cn("text-[10px] truncate leading-tight mt-0.5", isWhiteSkin ? "text-slate-500" : "text-neutral-400")}>
                          {item.description}
                        </p>
                      </div>
                    </div>
                    {("category" in item) && (
                      <span className={cn(
                        "text-[9px] font-mono px-1.5 py-0.2 rounded shrink-0 ml-2 border",
                        isWhiteSkin ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-white/5 border-white/10 text-neutral-400"
                      )}>
                        {(item as any).category}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ── UNIFIED 3X PROMPT COMPOSER CARD (AVOIDING GAPS) ── */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className={cn(
            "rounded-2xl border transition-all p-3 flex flex-col justify-between shadow-xs",
            isWhiteSkin
              ? "border-slate-300 bg-white focus-within:border-cyan-600 focus-within:ring-1 focus-within:ring-cyan-500/20 shadow-sm"
              : "border-white/10 bg-white/5 focus-within:border-cyan-500/40 focus-within:bg-black/40"
          )}
        >
          {/* Prompt Textarea: 3x height */}
          <textarea
            ref={textareaRef}
            rows={3}
            value={visibleInputText}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isLiveMode
                ? "Speak naturally or ask about operational telemetry (or type / or @)..."
                : hasOperationalContext
                ? "Ask Zaki about operational telemetry, causal graph, blast radius (type / or @)... [Shift+Enter for newline]"
                : "Ask Zaki or select a scenario (type / for skills, @ for entities)... [Shift+Enter for newline]"
            }
            disabled={isThinking}
            className={cn(
              "w-full bg-transparent border-0 p-0 text-xs focus:outline-none focus:ring-0 resize-none min-h-[64px] leading-relaxed",
              isWhiteSkin ? "text-slate-900 placeholder:text-slate-400" : "text-white placeholder:text-neutral-500"
            )}
          />

          {/* Attached Files Chips */}
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 py-1.5 border-t border-white/5 mt-1">
              {attachedFiles.map((f) => (
                <div
                  key={f.id}
                  className={cn(
                    "flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono border shadow-xs animate-fade-in",
                    isWhiteSkin
                      ? "bg-white border-slate-300 text-slate-800"
                      : "bg-cyan-950/40 border-cyan-500/30 text-cyan-200"
                  )}
                >
                  <Paperclip className="h-3 w-3 text-cyan-400 shrink-0" />
                  <span className="font-semibold truncate max-w-[160px]">{f.name}</span>
                  <span className="text-[10px] text-slate-400">({f.size})</span>
                  <button
                    type="button"
                    onClick={() => removeAttachedFile(f.id)}
                    className="p-0.5 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors ml-0.5 cursor-pointer"
                    title="Remove attachment"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* ── UNIFIED TOOLBAR: ACTIONS ON LEFT, MIC/SPEAKER/SEND FLUSH ON RIGHT ── */}
          <div className={cn(
            "flex items-center justify-between pt-2 mt-1.5 border-t text-[11px]",
            isWhiteSkin ? "border-slate-200" : "border-white/5"
          )}>
            {/* Left: Upload, Skills, Mentions */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="hidden"
                onChange={handleFileSelect}
                accept=".pcap,.pcapng,.json,.csv,.log,.txt,.yaml,.yml,.pdf"
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                title="Upload PCAP network trace, Telemetry CSV, Topology JSON, or incident logs"
                className={cn(
                  "flex items-center gap-1 px-2.5 py-1 rounded-lg border transition-all cursor-pointer font-medium select-none",
                  isWhiteSkin
                    ? "border-slate-300 bg-white hover:bg-cyan-50 hover:border-cyan-500 text-slate-700 hover:text-cyan-800 shadow-xs"
                    : "border-white/10 bg-white/5 hover:bg-cyan-500/10 hover:border-cyan-400/50 text-neutral-300 hover:text-white"
                )}
              >
                <Plus className="h-3.5 w-3.5 text-cyan-400 font-bold" />
                <span>Upload</span>
              </button>

              <button
                type="button"
                onClick={() => openAutocomplete("/")}
                title="Select operational skill (/diagnose, /mitigate, /correlate, /blast-radius...)"
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded-lg border transition-all cursor-pointer font-mono select-none",
                  isWhiteSkin
                    ? "border-slate-300 bg-white hover:bg-cyan-50 hover:border-cyan-500 text-slate-600 hover:text-cyan-800 shadow-xs"
                    : "border-white/10 bg-white/5 hover:bg-cyan-500/10 hover:border-cyan-400/50 text-neutral-400 hover:text-cyan-300"
                )}
              >
                <Terminal className="h-3 w-3 text-cyan-400" />
                <span>/ Skills</span>
              </button>

              <button
                type="button"
                onClick={() => openAutocomplete("@")}
                title="Tag a network component or trace file (@UPF-003, @PE-RTR-21, @trace.pcap...)"
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded-lg border transition-all cursor-pointer font-mono select-none",
                  isWhiteSkin
                    ? "border-slate-300 bg-white hover:bg-fuchsia-50 hover:border-fuchsia-400 text-slate-600 hover:text-fuchsia-800 shadow-xs"
                    : "border-white/10 bg-white/5 hover:bg-fuchsia-500/10 hover:border-fuchsia-400/50 text-neutral-400 hover:text-fuchsia-300"
                )}
              >
                <AtSign className="h-3 w-3 text-fuchsia-400" />
                <span>@ Mentions</span>
              </button>

              {/* Voice status */}
              {isSpeaking && (
                <div className="flex items-center gap-1 text-cyan-400 ml-1">
                  <Radio className="h-3 w-3 animate-pulse" />
                  <span className="font-mono text-[10px] hidden sm:inline">Soft Voice</span>
                </div>
              )}
            </div>

            {/* Right: Mic, Speaker, Send (Flush with prompt, zero gaps) */}
            <div className="flex items-center gap-1.5 shrink-0">
              {/* Mic Button */}
              <button
                type="button"
                onClick={toggleLiveMode}
                title={isLiveMode ? "Microphone ON (Active) — Click to mute/disconnect" : "Microphone OFF — Click to connect voice"}
                aria-label={isLiveMode ? "Microphone ON" : "Microphone OFF"}
                className={cn(
                  "h-8 w-8 flex items-center justify-center rounded-xl border transition-all cursor-pointer",
                  isLiveMode
                    ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.45)] animate-pulse"
                    : isWhiteSkin
                    ? "border-slate-300 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10 hover:border-white/20"
                )}
              >
                {isLiveMode ? <Mic className="h-3.5 w-3.5" /> : <MicOff className="h-3.5 w-3.5" />}
              </button>

              {/* Speaker / Mute Button */}
              <button
                type="button"
                onClick={toggleMute}
                title={isMuted ? "Speaker Muted — Click to unmute" : "Speaker Active (Soft Young Male) — Click to mute"}
                aria-label={isMuted ? "Unmute speaker" : "Mute speaker"}
                className={cn(
                  "h-8 w-8 flex items-center justify-center rounded-xl border transition-all cursor-pointer",
                  isMuted
                    ? "border-rose-500/30 bg-rose-500/20 text-rose-500"
                    : isSpeaking
                    ? "border-cyan-500/40 bg-cyan-500/20 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.3)] animate-pulse"
                    : isWhiteSkin
                    ? "border-slate-300 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    : "border-white/10 bg-white/5 text-neutral-300 hover:text-white hover:bg-white/10"
                )}
              >
                {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
              </button>

              {/* Send / Stop Button */}
              <Button
                type={isThinking ? "button" : "submit"}
                onClick={isThinking ? stop : undefined}
                size="icon"
                disabled={!isThinking && !inputText.trim() && attachedFiles.length === 0}
                className={cn(
                  "h-8 w-8 rounded-xl transition-all duration-300 shrink-0 cursor-pointer",
                  isThinking
                    ? "bg-rose-500 hover:bg-rose-600 text-white"
                    : "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-md shadow-cyan-500/20 disabled:opacity-40"
                )}
                title={isThinking ? "Stop analysis / speaking" : "Send query (Enter)"}
              >
                {isThinking ? (
                  <Square className="h-3.5 w-3.5 fill-current" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
});

export interface ZakiVoiceFABProps {
  runId?: string;
  scenarioId?: string;
  stageIndex?: number;
  simulationStatus?: string;
  className?: string;
  onMessageSubmit?: (text: string) => Promise<ZakiSubmitReply | void>;
  onResponse?: (answer: string, spoken?: string) => void;
  suggestedPrompts?: string[];
  anchorQuestion?: string;
  initialExpanded?: boolean;
  initialFullWindow?: boolean;
  simulationState?: any;
}

export function ZakiVoiceFAB({
  runId,
  scenarioId,
  stageIndex,
  simulationStatus,
  className,
  onMessageSubmit,
  onResponse,
  suggestedPrompts,
  anchorQuestion,
  initialExpanded = false,
  initialFullWindow = false,
  simulationState,
}: ZakiVoiceFABProps) {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [isFullWindow, setIsFullWindow] = useState(initialFullWindow);
  const [isThinking, setIsThinking] = useState(false);
  // Default message removed: initialized to empty array
  const [messages, setMessages] = useState<ZakiChatMessage[]>([]);
  const [voiceTranscript, setVoiceTranscript] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [leftW, setLeftW] = useState(365);
  const [rightW, setRightW] = useState(390);
  const [skin, setSkin] = useState<ZakiSkin>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("zaki_skin") as ZakiSkin;
      if (saved === "glass-morphic" || saved === "liquid-glass" || saved === "white") {
        return saved;
      }
    }
    return "glass-morphic";
  });

  const handleSetSkin = (newSkin: ZakiSkin) => {
    setSkin(newSkin);
    if (typeof window !== "undefined") {
      localStorage.setItem("zaki_skin", newSkin);
    }
  };

  const isWhiteSkin = skin === "white";
  const isLiquidSkin = skin === "liquid-glass";

  // Derive latest active storyteller payload from message stream
  const activeStoryteller = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].storyteller) return messages[i].storyteller;
    }
    return undefined;
  }, [messages]);

  const estimatedTokens = useMemo(() => {
    return messages.reduce((acc, m) => acc + Math.round((m.text?.length || 0) / 4), 0);
  }, [messages]);

  const latestLatency = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].latencyMs !== undefined) return messages[i].latencyMs;
    }
    return undefined;
  }, [messages]);

  // Listen for Escape key to exit full window mode or close expanded view
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isFullWindow) {
          setIsFullWindow(false);
        } else if (isExpanded) {
          setIsExpanded(false);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFullWindow, isExpanded]);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const streamingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Scroll to bottom helper (instant layout scroll avoids queuing browser physics)
  const scrollToBottom = useCallback((smooth = false) => {
    if (scrollContainerRef.current) {
      if (smooth) {
        scrollContainerRef.current.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: "smooth",
        });
      } else {
        scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
      }
    } else {
      messagesEndRef.current?.scrollIntoView({ behavior: smooth ? "smooth" : "auto" });
    }
  }, []);

  const scrollRafRef = useRef<number | null>(null);

  // Cleanup streaming timer and scroll RAF on unmount
  useEffect(() => {
    return () => {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current);
        streamingTimerRef.current = null;
      }
      if (scrollRafRef.current) {
        cancelAnimationFrame(scrollRafRef.current);
        scrollRafRef.current = null;
      }
    };
  }, []);

  // Progressively stream text with word-boundary snapping and constant velocity
  const startStreaming = useCallback((messageId: string, fullText: string) => {
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current);
      streamingTimerRef.current = null;
    }
    if (scrollRafRef.current) {
      cancelAnimationFrame(scrollRafRef.current);
      scrollRafRef.current = null;
    }

    // Immediately mark any older streaming messages as completed
    setMessages((prev) =>
      prev.map((msg) =>
        msg.isStreaming && msg.id !== messageId
          ? { ...msg, isStreaming: false, streamedLength: msg.text.length }
          : msg
      )
    );

    let currentLength = 0;
    const totalLength = fullText.length;
    // Target ~26-30 smooth frames total (~0.9s - 1.2s total duration)
    const targetFrames = 28;
    const baseStep = Math.max(8, Math.ceil(totalLength / targetFrames));

    streamingTimerRef.current = setInterval(() => {
      let nextLength = currentLength + baseStep;
      if (nextLength < totalLength) {
        // Snap to nearest space/newline to prevent parsing fragmented markdown tokens
        const spaceIdx = fullText.indexOf(" ", nextLength);
        if (spaceIdx !== -1 && spaceIdx - currentLength <= baseStep * 1.6) {
          nextLength = spaceIdx + 1;
        }
      }

      currentLength = Math.min(nextLength, totalLength);
      const isDone = currentLength >= totalLength;

      if (isDone) {
        currentLength = totalLength;
        if (streamingTimerRef.current) {
          clearInterval(streamingTimerRef.current);
          streamingTimerRef.current = null;
        }
      }

      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id !== messageId) return msg;
          return {
            ...msg,
            streamedLength: currentLength,
            isStreaming: !isDone,
          };
        })
      );

      // Decoupled layout scroll via requestAnimationFrame (prevents synchronous layout thrashing)
      if (scrollContainerRef.current && !scrollRafRef.current) {
        scrollRafRef.current = requestAnimationFrame(() => {
          if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
          }
          scrollRafRef.current = null;
        });
      }
    }, 30);
  }, []);

  // Skip streaming immediately
  const skipStreaming = useCallback((messageId: string) => {
    if (streamingTimerRef.current) {
      clearInterval(streamingTimerRef.current);
      streamingTimerRef.current = null;
    }
    if (scrollRafRef.current) {
      cancelAnimationFrame(scrollRafRef.current);
      scrollRafRef.current = null;
    }
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId
          ? { ...msg, streamedLength: msg.text.length, isStreaming: false }
          : msg
      )
    );
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, []);

  // Voice hook integration
  const {
    voiceState,
    isLiveMode,
    isSpeaking,
    isListening,
    isPaused,
    isMuted,
    playbackRate,
    setPlaybackRate,
    lastSpokenAnswer,
    toggleLiveMode,
    stop,
    toggleMute,
  } = useMarkVoice({
    runId,
    scenarioId,
    simulationStatus,
    onMessageSubmit,
    onTranscript: (text) => setVoiceTranscript(text),
    onResponse: (answer, spoken) => {
      setVoiceTranscript(null);
      onResponse?.(answer, spoken);
    },
  });

  const cycleSpeed = () => {
    const current = playbackRate || 1.0;
    let next = 1.0;
    if (Math.abs(current - 1.0) < 0.05) next = 1.25;
    else if (Math.abs(current - 1.25) < 0.05) next = 0.85;
    else next = 1.0;
    setPlaybackRate(next);
  };

  // Whenever a new spoken answer arrives from voice hook, stream it if it's not already in messages
  useEffect(() => {
    if (!lastSpokenAnswer) return;
    const exists = messagesRef.current.some((m) => m.text === lastSpokenAnswer);
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
  }, [lastSpokenAnswer, startStreaming]);

  // Handle user submitting message (typed or prompt clicked)
  const handleSendMessage = useCallback(async (textToSend: string, files?: AttachedFileItem[]) => {
    const trimmed = textToSend.trim();
    const filesToUse = files && files.length > 0 ? files : [];
    if ((!trimmed && filesToUse.length === 0) || isThinking) return;

    let displayUserText = trimmed;
    if (filesToUse.length > 0) {
      const fileBadge = `📎 [${filesToUse.map((f) => `${f.name} (${f.size})`).join(", ")}]`;
      displayUserText = trimmed ? `${trimmed}\n\n${fileBadge}` : `Analyze uploaded file(s): ${filesToUse.map((f) => `${f.name} (${f.size})`).join(", ")}`;
    }

    const userMsgId = `user-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: "user",
        text: displayUserText,
      },
    ]);
    setIsThinking(true);

    try {
      let reply: ZakiSubmitReply | void = undefined;
      const startedAt = Date.now();
      if (onMessageSubmit) {
        reply = await onMessageSubmit(displayUserText);
      }
      const elapsedMs = Date.now() - startedAt;

      let answerText = "Simulation telemetry synchronized. Awaiting next diagnostic inquiry.";
      let spokenText = answerText;
      let storyteller: ZakiChatMessage["storyteller"] = undefined;
      let latencyMs: number | undefined = elapsedMs;

      if (typeof reply === "string" && reply.trim()) {
        answerText = reply;
        spokenText = reply;
      } else if (reply && typeof reply === "object" && reply.text) {
        answerText = reply.text;
        spokenText = reply.spokenText || reply.text;
        storyteller = reply.storyteller || undefined;
        latencyMs = reply.latencyMs ?? elapsedMs;
      }

      const assistantId = `zaki-${Date.now()}`;

      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          sender: "zaki",
          text: answerText,
          spokenText: spokenText,
          isStreaming: true,
          streamedLength: 0,
          storyteller,
          latencyMs,
        },
      ]);

      startStreaming(assistantId, answerText);

      // Auto-narrate response with natural empathetic co-pilot dialogue (NO raw document readout!)
      if (!isMuted && typeof window !== "undefined") {
        jarvisVoice.speak(spokenText, { engine: "neural" });
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
  }, [isThinking, isMuted, onMessageSubmit, startStreaming]);

  const handleCopyText = useCallback((id: string, text: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  }, []);

  const handleClearMessage = useCallback((id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  // Smooth scroll ONLY when a new message is submitted/received or thinking state changes
  const prevMessagesCountRef = useRef(messages.length);
  useEffect(() => {
    if (messages.length > prevMessagesCountRef.current || isThinking) {
      scrollToBottom(true);
      prevMessagesCountRef.current = messages.length;
    }
  }, [messages.length, isThinking, scrollToBottom]);

  const getStatusLabel = () => {
    if (isPaused) return "Paused";
    if (voiceState === "listening" || isListening) return "Listening to voice input...";
    if (voiceState === "processing" || isThinking) return "Correlating causal graph & telemetry...";
    if (voiceState === "speaking" || isSpeaking) return "Speaking response...";
    if (isLiveMode) return "Full-Duplex Audio Active";
    return scenarioId ? `Monitoring ${scenarioId}` : "Awaiting Operational Context";
  };

  const getOrbRingColor = () => {
    if (isSpeaking) return "border-cyan-400 bg-cyan-500/20 shadow-cyan-400/40";
    if (isListening) return "border-emerald-400 bg-emerald-500/20 shadow-emerald-400/40";
    if (voiceState === "processing" || isThinking) return "border-purple-400 bg-purple-500/20 shadow-purple-400/40";
    if (isLiveMode) return "border-cyan-400/60 bg-cyan-950/60 shadow-[0_0_12px_rgba(6,182,212,0.3)]";
    return "border-white/15 bg-slate-900/80 hover:border-cyan-400/40";
  };

  // Check if operational context currently exists
  const hasOperationalContext = Boolean(scenarioId || (suggestedPrompts && suggestedPrompts.length > 0) || anchorQuestion);

  // ---------------------------------------------------------------------------
  // Collapsed Floating Button View (Positioned on the Right, Always on Top)
  // ---------------------------------------------------------------------------
  if (!isExpanded) {
    return (
      <div className={cn("fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[9999] transition-all duration-300", className)}>
        <button
          type="button"
          onClick={() => {
            setIsExpanded(true);
            if (!isLiveMode) toggleLiveMode();
          }}
          className={cn(
            "flex items-center gap-3 rounded-full px-4 py-2.5 text-xs font-medium shadow-2xl backdrop-blur-xl border transition-all hover:scale-105 cursor-pointer",
            isWhiteSkin
              ? isLiveMode
                ? "border-cyan-500 bg-white/95 text-slate-900 shadow-[0_0_25px_rgba(6,182,212,0.25)]"
                : "border-slate-300 bg-white/95 text-slate-800 hover:border-cyan-500 shadow-slate-300/50"
              : isLiquidSkin
              ? isLiveMode
                ? "border-cyan-400 bg-cyan-950/80 text-white shadow-[0_0_25px_rgba(6,182,212,0.45)] backdrop-blur-2xl"
                : "border-cyan-500/30 bg-[#071530]/85 text-white hover:border-cyan-400/50 shadow-black/50"
              : isLiveMode
              ? "border-cyan-400/60 bg-slate-950/90 text-white shadow-[0_0_25px_rgba(6,182,212,0.35)]"
              : "border-white/15 bg-slate-900/85 text-white hover:border-cyan-500/30 shadow-black/50"
          )}
        >
          {/* Animated Core Orb */}
          <div className="relative flex items-center justify-center">
            <div
              className={cn(
                "h-7 w-7 rounded-full border flex items-center justify-center transition-all",
                isWhiteSkin
                  ? isSpeaking
                    ? "border-cyan-500 bg-cyan-100 shadow-cyan-400/30"
                    : isListening
                    ? "border-emerald-500 bg-emerald-100 shadow-emerald-400/30"
                    : "border-slate-300 bg-slate-100"
                  : getOrbRingColor()
              )}
            >
              {isMuted ? (
                <MicOff className={cn("h-3.5 w-3.5", isWhiteSkin ? "text-rose-600" : "text-rose-400")} />
              ) : isSpeaking ? (
                <Radio className={cn("h-3.5 w-3.5 animate-pulse", isWhiteSkin ? "text-cyan-700" : "text-cyan-300")} />
              ) : (
                <Bot className={cn("h-3.5 w-3.5", isWhiteSkin ? "text-cyan-700" : "text-cyan-300")} />
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
              <span className={cn("font-bold text-xs tracking-wide", isWhiteSkin ? "text-slate-900" : "text-white")}>ZAKI</span>
              {isLiveMode && (
                <span className={cn(
                  "rounded-full px-1.5 py-0.2 text-[9px] font-mono uppercase",
                  isWhiteSkin ? "bg-cyan-100 text-cyan-800 border border-cyan-300" : "bg-cyan-500/20 text-cyan-300"
                )}>
                  LIVE
                </span>
              )}
            </div>
            <p className={cn("text-[10px] leading-none mt-0.5", isWhiteSkin ? "text-slate-500" : "text-neutral-400")}>{getStatusLabel()}</p>
          </div>

          <ChevronUp className={cn("h-3.5 w-3.5 ml-1", isWhiteSkin ? "text-slate-500" : "text-neutral-400")} />
        </button>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Expanded Unified Voice & Chat Copilot (Inspired by ChatPanel.tsx Design)
  // Always on Top (z-[9999]), clamped to viewport boundaries
  // ---------------------------------------------------------------------------
  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4 md:p-6 bg-black/60 backdrop-blur-sm transition-all duration-300 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          setIsExpanded(false);
          setIsFullWindow(false);
        }
      }}
    >
      <div
        className={cn(
          "relative flex flex-col overflow-hidden text-xs transition-all duration-300",
          isWhiteSkin
            ? "text-slate-800 bg-white/98 border border-slate-300 shadow-[0_25px_80px_rgba(0,0,0,0.25)] light-theme"
            : isLiquidSkin
            ? "text-neutral-200 bg-[#06142e]/92 border border-cyan-400/40 backdrop-blur-3xl shadow-[0_25px_90px_rgba(0,0,0,0.9),0_0_50px_rgba(6,182,212,0.35)] liquid-glass-theme"
            : "text-neutral-200 bg-[#070f22]/98 border border-cyan-500/30 backdrop-blur-2xl shadow-[0_25px_80px_rgba(0,0,0,0.85),0_0_45px_rgba(6,182,212,0.25)] glassmorphic-theme",
          isFullWindow
            ? "w-full h-full max-w-none max-h-none rounded-none sm:rounded-2xl"
            : "w-[min(1580px,calc(100vw-1.5rem))] h-[min(940px,calc(100dvh-2rem))] rounded-2xl",
          className
        )}
      >
      {/* ── TOP HEADER (Inspired by ChatPanel Header Bar) ── */}
      <div className={cn(
        "flex items-center justify-between px-4 py-3 shrink-0 gap-3 transition-colors",
        isWhiteSkin
          ? "border-b border-slate-200 bg-slate-50/90 text-slate-800"
          : "border-b border-white/10 bg-white/[0.02] text-neutral-200"
      )}>
        <div className="flex items-center gap-2.5 min-w-0">
          <div className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border shadow-sm",
            isWhiteSkin
              ? "border-cyan-600/40 bg-cyan-100 text-cyan-800"
              : "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_12px_rgba(0,229,255,0.25)]"
          )}>
            <Bot className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn("font-bold text-xs tracking-wide", isWhiteSkin ? "text-slate-900" : "text-white")}>
                ZAKI Copilot
              </span>
              <Badge variant={isLiveMode ? "default" : "muted"} className="text-[9px] py-0 px-2 font-mono">
                {isLiveMode ? "Full-Duplex" : "Standby"}
              </Badge>
              {scenarioId ? (
                <span className={cn(
                  "truncate rounded-md px-1.5 py-0.2 font-mono text-[9px] font-bold border",
                  isWhiteSkin
                    ? "border-cyan-300 bg-cyan-50 text-cyan-800"
                    : "border-cyan-500/30 bg-cyan-500/10 text-cyan-300"
                )}>
                  {scenarioId}
                </span>
              ) : (
                <span className={cn(
                  "rounded-md px-1.5 py-0.2 font-mono text-[9px] border",
                  isWhiteSkin ? "border-slate-300 bg-slate-100 text-slate-500" : "border-white/10 bg-white/5 text-neutral-400"
                )}>
                  No Context
                </span>
              )}
            </div>
            <p className={cn("text-[10px] truncate mt-0.5", isWhiteSkin ? "text-slate-500" : "text-neutral-400")}>{getStatusLabel()}</p>
          </div>
        </div>

        {/* Right Header Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Skin Selector: Minimalist Icons Only (No Text) */}
          <div className={cn(
            "flex items-center rounded-lg p-0.5 border text-xs gap-0.5",
            isWhiteSkin ? "bg-slate-100 border-slate-300 text-slate-600" : "bg-black/40 border-white/10 text-neutral-400"
          )}>
            <button
              type="button"
              onClick={() => handleSetSkin("glass-morphic")}
              className={cn(
                "h-6 w-6 rounded flex items-center justify-center transition-all cursor-pointer text-xs",
                skin === "glass-morphic"
                  ? (isWhiteSkin ? "bg-white text-cyan-800 shadow-sm border border-slate-200" : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.3)]")
                  : (isWhiteSkin ? "hover:text-slate-900" : "hover:text-neutral-200")
              )}
              title="Glass-morphic (Dark Frosted Glass)"
              aria-label="Glass-morphic skin"
            >
              <span>💎</span>
            </button>
            <button
              type="button"
              onClick={() => handleSetSkin("liquid-glass")}
              className={cn(
                "h-6 w-6 rounded flex items-center justify-center transition-all cursor-pointer text-xs",
                skin === "liquid-glass"
                  ? (isWhiteSkin ? "bg-white text-cyan-800 shadow-sm border border-slate-200" : "bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 shadow-[0_0_12px_rgba(6,182,212,0.4)]")
                  : (isWhiteSkin ? "hover:text-slate-900" : "hover:text-neutral-200")
              )}
              title="Liquid Glass (Refractive Fluid Glass)"
              aria-label="Liquid Glass skin"
            >
              <span>💧</span>
            </button>
            <button
              type="button"
              onClick={() => handleSetSkin("white")}
              className={cn(
                "h-6 w-6 rounded flex items-center justify-center transition-all cursor-pointer text-xs",
                skin === "white"
                  ? "bg-white text-slate-900 border border-slate-300 shadow-sm"
                  : (isWhiteSkin ? "hover:text-slate-900" : "hover:text-neutral-200")
              )}
              title="White Theme (Crisp High-Contrast White)"
              aria-label="White skin"
            >
              <span>⚪</span>
            </button>
          </div>

          <button
            type="button"
            onClick={cycleSpeed}
            title={`Speech speed: ${(playbackRate || 1.0).toFixed(2).replace(/\.00$/, "")}x (Click to cycle)`}
            className={cn(
              "rounded-lg px-2 py-1 font-mono text-[10px] font-semibold cursor-pointer transition-colors border",
              isWhiteSkin
                ? "bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300"
                : "bg-white/5 hover:bg-white/10 text-neutral-300 border-white/10"
            )}
          >
            {(playbackRate || 1.0).toFixed(2).replace(/\.00$/, "")}x
          </button>

          {/* Full Window / Restore A4 Toggle Button */}
          <button
            type="button"
            onClick={() => setIsFullWindow((prev) => !prev)}
            className={cn(
              "rounded-lg p-1.5 transition-colors cursor-pointer",
              isWhiteSkin ? "text-slate-600 hover:bg-slate-100 hover:text-cyan-800" : "text-neutral-400 hover:bg-white/10 hover:text-cyan-300"
            )}
            title={isFullWindow ? "Restore A4 center view (Esc)" : "Expand to full screen"}
            aria-label={isFullWindow ? "Restore A4 center view" : "Expand to full screen"}
          >
            {isFullWindow ? (
              <Minimize2 className={cn("h-4 w-4", isWhiteSkin ? "text-cyan-800" : "text-cyan-300")} />
            ) : (
              <Maximize2 className={cn("h-4 w-4", isWhiteSkin ? "text-slate-700 hover:text-cyan-800" : "text-neutral-300 hover:text-cyan-300")} />
            )}
          </button>

          {/* Minimize Button */}
          <button
            type="button"
            onClick={() => {
              setIsExpanded(false);
              setIsFullWindow(false);
            }}
            className={cn(
              "rounded-lg p-1.5 transition-colors cursor-pointer",
              isWhiteSkin ? "text-slate-600 hover:bg-slate-100 hover:text-slate-900" : "text-neutral-400 hover:bg-white/10 hover:text-white"
            )}
            title="Minimize to floating orb (Esc)"
            aria-label="Minimize"
          >
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Waveform indicator when listening/speaking */}
      {isLiveMode && (
        <div className={cn(
          "flex items-center justify-center gap-1 py-1.5 border-b",
          isWhiteSkin ? "bg-cyan-50/70 border-cyan-200" : "bg-cyan-950/20 border-cyan-500/10"
        )}>
          {[4, 10, 16, 8, 14, 20, 12, 6, 18, 10, 4].map((h, i) => (
            <span
              key={i}
              className={cn(
                "w-1 rounded-full transition-all duration-150",
                isSpeaking
                  ? (isWhiteSkin ? "bg-cyan-600 animate-pulse" : "bg-cyan-400 animate-pulse")
                  : isListening
                  ? (isWhiteSkin ? "bg-emerald-600 animate-pulse" : "bg-emerald-400 animate-pulse")
                  : (isWhiteSkin ? "bg-slate-300" : "bg-white/20")
              )}
              style={{
                height: isSpeaking || isListening ? `${h}px` : "4px",
                animationDelay: `${i * 60}ms`,
              }}
            />
          ))}
          <span className={cn("text-[10px] font-mono ml-2", isWhiteSkin ? "text-cyan-800" : "text-cyan-300")}>
            {isSpeaking ? "Voice Out" : isListening ? "Voice In" : "Duplex Ready"}
          </span>
        </div>
      )}

      {/* ── 3-PANEL COCKPIT BODY ── */}
      <div className="flex flex-1 min-h-0 overflow-hidden w-full">
        {/* LEFT PANEL: Sections 1, 2, 3 (Fixed size) */}
        <div
          style={{ width: `${leftW}px` }}
          className={cn(
            "hidden md:flex shrink-0 h-full overflow-hidden flex-col",
            isWhiteSkin
              ? "border-r border-slate-200 bg-slate-50/95"
              : isLiquidSkin
              ? "border-r border-cyan-500/20 bg-[#051124]/90"
              : "border-r border-white/10 bg-[#06111f]/95"
          )}
        >
          <StorytellerLeftPanel
            payload={activeStoryteller}
            simulationState={simulationState}
            scenarioId={scenarioId}
            stageIndex={stageIndex}
            className={isWhiteSkin ? "light-theme" : undefined}
            onNewChat={() => {
              stop();
              setMessages([]);
            }}
          />
        </div>

        {/* Sleek Vertical Splitter */}
        <VerticalSplitter onDrag={(dx) => setLeftW((w) => Math.min(440, Math.max(260, w + dx)))} />

        {/* CENTER PANEL: Section 5 — Zaki Chat UI (Fixed size flex-1, ONLY THIS SCROLLS) */}
        <div className={cn(
          "flex-1 min-w-[380px] flex flex-col h-full overflow-hidden",
          isWhiteSkin ? "bg-slate-100/60" : "bg-black/20"
        )}>
          {/* ── MESSAGES CONTAINER (Scrollable Area) ── */}
          <div
            ref={scrollContainerRef}
            className={cn(
              "flex-1 overflow-y-auto overflow-x-hidden p-4 space-y-4 min-h-0 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent",
              isWhiteSkin
                ? "[&::-webkit-scrollbar-thumb]:bg-slate-300 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-slate-400"
                : "[&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30"
            )}
          >
        <div className={cn("space-y-4 w-full", isFullWindow && "max-w-[1560px] mx-auto")}>
          {/* EMPTY STATE (When no messages exist yet) - Inspired by ChatPanel Hero */}
          {messages.length === 0 && !isThinking && (
            <div className="flex flex-col items-center justify-center text-center py-6 px-3">
              <div className={cn(
                "flex h-12 w-12 items-center justify-center rounded-2xl border mb-3 shadow-sm",
                isWhiteSkin
                  ? "border-cyan-600/40 bg-cyan-100 text-cyan-800"
                  : "border-cyan-500/30 bg-cyan-500/10 text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.2)]"
              )}>
                <Brain className="h-6 w-6 animate-pulse" />
              </div>
              <h3 className={cn("text-base font-semibold mb-1", isWhiteSkin ? "text-slate-900" : "text-white")}>
                ZAKI 
              </h3>
              <p className={cn("text-xs max-w-sm leading-relaxed mb-4", isWhiteSkin ? "text-slate-600" : "text-neutral-400")}>
                An Intent-Driven Cognitive Augmentation
              </p>

              {/* Operational Action Chips (Matching ChatPanel.tsx pages look & feel) */}
              <div className={cn(
                "w-full relative border rounded-2xl p-4 sm:p-5 backdrop-blur-md overflow-hidden select-none flex flex-col justify-center animate-fade-in text-left max-w-2xl",
                isWhiteSkin
                  ? "border-slate-200 bg-white/95 text-slate-800 shadow-sm"
                  : "border-white/5 bg-black/45 text-neutral-200"
              )}>
                <div className={cn("flex items-center justify-between pb-2.5 mb-3 border-b", isWhiteSkin ? "border-slate-200" : "border-white/5")}>
                  <div className="flex items-center gap-2">
                    <Sparkles className={cn("h-4 w-4", isWhiteSkin ? "text-cyan-700" : "text-cyan-400")} />
                    <span className={cn("text-xs font-semibold tracking-wide", isWhiteSkin ? "text-slate-900" : "text-white")}>
                      Operational Action Chips
                    </span>
                  </div>
                  <span className={cn(
                    "text-[10px] font-mono px-2 py-0.5 rounded-full border",
                    isWhiteSkin
                      ? "text-cyan-800 bg-cyan-50 border-cyan-300"
                      : "text-cyan-300 bg-cyan-500/10 border border-cyan-500/30"
                  )}>
                    {scenarioId || "Operational Context"}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                  {OPERATIONAL_ACTION_CHIPS.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSendMessage(item.prompt)}
                      className={cn(
                        "group relative flex flex-col items-start gap-2 rounded-xl border p-3.5 sm:p-4 text-left transition-all duration-300 hover:-translate-y-0.5 hover:scale-[1.01] cursor-pointer w-full",
                        isWhiteSkin
                          ? "border-slate-200 bg-slate-50/80 hover:border-cyan-500 hover:bg-cyan-50/60 shadow-xs"
                          : "border-white/5 bg-white/5 hover:border-cyan-400 hover:bg-cyan-500/10 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                      )}
                    >
                      <div className="flex w-full items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="transition-transform duration-300 ease-out group-hover:scale-110">
                            {item.icon}
                          </div>
                          <span className={cn(
                            "text-xs sm:text-sm font-medium transition-colors",
                            isWhiteSkin ? "text-slate-900 group-hover:text-cyan-800" : "text-white group-hover:text-cyan-300"
                          )}>
                            {item.title}
                          </span>
                        </div>
                        <span className={cn(
                          "text-[10px] font-mono rounded-full border px-2 py-0.5 transition-colors",
                          isWhiteSkin
                            ? "border-slate-300 bg-white text-slate-600 group-hover:border-cyan-400 group-hover:text-cyan-800"
                            : "border-white/10 bg-black/30 text-neutral-400 group-hover:border-cyan-500/20 group-hover:text-cyan-300"
                        )}>
                          {item.tag}
                        </span>
                      </div>
                      <p className={cn(
                        "text-xs line-clamp-2 transition-colors leading-relaxed mt-1",
                        isWhiteSkin ? "text-slate-600 group-hover:text-slate-800" : "text-neutral-400 group-hover:text-neutral-300"
                      )}>
                        &ldquo;{item.prompt}&rdquo;
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* MESSAGE LIST ITEMS (Memoized MessageBubble prevents re-parsing markdown on streaming) */}
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              isFullWindow={isFullWindow}
              copiedId={copiedId}
              onCopyText={handleCopyText}
              onSkipStreaming={skipStreaming}
              onClear={handleClearMessage}
              skin={skin}
            />
          ))}

          {/* Thinking / Analyzing Indicator (Matching ChatPanel) */}
          {isThinking && (
            <div className="flex items-start gap-2.5 py-1">
              <div className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border",
                isWhiteSkin
                  ? "border-cyan-600/40 bg-cyan-100 text-cyan-800"
                  : "border-cyan-500/30 bg-cyan-500/10 text-cyan-400"
              )}>
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex flex-col gap-1.5 pt-0.5">
                <div className="flex items-center gap-2">
                  <Loader2 className={cn("h-3.5 w-3.5 animate-spin", isWhiteSkin ? "text-cyan-700" : "text-cyan-400")} />
                  <span className={cn("text-xs font-semibold", isWhiteSkin ? "text-slate-900" : "text-white")}>ZAKI Correlating...</span>
                </div>
                <div className={cn(
                  "inline-flex w-fit items-center gap-1.5 rounded border px-2 py-1 text-[11px] font-mono",
                  isWhiteSkin
                    ? "border-slate-300 bg-white text-slate-600"
                    : "border-white/5 bg-black/30 text-neutral-400"
                )}>
                  <span className="animate-pulse">Analyzing telemetry, causal topology & blast radius</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ── ACTION CHIPS & RUNTIME INQUIRIES (Above Input Bar) ── */}
      {messages.length > 0 && (
        <div className={cn("px-3 py-1.5 shrink-0 transition-colors", isWhiteSkin ? "bg-slate-50/90 border-t border-slate-200" : "bg-white/[0.02] border-t border-white/5")}>
          <div className={cn("flex items-center justify-center gap-2 overflow-x-auto no-scrollbar", isFullWindow && "max-w-[1560px] mx-auto w-full")}>
            {OPERATIONAL_ACTION_CHIPS.map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(chip.prompt)}
                disabled={isThinking}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[10px] font-medium shrink-0 transition-all cursor-pointer disabled:opacity-50 border",
                  isWhiteSkin
                    ? "text-slate-700 bg-white border-slate-200 hover:border-cyan-500 hover:bg-cyan-50 hover:text-cyan-900 shadow-xs"
                    : "text-neutral-300 bg-white/5 border-white/10 hover:border-cyan-400/50 hover:bg-cyan-500/10 hover:text-white"
                )}
              >
                {chip.icon}
                <span>{chip.title}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Dynamic Stage Focus / Anchor Guide Banner */}
      {anchorQuestion && (
        <div className={cn("px-3.5 py-1.5 shrink-0 border-t text-[10px]", isWhiteSkin ? "bg-indigo-50 border-indigo-200 text-indigo-900" : "bg-indigo-950/40 border-indigo-500/20 text-indigo-300")}>
          <div className={cn("flex items-center gap-2", isFullWindow && "max-w-[1560px] mx-auto w-full")}>
            <Radio className={cn("h-3 w-3 shrink-0 animate-pulse", isWhiteSkin ? "text-indigo-600" : "text-indigo-400")} />
            <span className="truncate font-mono font-semibold">Operational Focus: {anchorQuestion}</span>
          </div>
        </div>
      )}

      {/* ── MEMOIZED PROMPT COMPOSER: ISOLATED TYPING STATE + 3X HEIGHT TEXTAREA + GEMINI ACTIONS ── */}
      <ZakiPromptComposer
        onSendMessage={handleSendMessage}
        isThinking={isThinking}
        stop={stop}
        voiceTranscript={voiceTranscript}
        onClearVoiceTranscript={() => setVoiceTranscript(null)}
        isLiveMode={isLiveMode}
        toggleLiveMode={toggleLiveMode}
        isMuted={isMuted}
        isSpeaking={isSpeaking}
        toggleMute={toggleMute}
        isWhiteSkin={isWhiteSkin}
        isFullWindow={isFullWindow}
        hasOperationalContext={hasOperationalContext}
        scenarioId={scenarioId}
      />
    </div>

    {/* Sleek Vertical Splitter */}
    <VerticalSplitter onDrag={(dx) => setRightW((w) => Math.min(520, Math.max(340, w - dx)))} />

    {/* RIGHT PANEL: Sections 6, 7, 8, 9 (Fixed size) */}
    <div
      style={{ width: `${rightW}px` }}
      className={cn(
        "hidden lg:flex shrink-0 h-full overflow-hidden flex-col",
        isWhiteSkin
          ? "border-l border-slate-200 bg-slate-50/95"
          : isLiquidSkin
          ? "border-l border-cyan-500/20 bg-[#051124]/90"
          : "border-l border-white/10 bg-[#06111f]/95"
      )}
    >
      <StorytellerRightPanel
        payload={activeStoryteller}
        simulationState={simulationState}
        scenarioId={scenarioId}
        stageIndex={stageIndex}
        className={isWhiteSkin ? "light-theme" : undefined}
        tokensConsumed={estimatedTokens}
        latencyMs={latestLatency}
        costUsd={estimatedTokens * 0.000002}
        throughputTps={latestLatency && latestLatency > 0 ? Number(((estimatedTokens / (latestLatency / 1000))).toFixed(1)) : 0.0}
      />
    </div>
  </div>
</div>
</div>
);
}

export default ZakiVoiceFAB;
