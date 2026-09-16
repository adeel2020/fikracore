"use client";

import React, { useState } from "react";
import {
  ChevronDown,
  Trash2,
  Clock,
  MessageSquare,
  Network,
  ExternalLink,
  Sparkles,
  Loader2,
  CheckCircle2,
  Play,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/api/config";
import { useChatHistory } from "./useChatHistory";

const iconStroke = { strokeWidth: 1.5 } as const;

/** Strip structured-event JSON blocks and agent markers that are embedded in raw message content. */
function cleanStructuredEvents(text: string): string {
  if (!text) return "";
  const startMarker = "__STRUCTURED_EVENT__";
  const endMarker = "__END_STRUCTURED_EVENT__";

  let result = text;
  while (true) {
    const startIdx = result.indexOf(startMarker);
    if (startIdx === -1) break;

    const endIdx = result.indexOf(endMarker, startIdx);
    if (endIdx === -1) {
      result = result.substring(0, startIdx);
      break;
    }

    result = result.substring(0, startIdx) + result.substring(endIdx + endMarker.length);
  }

  // Strip any lingering __AGENT__:... patterns
  result = result.replace(/__AGENT__:.*?\n/g, "");
  result = result.replace(/__AGENT__:.*?$/g, "");

  // Strip raw JSON objects/arrays that leaked from tool outputs or signal data.
  result = result.replace(/^\s*(\{[\s\S]*?\})\s*$/gm, (match, jsonCandidate) => {
    try {
      const parsed = JSON.parse(jsonCandidate);
      if (typeof parsed === "object" && parsed !== null) return "";
    } catch {
      // Not valid JSON, leave it alone
    }
    return match;
  });

  // Also strip inline JSON objects
  result = result.replace(
    /\{(?:"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\})(?:\s*,\s*"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\}))*)\}/g,
    ""
  );

  return result.trim();
}

/** Render formatted message content supporting bold, code, and clickable markdown links */
function renderFormattedContent(text: string): React.ReactNode {
  const cleaned = cleanStructuredEvents(text);
  if (!cleaned) return null;

  const lines = cleaned.split("\n");
  return (
    <div className="space-y-1.5 text-xs leading-relaxed">
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();
        if (trimmed === "---") {
          return <div key={`hr-${lineIdx}`} className="my-2 border-t border-white/10" />;
        }
        if (!trimmed) {
          return <div key={`empty-${lineIdx}`} className="h-1" />;
        }

        // Parse markdown links: [label](url)
        const linkRegex = /\[(.*?)\]\((.*?)\)/g;
        const parts: React.ReactNode[] = [];
        let lastIndex = 0;
        let match: RegExpExecArray | null;

        while ((match = linkRegex.exec(line)) !== null) {
          if (match.index > lastIndex) {
            parts.push(line.substring(lastIndex, match.index));
          }
          const label = match[1];
          const url = match[2];
          const isGraphLink =
            url.includes("telecom-knowledge-graph") || url.includes("artifacts");

          parts.push(
            <a
              key={`link-${lineIdx}-${match.index}`}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "inline-flex items-center gap-1.5 font-medium transition-all",
                isGraphLink
                  ? "my-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 hover:border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.25)] hover:shadow-[0_0_18px_rgba(16,185,129,0.45)] no-underline text-xs"
                  : "text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
              )}
            >
              {isGraphLink && <Network className="w-3.5 h-3.5 shrink-0" />}
              <span>{label}</span>
              <ExternalLink className="w-3 h-3 shrink-0 opacity-70" />
            </a>
          );
          lastIndex = match.index + match[0].length;
        }

        if (lastIndex < line.length) {
          parts.push(line.substring(lastIndex));
        }

        const nodes = parts.length > 0 ? parts : [line];

        return (
          <div key={`line-${lineIdx}`}>
            {nodes.map((node, nodeIdx) => {
              if (typeof node !== "string") return node;

              // Format bold **text**
              const boldTokens = node.split(/\*\*(.*?)\*\*/g);
              return boldTokens.map((bToken, bIdx) => {
                if (bIdx % 2 === 1) {
                  return (
                    <strong key={`b-${nodeIdx}-${bIdx}`} className="font-bold text-cyan-200">
                      {bToken}
                    </strong>
                  );
                }
                // Format inline code `code`
                const codeTokens = bToken.split(/`(.*?)`/g);
                return codeTokens.map((cToken, cIdx) => {
                  if (cIdx % 2 === 1) {
                    return (
                      <code
                        key={`c-${nodeIdx}-${bIdx}-${cIdx}`}
                        className="px-1.5 py-0.5 rounded bg-black/40 text-pink-400 font-mono text-[11px]"
                      >
                        {cToken}
                      </code>
                    );
                  }
                  return cToken;
                });
              });
            })}
          </div>
        );
      })}
    </div>
  );
}

