"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { Bot, User, Send, Square, Loader2, MessageSquare, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { useStorytellerChat } from "./hooks/useStorytellerChat";
import { API_BASE } from "@/lib/api/config";

interface ChatMessage {
  id: string;
  role: "bot" | "user";
  content: string;
  timestamp: number;
}

interface StorytellerChatProps {
  refreshKey?: number;
  focusedCluster?: string | null;
}

const iconStroke = { strokeWidth: 1.5 } as const;

const formatText = (text: string) => {
  if (!text) return "";
  const boldParts = text.split(/\*\*(.*?)\*\*/g);
  return boldParts.flatMap((part, i) => {
    if (i % 2 === 1) {
      return [
        <strong key={`b-${i}`} className="font-bold text-cyan-300">
          {part}
        </strong>,
      ];
    }
    const codeParts = part.split(/`(.*?)`/g);
    return codeParts.map((subPart, j) => {
      if (j % 2 === 1) {
        return (
          <code
            key={`c-${i}-${j}`}
            className="px-1.5 py-0.5 rounded bg-black/40 text-pink-400 font-mono text-xs"
          >
            {subPart}
          </code>
        );
      }
      return subPart;
    });
  });
};

const renderMessageContent = (content: string) => {
  if (!content) return null;
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let currentTableHeaders: string[] = [];
  let currentTableRows: string[][] = [];
  let isInsideTable = false;

  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();

    if (trimmed.startsWith("|")) {
      isInsideTable = true;
      const cells = trimmed
        .split("|")
        .map((c) => c.trim())
        .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      if (cells.every((c) => /^:?-+:?$/.test(c))) continue;
      if (currentTableHeaders.length === 0) currentTableHeaders = cells;
      else currentTableRows.push(cells);
      continue;
    } else {
      if (isInsideTable && currentTableHeaders.length > 0) {
        elements.push(
          <div key={`table-${i}`} className="my-3 overflow-x-auto rounded-xl border border-white/10 bg-white/5 backdrop-blur-md shadow-lg w-full">
            <table className="min-w-full divide-y divide-white/10 text-left text-xs text-neutral-200">
              <thead className="bg-white/10 text-neutral-100 font-semibold uppercase tracking-wider">
                <tr>
                  {currentTableHeaders.map((h, idx) => (
                    <th key={idx} className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap">
                      {formatText(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-transparent font-medium">
                {currentTableRows.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-white/5 transition-colors duration-150">
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap">
                        {formatText(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        currentTableHeaders = [];
        currentTableRows = [];
        isInsideTable = false;
      }
    }

    if (trimmed.startsWith("#")) {
      const match = trimmed.match(/^(#{1,6})\s*(.*)/);
      if (match) {
        const level = match[1].length;
        const text = match[2];
        if (level === 1)
          elements.push(
            <h1 key={i} className="text-xl font-bold text-white mt-4 mb-2 first:mt-0">
              {formatText(text)}
            </h1>
          );
        else if (level === 2)
          elements.push(
            <h2 key={i} className="text-lg font-semibold text-white mt-3 mb-2 first:mt-0">
              {formatText(text)}
            </h2>
          );
        else
          elements.push(
            <h3 key={i} className="text-base font-medium text-cyan-400 mt-2 mb-1 first:mt-0">
              {formatText(text)}
            </h3>
          );
        continue;
      }
    }

    if (trimmed === "---") {
      elements.push(<hr key={i} className="border-t border-white/10 my-4" />);
      continue;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const text = trimmed.substring(2);
      elements.push(
        <div key={i} className="flex gap-2 items-start my-1 text-sm text-neutral-300 pl-2">
          <span className="text-cyan-400 mt-1.5 shrink-0 select-none">•</span>
          <span>{formatText(text)}</span>
        </div>
      );
      continue;
    }

    if (trimmed)
      elements.push(
        <p key={i} className="text-sm text-neutral-300 leading-relaxed my-1">
          {formatText(trimmed)}
        </p>
      );
  }

  if (isInsideTable && currentTableHeaders.length > 0) {
    elements.push(
      <div key="table-final" className="my-3 overflow-x-auto rounded-xl border border-white/10 bg-white/5 backdrop-blur-md shadow-lg w-full">
        <table className="min-w-full divide-y divide-white/10 text-left text-xs text-neutral-200">
          <thead className="bg-white/10 text-neutral-100 font-semibold uppercase tracking-wider">
            <tr>
              {currentTableHeaders.map((h, idx) => (
                <th key={idx} className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap">
                  {formatText(h)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 bg-transparent font-medium">
            {currentTableRows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-white/5 transition-colors duration-150">
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap">
                    {formatText(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  return <div className="flex flex-col gap-1 w-full">{elements}</div>;
};

const StorytellerChat: React.FC<StorytellerChatProps> = ({ refreshKey = 0, focusedCluster }) => {
  const { loading, error } = useStorytellerChat(refreshKey);
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    { id: "welcome", role: "bot", content: "I'm your operational storyteller. Type a cluster name to analyse.", timestamp: Date.now() },
  ]);
  const [pending, setPending] = useState(false);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!focusedCluster) return;

    setOpen(true);
    setPending(true);

    const userMsgId = Date.now().toString() + "-user";
    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        role: "user",
        content: `Analyse cluster: ${focusedCluster}`,
        timestamp: Date.now(),
      },
    ]);

    let isCancelled = false;

    fetch(`${API_BASE}/api/datastory/cluster-story`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cluster_name: focusedCluster }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const detail = await res.json().then((r) => r?.detail).catch(() => res.statusText);
          throw new Error(detail);
        }
        return res.json();
      })
      .then((data: { summary: string }) => {
        if (isCancelled) return;
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString() + "-bot",
            role: "bot",
            content: data.summary,
            timestamp: Date.now(),
          },
        ]);
      })
      .catch((err: Error) => {
        if (isCancelled) return;
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString() + "-bot-err",
            role: "bot",
            content: `Failed to analyse cluster: ${err.message}`,
            timestamp: Date.now(),
          },
        ]);
      })
      .finally(() => {
        if (!isCancelled) setPending(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [focusedCluster]);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));
  }, [messages, pending, loading, error, open]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, pending, loading, error, open, scrollToBottom]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMessages([]);
  }, [refreshKey]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || pending) return;
    setInput("");

    const userMsg: ChatMessage = { id: `user-${Date.now()}`, role: "user", content: text, timestamp: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setPending(true);

    try {
      const res = await fetch(`${API_BASE}/api/datastory/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error("Failed to get response");
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { id: `bot-${Date.now()}`, role: "bot", content: data.response, timestamp: Date.now() },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: `bot-err-${Date.now()}`, role: "bot", content: "Sorry, I couldn't reach the storyteller right now. Try again shortly.", timestamp: Date.now() },
      ]);
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }, [input, pending]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSend();
  }, [handleSend]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <>
      {open ? (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            width: 400,
            height: 560,
            maxHeight: "calc(100vh - 48px)",
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            borderRadius: 18,
            overflow: "hidden",
            background: "rgba(8, 8, 10, 0.88)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.10)",
            boxShadow: "0 24px 70px rgba(0,0,0,0.55)",
          }}
        >
          <div className="flex items-center justify-between px-4 pt-3 pb-0 select-none flex-shrink-0">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-cyan-400" />
              <span className="text-sm font-semibold text-white">Storyteller Chat</span>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="flex items-center gap-1 text-[11px] text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer bg-transparent border-0"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto space-y-4 px-4 py-3 min-h-0 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.15)_transparent]"
          >
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-neutral-400 py-8 justify-center">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-500" />
                synthesizing narrative...
              </div>
            ) : error ? (
              <div className="text-sm text-lime-300/90 py-8 text-center">{error}</div>
            ) : (
              messages.map((msg) => {
                const isBot = msg.role === "bot";
                return (
                  <div key={msg.id} className={cn("flex gap-3 w-full py-1", isBot ? "justify-start" : "justify-end")}>
                    {isBot && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
                        <Bot className="h-5 w-5 text-cyan-400" />
                      </div>
                    )}
                    <div className={cn("flex flex-col max-w-[80%]", isBot ? "items-start" : "items-end")}>
                      {isBot && (
                        <div className="flex items-baseline gap-2 mb-1.5 ml-1 select-none">
                          <span className="text-sm font-semibold text-white">Data Storyteller</span>
                        </div>
                      )}
                      {msg.id === "welcome" ? (
                        <div className={cn("rounded-2xl px-4 py-3 text-sm w-full", glassSurfaceStatic)}>
                          <p className="text-sm text-neutral-300 leading-relaxed">{msg.content}</p>
                        </div>
                      ) : isBot ? (
                        <div className={cn("rounded-2xl px-4 py-3 text-sm w-full", glassSurfaceStatic)}>
                          {renderMessageContent(msg.content)}
                        </div>
                      ) : (
                        <div className="rounded-2xl px-4 py-3 text-sm bg-cyan-500/20 text-white whitespace-pre-wrap">
                          {msg.content}
                        </div>
                      )}
                    </div>
                    {!isBot && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5">
                        <User className="h-5 w-5 text-neutral-400" />
                      </div>
                    )}
                  </div>
                );
              })
            )}
            {pending && (
              <div className="flex w-full items-start gap-4 py-2">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
                  <Bot className="h-5 w-5 text-cyan-400" />
                </div>
                <div className="flex flex-col gap-2 pt-1">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-500" />
                    <span className="text-sm font-semibold text-white">Data Storyteller</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0 px-4 pb-4 pt-2">
            <div className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm flex items-center gap-2 focus-within:border-cyan-500/30 transition-colors">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={pending}
                placeholder="ask about your operational data..."
                autoFocus
                className="flex-1 bg-transparent border-0 p-0 text-white placeholder:text-neutral-500 focus:outline-none focus:ring-0 disabled:opacity-50 min-w-[120px]"
              />
            </div>
            <Button
              type={pending ? "button" : "submit"}
              size="icon"
              aria-label={pending ? "Stop" : "Send"}
              disabled={!pending && !input.trim()}
              className={cn("transition-all duration-300", pending ? "bg-rose-500 hover:bg-rose-600 text-white" : "")}
            >
              {pending ? (
                <Square className="h-4 w-4 fill-white" {...iconStroke} />
              ) : (
                <Send className="h-4 w-4" {...iconStroke} />
              )}
            </Button>
          </form>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 9999,
            width: 48,
            height: 48,
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(8, 8, 10, 0.80)",
            backdropFilter: "blur(18px)",
            WebkitBackdropFilter: "blur(18px)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.40)",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.12)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(8, 8, 10, 0.80)"; }}
        >
          <MessageSquare className="h-5 w-5 text-cyan-400" />
        </button>
      )}
    </>
  );
};

export default React.memo(StorytellerChat);
