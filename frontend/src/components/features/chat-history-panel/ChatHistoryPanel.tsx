"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  Activity,
  Layers,
  AlertTriangle,
  GitBranch,
  Wrench,
  ShieldCheck,
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

/** Render formatted message content using rich ReactMarkdown with telecom styling */
function renderFormattedContent(text: string): React.ReactNode {
  const cleaned = cleanStructuredEvents(text);
  if (!cleaned) return null;

  return (
    <div className="telecom-story-container text-xs leading-relaxed text-zinc-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <div className="my-3 pb-2 border-b border-cyan-500/30 flex items-center justify-between">
              <span className="text-sm font-bold tracking-wide text-cyan-200 uppercase flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400 animate-pulse shrink-0" />
                <span>{children}</span>
              </span>
            </div>
          ),
          h2: ({ children }) => (
            <div className="mt-4 mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-300 border-l-2 border-cyan-500 pl-2">
              <Layers className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>{children}</span>
            </div>
          ),
          h3: ({ children }) => {
            const title = String(children);
            let Icon = Layers;
            if (/summary/i.test(title)) Icon = Activity;
            else if (/topology|blast/i.test(title)) Icon = Layers;
            else if (/root cause|rca/i.test(title)) Icon = AlertTriangle;
            else if (/causal/i.test(title)) Icon = GitBranch;
            else if (/timeline|chronolog/i.test(title)) Icon = Clock;
            else if (/remediation|action/i.test(title)) Icon = Wrench;
            else if (/recovery/i.test(title)) Icon = ShieldCheck;

            return (
              <div className="mt-3.5 mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-300 border-l-2 border-cyan-500/80 pl-2">
                <Icon className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                <span>{children}</span>
              </div>
            );
          },
          blockquote: ({ children }) => (
            <div className="my-2 p-2.5 rounded-lg bg-zinc-900/90 border border-zinc-700/60 flex flex-wrap items-center gap-2 text-[11px] text-zinc-300 shadow-sm">
              {children}
            </div>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-cyan-200">{children}</strong>
          ),
          code: ({ className, children }) => {
            const isInline = !className?.includes("language-");
            const val = String(children).trim();

            if (isInline) {
              if (/\b(SEV-1|CRITICAL|P1)\b/i.test(val)) {
                return (
                  <span className="px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold font-mono text-[11px] shadow-[0_0_8px_rgba(244,63,94,0.2)]">
                    {val}
                  </span>
                );
              }
              if (/\b(SEV-2|MAJOR|P2)\b/i.test(val)) {
                return (
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold font-mono text-[11px] shadow-[0_0_8px_rgba(245,158,11,0.2)]">
                    {val}
                  </span>
                );
              }
              if (/\b(RESOLVED|HEALTHY|CLOSED)\b/i.test(val)) {
                return (
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold font-mono text-[11px] shadow-[0_0_8px_rgba(16,185,129,0.2)]">
                    {val}
                  </span>
                );
              }
              return (
                <code className="px-1.5 py-0.5 rounded bg-black/50 border border-zinc-800 text-pink-400 font-mono text-[11px]">
                  {children}
                </code>
              );
            }

            return (
              <pre className="my-2 p-3 rounded-lg bg-black/70 border border-zinc-800 font-mono text-[11px] overflow-x-auto text-emerald-400 leading-relaxed">
                <code>{children}</code>
              </pre>
            );
          },
          a: ({ href, children }) => {
            const url = href || "";
            const isGraphLink =
              url.includes("telecom-knowledge-graph") || url.includes("artifacts");

            return (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  "inline-flex items-center gap-1.5 font-medium transition-all",
                  isGraphLink
                    ? "my-1 px-3 py-1 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 hover:border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.25)] hover:shadow-[0_0_18px_rgba(16,185,129,0.45)] no-underline text-xs"
                    : "text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
                )}
              >
                {isGraphLink && <Network className="w-3.5 h-3.5 shrink-0" />}
                <span>{children}</span>
                <ExternalLink className="w-3 h-3 shrink-0 opacity-70" />
              </a>
            );
          },
          li: ({ children }) => {
            const textContent = React.Children.toArray(children)
              .map((c) => (typeof c === "string" ? c : ""))
              .join(" ");

            const isTimeline = /\b\d{2}:\d{2}(?::\d{2})?Z?\b/.test(textContent);
            const isCausal = textContent.includes("──►");

            if (isTimeline) {
              return (
                <li className="relative pl-4 py-1 list-none before:absolute before:left-0 before:top-2.5 before:w-2 before:h-2 before:rounded-full before:bg-cyan-400 border-l border-cyan-500/30 ml-2 my-0.5">
                  <span className="text-zinc-200">{children}</span>
                </li>
              );
            }

            if (isCausal) {
              return (
                <li className="my-1.5 p-2 rounded-lg bg-zinc-900/60 border border-zinc-800/80 list-none flex items-center gap-2 text-zinc-200 shadow-sm">
                  <GitBranch className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <span className="flex-1">{children}</span>
                </li>
              );
            }

            return (
              <li className="my-1 ml-4 list-disc text-zinc-300 leading-normal">
                {children}
              </li>
            );
          },
          ul: ({ children }) => (
            <ul className="my-1.5 space-y-1">{children}</ul>
          ),
          p: ({ children }) => (
            <p className="my-1.5 text-zinc-300 leading-relaxed">{children}</p>
          ),
          hr: () => <hr className="my-3 border-t border-white/10" />,
        }}
      >
        {cleaned}
      </ReactMarkdown>
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
