"use client";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { Suspense, useState, useEffect } from "react";
import { usePathname } from "next/navigation";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isJarvis = pathname === "/jarvis";
  const isSimulator = pathname?.startsWith("/simulator");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Track browser fullscreen state
  useEffect(() => {
    const onFsChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  // Sync state with localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("sidebar_collapsed");
    if (stored === "true") {
      setIsCollapsed(true);
    }
  }, []);

  const handleToggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar_collapsed", String(next));
      return next;
    });
  };

  const hideSidebar = isFullscreen;

  return (
    <div className="relative min-h-screen">
      {!hideSidebar && (
        <Suspense fallback={<div className="w-[240px] shrink-0" />}>
          <Sidebar isCollapsed={isCollapsed} onToggleCollapse={handleToggleCollapse} />
        </Suspense>
      )}
      <div
        className={`transition-all duration-300 h-screen flex flex-col ${
          hideSidebar
            ? "pl-0 pr-0 pt-0 pb-0"
            : isCollapsed
            ? "pl-[96px]"
            : "pl-[264px]"
        } ${!hideSidebar && isJarvis ? "pr-3 pt-2 pb-2" : !hideSidebar ? "pr-4" : ""}`}
      >
        {!isJarvis && !isSimulator && !hideSidebar && <Topbar />}
        <main className={`${isJarvis || isSimulator ? "" : "mt-2"} flex-1 min-h-0 overflow-hidden`}>
          {children}
        </main>
      </div>
    </div>
  );
}
