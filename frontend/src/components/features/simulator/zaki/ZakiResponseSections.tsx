"use client";

import React from "react";
import {
  Info,
  HelpCircle,
  CheckCircle2,
  XCircle,
  AlertOctagon,
  ArrowRightCircle,
  ShieldCheck,
  Globe2,
} from "lucide-react";
import type { ZakiResponseV2, HighlightedEntity } from "@/lib/simulation-store";

export interface ZakiResponseSectionsProps {
  response: ZakiResponseV2;
}

export function ZakiResponseSections({ response }: ZakiResponseSectionsProps) {
  const getSectionIcon = (title: string) => {
    const t = title.toLowerCase();
    if (t.includes("happened") && !t.includes("next")) {
      return <Info className="w-3.5 h-3.5 text-cyan-400" />;
    }
    if (t.includes("matters")) {
      return <HelpCircle className="w-3.5 h-3.5 text-purple-400" />;
    }
    if (t.includes("supports")) {
      return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
    }
    if (t.includes("contradicts")) {
      return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
    }
    if (t.includes("missing")) {
      return <AlertOctagon className="w-3.5 h-3.5 text-amber-400" />;
    }
    if (t.includes("next")) {
      return <ArrowRightCircle className="w-3.5 h-3.5 text-teal-400" />;
    }
    return <Info className="w-3.5 h-3.5 text-cyan-400" />;
  };

  const renderEntityBadge = (entity: HighlightedEntity) => {
    const role = entity.visual_role || "STRUCTURE";
    const colorClasses =
      role === "CONFIRMED"
        ? "bg-teal-500/10 text-teal-300 border-teal-500/30"
        : role === "FOCUS"
        ? "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/30"
        : "bg-cyan-500/10 text-cyan-300 border-cyan-500/30";

    return (
      <span
        key={entity.name}
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono border ${colorClasses}`}
        title={`${entity.type} (${entity.role}) - ${entity.description || ""}`}
        data-testid={`zaki-entity-${entity.name}`}
      >
        <span className="font-semibold">{entity.name}</span>
        <span className="text-[9px] opacity-70">[{entity.role}]</span>
      </span>
    );
  };

  // If structured sections exist, render them
  const hasSections = response.sections && response.sections.length > 0;

  return (
    <div className="flex flex-col gap-3 p-3 text-xs" data-testid="zaki-response-sections">
      {hasSections ? (
        response.sections.map((section, idx) => (
          <div
            key={idx}
            className="p-2.5 rounded-md bg-slate-900/50 border border-slate-800/80 flex flex-col gap-1.5"
            data-testid={`zaki-section-${section.title.toLowerCase().replace(/\s+/g, "-")}`}
          >
            <div className="flex items-center gap-1.5 text-[11px] font-bold tracking-wide uppercase text-slate-300">
              {getSectionIcon(section.title)}
              <span>{section.title}</span>
            </div>
            <p className="text-slate-300 leading-relaxed whitespace-pre-line text-xs">
              {section.content}
            </p>
          </div>
        ))
      ) : (
        <div className="p-2.5 rounded-md bg-slate-900/50 border border-slate-800/80">
          <p className="text-slate-200 leading-relaxed whitespace-pre-line text-xs">
            {response.answer}
          </p>
        </div>
      )}

      {/* Highlighted Entities Panel */}
      {response.highlighted_entities && response.highlighted_entities.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-1">
          <span className="text-[10px] uppercase font-mono font-bold text-slate-400 tracking-wider">
            Corroborated Objects
          </span>
          <div className="flex flex-wrap gap-1.5">
            {response.highlighted_entities.map(renderEntityBadge)}
          </div>
        </div>
      )}

      {/* Uncertainty Notice */}
      {response.uncertainty && response.uncertainty.length > 0 && (
        <div className="p-2 rounded bg-amber-950/20 border border-amber-500/30 text-amber-300/90 text-[11px] flex flex-col gap-1">
          <span className="font-semibold uppercase tracking-wider text-[10px]">
            Epistemic Uncertainty
          </span>
          <ul className="list-disc list-inside space-y-0.5">
            {response.uncertainty.map((u, i) => (
              <li key={i}>{u}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Simulation Grounding Footer */}
      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
        <div className="flex items-center gap-1 text-teal-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Grounded in Simulation</span>
        </div>
        <div className="flex items-center gap-1 text-slate-400">
          <Globe2 className="w-3 h-3 text-slate-400" />
          <span>Air-gapped (Zero Internet)</span>
        </div>
      </div>
    </div>
  );
}
