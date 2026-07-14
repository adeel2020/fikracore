"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";
import { NAV_ITEMS, type NavItem } from "@/lib/navigation";
import { cn, glassSurfaceStatic } from "@/lib/utils";

const iconStroke = { strokeWidth: 2.25 } as const;

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

/**
 * High-contrast, vivid nav icons.
 * - Idle:    solid brand-color background (high alpha), crisp dark icon for
 *           maximum contrast against the glass panel — no neon glow.
 * - Hover:   brighter saturated brand color with a subtle white ring.
 * - Active:  vivid solid brand color background + bold white icon, with a
 *           thin white ring to mark the selected item.
 *
 * The icon body is rendered in a near-black tone (slate-900) so the
 * saturated brand-color chip reads as a bold, vibrant badge rather
 * than a dim glow.
 */
function NavIcon({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <span
      className={cn(
        "relative flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-all duration-300"
      )}
      style={
        active
          ? {
              background: item.color,
              boxShadow: `inset 0 0 0 1.5px rgba(255,255,255,0.95), 0 4px 10px -2px ${item.color}cc`,
            }
          : {
              background: item.color,
              boxShadow: `inset 0 0 0 1px rgba(255,255,255,0.18)`,
            }
      }
    >
      <Icon
        className="h-4 w-4 transition-all duration-300 nav-icon"
        style={{
          color: active ? "#ffffff" : "#0B1220",
          stroke: active ? "#ffffff" : "#0B1220",
          opacity: 1,
        }}
        data-color={item.color}
        data-active={active ? "1" : "0"}
        {...iconStroke}
      />
    </span>
  );
}

export function Sidebar({ isCollapsed, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        glassSurfaceStatic,
        "fixed left-4 top-4 bottom-4 z-40 flex flex-col rounded-2xl p-3 transition-all duration-300",
        isCollapsed ? "w-[72px]" : "w-[240px]"
      )}
    >
      {/* Sidebar Header / Logo */}
      <div className="mb-8 flex items-center px-1">
        <button
          onClick={onToggleCollapse}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-cyan-500/30 bg-gradient-to-br from-cyan-400/20 to-fuchsia-500/20 hover:scale-105 hover:shadow-[0_0_12px_rgba(34,211,238,0.45)] transition-all duration-300 focus:outline-none cursor-pointer"
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          <Sparkles
            className="h-5 w-5"
            style={{
              color: "#22D3EE",
              stroke: "#22D3EE",
              filter: "drop-shadow(0 0 6px rgba(34,211,238,0.7))",
            }}
            {...iconStroke}
          />
        </button>
        <div
          className={cn(
            "flex flex-col transition-all duration-300 ease-in-out overflow-hidden",
            isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[150px] opacity-100 ml-3"
          )}
        >
          <p className="text-sm font-semibold text-white whitespace-nowrap">Data Storyteller</p>
          <p className="text-xs text-neutral-500 whitespace-nowrap">Obsidian Engine</p>
        </div>
      </div>

      {/* Nav Menu Items */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto font-sans custom-scrollbar">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;

          return (
            <div key={item.href} className="flex flex-col gap-1">
              <Link
                href={item.href}
                className={cn(
                  "group flex items-center rounded-xl px-3 py-2.5 text-sm transition-all duration-300",
                  active
                    ? "text-white"
                    : "text-neutral-300 hover:text-white"
                )}
                style={
                  active
                    ? {
                        borderColor: `${item.color}55`,
                        borderWidth: "1px",
                        background: `linear-gradient(90deg, ${item.color}26, transparent 70%)`,
                        boxShadow: `0 0 18px -4px ${item.color}80`,
                      }
                    : {
                        borderColor: "transparent",
                        borderWidth: "1px",
                      }
                }
              >
                <NavIcon item={item} active={active} />
                <span
                  className={cn(
                    "truncate transition-all duration-300 ease-in-out whitespace-nowrap",
                    isCollapsed ? "max-w-0 opacity-0 ml-0 pointer-events-none" : "max-w-[150px] opacity-100 ml-3"
                  )}
                  style={
                    active
                      ? { color: item.color }
                      : undefined
                  }
                >
                  {item.label}
                </span>
              </Link>
            </div>
          );
        })}
      </nav>



      {/* System Status Display */}
      <div className="mt-4 rounded-xl border border-white/5 bg-white/[0.02] p-3 shrink-0 flex items-center min-h-[48px] justify-start px-3">
        <div className="flex items-center justify-center min-w-[24px]">
          <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
        <div
          className={cn(
            "flex flex-col transition-all duration-300 ease-in-out overflow-hidden",
            isCollapsed ? "max-w-0 opacity-0 ml-0" : "max-w-[150px] opacity-100 ml-3"
          )}
        >
          <p className="text-[10px] text-neutral-500 leading-none whitespace-nowrap">System Status</p>
          <p className="mt-1 text-xs font-bold text-emerald-400 leading-none whitespace-nowrap">Online</p>
        </div>
      </div>
    </aside>
  );
}
