"use client";

import React from "react";
import { ArrowRightLeft, CheckSquare, ExternalLink, Code, Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GraphNode, ThemeConfig } from "../types/context.types";
import { TYPE_ICONS } from "./shared/constants";

interface GraphDetailPanelProps {
  focusedNode: GraphNode | null;
  currentTheme: ThemeConfig;
  guidance: {
    title: string;
    heading: string;
    advice: string;
    steps: string[];
  } | null;
  currentContextPayload: any;
  copied: boolean;
  handleCopy: (text: string) => void;
}

export const GraphDetailPanel: React.FC<GraphDetailPanelProps> = ({
  focusedNode,
  currentTheme,
  guidance,
  currentContextPayload,
  copied,
  handleCopy,
}) => {
  if (!focusedNode) {
    return (
      <div
        className={`border transition-all duration-300 backdrop-blur-md rounded-2xl p-5 h-full overflow-y-auto flex flex-col gap-4 ${
          currentTheme.isDark ? "border-white/5 bg-neutral-950" : "border-black/5 bg-white"
        }`}
      >
        <div className="flex flex-col items-center justify-center h-full text-center p-4">
          <ArrowRightLeft className="h-8 w-8 text-cyan-400 mb-3 animate-pulse" />
          <h4
            className={`text-sm font-semibold mt-2 ${
              currentTheme.isDark ? "text-white" : "text-slate-900"
            }`}
          >
            Back-Office Routing Explorer
          </h4>
          <p
            className={`text-xs mt-2 leading-relaxed max-w-[240px] ${
              currentTheme.isDark ? "text-neutral-400" : "text-slate-500"
            }`}
          >
            Click any complaint intent, affected service, or support platform node in the canvas to
            inspect escalation rules.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`border transition-all duration-300 backdrop-blur-md rounded-2xl p-5 h-full overflow-y-auto flex flex-col gap-4 ${
        currentTheme.isDark ? "border-white/5 bg-neutral-950" : "border-black/5 bg-white"
      }`}
    >
      <div className="flex flex-col gap-4 h-full">
        {/* Node Detail Section */}
        <div
          className={`rounded-xl border p-4 relative overflow-hidden ${
            currentTheme.isDark ? "border-white/5 bg-white/5" : "border-black/5 bg-black/5"
          }`}
        >
          <div
            className="absolute top-0 right-0 h-16 w-16 opacity-10 rounded-full blur-xl"
            style={{
              backgroundColor: currentTheme.nodeColors[focusedNode.type] || "#FFFFFF",
            }}
          />
          <div className="flex items-center gap-2">
            <span
              className={`p-1.5 rounded-lg border bg-neutral-950/60 ${
                currentTheme.isDark ? "border-white/5" : "border-black/5"
              }`}
            >
              {TYPE_ICONS[focusedNode.type] || <span>❓</span>}
            </span>
            <span
              className="text-[10px] uppercase font-bold tracking-widest"
              style={{ color: currentTheme.nodeColors[focusedNode.type] || "#FFFFFF" }}
            >
              {focusedNode.type}
            </span>
          </div>
          <h3
            className={`text-base font-bold mt-2 leading-tight ${
              currentTheme.isDark ? "text-white" : "text-slate-900"
            }`}
          >
            {focusedNode.label}
          </h3>
          <span
            className={`text-[10px] font-mono mt-1 block ${
              currentTheme.isDark ? "text-neutral-500" : "text-slate-500"
            }`}
          >
            ID: {focusedNode.id}
          </span>
        </div>

        {/* Back-Office Escalation Guidance Panel */}
        {guidance && (
          <div
            className={`rounded-xl border p-4 flex flex-col gap-2 ${
              currentTheme.isDark ? "border-white/5 bg-white/5" : "border-black/5 bg-black/5"
            }`}
          >
            <h4 className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5 border-b border-white/5 pb-1">
              <CheckSquare className="h-3.5 w-3.5" />
              {guidance.title}
            </h4>
            <p
              className={`text-[11px] font-medium leading-normal ${
                currentTheme.isDark ? "text-neutral-300" : "text-slate-700"
              }`}
            >
              {guidance.heading}
            </p>
            <p
              className={`text-[10px] leading-relaxed ${
                currentTheme.isDark ? "text-neutral-400" : "text-slate-500"
              }`}
            >
              {guidance.advice}
            </p>

            {focusedNode.type === "FAQ" && (
              <div className="mt-1 flex flex-col gap-1 border-t border-white/5 pt-2 pb-1">
                {focusedNode.url && (
                  <a
                    href={focusedNode.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[10px] text-cyan-400 flex items-center gap-1 hover:underline font-semibold"
                  >
                    <ExternalLink className="h-3.5 w-3.5 text-cyan-400" />
                    View Official Support Article
                  </a>
                )}
                {focusedNode.target && (
                  <div className="text-[10px] mt-1">
                    <span className="font-bold text-neutral-400 uppercase tracking-wider text-[9px] block">
                      Escalate To:
                    </span>
                    <span className="text-emerald-400 font-semibold">{focusedNode.target}</span>
                  </div>
                )}
                {focusedNode.prohibited && focusedNode.prohibited.length > 0 && (
                  <div className="text-[10px] mt-1">
                    <span className="font-bold text-neutral-400 uppercase tracking-wider text-[9px] block">
                      Prohibited Routes (SLA Risk):
                    </span>
                    <span className="text-rose-450 font-semibold">
                      {focusedNode.prohibited.join(", ")}
                    </span>
                  </div>
                )}
              </div>
            )}

            <div className="mt-2 flex flex-col gap-1.5">
              <span
                className={`text-[9px] uppercase font-bold tracking-wider ${
                  currentTheme.isDark ? "text-neutral-500" : "text-slate-400"
                }`}
              >
                {focusedNode.type === "FAQ" ? "Required Pre-checks:" : "Escalation Steps:"}
              </span>
              {(focusedNode.type === "FAQ" ? focusedNode.prechecks || [] : guidance.steps).map(
                (step, idx) => (
                  <div key={idx} className="flex gap-2 items-start text-[10px] pl-1">
                    <span className="text-cyan-400 shrink-0">•</span>
                    <span className={currentTheme.isDark ? "text-neutral-300" : "text-slate-750"}>
                      {step}
                    </span>
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* Intent Context Extraction Code Block */}
        {focusedNode.type === "Intent" && currentContextPayload ? (
          <div className="flex-1 flex flex-col min-h-[160px]">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5">
                <Code className="h-3.5 w-3.5" />
                LLM Subgraph Payload
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleCopy(JSON.stringify(currentContextPayload, null, 2))}
                className="h-7 px-2 text-neutral-400 hover:text-cyan-400 border border-white/5 bg-neutral-950/40"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-emerald-400 mr-1" />
                ) : (
                  <Copy className="h-3 w-3 mr-1" />
                )}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>

            <div className="flex-1 rounded-xl border border-white/5 bg-neutral-950/70 p-3 overflow-y-auto font-mono text-[10px] text-neutral-300 scrollbar-none">
              <pre className="whitespace-pre-wrap select-text">
                {JSON.stringify(currentContextPayload, null, 2)}
              </pre>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
