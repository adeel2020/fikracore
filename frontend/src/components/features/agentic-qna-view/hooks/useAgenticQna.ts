"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  fetchQnaHealth,
  streamOrchestrateMessage,
  fetchQnaTelemetry,
  fetchSkills,
  type ChatMessage,
  type ChartOptionItem,
  type QnaTelemetry,
  type SkillItem,
  streamMobileCoreAnalystMessage,
} from "@/lib/api/qna";
import { StructuredAgentResponse } from "../types/agentic-qna.types";

export const DEFAULT_TELEMETRY = {
  memoryPct: 0,
  cachePct: 0,
  tokens: 0,
  cost: 0.0,
  throughput: 0.0,
  latency: 0,
  contextUsed: 0,
  contextWindow: "50K",
};

export const MAX_PAGE_INDEX = 8;

export function classifyQuery(
  query: string
): "Data Storyteller" | "QnA Assistant" | "Cognitive Operation & Customer Center" {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return "Data Storyteller";

  if (
    ["cognitive operator", "cognitive", "customer center", "diagnostics", "plan"].some((kw) =>
      normalized.includes(kw)
    )
  ) {
    return "Cognitive Operation & Customer Center";
  }

  const interrogativeWords = [
    "what",
    "who",
    "when",
    "where",
    "why",
    "how",
    "is",
    "are",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "would",
    "which",
  ];

  const isInterrogative =
    interrogativeWords.some((word) => normalized.startsWith(word)) ||
    normalized.endsWith("?");

  return isInterrogative ? "QnA Assistant" : "Data Storyteller";
}

export const getDynamicStatusMessage = (text: string, currentAgent: string): string => {
  if (!text) return `[${currentAgent}] Initializing...`;
  
  const lower = text.toLowerCase();
  
  // 1. Check for Action / Tool Call
  if (lower.includes("action:")) {
    const actionIdx = lower.lastIndexOf("action:");
    const lineEnd = text.indexOf("\n", actionIdx);
    const actionLine = lineEnd !== -1 
      ? text.substring(actionIdx, lineEnd) 
      : text.substring(actionIdx);
      
    const toolName = actionLine.replace(/action\s*:/i, "").trim();
    if (toolName) {
      if (toolName.includes("query_causal_knowledge_graph")) {
        return `[${currentAgent}] Querying Causal Knowledge Graph...`;
      }
      if (toolName.includes("trace_causal_chain")) {
        return `[${currentAgent}] Tracing causal relationships...`;
      }
      if (toolName.includes("execute_sql_query")) {
        return `[${currentAgent}] Querying database registry (SQL)...`;
      }
      if (toolName.includes("evaluate_prechecks")) {
        return `[${currentAgent}] Evaluating core network prechecks...`;
      }
      return `[${currentAgent}] Executing tool: ${toolName}...`;
    }
  }
  
  // 2. Check for Thought/Reasoning
  if (lower.includes("thought:")) {
    const thoughtIdx = lower.lastIndexOf("thought:");
    const lineEnd = text.indexOf("\n", thoughtIdx);
    const thoughtLine = lineEnd !== -1 
      ? text.substring(thoughtIdx, lineEnd) 
      : text.substring(thoughtIdx);
      
    const thoughtText = thoughtLine.replace(/thought\s*:/i, "").trim();
    if (thoughtText && thoughtText.length > 5) {
      return `[${currentAgent}] ${thoughtText.substring(0, 65)}${thoughtText.length > 65 ? "..." : ""}`;
    }
  }
  
  return `[${currentAgent}] Analyzing and routing complaint...`;
};

export function extractStructuredPayload(text: string) {
  const startMarker = "__STRUCTURED_EVENT__";
  const endMarker = "__END_STRUCTURED_EVENT__";
  const startIndex = text.lastIndexOf(startMarker);
  const endIndex = text.lastIndexOf(endMarker);

  if (startIndex === -1) {
    return { content: text, structured: null as StructuredAgentResponse | null };
  }

  if (endIndex === -1 || endIndex <= startIndex) {
    return {
      content: text.substring(0, startIndex).trimEnd(),
      structured: null as StructuredAgentResponse | null,
    };
  }

  const content = text.substring(0, startIndex).trimEnd();
  const block = text.substring(startIndex + startMarker.length, endIndex).trim();
  const lines = block
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const structured: StructuredAgentResponse = {
    issue_summary: "",
    mandatory_prechecks: [],
    depends_on: [],
    assignment_target: "",
    message: null,
  };

  let currentSection: "mandatory_prechecks" | "depends_on" | null = null;
  for (const line of lines) {
    if (line.startsWith("issue_summary:")) {
      structured.issue_summary = line.slice("issue_summary:".length).trim();
      currentSection = null;
      continue;
    }
    if (line.startsWith("mandatory_prechecks:")) {
      currentSection = "mandatory_prechecks";
      continue;
    }
    if (line.startsWith("depends_on:")) {
      currentSection = "depends_on";
      continue;
    }
    if (line.startsWith("assignment_target:")) {
      structured.assignment_target = line.slice("assignment_target:".length).trim();
      currentSection = null;
      continue;
    }
    if (line.startsWith("message:")) {
      structured.message = line.slice("message:".length).trim() || null;
      currentSection = null;
      continue;
    }
    if (line.startsWith("- ") && currentSection) {
      const value = line.slice(2).trim();
      structured[currentSection].push(value);
    }
  }

  return {
    content,
    structured: structured.issue_summary || structured.assignment_target ? structured : null,
  };
}

/**
 * Strips raw JSON objects/arrays that leaked from tool outputs or signal data
 * into visible message content. These are not intended for display.
 */
