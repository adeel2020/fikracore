"use client";

import React from "react";
import {
  BookOpen,
  GitBranch,
  Network,
  BrainCircuit,
} from "lucide-react";
import { useContextView } from "./hooks/useContextView";
import { GraphViewPanel } from "./components/GraphViewPanel";
import { GraphDetailPanel } from "./components/GraphDetailPanel";
import { DocumentsPanel } from "./components/DocumentsPanel";
import { EmbeddingsPanel } from "./components/EmbeddingsPanel";
import { RagPanel } from "./components/RagPanel";

const CARDS = [
  {
    id: "documents",
    label: "KNOWLEDGE BASE",
    subtitle: "Centralized Repository of Structured Information.",
    icon: BookOpen,
    border: "border-orange-500/40",
    glow: "rgba(249,115,22,0.25)",
    bg: "hover:bg-orange-500/5",
    shadow: "shadow-orange-500/10",
  },
  {
    id: "graph",
    label: "KNOWLEDGE GRAPHS",
    subtitle: "Efficient Similarity Matching.",
    icon: GitBranch,
    border: "border-fuchsia-500/40",
    glow: "rgba(217,70,239,0.25)",
    bg: "hover:bg-fuchsia-500/5",
    shadow: "shadow-fuchsia-500/10",
  },
  {
    id: "rag",
    label: "RAG Console",
    subtitle: "Interconnected entities and concepts.",
    icon: Network,
    border: "border-cyan-400/40",
    glow: "rgba(34,211,238,0.25)",
    bg: "hover:bg-cyan-400/5",
    shadow: "shadow-cyan-400/10",
  },
  {
    id: "embeddings",
    label: "AI AGENTS",
    subtitle: "Autonomous Decision-Making and Tool Use.",
    icon: BrainCircuit,
    border: "border-yellow-400/40",
    glow: "rgba(250,204,21,0.25)",
    bg: "hover:bg-yellow-400/5",
    shadow: "shadow-yellow-400/10",
  },
];

