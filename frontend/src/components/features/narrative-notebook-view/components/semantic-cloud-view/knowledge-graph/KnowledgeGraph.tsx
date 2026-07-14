"use client";

import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import { GripVertical, Pin, Plus, X, Lock, Unlock } from "lucide-react";
import type { DashboardFeedResponse, SemanticPoint } from "../types/semantic-cloud.types";
import { getDashboardFeed } from "../hooks/useDashboardFeedCache";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface KGActions {
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
}

interface ColumnDef {
  id: string;
  field: string;
  label: string;
  docked: boolean;
  values: { value: string; count: number }[];
  x?: number;
  y?: number;
}

interface ColumnEdge {
  sourceCol: string;
  sourceVal: string;
  targetCol: string;
  targetVal: string;
  weight: number;
}

type InsertZone = "leftmost" | { between: number } | "rightmost";

const COLUMN_COLORS = [
  "#00E5FF", "#D500F9", "#FFEA00", "#FF4D6D",
  "#06B6D4", "#F97316", "#14B8A6", "#4F46E5",
  "#F43F5E", "#38BDF8", "#25C26E", "#FFB703",
];

const PASTEL_COLORS = [
  "#5EEAD4", "#E879F9", "#FDE047", "#FDA4AF",
  "#67E8F9", "#FDBA74", "#6EE7B7", "#A78BFA",
  "#FDA4AF", "#7DD3FC", "#86EFAC", "#FCD34D",
];

const NODE_HEIGHT = 36;
const NODE_GAP = 8;
const COLUMN_WIDTH = 200;
const COLUMN_GAP = 60;
const MIN_SCALE = 0.1;
const MAX_SCALE = 10;
const CONTROLS_HEIGHT = 64;

const EXCLUDE_FIELDS = new Set(["id", "tooltip", "eigenvectors", "x", "y", "z"]);

function fieldLabel(field: string): string {
  return field
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function extractValues(data: SemanticPoint[], ...fields: (keyof SemanticPoint)[]) {
  const result = new Map<string, { value: string; count: number }[]>();
  for (const field of fields) {
    const counts = new Map<string, number>();
    for (const point of data) {
      const val = String(point[field] ?? "").trim();
      if (val && val !== "undefined") counts.set(val, (counts.get(val) ?? 0) + 1);
    }
    result.set(field, Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).map(([value, count]) => ({ value, count })));
  }
  return result;
}

function fieldCoOccurrences(data: SemanticPoint[], fieldA: string, fieldB: string): Map<string, Map<string, number>> {
  const map = new Map<string, Map<string, number>>();
  for (const point of data) {
    const a = String(point[fieldA as keyof SemanticPoint] ?? "").trim();
    const b = String(point[fieldB as keyof SemanticPoint] ?? "").trim();
    if (!a || !b || a === "undefined" || b === "undefined") continue;
    if (!map.has(a)) map.set(a, new Map());
    const inner = map.get(a)!;
    inner.set(b, (inner.get(b) ?? 0) + 1);
  }
  return map;
}

function hasConnections(data: SemanticPoint[], fieldA: string, fieldB: string): boolean {
  if (fieldA === fieldB) return false;
  for (const point of data) {
    const a = String(point[fieldA as keyof SemanticPoint] ?? "").trim();
    const b = String(point[fieldB as keyof SemanticPoint] ?? "").trim();
    if (a && b && a !== "undefined" && b !== "undefined") return true;
  }
  return false;
}

function computeEdges(data: SemanticPoint[], cols: ColumnDef[]): ColumnEdge[] {
  const docked = cols.filter((c) => c.docked);
  const edges: ColumnEdge[] = [];
  for (let i = 0; i < docked.length; i++) {
    for (let j = i + 1; j < docked.length; j++) {
      const left = docked[i];
      const right = docked[j];
      const coOccur = fieldCoOccurrences(data, left.field, right.field);
      for (const [lv, inner] of coOccur) {
        for (const [rv, weight] of inner) {
          edges.push({ sourceCol: left.id, sourceVal: lv, targetCol: right.id, targetVal: rv, weight });
        }
      }
    }
  }
  return edges;
}

function buildAllColumns(data: SemanticPoint[], availableFields: string[]): ColumnDef[] {
  const point = data.length > 0 ? data[0] : undefined;
  if (!point) return [];
  const known = availableFields.filter((f): f is keyof SemanticPoint => !EXCLUDE_FIELDS.has(f) && f in point);
  const useFields = known.length > 0
    ? known
    : (Object.keys(point) as (keyof SemanticPoint)[]).filter((k) => !EXCLUDE_FIELDS.has(k));
  const all = extractValues(data, ...useFields);
  return useFields.map((field, i) => ({
    id: field as string,
    field: field as string,
    label: fieldLabel(field as string),
    docked: false,
    values: all.get(field as string) ?? [],
  }));
}

interface InsertSuggestion {
  zone: InsertZone;
  field: string;
  label: string;
}

