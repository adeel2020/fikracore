"use client";

import React, { FormEvent } from "react";
import {
  Users,
  TrendingUp,
  AlertTriangle,
  Phone,
  BarChart3,
  Network,
  Search,
  AlertCircle,
  CircleDollarSign,
  ShoppingBag,
  Clock,
  Zap,
  Award,
  PackageOpen,
  Truck,
  UserMinus,
  Scale,
  CheckCircle2,
  Eye,
  Activity,
  Brain,
  ChevronRight,
  ChevronLeft,
  Bot,
  Loader2,
  Terminal,
  Square,
  Send,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, glassSurfaceStatic } from "@/lib/utils";
import { ChatMessage, SkillItem } from "@/lib/api/qna";
import { StructuredAgentResponse } from "../types/agentic-qna.types";
import { MessageItem } from "./MessageItem";
import { MAX_PAGE_INDEX } from "../hooks/useAgenticQna";

const iconStroke = { strokeWidth: 1.5 } as const;

const PAGE_HEADER_META = [
  {
    title: "Cognitive Operation & Customer center",
    desc: "Select an active network workflow below to guide Cognitive Operation & Customer Center.",
    icon: <Brain className="h-6 w-6 text-pink-400 animate-pulse" />,
    iconClass: "bg-pink-500/10 border-pink-500/20",
  },
  {
    title: "Data Storyteller",
    desc: "Select a dataset below to explore, or type your own.",
    icon: <Users className="h-6 w-6 text-cyan-400 animate-float" />,
    iconClass: "bg-cyan-500/10 border-cyan-500/20",
  },
  {
    title: "QnA Assistant",
    desc: "Select a question below to explore, or type your own.",
    icon: <TrendingUp className="h-6 w-6 text-emerald-400 animate-float" />,
    iconClass: "bg-emerald-500/10 border-emerald-500/20",
  },
  {
    title: "Reasoning & Research Agent",
    desc: "Select an analytical prompt below, or type your own.",
    icon: <AlertTriangle className="h-6 w-6 text-rose-400 animate-float" />,
    iconClass: "bg-rose-500/10 border-rose-500/20",
  },
  {
    title: "Training & Evaluation",
    desc: "Select a validation prompt below, or type your own.",
    icon: <BarChart3 className="h-6 w-6 text-indigo-400 animate-float" />,
    iconClass: "bg-indigo-500/10 border-indigo-500/20",
  },
  {
    title: "Telecom Signaling Analyst",
    desc: "Select a telecom trace analysis prompt below, or type your own.",
    icon: <Network className="h-6 w-6 text-pink-400 animate-float" />,
    iconClass: "bg-pink-500/10 border-pink-500/20",
  },
  {
    title: "Mobile Core Analyst",
    desc: "Vector-search based intent identification and proxy pointer resolution.",
    icon: <Phone className="h-6 w-6 text-cyan-400 animate-float" />,
    iconClass: "bg-cyan-500/10 border-cyan-500/20",
  },
  {
    title: "Root Cause Analysis",
    desc: "Select a root cause prompt below, or type your own.",
    icon: <Search className="h-6 w-6 text-violet-400 animate-float" />,
    iconClass: "bg-violet-500/10 border-violet-500/20",
  },
  {
    title: "Anomaly Detection",
    desc: "Select an anomaly detection prompt below, or type your own.",
    icon: <AlertCircle className="h-6 w-6 text-orange-400 animate-float" />,
    iconClass: "bg-orange-500/10 border-orange-500/20",
  },
];

