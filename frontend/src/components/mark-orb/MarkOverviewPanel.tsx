"use client";

import { useEffect, useState } from "react";
import { Activity, BrainCircuit, Database, GitBranch, Network, Radio, ServerCog } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { MarkRouteTrace, MarkVisualState } from "@/lib/mark-capability-graph";

/*
 * Filament overview HUD adapted from APEX-UI's ApexOverviewPanel.tsx.
 * The original overview lamp panel credits 21st.dev community components and is
 * MIT-licensed. Preserve this attribution when moving or modifying the file.
 */

const ACCENT = "#00e5ff";

type Tile = {
  key: string;
  icon: LucideIcon;
  label: string;
  value: string;
};

function Clock() {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    const update = () => setNow(new Date());
    const first = window.setTimeout(update, 0);
    const id = setInterval(update, 30000);
    return () => {
      window.clearTimeout(first);
      clearInterval(id);
    };
  }, []);

  if (!now) {
    return (
      <div style={{ display: "flex", alignItems: "flex-end", gap: 22, flexWrap: "wrap", height: 48 }}>
        <div style={{ width: 92, height: 40 }} />
        <div style={{ width: 154, height: 36 }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 22, flexWrap: "wrap" }}>
      <div>
        <div style={{ fontSize: 32, fontWeight: 300, letterSpacing: "0.04em", color: "#f0ede8", lineHeight: 1, textShadow: `0 0 22px ${ACCENT}33` }}>
          {now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
        </div>
        <div style={{ fontSize: 10.5, letterSpacing: "0.2em", color: "rgba(240,237,232,0.55)", marginTop: 4, textTransform: "uppercase" }}>
          {now.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
        </div>
      </div>
      <div>
        <div style={{ fontSize: 18, fontWeight: 400, color: `${ACCENT}e6`, textTransform: "uppercase" }}>ZAKI</div>
        <div style={{ fontSize: 9.5, letterSpacing: "0.12em", color: "rgba(240,237,232,0.5)", marginTop: 2, textTransform: "uppercase" }}>
          TELECOM BRAIN ONLINE
        </div>
      </div>
    </div>
  );
}

function stateLabel(state: MarkVisualState) {
  return state.replace(/_/g, " ").toUpperCase();
}

export function MarkOverviewPanel({ state, trace }: { state: MarkVisualState; trace?: MarkRouteTrace | null }) {
  const [open, setOpen] = useState(false);
  const filament = open ? 482 : 320;
  const cap = "calc(100vw - 184px)";

  const tiles: Tile[] = [
    { key: "state", icon: Radio, label: "Runtime state", value: stateLabel(state) },
    { key: "engine", icon: BrainCircuit, label: "Active engine", value: trace?.activeEngineId?.replace(/_/g, " ") || "standing by" },
    { key: "services", icon: GitBranch, label: "Services", value: trace?.activeServiceIds?.join(", ").replace(/_/g, " ") || "none selected" },
    { key: "connectors", icon: ServerCog, label: "Connectors", value: trace?.activeConnectorIds?.join(", ").replace(/_/g, " ") || "gbrain ready" },
    { key: "namespaces", icon: Database, label: "gbrain namespace", value: trace?.activeNamespaces?.join(", ") || "semantic graph" },
    { key: "domain", icon: Network, label: "Domain spine", value: "telemetry -> correlation -> incident -> story -> learning" },
  ];

  return (
    <div className="absolute left-0 top-0 z-30 w-[540px] max-w-[92vw]" style={{ pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 8,
          width: "min(520px, 94vw)",
          height: 236,
          pointerEvents: "none",
          background: `radial-gradient(ellipse 48% 70% at 46% 0%, ${ACCENT}${open ? "55" : "28"}, ${ACCENT}0a 46%, transparent 72%)`,
          filter: "blur(10px)",
          transition: "all .5s ease",
        }}
      />

      <div
        onClick={() => setOpen((value) => !value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            setOpen((value) => !value);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Toggle Zaki overview panel"
        aria-expanded={open}
        style={{ position: "relative", height: 40, cursor: "pointer", pointerEvents: "auto", userSelect: "none" }}
      >
        <div
          style={{
            position: "absolute",
            top: 14,
            left: 8,
            width: `min(${filament}px, ${cap})`,
            height: 2,
            borderRadius: 2,
            background: "#a5f3fc",
            boxShadow: `0 0 10px ${ACCENT}, 0 0 26px ${ACCENT}${open ? ", 0 0 54px " + ACCENT : ""}`,
            transition: "all .5s ease",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 11,
            left: open ? `min(${filament}px, ${cap})` : 6,
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: "#e0fbff",
            boxShadow: `0 0 10px ${ACCENT}, 0 0 18px ${ACCENT}`,
            transition: "left .5s ease",
            pointerEvents: "none",
          }}
        />
        <span
          style={{
            position: "absolute",
            top: 20,
            left: 10,
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: 9,
            letterSpacing: "0.34em",
            color: `rgba(165,243,252,${open ? 0.9 : 0.55})`,
            transition: "color .4s",
          }}
        >
          OVERVIEW
        </span>
      </div>

      <div style={{ paddingLeft: 14, paddingTop: 6, width: "fit-content", pointerEvents: "auto" }}>
        <Clock />
        {open && (
          <div style={{ marginTop: 16, width: 310, display: "grid", gap: 8 }}>
            {tiles.map(({ key, icon: Icon, label, value }) => (
              <div
                key={key}
                style={{
                  display: "grid",
                  gridTemplateColumns: "22px minmax(0, 1fr)",
                  gap: 10,
                  padding: "10px 12px",
                  background: "rgba(6,14,26,0.74)",
                  border: `1px solid ${ACCENT}2a`,
                  borderRadius: 8,
                  backdropFilter: "blur(8px)",
                  color: "rgba(240,237,232,0.9)",
                }}
              >
                <span style={{ display: "flex", color: ACCENT, paddingTop: 1 }}>
                  <Icon size={15} />
                </span>
                <span style={{ minWidth: 0 }}>
                  <span style={{ display: "block", fontSize: 9, letterSpacing: "0.14em", color: "rgba(240,237,232,0.42)", textTransform: "uppercase" }}>{label}</span>
                  <span style={{ display: "block", marginTop: 2, fontSize: 11, lineHeight: 1.25, color: key === "domain" ? "#f5a623" : "rgba(240,237,232,0.82)", textTransform: "uppercase" }}>{value}</span>
                </span>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 7, paddingTop: 2, color: "rgba(240,237,232,0.48)", fontSize: 9.5, letterSpacing: "0.12em", textTransform: "uppercase" }}>
              <Activity size={13} color={ACCENT} />
              gbrain stores semantic context, not raw source data
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