function computeInsertSuggestions(data: SemanticPoint[], dockedCols: ColumnDef[], undockedFields: { field: string; label: string }[]): InsertSuggestion[] {
  if (dockedCols.length === 0) return [];
  const suggestions: InsertSuggestion[] = [];
  if (dockedCols.length === 1) {
    const singleField = dockedCols[0].field;
    for (const av of undockedFields) {
      if (av.field !== singleField && hasConnections(data, av.field, singleField)) {
        suggestions.push({ zone: "leftmost", field: av.field, label: av.label });
        suggestions.push({ zone: "rightmost", field: av.field, label: av.label });
      }
    }
    return suggestions;
  }
  const leftField = dockedCols[0].field;
  const rightField = dockedCols[dockedCols.length - 1].field;
  for (const av of undockedFields) {
    const hasLeft = hasConnections(data, av.field, leftField);
    const hasRight = hasConnections(data, av.field, rightField);
    if (hasLeft && hasRight) {
      for (let i = 0; i < dockedCols.length - 1; i++) {
        if (hasConnections(data, av.field, dockedCols[i].field) && hasConnections(data, av.field, dockedCols[i + 1].field)) {
          suggestions.push({ zone: { between: i }, field: av.field, label: av.label });
          break;
        }
      }
    } else if (hasRight && !hasLeft) {
      suggestions.push({ zone: "leftmost", field: av.field, label: av.label });
    } else if (hasLeft && !hasRight) {
      suggestions.push({ zone: "rightmost", field: av.field, label: av.label });
    }
  }
  return suggestions;
}

