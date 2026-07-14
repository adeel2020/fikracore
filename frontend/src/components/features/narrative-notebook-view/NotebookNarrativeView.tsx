"use client";

import React, { useEffect, useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { SemanticCloudView } from "./components/semantic-cloud-view";
import { getDashboardFeed } from "./components/semantic-cloud-view/hooks/useDashboardFeedCache";
import type { ClusterStory } from "./components/semantic-cloud-view/types/semantic-cloud.types";
import { useAudioNarrator } from "./hooks/useAudioNarrator";
import { Play, Square, Sun, Moon, Volume2, Edit2, FileText, GraduationCap, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";

import { UniversityTemplate } from "./components/university-template/UniversityTemplate";
import { RibbonBackground } from "./components/university-template/RibbonBackground";
import { PresentationTemplate, DraggableComponent } from "./components/presentation-template/PresentationTemplate";
import { QuantumLogoSwarm } from "./components/presentation-template/QuantumLogoSwarm";
import SciFiStudio from "./components/presentation-template/SciFiStudio";

// --- Presentational Components for the Chapters ---

function NarrativeVectorLoader({ isLight }: { isLight: boolean }) {
  const [stepIndex, setStepIndex] = useState(0);
  const steps = [
    "Initializing semantic vector space...",
    "Decomposing ticket multi-variant axes...",
    "Mapping dimensional centroids...",
    "Synthesizing executive stories...",
    "Securing diagnostic telemetry feeds..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % steps.length);
    }, 1600);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-20 min-h-[400px] w-full relative">
      <style>{`
        @keyframes orbit {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulseGlow {
          0%, 100% { transform: scale(1); opacity: 0.2; }
          50% { transform: scale(1.15); opacity: 0.6; }
        }
        @keyframes nodeFloat1 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(6px, -8px); }
        }
        @keyframes nodeFloat2 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(-8px, 6px); }
        }
        @keyframes nodeFloat3 {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(8px, 8px); }
        }
        @keyframes slideInUp {
          from { transform: translateY(12px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>

      {/* Glassmorphic Container Card */}
      <div className={cn(
        "p-10 rounded-3xl border backdrop-blur-xl shadow-2xl flex flex-col items-center max-w-sm w-full transition-all duration-500",
        isLight 
          ? "bg-white/80 border-slate-200/80 shadow-slate-100" 
          : "bg-black/40 border-white/5 shadow-black/40"
      )}>
        {/* Animated Vector SVG Graphic */}
        <div className="relative w-24 h-24 mb-6 flex items-center justify-center">
          {/* Pulsing center glow */}
          <div 
            className="absolute w-16 h-16 rounded-full blur-xl animate-[pulseGlow_3s_infinite]"
            style={{ backgroundColor: isLight ? 'rgba(14,165,233,0.3)' : 'rgba(0,229,255,0.2)' }}
          />

          {/* Rotating orbital ring */}
          <svg className="absolute w-24 h-24 animate-[orbit_8s_linear_infinite]" viewBox="0 0 100 100">
            <circle 
              cx="50" 
              cy="50" 
              r="40" 
              fill="none" 
              stroke={isLight ? "rgba(14,165,233,0.15)" : "rgba(255,255,255,0.06)"} 
              strokeWidth="1.5"
              strokeDasharray="4 8"
            />
            <circle 
              cx="50" 
              cy="50" 
              r="40" 
              fill="none" 
              stroke={isLight ? "#0EA5E9" : "#00E5FF"} 
              strokeWidth="2" 
              strokeDasharray="30 150"
            />
          </svg>

          {/* Inner Semantic Vector Nodes */}
          <svg className="absolute w-16 h-16 z-10" viewBox="0 0 60 60">
            {/* Connection Lines */}
            <line x1="30" y1="30" x2="15" y2="20" stroke={isLight ? "rgba(14,165,233,0.3)" : "rgba(0,229,255,0.2)"} strokeWidth="1" className="animate-[pulseGlow_2s_infinite]" />
            <line x1="30" y1="30" x2="45" y2="15" stroke={isLight ? "rgba(14,165,233,0.3)" : "rgba(0,229,255,0.2)"} strokeWidth="1" className="animate-[pulseGlow_2.5s_infinite]" />
            <line x1="30" y1="30" x2="35" y2="45" stroke={isLight ? "rgba(14,165,233,0.3)" : "rgba(0,229,255,0.2)"} strokeWidth="1" className="animate-[pulseGlow_3s_infinite]" />
            <line x1="15" y1="20" x2="45" y2="15" stroke={isLight ? "rgba(14,165,233,0.1)" : "rgba(255,255,255,0.05)"} strokeWidth="0.8" />
            <line x1="35" y1="45" x2="15" y2="20" stroke={isLight ? "rgba(14,165,233,0.1)" : "rgba(255,255,255,0.05)"} strokeWidth="0.8" />

            {/* Central Node */}
            <circle cx="30" cy="30" r="5.5" fill={isLight ? "#0EA5E9" : "#00E5FF"} className="shadow-lg" />
            
            {/* Floating Outer Nodes */}
            <circle cx="15" cy="20" r="4.5" fill={isLight ? "#3b82f6" : "#3b82f6"} className="animate-[nodeFloat1_4s_ease-in-out_infinite]" />
            <circle cx="45" cy="15" r="4" fill={isLight ? "#a855f7" : "#d946ef"} className="animate-[nodeFloat2_4.5s_ease-in-out_infinite]" />
            <circle cx="35" cy="45" r="5" fill={isLight ? "#10b981" : "#10b981"} className="animate-[nodeFloat3_3.5s_ease-in-out_infinite]" />
          </svg>
        </div>

        {/* Text loading progress indicators */}
        <div className="flex flex-col items-center text-center">
          <span 
            className="text-xs uppercase tracking-widest font-black mb-2 animate-pulse"
            style={{ color: isLight ? "#0284c7" : "#00E5FF" }}
          >
            Analyzing Feeds
          </span>
          <p 
            key={stepIndex}
            className={cn(
              "text-sm font-semibold tracking-wide transition-all duration-500 animate-[slideInUp_0.4s_ease-out_both] h-5 mb-1.5",
              isLight ? "text-slate-800" : "text-neutral-100"
            )}
          >
            {steps[stepIndex]}
          </p>
          <div className="flex items-center gap-1 mt-3">
            {steps.map((_, idx) => (
              <div 
                key={idx}
                className="w-1.5 h-1.5 rounded-full transition-all duration-300"
                style={{ 
                  backgroundColor: idx === stepIndex 
                    ? (isLight ? "#0ea5e9" : "#00e5ff") 
                    : (isLight ? "rgba(0,0,0,0.1)" : "rgba(255,255,255,0.1)"),
                  transform: idx === stepIndex ? "scale(1.25)" : "scale(1)"
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ChapterCard({ story, isLight, onPlay, onStop, isPlaying }: { story: ClusterStory; isLight: boolean; onPlay: () => void; onStop: () => void; isPlaying: boolean }) {
  return (
    <div className={cn(
      "mb-12 rounded-2xl p-8 border backdrop-blur-md transition-all duration-300",
      isLight 
        ? "bg-white/60 border-slate-200 shadow-sm" 
        : "bg-[#0A0A0A]/60 border-white/10 shadow-[0_4px_24px_rgba(0,0,0,0.4)]"
    )}>
      {/* Chapter Header */}
      <div className="flex items-start justify-between border-b pb-4 mb-6" style={{ borderColor: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)' }}>
        <div>
          <h2 className={cn("text-2xl font-bold tracking-tight", isLight ? "text-slate-900" : "text-white")}>
            {story.theme}
          </h2>
          <div className="flex gap-4 mt-2 font-mono text-xs uppercase tracking-wider">
            <span className={isLight ? "text-slate-500" : "text-neutral-400"}>
              Volume: {story.volume}
            </span>
            <span className={cn(isLight ? "text-cyan-600" : "text-cyan-400")}>
              Axis: {story.dominant_axis || 'Multi-variant'}
            </span>
          </div>
        </div>

        {/* Audio Control Bar */}
        <div className={cn(
          "flex items-center gap-2 rounded-full px-3 py-1.5 border",
          isLight ? "bg-slate-100 border-slate-200" : "bg-white/5 border-white/10"
        )}>
          {isPlaying ? (
            <button onClick={onStop} className={cn("p-1.5 rounded-full hover:scale-105 transition-transform", isLight ? "bg-red-500 text-white" : "bg-red-500/20 text-red-400")}>
              <Square size={14} fill="currentColor" />
            </button>
          ) : (
            <button onClick={onPlay} className={cn("p-1.5 rounded-full hover:scale-105 transition-transform", isLight ? "bg-cyan-500 text-white" : "bg-cyan-500/20 text-cyan-400")}>
              <Play size={14} fill="currentColor" className="ml-0.5" />
            </button>
          )}
          <Volume2 size={14} className={isLight ? "text-slate-400" : "text-neutral-500"} />
        </div>
      </div>

      {/* Curated Story Text */}
      <div className={cn(
        "prose prose-sm max-w-none leading-relaxed",
        isLight ? "prose-slate text-slate-700" : "prose-invert text-neutral-300"
      )}>
        <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2">
          <span>🌐</span> Incident Topology & Cross-Domain Isolation
        </h3>
        
        <p className="font-bold mb-1">Executive Summary</p>
        <p className="text-[15px] leading-relaxed mb-6">
          A sudden correlation of multi-variant customer tickets was registered across distinct core service journeys. The SOC Mobile Core Engineering team initiated an urgent cross-domain analysis to trace systemic anomalies and isolate touchpoint friction. By executing an unsupervised semantic clustering pass over the incident payload, the root-layer operational boundary was successfully identified and contained.
        </p>
        
        <hr className={cn("my-6 border-t", isLight ? "border-slate-200" : "border-white/10")} />

        <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2">
          <span>📊</span> Strategic Diagnostic Vector
        </h3>
        
        <ul className="list-disc pl-5 mb-6 space-y-2 text-[15px]">
          <li><strong>Primary System Friction:</strong> <code className={cn("px-1.5 py-0.5 rounded font-mono text-sm", isLight ? "bg-slate-100 text-rose-600" : "bg-white/10 text-rose-400")}>{story.theme}</code></li>
          <li><strong>Total Incident Volume:</strong> <code className={cn("px-1.5 py-0.5 rounded font-mono text-sm", isLight ? "bg-slate-100" : "bg-white/10")}>{story.complaints_count}</code> raw complaints correlated in this domain.</li>
          <li><strong>Impacted Service Journeys:</strong> {story.service_journeys.join(', ')}</li>
          <li><strong>Ingress Queue Footprint:</strong> {story.ticket_queues.join(', ')}</li>
          <li><strong>Target Domain Stakeholders:</strong> {story.reassigned_to.join(', ')}</li>
        </ul>

        <hr className={cn("my-6 border-t", isLight ? "border-slate-200" : "border-white/10")} />

        <h3 className="text-lg font-bold mt-4 mb-2 flex items-center gap-2">
          <span>🔍</span> Engineering Root-Cause & Routing Synopsis
        </h3>
        <p className="text-[15px] leading-relaxed mb-6">
          The spatial separation of the data cloud confirms that while incoming telemetry was highly fragmented across multiple edge user-plane ingress points, the core failure signatures converge precisely on a single systemic issue. To prevent ticket loops and safeguard SLA boundaries, ownership has been routed directly to the identified domain stakeholders for final architectural mitigation.
        </p>
      </div>

      {/* Micro-Infographics / Metrics Block */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Exemplar */}
        <div className={cn("p-4 rounded-xl border", isLight ? "bg-slate-50/50 border-slate-100" : "bg-white/[0.02] border-white/5")}>
          <h4 className={cn("text-xs font-bold uppercase tracking-wider mb-2", isLight ? "text-slate-500" : "text-neutral-500")}>Operational Norm</h4>
          <p className={cn("text-sm font-mono truncate", isLight ? "text-slate-800" : "text-neutral-300")}>{story.exemplar || "Standard execution path"}</p>
        </div>

        {/* Anomalies */}
        <div className={cn("p-4 rounded-xl border", isLight ? "bg-rose-50/50 border-rose-100" : "bg-rose-500/[0.02] border-rose-500/10")}>
          <h4 className={cn("text-xs font-bold uppercase tracking-wider mb-2", isLight ? "text-rose-500" : "text-rose-400/70")}>Systemic Friction</h4>
          {story.anomalies && story.anomalies.length > 0 ? (
            <ul className={cn("text-sm font-mono space-y-1 list-disc pl-4", isLight ? "text-rose-700" : "text-rose-300")}>
              {story.anomalies.slice(0, 3).map((anomaly, idx) => (
                <li key={idx} className="truncate">{anomaly}</li>
              ))}
              {story.anomalies.length > 3 && <li className="text-xs opacity-70">+{story.anomalies.length - 3} more...</li>}
            </ul>
          ) : (
            <p className={cn("text-sm font-mono", isLight ? "text-slate-500" : "text-neutral-500")}>No significant anomalies detected.</p>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Main View Controller ---

export function NotebookNarrativeView() {
  const [theme, setTheme] = useState<'dark' | 'light'>('light');
  const [template, setTemplate] = useState<'executive' | 'university' | 'presentation'>('presentation');
  const [editMode, setEditMode] = useState(false);
  const [stories, setStories] = useState<ClusterStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeTab, setActiveTab] = useState("landing");
  const fullscreenContainerRef = React.useRef<HTMLDivElement>(null);
  
  const narrator = useAudioNarrator();

  const cycleTemplate = () => {
    setTemplate(prev => {
      if (prev === 'executive') return 'university';
      if (prev === 'university') return 'presentation';
      return 'executive';
    });
  };

  const getTemplateIcon = () => {
    if (template === 'executive') return <FileText size={14} />;
    if (template === 'university') return <GraduationCap size={14} />;
    return <Monitor size={14} />;
  };

  const getTemplateTitle = () => {
    if (template === 'executive') return "Template: Executive Brief (Click to cycle)";
    if (template === 'university') return "Template: University Template (Click to cycle)";
    return "Template: Presentation Deck (Click to cycle)";
  };

  useEffect(() => {
    let cancelled = false;
    getDashboardFeed(refreshKey)
      .then((data) => {
        if (!cancelled && data.cluster_stories) {
          setStories(data.cluster_stories);
        }
      })
      .catch((err) => {
        console.error("Failed to fetch dashboard feed for narrative view:", err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [refreshKey]);

  const handleStoryChange = (updated: ClusterStory) => {
    setStories(prev => prev.map(s => s.id === updated.id ? updated : s));
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    // Calculate scroll progress from 0.0 to 1.0 based on how far down the user has scrolled
    const maxScroll = target.scrollHeight - target.clientHeight;
    if (maxScroll <= 0) {
      setScrollProgress(0);
    } else {
      setScrollProgress(Math.min(1, Math.max(0, target.scrollTop / maxScroll)));
    }
  };

  const handleFullscreen = async () => {
    if (!fullscreenContainerRef.current) return;
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await fullscreenContainerRef.current.requestFullscreen();
      }
    } catch (err) {
      console.error("Error toggling fullscreen:", err);
    }
  };

  const isLight = theme === 'light';

  return (
    <div 
      ref={fullscreenContainerRef}
      className={cn(
      "flex flex-col h-full w-full pt-3 px-4 pb-2 transition-colors duration-500 relative",
      isLight ? "bg-[#F8FAFC]" : "bg-[#050505]",
      "fullscreen:pt-3 fullscreen:px-4 fullscreen:pb-2 fullscreen:h-screen fullscreen:w-screen fullscreen:overflow-hidden"
    )}>
      {/* Global Ribbon Background for all modes and templates */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden rounded-xl">
        <RibbonBackground />
      </div>

      {/* Header - Compact layout */}
      <div className="flex items-center justify-between shrink-0 mb-2 px-1 relative z-30 min-h-[3.5rem] py-1">
        <div>
          <h1 className={cn(
            "text-lg font-bold tracking-widest uppercase transition-colors duration-300", 
            isLight ? "text-slate-900" : "text-white"
          )} 
          style={!isLight ? { textShadow: "0 0 20px rgba(0, 229, 255, 0.4)" } : {}}>
            Narrative Notebook
          </h1>
          <p className={cn("text-[10px] mt-0.5 tracking-wider", isLight ? "text-slate-500" : "text-neutral-400")}>
            Executive operational storytelling & semantic analysis
          </p>
        </div>

        {/* Center Quantum Logo Swarm Animation - Scaled for visibility */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none z-40 w-18 h-18">
          <DraggableComponent id="header_logo" defaultWidth="72px" isEditing={editMode}>
            <div 
              className={cn(
                "w-full aspect-square rounded-2xl overflow-hidden border backdrop-blur-md shadow-inner flex items-center justify-center transition-all duration-300 hover:scale-105 hover:border-white/20 select-none pointer-events-auto",
                isLight 
                  ? "bg-white/40 border-slate-200/80 shadow-slate-100" 
                  : "bg-black/20 border-white/10 shadow-black/40"
              )}
              title="du Tech Quantum Swarm"
            >
              <QuantumLogoSwarm isLight={isLight} />
            </div>
          </DraggableComponent>
        </div>

        <div className="flex items-center gap-2">
          {/* Edit Mode Toggle */}
          <button 
            onClick={() => setEditMode(!editMode)}
            className={cn(
              "p-1.5 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              editMode 
                ? "bg-rose-500 text-white border-rose-600 shadow-[0_0_8px_rgba(244,63,94,0.3)]" 
                : (isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-white/10 border-white/20 text-white")
            )}
            title={editMode ? "Exit Edit Mode" : "Enter Edit Mode"}
          >
            <Edit2 size={12} className={cn(editMode ? "animate-pulse" : "")} />
          </button>

          {/* Template Switcher */}
          <button 
            onClick={cycleTemplate}
            className={cn(
              "p-1.5 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-white/10 border-white/20 text-white"
            )}
            title={getTemplateTitle()}
          >
            {getTemplateIcon()}
          </button>

          {/* Fullscreen Toggle */}
          <button 
            onClick={handleFullscreen}
            className={cn(
              "p-1.5 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-white/10 border-white/20 text-white"
            )}
            title="Toggle Fullscreen"
          >
            <span className="text-xs leading-none">⛶</span>
          </button>

          {/* Theme Toggle */}
          <button 
            onClick={() => setTheme(isLight ? 'dark' : 'light')}
            className={cn(
              "p-1.5 rounded-full border transition-all duration-300 hover:scale-105 shadow-sm flex items-center justify-center cursor-pointer",
              isLight ? "bg-slate-100 border-slate-200 text-slate-600" : "bg-white/10 border-white/20 text-white"
            )}
            title={isLight ? "Use Dark Theme" : "Use Light Theme"}
          >
            {isLight ? <Moon size={12} /> : <Sun size={12} />}
          </button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0 relative z-10">
        <TabsList className={cn("mb-4 shrink-0 border-b", isLight ? "border-slate-200" : "border-white/10")}>
          <TabsTrigger 
            value="landing" 
            className={cn("data-[state=active]:text-cyan-500", isLight && "text-slate-500 data-[state=active]:text-cyan-600")}
          >
            Executive Brief
          </TabsTrigger>
          <TabsTrigger 
            value="cloud"
            className={cn("data-[state=active]:text-cyan-500", isLight && "text-slate-500 data-[state=active]:text-cyan-600")}
          >
            Semantic Cloud Analysis
          </TabsTrigger>
          <TabsTrigger 
            value="studio"
            className={cn("data-[state=active]:text-cyan-500", isLight && "text-slate-500 data-[state=active]:text-cyan-600")}
          >
            AR Virtual Studio
          </TabsTrigger>
        </TabsList>
        
        {/* Storytelling Canvas (Chapter Flow) */}
        <TabsContent 
          value="landing" 
          onScroll={handleScroll} 
          className={cn(
            "flex-1 min-h-0 relative",
            template === 'presentation' ? "overflow-hidden flex flex-col h-full" : "overflow-auto"
          )}
        >
          {activeTab === "landing" && (
            <div className={cn(
              "mx-auto relative z-10",
              template === 'presentation' ? "w-[96%] xl:w-[94%] h-full flex flex-col min-h-0 pb-4 pt-2" : "max-w-4xl py-8 px-4 sm:px-8"
            )}>
              {loading ? (
                <NarrativeVectorLoader isLight={isLight} />
              ) : stories.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <p className={cn("text-lg", isLight ? "text-slate-600" : "text-neutral-400")}>No curated stories found in current feed.</p>
                  <p className={cn("text-sm mt-2", isLight ? "text-slate-400" : "text-neutral-600")}>Try uploading a new dataset to generate the narrative.</p>
                </div>
              ) : template === 'presentation' ? (
                <div className="w-full h-full flex justify-center min-h-0">
                  <PresentationTemplate 
                    isLight={isLight} 
                    isPlaying={narrator.isPlaying} 
                    onPlay={(id, text, gender) => narrator.play(id, text, gender)}
                    onStop={() => narrator.pause()}
                    isEditing={editMode}
                  />
                </div>
              ) : (
                <div className="space-y-6">
                  {stories.map((story) => (
                    template === 'university' ? (
                      <UniversityTemplate 
                        key={story.id} 
                        story={story} 
                        isEditing={editMode} 
                        onStoryChange={handleStoryChange} 
                        isPlaying={narrator.activeChapterId === story.id && narrator.isPlaying}
                        onPlay={() => narrator.play(story.id, story.summary)}
                        onStop={() => narrator.pause()}
                      />
                    ) : (
                      <ChapterCard 
                        key={story.id} 
                        story={story} 
                        isLight={isLight}
                        isPlaying={narrator.activeChapterId === story.id && narrator.isPlaying}
                        onPlay={() => narrator.play(story.id, story.summary)}
                        onStop={() => narrator.pause()}
                      />
                    )
                  ))}
                </div>
              )}
            </div>
          )}
        </TabsContent>
        
        {/* The original 3D Sandbox, left fully intact */}
        <TabsContent value="cloud" className="flex-1 min-h-0 relative w-full h-full m-0 p-0 overflow-hidden rounded-xl border border-transparent">
          <div className="absolute inset-0">
            {activeTab === "cloud" && (
              <SemanticCloudView onRefresh={() => setRefreshKey(k => k + 1)} />
            )}
          </div>
        </TabsContent>

        <TabsContent value="studio" className="flex-1 min-h-0 relative w-full h-full m-0 p-0 overflow-hidden rounded-xl border border-transparent">
          <div className="absolute inset-0">
            {activeTab === "studio" && (
              <SciFiStudio />
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