const SUGGESTED_PROMPTS_PAGES = [
  // Page 0: Main Guide Screen
  [
    {
      icon: <Users className="h-5 w-5 text-cyan-400" />,
      title: "Data Storyteller",
      prompt:
        "Generate an executive narrative review covering user registration congestion and service health.",
      route: "Storyteller Workflow",
      isGuide: true,
      pageTarget: 1,
    },
    {
      icon: <TrendingUp className="h-5 w-5 text-emerald-400" />,
      title: "QnA Assistant",
      prompt: "What are the latest session stats and active subscriber profile utilizations?",
      route: "Fast QnA",
      isGuide: true,
      pageTarget: 2,
    },
    {
      icon: <AlertTriangle className="h-5 w-5 text-amber-400 animate-bounce" />,
      title: "Reasoning & Research",
      prompt: "Research optimal EPC load cell selections and analyze SGW interface failures.",
      route: "Fast QnA",
      isGuide: true,
      pageTarget: 3,
    },
    {
      icon: <Phone className="h-5 w-5 text-rose-400 animate-pulse" />,
      title: "Mobile RTR (Customer Issues)",
      prompt:
        "Diagnose active customer technical tickets and analyze real-time voice/data drops across local cell nodes.",
      route: "Cognitive Workflow",
      isGuide: true,
      pageTarget: 0,
    },
    {
      icon: <BarChart3 className="h-5 w-5 text-indigo-400" />,
      title: "Inference & Evaluation",
      prompt:
        "Verify 5G Core SLA predictive model accuracy and assess LSTM performance forecasts.",
      route: "Storyteller Workflow",
      isGuide: true,
      pageTarget: 4,
    },
    {
      icon: <Network className="h-5 w-5 text-rose-400 animate-pulse" />,
      title: "Telecom Signaling",
      prompt: "/trace-analyzer japan_tcap_over_m2pa.pcap",
      route: "Skill Workflow",
      isGuide: true,
      pageTarget: 5,
    },
    {
      icon: <Search className="h-5 w-5 text-violet-400" />,
      title: "Root Cause Analysis",
      prompt:
        "Trace escalated customer tickets to identify root causes for recurring voice and data session failures.",
      route: "Cognitive Workflow",
      isGuide: true,
      pageTarget: 7,
    },
    {
      icon: <AlertCircle className="h-5 w-5 text-orange-400 animate-pulse" />,
      title: "Anomaly Detection",
      prompt:
        "Detect anomalous signaling patterns and traffic spikes across 5G core network interfaces in real-time.",
      route: "Fast QnA",
      isGuide: true,
      pageTarget: 8,
    },
    {
      icon: <Phone className="h-5 w-5 text-cyan-400 animate-pulse" />,
      title: "Mobile Core Analyst",
      prompt: "Vector-search based intent identification and proxy pointer resolution",
      route: "Mobile Core Analyst",
      isGuide: true,
      pageTarget: 6,
    },
  ],
  // Page 1: Data Storyteller
  [
    {
      icon: <Users className="h-4 w-4 text-cyan-400" />,
      title: "Customer Churn",
      prompt: "Analyze the enterprise churn data and identify the top 3 driving factors.",
      route: "Storyteller Workflow",
    },
    {
      icon: <CircleDollarSign className="h-4 w-4 text-emerald-400" />,
      title: "Lifetime Value",
      prompt: "Analyze the customer lifetime value (CLV) dataset for high-value segments.",
      route: "Storyteller Workflow",
    },
    {
      icon: <ShoppingBag className="h-4 w-4 text-amber-400" />,
      title: "Sales Analysis",
      prompt: "Analyze the product sales data to find underperforming regional categories.",
      route: "Storyteller Workflow",
    },
    {
      icon: <Clock className="h-4 w-4 text-blue-400" />,
      title: "Support Speed",
      prompt: "Analyze the support ticket dataset to correlate resolution speed with satisfaction.",
      route: "Storyteller Workflow",
    },
  ],
  // Page 2: QnA Assistant
  [
    {
      icon: <TrendingUp className="h-4 w-4 text-emerald-400" />,
      title: "Issue Categories",
      prompt: "share the issue categories in descending order",
      route: "Fast QnA",
    },
    {
      icon: <Zap className="h-4 w-4 text-yellow-400" />,
      title: "Total Tickets",
      prompt: "What is the total number of rows/tickets in the Operations_Dashboard_Data_Template.xlsx dataset?",
      route: "Fast QnA",
    },
    {
      icon: <Award className="h-4 w-4 text-violet-400" />,
      title: "Rejection Reasons",
      prompt: "Which rejection reasons are present in the tickets and what are their occurrences?",
      route: "Fast QnA",
    },
    {
      icon: <PackageOpen className="h-4 w-4 text-orange-400" />,
      title: "Ticket Frequencies",
      prompt: "List the countries represented in the dataset along with their ticket frequencies.",
      route: "Fast QnA",
    },
  ],
  // Page 3: Reasoning & Research
  [
    {
      icon: <AlertTriangle className="h-4 w-4 text-rose-400" />,
      title: "Inventory Risk",
      prompt: "Which EU-WEST warehouses are currently below the reorder threshold?",
      route: "Fast QnA",
    },
    {
      icon: <Truck className="h-4 w-4 text-cyan-400" />,
      title: "Supply Chain",
      prompt: "Research supply chain logistics to identify optimal hub distribution.",
      route: "Fast QnA",
    },
    {
      icon: <UserMinus className="h-4 w-4 text-red-400" />,
      title: "Retention Impact",
      prompt: "Analyze the downstream impact of shipping delays on customer retention.",
      route: "Fast QnA",
    },
    {
      icon: <Scale className="h-4 w-4 text-teal-400" />,
      title: "Cost Efficiency",
      prompt: "Evaluate vendor pricing structures to optimize inventory cost efficiency.",
      route: "Fast QnA",
    },
  ],
  // Page 4: Training & Evaluation
  [
    {
      icon: <BarChart3 className="h-4 w-4 text-indigo-400" />,
      title: "Generate Dashboard",
      prompt:
        "Create a comprehensive correlation report comparing support tickets to renewal delays.",
      route: "Storyteller Workflow",
    },
    {
      icon: <CheckCircle2 className="h-4 w-4 text-green-400" />,
      title: "Model Accuracy",
      prompt: "Verify model classification accuracy against the synthetic validation set.",
      route: "Storyteller Workflow",
    },
    {
      icon: <Eye className="h-4 w-4 text-purple-400" />,
      title: "Bias Detection",
      prompt: "Assess training data completeness and detect potential bias factors.",
      route: "Storyteller Workflow",
    },
    {
      icon: <Activity className="h-4 w-4 text-pink-400" />,
      title: "Performance Report",
      prompt: "Generate a detailed model performance report for the custom LLM run.",
      route: "Storyteller Workflow",
    },
  ],
  // Page 5: Telecom Signaling Analyst
  [
    {
      icon: <Network className="h-4 w-4 text-pink-400" />,
      title: "SS7 MAP SMS Trace",
      prompt: "/trace-analyzer camel.pcap",
      route: "Skill Workflow",
    },
    {
      icon: <AlertTriangle className="h-4 w-4 text-rose-400" />,
      title: "TCAP OTA Auth Trace",
      prompt: "/trace-analyzer ansi_map_ota.pcap",
      route: "Skill Workflow",
    },
    {
      icon: <Activity className="h-4 w-4 text-cyan-400" />,
      title: "M2PA Signaling Flow",
      prompt: "/trace-analyzer japan_tcap_over_m2pa.pcap",
      route: "Skill Workflow",
    },
    {
      icon: <Zap className="h-4 w-4 text-yellow-400" />,
      title: "SIP-TCP Call Trace",
      prompt: "/trace-analyzer SIP-Call-Flow-Over-TCP.pcap",
      route: "Skill Workflow",
    },
  ],
  // Page 6: Mobile Core Analyst
  [
    {
      icon: <Phone className="h-4 w-4 text-cyan-400" />,
      title: "Voice Drops",
      prompt: "Voice call drops at local cells, poor signaling connection and low signal strength",
      route: "Mobile Core Analyst",
    },
    {
      icon: <Zap className="h-4 w-4 text-yellow-400" />,
      title: "eSIM Issues",
      prompt:
        "eSIM registration and profile activation failure with sm-dp+ server mismatch error",
      route: "Mobile Core Analyst",
    },
    {
      icon: <AlertTriangle className="h-4 w-4 text-rose-400" />,
      title: "5G Speed",
      prompt: "5G cellular network speed degradation, high packet latency and low bandwidth",
      route: "Mobile Core Analyst",
    },
    {
      icon: <Network className="h-4 w-4 text-pink-400" />,
      title: "Roaming Connect",
      prompt:
        "International roaming partner connection fails with forbidden land mobile network code",
      route: "Mobile Core Analyst",
    },
  ],
  // Page 7: Root Cause Analysis
  [
    {
      icon: <Search className="h-4 w-4 text-violet-400" />,
      title: "Voice Drop Root Cause",
      prompt:
        "Investigate recurring voice call drops across multiple cell sites and correlate with RRC re-establishment counters.",
      route: "Cognitive Workflow",
    },
    {
      icon: <Network className="h-4 w-4 text-cyan-400" />,
      title: "S-GW Failure Trace",
      prompt:
        "Trace S-GW path failure events from core logs and identify cascading impact on user session continuity.",
      route: "Cognitive Workflow",
    },
    {
      icon: <BarChart3 className="h-4 w-4 text-indigo-400" />,
      title: "E-RAB Drop Analysis",
      prompt:
        "Analyze E-RAB abnormal release causes across RAN and core segments to pinpoint recurring failure nodes.",
      route: "Cognitive Workflow",
    },
    {
      icon: <AlertTriangle className="h-4 w-4 text-rose-400" />,
      title: "Registration Storm RCA",
      prompt:
        "Diagnose root cause of registration storm events triggered by MME overload and TAI misconfiguration.",
      route: "Cognitive Workflow",
    },
  ],
  // Page 8: Anomaly Detection
  [
    {
      icon: <Activity className="h-4 w-4 text-orange-400" />,
      title: "Signaling Spike Alert",
      prompt:
        "Detect anomalous signaling message spikes on N2/N3 interfaces and flag potential network abuse patterns.",
      route: "Fast QnA",
    },
    {
      icon: <Zap className="h-4 w-4 text-yellow-400" />,
      title: "Latency Anomaly",
      prompt:
        "Identify latency anomaly clusters in user-plane traffic and isolate contributing cell sectors.",
      route: "Fast QnA",
    },
    {
      icon: <Network className="h-4 w-4 text-pink-400" />,
      title: "Protocol Deviation",
      prompt:
        "Detect non-standard protocol message sequences in SS7/SIGTRAN traffic indicating possible misconfiguration.",
      route: "Fast QnA",
    },
    {
      icon: <TrendingUp className="h-4 w-4 text-emerald-400" />,
      title: "Traffic Volume Shift",
      prompt:
        "Monitor for sudden traffic volume shifts across EPC nodes and flag capacity anomalies in real-time.",
      route: "Fast QnA",
    },
  ],
];

