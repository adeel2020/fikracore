"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Bell, Search, User, Maximize2, Minimize2 } from "lucide-react";
import { getNavItem } from "@/lib/navigation";
import { Button } from "@/components/ui/button";

const iconStroke = { strokeWidth: 1.5 } as const;

export function Topbar() {
  const pathname = usePathname();
  const current = getNavItem(pathname);

  // Global Fullscreen State
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(err => {
        console.error("Error attempting to enable fullscreen:", err);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().then(() => {
          setIsFullscreen(false);
        });
      }
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between px-2">
      <div>
        <h1 className="text-lg font-semibold text-white">
          {current?.label ?? "Data Storyteller"}
        </h1>
        <p className="text-xs text-neutral-400">
          {current?.description ?? "Enterprise data intelligence"}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 backdrop-blur-xl md:flex">
          <Search className="h-4 w-4 text-neutral-500" {...iconStroke} />
          <input
            type="search"
            placeholder="Search modules..."
            className="w-48 bg-transparent text-sm text-white placeholder:text-neutral-500 focus:outline-none"
          />
        </div>
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-4 w-4" {...iconStroke} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleFullscreen}
          aria-label={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
          className={isFullscreen ? "text-cyan-400 border border-cyan-500/30 bg-cyan-500/10 shadow-[0_0_12px_rgba(0,229,255,0.25)]" : ""}
        >
          {isFullscreen ? (
            <Minimize2 className="h-4 w-4" {...iconStroke} />
          ) : (
            <Maximize2 className="h-4 w-4" {...iconStroke} />
          )}
        </Button>
        <Button variant="ghost" size="icon" aria-label="Profile">
          <User className="h-4 w-4" {...iconStroke} />
        </Button>
      </div>
    </header>
  );
}
