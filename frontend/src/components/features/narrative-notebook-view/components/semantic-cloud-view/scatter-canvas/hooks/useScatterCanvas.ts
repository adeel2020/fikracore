"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  CanvasPoint,
  ClusteringDimension,
  DashboardFeedResponse,
  SemanticPoint,
  TerritoryOffset,
  ViewMode,
} from "../../types/semantic-cloud.types";
import { computeDistribution } from "../../utils/normalizeCloud";
import { getDashboardFeed } from "../../hooks/useDashboardFeedCache";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const CLOUD_RADIUS = 8;

interface UseScatterCanvasResult {
  data: SemanticPoint[];
  targetPositions: [number, number, number][];
  territoryOffsets: TerritoryOffset[];
  distribution: Record<string, number>;
  total: number;
  eigenvalues: number[];
  clusters: [string, number][];
  loading: boolean;
  error: string | null;
}

function centerAndScale(points: CanvasPoint[]): SemanticPoint[] {
  if (points.length === 0) return [];

  const mean = points.reduce<[number, number, number]>(
    (acc, point) => {
      acc[0] += point.x;
      acc[1] += point.y;
      acc[2] += point.z;
      return acc;
    },
    [0, 0, 0],
  );

  mean[0] /= points.length;
  mean[1] /= points.length;
  mean[2] /= points.length;

  let maxRadius = 0;
  for (const point of points) {
    const dx = point.x - mean[0];
    const dy = point.y - mean[1];
    const dz = point.z - mean[2];
    maxRadius = Math.max(maxRadius, Math.hypot(dx, dy, dz));
  }

  const scale = maxRadius > 0 ? CLOUD_RADIUS / maxRadius : 1;

  return points.map((point) => ({
    ...point,
    category: point.issue_category,
    x: (point.x - mean[0]) * scale,
    y: (point.y - mean[1]) * scale,
    z: (point.z - mean[2]) * scale,
    centrality: typeof point.centrality === "number" ? point.centrality : point.opacity_score ?? 0,
    eigenvectors: point.eigenvectors ?? [],
  }));
}

function groupKey(point: SemanticPoint, dimension: ClusteringDimension): string {
  return dimension === "reason"
    ? point.reassignment_reason || "(unassigned)"
    : point.category || point.issue_category || "(uncategorized)";
}

function territoryOffset(index: number, total: number): [number, number, number] {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const radius = 12 + Math.floor(index / 6) * 2.5;
  return [
    Math.cos(angle) * radius,
    Math.sin(angle) * radius,
    0,
  ];
}

function principalAxis(points: [number, number, number][]): [number, number, number] {
  if (points.length < 2) return [1, 0, 0];

  let cx = 0;
  let cz = 0;
  for (const p of points) {
    cx += p[0];
    cz += p[2];
  }
  cx /= points.length;
  cz /= points.length;

  let px = 1;
  let pz = 0;

  for (let iteration = 0; iteration < 12; iteration += 1) {
    let nx = 0;
    let nz = 0;

    for (const p of points) {
      const dx = p[0] - cx;
      const dz = p[2] - cz;
      const dot = dx * px + dz * pz;
      nx += dx * dot;
      nz += dz * dot;
    }

    const norm = Math.hypot(nx, nz) || 1;
    px = nx / norm;
    pz = nz / norm;
  }

  return [px, 0, pz];
}

function computeTargets(
  data: SemanticPoint[],
  eigenvalues: number[],
  viewMode: ViewMode,
  clusteringDimension: ClusteringDimension,
): { targetPositions: [number, number, number][]; territoryOffsets: TerritoryOffset[] } {
  const basePositions = data.map((point) => [point.x, point.y, point.z] as [number, number, number]);

  if (viewMode === "global" || data.length === 0) {
    return { targetPositions: basePositions, territoryOffsets: [] };
  }

  const groups = new Map<string, number[]>();
  data.forEach((point, index) => {
    const key = groupKey(point, clusteringDimension);
    const bucket = groups.get(key);
    if (bucket) bucket.push(index);
    else groups.set(key, [index]);
  });

  const entries = Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b));
  const territories = entries.map(([key, indices], index) => {
    const offset = territoryOffset(index, entries.length);
    const centroid = indices.reduce<[number, number, number]>(
      (acc, pointIndex) => {
        const position = basePositions[pointIndex];
        acc[0] += position[0];
        acc[1] += position[1];
        acc[2] += position[2];
        return acc;
      },
      [0, 0, 0],
    );

    centroid[0] /= indices.length;
    centroid[1] /= indices.length;
    centroid[2] /= indices.length;

    const axis = principalAxis(indices.map((pointIndex) => basePositions[pointIndex]));
    const eigenvalue = eigenvalues[index % Math.max(eigenvalues.length, 1)] ?? 1;

    return {
      key,
      offset,
      centroid,
      eigenvalue,
      axis,
      label: key,
    };
  });

  const territoryMap = new Map(territories.map((territory) => [territory.key, territory]));
  const targetPositions = data.map((point, index) => {
    const territory = territoryMap.get(groupKey(point, clusteringDimension));
    const position = basePositions[index];
    if (!territory) return position;
    return [
      position[0] + territory.offset[0],
      position[1] + territory.offset[1],
      position[2] + territory.offset[2],
    ] as [number, number, number];
  });

  return { targetPositions, territoryOffsets: territories };
}

export function useScatterCanvas(
  refreshKey: number,
  viewMode: ViewMode,
  clusteringDimension: ClusteringDimension,
): UseScatterCanvasResult {
  const [rawData, setRawData] = useState<SemanticPoint[]>([]);
  const [eigenvalues, setEigenvalues] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (!cancelled) {
        setLoading(true);
        setError(null);
      }
    });

    getDashboardFeed(refreshKey)
      .then((payload) => {
        if (cancelled) return;
        setRawData(centerAndScale(payload.ui_cloud_data ?? []).filter(
          (p) => 
            (p.reassignment_reason && p.reassignment_reason !== "(unassigned)" && p.reassignment_reason !== "reassignment_na") ||
            (p.rejection_reason && p.rejection_reason !== "rejection_na" && p.rejection_reason !== "") ||
            (p.resolution_reason && p.resolution_reason !== "resolution_na" && p.resolution_reason !== "")
        ));
        setEigenvalues(payload.eigenvalues ?? []);
      })
      .catch((exception: unknown) => {
        if (cancelled) return;
        const message = exception instanceof Error ? exception.message : "Failed to load canvas data";
        setError(
          message.includes("Semantic cache not found") || message.includes("cache has not been built")
            ? "Cache not built yet — upload operational data first."
            : message,
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const distribution = useMemo(() => computeDistribution(rawData), [rawData]);

  const { targetPositions, territoryOffsets } = useMemo(
    () => computeTargets(rawData, eigenvalues, viewMode, clusteringDimension),
    [rawData, eigenvalues, viewMode, clusteringDimension],
  );

  const clusters = useMemo(() => {
    const counts = new Map<string, number>();
    for (const point of rawData) {
      const key = point.reassignment_reason || "(unassigned)";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [rawData]);

  return {
    data: rawData,
    targetPositions,
    territoryOffsets,
    distribution,
    total: rawData.length,
    eigenvalues,
    clusters,
    loading,
    error,
  };
}
