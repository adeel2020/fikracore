"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { GitBranch, Globe, Layers, Orbit, RefreshCw, RotateCcw, Tags, ZoomIn, ZoomOut } from "lucide-react";
import ScatterCanvas from "./scatter-canvas/ScatterCanvas";
import type { ZoomActions } from "./scatter-canvas/ScatterCanvas";
import KnowledgeGraph from "./knowledge-graph/KnowledgeGraph";
import type { KGActions } from "./knowledge-graph/KnowledgeGraph";
import StorytellerChat from "./storyteller-chat/StorytellerChat";
import type { ClusteringDimension, ViewMode } from "./types/semantic-cloud.types";
import { API_BASE } from "@/lib/api/config";

const glassSurface: React.CSSProperties = {
  background: "rgba(5, 5, 5, 0.58)",
  backdropFilter: "blur(18px)",
  WebkitBackdropFilter: "blur(18px)",
  border: "1px solid rgba(255,255,255,0.10)",
  boxShadow: "0 20px 60px rgba(0,0,0,0.45)",
};

const controlBase: React.CSSProperties = {
  fontFamily: "'Geist Mono', 'SF Mono', monospace",
  fontSize: 9,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  padding: "8px 11px",
  borderRadius: 10,
  border: "1px solid transparent",
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  cursor: "pointer",
  transition: "all 160ms ease",
  whiteSpace: "nowrap",
};

const activeControl: React.CSSProperties = {
  ...controlBase,
  background: "rgba(255,255,255,0.10)",
  borderColor: "rgba(255,255,255,0.14)",
  color: "#FFFFFF",
};

const inactiveControl: React.CSSProperties = {
  ...controlBase,
  background: "transparent",
  borderColor: "transparent",
  color: "rgba(255,255,255,0.68)",
};

const zoomBtnBase: React.CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 8,
  border: "1px solid rgba(255,255,255,0.10)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
  color: "rgba(255,255,255,0.72)",
  transition: "color 140ms ease",
  background: "rgba(5, 5, 5, 0.58)",
  backdropFilter: "blur(18px)",
  WebkitBackdropFilter: "blur(18px)",
};

