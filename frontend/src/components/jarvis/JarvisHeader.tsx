"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Workflow,
  Eye,
  Database,
  Globe2,
  Bot,
  BookOpen,
  Search,
  Bell,
  Settings,
  UserCircle,
  Brain,
  ChevronDown,
  Sun,
  Moon,
  MessageSquare,
  Maximize2,
  Minimize2,
} from "lucide-react";

interface JarvisHeaderProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  isDarkMode?: boolean;
  onToggleTheme?: () => void;
  onOpenSearch?: () => void;
  onOpenSettings?: () => void;
  onOpenChat?: () => void;
}

const NAV_TABS = [
  { id: "correlation", label: "CORRELATION", icon: Workflow },
  { id: "fcsps", label: "FCAPS LENS", icon: Eye },
  { id: "digital-assets", label: "DIGITAL ASSETS", icon: Database },
  { id: "network", label: "NETWORK INTELLIGENCE", icon: Globe2 },
  { id: "automation", label: "AUTOMATION", icon: Bot },
  { id: "knowledge", label: "KNOWLEDGE CORE", icon: BookOpen },
];

export function JarvisHeader({
  activeTab,
  onSelectTab,
  isDarkMode = true,
  onToggleTheme,
  onOpenSearch,
  onOpenSettings,
  onOpenChat,
}: JarvisHeaderProps) {
  const [timeStr, setTimeStr] = useState("10:42:18 AM");
  const [dateStr, setDateStr] = useState("27 Aug 2026");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        new Intl.DateTimeFormat("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: true,
          timeZone: "Asia/Dubai",
        }).format(now)
      );
      setDateStr(
        new Intl.DateTimeFormat("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
          timeZone: "Asia/Dubai",
        }).format(now)
      );
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => {
      document.removeEventListener("fullscreenchange", onFsChange);
    };
  }, []);

  const toggleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        if (document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
        }
      } else {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        }
      }
    } catch (err) {
      console.warn("Fullscreen toggle failed", err);
    }
  };

  return (
    <header className="grid grid-cols-[auto_1fr_auto] items-center gap-3 w-full h-[60px] select-none">
      {/* 1. Left Brand Badge - Zaki Incident Manager */}
      <div className="jarvis-card flex items-center gap-2.5 px-3 py-1.5 h-full shrink-0">
        <div
          className={`relative w-9 h-9 rounded-full flex items-center justify-center shadow-inner ${
            isDarkMode
              ? "bg-cyan-950/60 border border-cyan-500/40 text-[#00e5ff]"
              : "bg-blue-50 border border-blue-200/90 text-[#0a66ff]"
          }`}
        >
          <div className="absolute inset-0.5 rounded-full border border-dashed border-cyan-400/60 hud-spin-slow pointer-events-none" />
          <Brain className="w-4.5 h-4.5 text-cyan-400" strokeWidth={2} />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1
              className={`font-mono text-[17px] font-bold tracking-wide leading-none ${
                isDarkMode ? "text-white drop-shadow-[0_0_10px_rgba(0,229,255,0.4)]" : "text-[#082863]"
              }`}
            >
              ZAKI
            </h1>
            <span className="font-mono text-[8.5px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-[#00e5ff] border border-cyan-400/35 tracking-wider">
              INCIDENT MGR
            </span>
          </div>
          <p className="font-mono text-[9px] font-bold uppercase tracking-[0.16em] text-[#00e5ff] mt-0.5">
            TELECOM BRAIN
          </p>
        </div>
      </div>

      {/* 2. Center Module Navigation Bar */}
      <div className="jarvis-card flex items-center justify-start sm:justify-center gap-1 sm:gap-1.5 px-2.5 h-full overflow-x-auto jarvis-scrollbar">
        {NAV_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg font-mono text-[10px] sm:text-[10.5px] font-bold uppercase tracking-wide transition-all duration-200 whitespace-nowrap cursor-pointer shrink-0 ${
                isActive
                  ? isDarkMode
                    ? "text-[#00e5ff] bg-cyan-500/15 shadow-[0_0_14px_rgba(0,229,255,0.25)] border border-cyan-400/40"
                    : "text-[#0a66ff] bg-blue-50 shadow-[0_2px_12px_rgba(10,102,255,0.15)] border border-blue-200"
                  : isDarkMode
                  ? "text-slate-300 hover:text-white hover:bg-white/5 border border-transparent"
                  : "text-slate-700 hover:text-[#0a66ff] hover:bg-slate-100/80 border border-transparent"
              }`}
            >
              <Icon className="w-3.5 h-3.5 shrink-0 text-cyan-400" strokeWidth={isActive ? 2.2 : 1.8} />
              <span>{tab.label}</span>
              {isActive && (
                <span
                  className={`absolute -bottom-1 left-1/2 -translate-x-1/2 w-5 h-0.5 rounded-full ${
                    isDarkMode ? "bg-[#00e5ff] shadow-[0_0_8px_#00e5ff]" : "bg-[#0a66ff]"
                  }`}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* 3. Right Status & Quick Utilities */}
      <div className="jarvis-card flex items-center gap-2.5 px-3 h-full shrink-0">
        {/* Dark / Light Mode Toggle */}
        <button
          onClick={onToggleTheme}
          className={`p-1.5 rounded-lg transition-all cursor-pointer ${
            isDarkMode
              ? "bg-cyan-500/10 text-[#00e5ff] hover:bg-cyan-500/20 border border-cyan-500/30 shadow-[0_0_12px_rgba(0,229,255,0.2)]"
              : "bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-300"
          }`}
          title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {isDarkMode ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>

        {/* Time / Date */}
        <div className="text-right border-r border-slate-200/40 dark:border-slate-700/50 pr-2.5" suppressHydrationWarning>
          <div
            className={`font-mono text-xs font-bold leading-none ${
              isDarkMode ? "text-slate-100" : "text-[#082863]"
            }`}
            suppressHydrationWarning
          >
            {timeStr}
          </div>
          <div className="font-mono text-[9px] font-medium text-slate-400 mt-0.5 tracking-wider" suppressHydrationWarning>
            {dateStr}
          </div>
        </div>

        {/* Location Selector */}
        <div className="flex items-center gap-1 font-mono text-xs font-bold text-[#0a66ff] dark:text-[#00e5ff] border-r border-slate-200/40 dark:border-slate-700/50 pr-2.5 cursor-pointer hover:opacity-80 transition-opacity">
          <Globe2 className="w-3.5 h-3.5" strokeWidth={2} />
          <span>Dubai, UAE</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </div>

        {/* Action Icons */}
        <button
          onClick={onOpenSearch}
          className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
            isDarkMode ? "text-slate-300 hover:text-[#00e5ff] hover:bg-white/5" : "text-slate-700 hover:text-[#0a66ff] hover:bg-blue-50"
          }`}
          title="Search incident registry & telemetry"
        >
          <Search className="w-4 h-4" strokeWidth={2} />
        </button>

        <div className="relative">
          <button
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDarkMode ? "text-slate-300 hover:text-[#00e5ff] hover:bg-white/5" : "text-slate-700 hover:text-[#0a66ff] hover:bg-blue-50"
            }`}
            title="3 Active Incidents Managed by Zaki"
          >
            <Bell className="w-4 h-4" strokeWidth={2} />
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-white text-[9px] font-black flex items-center justify-center">
              3
            </span>
          </button>
        </div>

        {/* AI Chat & Incident Dialogue Button */}
        <button
          onClick={onOpenChat}
          className={`p-1.5 rounded-lg transition-colors cursor-pointer relative ${
            isDarkMode ? "text-slate-300 hover:text-[#00e5ff] hover:bg-white/5" : "text-slate-700 hover:text-[#0a66ff] hover:bg-blue-50"
          }`}
          title="Open Zaki AI Chat & Dialogue"
          aria-label="Open Zaki AI Chat & Dialogue"
        >
          <MessageSquare className="w-4 h-4" strokeWidth={2} />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff] animate-pulse" />
        </button>

        {/* Short CKG Brain Access Link */}
        <Link
          href="/ckg"
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-mono text-[10.5px] font-bold uppercase tracking-wider border transition-all cursor-pointer ${
            isDarkMode
              ? "bg-cyan-500/15 text-[#00e5ff] border-cyan-400/40 hover:bg-cyan-500/25 shadow-[0_0_12px_rgba(0,229,255,0.25)]"
              : "bg-blue-50 text-[#0a66ff] border-blue-200 hover:bg-blue-100"
          }`}
          title="Access gbrain Causal Knowledge Graph (CKG)"
        >
          <Brain className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>CKG</span>
        </Link>

        {/* HUD Parameters & Control Panel Button */}
        <button
          onClick={onOpenSettings}
          className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
            isDarkMode ? "text-slate-300 hover:text-[#00e5ff] hover:bg-white/5" : "text-slate-700 hover:text-[#0a66ff] hover:bg-blue-50"
          }`}
          title="HUD Parameters & Control Panel"
          aria-label="HUD Parameters & Control Panel"
        >
          <Settings className="w-4 h-4" strokeWidth={2} />
        </button>

        {/* Fullscreen Expand / Exit Button */}
        <button
          onClick={toggleFullscreen}
          className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
            isDarkMode ? "text-slate-300 hover:text-[#00e5ff] hover:bg-white/5" : "text-slate-700 hover:text-[#0a66ff] hover:bg-blue-50"
          }`}
          title={isFullscreen ? "Exit Fullscreen (Esc)" : "Expand to Fullscreen (Immersive Mode)"}
          aria-label={isFullscreen ? "Exit Fullscreen" : "Expand to Fullscreen"}
        >
          {isFullscreen ? (
            <Minimize2 className="w-4 h-4 text-cyan-400" strokeWidth={2} />
          ) : (
            <Maximize2 className="w-4 h-4" strokeWidth={2} />
          )}
        </button>

        <div
          className={`p-1 rounded-full border cursor-pointer hover:ring-2 transition-all ${
            isDarkMode
              ? "bg-slate-800 text-slate-200 border-cyan-500/30 hover:ring-cyan-400"
              : "bg-blue-50 text-[#082863] border-blue-200/60 hover:ring-blue-300"
          }`}
        >
          <UserCircle className="w-5 h-5" strokeWidth={1.8} />
        </div>
      </div>
    </header>
  );
}