const KnowledgeGraph = forwardRef<KGActions, { refreshKey?: number }>(({ refreshKey = 0 }, ref) => {
  const [data, setData] = useState<SemanticPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [hovered, setHovered] = useState<{ col: string; val: string } | null>(null);
  const [columns, setColumns] = useState<ColumnDef[]>([]);
  const [pickField, setPickField] = useState<InsertZone | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewHeight, setViewHeight] = useState(600);
  const [viewWidth, setViewWidth] = useState(1200);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const isDragging = useRef(false);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const dragStartTransform = useRef({ x: 0, y: 0, scale: 1 });
  const [panelPinned, setPanelPinned] = useState(false);
  const [isLocked, setIsLocked] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [storedEdges, setStoredEdges] = useState<ColumnEdge[] | null>(null);
  const [scrollOffsets, setScrollOffsets] = useState<Record<string, number>>({});
  const [activeDragCol, setActiveDragCol] = useState<string | null>(null);
  const colDragStart = useRef({ x: 0, y: 0, colX: 0, colY: 0 });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await getDashboardFeed(refreshKey);
        if (cancelled) return;
        const valid = payload.ui_cloud_data ?? [];
        const fields = payload.available_fields?.length
          ? payload.available_fields
          : ["issue_category", "reassignment_reason", "reassigned_to", "ticket_queue"];
        setData(valid);
        const baseCols = buildAllColumns(valid, fields);
        try {
          const stateRes = await fetch(`${API_BASE}/api/datastory/knowledge-graph-state`);
          if (stateRes.ok) {
            const saved: { 
              columns?: { field: string; label: string; values: { value: string; count: number }[]; x?: number; y?: number }[]; 
              edges?: { source_col: string; source_val: string; target_col: string; target_val: string; weight: number }[] 
            } = await stateRes.json();
            if (saved?.columns?.length) {
              const savedFields = new Set(saved.columns.map(c => c.field));
              const savedDocked = saved.columns.map((c, i) => {
                const baseC = baseCols.find(b => b.field === c.field);
                return {
                  id: c.field,
                  field: c.field,
                  label: c.label,
                  docked: true,
                  values: baseC?.values ?? c.values ?? [],
                  x: c.x !== undefined ? c.x : xPos(i),
                  y: c.y !== undefined ? c.y : CONTROLS_HEIGHT + 16,
                };
              });
              const remainingUndocked = baseCols
                .filter(b => !savedFields.has(b.field))
                .map((b, i) => ({
                  ...b,
                  id: b.field,
                  docked: false,
                }));
              setColumns([...savedDocked, ...remainingUndocked]);
              if (saved.edges?.length) {
                const getFieldName = (colId: string) => {
                  if (colId.startsWith("col_docked_")) {
                    const idx = parseInt(colId.substring(11), 10);
                    if (saved.columns && saved.columns[idx]) {
                      return saved.columns[idx].field;
                    }
                  } else if (colId.startsWith("col_undocked_")) {
                    const idx = parseInt(colId.substring(13), 10);
                    const undockedFields = baseCols.filter(b => !savedFields.has(b.field));
                    if (undockedFields[idx]) {
                      return undockedFields[idx].field;
                    }
                  }
                  return colId; // Fallback to itself if it's already a field name
                };

                setStoredEdges(saved.edges.map((e) => ({
                  sourceCol: getFieldName(e.source_col),
                  sourceVal: e.source_val,
                  targetCol: getFieldName(e.target_col),
                  targetVal: e.target_val,
                  weight: e.weight,
                })));
              }
              setLoading(false);
              setTransform({ x: 0, y: 0, scale: 1 });
              return;
            }
          }
          } catch (err) { /* no saved state */ }
        setColumns(baseCols);
        setLoading(false);
        setTransform({ x: 0, y: 0, scale: 1 });
      } catch (err) {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [refreshKey]);

  useEffect(() => {
    const ob = new ResizeObserver(([entry]) => {
      setViewHeight(entry.contentRect.height);
      setViewWidth(entry.contentRect.width);
    });
    if (containerRef.current) ob.observe(containerRef.current);
    return () => ob.disconnect();
  }, []);

  const dockedCols = useMemo(() => columns.filter((c) => c.docked), [columns]);
  const undockedCols = useMemo(() => columns.filter((c) => !c.docked), [columns]);
  const edges = useMemo(() => storedEdges ?? computeEdges(data, columns), [data, columns, storedEdges]);

  // Precompute adjacency maps for O(1) node hover lookups
  const adjacencyList = useMemo(() => {
    const nodeToNodes = new Map<string, Set<string>>();
    const nodeToEdges = new Map<string, Set<string>>();
    
    for (const e of edges) {
      const srcKey = `${e.sourceCol}::${e.sourceVal}`;
      const tgtKey = `${e.targetCol}::${e.targetVal}`;
      const edgeKey = `${e.sourceCol}:${e.sourceVal}→${e.targetCol}:${e.targetVal}`;
      
      // Node-to-node connections
      if (!nodeToNodes.has(srcKey)) nodeToNodes.set(srcKey, new Set());
      if (!nodeToNodes.has(tgtKey)) nodeToNodes.set(tgtKey, new Set());
      nodeToNodes.get(srcKey)!.add(tgtKey);
      nodeToNodes.get(tgtKey)!.add(srcKey);

      // Node-to-edge connections
      if (!nodeToEdges.has(srcKey)) nodeToEdges.set(srcKey, new Set());
      if (!nodeToEdges.has(tgtKey)) nodeToEdges.set(tgtKey, new Set());
      nodeToEdges.get(srcKey)!.add(edgeKey);
      nodeToEdges.get(tgtKey)!.add(edgeKey);
    }
    
    return { nodeToNodes, nodeToEdges };
  }, [edges]);

  useEffect(() => {
    if (!storedEdges && columns.every((c) => !c.docked)) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const docked = columns.filter((c) => c.docked);
      const payload = {
        columns: docked.map((c) => ({ field: c.field, label: c.label, values: c.values, x: c.x, y: c.y })),
        edges: edges.map((e) => ({
          source_col: e.sourceCol, source_val: e.sourceVal,
          target_col: e.targetCol, target_val: e.targetVal,
          weight: e.weight,
        })),
      };
      fetch(`${API_BASE}/api/datastory/knowledge-graph-state`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch(() => {});
    }, 300);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [columns, storedEdges, edges]);
  const maxWeight = useMemo(() => Math.max(...edges.map((e) => e.weight), 1), [edges]);
  const columnMaxCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const col of dockedCols) {
      m.set(col.id, Math.max(...col.values.map((v) => v.count), 1));
    }
    return m;
  }, [dockedCols]);
  const insertSuggestions = useMemo(() => computeInsertSuggestions(data, dockedCols, undockedCols), [data, dockedCols, undockedCols]);

  const graphWidth = Math.max(1, dockedCols.length * COLUMN_WIDTH + (dockedCols.length - 1) * COLUMN_GAP);
  const panelWidth = 220;
  const xOffset = panelPinned
    ? Math.max(20, panelWidth + 20)
    : Math.max(20, (viewWidth - graphWidth) / 2);

  const xPos = useCallback((index: number) => xOffset + index * (COLUMN_WIDTH + COLUMN_GAP), [xOffset]);
  const yPos = useCallback((nodeIdx: number, colNodes: number) => {
    const totalHeight = colNodes * NODE_HEIGHT + (colNodes - 1) * NODE_GAP;
    return Math.max(CONTROLS_HEIGHT + 48, (viewHeight - totalHeight) / 2) + nodeIdx * (NODE_HEIGHT + NODE_GAP);
  }, [viewHeight]);

  useImperativeHandle(ref, () => ({
    zoomIn: () => { if (isLocked) return; setTransform((prev) => ({ ...prev, scale: Math.min(MAX_SCALE, prev.scale * 1.5) })); },
    zoomOut: () => { if (isLocked) return; setTransform((prev) => ({ ...prev, scale: Math.max(MIN_SCALE, prev.scale / 1.5) })); },
    fit: () => { if (isLocked) return; setTransform({ x: 0, y: 0, scale: 1 }); },
  }), [isLocked]);

  const handleColMouseDown = (e: React.MouseEvent, colId: string) => {
    if (isLocked) return;
    e.stopPropagation();
    if (e.button !== 0) return;
    const col = columns.find(c => c.id === colId);
    if (!col) return;
    const dockedIndex = dockedCols.indexOf(col);
    const currentX = col.x !== undefined ? col.x : xPos(dockedIndex);
    const currentY = col.y !== undefined ? col.y : CONTROLS_HEIGHT + 16;
    setActiveDragCol(colId);
    colDragStart.current = {
      x: e.clientX,
      y: e.clientY,
      colX: currentX,
      colY: currentY
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (isLocked) return;
    if (e.button !== 0) return;
    isDragging.current = true;
    setDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    dragStartTransform.current = { ...transform };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isLocked) return;
    if (activeDragCol) {
      const deltaX = (e.clientX - colDragStart.current.x) / transform.scale;
      const deltaY = (e.clientY - colDragStart.current.y) / transform.scale;
      
      setColumns((prev) => prev.map((c) => {
        if (c.id === activeDragCol) {
          return {
            ...c,
            x: colDragStart.current.colX + deltaX,
            y: colDragStart.current.colY + deltaY
          };
        }
        return c;
      }));
      return;
    }

    if (!isDragging.current) return;
    setTransform({
      x: dragStartTransform.current.x + e.clientX - dragStart.current.x,
      y: dragStartTransform.current.y + e.clientY - dragStart.current.y,
      scale: dragStartTransform.current.scale,
    });
  };

  const handleMouseUp = () => { 
    isDragging.current = false; 
    setDragging(false); 
    setActiveDragCol(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (isLocked) return;
    e.preventDefault();
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const delta = e.deltaY > 0 ? 0.88 : 1 / 0.88;
    const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, transform.scale * delta));
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    setTransform({
      x: cx - (cx - transform.x) * (newScale / transform.scale),
      y: cy - (cy - transform.y) * (newScale / transform.scale),
      scale: newScale,
    });
  };

  const dockColumnAt = useCallback((field: string, zone: InsertZone) => {
    if (isLocked) return;
    setStoredEdges(null);
    setColumns((prev) => {
      const next = [...prev];
      const idx = next.findIndex((c) => c.field === field);
      if (idx === -1) return prev;
      const dockedCount = next.filter(c => c.docked).length;
      const col = { 
        ...next[idx], 
        docked: true,
        x: xOffset + dockedCount * (COLUMN_WIDTH + COLUMN_GAP),
        y: CONTROLS_HEIGHT + 16
      };
      next.splice(idx, 1);
      if (zone === "leftmost") next.unshift(col);
      else if (zone === "rightmost") next.push(col);
      else next.splice((zone as { between: number }).between + 1, 0, col);
      
      let count = 0;
      return next.map(c => {
        if (c.docked) {
          const defaultX = xOffset + count * (COLUMN_WIDTH + COLUMN_GAP);
          count++;
          return {
            ...c,
            x: c.x !== undefined ? c.x : defaultX,
            y: c.y !== undefined ? c.y : CONTROLS_HEIGHT + 16
          };
        }
        return c;
      });
    });
    setPickField(null);
  }, [xOffset, isLocked]);

  const undockColumn = useCallback((colId: string) => {
    if (isLocked) return;
    setStoredEdges(null);
    setColumns((prev) => prev.map((c) => (c.id === colId ? { ...c, docked: false } : c)));
  }, [isLocked]);

  const getDropZone = useCallback((clientX: number): InsertZone | null => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect || dockedCols.length === 0) return null;
    const canvasX = (clientX - rect.left - transform.x) / transform.scale - xOffset;
    const colSlots = dockedCols.length + 1;
    const slotWidth = graphWidth / colSlots;
    const slot = Math.round(canvasX / slotWidth);
    const clamped = Math.max(0, Math.min(colSlots - 1, slot));
    if (clamped === 0) return "leftmost";
    if (clamped >= dockedCols.length) return "rightmost";
    return { between: clamped - 1 };
  }, [dockedCols, transform, xOffset, graphWidth]);

  const connectedSet = useMemo(() => {
    if (!hovered) return null;
    const key = `${hovered.col}::${hovered.val}`;
    const connected = adjacencyList.nodeToNodes.get(key) || new Set<string>();
    const s = new Set<string>(connected);
    s.add(key);
    return s;
  }, [hovered, adjacencyList]);

  const connectedEdgeKeys = useMemo(() => {
    if (!hovered) return null;
    const key = `${hovered.col}::${hovered.val}`;
    return adjacencyList.nodeToEdges.get(key) || new Set<string>();
  }, [hovered, adjacencyList]);

  if (loading) {
    return <div style={{ padding: 40, textAlign: "center", color: "rgba(255,255,255,0.5)", fontFamily: "'Geist Mono', monospace", fontSize: 11 }}>building knowledge graph...</div>;
  }
  if (data.length === 0) {
    return <div style={{ padding: 40, textAlign: "center", color: "rgba(255,255,255,0.4)", fontFamily: "'Geist Mono', monospace", fontSize: 11 }}>no data available</div>;
  }

  function isNodeDim(col: string, val: string) { return !!connectedSet && !connectedSet.has(`${col}::${val}`); }

  function edgeVisual(edge: ColumnEdge) {
    if (!hovered) { 
      const op = 0.06 + (edge.weight / maxWeight) * 0.35; 
      return { stroke: "rgba(255,255,255,0.25)", width: Math.max(0.5, op * 3), opacity: op, glow: false }; 
    }
    const edgeKey = `${edge.sourceCol}:${edge.sourceVal}→${edge.targetCol}:${edge.targetVal}`;
    const active = connectedEdgeKeys?.has(edgeKey);
    if (active) { 
      const ci = Math.max(0, dockedCols.findIndex((c) => c.id === edge.sourceCol)); 
      const c = PASTEL_COLORS[ci % PASTEL_COLORS.length]; 
      return { stroke: c, width: 2.2, opacity: 0.95, glow: true }; 
    }
    return { stroke: "rgba(255,255,255,0.25)", width: 0.5, opacity: 0.04, glow: false };
  }

  const hasBetween = (z: InsertZone): z is { between: number } => typeof z !== "string";
  const pickerItems = (zone: InsertZone) => insertSuggestions.filter((s) => {
    if (typeof zone === "string" && typeof s.zone === "string") return s.zone === zone;
    if (hasBetween(zone) && hasBetween(s.zone)) return s.zone.between === zone.between;
    return false;
  });
  const pickerLeft = (zone: InsertZone): number => {
    if (zone === "leftmost") return xPos(0) - 80 - 12;
    if (zone === "rightmost") return xPos(dockedCols.length - 1) + COLUMN_WIDTH + 8;
    return xPos((zone as { between: number }).between) + COLUMN_WIDTH + COLUMN_GAP / 2 - 80;
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", overflow: "hidden" }}>
      {/* Column panel */}
      {panelPinned && (
        <div
          ref={panelRef}
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            width: panelWidth,
            maxHeight: `calc(100% - ${CONTROLS_HEIGHT + 24}px)`,
            borderRadius: 14,
            border: "1px solid rgba(255,255,255,0.08)",
            display: "flex",
            flexDirection: "column",
            zIndex: 25,
            background: "rgba(5,5,5,0.72)",
            backdropFilter: "blur(14px)",
            boxShadow: "0 16px 48px rgba(0,0,0,0.45)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 12px 8px",
              borderBottom: "1px solid rgba(255,255,255,0.06)",
              flexShrink: 0,
            }}
          >
            <span style={{ fontSize: 9, fontFamily: "'Geist Mono', monospace", color: "rgba(255,255,255,0.5)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Columns
            </span>
            <div
              onClick={() => setPanelPinned(false)}
              title="Unpin panel"
              style={{ width: 18, height: 18, borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "rgba(255,255,255,0.35)", transition: "color 140ms ease" }}
              onMouseEnter={(e) => e.currentTarget.style.color = "#FFFFFF"}
              onMouseLeave={(e) => e.currentTarget.style.color = "rgba(255,255,255,0.35)"}
            >
              <Pin size={12} strokeWidth={2} fill="rgba(255,255,255,0.35)" />
            </div>
          </div>
          <div style={{ flex: 1, overflow: "auto", padding: "6px 8px 8px" }}>
            {undockedCols.length > 0 && dockedCols.length > 0 && (
              <div
                onClick={() => { if (isLocked) return; setStoredEdges(null); setColumns((prev) => prev.map((c) => ({ ...c, docked: true }))); }}
                style={{ padding: "4px 8px 6px", fontSize: 9, color: isLocked ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.35)", cursor: isLocked ? "not-allowed" : "pointer", fontFamily: "'Geist Mono', monospace", textAlign: "center", letterSpacing: "0.04em", transition: "color 120ms ease" }}
                onMouseEnter={(e) => { if (!isLocked) e.currentTarget.style.color = "rgba(255,255,255,0.7)"; }}
                onMouseLeave={(e) => { if (!isLocked) e.currentTarget.style.color = "rgba(255,255,255,0.35)"; }}
              >
                dock all ({undockedCols.length})
              </div>
            )}
            {dockedCols.length > 0 && (
              <div
                onClick={() => { if (isLocked) return; setStoredEdges(null); setColumns((prev) => prev.map((c) => ({ ...c, docked: false }))); }}
                style={{ padding: "4px 8px 6px", fontSize: 9, color: isLocked ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.35)", cursor: isLocked ? "not-allowed" : "pointer", fontFamily: "'Geist Mono', monospace", textAlign: "center", letterSpacing: "0.04em", transition: "color 120ms ease" }}
                onMouseEnter={(e) => { if (!isLocked) e.currentTarget.style.color = "rgba(255,255,255,0.7)"; }}
                onMouseLeave={(e) => { if (!isLocked) e.currentTarget.style.color = "rgba(255,255,255,0.35)"; }}
              >
                undock all ({dockedCols.length})
              </div>
            )}
            {columns.length > 0 && undockedCols.length === 0 && (
              <div style={{ padding: "12px 6px", fontSize: 10, color: "rgba(255,255,255,0.3)", textAlign: "center", fontFamily: "'Geist Mono', monospace" }}>
                all columns docked
              </div>
            )}
            {columns.length === 0 && !loading && (
              <div style={{ padding: "12px 6px", fontSize: 10, color: "rgba(255,255,255,0.25)", textAlign: "center", fontFamily: "'Geist Mono', monospace" }}>
                no columns available
              </div>
            )}
            {undockedCols.map((col, fi) => (
              <div
                key={col.id}
                draggable={!isLocked}
                onDragStart={(e) => { if (isLocked) return; e.dataTransfer.setData("text/plain", col.field); e.dataTransfer.effectAllowed = "move"; }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "7px 8px",
                  marginBottom: 3,
                  borderRadius: 8,
                  fontSize: 11,
                  color: isLocked ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.65)",
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  cursor: isLocked ? "not-allowed" : "grab",
                  fontFamily: "'Geist Sans', system-ui, sans-serif",
                  transition: "background 140ms ease",
                }}
                onMouseEnter={(e) => { if (!isLocked) e.currentTarget.style.background = "rgba(255,255,255,0.07)"; }}
                onMouseLeave={(e) => { if (!isLocked) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
              >
                <GripVertical size={11} color="rgba(255,255,255,0.25)" style={{ cursor: isLocked ? "not-allowed" : "grab" }} />
                <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", fontWeight: 500 }}>{col.label}</span>
                <span style={{ fontSize: 9, color: PASTEL_COLORS[fi % PASTEL_COLORS.length], fontFamily: "'Geist Mono', monospace", opacity: 0.7, marginRight: 4 }}>{col.values.length}</span>
                {!isLocked && (
                  <div
                    onClick={() => dockColumnAt(col.field, "rightmost")}
                    style={{
                      width: 16, height: 16, borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center",
                      cursor: "pointer", background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.4)",
                      transition: "all 120ms ease"
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(0,229,255,0.2)"; e.currentTarget.style.color = "#00E5FF"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.06)"; e.currentTarget.style.color = "rgba(255,255,255,0.4)"; }}
                    title="Dock Column"
                  >
                    <Plus size={10} strokeWidth={2.5} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unpin button when panel is hidden */}
      {!panelPinned && (
        <div
          onClick={() => setPanelPinned(true)}
          title="Show column panel"
          style={{
            position: "absolute",
            left: 12,
            top: "50%",
            transform: "translateY(-50%)",
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "rgba(5,5,5,0.6)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(255,255,255,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            zIndex: 25,
            color: "rgba(255,255,255,0.45)",
            transition: "color 140ms ease, background 140ms ease",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.10)"; e.currentTarget.style.color = "#FFFFFF"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(5,5,5,0.6)"; e.currentTarget.style.color = "rgba(255,255,255,0.45)"; }}
        >
          <Pin size={14} strokeWidth={2} />
        </div>
      )}

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height: "100%",
          position: "relative",
          overflow: "hidden",
          cursor: dragging ? "grabbing" : dockedCols.length > 0 ? "grab" : "default",
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={() => {}}
        onDrop={(e) => {
          e.preventDefault();
          const field = e.dataTransfer.getData("text/plain");
          if (!field) return;
          if (dockedCols.length === 0) { dockColumnAt(field, "leftmost"); return; }
          const zone = getDropZone(e.clientX);
          if (zone) dockColumnAt(field, zone);
        }}
      >
        {/* Background atmosphere */}
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none", zIndex: -1,
          background: "radial-gradient(ellipse at 50% 50%, rgba(255,255,255,0.02) 0%, transparent 70%)",
        }} />
        {dockedCols.length === 0 && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "rgba(255,255,255,0.18)",
              fontFamily: "'Geist Mono', monospace",
              fontSize: 11,
              letterSpacing: "0.06em",
              pointerEvents: "none",
              padding: "0 20%",
              textAlign: "center",
              lineHeight: 1.8,
            }}
          >
            drag columns from the left panel to build your graph
          </div>
        )}

        <div
          style={{
            width: "100%",
            height: "100%",
            transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
            transformOrigin: "0 0",
            position: "relative",
            transition: dragging ? "none" : "transform 80ms ease-out",
          }}
        >
          {/* Edges */}
          <svg style={{ position: "absolute", top: 0, left: 0, width: Math.max(4000, xOffset + graphWidth + 1000), height: Math.max(4000, viewHeight + 1000), overflow: "visible", pointerEvents: "none" }}>
            <defs>
              <pattern id="kg-dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1" fill="rgba(255,255,255,0.05)" />
              </pattern>
              <filter id="eg-glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              {dockedCols.map((_, ci) => {
                if (ci === dockedCols.length - 1) return null;
                const c1 = PASTEL_COLORS[ci % PASTEL_COLORS.length];
                const c2 = PASTEL_COLORS[(ci + 1) % PASTEL_COLORS.length];
                return (
                  <linearGradient key={`grad_${ci}`} id={`eg_${ci}`} x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor={c1} />
                    <stop offset="100%" stopColor={c2} />
                  </linearGradient>
                );
              })}
            </defs>

            <rect x="-4000" y="-4000" width="12000" height="12000" fill="url(#kg-dots)" />

            {edges.map((edge) => {
              const leftCol = dockedCols.find((c) => c.id === edge.sourceCol);
              const rightCol = dockedCols.find((c) => c.id === edge.targetCol);
              if (!leftCol || !rightCol) return null;
              
              const isLeftColLeft = (leftCol.x !== undefined ? leftCol.x : 0) < (rightCol.x !== undefined ? rightCol.x : 0);
              const colA = isLeftColLeft ? leftCol : rightCol;
              const colB = isLeftColLeft ? rightCol : leftCol;
              const valA = isLeftColLeft ? edge.sourceVal : edge.targetVal;
              const valB = isLeftColLeft ? edge.targetVal : edge.sourceVal;
              
              const colAIdx = dockedCols.indexOf(colA);
              const colBIdx = dockedCols.indexOf(colB);
              
              const vAIdx = colA.values.findIndex((v) => v.value === valA);
              const vBIdx = colB.values.findIndex((v) => v.value === valB);
              if (vAIdx === -1 || vBIdx === -1) return null;
              
              const colAX = colA.x !== undefined ? colA.x : xPos(colAIdx);
              const colAY = colA.y !== undefined ? colA.y : CONTROLS_HEIGHT + 16;
              const colBX = colB.x !== undefined ? colB.x : xPos(colBIdx);
              const colBY = colB.y !== undefined ? colB.y : CONTROLS_HEIGHT + 16;
              
              const scrollA = scrollOffsets[colA.id] || 0;
              const scrollB = scrollOffsets[colB.id] || 0;
              
              const headerHeight = 35;
              const paddingOffset = 8;
              const cardMaxHeight = Math.min(600, viewHeight - 120);
              const scrollHeight = cardMaxHeight - headerHeight - 16;
              
              const y1 = colAY + headerHeight + paddingOffset + vAIdx * (NODE_HEIGHT + NODE_GAP) - scrollA + NODE_HEIGHT / 2;
              const x1 = colAX + COLUMN_WIDTH;
              
              const y2 = colBY + headerHeight + paddingOffset + vBIdx * (NODE_HEIGHT + NODE_GAP) - scrollB + NODE_HEIGHT / 2;
              const x2 = colBX;
              
              const dx = Math.abs(x2 - x1);
              const cp = dx * 0.45;
              
              const y1Local = y1 - colAY - headerHeight - paddingOffset;
              const y2Local = y2 - colBY - headerHeight - paddingOffset;
              
              const isAVisible = y1Local >= 0 && y1Local <= scrollHeight;
              const isBVisible = y2Local >= 0 && y2Local <= scrollHeight;
              
              const vis = edgeVisual(edge);
              const finalOpacity = (isAVisible && isBVisible) ? vis.opacity : 0;
              
              const edgeStroke = vis.glow && colAIdx < dockedCols.length - 1 
                ? `url(#eg_${colAIdx})` 
                : vis.stroke;

              return (
                <React.Fragment key={`${edge.sourceCol}:${edge.sourceVal}→${edge.targetCol}:${edge.targetVal}`}>
                  {/* Glow Shadow Path Underneath */}
                  {vis.glow && (
                    <path
                      d={`M ${x1} ${y1} C ${x1 + cp} ${y1}, ${x2 - cp} ${y2}, ${x2} ${y2}`}
                      stroke={edgeStroke}
                      strokeWidth={vis.width * 3.5}
                      opacity={finalOpacity * 0.28}
                      fill="none"
                      strokeLinecap="round"
                      style={{ transition: "opacity 150ms ease, stroke 150ms ease" }}
                    />
                  )}
                  {/* Main Sharp Path */}
                  <path
                    d={`M ${x1} ${y1} C ${x1 + cp} ${y1}, ${x2 - cp} ${y2}, ${x2} ${y2}`}
                    stroke={edgeStroke}
                    strokeWidth={vis.width}
                    opacity={finalOpacity}
                    fill="none"
                    strokeLinecap="round"
                    style={{ transition: "opacity 150ms ease, stroke 150ms ease" }}
                  />
                </React.Fragment>
              );
            })}
          </svg>

          {/* Docked columns rendered as floating, draggable cards */}
          {dockedCols.map((col, ci) => {
            const color = COLUMN_COLORS[ci % COLUMN_COLORS.length];
            const nodeColor = PASTEL_COLORS[ci % PASTEL_COLORS.length];
            const colX = col.x !== undefined ? col.x : xPos(ci);
            const colY = col.y !== undefined ? col.y : CONTROLS_HEIGHT + 16;
            const cardMaxHeight = Math.min(600, viewHeight - 120);

            return (
              <div 
                key={col.id} 
                style={{ 
                  position: "absolute", 
                  top: colY, 
                  left: colX, 
                  width: COLUMN_WIDTH, 
                  maxHeight: cardMaxHeight,
                  display: "flex",
                  flexDirection: "column",
                  background: "rgba(10, 10, 10, 0.8)",
                  backdropFilter: "blur(14px)",
                  borderRadius: 12,
                  border: `1px solid ${color}40`,
                  boxShadow: `0 4px 20px rgba(0, 0, 0, 0.5), 0 0 15px ${color}10`,
                  zIndex: activeDragCol === col.id ? 40 : 20,
                  overflow: "hidden",
                }}
              >
                {/* Draggable Card Header */}
                <div 
                  onMouseDown={(e) => handleColMouseDown(e, col.id)}
                  style={{
                    fontSize: 10, fontFamily: "'Geist Mono', monospace", color, letterSpacing: "0.06em", textTransform: "uppercase",
                    padding: "10px 12px", fontWeight: 600,
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    display: "flex", alignItems: "center", gap: 6,
                    borderBottom: `1px solid ${color}18`,
                    background: `${color}0A`,
                    cursor: isLocked ? "default" : (activeDragCol === col.id ? "grabbing" : "grab"),
                    userSelect: "none",
                  }}
                >
                  <GripVertical size={12} style={{ opacity: isLocked ? 0.2 : 0.5, cursor: isLocked ? "default" : "grab" }} />
                  <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>{col.label}</span>
                  {!isLocked && (
                    <div
                      onClick={() => undockColumn(col.id)} title="Undock"
                      onMouseDown={(e) => e.stopPropagation()}
                      style={{
                        width: 18, height: 18, borderRadius: 4, display: "flex", alignItems: "center", justifyContent: "center",
                        cursor: "pointer", color: "rgba(255,255,255,0.35)", transition: "color 140ms ease, background 140ms ease", flexShrink: 0,
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = color; e.currentTarget.style.background = `${color}1A`; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "rgba(255,255,255,0.35)"; e.currentTarget.style.background = "transparent"; }}
                    >
                      <X size={11} strokeWidth={2} />
                    </div>
                  )}
                </div>

                {/* Scrollable node items */}
                <div 
                  onScroll={(e) => {
                    const scrollTop = e.currentTarget.scrollTop;
                    setScrollOffsets(prev => ({ ...prev, [col.id]: scrollTop }));
                  }}
                  style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "8px 6px" }}
                  className="scrollbar-none"
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: NODE_GAP }}>
                    {col.values.map((node, ni) => {
                      const nodeKey = `${col.id}::${node.value}`;
                      const isHovered = hovered?.col === col.id && hovered?.val === node.value;
                      const dim = isNodeDim(col.id, node.value);
                      const connected = connectedSet?.has(nodeKey) && !isHovered;
                      return (
                        <div
                          key={node.value}
                          onMouseEnter={() => setHovered({ col: col.id, val: node.value })}
                          onMouseLeave={() => setHovered(null)}
                          onMouseDown={(e) => e.stopPropagation()}
                          style={{
                            height: NODE_HEIGHT,
                            display: "flex", alignItems: "center", gap: 8, padding: "0 8px", borderRadius: 8, cursor: "pointer", overflow: "hidden",
                            background: isHovered
                              ? `${nodeColor}44`
                              : connected
                                ? `${nodeColor}15`
                                : "rgba(255,255,255,0.02)",
                            border: `1px solid ${isHovered ? `${nodeColor}80` : connected ? `${nodeColor}30` : "rgba(255,255,255,0.05)"}`,
                            boxShadow: isHovered ? `0 0 10px ${nodeColor}20` : "none",
                            opacity: dim ? 0.35 : 1,
                            transition: "all 140ms ease",
                          }}
                        >
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: nodeColor, flexShrink: 0 }} />
                          <span style={{
                            flex: 1, fontSize: 11, color: isHovered ? "#FFF" : "rgba(255,255,255,0.85)",
                            fontFamily: "'Geist Sans', system-ui, sans-serif", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis"
                          }}>
                            {node.value}
                          </span>
                          <span style={{ fontSize: 9, color: "rgba(255,255,255,0.35)", fontFamily: "'Geist Mono', monospace" }}>{node.count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}

          {/* '+' buttons */}
          {!isLocked && dockedCols.length > 0 && insertSuggestions.some((s) => s.zone === "leftmost") && (
            <InsertBtn x={xPos(0) - 18} y={CONTROLS_HEIGHT + 8} onClick={() => setPickField(pickField === "leftmost" ? null : "leftmost")} />
          )}
          {!isLocked && dockedCols.map((_, ci) => {
            if (ci === dockedCols.length - 1) return null;
            if (!insertSuggestions.some((s) => { const b = s.zone as { between: number }; return b.between === ci; })) return null;
            return <InsertBtn key={`gap_${ci}`} x={xPos(ci) + COLUMN_WIDTH + COLUMN_GAP / 2 - 12} y={CONTROLS_HEIGHT + 8} onClick={() => setPickField(pickField && (pickField as { between: number }).between === ci ? null : { between: ci })} />;
          })}
          {!isLocked && dockedCols.length > 0 && insertSuggestions.some((s) => s.zone === "rightmost") && (
            <InsertBtn x={xPos(dockedCols.length - 1) + COLUMN_WIDTH + 4} y={CONTROLS_HEIGHT + 8} onClick={() => setPickField(pickField === "rightmost" ? null : "rightmost")} />
          )}

          {/* Picker popover */}
          {pickField && pickerItems(pickField).length > 0 && (
            <div style={{
              position: "absolute", left: pickerLeft(pickField), top: CONTROLS_HEIGHT + 36, width: 180,
              background: "rgba(8,8,12,0.95)", backdropFilter: "blur(20px)",
              border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, zIndex: 30, padding: 4,
              boxShadow: "0 20px 60px rgba(0,0,0,0.60), 0 0 0 1px rgba(255,255,255,0.03)",
            }}>
              <div style={{
                fontSize: 8, fontFamily: "'Geist Mono', monospace", color: "rgba(255,255,255,0.25)",
                letterSpacing: "0.08em", textTransform: "uppercase", padding: "8px 10px 4px",
              }}>
                Add column
              </div>
              {pickerItems(pickField).map((item, idx) => (
                <div
                  key={item.field}
                  onClick={() => dockColumnAt(item.field, item.zone)}
                  style={{
                    padding: "8px 10px", borderRadius: 8, fontSize: 11, color: "rgba(255,255,255,0.80)",
                    cursor: "pointer", fontFamily: "'Geist Sans', system-ui, sans-serif",
                    transition: "background 120ms ease, color 120ms ease",
                    borderBottom: idx < pickerItems(pickField).length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none",
                    display: "flex", alignItems: "center", gap: 8,
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.06)"; e.currentTarget.style.color = "#FFFFFF"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "rgba(255,255,255,0.80)"; }}
                >
                  <span style={{
                    width: 6, height: 6, borderRadius: "50%",
                    background: PASTEL_COLORS[idx % PASTEL_COLORS.length],
                    flexShrink: 0,
                  }} />
                  {item.label}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Lock/Unlock Toggle in bottom-center */}
      <div
        onClick={() => setIsLocked(!isLocked)}
        title={isLocked ? "Unlock Graph Layout (Allows pan, zoom, drag & dock)" : "Lock Graph Layout (Disables pan, zoom, drag & dock)"}
        style={{
          position: "absolute",
          bottom: 24,
          left: "50%",
          transform: "translateX(-50%)",
          width: 38,
          height: 38,
          borderRadius: "50%",
          background: isLocked ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.05)",
          backdropFilter: "blur(12px)",
          border: isLocked ? "1px solid rgba(239,68,68,0.4)" : "1px solid rgba(255,255,255,0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 100,
          color: isLocked ? "#f87171" : "rgba(255,255,255,0.5)",
          boxShadow: isLocked ? "0 0 15px rgba(239,68,68,0.2)" : "0 4px 12px rgba(0,0,0,0.5)",
          transition: "all 200ms ease",
        }}
      >
        {isLocked ? <Lock size={16} /> : <Unlock size={16} />}
      </div>
    </div>
  );
});

function InsertBtn({ x, y, onClick }: { x: number; y: number; onClick: () => void }) {
  const [over, setOver] = useState(false);
  return (
    <div
      style={{
        position: "absolute", left: x, top: y, width: 26, height: 26, borderRadius: "50%",
        background: over
          ? "rgba(255,255,255,0.15)"
          : "rgba(255,255,255,0.04)",
        border: over
          ? "1.5px solid rgba(255,255,255,0.40)"
          : "1px solid rgba(255,255,255,0.08)",
        display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", zIndex: 20,
        transition: "background 180ms ease, border-color 180ms ease, transform 180ms ease, box-shadow 180ms ease",
        transform: over ? "scale(1.2)" : "scale(1)",
        boxShadow: over ? "0 0 18px rgba(255,255,255,0.12), 0 0 0 1px rgba(255,255,255,0.06)" : "none",
      }}
      onMouseEnter={() => setOver(true)}
      onMouseLeave={() => setOver(false)}
      onClick={(e) => { e.stopPropagation(); onClick(); }}
    >
      <Plus size={14} strokeWidth={2.5} color={over ? "#FFFFFF" : "rgba(255,255,255,0.45)"} />
    </div>
  );
}

KnowledgeGraph.displayName = "KnowledgeGraph";
export default KnowledgeGraph;
