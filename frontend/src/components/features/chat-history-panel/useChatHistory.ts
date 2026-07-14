import { useState, useEffect } from "react";

export interface HistorySession {
  session_id: string;
  created_at: number;
  last_accessed: number;
  message_count: number;
}

export interface HistoryMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: number;
}

export interface SessionData {
  session_id: string;
  created_at: number;
  message_count: number;
  messages: HistoryMessage[];
}

interface UseChatHistoryProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
}

export function useChatHistory({
  currentSessionId,
  onSessionSelect,
}: UseChatHistoryProps) {
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [expandedSessions, setExpandedSessions] = useState<Record<string, SessionData>>({});
  const [loadingSession, setLoadingSession] = useState<string | null>(null);

  // Fetch sessions once on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/history/sessions");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setSessions(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
      setSessions([]);
    }
  };

  const fetchAndExpandSession = async (sessionId: string) => {
    // If already expanded, collapse it
    if (expandedSessions[sessionId]) {
      setExpandedSessions((prev) => {
        const updated = { ...prev };
        delete updated[sessionId];
        return updated;
      });
      return;
    }

    // Load messages for this session
    setLoadingSession(sessionId);
    try {
      const res = await fetch(
        `http://localhost:8000/api/history/sessions/${sessionId}/messages`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as SessionData;
      setExpandedSessions((prev) => ({
        ...prev,
        [sessionId]: data,
      }));
      onSessionSelect(sessionId);
    } catch (error) {
      console.error("Failed to fetch session messages:", error);
    } finally {
      setLoadingSession(null);
    }
  };

  const handleDeleteSession = async (
    sessionId: string,
    e: React.MouseEvent
  ) => {
    e.stopPropagation();
    if (!confirm("Delete this session? This cannot be undone.")) return;

    try {
      const res = await fetch(
        `http://localhost:8000/api/history/sessions/${sessionId}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      setExpandedSessions((prev) => {
        const updated = { ...prev };
        delete updated[sessionId];
        return updated;
      });
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const formatDate = (timestamp: number): string => {
    if (!timestamp) return "—";
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const getSessionPreview = (session: HistorySession): string => {
    const expanded = expandedSessions[session.session_id];
    if (!expanded || expanded.messages.length === 0) {
      return "No messages yet";
    }
    // Show the last user message as preview
    const lastMessage = [...expanded.messages]
      .reverse()
      .find((m) => m.role === "user");
    if (!lastMessage) return "No user messages";
    return lastMessage.content.substring(0, 60);
  };

  return {
    sessions,
    expandedSessions,
    loadingSession,
    fetchAndExpandSession,
    handleDeleteSession,
    formatDate,
    getSessionPreview,
  };
}
