"use client";

import React from "react";
import { ChevronDown, Trash2, Clock, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
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
  // These appear as standalone lines starting with { or [ and are clearly not prose.
  result = result.replace(/^\s*(\{[\s\S]*?\})\s*$/gm, (match, jsonCandidate) => {
    try {
      const parsed = JSON.parse(jsonCandidate);
      if (typeof parsed === "object" && parsed !== null) return "";
    } catch {
      // Not valid JSON, leave it alone
    }
    return match;
  });

  // Also strip inline JSON objects like {"key": "value", ...} embedded in text
  result = result.replace(/\{(?:"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\})(?:\s*,\s*"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\}))*)\}/g, "");

  return result.trim();
}

interface ChatHistoryPanelProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

export function ChatHistoryPanel({
  currentSessionId,
  onSessionSelect,
  onNewSession,
}: ChatHistoryPanelProps) {
  const {
    sessions,
    expandedSessions,
    loadingSession,
    fetchAndExpandSession,
    handleDeleteSession,
    formatDate,
    getSessionPreview,
  } = useChatHistory({ currentSessionId, onSessionSelect });

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
                        <Badge
                          variant={isCurrentSession ? "default" : "muted"}
                          className="text-xs px-1.5"
                        >
                          {session.message_count}
                        </Badge>
                      </div>

                      {/* Session Preview */}
                      <p className="text-xs text-neutral-400 truncate ml-6 mb-1">
                        {getSessionPreview(session)}
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
                  <div className="ml-6 space-y-1 max-h-96 overflow-y-auto rounded-lg bg-white/5 p-2 border border-white/5">
                    {sessionData.messages.length === 0 ? (
                      <p className="text-xs text-neutral-500 p-2">No messages</p>
                    ) : (
                      sessionData.messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={cn(
                            "p-2 rounded text-xs leading-relaxed break-words",
                            msg.role === "user"
                              ? "bg-cyan-500/15 text-cyan-100 border-l-2 border-cyan-500/50"
                              : "bg-white/10 text-neutral-300 border-l-2 border-white/20"
                          )}
                        >
                          <div className="font-semibold text-xs mb-1 opacity-75">
                            {msg.role === "user" ? "You" : "Assistant"}
                          </div>
                          <div className="whitespace-normal">
                            {cleanStructuredEvents(msg.content)}
                          </div>
                          <div className="text-xs opacity-50 mt-1">
                            {formatDate(msg.created_at)}
                          </div>
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
