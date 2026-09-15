"use client";

import React, { useMemo, useRef, useState } from "react";
import {
  Activity,
  BarChart3,
  ChevronDown,
  GitBranch,
  ListChecks,
  Network,
  ShieldCheck,
  Sparkles,
  Maximize2,
  X,
} from "lucide-react";
import { ChatMessage } from "@/lib/api/qna";
import { cn } from "@/lib/utils";

type StorytellerPayload = NonNullable<ChatMessage["storyteller"]>;
type VisualExplanation = NonNullable<StorytellerPayload["visual_explanation"]>;
type VisualWidget = NonNullable<VisualExplanation["widgets"]>[number];

type DomainNode = {
  id?: string;
  label?: string;
  kind?: string;
};

type DomainLink = {
  source?: string;
  target?: string;
  relationship?: string;
};

type EvidenceRow = {
  claim_id?: string;
  statement?: string;
  grade?: string;
  confidence?: number;
  fcaps?: string[];
};

type CausalStep = {
  id?: string;
  label?: string;
};

type NextAction = {
  id?: string;
  label?: string;
  action_type?: string;
  priority?: number;
  requires_approval?: boolean;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function prettyLabel(value?: string | null): string {
  if (!value) return "unknown";
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function widgetIcon(type: string) {
  if (type.includes("domain") || type.includes("topology")) return Network;
  if (type.includes("causal") || type.includes("correlation")) return GitBranch;
  if (type.includes("timeline") || type.includes("kpi")) return Activity;
  if (type.includes("evidence")) return ShieldCheck;
  return ListChecks;
}

function confidenceTone(confidence?: number): string {
  if (typeof confidence !== "number") return "text-neutral-400";
  if (confidence >= 0.75) return "text-cyan-300";
  if (confidence >= 0.45) return "text-pink-300";
  return "text-fuchsia-300";
}

function compactWidgetTitle(title?: string): string {
  if (!title) return "Widget";
  const map: Record<string, string> = {
    "Domain and service impact": "Domain Impact",
    "Domain Impact": "Domain Impact",
    "Evidence confidence matrix": "Evidence Matrix",
    "Evidence Matrix": "Evidence Matrix",
    "Incident timeline": "Timeline",
    "Timeline": "Timeline",
    "Causal chain": "Causal Chain",
    "Causal Chain": "Causal Chain",
    "Next best actions": "Next Actions",
    "Next Actions": "Next Actions",
  };
  return map[title] || title;
}

function getPrimaryWidget(widgets: VisualWidget[], primary?: string | null): VisualWidget | undefined {
  return widgets.find((widget) => widget.type === primary) ?? widgets[0];
}

function MiniCanvas({ widget, expanded = false }: { widget?: VisualWidget; expanded?: boolean }) {
  const data = asRecord(widget?.data);
  const nodes = asArray<DomainNode>(data.nodes);
  const links = asArray<DomainLink>(data.links);
  const steps = asArray<CausalStep>(data.steps);
  const displayNodes = nodes.length
    ? nodes.slice(0, expanded ? nodes.length : 7)
    : steps.slice(0, expanded ? steps.length : 6).map((step, index) => ({
        id: step.id ?? `step-${index}`,
        label: step.label ?? `Step ${index + 1}`,
        kind: index === 0 ? "trigger" : "evidence",
      }));

  if (!displayNodes.length) {
    return (
      <div className="grid h-36 place-items-center rounded-xl border border-white/10 bg-black/20 text-xs text-neutral-500">
        No graphable evidence yet
      </div>
    );
  }

  const center = { x: 50, y: 50 };
  const plotted = displayNodes.map((node, index) => {
    const angle = -Math.PI / 2 + (index / Math.max(displayNodes.length, 1)) * Math.PI * 2;
    const radius = node.kind === "service" ? 27 : 35;
    return {
      ...node,
      x: Number((center.x + Math.cos(angle) * radius).toFixed(2)),
      y: Number((center.y + Math.sin(angle) * radius).toFixed(2)),
    };
  });

  if (expanded) {
    return <div className="space-y-3">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {displayNodes.map((node, index) => <div key={node.id ?? index} className="border-l-2 border-cyan-400/60 px-3 py-2 text-xs break-words">
          <span className="block text-slate-400 mb-1">{prettyLabel(node.kind)}</span>{node.label}
        </div>)}
      </div>
      {!!links.length && <ul className="divide-y divide-white/10 text-xs">
        {links.map((link, index) => <li key={index} className="py-2 break-words">
          {nodes.find((node) => node.id === link.source)?.label || link.source}
          <span className="text-slate-400"> {prettyLabel(link.relationship)} </span>
          {nodes.find((node) => node.id === link.target)?.label || link.target}
        </li>)}
      </ul>}
    </div>;
  }

  return (
    <div className="relative h-48 sm:h-52 overflow-hidden rounded-xl border border-cyan-400/20 bg-[#071527]/80 flex flex-col justify-between">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,200,255,0.18),transparent_60%)]" />
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(34,211,238,0.18)" strokeDasharray="4 5" />
        <circle cx="50" cy="50" r="24" fill="none" stroke="rgba(236,72,153,0.18)" />
        {plotted.map((node, index) => {
          const related = links.some((link) => link.source === node.id || link.target === node.id);
          return (
            <line
              key={`${node.id ?? index}-link`}
              x1="50"
              y1="50"
              x2={node.x}
              y2={node.y}
              stroke={related ? "rgba(34,211,238,0.6)" : "rgba(217,70,239,0.3)"}
              strokeDasharray="2 3"
              strokeWidth="0.5"
            />
          );
        })}
        <circle cx="50" cy="50" r="5.5" fill="rgba(8,40,99,0.95)" stroke="rgba(34,211,238,0.85)" strokeWidth="0.8" />
        {plotted.map((node, index) => (
          <g key={`${node.id ?? index}-node`}>
            <circle
              cx={node.x}
              cy={node.y}
              r={node.kind === "domain" ? 4.2 : 3.4}
              fill={node.kind === "domain" ? "rgba(34,211,238,0.95)" : "rgba(217,70,239,0.9)"}
              stroke="rgba(255,255,255,0.8)"
              strokeWidth="0.4"
            />
          </g>
        ))}
      </svg>
      {/* Visual Header / Node count */}
      <div className="relative z-10 px-3 pt-2 flex items-center justify-between text-[10px] text-cyan-300/80">
        <span className="font-semibold tracking-wider uppercase text-[9px]">{compactWidgetTitle(widget?.title)}</span>
        <span className="text-slate-400 font-mono text-[9px]">{displayNodes.length} nodes</span>
      </div>
      {/* Node Pills Row */}
      <div className="relative z-10 px-2 pb-2 flex flex-wrap items-center justify-center gap-1.5 max-h-16 overflow-hidden">
        {plotted.slice(0, 4).map((node, index) => (
          <div
            key={`${node.id ?? index}-label`}
            title={node.label}
            className="inline-flex items-center rounded-md border border-cyan-400/25 bg-[#06111f]/90 backdrop-blur-sm px-2 py-0.5 text-[10px] font-medium text-cyan-100 shadow-sm"
          >
            {node.label}
          </div>
        ))}
      </div>
    </div>
  );
}