export interface ChatHistoryPanelProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
  onSelectPersona?: (persona: string) => void;
  onRunPrompt?: (prompt: string, persona?: string) => void;
}

export function ChatHistoryPanel({
  currentSessionId,
  onSessionSelect,
  onNewSession,
  onSelectPersona,
  onRunPrompt,
}: ChatHistoryPanelProps) {
  const {
    sessions,
    expandedSessions,
    loadingSession,
    fetchAndExpandSession,
    handleDeleteSession,
    formatDate,
    getSessionPreview,
    fetchSessions,
  } = useChatHistory({ currentSessionId, onSessionSelect });

  const [isRunningGraph, setIsRunningGraph] = useState(false);
  const [graphStatus, setGraphStatus] = useState<string | null>(null);

  const handleRunKnowledgeGraph = async () => {
    if (isRunningGraph) return;
    setIsRunningGraph(true);
    setGraphStatus("Extracting FikraCore topology & compiling graph...");

    if (onRunPrompt) {
      onSelectPersona?.("Telecom Knowledge Graph Specialist");
      onRunPrompt("/telecom-knowledge-graph", "Telecom Knowledge Graph Specialist");
      setIsRunningGraph(false);
      setGraphStatus(null);
      return;
    }

    // Direct standalone execution fallback if not wired to external prompt runner
    try {
      const targetSessionId = currentSessionId || crypto.randomUUID();
      const res = await fetch(`${API_BASE}/api/qna/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "/telecom-knowledge-graph",
          session_id: targetSessionId,
          agent: "Telecom Knowledge Graph Specialist",
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchSessions();
      await fetchAndExpandSession(targetSessionId);
      setGraphStatus("Graph generated successfully!");
      setTimeout(() => setGraphStatus(null), 4000);
    } catch (err) {
      console.error("Failed to run telecom knowledge graph skill:", err);
      setGraphStatus("Execution failed. Check backend logs.");
      setTimeout(() => setGraphStatus(null), 4000);
    } finally {
      setIsRunningGraph(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 flex-shrink-0">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-cyan-400" {...iconStroke} />
          <h3 className="text-sm font-semibold text-white">Chat History</h3>
          {sessions.length > 0 && (
            <Badge variant="muted" className="text-xs px-2">
              {sessions.length}
            </Badge>
          )}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={onNewSession}
          className="text-xs h-7"
        >
          New Chat
        </Button>
      </div>

      {/* Graph Persona & Skill Launcher Card */}
      <div className="rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3 flex flex-col gap-2.5 shrink-0 shadow-lg relative overflow-hidden backdrop-blur-sm">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(16,185,129,0.3)]">
              <Network className="w-4 h-4 text-emerald-400" {...iconStroke} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-white truncate">
                  Knowledge Graph Specialist
                </span>
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
              </div>
              <p className="text-[10px] text-neutral-400 truncate">
                Skill: <code className="text-emerald-300 font-mono">/telecom-knowledge-graph</code>
              </p>
            </div>
          </div>
        </div>

        <p className="text-[11px] text-neutral-300 leading-snug">
          Compiles live FikraCore simulator runs into an interactive 11-domain causal topology explorer.
        </p>

        <div className="flex items-center gap-2 pt-0.5">
          <Button
            size="sm"
            onClick={handleRunKnowledgeGraph}
            disabled={isRunningGraph}
            className="flex-1 text-xs h-7 gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium border border-emerald-400/40 shadow-[0_0_12px_rgba(16,185,129,0.35)] transition-all"
          >
            {isRunningGraph ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Running Skill…</span>
              </>
            ) : (
              <>
                <Play className="w-3 h-3 fill-current" />
                <span>Generate Knowledge Graph</span>
              </>
            )}
          </Button>

          <a
            href="/artifacts/telecom-knowledge-graph.html"
            target="_blank"
            rel="noopener noreferrer"
            title="Open latest knowledge graph"
            className="h-7 px-2.5 rounded-lg border border-emerald-500/30 bg-white/5 hover:bg-white/10 text-emerald-300 text-[11px] font-medium inline-flex items-center gap-1 transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            <span>Open</span>
          </a>
        </div>

        {graphStatus && (
          <div className="text-[11px] text-emerald-300/90 flex items-center gap-1.5 bg-black/30 px-2 py-1 rounded border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
            <span className="truncate">{graphStatus}</span>
          </div>
        )}
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-2">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="w-6 h-6 text-neutral-600 mx-auto mb-2" />
            <p className="text-xs text-neutral-500">No chat sessions yet</p>
            <p className="text-xs text-neutral-600 mt-1">
              Start a new conversation to see history
            </p>
          </div>
        ) : (
          sessions.map((session) => {
            const isCurrentSession = currentSessionId === session.session_id;
            const isExpanded = !!expandedSessions[session.session_id];
            const sessionData = expandedSessions[session.session_id];
            const isLoading = loadingSession === session.session_id;
            const previewText = getSessionPreview(session);
            const hasGraphMention =
              previewText.toLowerCase().includes("graph") ||
              previewText.toLowerCase().includes("telecom-knowledge-graph");

            return (
              <div key={session.session_id} className="space-y-0">
                {/* Session Button */}
                <button
                  onClick={() => fetchAndExpandSession(session.session_id)}
                  disabled={isLoading}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded-lg transition-all duration-200",
                    isCurrentSession
                      ? "bg-cyan-500/20 border border-cyan-500/40 hover:bg-cyan-500/25"
                      : "hover:bg-white/8 border border-transparent hover:border-white/10",
                    isLoading && "opacity-50"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      {/* Session Header */}
                      <div className="flex items-center gap-2 mb-1">
                        <ChevronDown
                          className={cn(
                            "h-4 w-4 shrink-0 transition-transform duration-200",
                            isExpanded ? "" : "-rotate-90"
                          )}
                        />
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-neutral-500" />
                          <span className="text-xs font-medium text-neutral-300">
                            {formatDate(session.created_at)}
                          </span>
                        </div>
                        {hasGraphMention && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-0.5">
                            <Network className="w-2.5 h-2.5" /> Graph
                          </span>
                        )}
                        <Badge
                          variant={isCurrentSession ? "default" : "muted"}
                          className="text-xs px-1.5 ml-auto"
                        >
                          {session.message_count}
                        </Badge>
                      </div>

                      {/* Session Preview */}
                      <p className="text-xs text-neutral-400 truncate ml-6 mb-1">
                        {previewText}
                      </p>
                    </div>

                    {/* Delete Button */}
                    <button
                      onClick={(e) => handleDeleteSession(session.session_id, e)}
                      className={cn(
                        "text-neutral-500 hover:text-red-400 shrink-0 p-1 rounded transition-colors",
                        isLoading && "opacity-50 pointer-events-none"
                      )}
                      title="Delete session"
                    >
                      <Trash2 className="h-3.5 w-3.5" {...iconStroke} />
                    </button>
                  </div>
                </button>

                {/* Expanded Messages */}
                {isExpanded && sessionData && (
                  <div className="ml-6 space-y-2 max-h-96 overflow-y-auto rounded-lg bg-white/5 p-2.5 border border-white/5">
                    {sessionData.messages.length === 0 ? (
                      <p className="text-xs text-neutral-500 p-2">No messages</p>
                    ) : (
                      sessionData.messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={cn(
                            "p-2.5 rounded-lg text-xs leading-relaxed break-words",
                            msg.role === "user"
                              ? "bg-cyan-500/15 text-cyan-100 border-l-2 border-cyan-500/50"
                              : "bg-white/10 text-neutral-200 border-l-2 border-emerald-400/50"
                          )}
                        >
                          <div className="flex items-center justify-between mb-1.5 opacity-80 text-[11px] font-semibold">
                            <span className="flex items-center gap-1 text-cyan-300">
                              {msg.role === "user" ? "You" : "Knowledge Specialist"}
                            </span>
                            <span className="opacity-50 font-normal">
                              {formatDate(msg.created_at)}
                            </span>
                          </div>
                          <div>{renderFormattedContent(msg.content)}</div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
