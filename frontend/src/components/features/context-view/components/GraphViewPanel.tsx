"use client";

import React, { useMemo } from "react";
import dynamic from "next/dynamic";
import {
  Loader2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Palette,
  Layers,
  Network,
  ArrowUpDown,
  Workflow,
  X,
  FileJson,
  FileText,
  Upload,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { GraphNode, GraphLink, ThemeConfig } from "../types/context.types";
import { INTENT_WORKFLOWS, THEMES } from "./shared/constants";
import { createNodeCanvasObject, createLinkCanvasObject } from "./shared/canvas-helpers";

const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d").then((mod) => mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full min-h-[450px] w-full flex-col items-center justify-center gap-3 bg-neutral-950/20 rounded-2xl border border-white/5 backdrop-blur-md">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-400" />
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-widest">
          Initializing Force Graph Engine...
        </span>
      </div>
    ),
  }
);

interface GraphViewPanelProps {
  fgRef: React.RefObject<any>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  nodes: GraphNode[];
  links: GraphLink[];
  focusedNode: GraphNode | null;
  setFocusedNode: (node: GraphNode | null) => void;
  showIntentCatalog: boolean;
  setShowIntentCatalog: React.Dispatch<React.SetStateAction<boolean>>;
  selectedIntentWorkflow: string | null;
  setSelectedIntentWorkflow: React.Dispatch<React.SetStateAction<string | null>>;
  copiedWorkflow: boolean;
  setCopiedWorkflow: React.Dispatch<React.SetStateAction<boolean>>;
  dimensions: { width: number; height: number };
  selectedNodeType: string | null;
  setSelectedNodeType: React.Dispatch<React.SetStateAction<string | null>>;
  isExpanded: boolean;
  setIsExpanded: React.Dispatch<React.SetStateAction<boolean>>;
  activeTheme: string;
  changeTheme: (theme: string) => void;
  nodeStyle: "classic" | "glyphs" | "badges" | "geometry" | "bubble" | "crystal";
  changeStyle: (
    style: "classic" | "glyphs" | "badges" | "geometry" | "bubble" | "crystal"
  ) => void;
  showThemeCatalog: boolean;
  setShowThemeCatalog: React.Dispatch<React.SetStateAction<boolean>>;
  showStyleCatalog: boolean;
  setShowStyleCatalog: React.Dispatch<React.SetStateAction<boolean>>;
  layoutMode: "standard" | "synapses" | "orbit" | "pods" | "spoke";
  changeLayoutMode: (mode: "standard" | "synapses" | "orbit" | "pods" | "spoke") => void;
  showClusterCatalog: boolean;
  setShowClusterCatalog: React.Dispatch<React.SetStateAction<boolean>>;
  showExportCatalog: boolean;
  setShowExportCatalog: React.Dispatch<React.SetStateAction<boolean>>;
  handleDownload: (format: "json" | "markdown") => void;
  triggerUpload: (format: "json" | "markdown") => void;
  handleFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  graphData: { nodes: GraphNode[]; links: GraphLink[] };
  currentTheme: ThemeConfig;
  handleNodeClick: (node: any) => void;
  handleZoomIn: () => void;
  handleZoomOut: () => void;
  handleZoomToFit: () => void;
  toggleThemeCatalog: () => void;
  toggleStyleCatalog: () => void;
  toggleClusterCatalog: () => void;
  toggleExportCatalog: () => void;
  isLinkConnected: (link: any) => boolean;
  isLinkOfSelectedType: (link: any) => boolean;
}

