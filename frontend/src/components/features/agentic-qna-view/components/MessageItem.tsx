"use client";

import React, { useRef, useEffect, useState } from "react";
import {
  Brain,
  Phone,
  Bot,
  User,
  Loader2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Info,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { ChatMessage } from "@/lib/api/qna";
import { StructuredAgentResponse } from "../types/agentic-qna.types";
import { ChartPillPicker } from "../../context-view/components/RagPanel";

const CHART_API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

const iconStroke = { strokeWidth: 1.5 } as const;

function formatTimestamp(timestamp?: number) {
  const date = timestamp ? new Date(timestamp * 1000) : new Date();
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

// ====================================================================
// HELPERS & SUB-COMPONENTS
// ====================================================================

function ThoughtsBlock({
  thoughts,
  isLastMessage,
  loading,
}: {
  thoughts: string;
  isLastMessage: boolean;
  loading: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLastMessage && loading && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [thoughts, isLastMessage, loading]);

  return (
    <div
      ref={containerRef}
      className="mt-2 pl-3.5 whitespace-pre-wrap overflow-y-auto max-h-60 leading-relaxed border-l border-white/10 text-neutral-400 font-mono text-[11px] ml-1.5 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.15)_transparent]"
    >
      {thoughts}
    </div>
  );
}

function ThoughtsAccordion({
  thoughts,
  durationSeconds,
  isLastMessage,
  loading,
}: {
  thoughts?: string;
  durationSeconds?: number;
  isLastMessage: boolean;
  loading: boolean;
}) {
  const detailsRef = useRef<HTMLDetailsElement>(null);

  useEffect(() => {
    if (detailsRef.current) {
      if (loading) {
        if (thoughts && thoughts.trim().length > 0) {
          detailsRef.current.open = true;
        }
      } else {
        detailsRef.current.open = false;
      }
    }
  }, [loading, thoughts]);

  const cleanedThoughts = thoughts
    ? thoughts
        .replace(/__STRUCTURED_EVENT__/g, "")
        .replace(/__END_STRUCTURED_EVENT__/g, "")
        .trim()
    : "";

  return (
    <details
      ref={detailsRef}
      className="group mt-1.5 mb-1.5 w-full text-xs text-neutral-400 [&[open]_svg]:rotate-180"
    >
      <summary className="list-none [&::-webkit-details-marker]:hidden cursor-pointer font-sans font-normal text-neutral-400 hover:text-neutral-300 transition-colors inline-flex items-center gap-1 select-none focus:outline-none py-1 ml-1">
        <span>Thought for {durationSeconds || 1}s</span>
        <ChevronDown className="h-3.5 w-3.5 shrink-0 transition-transform duration-200" />
      </summary>
      {cleanedThoughts.length > 0 ? (
        <ThoughtsBlock thoughts={cleanedThoughts} isLastMessage={isLastMessage} loading={loading} />
      ) : (
        <div className="mt-2 pl-3.5 text-neutral-500 text-[11px] italic ml-1.5"></div>
      )}
    </details>
  );
}

function parseMermaidSequence(text: string) {
  const lines = text.split("\n");
  const participants: string[] = [];
  const steps: any[] = [];

  for (let line of lines) {
    line = line.trim();
    if (!line || line === "sequenceDiagram" || line === "autonumber") continue;

    if (line.startsWith("participant ")) {
      const p = line.substring(12).trim();
      if (!participants.includes(p)) participants.push(p);
      continue;
    }

    const noteMatch = line.match(/^Note\s+over\s+([\w\.-]+):\s*(.*)/i);
    if (noteMatch) {
      const participant = noteMatch[1].trim();
      const noteText = noteMatch[2];
      steps.push({ type: "note", noteOver: participant, label: noteText });
      if (!participants.includes(participant)) participants.push(participant);
      continue;
    }

    const msgMatch = line.match(/^([\w\.-]+)->>([\w\.-]+):\s*(.*)/);
    if (msgMatch) {
      const from = msgMatch[1].trim();
      const to = msgMatch[2].trim();
      const msgText = msgMatch[3];
      steps.push({ type: "message", from, to, label: msgText });
      if (!participants.includes(from)) participants.push(from);
      if (!participants.includes(to)) participants.push(to);
      continue;
    }
  }

  if (participants.length === 0) {
    participants.push("gsmSSF", "gsmSCF");
  }

  return { participants, steps };
}

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

const RenderTable = ({ data }: { data: any }) => {
  const { headers, rows } = data;
  return (
    <div className="my-3 overflow-x-auto rounded-xl border border-white/10 bg-white/5 backdrop-blur-md shadow-lg w-full">
      <table className="min-w-full divide-y divide-white/10 text-left text-xs text-neutral-200">
        <thead className="bg-white/10 text-neutral-100 font-semibold uppercase tracking-wider">
          <tr>
            {headers.map((h: string, idx: number) => (
              <th
                key={idx}
                className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap"
              >
                {formatText(h)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 bg-transparent font-medium">
          {rows.map((row: string[], rowIdx: number) => (
            <tr key={rowIdx} className="hover:bg-white/5 transition-colors duration-150">
              {row.map((cell: string, cellIdx: number) => (
                <td
                  key={cellIdx}
                  className="px-4 py-3 border-r border-white/5 last:border-0 whitespace-nowrap"
                >
                  {formatText(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RenderSequenceDiagram = ({ data }: { data: any }) => {
  const { participants, steps } = data;
  const isScrollable = steps.length > 8;
  return (
    <div className="my-4 p-4 rounded-xl border border-white/5 bg-black/25 w-full overflow-x-auto">
      <div className="flex justify-around items-center border-b border-white/5 pb-3 mb-5 min-w-[360px]">
        {participants.map((p: string, idx: number) => (
          <div
            key={idx}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-white/5 text-neutral-200 text-xs font-semibold uppercase tracking-wider min-w-[100px] justify-center"
          >
            <div className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
            <span>{p}</span>
          </div>
        ))}
      </div>
      <div
        className={cn(
          "pr-1",
          isScrollable
            ? "max-h-[380px] overflow-y-auto overflow-x-hidden [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.15)_transparent]"
            : "w-full"
        )}
      >
        <div className="flex flex-col gap-6 relative min-w-[360px] px-4 pb-2">
          <div className="absolute inset-0 flex justify-around pointer-events-none">
            {participants.map((_: any, idx: number) => (
              <div key={idx} className="w-0 border-l-2 border-dashed border-white/30 h-full" />
            ))}
          </div>
          {steps.map((step: any, idx: number) => {
            if (step.type === "note") {
              const partIdx = participants.indexOf(step.noteOver);
              if (partIdx === -1) return null;
              const numPart = participants.length;
              const centerPercent = (partIdx / numPart) * 100 + 50 / numPart;
              return (
                <div key={idx} className="relative z-10 flex w-full my-0.5 justify-center h-8">
                  <div
                    className="max-w-[80%] px-2.5 py-1 rounded border border-neutral-700 bg-neutral-900 text-neutral-400 text-[11px] font-mono absolute"
                    style={{ left: `${centerPercent}%`, transform: "translateX(-50%)" }}
                  >
                    {step.label}
                  </div>
                </div>
              );
            }
            if (step.type === "message") {
              const fromIdx = participants.indexOf(step.from);
              const toIdx = participants.indexOf(step.to);
              if (fromIdx === -1 || toIdx === -1) return null;
              const isRight = fromIdx < toIdx;
              const left = Math.min(fromIdx, toIdx);
              const right = Math.max(fromIdx, toIdx);
              const numPart = participants.length;
              const widthPercent = ((right - left) / numPart) * 100;
              const leftPercent = (left / numPart) * 100 + 50 / numPart;
              return (
                <div key={idx} className="relative z-10 w-full flex flex-col items-center my-1.5 h-12">
                  <div
                    className="text-[11px] font-mono text-cyan-300 bg-neutral-900/80 px-2 py-0.5 rounded border border-white/5 mb-1 z-20 absolute whitespace-nowrap"
                    style={{
                      left: `${leftPercent + widthPercent / 2}%`,
                      transform: "translateX(-50%)",
                      top: "0px",
                    }}
                  >
                    {formatText(step.label)}
                  </div>
                  <div
                    className="absolute flex items-center h-3"
                    style={{ left: `${leftPercent}%`, width: `${widthPercent}%`, top: "24px" }}
                  >
                    {isRight ? (
                      <div className="w-full flex items-center relative">
                        <div className="h-[1px] bg-cyan-500/60 w-full" />
                        <ChevronRight className="h-3 w-3 text-cyan-500/80 absolute -right-1 shrink-0" />
                      </div>
                    ) : (
                      <div className="w-full flex items-center relative">
                        <ChevronLeft className="h-3 w-3 text-cyan-500/80 absolute -left-1 shrink-0" />
                        <div className="h-[1px] bg-cyan-500/60 w-full" />
                      </div>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          })}
        </div>
      </div>
    </div>
  );
};

const cleanStructuredEvents = (text: string): string => {
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
  
  // Strip any lingering __AGENT__:... patterns (with or without trailing newline)
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
};

const renderMessageContent = (content: string) => {
  if (!content) return null;
  const cleanedContent = cleanStructuredEvents(content);
  if (!cleanedContent) return null;
  const lines = cleanedContent.split("\n");
  const elements: React.ReactNode[] = [];
  let currentTableHeaders: string[] = [];
  let currentTableRows: string[][] = [];
  let isInsideTable = false;
  let isInsideMermaid = false;
  let mermaidText = "";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith("```mermaid")) {
      isInsideMermaid = true;
      mermaidText = "";
      continue;
    }
    if (isInsideMermaid) {
      if (trimmed.startsWith("```")) {
        isInsideMermaid = false;
        const mermaidData = parseMermaidSequence(mermaidText);
        elements.push(<RenderSequenceDiagram key={`mermaid-${i}`} data={mermaidData} />);
        continue;
      }
      mermaidText += line + "\n";
      continue;
    }
    if (trimmed.startsWith("```")) continue;

    if (trimmed.includes("|")) {
      isInsideTable = true;
      const cells = trimmed
        .split("|")
        .map((c) => c.trim())
        .filter((c) => c.length > 0);
      if (cells.every((c) => /^:?-+:?$/.test(c))) continue;
      if (currentTableHeaders.length === 0) currentTableHeaders = cells;
      else currentTableRows.push(cells);
      continue;
    } else {
      if (isInsideTable) {
        elements.push(
          <RenderTable
            key={`table-${i}`}
            data={{ headers: currentTableHeaders, rows: currentTableRows }}
          />
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

  if (isInsideTable && currentTableHeaders.length > 0)
    elements.push(
      <RenderTable
        key="table-final"
        data={{ headers: currentTableHeaders, rows: currentTableRows }}
      />
    );
  return <div className="flex flex-col gap-1 w-full">{elements}</div>;
};

const renderStructuredCard = (payload: StructuredAgentResponse | null) => {
  if (!payload) return null;
  return (
    <div className="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-4 text-sm text-neutral-200">
      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-cyan-300">
        Structured Response
      </div>
      <div className="space-y-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-neutral-400">Issue Summary</div>
          <div className="mt-1">{payload.issue_summary}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wider text-neutral-400">
            Mandatory Prechecks
          </div>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {payload.mandatory_prechecks.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wider text-neutral-400">Depends On</div>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {payload.depends_on.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wider text-neutral-400">Assignment Target</div>
          <div className="mt-1 font-mono text-cyan-300">{payload.assignment_target}</div>
        </div>
        {payload.message ? (
          <div>
            <div className="text-xs uppercase tracking-wider text-neutral-400">Message</div>
            <div className="mt-1">{payload.message}</div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

// ====================================================================
// COMPONENT MAIN
// ====================================================================

interface MessageItemProps {
  message: ChatMessage;
  isLastMessage: boolean;
  loading: boolean;
  activePersona: string;
  statusMessage: string;
  globalStructuredResponse: StructuredAgentResponse | null;
}

export function MessageItem({
  message,
  isLastMessage,
  loading,
  activePersona,
  statusMessage,
  globalStructuredResponse,
}: MessageItemProps) {
  const isAssistant = message.role === "assistant";
  const persona = message.persona || activePersona;
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const [chartScreenshot, setChartScreenshot] = useState<string | null>(null);
  const statsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showInfo && statsRef.current) {
      const timer = setTimeout(() => {
        statsRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [showInfo]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <div className={cn("flex gap-3 w-full py-2", isAssistant ? "justify-start" : "justify-end")}>
      {isAssistant && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
          {persona === "Cognitive Operation & Customer Center" ? (
            <Brain className="h-5 w-5 text-pink-400 animate-pulse" />
          ) : persona === "Mobile Core Analyst" ? (
            <Phone className="h-5 w-5 text-cyan-400 animate-pulse" />
          ) : (
            <Bot className="h-5 w-5 text-cyan-400" />
          )}
        </div>
      )}
      <div className={cn("flex flex-col max-w-[80%]", isAssistant ? "items-start" : "items-end")}>
        {isAssistant ? (
          <div className="flex items-baseline gap-2 mb-1.5 ml-1 select-none">
            <span className="text-sm font-semibold text-white">{persona}</span>
            <span className="text-[10px] text-neutral-500/80 font-mono font-medium">
              {formatTimestamp(message.created_at)}
            </span>
          </div>
        ) : (
          <div className="flex items-baseline gap-2 mb-1.5 mr-1 select-none">
            <span className="text-[10px] text-neutral-500/80 font-mono font-medium">
              {formatTimestamp(message.created_at)}
            </span>
          </div>
        )}
        {isAssistant && (
          <ThoughtsAccordion
            thoughts={message.thoughts}
            durationSeconds={message.durationSeconds}
            isLastMessage={isLastMessage}
            loading={loading}
          />
        )}
        {/* Render text bubble if visible (also show if chartOptions are present) */}
        {(message.content || message.chartOptions) && (!(isAssistant && persona === "Mobile Core Analyst") || (!message.structuredResponse && !globalStructuredResponse)) && (
          <div
            className={cn(
              "rounded-2xl px-4 py-3 text-sm w-full",
              isAssistant ? `${glassSurfaceStatic} whitespace-normal` : "bg-cyan-500/20 text-white whitespace-pre-wrap"
            )}
            style={
              isAssistant && isLastMessage && !loading
                ? { animation: "ghost-unveil 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards" }
                : undefined
            }
          >
            {/* Only show text content when there are no chart pills (the pills are the answer) */}
            {message.chartOptions && message.chartOptions.length > 0
              ? null
              : message.content && (isAssistant ? renderMessageContent(message.content) : message.content)
            }
            {isAssistant && message.chartOptions && message.chartOptions.length > 0 && (
              <div>
                <ChartPillPicker
                  options={message.chartOptions}
                  preSelectedId={message.preSelectedDomId || null}
                  apiBase={CHART_API_BASE}
                  onCapture={(screenshot) => setChartScreenshot(screenshot)}
                />
              </div>
            )}
            {chartScreenshot && (
              <div className="mt-3 rounded-lg overflow-hidden border border-white/10">
                <img
                  src={`data:image/png;base64,${chartScreenshot}`}
                  alt="Chart screenshot"
                  className="w-full h-auto"
                  onError={() => setChartScreenshot(null)}
                />
              </div>
            )}
          </div>
        )}

        {/* Render structured card if present */}
        {isAssistant &&
          renderStructuredCard((message.structuredResponse || globalStructuredResponse) ?? null)}

        {/* Render Action Row and Stats Accordion */}
        {(message.content || message.chartOptions || message.structuredResponse || globalStructuredResponse) && (
          <div className={cn("flex flex-col w-full", isAssistant ? "items-start" : "items-end")}>
            {/* Sleek Action Row */}
            <div className="flex items-center gap-1.5 mt-1.5 px-1 select-none">
              <button
                onClick={handleCopy}
                className="text-neutral-500/60 hover:text-cyan-400 transition-colors p-1 rounded hover:bg-white/5 cursor-pointer focus:outline-none flex items-center justify-center select-none"
                title="Copy to clipboard"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
              
              {isAssistant && (
                <>
                  <button
                    onClick={() => setFeedback(feedback === "up" ? null : "up")}
                    className={cn(
                      "transition-colors p-1 rounded hover:bg-white/5 cursor-pointer focus:outline-none flex items-center justify-center select-none",
                      feedback === "up" ? "text-emerald-400" : "text-neutral-500/60 hover:text-cyan-400"
                    )}
                    title="Thumbs up"
                  >
                    <ThumbsUp className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setFeedback(feedback === "down" ? null : "down")}
                    className={cn(
                      "transition-colors p-1 rounded hover:bg-white/5 cursor-pointer focus:outline-none flex items-center justify-center select-none",
                      feedback === "down" ? "text-rose-400" : "text-neutral-500/60 hover:text-cyan-400"
                    )}
                    title="Thumbs down"
                  >
                    <ThumbsDown className="h-3.5 w-3.5" />
                  </button>

                  {(message.tokens_consumed != null || message.tokens_per_second != null) && (
                    <button
                      onClick={() => setShowInfo(!showInfo)}
                      className={cn(
                        "transition-colors p-1 rounded hover:bg-white/5 cursor-pointer focus:outline-none flex items-center justify-center select-none",
                        showInfo ? "text-cyan-400" : "text-neutral-500/60 hover:text-cyan-400"
                      )}
                      title="Generation statistics"
                    >
                      <Info className="h-3.5 w-3.5" />
                    </button>
                  )}
                </>
              )}
            </div>

            {/* Sleek info accordion stats container */}
            {isAssistant && showInfo && (message.tokens_consumed != null || message.tokens_per_second != null) && (
              <div ref={statsRef} className="mt-1.5 p-2 rounded-lg bg-white/[0.03] border border-white/5 text-[10px] text-neutral-400 font-mono flex items-center gap-3 select-none ml-1 animate-qna-fade-in">
                {message.tokens_per_second != null && (
                  <div>
                    <span className="text-neutral-500">speed:</span>{" "}
                    <span className="text-cyan-400 font-medium">{message.tokens_per_second.toFixed(1)} t/s</span>
                  </div>
                )}
                {message.tokens_consumed != null && (
                  <>
                    <div className="h-2 w-[1px] bg-white/10" />
                    <div>
                      <span className="text-neutral-500">tokens:</span>{" "}
                      <span className="text-pink-400 font-medium">{message.tokens_consumed}</span>
                    </div>
                  </>
                )}
                {message.latency_ms != null && (
                  <>
                    <div className="h-2 w-[1px] bg-white/10" />
                    <div>
                      <span className="text-neutral-500">latency:</span>{" "}
                      <span className="text-emerald-400 font-medium">{(message.latency_ms / 1000).toFixed(2)}s</span>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}
        {isAssistant && isLastMessage && loading && statusMessage && (
          <div className="mt-2 inline-flex w-fit items-center gap-2 rounded border border-white/5 bg-black/20 px-2 py-1 text-xs font-mono text-neutral-400 ml-1">
            <Loader2 className="h-3 w-3 animate-spin text-cyan-500" />
            <span className="animate-pulse">{statusMessage}</span>
          </div>
        )}
      </div>
      {!isAssistant && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5">
          <User className="h-5 w-5 text-neutral-400" />
        </div>
      )}
    </div>
  );
}
