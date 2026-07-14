"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Search, 
  Activity, 
  Cpu, 
  Sparkles, 
  Server, 
  Check, 
  Loader2, 
  AlertCircle, 
  FileText,
  Workflow,
  ShieldCheck,
  LineChart,
  Trash2,
  Brain,
  ChevronDown,
  User,
  Bot,
  Copy
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API_BASE = "http://localhost:8000";

// Predefined validation queries matching the dataset ontology
const DEFAULT_EVAL_QUERIES = [
  "share the issue categories in descending order",
  "What is the total number of rows/tickets in the Operations_Dashboard_Data_Template.xlsx dataset?",
  "Which rejection reasons are present in the tickets and what are their occurrences?",
  "List the countries represented in the dataset along with their ticket frequencies."
];

// Query suggestions shown to support agents
const QUERY_SUGGESTIONS = [
  "share the issue categories in descending order",
  "What is the total number of rows/tickets in the Operations_Dashboard_Data_Template.xlsx dataset?",
  "Which rejection reasons are present in the tickets and what are their occurrences?",
  "List the countries represented in the dataset along with their ticket frequencies."
];


// ── ChartPillPicker ───────────────────────────────────────────────────────────
// Self-contained pill picker. Fetches pre-selected chart on mount if provided.
interface ChartOption { name: string; dom_id: string; }

export type { ChartOption };

function ChartPillPicker({
  options,
  preSelectedId,
  apiBase,
  onCapture,
}: {
  options: ChartOption[];
  preSelectedId: string | null;
  apiBase: string;
  onCapture: (screenshot: string) => void;
}) {
  const [activeId, setActiveId]   = React.useState<string | null>(null);
  const [capturedId, setCapturedId] = React.useState<string | null>(null);
  const hasFired = React.useRef(false);

  const fetchChart = React.useCallback(async (domId: string) => {
    setActiveId(domId);
    try {
      const res  = await fetch(`${apiBase}/rag/chart-screenshot/${domId}?_t=${Date.now()}`);
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();
      setCapturedId(domId);
      onCapture(data.chart_screenshot);
    } catch {
      // leave pills intact on error
    } finally {
      setActiveId(null);
    }
  }, [apiBase, onCapture]);

  // Auto-trigger pre-selected pill once on mount
  React.useEffect(() => {
    if (preSelectedId && !hasFired.current) {
      hasFired.current = true;
      fetchChart(preSelectedId);
    }
  }, [preSelectedId, fetchChart]);

  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => {
        const isCapturing = activeId === opt.dom_id;
        const isSelected  = capturedId === opt.dom_id && !activeId;
        const isDisabled  = !!activeId && !isCapturing;
        return (
          <button
            key={opt.dom_id}
            disabled={!!activeId}
            onClick={() => fetchChart(opt.dom_id)}
            className={[
              "px-3 py-1.5 rounded-lg border text-[11px] font-medium whitespace-nowrap select-none",
              "transition-all duration-300 ease-in-out",
              isCapturing
                ? "border-cyan-400/70 bg-cyan-500/15 text-cyan-300 scale-[1.03] shadow-[0_0_12px_rgba(34,211,238,0.25)] cursor-wait"
                : isSelected
                  ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-300"
                  : isDisabled
                    ? "border-white/5 bg-white/[0.02] text-neutral-600 opacity-30 cursor-not-allowed pointer-events-none"
                    : "border-white/10 bg-white/5 text-neutral-300 cursor-pointer hover:border-cyan-500/50 hover:bg-cyan-500/10 hover:text-cyan-300 hover:scale-[1.02] hover:shadow-[0_0_8px_rgba(34,211,238,0.12)]",
            ].join(" ")}
          >
            {isCapturing ? (
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping inline-block" />
                Capturing…
              </span>
            ) : opt.name}
          </button>
        );
      })}
    </div>
  );
}
// ─────────────────────────────────────────────────────────────────────────────

export { ChartPillPicker };

