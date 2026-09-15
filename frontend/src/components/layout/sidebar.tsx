"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Suspense } from "react";
import { Cpu } from "lucide-react";
import { NAV_ITEMS, type NavItem } from "@/lib/navigation";
import { cn } from "@/lib/utils";

const iconStroke = { strokeWidth: 2.2 } as const;

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

function NavIcon({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <span
      className={cn(
        "relative flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-all duration-300",
        active
          ? "shadow-[0_0_14px_rgba(0,229,255,0.45)] ring-1 ring-white/60"
          : "ring-1 ring-white/10 group-hover:ring-white/25"
      )}
      style={{
        background: active
          ? `linear-gradient(135deg, ${item.color}, ${item.accentColor})`
          : "rgba(15, 23, 42, 0.7)",
      }}
    >
      <Icon
        className="h-4 w-4 transition-all duration-300"
        style={{
          color: active ? "#ffffff" : item.color,
          stroke: active ? "#ffffff" : item.color,
          filter: active ? `drop-shadow(0 0 6px ${item.color})` : undefined,
        }}
        {...iconStroke}
      />
    </span>
  );
}

function SidebarContent({ isCollapsed, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "fixed left-4 top-4 bottom-4 z-40 flex flex-col rounded-2xl p-3 transition-all duration-300",
        "border border-cyan-500/25 bg-slate-950/85 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7),inset_0_1px_0_rgba(255,255,255,0.12)]",
        isCollapsed ? "w-[72px]" : "w-[245px]"
      )}
    >
      {/* Sidebar Header / Jarvis Holographic Brand */}
      <div className="mb-4 flex items-center px-1">
        <button
          onClick={onToggleCollapse}
          className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-cyan-400/40 bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-purple-600/20 hover:scale-105 hover:shadow-[0_0_16px_rgba(0,229,255,0.55)] transition-all duration-300 focus:outline-none cursor-pointer group"
          title={isCollapsed ? "Expand Navigation" : "Collapse Navigation"}
        >
          <div className="absolute inset-0 rounded-xl bg-cyan-400/10 animate-pulse" />
          <Cpu
            className="h-5 w-5 text-cyan-300 group-hover:text-cyan-100 transition-colors drop-shadow-[0_0_8px_rgba(0,229,255,0.8)]"
            {...iconStroke}
          />
        </button>
        <div
          className={cn(
            "flex flex-col transition-all duration-300 ease-in-out overflow-hidden",
            isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[170px] opacity-100 ml-3"
          )}
        >
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-black tracking-widest text-cyan-300 uppercase whitespace-nowrap">
              FIKRA<span className="text-white">CORE</span>
            </span>
            <span className="text-[9px] font-bold px-1 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 leading-none">
              v3
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono tracking-wider whitespace-nowrap uppercase mt-0.5">
            AI Operations Suite
          </p>
        </div>
      </div>

      {/* Nav Menu Items */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto font-sans custom-scrollbar pr-0.5">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "group relative flex items-center rounded-xl px-2 py-1.5 text-sm transition-all duration-300 min-w-0",
                isActive
                  ? "text-white bg-gradient-to-r from-cyan-500/20 via-blue-500/10 to-transparent border border-cyan-400/40 shadow-[0_0_15px_-3px_rgba(0,229,255,0.3)]"
                  : "text-slate-300 hover:text-white hover:bg-white/[0.04] border border-transparent"
              )}
              title={isCollapsed ? `${item.label} (${item.description})` : undefined}
            >
              {isActive && (
                <div
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full shadow-[0_0_8px_rgba(0,229,255,0.9)]"
                  style={{ background: item.color }}
                />
              )}

              <NavIcon item={item} active={isActive} />

              <div
                className={cn(
                  "flex items-center justify-between flex-1 min-w-0 transition-all duration-300 ease-in-out",
                  isCollapsed ? "max-w-0 opacity-0 ml-0 pointer-events-none" : "max-w-[170px] opacity-100 ml-2.5"
                )}
              >
                <span
                  className="truncate text-xs font-semibold tracking-wide whitespace-nowrap"
                  style={isActive ? { color: item.color } : undefined}
                >
                  {item.label}
                </span>

                {item.badge && (
                  <span
                    className={cn(
                      "text-[9px] font-mono px-1.5 py-0.5 rounded tracking-tighter uppercase shrink-0 border ml-1",
                      isActive
                        ? "bg-cyan-500/25 border-cyan-400/50 text-cyan-200"
                        : "bg-slate-800/80 border-slate-700/60 text-slate-400 group-hover:border-slate-600 group-hover:text-slate-300"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Real-time Telemetry Status Display (Jarvis Inspired) */}
      <div className="mt-2 rounded-xl border border-cyan-500/20 bg-slate-900/60 p-2.5 shrink-0 flex items-center min-h-[48px] justify-start">
        <div className="relative flex items-center justify-center min-w-[24px]">
          <div className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
          <div className="absolute h-4 w-4 rounded-full border border-emerald-400/40 animate-ping" />
        </div>
        <div
          className={cn(
            "flex flex-col transition-all duration-300 ease-in-out overflow-hidden",
            isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[170px] opacity-100 ml-2.5"
          )}
        >
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-slate-400 font-mono tracking-wider uppercase leading-none whitespace-nowrap">
              gbrain MCP
            </span>
            <span className="text-[9px] font-bold text-emerald-300 font-mono leading-none">
              LIVE
            </span>
          </div>
          <p className="mt-1 text-[11px] font-semibold text-white font-mono leading-none whitespace-nowrap truncate">
            Parity: 100% (132p)
          </p>
        </div>
      </div>
    </aside>
  );
}

export function Sidebar(props: SidebarProps) {
  return (
    <Suspense fallback={null}>
      <SidebarContent {...props} />
    </Suspense>
  );
}