interface ChatPanelProps {
  messages: ChatMessage[];
  input: string;
  setInput: (val: string) => void;
  sessionId: string | null;
  loading: boolean;
  error: string | null;
  backendOnline: boolean | null;
  agentMode: string;
  activePersona: string;
  statusMessage: string;
  structuredResponse: StructuredAgentResponse | null;
  activeIndex: number;
  scrollRef: React.RefObject<HTMLDivElement | null>;
  inputRef: React.RefObject<HTMLInputElement | null>;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  handleScroll: () => void;
  scroll: (direction: "left" | "right") => void;
  scrollToPage: (idx: number) => void;
  handleSuggestedPrompt: (promptText: string, route: string) => void;
  handlePageChipClick: (item: any) => void;
  handleSubmit: (e?: FormEvent) => void;
  handleStop: () => void;
  handleSelectSkill: (skillName: string) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  showSkillsPopup: boolean;
  filteredSkills: SkillItem[];
  selectedSkill: string | null;
  setSelectedSkill: (val: string | null) => void;
  activeSkillIndex: number;
  showHistory: boolean;
  setShowHistory: (val: boolean) => void;
}

interface SuggestedPromptsProps {
  activeIndex: number;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  handleScroll: () => void;
  scroll: (direction: "left" | "right") => void;
  scrollToPage: (idx: number) => void;
  handleSuggestedPrompt: (promptText: string, route: string) => void;
  handlePageChipClick: (item: any) => void;
}

