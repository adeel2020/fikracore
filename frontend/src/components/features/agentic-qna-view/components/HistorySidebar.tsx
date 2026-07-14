"use client";

import React from "react";
import { ChevronLeft, Pin, Trash2 } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface HistorySidebarProps {
  showHistory: boolean;
  setShowHistory: (show: boolean) => void;
  handleNewChat: () => void;
  sessions: any[];
  pinnedSessionIds: string[];
  sessionPreviews: Record<string, string>;
  loadingSessionId: string | null;
  sessionId: string | null;
  loadSession: (sid: string) => void;
  togglePinSession: (sid: string, e: React.MouseEvent) => void;
  deleteSession: (sid: string, e: React.MouseEvent) => void;
}

export function HistorySidebar({
  showHistory,
  setShowHistory,
  handleNewChat,
  sessions,
  pinnedSessionIds,
  sessionPreviews,
  loadingSessionId,
  sessionId,
  loadSession,
  togglePinSession,
  deleteSession,
}: HistorySidebarProps) {
  if (!showHistory) return null;

  const sortedSessions = [...sessions].sort((a, b) => {
    const aP = pinnedSessionIds.includes(a.session_id);
    const bP = pinnedSessionIds.includes(b.session_id);
    if (aP && !bP) return -1;
    if (!aP && bP) return 1;
    return 0;
  });

  return (
    <div className="overflow-hidden transition-all duration-300 w-[280px] shrink-0">
      <GlassCard className="flex h-full flex-col p-4 overflow-hidden" hover={false}>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-medium text-white">History</h3>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowHistory(false)}
            className="h-6 w-6 p-0"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 space-y-2 overflow-y-auto scrollbar-none [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          <button
            onClick={handleNewChat}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-white hover:bg-white/10 transition-colors"
          >
            + New Chat
          </button>
          {sortedSessions.map((session) => {
            const preview = sessionPreviews[session.session_id] || "Loading...";
            const isLoading = loadingSessionId === session.session_id;
            const isPinned = pinnedSessionIds.includes(session.session_id);
            return (
              <div
                key={session.session_id}
                onClick={() => !isLoading && loadSession(session.session_id)}
                className={cn(
                  "group relative w-full rounded-lg border px-3 py-2 text-left text-xs transition-colors cursor-pointer flex items-center justify-between gap-2",
                  sessionId === session.session_id
                    ? "border-cyan-500/40 bg-cyan-500/15 text-white"
                    : "border-white/10 bg-white/5 text-neutral-300 hover:bg-white/10",
                  isLoading && "opacity-50 pointer-events-none"
                )}
              >
                <div className="flex-1 min-w-0">
                  <p className="truncate font-medium flex items-center gap-1.5">
                    {isPinned && (
                      <Pin className="h-3 w-3 text-cyan-400 rotate-45 fill-cyan-400/20 shrink-0" />
                    )}
                    <span className="truncate">{preview}</span>
                  </p>
                  <p className="text-xs text-neutral-500 mt-1">{session.message_count} messages</p>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button
                    onClick={(e) => togglePinSession(session.session_id, e)}
                    title={isPinned ? "Unpin chat" : "Pin chat"}
                    className={cn(
                      "p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-cyan-400 transition-colors",
                      isPinned && "text-cyan-400"
                    )}
                  >
                    <Pin className={cn("h-3.5 w-3.5 rotate-45", isPinned && "fill-cyan-400/20")} />
                  </button>
                  <button
                    onClick={(e) => deleteSession(session.session_id, e)}
                    title="Delete chat"
                    className="p-1 rounded hover:bg-white/10 text-neutral-400 hover:text-rose-400 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>
    </div>
  );
}