export function ContextView() {
  const {
    loading,
    fgRef,
    containerRef,
    fileInputRef,
    nodes,
    links,
    focusedNode,
    setFocusedNode,
    copied,
    showIntentCatalog,
    setShowIntentCatalog,
    selectedIntentWorkflow,
    setSelectedIntentWorkflow,
    copiedWorkflow,
    setCopiedWorkflow,
    activeTab,
    setActiveTab,
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
    currentContextPayload,
    handleCopy,
    guidance,
  } = useContextView();

  return (
    <div className="w-full">
      {/* Widget-style Card Navigation */}
      <div className="bg-neutral-950/60 rounded-2xl border border-white/5 p-4 mb-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {CARDS.map((card) => {
            const Icon = card.icon;
            const active = activeTab === card.id;
            return (
              <button
                key={card.id}
                onClick={() => setActiveTab(card.id)}
                className={[
                  "group relative flex flex-col gap-2 p-3.5 rounded-xl border backdrop-blur-md transition-all duration-300 text-left",
                  active
                    ? `${card.border} ${card.bg} bg-neutral-900/90`
                    : "border-white/5 bg-neutral-950/40 hover:border-white/10 hover:bg-white/[0.02]",
                  active ? `shadow-[0_0_18px_${card.glow}]` : "",
                ].join(" ")}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={[
                      "flex items-center justify-center h-9 w-9 rounded-lg border shrink-0 transition-all duration-300",
                      active ? card.border : "border-white/5",
                      "bg-neutral-900/80",
                    ].join(" ")}
                  >
                    <Icon className={[
                      "h-[18px] w-[18px] transition-colors duration-300",
                      active ? "text-white" : "text-neutral-500 group-hover:text-neutral-300",
                    ].join(" ")} />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className={[
                      "text-xs font-bold uppercase tracking-wider transition-colors duration-300",
                      active ? "text-white" : "text-neutral-500 group-hover:text-neutral-300",
                    ].join(" ")}>
                      {card.label}
                    </span>
                    <span className={[
                      "text-[10px] leading-relaxed transition-colors duration-300 truncate",
                      active ? "text-neutral-400" : "text-neutral-600 group-hover:text-neutral-500",
                    ].join(" ")}>
                      {card.subtitle}
                    </span>
                  </div>
                  {active && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.6)] shrink-0" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Panel Content */}
      {activeTab === "graph" && (
        <div className="relative h-[680px] w-full">
          {loading && (
            <div className="absolute inset-0 z-20 flex items-center justify-center rounded-2xl border border-white/5 bg-neutral-950/80 backdrop-blur-md">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
                <span className="text-xs font-semibold text-neutral-400 uppercase tracking-widest">
                  Loading Knowledge Graph...
                </span>
              </div>
            </div>
          )}
          <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 h-full w-full overflow-hidden select-none ${loading ? "opacity-40 pointer-events-none" : ""}`}>
            <GraphViewPanel
              fgRef={fgRef}
              containerRef={containerRef}
              fileInputRef={fileInputRef}
              nodes={nodes}
              links={links}
              focusedNode={focusedNode}
              setFocusedNode={setFocusedNode}
              showIntentCatalog={showIntentCatalog}
              setShowIntentCatalog={setShowIntentCatalog}
              selectedIntentWorkflow={selectedIntentWorkflow}
              setSelectedIntentWorkflow={setSelectedIntentWorkflow}
              copiedWorkflow={copiedWorkflow}
              setCopiedWorkflow={setCopiedWorkflow}
              dimensions={dimensions}
              selectedNodeType={selectedNodeType}
              setSelectedNodeType={setSelectedNodeType}
              isExpanded={isExpanded}
              setIsExpanded={setIsExpanded}
              activeTheme={activeTheme}
              changeTheme={changeTheme}
              nodeStyle={nodeStyle}
              changeStyle={changeStyle}
              showThemeCatalog={showThemeCatalog}
              setShowThemeCatalog={setShowThemeCatalog}
              showStyleCatalog={showStyleCatalog}
              setShowStyleCatalog={setShowStyleCatalog}
              layoutMode={layoutMode}
              changeLayoutMode={changeLayoutMode}
              showClusterCatalog={showClusterCatalog}
              setShowClusterCatalog={setShowClusterCatalog}
              showExportCatalog={showExportCatalog}
              setShowExportCatalog={setShowExportCatalog}
              handleDownload={handleDownload}
              triggerUpload={triggerUpload}
              handleFileUpload={handleFileUpload}
              graphData={graphData}
              currentTheme={currentTheme}
              handleNodeClick={handleNodeClick}
              handleZoomIn={handleZoomIn}
              handleZoomOut={handleZoomOut}
              handleZoomToFit={handleZoomToFit}
              toggleThemeCatalog={toggleThemeCatalog}
              toggleStyleCatalog={toggleStyleCatalog}
              toggleClusterCatalog={toggleClusterCatalog}
              toggleExportCatalog={toggleExportCatalog}
              isLinkConnected={isLinkConnected}
              isLinkOfSelectedType={isLinkOfSelectedType}
            />

            {!isExpanded && (
              <GraphDetailPanel
                focusedNode={focusedNode}
                currentTheme={currentTheme}
                guidance={guidance}
                currentContextPayload={currentContextPayload}
                copied={copied}
                handleCopy={handleCopy}
              />
            )}
          </div>
        </div>
      )}

      {activeTab === "documents" && (
        <div className="h-[680px] overflow-y-auto">
          <DocumentsPanel />
        </div>
      )}

      {activeTab === "embeddings" && (
        <div className="h-[680px] overflow-y-auto">
          <EmbeddingsPanel />
        </div>
      )}

      {activeTab === "rag" && <RagPanel />}
    </div>
  );
}
export default ContextView;
