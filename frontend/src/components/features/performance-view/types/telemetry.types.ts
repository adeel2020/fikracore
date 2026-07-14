export interface SparklineDataPoint {
  d: string;
  v: number;
}

export interface ThroughputDataPoint {
  h: string;
  v: number;
}

export interface QueryDistDataPoint {
  name: string;
  value: number;
  color: string;
}

export interface Task {
  id: string;
  label: string;
  status: "planning" | "executing" | "verifying" | "queued" | "complete";
  progress: number;
}

export interface VectorDensityDataPoint {
  index: number;
  score: number;
}

export interface GraphHopsData {
  "1-Hop": number;
  "2-Hop": number;
  "3-Hop": number;
}

export interface WeightDataPoint {
  name: string;
  weight: number;
}

export interface LatencyDataPoint {
  t: number;
  v: number;
}

// ─── Color Tokens ───────────────────────────────────────────────────────────
export const C = {
  purple: "#A855F7",
  purpleSoft: "#C084FC",
  purpleDark: "#8B5CF6",
  blue: "#22D3EE",
  blueSoft: "#60A5FA",
  lime: "#CCFF00",
  magenta: "#FF00FF",
  cyan: "#00E5FF",
  orange: "#FB923C",
  orangeHot: "#FF6B35",
  yellow: "#FFE500",
  green: "#00FF87",
  greenGlow: "#10B981",
  pink: "#FF1493",
  red: "#FF4444",
  teal: "#2DD4BF",
  indigo: "#818CF8",
  rose: "#F43F5E",
  white: "#FFFFFF",
} as const;

export const iconStroke = { strokeWidth: 1.5 } as const;
