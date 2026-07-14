import type { CanvasPoint } from "../types/semantic-cloud.types";

function robustRange(values: number[]): { min: number; max: number } {
  const sorted = [...values].sort((a, b) => a - b);
  const lo = Math.floor(0.01 * sorted.length);
  const hi = Math.floor(0.99 * sorted.length);
  return {
    min: sorted[lo],
    max: sorted[Math.min(hi, sorted.length - 1)],
  };
}

export function normalizeCloud(points: CanvasPoint[]): CanvasPoint[] {
  if (points.length < 2) return points;

  const { min: xMin, max: xMax } = robustRange(points.map((p) => p.x));
  const { min: yMin, max: yMax } = robustRange(points.map((p) => p.y));
  const { min: zMin, max: zMax } = robustRange(points.map((p) => p.z));

  const xRange = Math.max(xMax - xMin, 1e-12);
  const yRange = Math.max(yMax - yMin, 1e-12);
  const zRange = Math.max(zMax - zMin, 1e-12);

  return points.map((p) => ({
    ...p,
    x: (Math.max(xMin, Math.min(xMax, p.x)) - xMin) / xRange,
    y: (Math.max(yMin, Math.min(yMax, p.y)) - yMin) / yRange,
    z: (Math.max(zMin, Math.min(zMax, p.z)) - zMin) / zRange,
    eigenvectors: p.eigenvectors ?? [],
  }));
}

export function computeDistribution(
  points: CanvasPoint[],
): Record<string, number> {
  const dist: Record<string, number> = {};
  for (const p of points) {
    const axis = p.color_axis ?? 0;
    const key = String(axis);
    dist[key] = (dist[key] ?? 0) + 1;
  }
  return dist;
}