export default function SemanticCloudView({ onRefresh }: { onRefresh?: () => void } = {}) {
  const [refreshKey, setRefreshKey] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("global");
  const [clusteringDimension, setClusteringDimension] = useState<ClusteringDimension>("reason");
  const [isGraph, setIsGraph] = useState(false);
  const [semanticMode, setSemanticMode] = useState(false);
  const [is3DMode, setIs3DMode] = useState(false);
  const [focusedCluster, setFocusedCluster] = useState<string | null>(null);
  const [palette, setPalette] = useState<[string, string][] | null>(null);
  const zoomRef = useRef<ZoomActions>(null);
  const kgRef = useRef<KGActions>(null);

  const handlePaletteChange = useCallback((newPalette: Map<string, string>) => {
    setPalette(Array.from(newPalette.entries()));
  }, []);

  useEffect(() => {
    if (document.getElementById("semantic-cloud-scroll-style")) return;
    const style = document.createElement("style");
    style.id = "semantic-cloud-scroll-style";
    style.textContent = `
      .semantic-cloud-scroll::-webkit-scrollbar { width: 6px; }
      .semantic-cloud-scroll::-webkit-scrollbar-track { background: transparent; }
      .semantic-cloud-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.14); border-radius: 999px; }
    `;
    document.head.appendChild(style);
  }, []);

  const triggerUpload = useCallback(async () => {
    setUploading(true);
    setUploadStatus("computing delta...");
    try {
      const res = await fetch(`${API_BASE}/api/datastory/upload`, { method: "POST" });
      if (!res.ok) {
        const detail = await res
          .json()
          .then((body) => body?.detail ?? res.statusText)
          .catch(() => res.statusText);
        throw new Error(detail);
      }
      setRefreshKey((value) => value + 1);
      if (onRefresh) onRefresh();
      setUploadStatus(null);
    } catch (error: unknown) {
      setUploadStatus(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        background: "#050505",
        color: "#FFFFFF",
        fontFamily: "'Geist Sans', system-ui, sans-serif",
      }}
    >
      <div style={{ flex: 1, position: "relative", minWidth: 0 }}>
        <div style={{ position: "absolute", inset: 0, display: isGraph ? "block" : "none" }}>
          <KnowledgeGraph ref={kgRef} refreshKey={refreshKey} />
        </div>
        <div style={{ position: "absolute", inset: 0, display: isGraph ? "none" : "block" }}>
          <ScatterCanvas
            ref={zoomRef}
            refreshKey={refreshKey}
            viewMode={viewMode}
            clusteringDimension={clusteringDimension}
            semanticMode={semanticMode}
            is3DMode={is3DMode}
            focusedCluster={focusedCluster}
            onFocusCluster={setFocusedCluster}
            onPaletteChange={handlePaletteChange}
          />
        </div>

        <div style={{ position: "absolute", top: 16, left: 16, display: "flex", flexWrap: "wrap", gap: 10, pointerEvents: "auto", zIndex: 10 }}>
          <div style={{ ...glassSurface, borderRadius: 16, padding: 8, display: "flex", gap: 4 }}>
            <button type="button" onClick={() => { if (viewMode === "global") { setSemanticMode((v) => !v); } else { setViewMode("global"); setSemanticMode(false); } }} style={viewMode === "global" && !isGraph ? activeControl : inactiveControl}>
              <Globe size={10} strokeWidth={1.5} /> {semanticMode && viewMode === "global" ? "global semantic" : "global convergence"}
            </button>
            <button type="button" onClick={() => { if (viewMode === "federated") { setSemanticMode((v) => !v); } else { setViewMode("federated"); setSemanticMode(false); } }} style={viewMode === "federated" && !isGraph ? activeControl : inactiveControl}>
              <Orbit size={10} strokeWidth={1.5} /> {semanticMode && viewMode === "federated" ? "semantic territories" : "federated territories"}
            </button>
            <button type="button" onClick={() => { setIs3DMode((v) => !v); setSemanticMode(true); }} style={is3DMode ? activeControl : inactiveControl}>
              <Orbit size={10} strokeWidth={1.5} /> 3D
            </button>
            <button type="button" onClick={() => setIsGraph((v) => !v)} style={isGraph ? activeControl : inactiveControl}>
              <GitBranch size={10} strokeWidth={1.5} /> graph
            </button>
          </div>

          {!isGraph && (
          <div style={{ ...glassSurface, borderRadius: 16, padding: 8, display: "flex", gap: 4 }}>
            <button type="button" onClick={() => setClusteringDimension("reason")} style={clusteringDimension === "reason" ? activeControl : inactiveControl}>
              <Layers size={10} strokeWidth={1.5} /> group by reason
            </button>
            <button type="button" onClick={() => setClusteringDimension("category")} style={clusteringDimension === "category" ? activeControl : inactiveControl}>
              <Tags size={10} strokeWidth={1.5} /> group by category
            </button>
          </div>
          )}

          <button
            type="button"
            onClick={triggerUpload}
            disabled={uploading}
            style={{
              ...glassSurface,
              ...controlBase,
              borderRadius: 16,
              color: uploading ? "rgba(255,255,255,0.55)" : "#FFFFFF",
              pointerEvents: "auto",
              padding: "10px 14px",
            }}
          >
            {uploading ? <RefreshCw size={10} strokeWidth={1.5} className="animate-spin" /> : null}
            {uploadStatus ?? "trigger update"}
          </button>

          <div style={{ ...glassSurface, borderRadius: 16, padding: 8, display: "flex", gap: 4 }}>
            <button
              type="button"
              onClick={() => (isGraph ? kgRef.current?.zoomIn() : zoomRef.current?.zoomIn())}
              style={zoomBtnBase}
              title="Zoom in"
            >
              <ZoomIn size={14} strokeWidth={1.5} />
            </button>
            <button
              type="button"
              onClick={() => (isGraph ? kgRef.current?.zoomOut() : zoomRef.current?.zoomOut())}
              style={zoomBtnBase}
              title="Zoom out"
            >
              <ZoomOut size={14} strokeWidth={1.5} />
            </button>
            <button
              type="button"
              onClick={() => (isGraph ? kgRef.current?.fit() : zoomRef.current?.fit())}
              style={zoomBtnBase}
              title="Reset view"
            >
              <RotateCcw size={14} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        {!isGraph && palette && palette.length > 1 && (
          <div
            style={{
              position: "absolute",
              top: 16,
              right: 16,
              zIndex: 10,
              display: "flex",
              flexWrap: "wrap",
              gap: 4,
              maxWidth: 280,
              justifyContent: "flex-end",
            }}
          >
            {focusedCluster && (
              <button
                type="button"
                onClick={() => { zoomRef.current?.focusCluster(null); setFocusedCluster(null); }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 5,
                  padding: "4px 8px",
                  borderRadius: 6,
                  background: "rgba(0,0,0,0.55)",
                  backdropFilter: "blur(6px)",
                  WebkitBackdropFilter: "blur(6px)",
                  fontSize: 9,
                  fontFamily: "'Geist Mono', 'SF Mono', monospace",
                  color: "rgba(255,255,255,0.85)",
                  letterSpacing: "0.04em",
                  border: "1px solid rgba(255,255,255,0.15)",
                  cursor: "pointer",
                }}
              >
                ← All
              </button>
            )}
            {palette.map(([label, color]) => (
              <button
                key={label}
                type="button"
                onClick={() => { zoomRef.current?.focusCluster(label); setFocusedCluster(label); }}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 5,
                  padding: "4px 8px",
                  borderRadius: 6,
                  background: "rgba(0,0,0,0.45)",
                  backdropFilter: "blur(6px)",
                  WebkitBackdropFilter: "blur(6px)",
                  fontSize: 9,
                  fontFamily: "'Geist Mono', 'SF Mono', monospace",
                  color: focusedCluster && focusedCluster !== label ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.75)",
                  letterSpacing: "0.04em",
                  border: "1px solid transparent",
                  cursor: "pointer",
                  opacity: focusedCluster && focusedCluster !== label ? 0.5 : 1,
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: color,
                    flexShrink: 0,
                  }}
                />
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      <StorytellerChat refreshKey={refreshKey} focusedCluster={focusedCluster} />
    </div>
  );
};
