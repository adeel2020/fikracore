"use client";

import { X, Activity, CheckCircle2, AlertTriangle, GitBranch, ServerCog } from "lucide-react";
import type { MarkCapabilityNode } from "@/lib/mark-capability-graph";

function statusText(status: MarkCapabilityNode["status"]) {
  if (status === "requires_approval") return "Approval gated";
  return status.replace(/_/g, " ");
}

function statusColor(status: MarkCapabilityNode["status"]) {
  if (status === "online") return "#34d399";
  if (status === "degraded") return "#fb7185";
  if (status === "requires_approval") return "#f5a623";
  return "#7f9bb3";
}

export function MarkCapabilityPanel({
  node,
  onClose,
  onRunAction,
}: {
  node: MarkCapabilityNode;
  onClose: () => void;
  onRunAction?: (query: string) => void;
}) {
  const color = node.color;
  const status = statusColor(node.status);

  return (
    <aside
      role="dialog"
      aria-modal="false"
      aria-label={`${node.label} details`}
      className="absolute right-3 top-14 z-40 max-h-[72%] w-[min(360px,calc(100vw-24px))] overflow-hidden rounded-lg border bg-[#04080f]/92 text-slate-100 shadow-[0_20px_70px_rgba(0,0,0,0.55)] backdrop-blur-2xl"
      style={{ borderColor: `${color}55`, boxShadow: `0 0 42px ${color}18, 0 20px 70px rgba(0,0,0,0.55)` }}
    >
      <div className="flex items-center gap-3 border-b border-white/10 p-3.5" style={{ background: `linear-gradient(135deg, ${color}16, transparent)` }}>
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full border" style={{ borderColor: `${color}66`, backgroundColor: `${color}16` }}>
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 16px ${color}` }} />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-black uppercase tracking-[0.12em]" style={{ color }}>
            {node.label}
          </h2>
          <p className="mt-0.5 text-[10px] uppercase tracking-[0.12em] text-slate-500">{node.kind}</p>
        </div>
        <button type="button" onClick={onClose} aria-label="Close details" className="rounded p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="max-h-[calc(72vh-72px)] overflow-y-auto p-3.5 jarvis-scrollbar">
        <p className="text-xs leading-relaxed text-slate-300">{node.role}</p>

        <div className="mt-3 flex items-center gap-2 border-t border-white/10 pt-3">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: status, boxShadow: `0 0 10px ${status}` }} />
          <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{statusText(node.status)}</span>
        </div>

        <section className="mt-4">
          <h3 className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">
            <Activity className="h-3.5 w-3.5" />
            Handles
          </h3>
          <div className="grid gap-1.5">
            {node.handles.map((item) => (
              <div key={item} className="flex items-start gap-2 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-2 text-[11px] text-slate-300">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" style={{ color }} />
                {item}
              </div>
            ))}
          </div>
        </section>

        {!!node.namespaces?.length && (
          <section className="mt-4">
            <h3 className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">
              <GitBranch className="h-3.5 w-3.5" />
              gbrain namespaces
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {node.namespaces.map((namespace) => (
                <code key={namespace} className="rounded-md border border-cyan-400/20 bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-100">
                  {namespace}
                </code>
              ))}
            </div>
          </section>
        )}

        {!!node.connectors?.length && (
          <section className="mt-4">
            <h3 className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">
              <ServerCog className="h-3.5 w-3.5" />
              Connectors
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {node.connectors.map((connector) => (
                <span key={connector} className="rounded-md border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[10px] uppercase tracking-[0.08em] text-amber-100">
                  {connector.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </section>
        )}

        {!!node.actions?.length && (
          <section className="mt-4 border-t border-white/10 pt-3">
            <h3 className="mb-2 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.14em] text-slate-500">
              <AlertTriangle className="h-3.5 w-3.5" />
              Actions
            </h3>
            <div className="grid gap-1.5">
              {node.actions.map((action) => (
                <button
                  key={action}
                  type="button"
                  onClick={() => onRunAction?.(action)}
                  className="rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-left text-[11px] font-semibold text-slate-200 transition hover:border-cyan-300/40 hover:bg-cyan-300/10"
                >
                  {action}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}