const SuggestedPrompts = React.memo(function SuggestedPrompts({
  activeIndex,
  scrollContainerRef,
  handleScroll,
  scroll,
  scrollToPage,
  handleSuggestedPrompt,
  handlePageChipClick,
}: SuggestedPromptsProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 w-full">
      <div className="relative w-full flex flex-col items-center" style={{ maxWidth: "1024px" }}>
        {activeIndex > 0 && (
          <button
            type="button"
            onClick={() => scroll("left")}
            className="absolute -left-12 top-[50%] -translate-y-1/2 z-20 h-9 w-9 flex items-center justify-center rounded-full bg-black/30 backdrop-blur-md border border-white/5 hover:bg-white/10 hover:border-cyan-500/30 text-white/50 hover:text-cyan-400 transition-all duration-300 focus:outline-none"
            aria-label="Previous page"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        )}
        {activeIndex < MAX_PAGE_INDEX && (
          <button
            type="button"
            onClick={() => scroll("right")}
            className="absolute -right-12 top-[50%] -translate-y-1/2 z-20 h-9 w-9 flex items-center justify-center rounded-full bg-black/30 backdrop-blur-md border border-white/5 hover:bg-white/10 hover:border-cyan-500/30 text-white/50 hover:text-cyan-400 transition-all duration-300 focus:outline-none"
            aria-label="Next page"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        )}
        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex overflow-x-auto scrollbar-none snap-x snap-mandatory scroll-smooth w-full px-1 py-1 min-h-0 gap-0"
        >
          {SUGGESTED_PROMPTS_PAGES.map((pageItems, pageIdx) => {
            if (pageIdx === 0) {
              return (
                <div
                  key={pageIdx}
                  className={cn(
                    "snap-center shrink-0 w-full flex flex-col justify-center items-center px-1",
                    pageIdx !== activeIndex && "pointer-events-none"
                  )}
                >
                  <div
                    className="flex flex-col items-center justify-end text-center w-full mb-4 h-[150px]"
                    style={{ maxWidth: "1024px" }}
                  >
                    <div
                      className={cn(
                        "flex h-12 w-12 items-center justify-center rounded-2xl border mb-2 animate-pulse-glow relative overflow-hidden",
                        PAGE_HEADER_META[pageIdx].iconClass
                      )}
                    >
                      {PAGE_HEADER_META[pageIdx].icon}
                    </div>
                    <h2 className="text-xl font-semibold text-white mb-1">
                      {PAGE_HEADER_META[pageIdx].title}
                    </h2>
                    <p className="text-sm text-neutral-400 text-center max-w-xl leading-relaxed">
                      {PAGE_HEADER_META[pageIdx].desc}
                    </p>
                  </div>
                  <div
                    className="w-full relative border border-white/5 rounded-2xl p-5 bg-black/45 backdrop-blur-md overflow-hidden min-h-[220px] select-none"
                    style={{ maxWidth: "1024px" }}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
                      {/* Column 1: Analysis & Narrative */}
                      <div className="flex flex-col gap-3 justify-center z-10">
                        <h4 className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest border-b border-white/5 pb-1 mb-1 text-center">
                          Analysis & Narrative
                        </h4>
                        {pageItems
                          .filter(
                            (item: any) =>
                              item.title === "Data Storyteller" ||
                              item.title === "Mobile RTR (Customer Issues)" ||
                              item.title === "Root Cause Analysis"
                          )
                          .map((item: any, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => handlePageChipClick(item)}
                              className="group relative flex flex-col items-start gap-1 rounded-xl p-3 text-left transition-all duration-300 border border-cyan-400/50 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)] hover:-translate-y-1 hover:scale-[1.02] cursor-pointer w-full h-[110px]"
                            >
                              <div className="flex w-full items-center gap-2">
                                <div className="transition-transform duration-500 group-hover:scale-110">
                                  {item.icon}
                                </div>
                                <span className="text-xs font-semibold text-neutral-400 group-hover:text-cyan-300 transition-colors">
                                  {item.title}
                                </span>
                              </div>
                              <p className="text-[10px] text-neutral-400 line-clamp-2 leading-relaxed mt-1 group-hover:text-neutral-300 transition-colors">
                                {item.prompt}
                              </p>
                            </button>
                          ))}
                      </div>
                      {/* Splitter Column 1-2 */}
                      <div className="glow-splitter left-[33.3%]">
                        <div className="glow-light" />
                      </div>
                      {/* Column 2: Search & Diagnostics */}
                      <div className="flex flex-col gap-3 justify-center z-10">
                        <h4 className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest border-b border-white/5 pb-1 mb-1 text-center">
                          Search & Diagnostics
                        </h4>
                        {pageItems
                          .filter(
                            (item: any) =>
                              item.title === "QnA Assistant" ||
                              item.title === "Reasoning & Research" ||
                              item.title === "Anomaly Detection"
                          )
                          .map((item: any, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => handlePageChipClick(item)}
                              className="group relative flex flex-col items-start gap-1 rounded-xl p-3 text-left transition-all duration-300 border border-cyan-400/50 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)] hover:-translate-y-1 hover:scale-[1.02] cursor-pointer w-full h-[110px]"
                            >
                              <div className="flex w-full items-center gap-2">
                                <div className="transition-transform duration-500 group-hover:scale-110">
                                  {item.icon}
                                </div>
                                <span className="text-xs font-semibold text-neutral-400 group-hover:text-cyan-300 transition-colors">
                                  {item.title}
                                </span>
                              </div>
                              <p className="text-[10px] text-neutral-400 line-clamp-2 leading-relaxed mt-1 group-hover:text-neutral-300 transition-colors">
                                {item.prompt}
                              </p>
                            </button>
                          ))}
                      </div>
                      {/* Splitter Column 2-3 */}
                      <div className="glow-splitter left-[66.6%]">
                        <div className="glow-light-delayed" />
                      </div>
                      {/* Column 3: Metrics & Protocol */}
                      <div className="flex flex-col gap-3 justify-center z-10">
                        <h4 className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest border-b border-white/5 pb-1 mb-1 text-center">
                          Metrics & Protocol
                        </h4>
                        {pageItems
                          .filter(
                            (item: any) =>
                              item.title === "Inference & Evaluation" ||
                              item.title === "Telecom Signaling" ||
                              item.title === "Mobile Core Analyst"
                          )
                          .map((item: any, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => handlePageChipClick(item)}
                              className="group relative flex flex-col items-start gap-1 rounded-xl p-3 text-left transition-all duration-300 border border-cyan-400/50 bg-cyan-500/10 shadow-[0_0_15px_rgba(6,182,212,0.15)] hover:-translate-y-1 hover:scale-[1.02] cursor-pointer w-full h-[110px]"
                            >
                              <div className="flex w-full items-center gap-2">
                                <div className="transition-transform duration-500 group-hover:scale-110">
                                  {item.icon}
                                </div>
                                <span className="text-xs font-semibold text-neutral-400 group-hover:text-cyan-300 transition-colors">
                                  {item.title}
                                </span>
                              </div>
                              <p className="text-[10px] text-neutral-400 line-clamp-2 leading-relaxed mt-1 group-hover:text-neutral-300 transition-colors">
                                {item.prompt}
                              </p>
                            </button>
                          ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            }
            return (
              <div
                key={pageIdx}
                className={cn(
                  "snap-center shrink-0 w-full flex flex-col justify-center items-center px-1 animate-fade-in",
                  pageIdx !== activeIndex && "pointer-events-none"
                )}
              >
                <div
                  className="flex flex-col items-center justify-end text-center w-full mb-4 h-[150px]"
                  style={{ maxWidth: "672px" }}
                >
                  <div
                    className={cn(
                      "flex h-12 w-12 items-center justify-center rounded-2xl border mb-2 animate-pulse-glow relative overflow-hidden",
                      PAGE_HEADER_META[pageIdx]?.iconClass
                    )}
                  >
                    {PAGE_HEADER_META[pageIdx]?.icon}
                  </div>
                  <h2 className="text-xl font-semibold text-white mb-1">
                    {PAGE_HEADER_META[pageIdx]?.title}
                  </h2>
                  <p className="text-sm text-neutral-400 text-center max-w-md leading-relaxed">
                    {PAGE_HEADER_META[pageIdx]?.desc}
                  </p>
                </div>
                <div
                  className="w-full relative border border-white/5 rounded-2xl p-5 bg-black/45 backdrop-blur-md overflow-hidden min-h-[220px] select-none flex flex-col justify-center animate-fade-in"
                  style={{ maxWidth: "672px" }}
                >
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 w-full">
                    {pageItems.map((item: any, idx: number) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestedPrompt(item.prompt, item.route)}
                        className="group relative flex flex-col items-start gap-2 rounded-xl border border-white/5 bg-white/5 p-4 text-left transition-all duration-300 hover:border-cyan-400 hover:bg-cyan-500/10 hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] hover:-translate-y-1 hover:scale-[1.02] cursor-pointer w-full"
                      >
                        <div className="flex w-full items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="transition-transform duration-500 ease-out group-hover:scale-110 group-hover:rotate-6">
                              {item.icon}
                            </div>
                            <span className="text-sm font-medium text-white transition-colors group-hover:text-cyan-300">
                              {item.title}
                            </span>
                          </div>
                          <span className="text-[10px] rounded-full border border-white/10 bg-black/20 px-2 py-0.5 text-neutral-400 group-hover:border-cyan-500/20 group-hover:text-cyan-300 transition-colors">
                            {item.route}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-400 line-clamp-2 transition-colors group-hover:text-neutral-300 leading-relaxed mt-1">
                          "{item.prompt}"
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Scroll Bar Indicators */}
        <div className="mt-6 flex items-center justify-center gap-1.5 w-full">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => scrollToPage(idx)}
              className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer focus:outline-none ${
                activeIndex === idx ? "w-6 bg-cyan-400" : "w-3 bg-white/10 hover:bg-white/20"
              }`}
              aria-label={`Go to page ${idx + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
});

export function ChatPanel({
  messages,
  input,
  setInput,
  sessionId,
  loading,
  error,
  backendOnline,
  agentMode,
  activePersona,
  statusMessage,
  structuredResponse,
  activeIndex,
  scrollRef,
  inputRef,
  scrollContainerRef,
  handleScroll,
  scroll,
  scrollToPage,
  handleSuggestedPrompt,
  handlePageChipClick,
  handleSubmit,
  handleStop,
  handleSelectSkill,
  handleKeyDown,
  showSkillsPopup,
  filteredSkills,
  selectedSkill,
  setSelectedSkill,
  activeSkillIndex,
  showHistory,
  setShowHistory,
}: ChatPanelProps) {
  // Stable wrapper callbacks to prevent SuggestedPrompts from re-rendering during typing
  const latestCallbacks = React.useRef({
    handleScroll,
    scroll,
    scrollToPage,
    handleSuggestedPrompt,
    handlePageChipClick,
  });

  React.useEffect(() => {
    latestCallbacks.current = {
      handleScroll,
      scroll,
      scrollToPage,
      handleSuggestedPrompt,
      handlePageChipClick,
    };
  }, [handleScroll, scroll, scrollToPage, handleSuggestedPrompt, handlePageChipClick]);

  const stableHandleScroll = React.useCallback(() => {
    latestCallbacks.current.handleScroll();
  }, []);

  const stableScroll = React.useCallback((direction: "left" | "right") => {
    latestCallbacks.current.scroll(direction);
  }, []);

  const stableScrollToPage = React.useCallback((idx: number) => {
    latestCallbacks.current.scrollToPage(idx);
  }, []);

  const stableHandleSuggestedPrompt = React.useCallback((promptText: string, route: string) => {
    latestCallbacks.current.handleSuggestedPrompt(promptText, route);
  }, []);

  const stableHandlePageChipClick = React.useCallback((item: any) => {
    latestCallbacks.current.handlePageChipClick(item);
  }, []);

  return (
    <GlassCard className="relative z-10 flex flex-col p-4 h-full overflow-hidden" hover={false}>
      <div className="mb-3 flex flex-wrap items-center gap-2 flex-shrink-0">
        {!showHistory && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowHistory(true)}
            className="h-6 w-6 p-0"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
        <span className="inline-flex">
          <Badge variant={backendOnline ? "default" : "alert"}>
            {backendOnline === null
              ? "Connecting…"
              : backendOnline
              ? `Agent: ${agentMode}`
              : "API offline"}
          </Badge>
        </span>
        {sessionId && (
          <span className="truncate text-xs text-neutral-500">session {sessionId.slice(0, 8)}…</span>
        )}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-4 pr-2 min-h-0 [&::-webkit-scrollbar]:w-[3px] [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:bg-white/15 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/30 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.15)_transparent]"
      >
        {messages.length === 0 && !loading && (
          <SuggestedPrompts
            activeIndex={activeIndex}
            scrollContainerRef={scrollContainerRef}
            handleScroll={stableHandleScroll}
            scroll={stableScroll}
            scrollToPage={stableScrollToPage}
            handleSuggestedPrompt={stableHandleSuggestedPrompt}
            handlePageChipClick={stableHandlePageChipClick}
          />
        )}
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1;
          return (
            <MessageItem
              key={index}
              message={message}
              isLastMessage={isLastMessage}
              loading={loading}
              activePersona={activePersona}
              statusMessage={statusMessage}
              globalStructuredResponse={structuredResponse}
            />
          );
        })}
        {loading && (!messages.length || messages[messages.length - 1]?.role === "user") && (
          <div className="flex w-full items-start gap-4 py-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10">
              {activePersona === "Cognitive Operation & Customer Center" ? (
                <Brain className="h-5 w-5 text-pink-400 animate-pulse" />
              ) : activePersona === "Mobile Core Analyst" ? (
                <Phone className="h-5 w-5 text-cyan-400 animate-pulse" />
              ) : (
                <Bot className="h-5 w-5 text-cyan-400" />
              )}
            </div>
            <div className="flex flex-col gap-2 pt-1">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-500" />
                <span className="text-sm font-semibold text-white">{activePersona}</span>
              </div>
              {statusMessage && (
                <div className="inline-flex w-fit items-center gap-2 rounded border border-white/5 bg-black/20 px-2 py-1 text-xs font-mono text-neutral-400">
                  <span className="animate-pulse">{statusMessage}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="text-xs text-lime-300/90 flex-shrink-0 my-2" role="alert">
          {error}
          {backendOnline === false && (
            <>
              {" "}
              — start the API with <code className="text-cyan-400">uv run storyteller-api</code>
            </>
          )}
        </p>
      )}

      {showSkillsPopup && filteredSkills.length > 0 && (
        <div className="w-full mb-2 rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-1.5 flex flex-col gap-1 transition-all duration-300 animate-in fade-in slide-in-from-bottom-2 duration-200">
          {filteredSkills.map((skill, index) => (
            <button
              key={skill.name}
              type="button"
              onClick={() => handleSelectSkill(skill.name)}
              className={cn(
                "w-full rounded-lg px-3 py-2 text-left text-xs transition-all duration-200 flex items-center gap-2.5 text-neutral-300 cursor-pointer",
                activeSkillIndex === index
                  ? "bg-white/10 text-white font-semibold"
                  : "hover:bg-white/5 hover:text-white"
              )}
            >
              <Terminal className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
              <span className="font-mono font-bold text-white shrink-0">/{skill.name}</span>
              <span className="text-neutral-400 truncate flex-1">{skill.description}</span>
            </button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0 mt-2">
        <div className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm flex items-center gap-2 focus-within:border-cyan-500/30 transition-colors">
          {selectedSkill && (
            <span className="inline-flex items-center bg-white/10 px-2.5 py-0.5 rounded-md text-xs font-mono text-white gap-1 border border-white/10 select-none shadow-sm shadow-black/50">
              {selectedSkill}
              <button
                type="button"
                onClick={() => setSelectedSkill(null)}
                className="hover:text-rose-400 font-sans font-normal ml-0.5 text-sm leading-none"
              >
                &times;
              </button>
            </span>
          )}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedSkill ? "Add trace files or instructions..." : "Ask about your data..."
            }
            disabled={loading}
            autoFocus
            className="flex-1 bg-transparent border-0 p-0 text-white placeholder:text-neutral-500 focus:outline-none focus:ring-0 disabled:opacity-50 min-w-[120px]"
          />
        </div>
        <Button
          type={loading ? "button" : "submit"}
          onClick={loading ? handleStop : undefined}
          size="icon"
          aria-label={loading ? "Stop" : "Send"}
          disabled={!loading && !input.trim() && !selectedSkill}
          className={cn("transition-all duration-300", loading ? "bg-rose-500 hover:bg-rose-600 text-white" : "")}
        >
          {loading ? (
            <Square className="h-4 w-4 fill-white" {...iconStroke} />
          ) : (
            <Send className="h-4 w-4" {...iconStroke} />
          )}
        </Button>
      </form>
    </GlassCard>
  );
}
