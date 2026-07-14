"use client";

import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { Suspense, useState, useEffect } from "react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

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

  return (
    <div className="relative min-h-screen">
      <Suspense fallback={<div className="w-[240px] shrink-0" />}>
        <Sidebar isCollapsed={isCollapsed} onToggleCollapse={handleToggleCollapse} />
      </Suspense>
      <div className={`transition-all duration-300 h-screen flex flex-col ${isCollapsed ? "pl-[104px]" : "pl-[272px]"} pr-6`}>
        <Topbar />
        <main className="mt-2 flex-1 min-h-0 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