function EvidenceMatrix({ widget }: { widget?: VisualWidget }) {
  const rows = asArray<EvidenceRow>(asRecord(widget?.data).rows).slice(0, 5);
  if (!rows.length) return null;

  return (
    <div className="grid gap-2">
      {rows.map((row, index) => (
        <div key={row.claim_id ?? index} className="rounded-lg border border-white/10 bg-black/20 p-2">
          <div className="flex items-center justify-between gap-2">
            <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-2 py-0.5 text-[10px] text-cyan-200">
              {prettyLabel(row.grade)}
            </span>
            <span className={cn("text-[10px]", confidenceTone(row.confidence))}>
              {typeof row.confidence === "number" ? `${Math.round(row.confidence * 100)}%` : "n/a"}
            </span>
          </div>
          <div className="mt-1 line-clamp-2 text-[11px] leading-snug text-neutral-300">{row.statement}</div>
        </div>
      ))}
    </div>
  );
}

function TimelineStrip({ widget }: { widget?: VisualWidget }) {
  const events = asArray<Record<string, unknown>>(asRecord(widget?.data).events).slice(0, 5);
  if (!events.length) return null;

  return (
    <div className="relative grid gap-2 pl-3">
      <div className="absolute bottom-1 left-1 top-1 w-px bg-cyan-400/25" />
      {events.map((event, index) => (
        <div key={String(event.id ?? index)} className="relative rounded-lg border border-white/10 bg-black/20 p-2">
          <div className="absolute -left-[13px] top-3 h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_12px_rgba(34,211,238,0.8)]" />
          <div className="text-[10px] uppercase tracking-wide text-neutral-500">
            {String(event.timestamp ?? event.time ?? `event ${index + 1}`)}
          </div>
          <div className="mt-0.5 line-clamp-2 text-[11px] text-neutral-300">
            {String(event.label ?? event.value ?? event.description ?? "Timeline event")}
          </div>
        </div>
      ))}
    </div>
  );
}