// Helper to parse and render answers containing markdown tables
const renderAnswerContent = (text: string) => {
  if (!text) return null;

  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentTableRows: string[][] = [];
  let inTable = false;

  const flushTable = (key: string) => {
    if (currentTableRows.length === 0) return;
    
    let hasDivider = false;
    let dataRows = [...currentTableRows];
    let headers: string[] = [];
    
    if (dataRows.length > 1 && dataRows[1].some(cell => cell.trim().startsWith("-") || cell.trim().includes("---"))) {
      hasDivider = true;
    }
    
    if (hasDivider) {
      headers = dataRows[0];
      dataRows = dataRows.slice(2);
    } else if (dataRows.length > 0) {
      headers = dataRows[0];
      dataRows = dataRows.slice(1);
    }
    
    elements.push(
      <div key={key} className="overflow-x-auto my-3.5 border border-white/5 rounded-xl bg-neutral-950/40">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-white/5 font-bold text-cyan-400">
              {headers.map((h, i) => (
                <th key={i} className="px-4 py-2.5 font-bold uppercase tracking-wider">{h.trim()}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((row, rowIndex) => (
              <tr key={rowIndex} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-4 py-2 text-neutral-300 font-mono">{cell.trim()}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    currentTableRows = [];
    inTable = false;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const isTableRow = line.trim().startsWith("|") && line.trim().endsWith("|");

    if (isTableRow) {
      if (!inTable) {
        inTable = true;
      }
      const cells = line.split("|").slice(1, -1);
      currentTableRows.push(cells);
    } else {
      if (inTable) {
        flushTable(`table-${i}`);
      }
      if (line.trim()) {
        elements.push(
          <p key={`p-${i}`} className="text-sm leading-relaxed text-neutral-200 mb-2.5 whitespace-pre-wrap select-text">
            {line}
          </p>
        );
      }
    }
  }

  if (inTable) {
    flushTable(`table-end`);
  }

  return elements;
};

// Collapsable thoughts accordion to display pre-processing SQL generation and vector routing steps
const ThoughtsAccordion: React.FC<{
  thoughts?: string;
  loading: boolean;
  durationSeconds?: number;
}> = ({ thoughts, loading, durationSeconds }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  useEffect(() => {
    if (loading && thoughts) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  }, [loading, thoughts]);

  if (!thoughts && !loading) return null;

  return (
    <details
      open={isOpen}
      onToggle={(e) => setIsOpen((e.target as HTMLDetailsElement).open)}
      className="group mt-1 w-full text-xs text-neutral-450 [&[open]_svg]:rotate-180"
    >
      <summary className="list-none [&::-webkit-details-marker]:hidden cursor-pointer font-sans font-normal text-neutral-400 hover:text-neutral-355 transition-colors inline-flex items-center gap-1 select-none focus:outline-none py-1 ml-1 select-none">
        <span>{loading ? "RAG Retrievals..." : `RAG Retrievals (${durationSeconds || 1}s)`}</span>
        <ChevronDown className="h-3.5 w-3.5 text-neutral-550 shrink-0 transition-transform duration-200" />
      </summary>
      <div className="mt-2 pl-3.5 whitespace-pre-wrap max-h-100 overflow-y-auto leading-relaxed border-l border-white/10 text-neutral-400 font-mono text-[10.5px] ml-1.5 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full">
        {thoughts || "Analyzing query and formulating search parameters..."}
      </div>
    </details>
  );
};

export const RagPanel: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<"query" | "eval">("query");
  
  // Chatbot states
  const [queryStr, setQueryStr] = useState("");
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [expandedLogIndex, setExpandedLogIndex] = useState<number | null>(null);
  const [loadingChartId, setLoadingChartId] = useState<string | null>(null);
  const [expandedImg, setExpandedImg] = useState<string | null>(null);
  const [copiedImg, setCopiedImg] = useState<string | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  const copyToClipboard = async (base64: string) => {
    const byteChars = atob(base64);
    const byteNums = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
      byteNums[i] = byteChars.charCodeAt(i);
    }
    const blob = new Blob([new Uint8Array(byteNums)], { type: "image/png" });
    await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
    setCopiedImg(base64);
    setTimeout(() => setCopiedImg(null), 2000);
  };
  
  // Evaluation states
  const [evaluating, setEvaluating] = useState(false);
  const [evalTaskId, setEvalTaskId] = useState<string | null>(null);
  const [evalStatus, setEvalStatus] = useState<any>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Load persistent states from LocalStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTab = localStorage.getItem("rag-active-tab");
      if (savedTab === "query" || savedTab === "eval") {
        setActiveSubTab(savedTab);
      }
      
      const savedQuery = localStorage.getItem("rag-query-str");
      if (savedQuery) {
        setQueryStr(savedQuery);
      }
      
      const savedMessages = localStorage.getItem("rag-chat-history");
      if (savedMessages) {
        try {
          setMessages(JSON.parse(savedMessages));
        } catch {
          localStorage.removeItem("rag-chat-history");
        }
      }
    }
  }, []);

  // Scroll to bottom when messages or loading changes
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loadingQuery]);


  // Poll Evaluation Status
  useEffect(() => {
    if (!evalTaskId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/rag/evaluate/status/${evalTaskId}`);
        if (!res.ok) throw new Error("Failed to fetch evaluation status.");
        const data = await res.json();
        setEvalStatus(data);
        
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          setEvaluating(false);
          setEvalTaskId(null);
          clearInterval(interval);
        }
      } catch (err: any) {
        setEvalError(err.message || "Failed to poll evaluation status.");
        setEvaluating(false);
        setEvalTaskId(null);
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [evalTaskId]);

  // Handle Tab switches
  const handleTabChange = (tab: "query" | "eval") => {
    setActiveSubTab(tab);
    localStorage.setItem("rag-active-tab", tab);
  };

  // Clear chat history
  const clearChat = () => {
    if (window.confirm("Are you sure you want to clear the chat history?")) {
      setMessages([]);
      localStorage.removeItem("rag-chat-history");
      setExpandedLogIndex(null);
    }
  };

  const saveMessages = (msgs: any[]) => {
    try {
      const trimmed = msgs.map((m: any) => ({
        ...m,
        chart_screenshot: undefined,
        source_nodes: undefined,
      }));
      localStorage.setItem("rag-chat-history", JSON.stringify(trimmed));
    } catch {
      // localStorage full — clear old history and retry once
      try {
        localStorage.removeItem("rag-chat-history");
        const trimmed = msgs.slice(-4).map((m: any) => ({
          ...m,
          chart_screenshot: undefined,
          source_nodes: undefined,
        }));
        localStorage.setItem("rag-chat-history", JSON.stringify(trimmed));
      } catch {}
    }
  };

  // Send message in Chatbot
  const executeQuery = async (queryOverride?: string) => {
    const activeQuery = queryOverride || queryStr;
    if (!activeQuery.trim() || loadingQuery) return;
    
    const userMsg = { role: "user", content: activeQuery };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setQueryStr("");
    setLoadingQuery(true);
    
    // Save in localStorage
    saveMessages(newMessages);
    
    const startTime = Date.now();
    try {
      // Package clean message history payload for backend
      const historyPayload = newMessages.slice(0, -1).map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const res = await fetch(`${API_BASE}/rag/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          query: activeQuery,
          chat_history: historyPayload
        })
      });
      if (!res.ok) throw new Error("Failed to execute RAG query.");
      const data = await res.json();
      
      const endTime = Date.now();
      const duration = Math.max(1, Math.round((endTime - startTime) / 1000));
      
      const assistantMsg = { 
        role: "assistant", 
        content: data.answer,
        source_nodes: data.source_nodes,
        hyde_query: data.hyde_query,
        graph_triples: data.graph_triples,
        rag_retrievals: data.rag_retrievals,
        chart_screenshot: data.chart_screenshot || null,
        chart_options: data.chart_options || null,
        pre_selected_dom_id: data.pre_selected_dom_id || null,
        durationSeconds: duration
      };
      
      const updatedMessages = [...newMessages, assistantMsg];
      setMessages(updatedMessages);
      saveMessages(updatedMessages);
    } catch (err: any) {
      const endTime = Date.now();
      const duration = Math.max(1, Math.round((endTime - startTime) / 1000));
      const assistantMsg = { 
        role: "assistant", 
        content: `Failed to retrieve answer: ${err.message || "Unknown error."}`,
        source_nodes: [],
        hyde_query: activeQuery,
        graph_triples: [],
        rag_retrievals: "Failed to complete query pre-processing.",
        durationSeconds: duration
      };
      const updatedMessages = [...newMessages, assistantMsg];
      setMessages(updatedMessages);
      saveMessages(updatedMessages);
    } finally {
      setLoadingQuery(false);
    }
  };


  // Run System evaluations
  const executeEvaluation = async () => {
    setEvaluating(true);
    setEvalError(null);
    setEvalStatus({ status: "PENDING", progress: 0.0 });
    try {
      const res = await fetch(`${API_BASE}/rag/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ queries: DEFAULT_EVAL_QUERIES })
      });
      if (!res.ok) throw new Error("Failed to trigger evaluation run.");
      const data = await res.json();
      setEvalTaskId(data.task_id);
    } catch (err: any) {
      setEvalError(err.message || "Failed to trigger evaluation.");
      setEvaluating(false);
    }
  };

  return (
    <div className="border border-white/5 bg-neutral-950 backdrop-blur-md rounded-2xl p-6 h-[680px] w-full flex flex-col gap-6 text-white overflow-hidden">
      
      {/* RAG Header & Subtabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 pb-4 gap-4">
        <div>
          <h3 className="text-lg font-bold text-cyan-400 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-cyan-400" />
            Enterprise Document RAG Console
          </h3>
          <p className="text-xs text-neutral-400 mt-1">
            Troubleshoot cases by querying unstructured document pools with concurrent Hybrid Graph-vector indexing.
          </p>
        </div>
        <div className="flex gap-1.5 bg-neutral-900/60 p-1 border border-white/5 rounded-xl self-start md:self-auto shrink-0 select-none">
          <button
            onClick={() => handleTabChange("query")}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all ${
              activeSubTab === "query" ? "bg-cyan-500 text-neutral-950 font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            Query Console
          </button>
          <button
            onClick={() => handleTabChange("eval")}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all ${
              activeSubTab === "eval" ? "bg-cyan-500 text-neutral-950 font-bold" : "text-neutral-400 hover:text-white"
            }`}
          >
            System Evaluation
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-y-auto pr-1">

        {/* Tab 1: Chat Console */}
        {activeSubTab === "query" && (
          <div className="flex flex-col h-full overflow-hidden">
            
            {/* Chat Header & Actions */}
            <div className="flex justify-between items-center border-b border-white/5 pb-2.5 mb-3.5 shrink-0">
              <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider">Active Dialogue Transcript</span>
              {messages.length > 0 && (
                <button
                  onClick={clearChat}
                  className="text-[10px] font-bold text-neutral-500 hover:text-rose-455 flex items-center gap-1.5 transition-all"
                  title="Reset Chat Session"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear Session
                </button>
              )}
            </div>

            {/* Chat Message Stream */}
            <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-4 mb-4 min-h-0">
              {messages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center py-12 border border-dashed border-white/5 rounded-2xl bg-neutral-900/10">
                  <Sparkles className="h-8 w-8 text-neutral-600 mb-2.5" />
                  <p className="text-sm text-neutral-400 font-semibold">RAG Conversational Assistant</p>
                  <p className="text-xs text-neutral-500 mt-1 max-w-sm text-center">
                    Ask dynamic follow-up questions about files in your registry. Frequencies and tables will render visually.
                  </p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className={`flex gap-3 w-full py-2 ${msg.role === "assistant" ? "justify-start" : "justify-end"}`}>
                    
                    {msg.role === "assistant" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 select-none">
                        <Brain className="h-5 w-5 text-pink-400 animate-pulse" />
                      </div>
                    )}
                    
                    <div className={`flex flex-col ${msg.role === "assistant" ? "items-start max-w-[80%]" : "items-end max-w-[80%]"}`}>
                      
                      {msg.role === "assistant" ? (
                        <div className="flex items-baseline gap-2 mb-1.5 ml-1 select-none">
                          <span className="text-sm font-semibold text-white">Report Analyst</span>
                          <span className="text-[10px] text-neutral-500/80 font-mono font-medium">
                            {/* Timestamp */}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-baseline gap-2 mb-1.5 mr-1 select-none">
                          <span className="text-[10px] text-neutral-500/80 font-mono font-medium">
                            {/* Timestamp */}
                          </span>
                        </div>
                      )}

                      {msg.role === "assistant" && (
                        <ThoughtsAccordion 
                          thoughts={msg.rag_retrievals} 
                          loading={loadingQuery && idx === messages.length - 1} 
                          durationSeconds={msg.durationSeconds}
                        />
                      )}

                      {/* Message Bubble */}
                      <div 
                        className={`rounded-2xl px-5 py-3 text-sm leading-relaxed relative overflow-hidden border w-full ${
                          msg.role === "user" 
                            ? "bg-cyan-950/20 border-cyan-500/20 text-neutral-100 rounded-tr-none" 
                            : "bg-white/5 border-white/5 text-neutral-200 rounded-tl-none"
                        }`}
                      >
                        {msg.role === "assistant" && (
                          <div className="absolute top-0 right-0 h-16 w-16 bg-cyan-500/5 rounded-full blur-xl pointer-events-none" />
                        )}
                        
                        {msg.role === "assistant" ? (
                          <div className="flex flex-col gap-3">
                            {/* ── Chart pills (always shown when chart_options present) ── */}
                            {msg.chart_options && (
                              <ChartPillPicker
                                options={msg.chart_options}
                                preSelectedId={msg.pre_selected_dom_id || null}
                                apiBase={API_BASE}
                                onCapture={(screenshot) => {
                                  setMessages(prev => {
                                    const updated = prev.map((m, i) =>
                                      i === idx ? { ...m, chart_screenshot: screenshot } : m
                                    );
                                    saveMessages(updated);
                                    return updated;
                                  });
                                }}
                              />
                            )}
                            {/* ── Screenshot result ── */}
                            {msg.chart_screenshot && (
                              <div className="relative group rounded-xl overflow-hidden border border-cyan-500/20 shadow-lg shadow-cyan-500/5 mt-1 max-w-[520px]">
                                <img
                                  src={`data:image/png;base64,${msg.chart_screenshot}`}
                                  alt="Dashboard chart screenshot"
                                  className="w-full h-auto max-h-100 object-contain rounded-xl cursor-pointer"
                                  onClick={() => setExpandedImg(msg.chart_screenshot)}
                                />
                                <button
                                  onClick={() => copyToClipboard(msg.chart_screenshot)}
                                  className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/60 border border-white/10 text-neutral-300 hover:text-cyan-300 hover:border-cyan-500/40 opacity-0 group-hover:opacity-100 transition-all z-10"
                                  title={copiedImg === msg.chart_screenshot ? "Copied!" : "Copy screenshot to clipboard"}
                                >
                                  {copiedImg === msg.chart_screenshot ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                                </button>
                              </div>
                            )}
                            {/* ── Expanded screenshot modal ── */}
                            {expandedImg && (
                              <div
                                className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6"
                                onClick={() => setExpandedImg(null)}
                              >
                                <div className="relative max-w-[90vw] max-h-[90vh]" onClick={e => e.stopPropagation()}>
                                  <img
                                    src={`data:image/png;base64,${expandedImg}`}
                                    alt="Expanded chart screenshot"
                                    className="w-full h-auto max-h-[85vh] object-contain rounded-xl border border-white/10 shadow-2xl"
                                  />
                                  <button
                                    onClick={() => copyToClipboard(expandedImg)}
                                    className="absolute top-3 right-3 p-2 rounded-lg bg-black/60 border border-white/10 text-neutral-300 hover:text-cyan-300 hover:border-cyan-500/40 transition-all z-10"
                                    title={copiedImg === expandedImg ? "Copied!" : "Copy screenshot to clipboard"}
                                  >
                                    {copiedImg === expandedImg ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                                  </button>
                                </div>
                              </div>
                            )}
                            {/* ── Text answer fallback (no chart) ── */}
                            {!msg.chart_options && !msg.chart_screenshot && renderAnswerContent(msg.content)}
                          </div>
                        ) : (
                          <p className="whitespace-pre-wrap select-text">{msg.content}</p>
                        )}
                      </div>

                      {/* Log Diagnostic Toggle for Assistant replies */}
                      {msg.role === "assistant" && (msg.source_nodes?.length > 0 || msg.graph_triples?.length > 0) && (
                        <button
                          onClick={() => setExpandedLogIndex(expandedLogIndex === idx ? null : idx)}
                          className="mt-2 text-[10px] font-bold text-neutral-500 hover:text-cyan-400 flex items-center gap-1 transition-all select-none"
                        >
                          <Activity className="h-3 w-3" />
                          {expandedLogIndex === idx ? "Hide Retrieval Logs" : "Show Retrieval Logs"}
                        </button>
                      )}
                    </div>

                    {/* Collapsable Diagnostic Logs */}
                    {msg.role === "assistant" && expandedLogIndex === idx && (
                      <div className="w-[90%] mt-3 flex flex-col gap-3 animate-fadeIn">
                        
                        {/* HyDE expansion info */}
                        {msg.hyde_query && (
                          <div className="border border-white/5 bg-neutral-900/40 rounded-xl p-3.5">
                            <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500 block mb-0.5">
                              HyDE Query Expansion:
                            </span>
                            <p className="text-xs text-neutral-300 italic font-mono">
                              "{msg.hyde_query}"
                            </p>
                          </div>
                        )}

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
                          {/* Graph Triples */}
                          <div className="border border-white/5 bg-neutral-900/40 rounded-xl p-3.5 flex flex-col gap-1.5">
                            <span className="text-[10px] font-bold text-cyan-400 flex items-center gap-1 border-b border-white/5 pb-1 uppercase tracking-wider">
                              <Workflow className="h-3.5 w-3.5" />
                              Graph Relations
                            </span>
                            {msg.graph_triples && msg.graph_triples.length > 0 ? (
                              <div className="flex flex-col gap-1 max-h-[120px] overflow-y-auto text-[10px] font-mono text-neutral-300">
                                {msg.graph_triples.map((triple: any, tIdx: number) => (
                                  <div key={tIdx} className="flex gap-1.5">
                                    <span className="text-cyan-500">•</span>
                                    <span>({triple.source}) -[{triple.relation}]-&gt; ({triple.target})</span>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-[10px] text-neutral-500 italic">No graph neighborhood matches.</p>
                            )}
                          </div>

                          {/* Source Chunks */}
                          <div className="border border-white/5 bg-neutral-900/40 rounded-xl p-3.5 flex flex-col gap-1.5">
                            <span className="text-[10px] font-bold text-cyan-400 flex items-center gap-1 border-b border-white/5 pb-1 uppercase tracking-wider">
                              <FileText className="h-3.5 w-3.5" />
                              Source Chunks
                            </span>
                            {msg.source_nodes && msg.source_nodes.length > 0 ? (
                              <div className="flex flex-col gap-2 max-h-[120px] overflow-y-auto text-[10px]">
                                {msg.source_nodes.map((node: any, nIdx: number) => (
                                  <div key={nIdx} className="border-b border-white/5 pb-1.5 last:border-0 last:pb-0">
                                    <div className="flex justify-between items-center text-neutral-400 mb-0.5">
                                      <span className="font-semibold text-neutral-300">Chunk {nIdx+1}</span>
                                      <span className="font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-850 px-1 rounded">
                                        Score: {node.score !== undefined ? node.score.toFixed(2) : "RRF"}
                                      </span>
                                    </div>
                                    <p className="text-neutral-400 leading-normal line-clamp-2 select-text">{node.content}</p>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className="text-[10px] text-neutral-500 italic">No source documents matched.</p>
                            )}
                          </div>
                        </div>

                      </div>
                    )}

                    {msg.role === "user" && (
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/5 select-none">
                        <User className="h-5 w-5 text-neutral-400" />
                      </div>
                    )}

                  </div>
                ))
              )}

              {/* Streaming/Loading bubble */}
              {loadingQuery && (
                <div className="flex gap-3 w-full py-2 justify-start animate-pulse">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 select-none">
                    <Brain className="h-5 w-5 text-pink-400 animate-pulse" />
                  </div>
                  <div className="flex flex-col max-w-[80%] items-start">
                    <div className="flex items-baseline gap-2 mb-1.5 ml-1 select-none">
                      <span className="text-sm font-semibold text-white">Report Analyst</span>
                    </div>
                    
                    <ThoughtsAccordion thoughts="" loading={true} />
                    
                    <div className="bg-white/5 border border-white/5 rounded-2xl rounded-tl-none px-5 py-3.5 flex gap-2.5 items-center w-full select-none">
                      <Loader2 className="h-4 w-4 text-cyan-400 animate-spin" />
                      <span className="text-xs text-neutral-400 font-medium">Resolving context and formulating response...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={chatEndRef} />
            </div>

            {/* Suggestions & Input Area */}
            <div className="flex flex-col gap-3.5 shrink-0 border-t border-white/5 pt-4">
              
              {/* Query Suggestions */}
              {messages.length === 0 && (
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-neutral-500">Query suggestions:</span>
                  <div className="flex flex-wrap gap-2">
                    {QUERY_SUGGESTIONS.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => executeQuery(suggestion)}
                        className="bg-neutral-900 hover:bg-cyan-950/30 hover:border-cyan-850 text-neutral-300 hover:text-cyan-400 border border-white/5 rounded-xl px-3 py-1.5 text-[11px] font-medium transition-all text-left max-w-full truncate"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Chat Input Bar */}
              <div className="flex gap-2.5">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Ask follow-up or diagnostic question (e.g. resolve SIM profiles, ticket counts)..."
                    value={queryStr}
                    onChange={(e) => setQueryStr(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && executeQuery()}
                    disabled={loadingQuery}
                    className="w-full bg-neutral-900/60 border border-white/5 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:border-cyan-500 text-white placeholder-neutral-500 disabled:opacity-50"
                  />
                  <Search className="absolute left-3 top-3.5 h-4.5 w-4.5 text-neutral-500" />
                </div>
                <Button 
                  onClick={() => executeQuery()} 
                  disabled={loadingQuery || !queryStr.trim()}
                  className="bg-cyan-500 text-neutral-950 hover:bg-cyan-400 font-bold rounded-xl px-5 flex gap-1.5"
                >
                  {loadingQuery ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Send
                </Button>
              </div>

            </div>

          </div>
        )}

        {/* Tab 2: System Evaluation */}
        {activeSubTab === "eval" && (
          <div className="flex flex-col gap-6 h-full">
            <div className="flex justify-between items-center border-b border-white/5 pb-3 shrink-0">
              <div>
                <h4 className="text-sm font-bold">RAG Validation Pipeline</h4>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Execute deterministic Pandas exact-match and LLM-as-a-judge diagnostics.
                </p>
              </div>
              <Button
                onClick={executeEvaluation}
                disabled={evaluating}
                className="bg-cyan-500 text-neutral-950 hover:bg-cyan-400 font-bold rounded-xl text-xs flex gap-1.5 shrink-0"
              >
                {evaluating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Trigger Evaluation Run
              </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-hidden flex-1 min-h-0">
              
              {/* Left Column: Queries & Detailed Outputs (2/3 width) */}
              <div className="lg:col-span-2 flex flex-col gap-5 overflow-y-auto pr-1">
                
                {/* Target Queries List */}
                <div className="border border-white/5 bg-neutral-900/20 rounded-xl p-4 flex flex-col gap-2 shrink-0">
                  <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
                    Target Evaluation Queries ({DEFAULT_EVAL_QUERIES.length})
                  </span>
                  <div className="flex flex-col gap-1.5 text-xs text-neutral-300">
                    {DEFAULT_EVAL_QUERIES.map((q, idx) => (
                      <div key={idx} className="flex gap-2">
                        <span className="text-cyan-500">•</span>
                        <span>"{q}"</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Progress bar / Ingress */}
                {evalStatus && evalStatus.status !== "COMPLETED" && evalStatus.status !== "FAILED" && (
                  <div className="border border-white/5 bg-neutral-900/40 rounded-2xl p-5 flex flex-col gap-4 shrink-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                        <Activity className="h-4 w-4 animate-pulse" />
                        Evaluation Run Progress
                      </span>
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-950/40 text-cyan-400 border border-cyan-850 animate-pulse">
                        {evalStatus.status}
                      </span>
                    </div>

                    <div className="w-full bg-neutral-950 rounded-full h-2 overflow-hidden border border-white/5">
                      <div 
                        className="bg-cyan-500 h-full transition-all duration-300"
                        style={{ width: `${evalStatus.progress * 100}%` }}
                      />
                    </div>

                    {evalStatus.metadata && evalStatus.metadata.status_message && (
                      <p className="text-xs text-neutral-400 font-mono">&gt; {evalStatus.metadata.status_message}</p>
                    )}
                  </div>
                )}

                {/* Error Card */}
                {evalError && (
                  <div className="border border-rose-955/40 bg-rose-955/10 rounded-2xl p-4 flex gap-2.5 items-start text-xs text-rose-450 shrink-0">
                    <AlertCircle className="h-4 w-4 shrink-0 text-rose-450 mt-0.5" />
                    <div>
                      <h5 className="font-bold">Evaluation Run Failed</h5>
                      <p className="text-neutral-400 mt-0.5">{evalError}</p>
                    </div>
                  </div>
                )}

                {/* Detailed Results List */}
                {evalStatus && evalStatus.status === "COMPLETED" && evalStatus.metadata.detailed_results && (
                  <div className="border border-white/5 bg-neutral-900/40 rounded-2xl p-5 flex flex-col gap-4">
                    <span className="text-xs font-bold text-cyan-400 border-b border-white/5 pb-1 flex items-center gap-1.5">
                      <Workflow className="h-4 w-4" />
                      Detailed Evaluation Query Outputs
                    </span>
                    <div className="flex flex-col gap-4">
                      {evalStatus.metadata.detailed_results.map((res: any, idx: number) => (
                        <div key={idx} className="flex flex-col gap-2 bg-neutral-950/60 p-4 border border-white/5 rounded-xl text-xs">
                          <div className="flex justify-between items-center border-b border-white/5 pb-2">
                            <span className="font-bold text-neutral-200">Query {idx+1}: "{res.query}"</span>
                            <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                              res.pandas_accuracy === 1.0 ? "bg-pink-950/40 text-pink-400 border border-pink-850" : "bg-neutral-900 text-neutral-400"
                            }`}>
                              Exact Match: {res.pandas_accuracy !== undefined ? (res.pandas_accuracy * 100).toFixed(0) + "%" : "100%"}
                            </span>
                          </div>
                          <div className="pt-1 select-text">
                            {renderAnswerContent(res.answer)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Column: Sleek Magenta Minimalistic Sidebar (1/3 width) */}
              <div className="border border-pink-500/15 bg-pink-950/5 backdrop-blur-sm rounded-2xl p-5 flex flex-col gap-5 h-fit relative overflow-hidden shrink-0">
                <div className="absolute top-0 right-0 h-32 w-32 bg-pink-500/5 rounded-full blur-3xl pointer-events-none" />
                
                <h5 className="text-xs font-bold text-pink-500 uppercase tracking-widest flex items-center gap-1.5 border-b border-pink-500/10 pb-2.5">
                  <Activity className="h-3.5 w-3.5 text-pink-500" />
                  RAG Analytics
                </h5>

                {evalStatus && evalStatus.status === "COMPLETED" && evalStatus.metadata.metrics ? (
                  <div className="flex flex-col gap-6">
                    
                    {/* Big Metric Card: Pandas Exact Match */}
                    <div className="flex flex-col gap-1.5 border-b border-pink-500/10 pb-4">
                      <span className="text-[9px] font-bold text-neutral-400 uppercase tracking-wider">Spreadsheet Exact Match</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-extrabold text-pink-500">
                          {(evalStatus.metadata.metrics.pandas_accuracy * 100).toFixed(0)}%
                        </span>
                        <span className="text-[10px] text-pink-400/80 font-mono font-bold">(Pandas Verification)</span>
                      </div>
                      <p className="text-[10px] text-neutral-400 leading-relaxed mt-1">
                        Direct cell-by-cell equivalence between RAG output tables and Pandas aggregations.
                      </p>
                    </div>

                    {/* Minimalist Magenta Gauges */}
                    <div className="flex flex-col gap-4">
                      
                      {/* Metric 1 */}
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-neutral-300 font-semibold">
                          <span>Faithfulness</span>
                          <span className="text-pink-400 font-mono">{(evalStatus.metadata.metrics.faithfulness * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-neutral-900/60 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className="bg-pink-500 h-full transition-all duration-300"
                            style={{ width: `${evalStatus.metadata.metrics.faithfulness * 100}%` }}
                          />
                        </div>
                      </div>

                      {/* Metric 2 */}
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-neutral-300 font-semibold">
                          <span>Answer Relevance</span>
                          <span className="text-pink-400 font-mono">{(evalStatus.metadata.metrics.answer_relevance * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-neutral-900/60 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className="bg-pink-500 h-full transition-all duration-300"
                            style={{ width: `${evalStatus.metadata.metrics.answer_relevance * 100}%` }}
                          />
                        </div>
                      </div>

                      {/* Metric 3 */}
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-neutral-300 font-semibold">
                          <span>Context Precision</span>
                          <span className="text-pink-400 font-mono">{(evalStatus.metadata.metrics.context_precision * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-neutral-900/60 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className="bg-pink-500 h-full transition-all duration-300"
                            style={{ width: `${evalStatus.metadata.metrics.context_precision * 100}%` }}
                          />
                        </div>
                      </div>

                      {/* Metric 4 */}
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-neutral-300 font-semibold">
                          <span>Context Recall</span>
                          <span className="text-pink-400 font-mono">{(evalStatus.metadata.metrics.context_recall * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-neutral-900/60 h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className="bg-pink-500 h-full transition-all duration-300"
                            style={{ width: `${evalStatus.metadata.metrics.context_recall * 100}%` }}
                          />
                        </div>
                      </div>

                    </div>

                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 text-center text-neutral-500 gap-2">
                    <Activity className="h-6 w-6 text-neutral-600" />
                    <p className="text-[10px] font-bold text-neutral-400">No active evaluation run</p>
                    <p className="text-[9px] leading-relaxed max-w-[150px]">Trigger an evaluation run on the left to compute exact match verification accuracy.</p>
                  </div>
                )}

              </div>

            </div>

          </div>
        )}


      </div>
    </div>
  );
};
