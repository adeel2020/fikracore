import { CHART_COLORS } from "@/lib/chart-colors";

export interface SparklinePoint {
  v: number;
}

export interface LatencyBarPoint {
  name: string;
  v: number;
}

export interface ToolVolumePoint {
  day: string;
  v: number;
}

export interface TaskSuccessPoint {
  name: string;
  value: number;
  color: string;
}

export interface CollabWavesPoint {
  month: string;
  collaborators: number;
  commits: number;
}

export interface AgentSpecializationPoint {
  name: string;
  value: number;
  color: string;
}

export interface ProjectCostPoint {
  name: string;
  value: number;
  cost: string;
  color: string;
}

export const sparklineData: SparklinePoint[] = [
  { v: 60 }, { v: 72 }, { v: 68 }, { v: 85 }, { v: 73 },
];

export const latencyBarData: LatencyBarPoint[] = [
  { name: "00:00", v: 2400 }, { name: "04:00", v: 2900 },
  { name: "08:00", v: 3200 }, { name: "12:00", v: 2800 },
  { name: "16:00", v: 3500 }, { name: "20:00", v: 3100 },
];

export const toolVolumeData: ToolVolumePoint[] = [
  { day: "Mon", v: 420 }, { day: "Tue", v: 510 },
  { day: "Wed", v: 480 }, { day: "Thu", v: 620 },
  { day: "Fri", v: 710 }, { day: "Sat", v: 390 }, { day: "Sun", v: 306 },
];

export const taskSuccessData: TaskSuccessPoint[] = [
  { name: "Deployment A", value: 91, color: CHART_COLORS.neonCyan },
  { name: "Deployment B", value: 88, color: CHART_COLORS.neonMagenta },
  { name: "Deployment C", value: 94, color: CHART_COLORS.neonLime },
];

export const collabWavesData: CollabWavesPoint[] = [
  { month: "Oct", collaborators: 980, commits: 420 },
  { month: "Nov", collaborators: 1120, commits: 510 },
  { month: "Dec", collaborators: 1050, commits: 480 },
  { month: "Jan", collaborators: 1340, commits: 620 },
  { month: "Feb", collaborators: 1529, commits: 710 },
  { month: "Mar", collaborators: 1480, commits: 763 },
];

export const agentSpecializationData: AgentSpecializationPoint[] = [
  { name: "Knowledge Graph Agents", value: 75, color: CHART_COLORS.neonLime },
  { name: "RAG Retrieval Agents", value: 13, color: CHART_COLORS.neonMagenta },
  { name: "Action Execution Agents", value: 7, color: CHART_COLORS.neonOrange },
  { name: "Tool Calling Agents", value: 5, color: CHART_COLORS.electricBlue },
];

export const projectCostData: ProjectCostPoint[] = [
  { name: "Training Clusters", value: 31, cost: "$112.7M", color: CHART_COLORS.neonMagenta },
  { name: "Inference Nodes", value: 25, cost: "$89.2M", color: CHART_COLORS.neonBlue },
  { name: "Storage Tiers", value: 28, cost: "$94.8M", color: CHART_COLORS.neonCyan },
  { name: "API Gateways", value: 16, cost: "$65.3M", color: CHART_COLORS.neonOrange },
];

export const heatmapData: number[][] = Array.from({ length: 8 }, (_, ri) =>
  Array.from({ length: 16 }, (_, ci) => {
    const seed = (ri * 13 + ci * 7) % 101;
    return 0.1 + (seed / 100) * 0.9;
  })
);