export function stripLeakedJson(text: string): string {
  if (!text) return "";
  let result = text;

  // Strip standalone JSON objects on their own lines (tool output dumps)
  result = result.replace(/^\s*\{[\s\S]*?\}\s*$/gm, (match) => {
    try {
      const parsed = JSON.parse(match.trim());
      if (typeof parsed === "object" && parsed !== null) return "";
    } catch {
      // Not valid JSON, leave it
    }
    return match;
  });

  // Strip inline JSON objects like {"key": "value", ...} embedded in prose
  result = result.replace(
    /\{(?:"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\})(?:\s*,\s*"[^"]*"\s*:\s*(?:"[^"]*"|[\d.]+|true|false|null|\[[^\]]*\]|\{[^}]*\}))*)\}/g,
    ""
  );

  return result.trim();
}

export function useAgenticQna() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState(DEFAULT_TELEMETRY);
  const [agentMode, setAgentMode] = useState<string>("…");
  const [loading, setLoading] = useState(false);
  const [currentStreamingAgent, setCurrentStreamingAgent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [showHistory, setShowHistory] = useState(true);
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionPreviews, setSessionPreviews] = useState<Record<string, string>>({});
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);
  const [activePersona, setActivePersona] = useState<string>("Data Storyteller");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [pinnedSessionIds, setPinnedSessionIds] = useState<string[]>([]);
  const [availableSkills, setAvailableSkills] = useState<SkillItem[]>([]);
  const [activeSkillIndex, setActiveSkillIndex] = useState(0);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [structuredResponse, setStructuredResponse] = useState<StructuredAgentResponse | null>(null);

  const [activeIndex, setActiveIndex] = useState(0);

  const scrollRef = useRef<HTMLDivElement>(null);
  const lastScrolledIndexRef = useRef<number>(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const activeSessionIdRef = useRef<string | null>(null);
  const activeIndexRef = useRef(0);

  useEffect(() => {
    activeIndexRef.current = activeIndex;
  }, [activeIndex]);

  useEffect(() => {
    activeSessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    fetchSkills()
      .then(setAvailableSkills)
      .catch((err) => console.error("Error fetching skills:", err));
  }, []);

  useEffect(() => {
    setActiveSkillIndex(0);
  }, [input]);

  useEffect(() => {
    if (messages.length === 0 && !loading && scrollContainerRef.current) {
      const clientWidth = scrollContainerRef.current.clientWidth;
      scrollContainerRef.current.scrollTo({
        left: activeIndex * clientWidth,
        behavior: "instant",
      });
    }
  }, [messages.length, loading, activeIndex]);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollLeft, clientWidth } = scrollContainerRef.current;
    if (clientWidth <= 0) return;

    const pageFraction = scrollLeft / clientWidth;
    const roundedIndex = Math.min(Math.max(Math.round(pageFraction), 0), MAX_PAGE_INDEX);

    if (roundedIndex !== activeIndex) {
      setActiveIndex(roundedIndex);
    }
  };

  const scroll = (direction: "left" | "right") => {
    if (scrollContainerRef.current) {
      const clientWidth = scrollContainerRef.current.clientWidth;
      let nextIndex = activeIndex;
      if (direction === "left") {
        nextIndex = Math.max(0, activeIndex - 1);
      } else {
        nextIndex = Math.min(MAX_PAGE_INDEX, activeIndex + 1);
      }

      scrollContainerRef.current.scrollTo({
        left: nextIndex * clientWidth,
        behavior: "smooth",
      });
      setActiveIndex(nextIndex);
    }
  };

  const scrollToPage = (pageIndex: number) => {
    if (scrollContainerRef.current) {
      const clientWidth = scrollContainerRef.current.clientWidth;
      scrollContainerRef.current.scrollTo({
        left: pageIndex * clientWidth,
        behavior: "smooth",
      });
      setActiveIndex(pageIndex);
    }
  };

  useEffect(() => {
    fetchQnaHealth()
      .then((h) => {
        setBackendOnline(true);
        setAgentMode(h.agent_mode);
      })
      .catch(() => {
        setBackendOnline(false);
        setAgentMode("offline");
      });

    const fetchSessions = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/history/sessions");
        const data = await res.json();
        if (Array.isArray(data)) {
          setSessions(data);
          const previews: Record<string, string> = {};
          for (const session of data) {
            previews[session.session_id] = session.preview || "No messages";
          }
          setSessionPreviews(previews);
        }
      } catch {
        // Silently fail
      }
    };

    fetchSessions();

    const stored = localStorage.getItem("pinned_sessions");
    if (stored) {
      try {
        setPinnedSessionIds(JSON.parse(stored));
      } catch {
        // ignore
      }
    }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      const lastMsgIdx = messages.length - 1;
      const lastMsg = messages[lastMsgIdx];
      if (lastMsg) {
        const isTraceAnalyzer = lastMsg.role === "assistant" && lastMsg.content?.includes("```mermaid");
        if (isTraceAnalyzer) {
          if (lastScrolledIndexRef.current !== lastMsgIdx) {
            lastScrolledIndexRef.current = lastMsgIdx;
            const messageElements = scrollRef.current.children;
            if (messageElements.length > 0) {
              const lastEl = messageElements[messageElements.length - 1] as HTMLElement;
              if (lastEl) {
                lastEl.scrollIntoView({ behavior: "smooth", block: "start" });
              }
            }
          }
        } else {
          lastScrolledIndexRef.current = -1;
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      } else {
        lastScrolledIndexRef.current = -1;
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }
  }, [messages, loading]);

  const getSkillRole = (query: string): string | null => {
    const trimmed = query.trim();
    if (trimmed.startsWith("/")) {
      const skillName = trimmed.split(" ")[0].substring(1);
      const skill = availableSkills.find((s) => s.name === skillName);
      return skill?.role || "Specialist Agent";
    }
    return null;
  };

  const reconnectOngoingStream = async (queryText: string, activeSessionId: string, persona: string) => {
    setError(null);
    setLoading(true);
    setCurrentStreamingAgent(null);
    setStatusMessage("Reconnecting to ongoing background agent...");
    setStructuredResponse(null);

    let accumulatedRaw = "";
    let streamBuffer = "";
    let chartOptions: ChartOptionItem[] | undefined = undefined;
    let preSelectedDomId: string | null = null;
    const currentStatusSteps = ["Reconnecting to ongoing background agent..."];
    const startTime = Date.now();

    try {
      let activeAgent = persona;
      const isMobileCoreQuery =
        (activeIndexRef.current === 6 || persona === "Mobile Core Analyst") &&
        !queryText.trim().startsWith("/");
        
      if (isMobileCoreQuery) {
        const userRole = activeIndexRef.current === 5 ? "Customer_Ops" : "Network_Eng";
        await streamMobileCoreAnalystMessage(queryText, activeSessionId, userRole, (chunk) => {
          if (activeSessionIdRef.current !== activeSessionId) return;
          streamBuffer += chunk;
          const agentPattern = /__AGENT__:(.*?)\n/g;
          let match;
          let currentAgent = "Senior Mobile Core Analyst";
          while ((match = agentPattern.exec(streamBuffer)) !== null) {
            const agentRole = match[1].trim();
            if (agentRole) {
              activeAgent = agentRole;
              currentAgent = agentRole;
              setCurrentStreamingAgent(agentRole);
              setStatusMessage(`[${agentRole}] Thinking! …`);
            }
          }
          const cleanChunk = streamBuffer.replace(/__AGENT__:.*?\n/g, "");
          const { content: textChunk, structured: parsedStructuredResponse } = extractStructuredPayload(cleanChunk);
          const lastAgentIdx = textChunk.indexOf("__AGENT__");
          let finalCleanedText = textChunk;
          if (lastAgentIdx !== -1) finalCleanedText = textChunk.substring(0, lastAgentIdx);
          accumulatedRaw = finalCleanedText;
          
          let thoughtsPart = "";
          let contentPart = "";
          const marker = "final answer:";
          const lowerRaw = accumulatedRaw.toLowerCase();
          if (lowerRaw.includes(marker)) {
            const index = lowerRaw.lastIndexOf(marker);
            thoughtsPart = accumulatedRaw.substring(0, index).trim();
            let rawContent = accumulatedRaw.substring(index + marker.length);
            if (rawContent.startsWith(":")) rawContent = rawContent.substring(1);
            contentPart = rawContent.trimStart();
          } else {
            const isReasoning =
              activeAgent !== "System Validator" &&
              (persona === "Mobile Core Analyst" ||
               activeAgent === "Mobile Core Analyst" ||
               activeAgent === "Customer Complaint Analyst" ||
               lowerRaw.includes("thought:") ||
               lowerRaw.includes("action:") ||
               lowerRaw.includes("observation:") ||
               accumulatedRaw.trim().startsWith("{") ||
               accumulatedRaw.trim().startsWith("["));
            if (isReasoning) {
              thoughtsPart = accumulatedRaw;
              contentPart = "";
            } else {
              thoughtsPart = "";
              contentPart = accumulatedRaw;
            }
          }
          contentPart = stripLeakedJson(contentPart);
          const elapsed = Math.round((Date.now() - startTime) / 1000);
          setMessages((prev) => {
            const updated = [...prev];
            if (updated.length > 0) {
              updated[updated.length - 1] = {
                role: "assistant",
                content: contentPart,
                thoughts: thoughtsPart,
                statusSteps: [
                  "Vector search completed",
                  "Retrieval confidence checked",
                  `Agent [${currentAgent}] executing...`,
                ],
                persona: "Mobile Core Analyst",
                durationSeconds: elapsed || 1,
                structuredResponse: parsedStructuredResponse ?? undefined,
              };
            }
            return updated;
          });
        });

        if (activeSessionIdRef.current === activeSessionId) {
          fetchQnaTelemetry(activeSessionId)
            .then((tel) => {
              if (activeSessionIdRef.current === activeSessionId) {
                setTelemetry({
                  memoryPct: tel.memory_pct ?? 0,
                  cachePct: tel.token_cache_pct ?? 0,
                  tokens: tel.tokens_consumed ?? 0,
                  cost: tel.token_cost ?? 0.0,
                  throughput: tel.tokens_per_second ?? 0.0,
                  latency: tel.latency_ms ?? 0,
                  contextUsed: tel.estimated_tokens ?? 0,
                  contextWindow: tel.context_window ?? "50K",
                });
                setMessages((prev) => {
                  const updated = [...prev];
                  if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                    updated[updated.length - 1] = {
                      ...updated[updated.length - 1],
                      tokens_consumed: tel.tokens_consumed,
                      tokens_per_second: tel.tokens_per_second,
                      latency_ms: tel.latency_ms,
                    };
                  }
                  return updated;
                });
              }
            })
            .catch((err) => console.error("Telemetry fetch error:", err));
        }
      } else {
        // Orchestrated query
        await streamOrchestrateMessage(queryText, activeSessionId, (chunk) => {
          if (activeSessionIdRef.current !== activeSessionId) return;
          streamBuffer += chunk;
          const agentPattern = /__AGENT__:(.*?)\n/g;
          let match;
          while ((match = agentPattern.exec(streamBuffer)) !== null) {
            const agentRole = match[1].trim();
            if (agentRole) {
              activeAgent = agentRole;
              setCurrentStreamingAgent(agentRole);
              setStatusMessage(`[${agentRole}] Thinking! …`);
              setMessages((prev) => {
                const updated = [...prev];
                if (updated.length > 0) {
                  updated[updated.length - 1] = { ...updated[updated.length - 1], persona: agentRole };
                }
                return updated;
              });
            }
          }
          const cleanChunk = streamBuffer.replace(/__AGENT__:.*?\n/g, "");
          const { content: textChunk, structured: parsedStructuredResponse } = extractStructuredPayload(cleanChunk);
          const lastAgentIdx = textChunk.indexOf("__AGENT__");
          let finalCleanedText = textChunk;
          if (lastAgentIdx !== -1) finalCleanedText = textChunk.substring(0, lastAgentIdx);
          accumulatedRaw = finalCleanedText;
          let thoughtsPart = "";
          let contentPart = "";

          // Detect JSON with chart_options from RAG chart queries
          const trimmed = accumulatedRaw.trim();
          let isChartJson = false;
          if (trimmed.startsWith("{") && trimmed.includes('"chart_options"')) {
            try {
              const parsed = JSON.parse(trimmed);
              if (parsed.chart_options && Array.isArray(parsed.chart_options)) {
                chartOptions = parsed.chart_options;
                preSelectedDomId = parsed.pre_selected_dom_id || null;
                contentPart = "";
                thoughtsPart = parsed.rag_retrievals || parsed.answer || "";
                isChartJson = true;
              }
            } catch {}
          }

          if (!isChartJson) {
            const marker = "final answer:";
            const lowerRaw = accumulatedRaw.toLowerCase();
            if (lowerRaw.includes(marker)) {
              const index = lowerRaw.lastIndexOf(marker);
              thoughtsPart = accumulatedRaw.substring(0, index).trim();
              let rawContent = accumulatedRaw.substring(index + marker.length);
              if (rawContent.startsWith(":")) rawContent = rawContent.substring(1);
              contentPart = rawContent.trimStart();
            } else {
              const isReasoning =
                activeAgent !== "System Validator" &&
                (persona === "Mobile Core Analyst" ||
                 activeAgent === "Mobile Core Analyst" ||
                 activeAgent === "Customer Complaint Analyst" ||
                 lowerRaw.includes("thought:") ||
                 lowerRaw.includes("action:") ||
                 lowerRaw.includes("observation:") ||
                 accumulatedRaw.trim().startsWith("{") ||
                 accumulatedRaw.trim().startsWith("["));
              if (isReasoning) {
                thoughtsPart = accumulatedRaw;
                contentPart = "";
              } else {
                thoughtsPart = "";
                contentPart = accumulatedRaw;
              }
            }
            contentPart = stripLeakedJson(contentPart);
          }
          const elapsed = Math.round((Date.now() - startTime) / 1000);
          setMessages((prev) => {
            const updated = [...prev];
            if (updated.length > 0) {
              updated[updated.length - 1] = {
                role: "assistant",
                content: contentPart,
                thoughts: thoughtsPart,
                statusSteps: currentStatusSteps,
                persona: activeAgent,
                durationSeconds: elapsed || 1,
                structuredResponse: parsedStructuredResponse ?? undefined,
                chartOptions: isChartJson ? chartOptions : undefined,
                preSelectedDomId: isChartJson ? preSelectedDomId : undefined,
              };
            }
            return updated;
          });
        });
      }
    } catch (err) {
      if (activeSessionIdRef.current === activeSessionId) {
        setError(err instanceof Error ? err.message : "Failed to reconnect to agent query");
        setMessages((prev) => {
          const updated = [...prev];
          if (updated.length > 0 && !accumulatedRaw) return updated.slice(0, -1);
          return updated;
        });
      }
    } finally {
      if (activeSessionIdRef.current === activeSessionId) {
        setLoading(false);
        setCurrentStreamingAgent(null);
        setStatusMessage("");
        inputRef.current?.focus();
      }
    }
  };

  const loadSession = async (sid: string) => {
    if (loadingSessionId === sid || sessionId === sid) return;

    setLoading(false);
    setStatusMessage("");
    setCurrentStreamingAgent(null);
    setError(null);

    const targetSession = sessions.find((s) => s.session_id === sid);
    if (targetSession && targetSession.message_count === 0) {
      setSessionId(sid);
      activeSessionIdRef.current = sid;
      setMessages([]);
      setTelemetry(DEFAULT_TELEMETRY);
      return;
    }

    setLoadingSessionId(sid);
    try {
      const res = await fetch(`http://localhost:8000/api/history/sessions/${sid}/messages`);
      if (!res.ok) throw new Error("Failed to fetch session");
      const data = await res.json();
      setSessionId(sid);
      activeSessionIdRef.current = sid;

      let reconnectQuery = "";
      let reconnectPersona = "";
      let shouldReconnect = false;

      const parsedMessages = (data.messages || []).map((msg: any, i: number) => {
        if (msg.role === "assistant") {
          const rawContent = msg.content || "";
          let thoughtsPart = "";
          let contentPart = "";
          let structuredResponseData: StructuredAgentResponse | null = null;
          let chartOptions: ChartOptionItem[] | undefined = undefined;
          let preSelectedDomId: string | null = null;
          
          // 1. Check for chart_options JSON first
          let isChartJson = false;
          const trimmed = rawContent.trim();
          if (trimmed.startsWith("{") && trimmed.includes('"chart_options"')) {
            try {
              const parsed = JSON.parse(trimmed);
              if (parsed.chart_options && Array.isArray(parsed.chart_options)) {
                chartOptions = parsed.chart_options;
                preSelectedDomId = parsed.pre_selected_dom_id || null;
                contentPart = "";
                thoughtsPart = parsed.rag_retrievals || parsed.answer || "";
                isChartJson = true;
              }
            } catch {}
          }

          if (!isChartJson) {
            // 2. Extract the structured payload first from the raw content
            const extracted = extractStructuredPayload(rawContent);
            const cleanedContent = extracted.content;
            structuredResponseData = extracted.structured;
            
            // 3. Split the cleaned content into thoughts and content parts
            const marker = "final answer:";
            const lowerContent = cleanedContent.toLowerCase();
            
            if (lowerContent.includes(marker)) {
              const index = lowerContent.lastIndexOf(marker);
              thoughtsPart = cleanedContent.substring(0, index).trim();
              let finalAnsContent = cleanedContent.substring(index + marker.length);
              if (finalAnsContent.startsWith(":")) {
                finalAnsContent = finalAnsContent.substring(1);
              }
              contentPart = finalAnsContent.trimStart();
            } else {
              const reactPattern = /\b(thought|action|action\s+input|observation)\b/i;
              if (reactPattern.test(cleanedContent)) {
                thoughtsPart = cleanedContent;
                contentPart = "";
              } else {
                thoughtsPart = "";
                contentPart = cleanedContent;
              }
            }
            
            contentPart = stripLeakedJson(contentPart);
          }
          const prevUserMsg = i > 0 ? data.messages[i - 1]?.content || "" : "";
          const skillRole = getSkillRole(prevUserMsg);
          const persona =
            msg.persona ||
            skillRole ||
            (structuredResponseData ? "Mobile Core Analyst" : classifyQuery(prevUserMsg));
            
          return {
            ...msg,
            thoughts: thoughtsPart,
            content: contentPart,
            persona,
            structuredResponse: structuredResponseData ?? undefined,
            chartOptions: isChartJson ? chartOptions : undefined,
            preSelectedDomId: isChartJson ? preSelectedDomId : undefined,
          };
        }
        return msg;
      });

      // Check if last message is from user (interrupted query)
      const lastMsg = parsedMessages[parsedMessages.length - 1];
      if (lastMsg && lastMsg.role === "user") {
        shouldReconnect = true;
        reconnectQuery = lastMsg.content;
        const skillRole = getSkillRole(reconnectQuery);
        reconnectPersona = skillRole || "Mobile Core Analyst";

        parsedMessages.push({
          role: "assistant",
          content: "",
          persona: reconnectPersona,
          created_at: Date.now() / 1000,
        });
      }

      setMessages(parsedMessages);

      const lastAssistant = [...parsedMessages].reverse().find((m) => m.role === "assistant");
      if (lastAssistant?.persona) setActivePersona(lastAssistant.persona);

      try {
        const tel = await fetchQnaTelemetry(sid);
        setTelemetry({
          memoryPct: tel.memory_pct ?? 0,
          cachePct: tel.token_cache_pct ?? 0,
          tokens: tel.tokens_consumed ?? 0,
          cost: tel.token_cost ?? 0.0,
          throughput: tel.tokens_per_second ?? 0.0,
          latency: tel.latency_ms ?? 0,
          contextUsed: tel.estimated_tokens ?? 0,
          contextWindow: tel.context_window ?? "50K",
        });
      } catch (telErr) {
        console.error("Error fetching telemetry for loaded session:", telErr);
        setTelemetry(DEFAULT_TELEMETRY);
      }

      if (shouldReconnect) {
        reconnectOngoingStream(reconnectQuery, sid, reconnectPersona);
      }

    } catch (err) {
      console.error("Error loading session:", err);
    } finally {
      setLoadingSessionId(null);
    }
  };

  const togglePinSession = (sid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPinnedSessionIds((prev) => {
      const isPinned = prev.includes(sid);
      const updated = isPinned ? prev.filter((id) => id !== sid) : [...prev, sid];
      localStorage.setItem("pinned_sessions", JSON.stringify(updated));
      return updated;
    });
  };

  const deleteSession = async (sid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat?")) return;
    const targetSession = sessions.find((s) => s.session_id === sid);
    const isUnsaved = targetSession && targetSession.message_count === 0;
    try {
      if (!isUnsaved) {
        const res = await fetch(`http://localhost:8000/api/history/sessions/${sid}`, {
          method: "DELETE",
        });
        if (!res.ok && res.status !== 404) throw new Error("Failed to delete session");
      }
      setSessions((prev) => prev.filter((s) => s.session_id !== sid));
      setPinnedSessionIds((prev) => {
        const updated = prev.filter((id) => id !== sid);
        localStorage.setItem("pinned_sessions", JSON.stringify(updated));
        return updated;
      });
      if (sessionId === sid) {
        setSessionId(null);
        activeSessionIdRef.current = null;
        setMessages([]);
        setTelemetry(DEFAULT_TELEMETRY);
      }
    } catch (err) {
      console.error("Error deleting session:", err);
      alert("Failed to delete session. Please try again.");
    }
  };

  const handleSuggestedPrompt = (promptText: string, route: string) => {
    let persona = "Data Storyteller";
    if (route === "Fast QnA") {
      persona = "QnA Assistant";
    } else if (route === "Cognitive Workflow") {
      persona = "Cognitive Operation & Customer Center";
    } else if (route === "Mobile Core Analyst") {
      persona = "Mobile Core Analyst";
    }
    setActivePersona(persona);
    setInput(promptText);
    setTimeout(() => {
      const formEvent = { preventDefault: () => {} } as React.FormEvent;
      handleSubmit(formEvent);
    }, 50);
  };

  const handlePageChipClick = (item: any) => {
    if (item.pageTarget !== undefined && item.pageTarget !== 0) {
      scrollToPage(item.pageTarget);
    } else {
      handleSuggestedPrompt(item.prompt, item.route);
    }
  };

  const handleSubmit = useCallback(
    async (e?: FormEvent) => {
      e?.preventDefault();
      const text = input.trim();
      if ((!text && !selectedSkill) || loading) return;

      setError(null);
      setLoading(true);
      setCurrentStreamingAgent(null);
      setStatusMessage("Agent executing in background workspace...");

      const fullText = selectedSkill ? `/${selectedSkill} ${text}`.trim() : text;

      const skillRole = getSkillRole(fullText);
      const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
      const persona =
        skillRole || (
          activeIndexRef.current === 6
            ? "Mobile Core Analyst"
            : lastAssistantMsg?.persona || classifyQuery(fullText)
        );
      setActivePersona(persona);

      setInput("");
      setSelectedSkill(null);
      setMessages((prev) => [...prev, { role: "user", content: fullText, created_at: Date.now() / 1000 }]);

      const activeSessionId = sessionId ?? crypto.randomUUID();
      if (!sessionId) {
        setSessionId(activeSessionId);
        activeSessionIdRef.current = activeSessionId;
      }

      setSessions((prev) => {
        const exists = prev.some((s) => s.session_id === activeSessionId);
        if (exists) {
          return prev.map((s) =>
            s.session_id === activeSessionId ? { ...s, message_count: s.message_count + 1 } : s
          );
        } else {
          return [
            {
              session_id: activeSessionId,
              message_count: 1,
              created_at: new Date().toISOString(),
              last_accessed: new Date().toISOString(),
            },
            ...prev,
          ];
        }
      });

      setSessionPreviews((prev) => ({
        ...prev,
        [activeSessionId]: fullText.substring(0, 60) + (fullText.length > 60 ? "..." : ""),
      }));

      setMessages((prev) => [...prev, { role: "assistant", content: "", persona, created_at: Date.now() / 1000 }]);
      setStructuredResponse(null);
      let accumulatedRaw = "";
      let streamBuffer = "";
      let chartOptions: ChartOptionItem[] | undefined = undefined;
      let preSelectedDomId: string | null = null;
      const currentStatusSteps = ["Agent executing in background workspace..."];
      const startTime = Date.now();

      try {
        let activeAgent = persona;
        const isMobileCoreQuery =
          (activeIndexRef.current === 6 || lastAssistantMsg?.persona === "Mobile Core Analyst") &&
          !fullText.trim().startsWith("/");
        if (isMobileCoreQuery) {
          const userRole = activeIndexRef.current === 5 ? "Customer_Ops" : "Network_Eng";
          await streamMobileCoreAnalystMessage(fullText, activeSessionId, userRole, (chunk) => {
            if (activeSessionIdRef.current !== activeSessionId) return;
            streamBuffer += chunk;
            const agentPattern = /__AGENT__:(.*?)\n/g;
            let match;
            let currentAgent = "Senior Mobile Core Analyst";
            while ((match = agentPattern.exec(streamBuffer)) !== null) {
              const agentRole = match[1].trim();
              if (agentRole) {
                activeAgent = agentRole;
                currentAgent = agentRole;
                setCurrentStreamingAgent(agentRole);
              }
            }
            setStatusMessage(getDynamicStatusMessage(streamBuffer, currentAgent));
            const cleanChunk = streamBuffer.replace(/__AGENT__:.*?\n/g, "");
            const { content: textChunk, structured: parsedStructuredResponse } = extractStructuredPayload(cleanChunk);
            const lastAgentIdx = textChunk.indexOf("__AGENT__");
            let finalCleanedText = textChunk;
            if (lastAgentIdx !== -1) finalCleanedText = textChunk.substring(0, lastAgentIdx);
            accumulatedRaw = finalCleanedText;
            
            let thoughtsPart = "";
            let contentPart = "";
            const marker = "final answer:";
            const lowerRaw = accumulatedRaw.toLowerCase();
            if (lowerRaw.includes(marker)) {
              const index = lowerRaw.lastIndexOf(marker);
              thoughtsPart = accumulatedRaw.substring(0, index).trim();
              let rawContent = accumulatedRaw.substring(index + marker.length);
              if (rawContent.startsWith(":")) rawContent = rawContent.substring(1);
              contentPart = rawContent.trimStart();
            } else {
              const isReasoning =
                activeAgent !== "System Validator" &&
                (persona === "Mobile Core Analyst" ||
                 activeAgent === "Mobile Core Analyst" ||
                 activeAgent === "Customer Complaint Analyst" ||
                 lowerRaw.includes("thought:") ||
                 lowerRaw.includes("action:") ||
                 lowerRaw.includes("observation:") ||
                 accumulatedRaw.trim().startsWith("{") ||
                 accumulatedRaw.trim().startsWith("["));
              if (isReasoning) {
                thoughtsPart = accumulatedRaw;
                contentPart = "";
              } else {
                thoughtsPart = "";
                contentPart = accumulatedRaw;
              }
            }
            contentPart = stripLeakedJson(contentPart);
            const elapsed = Math.round((Date.now() - startTime) / 1000);
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: contentPart,
                  thoughts: thoughtsPart,
                  statusSteps: [
                    "Vector search completed",
                    "Retrieval confidence checked",
                    `Agent [${currentAgent}] executing...`,
                  ],
                  persona: fullText.trim().startsWith("/") ? activeAgent : "Mobile Core Analyst",
                  durationSeconds: elapsed || 1,
                  structuredResponse: parsedStructuredResponse ?? undefined,
                };
              }
              return updated;
            });
          });

          if (activeSessionIdRef.current === activeSessionId) {
            setSessions((prev) =>
              prev.map((s) =>
                s.session_id === activeSessionId ? { ...s, message_count: s.message_count + 1 } : s
              )
            );
            try {
              const tel = await fetchQnaTelemetry(activeSessionId);
              setTelemetry({
                memoryPct: tel.memory_pct ?? 0,
                cachePct: tel.token_cache_pct ?? 0,
                tokens: tel.tokens_consumed ?? 0,
                cost: tel.token_cost ?? 0.0,
                throughput: tel.tokens_per_second ?? 0.0,
                latency: tel.latency_ms ?? 0,
                contextUsed: tel.estimated_tokens ?? 0,
                contextWindow: tel.context_window ?? "50K",
              });
              setMessages((prev) => {
                const updated = [...prev];
                if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    tokens_consumed: tel.tokens_consumed,
                    tokens_per_second: tel.tokens_per_second,
                    latency_ms: tel.latency_ms,
                  };
                }
                return updated;
              });
            } catch (err) {
              console.error("Failed to fetch telemetry after stream", err);
            }
          }
        } else {
          await streamOrchestrateMessage(fullText, activeSessionId, (chunk) => {
            if (activeSessionIdRef.current !== activeSessionId) return;
            streamBuffer += chunk;
            const agentPattern = /__AGENT__:(.*?)\n/g;
            let match;
            while ((match = agentPattern.exec(streamBuffer)) !== null) {
              const agentRole = match[1].trim();
              if (agentRole) {
                activeAgent = agentRole;
                setCurrentStreamingAgent(agentRole);
                setMessages((prev) => {
                  const updated = [...prev];
                  if (updated.length > 0) {
                    updated[updated.length - 1] = { ...updated[updated.length - 1], persona: agentRole };
                  }
                  return updated;
                });
              }
            }
            setStatusMessage(getDynamicStatusMessage(streamBuffer, activeAgent));
            const cleanChunk = streamBuffer.replace(/__AGENT__:.*?\n/g, "");
            const { content: textChunk, structured: parsedStructuredResponse } = extractStructuredPayload(cleanChunk);
            const lastAgentIdx = textChunk.indexOf("__AGENT__");
            let finalCleanedText = textChunk;
            if (lastAgentIdx !== -1) finalCleanedText = textChunk.substring(0, lastAgentIdx);
            accumulatedRaw = finalCleanedText;
            let thoughtsPart = "";
            let contentPart = "";

            // Detect JSON with chart_options from RAG chart queries
            const trimmed = accumulatedRaw.trim();
            let isChartJson = false;
            if (trimmed.startsWith("{") && trimmed.includes('"chart_options"')) {
              try {
                const parsed = JSON.parse(trimmed);
                if (parsed.chart_options && Array.isArray(parsed.chart_options)) {
                  chartOptions = parsed.chart_options;
                  preSelectedDomId = parsed.pre_selected_dom_id || null;
                  contentPart = parsed.answer || "";
                  thoughtsPart = parsed.rag_retrievals || "";
                  isChartJson = true;
                }
              } catch {}
            }

            if (!isChartJson) {
              const marker = "final answer:";
              const lowerRaw = accumulatedRaw.toLowerCase();
              if (lowerRaw.includes(marker)) {
                const index = lowerRaw.lastIndexOf(marker);
                thoughtsPart = accumulatedRaw.substring(0, index).trim();
                let rawContent = accumulatedRaw.substring(index + marker.length);
                if (rawContent.startsWith(":")) rawContent = rawContent.substring(1);
                contentPart = rawContent.trimStart();
              } else {
                const isReasoning =
                  activeAgent !== "System Validator" &&
                  (persona === "Mobile Core Analyst" ||
                   activeAgent === "Mobile Core Analyst" ||
                   activeAgent === "Customer Complaint Analyst" ||
                   lowerRaw.includes("thought:") ||
                   lowerRaw.includes("action:") ||
                   lowerRaw.includes("observation:") ||
                   accumulatedRaw.trim().startsWith("{") ||
                   accumulatedRaw.trim().startsWith("["));
                if (isReasoning) {
                  thoughtsPart = accumulatedRaw;
                  contentPart = "";
                } else {
                  thoughtsPart = "";
                  contentPart = accumulatedRaw;
                }
              }
              contentPart = stripLeakedJson(contentPart);
            }
            const elapsed = Math.round((Date.now() - startTime) / 1000);
            setMessages((prev) => {
              const updated = [...prev];
              if (updated.length > 0) {
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: contentPart,
                  thoughts: thoughtsPart,
                  statusSteps: currentStatusSteps,
                  persona: activeAgent,
                  durationSeconds: elapsed || 1,
                  structuredResponse: parsedStructuredResponse ?? undefined,
                  chartOptions: isChartJson ? chartOptions : undefined,
                  preSelectedDomId: isChartJson ? preSelectedDomId : undefined,
                };
              }
              return updated;
            });
          });

          if (activeSessionIdRef.current === activeSessionId) {
            setSessions((prev) =>
              prev.map((s) =>
                s.session_id === activeSessionId ? { ...s, message_count: s.message_count + 1 } : s
              )
            );
            fetchQnaTelemetry(activeSessionId)
              .then((tel) => {
                if (activeSessionIdRef.current === activeSessionId) {
                  setTelemetry({
                    memoryPct: tel.memory_pct ?? 0,
                    cachePct: tel.token_cache_pct ?? 0,
                    tokens: tel.tokens_consumed ?? 0,
                    cost: tel.token_cost ?? 0.0,
                    throughput: tel.tokens_per_second ?? 0.0,
                    latency: tel.latency_ms ?? 0,
                    contextUsed: tel.estimated_tokens ?? 0,
                    contextWindow: tel.context_window ?? "50K",
                  });
                  setMessages((prev) => {
                    const updated = [...prev];
                    if (updated.length > 0 && updated[updated.length - 1].role === "assistant") {
                      updated[updated.length - 1] = {
                        ...updated[updated.length - 1],
                        tokens_consumed: tel.tokens_consumed,
                        tokens_per_second: tel.tokens_per_second,
                        latency_ms: tel.latency_ms,
                      };
                    }
                    return updated;
                  });
                }
              })
              .catch((err) => console.error("Telemetry fetch error:", err));
          }
        }
      } catch (err) {
        if (activeSessionIdRef.current === activeSessionId) {
          setError(err instanceof Error ? err.message : "Failed to reach the agent API");
          setMessages((prev) => {
            const updated = [...prev];
            if (updated.length > 0 && !accumulatedRaw) return updated.slice(0, -1);
            return updated;
          });
          setInput(text);
        }
      } finally {
        if (activeSessionIdRef.current === activeSessionId) {
          setLoading(false);
          setCurrentStreamingAgent(null);
          setStatusMessage("");
          inputRef.current?.focus();
        }
      }
    },
    [input, loading, sessionId, selectedSkill, availableSkills, messages]
  );

  const handleNewChat = () => {
    setLoading(false);
    setStatusMessage("");
    setCurrentStreamingAgent(null);
    setError(null);

    const existingEmptySession = sessions.find(
      (s) =>
        s.message_count === 0 ||
        sessionPreviews[s.session_id] === "New Chat" ||
        sessionPreviews[s.session_id] === "No messages"
    );

    if (existingEmptySession) {
      setSessionId(existingEmptySession.session_id);
      activeSessionIdRef.current = existingEmptySession.session_id;
      setMessages([]);
      setTelemetry(DEFAULT_TELEMETRY);
    } else {
      const newSid = crypto.randomUUID();
      setSessions((prev) => [
        {
          session_id: newSid,
          message_count: 0,
          created_at: new Date().toISOString(),
          last_accessed: new Date().toISOString(),
        },
        ...prev,
      ]);
      setSessionPreviews((prev) => ({ ...prev, [newSid]: "New Chat" }));
      setSessionId(newSid);
      activeSessionIdRef.current = newSid;
      setMessages([]);
      setTelemetry(DEFAULT_TELEMETRY);
    }
  };

  const handleStop = () => {
    setLoading(false);
    setStatusMessage("");
    setCurrentStreamingAgent(null);
    activeSessionIdRef.current = null;
  };

  const handleSelectSkill = (skillName: string) => {
    setSelectedSkill(skillName);
    setInput("");
    inputRef.current?.focus();
  };

  const showSkillsPopup = input.startsWith("/");
  const filterQuery = showSkillsPopup ? input.slice(1).toLowerCase() : "";
  const filteredSkills = availableSkills.filter((skill) =>
    skill.name.toLowerCase().includes(filterQuery)
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showSkillsPopup && filteredSkills.length > 0) {
      if (e.key === "Tab" || e.key === "Enter") {
        e.preventDefault();
        handleSelectSkill(filteredSkills[activeSkillIndex].name);
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveSkillIndex((prev) => (prev + 1) % filteredSkills.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveSkillIndex((prev) => (prev - 1 + filteredSkills.length) % filteredSkills.length);
      } else if (e.key === "Escape") {
        e.preventDefault();
        setInput(input.replace(/^\//, ""));
      }
    } else if (e.key === "Backspace" && input === "" && selectedSkill) {
      e.preventDefault();
      setInput(`/${selectedSkill}`);
      setSelectedSkill(null);
    }
  };

  return {
    messages,
    setMessages,
    input,
    setInput,
    sessionId,
    setSessionId,
    telemetry,
    setTelemetry,
    agentMode,
    setAgentMode,
    loading,
    setLoading,
    currentStreamingAgent,
    setCurrentStreamingAgent,
    error,
    setError,
    backendOnline,
    setBackendOnline,
    showHistory,
    setShowHistory,
    sessions,
    setSessions,
    sessionPreviews,
    setSessionPreviews,
    loadingSessionId,
    setLoadingSessionId,
    activePersona,
    setActivePersona,
    statusMessage,
    setStatusMessage,
    pinnedSessionIds,
    setPinnedSessionIds,
    availableSkills,
    setAvailableSkills,
    activeSkillIndex,
    setActiveSkillIndex,
    selectedSkill,
    setSelectedSkill,
    structuredResponse,
    setStructuredResponse,
    activeIndex,
    setActiveIndex,
    scrollRef,
    inputRef,
    scrollContainerRef,
    handleScroll,
    scroll,
    scrollToPage,
    loadSession,
    togglePinSession,
    deleteSession,
    handleSuggestedPrompt,
    handlePageChipClick,
    handleSubmit,
    handleNewChat,
    handleStop,
    handleSelectSkill,
    handleKeyDown,
    showSkillsPopup,
    filteredSkills,
  };
}
