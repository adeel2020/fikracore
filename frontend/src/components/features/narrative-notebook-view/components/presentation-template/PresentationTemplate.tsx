"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import { 
  Play, 
  Square, 
  Volume2, 
  ChevronRight, 
  ChevronLeft, 
  Sliders, 
  X,
  Bold,
  Italic,
  Underline,
  Heading1,
  Heading2,
  List,
  Code,
  Maximize2,
  Minimize2,
  Sparkles
} from "lucide-react";
import { GlassCardContext } from "@/components/ui/glass-card";
import TalkingAvatar, { TalkingAvatarHandle, PERSONAS, Persona, SpeakAudioData } from "./TalkingAvatar";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { AvatarProvider, useAvatar } from "./AvatarContext";
import { AvatarControlPanel } from "./AvatarControlPanel";


const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

import { EarlyWarningDiagnostics } from "../../../complaint-dashboard-view/components/EarlyWarningDiagnostics";
import { TopReassignmentsQueue, TopRejectionReason, PercentageNocTickets } from "../../../complaint-dashboard-view/components/CoreOperationalMetrics";
import { TotalTicketDistribution, TopComplaintCategories, AvgQueueTime, SloMeterBar } from "../../../complaint-dashboard-view/components/QueuePerformanceAnalytics";
import { TopRoamingComplaints } from "../../../complaint-dashboard-view/components/SpatialTrafficTrends";
import { OperationalHealthInfographic } from "../../../complaint-dashboard-view/components/OperationalHealthInfographic";

import { 
  StepFlowerProcess, 
  ChevronOptionsList, 
  LeafStepList, 
  StatsRingMeters, 
  ArrowBarList, 
  TimelineStems 
} from "./PrebuiltInfographics";

interface LayoutTemplate {
  id: string;
  name: string;
  shortName: string;
  icon: string;
}

const LAYOUT_TEMPLATES: LayoutTemplate[] = [
  { id: "split-panel", name: "Split Screen (Classic)", shortName: "Split", icon: "🌓" },
  { id: "hero-banner", name: "Hero Banner (Top)", shortName: "Banner", icon: "🥞" },
  { id: "right-focus", name: "Right Narrative (Focus)", shortName: "Right", icon: "🌗" },
  { id: "immersive-story", name: "Immersive Centered", shortName: "Center", icon: "🎯" },
  { id: "staggered-flow", name: "Horizontal Flow", shortName: "Flow", icon: "📑" }
];

interface PresentationSlide {
  id: string;
  title: string;
  subtitle: string;
  narrative: string;
  icon: string;
  ComponentA?: React.FC<any>;
  ComponentAWidth?: string;
  ComponentB?: React.FC<any>;
  ComponentBWidth?: string;
}

const PRESENTATION_SLIDES: PresentationSlide[] = [
  {
    id: "slide-1-executive",
    title: "Executive Diagnostics & Early Warnings",
    subtitle: "Global View of Anomalous Telemetry",
    icon: "🌐",
    narrative: "Cognitive Operations & Customer Center: Over the past 4 hours, our AI-driven telemetry sweeps have isolated several multi-variant incidents across the core service journeys. The Early Warning Dashboard highlights impending friction points before they escalate into critical SLA breaches. Concurrently, NOC ticket distribution indicates a heavy volume shift towards core infrastructural complaints, demanding immediate strategic containment.",
    ComponentA: EarlyWarningDiagnostics,
    ComponentAWidth: "400px", // Originally 1/3 grid
    ComponentB: PercentageNocTickets,
    ComponentBWidth: "280px", // Originally 2/12 grid
  },
  {
    id: "slide-2-queue",
    title: "Ingress & Ticket Distribution",
    subtitle: "Complaint Volumes and Category Breakdown",
    icon: "📊",
    narrative: "An analysis of incoming trouble tickets over the last 30 days reveals distinct operational bottlenecks. The Total Ticket Distribution showcases a steady ingress, while the Top Complaint Categories identify primary service disruptions affecting end-users. By isolating these friction categories, engineering teams can prioritize root-cause resolutions over symptomatic patching.",
    ComponentA: TotalTicketDistribution,
    ComponentAWidth: "400px", // Originally 1/3 grid
    ComponentB: TopComplaintCategories,
    ComponentBWidth: "280px", // Originally 2/12 grid
  },
  {
    id: "slide-3-reassignments",
    title: "Cross-Domain Reassignment Topology",
    subtitle: "Tracking Ticket Routing and Structural Friction",
    icon: "🔄",
    narrative: "When tickets bounce between queues, mean-time-to-resolve (MTTR) degrades significantly. The Top Reassignments analysis traces the precise structural friction across domains. We observed a high volume of payload transfers between tier-1 support and specialized core engineering. By executing an unsupervised semantic clustering pass, we identified misrouted ticket categories, allowing us to enforce stricter operational boundaries and routing rules.",
    ComponentA: TopReassignmentsQueue,
    ComponentAWidth: "280px", // Originally 2/12 grid
    ComponentB: AvgQueueTime,
    ComponentBWidth: "400px", // Originally 1/3 grid
  },
  {
    id: "slide-4-rejections",
    title: "Rejection Signatures & End-User Friction",
    subtitle: "Evaluating Root-Layer Operational Boundaries",
    icon: "🛡️",
    narrative: "Ticket rejections often highlight a misalignment between customer expectations and NOC operational capabilities. The Top Rejection Reasons chart isolates where support teams are pushing back due to insufficient telemetry or out-of-scope requests. By addressing these specific rejection vectors, the Customer Center can refine their initial troubleshooting scripts and improve first-touch resolution rates.",
    ComponentA: TopRejectionReason,
    ComponentAWidth: "280px", // Originally 2/12 grid
    ComponentB: SloMeterBar,
    ComponentBWidth: "200px", // Originally 1/12 grid
  },
  {
    id: "slide-5-spatial",
    title: "Spatial Anomalies & Roaming Impact",
    subtitle: "Geographical Distribution of Service Friction",
    icon: "🗺️",
    narrative: "The spatial separation of the data cloud confirms that while incoming telemetry was highly fragmented across multiple edge user-plane ingress points, the core failure signatures converge precisely on specific roaming zones. The Top Roaming Complaints index pinpoints geographical areas experiencing the highest service degradation. Ownership has been routed directly to the identified domain stakeholders for final architectural mitigation.",
    ComponentA: TopRoamingComplaints,
    ComponentAWidth: "350px", // Originally 3/12 grid
  }
];

interface PresentationTemplateProps {
  isLight: boolean;
  isPlaying: boolean;
  onPlay: (id: string, text: string, gender?: "male" | "female") => void;
  onStop: () => void;
  isEditing: boolean;
}