function NextActions({ widget }: { widget?: VisualWidget }) {
  const actions = asArray<NextAction>(asRecord(widget?.data).actions).slice(0, 4);
  const questions = asArray<string>(asRecord(widget?.data).questions).slice(0, 3);
  if (!actions.length && !questions.length) return null;

  return (
    <div className="grid gap-2">
      {actions.map((action, index) => (
        <div key={action.id ?? index} className="flex items-start gap-2 rounded-lg border border-white/10 bg-black/20 p-2">
          <div className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-cyan-400/10 text-[10px] text-cyan-200">
            {action.priority ?? index + 1}
          </div>
          <div className="min-w-0">
            <div className="line-clamp-2 text-[11px] font-semibold text-neutral-100">{action.label}</div>
            <div className="mt-0.5 text-[10px] text-neutral-500">{prettyLabel(action.action_type)}</div>
          </div>
        </div>
      ))}
      {questions.map((question, index) => (
        <div key={`${question}-${index}`} className="rounded-lg border border-fuchsia-300/20 bg-fuchsia-300/[0.05] p-2 text-[11px] text-fuchsia-100">
          {question}
        </div>
      ))}
    </div>
  );
}

export function StorytellerVisualExplanation({ payload, speaking = false }: { payload: StorytellerPayload; speaking?: boolean }) {
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const visual = payload.visual_explanation;
  const widgets = useMemo(() => visual?.widgets ?? [], [visual?.widgets]);
  const primaryWidget = getPrimaryWidget(widgets, visual?.primary_widget);
  const selectedWidget = widgets.find((widget) => widget.id === selectedId) ?? primaryWidget;
  const evidenceWidget = widgets.find((widget) => widget.type === "evidence_confidence_matrix");
  const timelineWidget = widgets.find((widget) => widget.type === "timeline");
  const nextActionWidget = widgets.find((widget) => widget.type === "next_action_tree");

  if (!widgets.length) return null;

  const confidence = primaryWidget?.confidence;
  const claims = payload.narrative?.claims ?? [];
  const actions = payload.narrative?.next_actions ?? [];

  return (
    <div data-testid="story-visual" data-speaking={speaking} className={cn("mt-3 overflow-hidden rounded-2xl border bg-[#06111f]/85 shadow-[0_18px_50px_rgba(6,182,212,0.08)]", speaking ? "border-cyan-300 ring-1 ring-cyan-300/40" : "border-cyan-400/20")}>
      <div className="relative p-3">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_12%,rgba(34,211,238,0.16),transparent_30%),radial-gradient(circle_at_84%_8%,rgba(217,70,239,0.13),transparent_34%)]" />
        <div className="relative grid gap-4 lg:grid-cols-[minmax(280px,1fr)_minmax(280px,1.15fr)]">
          <div className="flex flex-col justify-between space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-cyan-400/30 bg-cyan-400/10 text-cyan-300 shadow-sm">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-slate-100 truncate">
                    {Boolean(payload.narrative?.title?.includes("Mobile RTR") || payload.answer?.includes("Mobile Core RTR"))
                      ? "Mobile Core RTR Investigation"
                      : "Visual Explanation"}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">
                    {Boolean(payload.narrative?.title?.includes("Mobile RTR") || payload.answer?.includes("Mobile Core RTR"))
                      ? "Domain: Mobile Core · Role: Mobile RTR"
                      : `${prettyLabel(payload.intent)} · ${widgets.length} views`}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  title="Open investigation workspace"
                  aria-label="Open investigation workspace"
                  onClick={() => dialog.current?.showModal()}
                  className="p-1.5 text-cyan-200 hover:bg-white/10 rounded-md transition"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setOpen((value) => !value)}
                  className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-neutral-300 transition hover:border-cyan-300/40 hover:text-cyan-100"
                >
                  {open ? "Hide detail" : "Investigate"}
                  <ChevronDown className={cn("h-3 w-3 transition", open && "rotate-180")} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl border border-white/10 bg-black/25 p-2 sm:p-2.5 min-w-0">
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 font-medium">Audience</div>
                <div className="mt-0.5 text-xs font-semibold text-neutral-100 truncate" title={prettyLabel(visual?.audience ?? payload.narrative?.audience)}>
                  {prettyLabel(visual?.audience ?? payload.narrative?.audience)}
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-2 sm:p-2.5 min-w-0">
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 font-medium">Confidence</div>
                <div className={cn("mt-0.5 text-xs font-semibold font-mono", confidenceTone(confidence))}>
                  {typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "n/a"}
                </div>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/25 p-2 sm:p-2.5 min-w-0">
                <div className="text-[10px] uppercase tracking-wider text-neutral-400 font-medium">Actions</div>
                <div className="mt-0.5 text-xs font-semibold text-neutral-100 font-mono">{actions.length}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-2">
              {widgets.slice(0, 4).map((widget) => {
                const Icon = widgetIcon(widget.type);
                const title = compactWidgetTitle(widget.title);
                const isSelected = selectedWidget?.id === widget.id;
                return (
                  <button
                    type="button"
                    key={widget.id}
                    onClick={() => setSelectedId(widget.id)}
                    aria-pressed={isSelected}
                    className={cn(
                      "group rounded-xl border p-2.5 text-left transition relative overflow-hidden",
                      isSelected
                        ? "border-cyan-400/80 bg-cyan-950/40 shadow-[0_0_18px_rgba(217,70,239,0.16)] ring-1 ring-cyan-400/40"
                        : "border-white/10 bg-black/20 hover:border-fuchsia-400/30 hover:bg-fuchsia-400/[0.04]"
                    )}
                  >
                    <div className="flex items-center justify-between gap-1.5">
                      <div className="flex items-center gap-2 min-w-0">
                        <Icon className={cn("h-3.5 w-3.5 shrink-0 transition", isSelected ? "text-cyan-300" : "text-neutral-400 group-hover:text-cyan-300")} />
                        <span className="truncate text-xs font-semibold text-neutral-200 group-hover:text-white" title={widget.title}>
                          {title}
                        </span>
                      </div>
                      {typeof widget.confidence === "number" ? (
                        <span className={cn("text-[10px] font-mono shrink-0 px-1.5 py-0.5 rounded bg-white/5", confidenceTone(widget.confidence))}>
                          {Math.round(widget.confidence * 100)}%
                        </span>
                      ) : null}
                    </div>
                    {widget.supports_claim_ids?.length ? (
                      <div className="mt-1 text-[10px] text-neutral-400/90 pl-5.5 truncate">
                        supports {widget.supports_claim_ids.length} claim{widget.supports_claim_ids.length === 1 ? "" : "s"}
                      </div>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
          <MiniCanvas widget={selectedWidget} />
        </div>
      </div>

      {open ? (
        <div className="grid gap-3 border-t border-cyan-400/10 bg-black/20 p-3 lg:grid-cols-3">
          <section>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold text-cyan-100">
              <ShieldCheck className="h-3.5 w-3.5" />
              Evidence
            </div>
            <EvidenceMatrix widget={evidenceWidget} />
          </section>
          <section>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold text-cyan-100">
              <BarChart3 className="h-3.5 w-3.5" />
              Timeline
            </div>
            <TimelineStrip widget={timelineWidget} />
          </section>
          <section>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold text-cyan-100">
              <ListChecks className="h-3.5 w-3.5" />
              Next
            </div>
            <NextActions widget={nextActionWidget} />
          </section>
          {claims.length ? (
            <div className="lg:col-span-3 rounded-xl border border-white/10 bg-black/20 p-2 text-[10px] text-neutral-500">
              Claims are rendered as structured visual context. Full technical proof remains in the written answer above.
            </div>
          ) : null}
        </div>
      ) : null}
      <dialog ref={dialog} aria-label="Incident investigation" className="fixed inset-0 m-auto h-[90dvh] w-[96vw] max-w-7xl overflow-hidden rounded-lg border border-cyan-400/30 bg-[#06111f] p-0 text-slate-100 backdrop:bg-black/60">
        <div className="flex h-full flex-col">
          <header className="flex shrink-0 items-center justify-between gap-3 border-b border-white/10 p-4">
            <div className="min-w-0">
              <h2 className="text-base font-semibold break-words">{payload.narrative?.title || "Incident investigation"}</h2>
              <p className="text-xs text-slate-400">{prettyLabel(payload.narrative?.lifecycle_state)} · {prettyLabel(payload.narrative?.audience)}</p>
            </div>
            <button type="button" title="Close investigation" aria-label="Close investigation" onClick={() => dialog.current?.close()} className="p-2 hover:bg-white/10 rounded"><X className="h-5 w-5" /></button>
          </header>
          <div className="min-h-0 flex-1 overflow-auto p-4">
            <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Investigation views">
              {widgets.map((widget) => (
                <button
                  type="button"
                  key={widget.id}
                  aria-pressed={selectedWidget?.id === widget.id}
                  onClick={() => setSelectedId(widget.id)}
                  className={cn(
                    "border-b-2 px-3 py-2 text-xs font-medium transition",
                    selectedWidget?.id === widget.id
                      ? "border-cyan-300 text-cyan-200 font-semibold"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  )}
                >
                  {compactWidgetTitle(widget.title)}
                </button>
              ))}
            </div>
            <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(260px,2fr)]">
              <section className="min-w-0">
                <h3 className="text-sm font-semibold mb-3">{selectedWidget?.title}</h3>
                {selectedWidget?.type === "evidence_confidence_matrix" ? <EvidenceMatrix widget={selectedWidget} /> : selectedWidget?.type === "timeline" ? <TimelineStrip widget={selectedWidget} /> : selectedWidget?.type === "next_action_tree" ? <NextActions widget={selectedWidget} /> : <MiniCanvas widget={selectedWidget} expanded />}
              </section>
              <section className="min-w-0">
                <h3 className="text-sm font-semibold mb-3">Supporting claims</h3>
                {claims.filter((claim) => selectedWidget?.supports_claim_ids?.includes(claim.id)).map((claim) => <article key={claim.id} className="border-b border-white/10 py-3 text-xs">
                  <p>{claim.statement}</p>
                  <p className="mt-2 text-slate-400">{prettyLabel(claim.grade)} · {Math.round(claim.confidence * 100)}% confidence</p>
                  {!!claim.fcaps?.length && <p className="mt-1 text-slate-400">FCAPS: {claim.fcaps.join(", ")}</p>}
                </article>)}
                {!selectedWidget?.supports_claim_ids?.length && <p className="text-xs text-slate-400">No linked claims supplied.</p>}
                <h3 className="text-sm font-semibold mt-5 mb-3">Source references</h3>
                <ul className="space-y-2 text-xs text-slate-300 break-words">
                  {(selectedWidget?.provenance ?? []).map((source, index) => <li key={index}>{typeof source === "string" ? source : <>
                    <span className="block">{String(source.source || "Source")}</span>
                    {source.slug ? <code className="text-cyan-200">{String(source.slug)}</code> : null}
                    {source.relationship ? <span className="block text-slate-400">{String(source.relationship)}</span> : null}
                    {source.timestamp ? <time className="block text-slate-400">{String(source.timestamp)}</time> : null}
                  </>}</li>)}
                </ul>
                {!selectedWidget?.provenance?.length && <p className="text-xs text-slate-400">No source references supplied.</p>}
              </section>
            </div>
          </div>
        </div>
      </dialog>
    </div>
  );
}