export const GraphViewPanel: React.FC<GraphViewPanelProps> = ({
  fgRef,
  containerRef,
  fileInputRef,
  nodes,
  links,
  focusedNode,
  setFocusedNode,
  showIntentCatalog,
  setShowIntentCatalog,
  selectedIntentWorkflow,
  setSelectedIntentWorkflow,
  copiedWorkflow,
  setCopiedWorkflow,
  dimensions,
  selectedNodeType,
  setSelectedNodeType,
  isExpanded,
  setIsExpanded,
  activeTheme,
  changeTheme,
  nodeStyle,
  changeStyle,
  showThemeCatalog,
  setShowThemeCatalog,
  showStyleCatalog,
  setShowStyleCatalog,
  layoutMode,
  changeLayoutMode,
  showClusterCatalog,
  setShowClusterCatalog,
  showExportCatalog,
  setShowExportCatalog,
  handleDownload,
  triggerUpload,
  handleFileUpload,
  graphData,
  currentTheme,
  handleNodeClick,
  handleZoomIn,
  handleZoomOut,
  handleZoomToFit,
  toggleThemeCatalog,
  toggleStyleCatalog,
  toggleClusterCatalog,
  toggleExportCatalog,
  isLinkConnected,
  isLinkOfSelectedType,
}) => {
  const nodeCanvasObject = useMemo(() => {
    return createNodeCanvasObject(
      focusedNode,
      selectedNodeType,
      nodeStyle,
      currentTheme,
      layoutMode
    );
  }, [focusedNode, selectedNodeType, nodeStyle, currentTheme, layoutMode]);

  const linkCanvasObject = useMemo(() => {
    return createLinkCanvasObject(
      focusedNode,
      selectedNodeType,
      currentTheme,
      layoutMode,
      nodes,
      nodeStyle
    );
  }, [focusedNode, selectedNodeType, currentTheme, layoutMode, nodes, nodeStyle]);

  return (
    <div
      className={`${
        isExpanded ? "lg:col-span-3" : "lg:col-span-2"
      } relative border transition-all duration-300 ease-in-out rounded-2xl overflow-hidden h-full flex flex-col ${
        currentTheme.isDark ? "border-white/5 bg-neutral-950" : "border-slate-200 bg-white"
      }`}
      style={{
        backgroundColor: currentTheme.isDark ? "#0A0A0A" : "#FFFFFF",
        backgroundImage: currentTheme.gridBackground,
        backgroundSize: "100% 100%, 100% 100%, 100% 100%, 100% 100%, 30px 30px, 30px 30px",
        backgroundPosition: "center",
      }}
    >
      {/* Canvas Floating Zoom & Expand Controls */}
      <div className="absolute top-4 right-4 z-20 flex gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomIn}
          title="Zoom In"
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomOut}
          title="Zoom Out"
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomToFit}
          title="Fit to View"
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleThemeCatalog}
          title={`Theme: ${currentTheme.name} (Click to select)`}
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            showThemeCatalog
              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
              : currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <Palette className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleStyleCatalog}
          title={`Node Style: ${nodeStyle.toUpperCase()} (Click to select)`}
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            showStyleCatalog
              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
              : currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <Layers className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleClusterCatalog}
          title={`Layout: ${layoutMode.toUpperCase()} (Click to select)`}
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            showClusterCatalog
              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
              : currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <Network className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleExportCatalog}
          disabled={!graphData.nodes || graphData.nodes.length === 0}
          title="Import & Export Graph Data"
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            showExportCatalog
              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
              : currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <ArrowUpDown className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            setShowIntentCatalog((prev) => !prev);
            setShowThemeCatalog(false);
            setShowStyleCatalog(false);
            setShowClusterCatalog(false);
            setShowExportCatalog(false);
          }}
          title="Intent Workflows Catalog"
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            showIntentCatalog
              ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
              : currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          <Workflow className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsExpanded(!isExpanded)}
          title={isExpanded ? "Minimize View" : "Maximize View"}
          className={`h-8 w-8 hover:bg-cyan-500/10 hover:text-cyan-400 border backdrop-blur-sm transition-all ${
            currentTheme.isDark
              ? "bg-neutral-900/60 border-white/5 text-neutral-300"
              : "bg-white/70 border-black/10 text-slate-700"
          }`}
        >
          {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </Button>
      </div>

      {/* Left Sidebar Intent Catalog */}
      {showIntentCatalog && (
        <div
          className={`absolute top-4 left-4 bottom-4 z-30 w-72 rounded-xl border p-4 shadow-2xl backdrop-blur-md flex flex-col gap-4 animate-in fade-in slide-in-from-left-2 duration-250 ${
            currentTheme.isDark
              ? "border-white/10 bg-neutral-950/95 text-white"
              : "border-black/10 bg-white/95 text-slate-900"
          }`}
        >
          <div className="flex items-center justify-between border-b border-white/10 pb-2">
            <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-cyan-400">
              <Workflow className="h-3.5 w-3.5" />
              Intents Catalog
            </h4>
            <button
              onClick={() => setShowIntentCatalog(false)}
              className={`text-[10px] font-mono hover:text-white px-1.5 py-0.5 rounded transition-all ${
                currentTheme.isDark
                  ? "text-neutral-400 bg-white/5 hover:bg-white/10"
                  : "text-slate-500 bg-slate-100 hover:bg-slate-200"
              }`}
            >
              Close
            </button>
          </div>

          <div className="flex flex-col gap-2 overflow-y-auto flex-1 pr-1 scrollbar-none">
            {Object.keys(INTENT_WORKFLOWS).map((intentKey) => {
              const workflow = INTENT_WORKFLOWS[intentKey];
              const isSelected = selectedIntentWorkflow === intentKey;

              return (
                <button
                  key={intentKey}
                  onClick={() => {
                    setSelectedIntentWorkflow(intentKey);
                    const matchingNode = nodes.find((n) => n.id === intentKey);
                    if (matchingNode) {
                      handleNodeClick(matchingNode);
                    }
                  }}
                  className={`flex items-center gap-3 w-full p-3 rounded-lg border text-left transition-all ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-400"
                      : currentTheme.isDark
                      ? "bg-white/5 border-white/5 hover:bg-white/10 text-neutral-300 hover:text-white"
                      : "bg-slate-550/5 border-slate-100 hover:bg-slate-100 text-slate-700 hover:text-slate-900"
                  }`}
                >
                  <span className="h-4 w-4 shrink-0 text-cyan-400">❓</span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs font-bold">{workflow.label}</span>
                    <span className="text-[9px] text-neutral-450 uppercase tracking-widest">
                      {intentKey.replace("intent_", "")}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Detached Intent Workflow Panel */}
      {selectedIntentWorkflow && INTENT_WORKFLOWS[selectedIntentWorkflow] && (
        <div
          className={`absolute top-4 right-4 lg:right-20 bottom-4 z-30 w-[380px] rounded-xl border p-5 shadow-2xl backdrop-blur-md flex flex-col gap-4 animate-in fade-in slide-in-from-right-2 duration-250 ${
            currentTheme.isDark
              ? "border-white/10 bg-neutral-950/95 text-white"
              : "border-black/10 bg-white/95 text-slate-900"
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
            <div className="flex items-center gap-2">
              <Workflow className="h-4 w-4 text-cyan-400" />
              <h4 className="text-xs font-bold uppercase tracking-wider">
                Logical Flow Workflow
              </h4>
            </div>
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  const flow = INTENT_WORKFLOWS[selectedIntentWorkflow];
                  const yamlString = `intent: ${selectedIntentWorkflow}
label: "${flow.label}"
channels:
${flow.channels.map((c) => `  - "${c}"`).join("\n")}
prechecks:
${flow.prechecks.map((p) => `  - "${p}"`).join("\n")}
dependencies:
${flow.dependencies.map((d) => `  - "${d}"`).join("\n")}
escalation_target: "${flow.target}"
prohibited_routes:
${flow.prohibited.map((pr) => `  - "${pr}"`).join("\n")}
fallback_domain: "${flow.fallback}"`;
                  navigator.clipboard.writeText(yamlString);
                  setCopiedWorkflow(true);
                  setTimeout(() => setCopiedWorkflow(false), 2000);
                }}
                className="h-6 px-2 text-[10px] text-neutral-450 hover:text-cyan-400 border border-white/5 bg-neutral-900/40"
              >
                {copiedWorkflow ? (
                  <Check className="h-3 w-3 text-emerald-400 mr-1" />
                ) : (
                  <Copy className="h-3 w-3 mr-1" />
                )}
                {copiedWorkflow ? "Copied" : "Copy YAML"}
              </Button>
              <button
                onClick={() => setSelectedIntentWorkflow(null)}
                className="p-1 hover:bg-white/10 rounded transition-all text-neutral-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Sub-header Title */}
          <div>
            <h3 className="text-sm font-bold text-cyan-400">
              {INTENT_WORKFLOWS[selectedIntentWorkflow].label}
            </h3>
            <p className="text-[10px] text-neutral-450 mt-1 leading-relaxed">
              {INTENT_WORKFLOWS[selectedIntentWorkflow].description}
            </p>
          </div>

          {/* Timeline Flow */}
          <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-4 scrollbar-none my-1">
            {/* Step 1: Intake Channels */}
            <div className="flex gap-3 relative">
              <div className="flex flex-col items-center">
                <div className="h-5 w-5 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-[10px] font-bold text-cyan-400 z-10">
                  1
                </div>
                <div className="w-0.5 flex-1 bg-white/10 my-1"></div>
              </div>
              <div className="flex-1 pb-2">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block">
                  Intake Channels
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {INTENT_WORKFLOWS[selectedIntentWorkflow].channels.map((chan, idx) => (
                    <span
                      key={idx}
                      className="text-[9px] bg-cyan-950/40 border border-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full font-semibold"
                    >
                      {chan}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 2: Prechecks */}
            <div className="flex gap-3 relative">
              <div className="flex flex-col items-center">
                <div className="h-5 w-5 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-[10px] font-bold text-cyan-400 z-10">
                  2
                </div>
                <div className="w-0.5 flex-1 bg-white/10 my-1"></div>
              </div>
              <div className="flex-1 pb-2">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block">
                  Mandatory Pre-Checks
                </span>
                <div className="flex flex-col gap-1.5 mt-1.5">
                  {INTENT_WORKFLOWS[selectedIntentWorkflow].prechecks.map((pre, idx) => (
                    <div key={idx} className="flex gap-2 items-start text-[10px]">
                      <span className="text-cyan-400 text-xs mt-0.5 font-bold">•</span>
                      <span className={currentTheme.isDark ? "text-neutral-300" : "text-slate-700"}>
                        {pre}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 3: Wallet Dependencies */}
            <div className="flex gap-3 relative">
              <div className="flex flex-col items-center">
                <div className="h-5 w-5 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-[10px] font-bold text-cyan-400 z-10">
                  3
                </div>
                <div className="w-0.5 flex-1 bg-white/10 my-1"></div>
              </div>
              <div className="flex-1 pb-2">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block">
                  Wallet / Benefit Dependencies
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {INTENT_WORKFLOWS[selectedIntentWorkflow].dependencies.map((dep, idx) => (
                    <span
                      key={idx}
                      className="text-[9px] bg-neutral-900/60 border border-white/5 text-neutral-300 px-2 py-0.5 rounded font-mono"
                    >
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Step 4: Routing Escalation */}
            <div className="flex gap-3 relative">
              <div className="flex flex-col items-center">
                <div className="h-5 w-5 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center text-[10px] font-bold text-cyan-400 z-10">
                  4
                </div>
              </div>
              <div className="flex-1">
                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block">
                  Escalation Routing
                </span>

                <div className="mt-2 text-[10px]">
                  <span className="font-bold text-neutral-450 uppercase text-[9px] block">
                    Target Team:
                  </span>
                  <span className="text-emerald-450 font-semibold text-xs mt-0.5 block">
                    {INTENT_WORKFLOWS[selectedIntentWorkflow].target}
                  </span>
                </div>

                {INTENT_WORKFLOWS[selectedIntentWorkflow].prohibited.length > 0 && (
                  <div className="mt-2 text-[10px]">
                    <span className="font-bold text-neutral-450 uppercase text-[9px] block">
                      Prohibited Routes (SLA Risk):
                    </span>
                    <span className="text-rose-450 font-semibold mt-0.5 block">
                      {INTENT_WORKFLOWS[selectedIntentWorkflow].prohibited.join(", ")}
                    </span>
                  </div>
                )}

                <div className="mt-2 text-[10px]">
                  <span className="font-bold text-neutral-450 uppercase text-[9px] block">
                    Fallback Domain:
                  </span>
                  <span className="text-neutral-300 mt-0.5 block font-medium">
                    {INTENT_WORKFLOWS[selectedIntentWorkflow].fallback}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Floating Selection Catalogs */}
      {showThemeCatalog && (
        <div className="absolute top-14 right-4 z-30 w-64 rounded-xl border border-white/10 bg-neutral-950/95 p-4 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
            <h4 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-1.5">
              <Palette className="h-3.5 w-3.5 text-cyan-400" />
              Select Theme
            </h4>
            <button
              onClick={() => setShowThemeCatalog(false)}
              className="text-[10px] font-mono text-neutral-400 hover:text-white bg-white/5 hover:bg-white/10 px-1.5 py-0.5 rounded transition-all"
            >
              Close
            </button>
          </div>
          <div className="flex flex-col gap-1.5 max-h-[380px] overflow-y-auto pr-0.5 scrollbar-none">
            {Object.keys(THEMES).map((themeKey) => {
              const theme = THEMES[themeKey];
              const isSelected = activeTheme === themeKey;
              return (
                <button
                  key={themeKey}
                  onClick={() => {
                    changeTheme(themeKey);
                  }}
                  className={`flex flex-col gap-1.5 w-full p-2.5 rounded-lg border text-left transition-all ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500/40 text-white"
                      : "bg-white/5 border-white/5 hover:bg-white/10 text-neutral-300 hover:text-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{theme.name}</span>
                    {isSelected && (
                      <span className="text-[9px] text-cyan-400 font-mono font-bold">ACTIVE</span>
                    )}
                  </div>
                  {/* Preview colors */}
                  <div className="flex gap-1.5">
                    {Object.values(theme.nodeColors)
                      .slice(0, 5)
                      .map((color, idx) => (
                        <span
                          key={idx}
                          className="h-2.5 w-2.5 rounded-full border border-black/20"
                          style={{ backgroundColor: color }}
                        />
                      ))}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {showStyleCatalog && (
        <div className="absolute top-14 right-4 z-30 w-64 rounded-xl border border-white/10 bg-neutral-950/95 p-4 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
            <h4 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-cyan-400" />
              Select Node Style
            </h4>
            <button
              onClick={() => setShowStyleCatalog(false)}
              className="text-[10px] font-mono text-neutral-400 hover:text-white bg-white/5 hover:bg-white/10 px-1.5 py-0.5 rounded transition-all"
            >
              Close
            </button>
          </div>
          <div className="flex flex-col gap-1.5 max-h-[380px] overflow-y-auto pr-0.5 scrollbar-none">
            {[
              { id: "classic", name: "Classic Dot", desc: "Small colored core within circular boundaries" },
              { id: "glyphs", name: "Unicode Glyphs", desc: "Centered symbols inside rings indicating role type" },
              { id: "badges", name: "Neo4j Pill Badges", desc: "Text labels drawn directly inside capsule pills" },
              { id: "geometry", name: "Geometric Shapes", desc: "Diamonds, hexagons, squares, triangles based on category" },
              { id: "bubble", name: "Bubble Style", desc: "Shiny 3D sphere bubbles with specular gloss reflections" },
              { id: "crystal", name: "Crystal Style", desc: "Faceted hexagonal glass prisms with internal reflection lines" },
            ].map((style) => {
              const isSelected = nodeStyle === style.id;
              return (
                <button
                  key={style.id}
                  onClick={() => {
                    changeStyle(style.id as any);
                  }}
                  className={`flex flex-col gap-0.5 w-full p-2.5 rounded-lg border text-left transition-all ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500/40 text-white"
                      : "bg-white/5 border-white/5 hover:bg-white/10 text-neutral-300 hover:text-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{style.name}</span>
                    {isSelected && (
                      <span className="text-[9px] text-cyan-400 font-mono font-bold">ACTIVE</span>
                    )}
                  </div>
                  <span className="text-[10px] text-neutral-400 leading-normal">{style.desc}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {showClusterCatalog && (
        <div className="absolute top-14 right-4 z-30 w-64 rounded-xl border border-white/10 bg-neutral-950/95 p-4 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
            <h4 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-1.5">
              <Network className="h-3.5 w-3.5 text-cyan-400" />
              Select Layout Mode
            </h4>
            <button
              onClick={() => setShowClusterCatalog(false)}
              className="text-[10px] font-mono text-neutral-400 hover:text-white bg-white/5 hover:bg-white/10 px-1.5 py-0.5 rounded transition-all"
            >
              Close
            </button>
          </div>
          <div className="flex flex-col gap-1.5 max-h-[380px] overflow-y-auto pr-0.5 scrollbar-none">
            {[
              {
                id: "synapses",
                name: "Neural Synapses",
                desc: "Category groups around + / - hubs, with curved synapse signals (Default)",
              },
              {
                id: "pods",
                name: "Category Pods",
                desc: "8 dense, separated modular clusters positioned around the canvas",
              },
              {
                id: "spoke",
                name: "Parent-Spoke",
                desc: "Starburst fanning layout showing leaf connections around parent nodes",
              },
              {
                id: "orbit",
                name: "Category Orbit",
                desc: "Radar-like concentric orbits representing ontology layers",
              },
              {
                id: "standard",
                name: "Standard Force",
                desc: "Original flat, unclustered force-directed layout",
              },
            ].map((layout) => {
              const isSelected = layoutMode === layout.id;
              return (
                <button
                  key={layout.id}
                  onClick={() => {
                    changeLayoutMode(layout.id as any);
                  }}
                  className={`flex flex-col gap-0.5 w-full p-2.5 rounded-lg border text-left transition-all ${
                    isSelected
                      ? "bg-cyan-500/10 border-cyan-500/40 text-white"
                      : "bg-white/5 border-white/5 hover:bg-white/10 text-neutral-300 hover:text-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{layout.name}</span>
                    {isSelected && (
                      <span className="text-[9px] text-cyan-400 font-mono font-bold">ACTIVE</span>
                    )}
                  </div>
                  <span className="text-[10px] text-neutral-400 leading-normal">{layout.desc}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {showExportCatalog && (
        <div className="absolute top-14 right-4 z-30 w-64 rounded-xl border border-white/10 bg-neutral-950/95 p-4 shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
            <h4 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-1.5">
              <ArrowUpDown className="h-3.5 w-3.5 text-cyan-400" />
              Import & Export Graph
            </h4>
            <button
              onClick={() => setShowExportCatalog(false)}
              className="text-[10px] font-mono text-neutral-400 hover:text-white bg-white/5 hover:bg-white/10 px-1.5 py-0.5 rounded transition-all"
            >
              Close
            </button>
          </div>

          <div className="flex flex-col gap-3">
            {/* Download Options */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500">
                Download (Export)
              </span>
              <button
                onClick={() => {
                  handleDownload("json");
                  setShowExportCatalog(false);
                }}
                disabled={!graphData.nodes || graphData.nodes.length === 0}
                className="flex items-center gap-2.5 w-full p-2.5 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:pointer-events-none text-neutral-300 hover:text-white text-left transition-all"
              >
                <FileJson className="h-4 w-4 text-cyan-400 shrink-0" />
                <div className="flex flex-col">
                  <span className="text-xs font-bold">Download JSON</span>
                  <span className="text-[10px] text-neutral-400">Raw nodes & links payload</span>
                </div>
              </button>
              <button
                onClick={() => {
                  handleDownload("markdown");
                  setShowExportCatalog(false);
                }}
                disabled={!graphData.nodes || graphData.nodes.length === 0}
                className="flex items-center gap-2.5 w-full p-2.5 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 disabled:opacity-50 disabled:pointer-events-none text-neutral-300 hover:text-white text-left transition-all"
              >
                <FileText className="h-4 w-4 text-cyan-400 shrink-0" />
                <div className="flex flex-col">
                  <span className="text-xs font-bold">Download Triplets (MD)</span>
                  <span className="text-[10px] text-neutral-400">
                    Formatted semantic triplets document
                  </span>
                </div>
              </button>
            </div>

            {/* Upload Options */}
            <div className="flex flex-col gap-1.5 border-t border-white/5 pt-2.5">
              <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500">
                Upload (Import)
              </span>
              <button
                onClick={() => {
                  triggerUpload("json");
                  setShowExportCatalog(false);
                }}
                className="flex items-center gap-2.5 w-full p-2.5 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 text-neutral-300 hover:text-white text-left transition-all"
              >
                <Upload className="h-4 w-4 text-lime-400 shrink-0" />
                <div className="flex flex-col">
                  <span className="text-xs font-bold">Upload JSON</span>
                  <span className="text-[10px] text-neutral-400">Load from graph JSON file</span>
                </div>
              </button>
              <button
                onClick={() => {
                  triggerUpload("markdown");
                  setShowExportCatalog(false);
                }}
                className="flex items-center gap-2.5 w-full p-2.5 rounded-lg border border-white/5 bg-white/5 hover:bg-white/10 text-neutral-300 hover:text-white text-left transition-all"
              >
                <FileText className="h-4 w-4 text-lime-400 shrink-0" />
                <div className="flex flex-col">
                  <span className="text-xs font-bold">Upload Triplets (MD)</span>
                  <span className="text-[10px] text-neutral-400">Load from MD triplets list</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Force Graph Canvas Area */}
      <div className="flex-1 w-full h-full relative" ref={containerRef}>
        {dimensions.width > 0 && dimensions.height > 0 && (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeCanvasObject={nodeCanvasObject}
            nodePointerAreaPaint={(node: any, color, ctx) => {
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(node.x, node.y, node.isHub ? 20 : 14, 0, 2 * Math.PI, false);
              ctx.fill();
            }}
            onNodeClick={handleNodeClick}
            onBackgroundClick={() => {
              setShowThemeCatalog(false);
              setShowStyleCatalog(false);
              setShowClusterCatalog(false);
              setShowExportCatalog(false);
              setShowIntentCatalog(false);
            }}
            linkColor={(link: any) => {
              if (layoutMode === "synapses") {
                if (link.isHubLink) {
                  return currentTheme.isDark
                    ? "rgba(255, 255, 255, 0.08)"
                    : "rgba(0, 0, 0, 0.07)";
                }
                return "transparent";
              }
              const isConnected = isLinkConnected(link);
              const isSelected = isLinkOfSelectedType(link);
              if (isConnected) {
                return currentTheme.nodeColors[focusedNode?.type || ""] || "#FFFFFF";
              }
              if (selectedNodeType) {
                return isSelected
                  ? currentTheme.inactiveLinkColor
                  : "rgba(255, 255, 255, 0.08)";
              }
              return currentTheme.inactiveLinkColor;
            }}
            linkWidth={(link: any) => {
              if (layoutMode === "synapses") {
                if (link.isHubLink) return 0.8;
                const isConnected = isLinkConnected(link);
                return isConnected ? 5.5 : 3.0;
              }
              const isConnected = isLinkConnected(link);
              const isSelected = isLinkOfSelectedType(link);
              if (isConnected) return 2.8;
              if (selectedNodeType && !isSelected) return 0.5;
              return 1.5;
            }}
            linkCanvasObject={linkCanvasObject}
            linkCanvasObjectMode={() => "after"}
            linkCurvature={(link: any) => {
              if (layoutMode === "synapses") {
                return link.isHubLink ? 0 : 0.35;
              }
              if (layoutMode === "orbit") {
                return 0.15;
              }
              return 0;
            }}
            linkDirectionalArrowLength={(link: any) => {
              if (layoutMode === "synapses" && link.isHubLink) return 0;
              return isLinkConnected(link) ? 6 : 4.5;
            }}
            linkDirectionalArrowRelPos={1}
            linkDirectionalParticles={(link: any) => {
              if (layoutMode === "synapses") {
                if (link.isHubLink) return 0;
                return isLinkConnected(link) ? 5 : 2;
              }
              if (isLinkConnected(link)) return 4;
              if (selectedNodeType && !isLinkOfSelectedType(link)) return 0;
              return 1;
            }}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleColor={(link: any) => {
              if (layoutMode === "synapses") {
                return "#CCFF00";
              }
              return isLinkConnected(link)
                ? currentTheme.nodeColors[focusedNode?.type || ""] || "#FFFFFF"
                : currentTheme.inactiveLinkColor;
            }}
            linkDirectionalParticleWidth={(link: any) => (layoutMode === "synapses" ? 2.5 : 1.8)}
            cooldownTicks={120}
          />
        )}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          className="hidden"
          accept=".json,.md,.txt"
        />
      </div>

      {/* Interactive Node Legend Panel */}
      <div className="absolute bottom-4 left-4 z-20 flex flex-wrap gap-2 max-w-[75%] pointer-events-auto">
        {Object.keys(currentTheme.nodeColors).map((type) => {
          const isActive = selectedNodeType === type;
          const isAnyActive = selectedNodeType !== null;
          const color = currentTheme.nodeColors[type];

          return (
            <button
              key={type}
              onClick={() => setSelectedNodeType(isActive ? null : type)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-bold tracking-wide transition-all backdrop-blur-sm select-none ${
                isActive
                  ? currentTheme.isDark
                    ? "bg-neutral-900/90 shadow-[0_0_12px_rgba(255,255,255,0.05)] border-white/20"
                    : "bg-white/90 shadow-[0_0_12px_rgba(0,0,0,0.05)] border-black/20"
                  : isAnyActive
                  ? currentTheme.isDark
                    ? "bg-neutral-950/40 border-white/5 text-neutral-500 opacity-30 hover:opacity-60"
                    : "bg-white/30 border-black/5 text-neutral-400 opacity-35 hover:opacity-65"
                  : currentTheme.isDark
                  ? "bg-neutral-950/60 border-white/10 hover:bg-neutral-900/80 text-neutral-300"
                  : "bg-white/60 border-black/10 hover:bg-slate-50/80 text-slate-700"
              }`}
              style={{
                color: isAnyActive && !isActive ? undefined : color,
                borderColor: isActive ? color : undefined,
                boxShadow: isActive ? `0 0 10px ${color}44` : undefined,
              }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
              {type}
            </button>
          );
        })}
      </div>
    </div>
  );
};