export function DraggableComponent({ 
  children, 
  defaultWidth, 
  id,
  onRemove,
  defaultX = 0,
  defaultY = 0,
  isEditing,
  isLight
}: { 
  children: React.ReactNode; 
  defaultWidth?: string; 
  id: string;
  onRemove?: () => void;
  defaultX?: number;
  defaultY?: number;
  isEditing: boolean;
  isLight?: boolean;
}) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const position = React.useRef({ x: defaultX, y: defaultY });
  const scale = React.useRef({ x: 1, y: 1 });

  // Load from localStorage on mount
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(`draggable_${id}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.position) position.current = parsed.position;
        if (parsed.scale) scale.current = parsed.scale;
      } else {
        // Use default offsets
        position.current = { x: defaultX, y: defaultY };
      }
      
      if (containerRef.current) {
        containerRef.current.style.transform = `translate(${position.current.x}px, ${position.current.y}px) scale(${scale.current.x}, ${scale.current.y})`;
      }
    } catch (e) {}
  }, [id, defaultX, defaultY]);

  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);

  // Global window pointerup/cancel listener to guarantee cursor release
  React.useEffect(() => {
    if (!isDragging && !isResizing) return;
    const handleGlobalUp = () => {
      setIsDragging(false);
      setIsResizing(false);
    };
    window.addEventListener("pointerup", handleGlobalUp);
    window.addEventListener("pointercancel", handleGlobalUp);
    return () => {
      window.removeEventListener("pointerup", handleGlobalUp);
      window.removeEventListener("pointercancel", handleGlobalUp);
    };
  }, [isDragging, isResizing]);
  
  const dragStart = React.useRef({ startX: 0, startY: 0, initialPosX: 0, initialPosY: 0 });
  const resizeStart = React.useRef({ scale: { x: 1, y: 1 }, x: 0, y: 0 });

  const handlePointerDown = (e: React.PointerEvent) => {
    if (!isEditing) return; // Disable dragging and resizing if not editing
    const target = e.target as HTMLElement;
    
    if (target.closest('[data-action="resize"]')) {
      e.stopPropagation();
      e.currentTarget.setPointerCapture(e.pointerId);
      setIsResizing(true);
      resizeStart.current = { scale: { ...scale.current }, x: e.clientX, y: e.clientY };
      return;
    }

    if (target.closest('[data-action="drag"]')) {
      e.stopPropagation();
      e.currentTarget.setPointerCapture(e.pointerId);
      setIsDragging(true);
      dragStart.current = { startX: e.clientX, startY: e.clientY, initialPosX: position.current.x, initialPosY: position.current.y };
      return;
    }
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isEditing) return;
    if (isResizing) {
      const deltaX = e.clientX - resizeStart.current.x;
      const deltaY = e.clientY - resizeStart.current.y;
      
      const newScaleX = Math.max(0.4, Math.min(2.5, resizeStart.current.scale.x + (deltaX / 300)));
      const newScaleY = Math.max(0.4, Math.min(2.5, resizeStart.current.scale.y + (deltaY / 300)));
      
      scale.current = { x: newScaleX, y: newScaleY };
      if (containerRef.current) {
        containerRef.current.style.transform = `translate(${position.current.x}px, ${position.current.y}px) scale(${scale.current.x}, ${scale.current.y})`;
      }
      return;
    }

    if (isDragging) {
      const deltaX = e.clientX - dragStart.current.startX;
      const deltaY = e.clientY - dragStart.current.startY;
      
      position.current = {
        x: dragStart.current.initialPosX + deltaX,
        y: dragStart.current.initialPosY + deltaY
      };
      
      if (containerRef.current) {
        containerRef.current.style.transform = `translate(${position.current.x}px, ${position.current.y}px) scale(${scale.current.x}, ${scale.current.y})`;
      }
    }
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!isEditing) return;

    // Explicitly release pointer capture to prevent cursor stickiness
    try {
      if (e.currentTarget.hasPointerCapture(e.pointerId)) {
        e.currentTarget.releasePointerCapture(e.pointerId);
      }
    } catch (err) {}

    if (isResizing) setIsResizing(false);
    if (isDragging) setIsDragging(false);
    
    try {
      localStorage.setItem(`draggable_${id}`, JSON.stringify({ position: position.current, scale: scale.current }));
    } catch (e) {}
  };

  return (
    <div
      ref={containerRef}
      style={{ 
        width: defaultWidth || 'auto',
        transformOrigin: 'top left',
      }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onDragStart={(e) => e.preventDefault()} // Prevent browser native drag-and-drop hijacking
      className={cn(
        "absolute top-0 left-0 will-change-transform pointer-events-auto select-none",
        (isDragging || isResizing) ? "transition-none" : "transition-all duration-300",
        isEditing 
          ? isLight 
            ? "rounded-xl bg-white/90 border border-slate-300 shadow-xl hover:ring-1 hover:ring-cyan-500/30 text-slate-800"
            : "rounded-xl bg-black/40 border border-white/5 shadow-2xl hover:ring-1 hover:ring-cyan-500/30" 
          : "bg-transparent border-none shadow-none",
        isDragging ? "z-50 ring-2 ring-cyan-500/50" : "z-10",
        isResizing ? "z-50 ring-2 ring-purple-500/50" : "",
        "animate-in fade-in slide-in-from-bottom-4 duration-700"
      )}
    >
      {/* Top Drag Bar */}
      {isEditing && (
        <div 
          data-action="drag"
          className="w-full h-8 bg-cyan-500/5 hover:bg-cyan-500/10 border-b border-white/5 rounded-t-xl cursor-grab flex items-center justify-between px-3 transition-colors relative"
          title="Drag to adjust position"
        >
          <div className="w-4" /> {/* Spacer */}
          <div className="w-12 h-1 rounded-full bg-white/20 pointer-events-none" />
          
          {onRemove ? (
            <button 
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-white/40 hover:text-rose-400 hover:bg-rose-500/20 rounded p-1 transition-colors cursor-pointer flex items-center justify-center"
              title="Remove component from slide"
            >
              <span className="text-[10px] leading-none">✕</span>
            </button>
          ) : (
            <div className="w-4" />
          )}
        </div>
      )}

      {/* Resize Indicator Handle */}
      {isEditing && (
        <div 
          data-action="resize"
          className="absolute -bottom-2 -right-2 w-6 h-6 rounded-full bg-purple-500/20 backdrop-blur-sm border border-purple-500/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity z-20 cursor-nwse-resize" 
          title="Drag to resize (Length & Width)"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-purple-400 pointer-events-none" />
        </div>
      )}

      <div className={cn(isEditing ? "p-2" : "p-0", isDragging ? "pointer-events-none" : "")}>
        <GlassCardContext.Provider value={{ isEditing, isLight }}>
          {children}
        </GlassCardContext.Provider>
      </div>
    </div>
  );
}

const COMPONENT_REGISTRY: Record<string, { name: string; icon: string; component: React.FC<any>; defaultWidth: string }> = {
  "EarlyWarningDiagnostics": { name: "Early Warning Diagnostics", icon: "⚠️", component: EarlyWarningDiagnostics, defaultWidth: "400px" },
  "PercentageNocTickets": { name: "Percentage NOC Tickets", icon: "🎫", component: PercentageNocTickets, defaultWidth: "280px" },
  "TotalTicketDistribution": { name: "Total Ticket Distribution", icon: "📈", component: TotalTicketDistribution, defaultWidth: "400px" },
  "TopComplaintCategories": { name: "Top Complaint Categories", icon: "🗂️", component: TopComplaintCategories, defaultWidth: "280px" },
  "TopReassignmentsQueue": { name: "Top Reassignments Queue", icon: "🔄", component: TopReassignmentsQueue, defaultWidth: "280px" },
  "AvgQueueTime": { name: "Average Queue Time", icon: "⏱️", component: AvgQueueTime, defaultWidth: "400px" },
  "TopRejectionReason": { name: "Top Rejection Reasons", icon: "🚫", component: TopRejectionReason, defaultWidth: "280px" },
  "SloMeterBar": { name: "SLO Meter Bar", icon: "📊", component: SloMeterBar, defaultWidth: "200px" },
  "TopRoamingComplaints": { name: "Top Roaming Complaints", icon: "🗺️", component: TopRoamingComplaints, defaultWidth: "350px" },
  "OperationalHealth": { name: "System Health & Core Signals", icon: "⚡", component: OperationalHealthInfographic, defaultWidth: "410px" },
  "StepFlowerProcess": { name: "Step Flower Process", icon: "🌸", component: StepFlowerProcess, defaultWidth: "410px" },
  "ChevronOptionsList": { name: "Chevron Action Options", icon: "🏷️", component: ChevronOptionsList, defaultWidth: "410px" },
  "LeafStepList": { name: "Leaf Step Diagnostics", icon: "🍃", component: LeafStepList, defaultWidth: "410px" },
  "StatsRingMeters": { name: "Radial Stats Rings", icon: "⭕", component: StatsRingMeters, defaultWidth: "410px" },
  "ArrowBarList": { name: "Arrow Bar Comparison", icon: "🏹", component: ArrowBarList, defaultWidth: "410px" },
  "TimelineStems": { name: "Timeline Stems", icon: "📅", component: TimelineStems, defaultWidth: "410px" }
};

interface SlideTheme {
  id: string;
  name: string;
  className: string;
  headerBorderClass: string;
  subtitleClass: string;
  buttonClass: string;
  narrativeCardClass: string;
  narrativeTitleClass: string;
  narrativeTextClass: string;
  placeholderClass: string;
  sidebarClass: string;
  sidebarHeaderBorderClass: string;
  sidebarBadgeClass: string;
  sidebarResetButtonClass: string;
  sidebarItemHoverClass: string;
  sidebarStatusDotClass: string;
  sidebarItemTextClass: string;
  footerClass: string;
  footerButtonClass: string;
  footerIndicatorClass: string;
  swatchColors: string[];
  accentColor: string;
}

const SLIDE_THEMES: SlideTheme[] = [
  {
    id: "midnight-slate",
    name: "Midnight Slate",
    className: "bg-[#090D16]/95 border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.6)]",
    headerBorderClass: "border-white/10",
    subtitleClass: "text-neutral-400",
    buttonClass: "border-white/10 text-neutral-300 bg-white/5 hover:bg-white/10",
    narrativeCardClass: "bg-black/40 border-white/5 shadow-inner",
    narrativeTitleClass: "text-neutral-300",
    narrativeTextClass: "text-neutral-300",
    placeholderClass: "border-white/10 text-neutral-500",
    sidebarClass: "bg-[#0A0A0A]/95 border-white/10 shadow-[-8px_0_32px_rgba(0,0,0,0.5)]",
    sidebarHeaderBorderClass: "border-white/10",
    sidebarBadgeClass: "bg-white/5 text-neutral-500",
    sidebarResetButtonClass: "border-white/10 text-neutral-400 hover:bg-white/5 hover:text-white",
    sidebarItemHoverClass: "hover:bg-white/[0.02]",
    sidebarStatusDotClass: "bg-white/15",
    sidebarItemTextClass: "text-neutral-100 text-neutral-400 group-hover:text-neutral-300",
    footerClass: "bg-black/60 border-white/5",
    footerButtonClass: "text-white hover:bg-white/10",
    footerIndicatorClass: "w-6 bg-white/20",
    swatchColors: ["#090D16", "#00E5FF"],
    accentColor: "#00E5FF"
  },
  {
    id: "light-slate",
    name: "Light Slate",
    className: "bg-white/95 border-slate-200 shadow-[0_8px_32px_rgba(0,0,0,0.08)]",
    headerBorderClass: "border-slate-200",
    subtitleClass: "text-slate-500",
    buttonClass: "border-slate-200 text-slate-600 bg-slate-100 hover:bg-slate-200",
    narrativeCardClass: "bg-slate-50/80 border-slate-200 shadow-inner",
    narrativeTitleClass: "text-slate-600",
    narrativeTextClass: "text-slate-700",
    placeholderClass: "border-slate-300 text-slate-400",
    sidebarClass: "bg-white/95 border-slate-200 shadow-[-8px_0_32px_rgba(0,0,0,0.05)]",
    sidebarHeaderBorderClass: "border-slate-200",
    sidebarBadgeClass: "bg-slate-100 text-slate-500",
    sidebarResetButtonClass: "border-slate-200 text-slate-500 hover:bg-slate-100",
    sidebarItemHoverClass: "hover:bg-slate-100/50",
    sidebarStatusDotClass: "bg-slate-300",
    sidebarItemTextClass: "text-slate-900 text-slate-500",
    footerClass: "bg-slate-50 border-slate-200",
    footerButtonClass: "text-slate-700 hover:bg-slate-200",
    footerIndicatorClass: "w-6 bg-slate-300",
    swatchColors: ["#FFFFFF", "#0EA5E9"],
    accentColor: "#0EA5E9"
  },
  {
    id: "neon-cyberpunk",
    name: "Neon Cyberpunk",
    className: "bg-[#0B0314]/95 border-fuchsia-500/25 shadow-[0_0_24px_rgba(217,70,239,0.15)]",
    headerBorderClass: "border-fuchsia-500/15",
    subtitleClass: "text-fuchsia-300/70",
    buttonClass: "border-fuchsia-500/20 text-fuchsia-300 bg-fuchsia-500/5 hover:bg-fuchsia-500/15",
    narrativeCardClass: "bg-[#180424]/60 border-fuchsia-500/10 shadow-[inset_0_1px_6px_rgba(217,70,239,0.1)]",
    narrativeTitleClass: "text-fuchsia-400",
    narrativeTextClass: "text-purple-100",
    placeholderClass: "border-fuchsia-500/20 text-fuchsia-500/50",
    sidebarClass: "bg-[#0B0314]/95 border-fuchsia-500/25 shadow-[-8px_0_32px_rgba(217,70,239,0.15)]",
    sidebarHeaderBorderClass: "border-fuchsia-500/15",
    sidebarBadgeClass: "bg-fuchsia-500/10 text-fuchsia-400",
    sidebarResetButtonClass: "border-fuchsia-500/20 text-fuchsia-400 hover:bg-fuchsia-500/10",
    sidebarItemHoverClass: "hover:bg-fuchsia-500/[0.03]",
    sidebarStatusDotClass: "bg-fuchsia-950",
    sidebarItemTextClass: "text-fuchsia-300 text-neutral-400 group-hover:text-fuchsia-300/80",
    footerClass: "bg-[#12021B]/80 border-fuchsia-500/15",
    footerButtonClass: "text-fuchsia-200 hover:bg-fuchsia-500/10",
    footerIndicatorClass: "w-6 bg-fuchsia-950",
    swatchColors: ["#0B0314", "#D946EF"],
    accentColor: "#D946EF"
  },
  {
    id: "sunset-warmth",
    name: "Sunset Warmth",
    className: "bg-[#1A0C00]/95 border-amber-500/25 shadow-[0_0_24px_rgba(245,158,11,0.15)]",
    headerBorderClass: "border-amber-500/15",
    subtitleClass: "text-amber-200/60",
    buttonClass: "border-amber-500/20 text-amber-300 bg-amber-500/5 hover:bg-amber-500/15",
    narrativeCardClass: "bg-[#2C1400]/60 border-amber-500/10 shadow-[inset_0_1px_6px_rgba(245,158,11,0.1)]",
    narrativeTitleClass: "text-amber-400",
    narrativeTextClass: "text-amber-100",
    placeholderClass: "border-amber-500/20 text-amber-500/50",
    sidebarClass: "bg-[#1A0C00]/95 border-amber-500/25 shadow-[-8px_0_32px_rgba(245,158,11,0.15)]",
    sidebarHeaderBorderClass: "border-amber-500/15",
    sidebarBadgeClass: "bg-amber-500/10 text-amber-400",
    sidebarResetButtonClass: "border-amber-500/20 text-amber-400 hover:bg-amber-500/10",
    sidebarItemHoverClass: "hover:bg-amber-500/[0.03]",
    sidebarStatusDotClass: "bg-amber-950",
    sidebarItemTextClass: "text-amber-300 text-neutral-400 group-hover:text-amber-300/80",
    footerClass: "bg-[#1F0E00]/80 border-amber-500/15",
    footerButtonClass: "text-amber-200 hover:bg-amber-500/10",
    footerIndicatorClass: "w-6 bg-amber-950",
    swatchColors: ["#1A0C00", "#F59E0B"],
    accentColor: "#F59E0B"
  },
  {
    id: "forest-teal",
    name: "Forest Teal",
    className: "bg-[#021A12]/95 border-emerald-500/25 shadow-[0_0_24px_rgba(52,211,153,0.15)]",
    headerBorderClass: "border-emerald-500/15",
    subtitleClass: "text-emerald-200/60",
    buttonClass: "border-emerald-500/20 text-emerald-300 bg-emerald-500/5 hover:bg-emerald-500/15",
    narrativeCardClass: "bg-[#04281C]/60 border-emerald-500/10 shadow-[inset_0_1px_6px_rgba(52,211,153,0.1)]",
    narrativeTitleClass: "text-emerald-400",
    narrativeTextClass: "text-emerald-100",
    placeholderClass: "border-emerald-500/20 text-emerald-500/50",
    sidebarClass: "bg-[#021A12]/95 border-emerald-500/25 shadow-[-8px_0_32px_rgba(52,211,153,0.15)]",
    sidebarHeaderBorderClass: "border-emerald-500/15",
    sidebarBadgeClass: "bg-emerald-500/10 text-emerald-400",
    sidebarResetButtonClass: "border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10",
    sidebarItemHoverClass: "hover:bg-emerald-500/[0.03]",
    sidebarStatusDotClass: "bg-emerald-950",
    sidebarItemTextClass: "text-emerald-300 text-neutral-400 group-hover:text-emerald-300/80",
    footerClass: "bg-[#031E15]/80 border-emerald-500/15",
    footerButtonClass: "text-emerald-200 hover:bg-emerald-500/10",
    footerIndicatorClass: "w-6 bg-emerald-950",
    swatchColors: ["#021A12", "#10B981"],
    accentColor: "#10B981"
  }
];

function PresentationBody({ isLight, isPlaying, onPlay, onStop, isEditing }: PresentationTemplateProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const [avatarPos, setAvatarPos] = useState({ x: 0, y: 0 });
  const avatarDragStart = React.useRef({ x: 0, y: 0, posX: 0, posY: 0, time: 0 });
  const [isAvatarDragging, setIsAvatarDragging] = useState(false);
  const isAvatarDraggingRef = React.useRef(false);

  const avatarRef = React.useRef<TalkingAvatarHandle>(null);
  const { registerAvatar, isPlaying: globalIsPlaying, isChatBotOpen: globalIsChatOpen, persona: globalPersona, setIsPlaying: setGlobalIsPlaying, gender: globalGender, setGender: setGlobalGender, isMuted } = useAvatar();

  const [isAvatarSpeaking, setIsAvatarSpeaking] = useState(false);
  const isAvatarSpeakingRef = React.useRef(false);
  const isPlayingRef = React.useRef(isPlaying);
  const activeThemeRef = React.useRef<any>(null);

  const [avatarGender, setAvatarGender] = useState<"male" | "female">(() => {
    try {
      const saved = localStorage.getItem("presentation_avatar_gender");
      if (saved === "male" || saved === "female") return saved;
    } catch (e) {}
    return "male";
  });
  const [currentPersona, setCurrentPersona] = useState<Persona>("friendly");
  const [isPersonaMenuOpen, setIsPersonaMenuOpen] = useState(false);
  const personaMenuRef = React.useRef<HTMLDivElement>(null);
  const [avatarScale, setAvatarScale] = useState(1);
  const [waitingForResponse, setWaitingForResponse] = useState(false);

  React.useEffect(() => {
    registerAvatar(avatarRef.current);
    return () => registerAvatar(null);
  }, [avatarRef.current, registerAvatar]);

  React.useEffect(() => {
    setIsAvatarSpeaking(globalIsPlaying);
  }, [globalIsPlaying]);

  React.useEffect(() => {
    setIsChatOpen(globalIsChatOpen);
  }, [globalIsChatOpen]);

  React.useEffect(() => {
    setCurrentPersona(globalPersona);
  }, [globalPersona]);

  React.useEffect(() => {
    setGlobalIsPlaying(isAvatarSpeaking);
  }, [isAvatarSpeaking, setGlobalIsPlaying]);

  React.useEffect(() => {
    setAvatarGender(globalGender);
  }, [globalGender]);

  React.useEffect(() => {
    setGlobalGender(avatarGender);
  }, [avatarGender, setGlobalGender]);
  const personaKeys = React.useMemo(() => Object.keys(PERSONAS), []);

  // Close persona menu on outside click
  React.useEffect(() => {
    if (!isPersonaMenuOpen) return;
    const onPointerDown = (e: PointerEvent) => {
      if (personaMenuRef.current && !personaMenuRef.current.contains(e.target as Node)) {
        setIsPersonaMenuOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown, true);
    return () => document.removeEventListener("pointerdown", onPointerDown, true);
  }, [isPersonaMenuOpen]);

  const [avatarState, setAvatarState] = useState<"idle" | "thinking" | "speaking">("idle");
  const avatarStateRef = React.useRef(avatarState);
  React.useEffect(() => {
    avatarStateRef.current = avatarState;
  }, [avatarState]);

  // Sync persona changes to the avatar ref dynamically
  React.useEffect(() => {
    avatarRef.current?.setPersona?.(currentPersona);
  }, [currentPersona]);

  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ sender: "user" | "avatar"; text: string }>>([
    { sender: "avatar", text: "Hello! I am your AI operational co-pilot. I have scanned the telemetry data for this slide and can answer any questions. What would you like to know?" }
  ]);
  const [chatInput, setChatInput] = useState("");

  React.useEffect(() => {
    if (isAvatarSpeaking) {
      setAvatarState("speaking");
    } else {
      setAvatarState(prev => prev === "speaking" ? "idle" : prev);
    }
  }, [isAvatarSpeaking]);

  const prevAvatarSpeakingRef = React.useRef(false);
  React.useEffect(() => {
    isPlayingRef.current = isAvatarSpeaking;
    isAvatarSpeakingRef.current = isAvatarSpeaking;
    prevAvatarSpeakingRef.current = isAvatarSpeaking;
  }, [isAvatarSpeaking]);

  React.useEffect(() => {
    if (!isAvatarDragging) return;
    const handleGlobalUp = () => {
      setIsAvatarDragging(false);
      isAvatarDraggingRef.current = false;
    };
    window.addEventListener("pointerup", handleGlobalUp);
    window.addEventListener("pointercancel", handleGlobalUp);
    return () => {
      window.removeEventListener("pointerup", handleGlobalUp);
      window.removeEventListener("pointercancel", handleGlobalUp);
    };
  }, [isAvatarDragging]);

  const handleAvatarPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    avatarDragStart.current = {
      x: e.clientX,
      y: e.clientY,
      posX: avatarPos.x,
      posY: avatarPos.y,
      time: Date.now()
    };
    setIsAvatarDragging(true);
    isAvatarDraggingRef.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handleAvatarPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isAvatarDraggingRef.current) return;
    e.stopPropagation();
    const deltaX = e.clientX - avatarDragStart.current.x;
    const deltaY = e.clientY - avatarDragStart.current.y;
    setAvatarPos({
      x: avatarDragStart.current.posX + deltaX,
      y: avatarDragStart.current.posY + deltaY
    });
  };

  const handleAvatarPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isAvatarDraggingRef.current) return;
    setIsAvatarDragging(false);
    isAvatarDraggingRef.current = false;
    e.stopPropagation();
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch (err) {}
  };

  const toggleAvatarGender = () => {
    const nextGender = avatarGender === "male" ? "female" : "male";
    setAvatarGender(nextGender);
    try {
      localStorage.setItem("presentation_avatar_gender", nextGender);
    } catch (e) {}
  };

  const handleSendMessage = async (customMessage?: string) => {
    const textToSend = customMessage !== undefined ? customMessage : chatInput;
    if (!textToSend.trim()) return;

    if (customMessage === undefined) {
      setChatInput("");
    }

    setChatMessages(prev => [...prev, { sender: "user", text: textToSend }]);
    setAvatarState("thinking");

    try {
      // Build conversation history from previous messages
      const historyMessages = chatMessages.map(m => ({
        role: m.sender === "user" ? "user" as const : "assistant" as const,
        content: m.text,
      }));

      const res = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "noc-storyteller",
          messages: [...historyMessages, { role: "user", content: textToSend }],
          stream: true,
        }),
      });

      // Read SSE stream
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const decoder = new TextDecoder();
      let fullText = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === "data: [DONE]") continue;
          if (!trimmed.startsWith("data: ")) continue;
          try {
            const parsed = JSON.parse(trimmed.slice(6));
            const delta = parsed.choices?.[0]?.delta?.content;
            if (delta) fullText += delta;
          } catch {}
        }
      }

      const response = fullText.trim();
      setChatMessages(prev => [...prev, { sender: "avatar", text: response }]);
      setAvatarState("speaking");
      avatarRef.current?.speak(response);
    } catch (e) {
      console.error(e);
      const fallbackText = "I am running in local mode. Based on this slide's telemetry, I can see SLA data and queue volumes. What specific operational detail would you like to discuss?";
      setChatMessages(prev => [...prev, { sender: "avatar", text: fallbackText }]);
      setAvatarState("speaking");
      avatarRef.current?.speak(fallbackText);
    }
  };

  const [slideThemeId, setSlideThemeId] = useState<string>(() => {
    try {
      const saved = localStorage.getItem("presentation_slide_theme");
      if (saved) return saved;
    } catch (e) {}
    return isLight ? "light-slate" : "midnight-slate";
  });

  React.useEffect(() => {
    try {
      const saved = localStorage.getItem("presentation_slide_theme");
      if (!saved) {
        setSlideThemeId(isLight ? "light-slate" : "midnight-slate");
      }
    } catch (e) {}
  }, [isLight]);

  const handleThemeChange = (themeId: string) => {
    setSlideThemeId(themeId);
    try {
      localStorage.setItem("presentation_slide_theme", themeId);
    } catch (e) {}
  };

  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  const [slideComponents, setSlideComponents] = useState<Record<string, string[]>>(() => {
    try {
      const saved = localStorage.getItem("presentation_slide_components");
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    
    return {
      "slide-1-executive": ["EarlyWarningDiagnostics", "PercentageNocTickets"],
      "slide-2-queue": ["TotalTicketDistribution", "TopComplaintCategories"],
      "slide-3-reassignments": ["TopReassignmentsQueue", "AvgQueueTime"],
      "slide-4-rejections": ["TopRejectionReason", "SloMeterBar"],
      "slide-5-spatial": ["TopRoamingComplaints"]
    };
  });

  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const [resetCounter, setResetCounter] = useState(0);
  const libraryTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const resetLibraryTimer = React.useCallback(() => {
    if (libraryTimeoutRef.current) {
      clearTimeout(libraryTimeoutRef.current);
    }
    if (isLibraryOpen) {
      libraryTimeoutRef.current = setTimeout(() => {
        setIsLibraryOpen(false);
      }, 7000);
    }
  }, [isLibraryOpen]);

  React.useEffect(() => {
    if (isLibraryOpen) {
      resetLibraryTimer();
    } else {
      if (libraryTimeoutRef.current) {
        clearTimeout(libraryTimeoutRef.current);
      }
    }
    return () => {
      if (libraryTimeoutRef.current) {
        clearTimeout(libraryTimeoutRef.current);
      }
    };
  }, [isLibraryOpen, resetLibraryTimer]);

  const slide = PRESENTATION_SLIDES[currentSlide];
  const activeKeys = slideComponents[slide.id] || [];

  const handleNext = () => {
    if (currentSlide < PRESENTATION_SLIDES.length - 1) setCurrentSlide(prev => prev + 1);
  };

  const handlePrev = () => {
    if (currentSlide > 0) setCurrentSlide(prev => prev - 1);
  };

  const handleResetPositions = () => {
    const defaults: Record<string, string[]> = {
      "slide-1-executive": ["EarlyWarningDiagnostics", "PercentageNocTickets"],
      "slide-2-queue": ["TotalTicketDistribution", "TopComplaintCategories"],
      "slide-3-reassignments": ["TopReassignmentsQueue", "AvgQueueTime"],
      "slide-4-rejections": ["TopRejectionReason", "SloMeterBar"],
      "slide-5-spatial": ["TopRoamingComplaints"]
    };
    
    const defaultKeys = defaults[slide.id] || [];
    
    // Clear localStorage positions for ALL possible registry components on the current slide
    Object.keys(COMPONENT_REGISTRY).forEach(key => {
      try {
        localStorage.removeItem(`draggable_${slide.id}-${key}`);
      } catch (e) {}
    });
    
    setSlideComponents(prev => {
      const newConfig = { ...prev, [slide.id]: defaultKeys };
      try {
        localStorage.setItem("presentation_slide_components", JSON.stringify(newConfig));
      } catch (e) {}
      return newConfig;
    });

    setSlideLayouts(prev => {
      const updated = { ...prev, [slide.id]: "split-panel" };
      try {
        localStorage.setItem("presentation_slide_layouts", JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });

    setResetCounter(prev => prev + 1);
  };

  const handleToggleComponent = (key: string) => {
    resetLibraryTimer();
    setSlideComponents(prev => {
      const active = prev[slide.id] || [];
      const updated = active.includes(key)
        ? active.filter(k => k !== key)
        : [...active, key];
      
      const newConfig = { ...prev, [slide.id]: updated };
      try {
        localStorage.setItem("presentation_slide_components", JSON.stringify(newConfig));
      } catch (e) {}
      return newConfig;
    });
  };

  const handleRemoveComponent = (key: string) => {
    resetLibraryTimer();
    setSlideComponents(prev => {
      const active = prev[slide.id] || [];
      const updated = active.filter(k => k !== key);
      
      const newConfig = { ...prev, [slide.id]: updated };
      try {
        localStorage.setItem("presentation_slide_components", JSON.stringify(newConfig));
      } catch (e) {}
      return newConfig;
    });
  };

  const activeTheme = SLIDE_THEMES.find(t => t.id === slideThemeId) || SLIDE_THEMES[0];

  React.useEffect(() => {
    activeThemeRef.current = activeTheme;
  }, [activeTheme]);

  // TalkingHead avatar accent color sync
  const currentAccentColor = activeThemeRef.current?.accentColor || "#00E5FF";

  const [isNarrativeExpanded, setIsNarrativeExpanded] = useState(false);

  const [slideNarratives, setSlideNarratives] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem("presentation_slide_narratives");
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return {};
  });

  const [isAiPanelOpen, setIsAiPanelOpen] = useState(false);
  const [aiInstruction, setAiInstruction] = useState("");
  const [isAiGenerating, setIsAiGenerating] = useState(false);
  const [isAiInputFocused, setIsAiInputFocused] = useState(false);

  const [slideLayouts, setSlideLayouts] = useState<Record<string, string>>(() => {
    try {
      const saved = localStorage.getItem("presentation_slide_layouts");
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return {};
  });

  const activeLayout = slideLayouts[slide.id] || "split-panel";

  const handleLayoutChange = (layoutId: string) => {
    setSlideLayouts(prev => {
      const updated = { ...prev, [slide.id]: layoutId };
      try {
        localStorage.setItem("presentation_slide_layouts", JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const handleAiGenerate = async () => {
    const currentText = slideNarratives[slide.id] !== undefined ? slideNarratives[slide.id] : slide.narrative;
    setIsAiGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/api/datastory/generate-narrative`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: currentText,
          instruction: aiInstruction
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.text) {
          handleNarrativeChange({ target: { value: data.text } } as any);
          setAiInstruction("");
          setIsAiPanelOpen(false);
        }
      }
    } catch (e) {
      console.error("AI narrative generation failed", e);
    } finally {
      setIsAiGenerating(false);
    }
  };

  const currentNarrative = slideNarratives[slide.id] !== undefined ? slideNarratives[slide.id] : slide.narrative;

  const handleNarrativeChange = (e: React.ChangeEvent<HTMLTextAreaElement> | { target: { value: string } }) => {
    const text = e.target.value;
    setSlideNarratives(prev => {
      const updated = { ...prev, [slide.id]: text };
      try {
        localStorage.setItem("presentation_slide_narratives", JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const insertFormatting = (syntaxStart: string, syntaxEnd = "") => {
    const textarea = document.getElementById("narrative-textarea") as HTMLTextAreaElement;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selected = text.substring(start, end);
    const replacement = syntaxStart + selected + syntaxEnd;

    const updatedText = text.substring(0, start) + replacement + text.substring(end);
    handleNarrativeChange({ target: { value: updatedText } });

    // Refocus and re-select selection
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + syntaxStart.length, start + syntaxStart.length + selected.length);
    }, 0);
  };

  const parseMarkdown = (text: string) => {
    if (!text) return "";
    
    // Escape HTML tags to prevent execution of unescaped markup
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
      
    // Restore allowed formatting tags
    html = html
      .replace(/&lt;u&gt;/g, "<u>")
      .replace(/&lt;\/u&gt;/g, "</u>")
      .replace(/&lt;strong&gt;/g, "<strong>")
      .replace(/&lt;\/strong&gt;/g, "</strong>")
      .replace(/&lt;em&gt;/g, "<em>")
      .replace(/&lt;\/em&gt;/g, "</em>");

    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Italic: *text*
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    
    // Headers
    html = html.replace(/^## (.*?)$/gm, '<h4 class="text-sm font-bold mt-2.5 mb-1 text-white opacity-90">$1</h4>');
    html = html.replace(/^# (.*?)$/gm, '<h3 class="text-base font-black mt-3.5 mb-1.5 text-white">$1</h3>');

    // Bullet Lists (lines starting with "- ")
    html = html.replace(/^- (.*?)$/gm, '<div class="pl-3.5 flex items-start gap-1.5 my-0.5"><span class="text-cyan-400 select-none">•</span><span>$1</span></div>');

    // Code: `code`
    html = html.replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 rounded font-mono text-xs bg-white/10 text-cyan-400">$1</code>');

    // Replace line breaks with `<br/>`
    html = html.replace(/\n/g, "<br/>");
    
    return html;
  };

  const cleanTextForSpeech = (text: string) => {
    if (!text) return "";
    // Remove HTML tags
    let cleaned = text.replace(/<\/?[^>]+(>|$)/g, "");
    // Remove markdown symbols
    cleaned = cleaned
      .replace(/^[#*-\s]+/gm, "")
      .replace(/[\*_`]+/g, "");
    return cleaned;
  };

  // Resolve layout-specific CSS classes
  const getLayoutClasses = () => {
    switch (activeLayout) {
      case "hero-banner":
        return {
          container: "flex flex-col p-6 gap-6 flex-1 min-h-0 overflow-y-auto scrollbar-none relative z-10",
          narrativeWrapper: "w-full shrink-0 animate-[slideInDown_0.6s_ease-out_both] key-narrative",
          narrativeCard: "p-6 rounded-2xl border backdrop-blur-sm shadow-inner flex flex-col min-h-[160px] max-h-[220px]",
          componentsWrapper: "relative flex-1 min-h-[450px] w-full animate-[slideInUp_0.7s_ease-out_0.15s_both] key-components"
        };
      case "right-focus":
        return {
          container: "flex flex-col md:flex-row-reverse p-6 gap-6 flex-1 min-h-0 overflow-hidden relative z-10",
          narrativeWrapper: cn(
            "flex flex-col gap-4 min-h-0 transition-all duration-300 animate-[slideInRight_0.6s_ease-out_both] key-narrative",
            isNarrativeExpanded ? "md:w-2/3" : "md:w-1/3"
          ),
          narrativeCard: "p-6 rounded-2xl border backdrop-blur-sm h-full shadow-inner overflow-y-auto scrollbar-none flex flex-col",
          componentsWrapper: cn(
            "relative h-full min-h-0 overflow-y-auto scrollbar-none transition-all duration-300 animate-[fadeInScale_0.8s_ease-out_0.1s_both] key-components",
            isNarrativeExpanded ? "md:w-1/3" : "md:w-2/3"
          )
        };
      case "immersive-story":
        return {
          container: "flex flex-col items-center p-6 gap-6 flex-1 min-h-0 overflow-y-auto scrollbar-none relative z-10",
          narrativeWrapper: "w-full max-w-4xl shrink-0 animate-[deepZoom_0.8s_ease-out_both] key-narrative",
          narrativeCard: "p-8 rounded-2xl border-2 backdrop-blur-md shadow-2xl flex flex-col min-h-[180px]",
          componentsWrapper: "relative w-full max-w-4xl min-h-[450px] mt-4 animate-[slideInUp_0.7s_ease-out_0.2s_both] key-components"
        };
      case "staggered-flow":
        return {
          container: "flex flex-col md:flex-row p-6 gap-6 flex-1 min-h-0 overflow-x-auto scrollbar-none relative z-10",
          narrativeWrapper: "flex flex-col gap-4 min-h-0 shrink-0 w-[350px] animate-[slideInLeft_0.6s_ease-out_both] key-narrative",
          narrativeCard: "p-6 rounded-2xl border backdrop-blur-sm h-full shadow-inner overflow-y-auto scrollbar-none flex flex-col",
          componentsWrapper: "relative h-full min-h-0 flex-1 flex flex-col md:flex-row gap-6 overflow-visible animate-[staggerSlideIn_0.7s_ease-out_0.15s_both] key-components"
        };
      case "split-panel":
      default:
        return {
          container: "flex flex-col md:flex-row p-6 gap-6 flex-1 min-h-0 overflow-hidden relative z-10",
          narrativeWrapper: cn(
            "flex flex-col gap-4 min-h-0 transition-all duration-300 animate-[slideInLeft_0.6s_ease-out_both] key-narrative",
            isNarrativeExpanded ? "md:w-2/3" : "md:w-1/3"
          ),
          narrativeCard: "p-6 rounded-2xl border backdrop-blur-sm h-full shadow-inner overflow-y-auto scrollbar-none flex flex-col",
          componentsWrapper: cn(
            "relative h-full min-h-0 overflow-y-auto scrollbar-none transition-all duration-300 animate-[fadeInScale_0.8s_ease-out_0.1s_both] key-components",
            isNarrativeExpanded ? "md:w-1/3" : "md:w-2/3"
          )
        };
    }
  };

  const layoutClasses = getLayoutClasses();

  return (
    <div 
      className={cn(
        "w-full flex flex-col rounded-2xl border backdrop-blur-xl shadow-2xl overflow-hidden transition-all duration-700 h-full relative",
        activeTheme.className,
        `theme-${activeTheme.id}`
      )}
    >
      {/* Dynamic theme background animations */}
      {activeTheme.id === "neon-cyberpunk" && (
        <div className="absolute inset-0 pointer-events-none opacity-[0.06] bg-[linear-gradient(rgba(217,70,239,0.2)_1px,transparent_1px),linear-gradient(90deg,rgba(217,70,239,0.2)_1px,transparent_1px)] bg-[size:30px_30px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_40%,#000_70%,transparent_100%)] animate-[gridMove_20s_linear_infinite]" />
      )}
      {activeTheme.id === "sunset-warmth" && (
        <div className="absolute inset-0 pointer-events-none opacity-30 bg-gradient-to-tr from-amber-500/5 via-red-500/5 to-transparent blur-3xl animate-[sunsetFlow_10s_ease-in-out_infinite]" />
      )}
      {activeTheme.id === "forest-teal" && (
        <div className="absolute inset-0 pointer-events-none opacity-30 bg-gradient-to-bl from-emerald-500/5 via-teal-500/5 to-transparent blur-3xl animate-[forestFlow_12s_ease-in-out_infinite]" />
      )}

      {/* Floating Interactive AI Narrator Avatar */}
      <div
        onPointerDown={handleAvatarPointerDown}
        onPointerMove={handleAvatarPointerMove}
        onPointerUp={handleAvatarPointerUp}
        onPointerCancel={handleAvatarPointerUp}
        onDragStart={(e) => e.preventDefault()}
        className={cn(
          "absolute left-1/2 top-[45%] z-40 select-none touch-none group",
          isAvatarDragging ? "" : "animate-[avatarFloat_4s_ease-in-out_infinite]"
        )}
        style={{
          transform: `translate(calc(-50% + ${avatarPos.x}px), calc(-50% + ${avatarPos.y}px))`,
          cursor: isAvatarDragging ? "grabbing" : "grab",
          ["--x" as any]: `${avatarPos.x}px`,
          ["--y" as any]: `${avatarPos.y}px`,
        }}
      >
        {/* Glowing Floor Contact Shadow / Aura Ring */}
        <div 
          className="absolute bottom-4 left-1/2 -translate-x-1/2 w-40 h-8 rounded-full blur-md opacity-45 pointer-events-none transition-all duration-300 z-0"
          style={{ 
            background: `radial-gradient(ellipse at center, ${activeTheme.accentColor}50 0%, transparent 70%)`,
            boxShadow: isPlaying ? `0 10px 25px ${activeTheme.accentColor}` : `0 4px 10px ${activeTheme.accentColor}30`
          }}
        />

        {/* Avatar WebGL 3D Standing Presenter Container */}
        <div className="w-72 h-[460px] relative z-10 transition-transform duration-300 group-hover:scale-[1.02]">
          <TalkingAvatar
            ref={avatarRef}
            gender={avatarGender}
            persona={currentPersona}
            scale={avatarScale}
            isPlaying={isAvatarSpeaking}
            accentColor={currentAccentColor}
            isFullscreen={isFullscreen}
            onSpeakingChange={setIsAvatarSpeaking}
          />
        </div>

        {/* Active Speaking Indicator */}
        {isAvatarSpeaking && (
          <div 
            className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full text-[8px] font-black tracking-widest text-white uppercase z-20 shadow-lg animate-pulse"
            style={{ backgroundColor: activeTheme.accentColor }}
          >
            NARRATING
          </div>
        )}

        {/* Reusable Speech Controls Panel */}
        <AvatarControlPanel
          currentNarrative={cleanTextForSpeech(currentNarrative)}
          className="absolute -bottom-10 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-auto z-30"
        />

        {/* Cognitive Glassmorphic Chat Panel */}
        {isChatOpen && (
          <div 
            onClick={(e) => e.stopPropagation()}
            onPointerDown={(e) => e.stopPropagation()}
            className={cn(
              "absolute top-0 w-72 h-[380px] rounded-2xl border shadow-2xl flex flex-col z-50 overflow-hidden transition-all duration-500 origin-left pointer-events-auto",
              isLight ? "border-slate-200/90 text-slate-900 bg-white/95" : "border-white/10 text-white bg-slate-950/95",
              avatarPos.x > 150 ? "right-full mr-4 left-auto" : "left-full ml-4 right-auto"
            )}
          >
            {/* Header */}
            <div className={cn(
              "px-3 py-2 border-b flex items-center justify-between",
              isLight ? "border-slate-200/90 bg-slate-50" : "border-white/10 bg-white/[0.02]"
            )}>
              <div className="flex items-center gap-1.5">
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  avatarState === "thinking" ? "bg-blue-500 animate-pulse" :
                  avatarState === "speaking" ? "bg-green-500 animate-pulse" : "bg-neutral-500"
                )} />
                <span className="text-[9px] font-black tracking-widest uppercase">
                  {avatarState === "thinking" ? "THINKING..." :
                   avatarState === "speaking" ? "SPEAKING..." : "AI CO-PILOT"}
                </span>
              </div>
              <button 
                onClick={() => setIsChatOpen(false)}
                className={cn(
                  "p-1 rounded-full transition-colors cursor-pointer",
                  isLight ? "hover:bg-slate-200 text-slate-500" : "hover:bg-white/10 text-neutral-400"
                )}
              >
                <X size={10} />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 text-[11px] leading-relaxed scrollbar-thin">
              {chatMessages.map((msg, i) => (
                <div 
                  key={i} 
                  className={cn(
                    "flex flex-col max-w-[85%] rounded-xl px-2.5 py-1.5",
                    msg.sender === "user" 
                      ? "ml-auto bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" 
                      : isLight 
                        ? "bg-slate-100 text-slate-800 border border-slate-200" 
                        : "bg-white/[0.04] text-neutral-200 border border-white/5"
                  )}
                >
                  <span className="font-semibold text-[8px] tracking-wider uppercase opacity-50 mb-0.5">
                    {msg.sender === "user" ? "You" : "Co-Pilot"}
                  </span>
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>
              ))}
              {avatarState === "thinking" && (
                <div className="flex items-center gap-1.5 pl-2 py-1 text-cyan-400/70">
                  <div className="flex gap-1 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-wider">Syncing neural paths...</span>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="px-3 py-1.5 flex flex-wrap gap-1 border-t border-dashed border-white/10">
              <button 
                onClick={() => handleSendMessage("Analyze Slide Context")}
                className={cn(
                  "px-2 py-0.5 rounded-full text-[9px] border transition-colors cursor-pointer",
                  isLight 
                    ? "border-slate-300 text-slate-600 hover:bg-slate-100" 
                    : "border-white/10 text-neutral-400 hover:bg-white/5 hover:text-white"
                )}
              >
                🔍 Analyze Slide
              </button>
              <button 
                onClick={() => handleSendMessage("Suggest actionable fixes for this slide context")}
                className={cn(
                  "px-2 py-0.5 rounded-full text-[9px] border transition-colors cursor-pointer",
                  isLight 
                    ? "border-slate-300 text-slate-600 hover:bg-slate-100" 
                    : "border-white/10 text-neutral-400 hover:bg-white/5 hover:text-white"
                )}
              >
                ⚡ Suggest Fixes
              </button>
            </div>

            {/* Input Box */}
            <div className={cn(
              "p-2 border-t flex gap-1.5 items-center",
              isLight ? "border-slate-200 bg-slate-50" : "border-white/10 bg-white/[0.01]"
            )}>
              <input 
                type="text" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSendMessage();
                  }
                }}
                placeholder="Ask co-pilot to reason about metrics..."
                className={cn(
                  "flex-1 px-2.5 py-1 text-[11px] rounded-lg border outline-none transition-colors",
                  isLight 
                    ? "bg-white border-slate-300 text-slate-900 focus:border-cyan-500" 
                    : "bg-black/40 border-white/10 text-white focus:border-cyan-500 focus:bg-black/60"
                )}
              />
              <button 
                onClick={() => handleSendMessage()}
                disabled={!chatInput.trim()}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer",
                  chatInput.trim() 
                    ? "bg-cyan-500 text-black hover:bg-cyan-400 active:scale-95" 
                    : isLight 
                      ? "bg-slate-200 text-slate-400 cursor-not-allowed" 
                      : "bg-white/5 text-neutral-600 cursor-not-allowed"
                )}
              >
                Send
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes gridMove {
          from { background-position: 0 0; }
          to { background-position: 0 60px; }
        }
        @keyframes sunsetFlow {
          0%, 100% { transform: scale(1) translate(0, 0); }
          50% { transform: scale(1.1) translate(-2%, 2%); }
        }
        @keyframes forestFlow {
          0%, 100% { transform: scale(1) translate(0, 0); }
          50% { transform: scale(1.15) translate(2%, -2%); }
        }
        @keyframes slideInLeft {
          from { transform: translateX(-40px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideInRight {
          from { transform: translateX(40px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideInDown {
          from { transform: translateY(-40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes slideInUp {
          from { transform: translateY(40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        @keyframes fadeInScale {
          from { transform: scale(0.96); opacity: 0; }
          to { transform: scale(1); opacity: 1; }
        }
        @keyframes deepZoom {
          from { transform: scale(0.9); opacity: 0; filter: blur(8px); }
          to { transform: scale(1); opacity: 1; filter: blur(0); }
        }
        @keyframes staggerSlideIn {
          from { transform: translateX(60px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }

        /* ========================================================
           LIGHT MODE OVERRIDES FOR SLIDES & INFOGRAPHICS
           ======================================================== */
        .theme-light-slate [id*="-card"], 
        .theme-light-slate .glass-card,
        .theme-light-slate [class*="glassSurfaceStatic"],
        .theme-light-slate [class*="bg-[#131926]"] {
          background-color: rgba(248, 250, 252, 0.95) !important;
          border-color: rgba(226, 232, 240, 0.9) !important;
          color: #1e293b !important;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        }

        /* Edit Mode Draggable Wrapper overrides */
        .theme-light-slate [class*="bg-black/40"] {
          background-color: rgba(241, 245, 249, 0.85) !important;
          border-color: rgba(226, 232, 240, 0.9) !important;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
        }

        /* Drag handles */
        .theme-light-slate [data-action="drag"] {
          background-color: rgba(6, 182, 212, 0.03) !important;
          border-bottom-color: rgba(226, 232, 240, 0.9) !important;
        }
        .theme-light-slate [data-action="drag"] [class*="bg-white/20"] {
          background-color: rgba(0, 0, 0, 0.15) !important;
        }
        .theme-light-slate [data-action="drag"] button {
          color: rgba(0, 0, 0, 0.35) !important;
        }
        .theme-light-slate [data-action="drag"] button:hover {
          color: #ef4444 !important;
          background-color: rgba(239, 68, 68, 0.1) !important;
        }

        /* General text overrides inside light-theme cards */
        .theme-light-slate [id*="-card"] .text-white,
        .theme-light-slate .glass-card .text-white,
        .theme-light-slate [id*="-card"] span[class*="text-white"],
        .theme-light-slate .glass-card span[class*="text-white"],
        .theme-light-slate [id*="-card"] div[class*="text-white"],
        .theme-light-slate .glass-card div[class*="text-white"],
        .theme-light-slate [id*="-card"] text[fill*="white"] {
          color: #0f172a !important;
        }
        
        .theme-light-slate [id*="-card"] .text-neutral-300,
        .theme-light-slate .glass-card .text-neutral-300,
        .theme-light-slate [id*="-card"] span[class*="text-neutral-300"],
        .theme-light-slate .glass-card span[class*="text-neutral-300"],
        .theme-light-slate [id*="-card"] div[class*="text-neutral-300"] {
          color: #334155 !important;
        }

        .theme-light-slate [id*="-card"] .text-neutral-400,
        .theme-light-slate .glass-card .text-neutral-400,
        .theme-light-slate [id*="-card"] span[class*="text-neutral-400"],
        .theme-light-slate .glass-card span[class*="text-neutral-400"],
        .theme-light-slate [id*="-card"] div[class*="text-neutral-400"] {
          color: #475569 !important;
        }

        .theme-light-slate [id*="-card"] .text-neutral-500,
        .theme-light-slate .glass-card .text-neutral-500,
        .theme-light-slate [id*="-card"] span[class*="text-neutral-500"],
        .theme-light-slate .glass-card span[class*="text-neutral-500"],
        .theme-light-slate [id*="-card"] p[class*="text-neutral-500"] {
          color: #64748b !important;
        }

        /* SVG Text colors */
        .theme-light-slate [id*="-card"] text,
        .theme-light-slate .glass-card text {
          fill: #334155 !important;
        }
        .theme-light-slate [id*="-card"] text[fill="rgba(255, 255, 255, 0.5)"] {
          fill: rgba(51, 65, 85, 0.6) !important;
        }

        /* Borders & dividers inside cards */
        .theme-light-slate [id*="-card"] .border-b,
        .theme-light-slate .glass-card .border-b,
        .theme-light-slate [id*="-card"] .border-t,
        .theme-light-slate .glass-card .border-t,
        .theme-light-slate [id*="-card"] [class*="border-[#242F41]/45"] {
          border-color: rgba(226, 232, 240, 0.9) !important;
        }

        /* Tooltip popups bg and arrow overrides */
        .theme-light-slate [class*="bg-[#131926]/95"],
        .theme-light-slate [class*="bg-[#131926]"] {
          background-color: rgba(255, 255, 255, 0.98) !important;
          border-color: rgba(6, 182, 212, 0.3) !important;
        }
        .theme-light-slate [class*="bg-[#131926]/95"] [class*="bg-[#131926]"] {
          background-color: #f8fafc !important;
          border-color: rgba(226, 232, 240, 0.9) !important;
        }
        .theme-light-slate [class*="bg-[#131926]/95"] .text-white,
        .theme-light-slate [class*="bg-[#131926]/95"] .text-neutral-200,
        .theme-light-slate [class*="bg-[#131926]/95"] .text-neutral-300 {
          color: #0f172a !important;
        }
        .theme-light-slate [class*="bg-[#131926]/95"] .text-neutral-400 {
          color: #475569 !important;
        }

        /* Recharts Tooltip overrides */
        .theme-light-slate .recharts-default-tooltip {
          background-color: rgba(255, 255, 255, 0.98) !important;
          border-color: rgba(226, 232, 240, 0.9) !important;
          color: #0f172a !important;
        }

        /* Diagnostic Card sub-elements */
        .theme-light-slate [id*="-card"] [class*="bg-neutral-900/20"],
        .theme-light-slate [id*="-card"] [class*="border-neutral-800"],
        .theme-light-slate [id*="-card"] [class*="bg-white/5"],
        .theme-light-slate [id*="-card"] [class*="bg-white/[0.02]"],
        .theme-light-slate [id*="-card"] [class*="bg-white/[0.01]"],
        .theme-light-slate [id*="-card"] [class*="bg-white/[0.04]"],
        .theme-light-slate [id*="-card"] [class*="border-white/5"] {
          background-color: rgba(241, 245, 249, 0.6) !important;
          border-color: rgba(226, 232, 240, 0.8) !important;
        }

        /* Active option highlights */
        .theme-light-slate [id*="-card"] [class*="bg-white/[0.04]"] {
          background-color: rgba(0, 0, 0, 0.04) !important;
        }
        .theme-light-slate [id*="-card"] [class*="border-white/15"] {
          border-color: rgba(6, 182, 212, 0.25) !important;
        }

        /* Progress tracks & bar backgrounds */
        .theme-light-slate [id*="-card"] [class*="bg-[#1A2333]"] {
          background-color: rgba(226, 232, 240, 0.7) !important;
        }

        /* Leaf Steps specific adjustments */
        .theme-light-slate [id*="leaf-step-card"] [class*="h-56"] {
          background-color: rgba(0, 0, 0, 0.015) !important;
          border-color: rgba(0, 0, 0, 0.04) !important;
        }
        .theme-light-slate [id*="leaf-step-card"] [class*="h-56"]:hover {
          background-color: rgba(0, 0, 0, 0.045) !important;
          border-color: rgba(0, 0, 0, 0.08) !important;
        }

        /* Step Flower specific adjustments */
        .theme-light-slate [id*="step-flower-card"] circle[fill="#0F172A"] {
          fill: #f8fafc !important;
        }
        .theme-light-slate [id*="step-flower-card"] circle[stroke="rgba(255, 255, 255, 0.05)"] {
          stroke: rgba(0, 0, 0, 0.05) !important;
        }
        .theme-light-slate [id*="step-flower-card"] circle[stroke="rgba(255, 255, 255, 0.1)"] {
          stroke: rgba(0, 0, 0, 0.1) !important;
        }
        .theme-light-slate [id*="step-flower-card"] circle[stroke="rgba(255, 255, 255, 0.15)"] {
          stroke: rgba(0, 0, 0, 0.15) !important;
        }

        /* Timeline stems specific adjustments */
        .theme-light-slate [id*="timeline-stems-card"] [class*="h-0.5 bg-white/10"],
        .theme-light-slate [id*="timeline-stems-card"] [class*="bg-white/10"] {
          background-color: rgba(0, 0, 0, 0.1) !important;
        }
        .theme-light-slate [id*="timeline-stems-card"] [class*="bg-white/5 border border-white/10"] {
          background-color: rgba(0, 0, 0, 0.02) !important;
          border-color: rgba(0, 0, 0, 0.1) !important;
        }
        .theme-light-slate [id*="timeline-stems-card"] [class*="border-[#090D16]"] {
          border-color: #f8fafc !important;
        }

        /* Operational Health infographic tabs */
        .theme-light-slate [id*="operational-health-card"] [class*="bg-white/5"] {
          background-color: rgba(0, 0, 0, 0.04) !important;
        }
        .theme-light-slate [id*="operational-health-card"] button:not([class*="bg-cyan-500"]) {
          color: #475569 !important;
        }
        .theme-light-slate [id*="operational-health-card"] button:not([class*="bg-cyan-500"]):hover {
          color: #0f172a !important;
        }
        .theme-light-slate [id*="operational-health-card"] circle[stroke="rgba(255, 255, 255, 0.05)"] {
          stroke: rgba(0, 0, 0, 0.06) !important;
        }
        @keyframes avatarFloat {
          0%, 100% { transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y) - 6px)); }
          50% { transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y) + 6px)); }
        }
        @keyframes wavePulse {
          0% { transform: scale(0.9); opacity: 0.6; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        @keyframes scanline {
          0% { top: 0%; }
          50% { top: 100%; }
          100% { top: 0%; }
        }
      `}</style>
      
      {/* Header */}
      <div className={cn(
        "px-6 py-4 border-b flex items-center justify-between relative z-10",
        activeTheme.headerBorderClass
      )}>
        <div className="flex items-center gap-3">
          <div 
            className="flex items-center justify-center w-10 h-10 rounded-full text-xl border transition-colors"
            style={{ 
              backgroundColor: `${activeTheme.accentColor}18`, 
              borderColor: `${activeTheme.accentColor}40` 
            }}
          >
            {slide.icon}
          </div>
          <div>
            <h2 
              className="text-xl font-bold bg-gradient-to-r bg-clip-text text-transparent"
              style={{ backgroundImage: `linear-gradient(to right, ${activeTheme.accentColor}, #3b82f6)` }}
            >
              {slide.title}
            </h2>
            <p className={cn("text-xs transition-colors", activeTheme.subtitleClass)}>
              {slide.subtitle}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Components Library Toggle Button */}
          <button 
            onClick={() => setIsLibraryOpen(!isLibraryOpen)}
            className={cn(
              "p-2 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isLibraryOpen 
                ? "border-cyan-500 text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20"
                : activeTheme.buttonClass
            )}
            title="Configure Slide Components"
          >
            <Sliders size={16} />
          </button>

          <button 
            onClick={() => {
              if (isAvatarSpeaking) {
                avatarRef.current?.stop();
              } else {
                const text = cleanTextForSpeech(currentNarrative);
                avatarRef.current?.speak(text);
              }
            }}
            className={cn(
              "p-2 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isAvatarSpeaking 
                ? "border-red-500/50 text-red-500 bg-red-500/10 hover:bg-red-500/20 shadow-[0_0_8px_rgba(239,68,68,0.3)]"
                : activeTheme.buttonClass
            )}
            title={isAvatarSpeaking ? "Stop Insights Audio" : "Play Insights Audio"}
          >
            <Volume2 size={16} className={cn(isAvatarSpeaking ? "animate-pulse" : "")} />
          </button>
        </div>
      </div>

      {/* Main Content Area Wrapper */}
      <div className="flex-1 min-h-0 relative flex overflow-hidden">
        
        {/* Main Content Area */}
        <div 
          key={`${slide.id}-${activeLayout}`}
          className={layoutClasses.container}
        >
          {/* Narrative Panel */}
          <div className={layoutClasses.narrativeWrapper}>
            <div 
              className={cn(layoutClasses.narrativeCard, activeTheme.narrativeCardClass)}
              style={activeLayout === "immersive-story" ? {
                boxShadow: `0 0 30px ${activeTheme.accentColor}15, inset 0 1px 1px rgba(255,255,255,0.05)`,
                borderColor: `${activeTheme.accentColor}30`
              } : undefined}
            >
              <div className="flex items-center gap-2 mb-4 flex-shrink-0">
                <div 
                  className="w-1.5 h-6 rounded-full transition-colors" 
                  style={{ backgroundColor: activeTheme.accentColor }} 
                />
                <h3 className={cn("text-sm font-semibold tracking-wider uppercase transition-colors", activeTheme.narrativeTitleClass)}>
                  System Insights
                </h3>
                {activeLayout !== "hero-banner" && activeLayout !== "immersive-story" && activeLayout !== "staggered-flow" && (
                  <button
                    onClick={() => setIsNarrativeExpanded(!isNarrativeExpanded)}
                    className="p-1.5 rounded-full text-neutral-400 hover:text-white hover:bg-white/10 transition-all ml-auto cursor-pointer flex items-center justify-center"
                    title={isNarrativeExpanded ? "Collapse panel (1/3 width)" : "Expand panel (2/3 width)"}
                  >
                    {isNarrativeExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
                  </button>
                )}
              </div>
              
              {isEditing && (
                <div className={cn(
                  "flex items-center gap-1 pb-2 mb-2 border-b flex-wrap flex-shrink-0",
                  activeTheme.headerBorderClass
                )}>
                  <button
                    onClick={() => insertFormatting("**", "**")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Bold (**)"
                  >
                    <Bold size={13} />
                  </button>
                  <button
                    onClick={() => insertFormatting("*", "*")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Italic (*)"
                  >
                    <Italic size={13} />
                  </button>
                  <button
                    onClick={() => insertFormatting("<u>", "</u>")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Underline (<u>)"
                  >
                    <Underline size={13} />
                  </button>
                  <div className="w-[1px] h-3 bg-white/10 mx-0.5" />
                  <button
                    onClick={() => insertFormatting("# ")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Heading 1 (#)"
                  >
                    <Heading1 size={13} />
                  </button>
                  <button
                    onClick={() => insertFormatting("## ")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Heading 2 (##)"
                  >
                    <Heading2 size={13} />
                  </button>
                  <button
                    onClick={() => insertFormatting("- ")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="List Item (-)"
                  >
                    <List size={13} />
                  </button>
                  <button
                    onClick={() => insertFormatting("`", "`")}
                    className="p-1 rounded text-neutral-400 hover:text-white hover:bg-white/10 transition-colors"
                    title="Code inline (`)"
                  >
                    <Code size={13} />
                  </button>
                  <div className="w-[1px] h-3 bg-white/10 mx-0.5" />
                  <button
                    onClick={() => setIsAiPanelOpen(!isAiPanelOpen)}
                    className={cn(
                      "p-1 rounded transition-colors flex items-center justify-center cursor-pointer",
                      isAiPanelOpen 
                        ? "border" 
                        : "text-neutral-400 hover:bg-white/10"
                    )}
                    style={{
                      backgroundColor: isAiPanelOpen ? `${activeTheme.accentColor}20` : undefined,
                      color: isAiPanelOpen ? activeTheme.accentColor : undefined,
                      borderColor: isAiPanelOpen ? `${activeTheme.accentColor}30` : undefined,
                    }}
                    title="AI Story Refiner"
                  >
                    <Sparkles 
                      size={13} 
                      className={cn(isAiGenerating ? "animate-spin" : "")} 
                      style={{ 
                        color: isAiGenerating || isAiPanelOpen ? activeTheme.accentColor : undefined 
                      }} 
                    />
                  </button>
                </div>
              )}

              {isEditing && isAiPanelOpen && (
                <div 
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-1.5 rounded-full border transition-all duration-300 relative z-15 mb-3.5 shadow-sm",
                    isAiInputFocused
                      ? (activeTheme.id === "light-slate" ? "bg-white" : "bg-black/40")
                      : (activeTheme.id === "light-slate" ? "bg-slate-100" : "bg-white/[0.02]")
                  )}
                  style={{
                    borderColor: isAiInputFocused
                      ? `${activeTheme.accentColor}80`
                      : (activeTheme.id === "light-slate" ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.08)"),
                    boxShadow: isAiInputFocused
                      ? `0 0 12px ${activeTheme.accentColor}20, inset 0 1px 1px ${activeTheme.id === "light-slate" ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.05)"}`
                      : undefined
                  }}
                >
                  <Sparkles 
                    size={13}
                    className={cn(
                      "flex-shrink-0 transition-all duration-300",
                      isAiGenerating ? "animate-spin" : (isAiInputFocused ? "animate-pulse" : "")
                    )}
                    style={{ 
                      color: isAiGenerating || isAiInputFocused 
                        ? activeTheme.accentColor 
                        : (activeTheme.id === "light-slate" ? "rgba(0,0,0,0.4)" : "rgba(255,255,255,0.4)") 
                    }}
                  />
                  <input
                    type="text"
                    value={aiInstruction}
                    onChange={(e) => setAiInstruction(e.target.value)}
                    onFocus={() => setIsAiInputFocused(true)}
                    onBlur={() => setIsAiInputFocused(false)}
                    placeholder="Ask AI to refine story (e.g., 'make professional', 'expand SLA')..."
                    className={cn(
                      "flex-1 bg-transparent border-none p-0 text-xs focus:outline-none focus:ring-0 leading-normal",
                      activeTheme.id === "light-slate"
                        ? "text-slate-800 placeholder-slate-400"
                        : "text-white placeholder-neutral-500"
                    )}
                    disabled={isAiGenerating}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleAiGenerate();
                      } else if (e.key === "Escape") {
                        setIsAiPanelOpen(false);
                      }
                    }}
                  />
                  
                  {!isAiGenerating && (
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {aiInstruction ? (
                        <button
                          onClick={handleAiGenerate}
                          className="text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider transition-all duration-200 cursor-pointer"
                          style={{
                            backgroundColor: `${activeTheme.accentColor}20`,
                            color: activeTheme.accentColor
                          }}
                        >
                          Refine
                        </button>
                      ) : (
                        <span 
                          className={cn(
                            "text-[9px] font-mono px-1.5 py-0.5 rounded border flex items-center gap-0.5 pointer-events-none select-none",
                            activeTheme.id === "light-slate"
                              ? "bg-slate-200 border-slate-300 text-slate-500"
                              : "bg-white/5 border-white/5 text-neutral-400"
                          )}
                        >
                          <span>Enter</span>
                          <span className="text-[10px] leading-none">↵</span>
                        </span>
                      )}
                      <button
                        onClick={() => {
                          setAiInstruction("");
                          setIsAiPanelOpen(false);
                        }}
                        className={cn(
                          "p-0.5 rounded-full border transition-all duration-200 cursor-pointer flex items-center justify-center",
                          activeTheme.id === "light-slate"
                            ? "bg-slate-200 border-slate-300 text-slate-400 hover:bg-slate-300 hover:text-slate-600"
                            : "bg-white/5 border-white/5 text-neutral-500 hover:text-white hover:bg-white/10 hover:border-white/10"
                        )}
                        title="Close AI story refiner (ESC)"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  )}
                  {isAiGenerating && (
                    <span
                      className="text-[10px] font-semibold uppercase tracking-wider animate-pulse flex-shrink-0"
                      style={{ color: activeTheme.accentColor }}
                    >
                      Refining...
                    </span>
                  )}
                </div>
              )}

              <div className="flex-1 min-h-0 w-full overflow-y-auto scrollbar-none">
                {isEditing ? (
                  <textarea
                    id="narrative-textarea"
                    value={currentNarrative}
                    onChange={handleNarrativeChange}
                    className={cn(
                      "w-full h-full min-h-[180px] bg-transparent border-none resize-y focus:outline-none focus:ring-0 leading-relaxed text-sm md:text-base transition-colors scrollbar-none",
                      activeTheme.narrativeTextClass
                    )}
                    placeholder="Type slide narrative here..."
                  />
                ) : (
                  <div 
                    className={cn("leading-relaxed text-sm md:text-base transition-colors", activeTheme.narrativeTextClass)}
                    dangerouslySetInnerHTML={{ __html: parseMarkdown(currentNarrative) }}
                  />
            )}
          </div>
          </div>
          </div>

          {/* Live Components Panel */}
          <div className={layoutClasses.componentsWrapper}>
            {activeKeys.map((key, index) => {
              const data = COMPONENT_REGISTRY[key];
              if (!data) return null;
              const Comp = data.component;
              
              // Calculate default side-by-side grid positions (safe offsets for all component dimensions)
              const defaultX = (index % 2) * 420;
              const defaultY = Math.floor(index / 2) * 450;

              return (
                <DraggableComponent 
                  key={`${slide.id}-${key}-${resetCounter}-${isFullscreen ? 'fs' : 'normal'}`}
                  id={`${slide.id}-${key}`} 
                  defaultWidth={data.defaultWidth}
                  onRemove={() => handleRemoveComponent(key)}
                  defaultX={defaultX}
                  defaultY={defaultY}
                  isEditing={isEditing}
                  isLight={activeTheme.id === "light-slate"}
                >
                  <Comp />
                </DraggableComponent>
              );
            })}
            {activeKeys.length === 0 && (
              <div className={cn(
                "absolute inset-0 flex flex-col items-center justify-center border border-dashed rounded-2xl p-8 opacity-60",
                activeTheme.placeholderClass
              )}>
                <span className="text-4xl mb-2">🔌</span>
                <p className="text-sm font-semibold">No components active on this slide</p>
                <button 
                  onClick={() => setIsLibraryOpen(true)}
                  className="mt-3 text-xs px-3 py-1.5 rounded-full transition-all font-bold uppercase tracking-wider cursor-pointer"
                  style={{ backgroundColor: `${activeTheme.accentColor}25`, color: activeTheme.accentColor }}
                >
                  Open Components Library
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Collapsible Panel */}
        <div className={cn(
          "absolute right-0 top-0 bottom-0 w-80 border-l backdrop-blur-2xl shadow-2xl transition-all duration-300 z-30 flex flex-col min-h-0",
          isLibraryOpen ? "translate-x-0" : "translate-x-full",
          activeTheme.sidebarClass
        )}>
          {/* Panel Header */}
          <div className={cn(
            "px-4 py-3 border-b flex items-center justify-between",
            activeTheme.sidebarHeaderBorderClass
          )}>
            <div className="flex items-center gap-2">
              <span 
                className="text-xs font-bold uppercase tracking-wider bg-gradient-to-r bg-clip-text text-transparent"
                style={{ backgroundImage: `linear-gradient(to right, ${activeTheme.accentColor}, #3b82f6)` }}
              >
                Slide Elements
              </span>
              <span className={cn(
                "text-[9px] px-1.5 py-0.5 rounded-full font-bold transition-colors",
                activeTheme.sidebarBadgeClass
              )}>
                {activeKeys.length} active
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button 
                onClick={handleResetPositions}
                className={cn(
                  "text-[9px] uppercase font-bold px-2 py-1 rounded transition-colors border cursor-pointer",
                  activeTheme.sidebarResetButtonClass
                )}
                title="Reset components and coordinates to defaults"
              >
                Reset
              </button>
              <button 
                onClick={() => setIsLibraryOpen(false)} 
                className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center transition-colors text-neutral-400 hover:text-neutral-200 cursor-pointer"
                )}
              >
                <X size={12} />
              </button>
            </div>
          </div>

          {/* Theme Selector Section */}
          <div className={cn(
            "px-4 py-3 border-b flex flex-col gap-2 relative z-10",
            activeTheme.sidebarHeaderBorderClass
          )}>
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              Slide Theme
            </span>
            <div className="flex items-center gap-2.5">
              {SLIDE_THEMES.map((t) => {
                const isThemeActive = t.id === slideThemeId;
                return (
                  <button
                    key={t.id}
                    onClick={() => handleThemeChange(t.id)}
                    className={cn(
                      "w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all cursor-pointer hover:scale-115",
                      isThemeActive 
                        ? "scale-110" 
                        : "border-transparent opacity-65 hover:opacity-100"
                    )}
                    style={{ borderColor: isThemeActive ? activeTheme.accentColor : "transparent" }}
                    title={t.name}
                  >
                    <div 
                      className="w-5 h-5 rounded-full relative overflow-hidden"
                      style={{ 
                        background: `linear-gradient(135deg, ${t.swatchColors[0]} 0%, ${t.swatchColors[0]} 50%, ${t.swatchColors[1]} 50%, ${t.swatchColors[1]} 100%)`,
                        boxShadow: "inset 0 0 4px rgba(0,0,0,0.4)"
                      }}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Slide Layout Selector Section */}
          <div className={cn(
            "px-4 py-3 border-b flex flex-col gap-2 relative z-10",
            activeTheme.sidebarHeaderBorderClass
          )}>
            <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-400">
              Slide Layout Template
            </span>
            <div className="grid grid-cols-5 gap-1.5">
              {LAYOUT_TEMPLATES.map((layout) => {
                const isLayoutActive = layout.id === activeLayout;
                return (
                  <button
                    key={layout.id}
                    onClick={() => handleLayoutChange(layout.id)}
                    className={cn(
                      "flex flex-col items-center justify-center p-1.5 rounded-lg border transition-all cursor-pointer",
                      isLayoutActive
                        ? "bg-white/10"
                        : "bg-transparent border-transparent opacity-60 hover:opacity-100 hover:bg-white/5"
                    )}
                    style={{ 
                      borderColor: isLayoutActive ? activeTheme.accentColor : "transparent",
                      color: isLayoutActive ? activeTheme.accentColor : "inherit"
                    }}
                    title={layout.name}
                  >
                    <span className="text-base mb-0.5">{layout.icon}</span>
                    <span className="text-[8px] font-semibold text-center leading-tight truncate w-full">
                      {layout.shortName}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Panel Content (List of components) */}
          <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-none relative z-10">
            {Object.entries(COMPONENT_REGISTRY).map(([key, data]) => {
              const isActive = activeKeys.includes(key);
              const isInfographicStart = key === "StepFlowerProcess";
              return (
                <React.Fragment key={key}>
                  {isInfographicStart && (
                    <div className="py-2 px-1">
                      <div className={cn("border-t my-1", activeTheme.sidebarHeaderBorderClass)} />
                      <span className="text-[9px] font-black uppercase tracking-wider opacity-40 block ml-1.5 mt-1.5">
                        Interactive Infographics
                      </span>
                    </div>
                  )}
                  <div 
                    onClick={() => handleToggleComponent(key)}
                    className={cn(
                      "flex items-center justify-between py-1.5 px-2.5 rounded-md cursor-pointer transition-all duration-155 group",
                      activeTheme.sidebarItemHoverClass
                    )}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {/* Minimal status indicator dot */}
                      <div className={cn(
                        "w-1 h-1 rounded-full flex-shrink-0 transition-all",
                        isActive 
                          ? "shadow-[0_0_4px_rgba(6,182,212,0.8)]" 
                          : activeTheme.sidebarStatusDotClass
                      )} 
                      style={{ backgroundColor: isActive ? activeTheme.accentColor : undefined }}
                      />
                      <span className={cn(
                        "text-[11px] font-medium transition-colors truncate",
                        isActive
                          ? activeTheme.sidebarItemTextClass.split(' ')[0] + " font-semibold"
                          : activeTheme.sidebarItemTextClass.split(' ')[1]
                      )}>
                        {data.name}
                      </span>
                    </div>
                    
                    {/* Subtle actions text */}
                    <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      {isActive ? (
                        <span className="text-[8px] uppercase font-extrabold text-rose-500/80 hover:text-rose-400">Remove</span>
                      ) : (
                        <span className="text-[8px] uppercase font-extrabold text-cyan-400/80 hover:text-cyan-400">Add</span>
            )}
          </div>
        </div>
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Slide Footer / Navigation */}
      <div className={cn(
        "flex items-center justify-between px-6 py-3 border-t shrink-0 relative z-10",
        activeTheme.footerClass
      )}>
        <button 
          onClick={handlePrev}
          disabled={currentSlide === 0}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer",
            currentSlide === 0 ? "opacity-30 cursor-not-allowed" : activeTheme.footerButtonClass
          )}
        >
          <ChevronLeft size={16} /> Previous
        </button>
        
        <div className="flex gap-2">
          {PRESENTATION_SLIDES.map((_, idx) => (
            <div 
              key={idx} 
              className={cn(
                "w-2 h-2 rounded-full transition-all duration-300",
                idx === currentSlide 
                  ? activeTheme.footerIndicatorClass.split(' ')[0]
                  : activeTheme.footerIndicatorClass.split(' ')[1]
              )}
              style={{ backgroundColor: idx === currentSlide ? activeTheme.accentColor : undefined }}
            />
          ))}
        </div>

        <button 
          onClick={handleNext}
          disabled={currentSlide === PRESENTATION_SLIDES.length - 1}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer",
            currentSlide === PRESENTATION_SLIDES.length - 1 ? "opacity-30 cursor-not-allowed" : activeTheme.footerButtonClass
          )}
        >
          Next Slide <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

export function PresentationTemplate(props: PresentationTemplateProps) {
  return (
    <AvatarProvider>
      <PresentationBody {...props} />
    </AvatarProvider>
  );
}
