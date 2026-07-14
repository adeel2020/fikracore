export interface SemanticPoint {
  id: string;
  ticket_queue: string;
  issue_category: string;
  category?: string;
  reassignment_reason: string;
  rejection_reason?: string;
  resolution_reason?: string;
  reassigned_to?: string;
  is_anomaly: boolean;
  centrality?: number;
  tooltip?: string;
  color_axis?: number;
  opacity_score?: number;
  x: number;
  y: number;
  z: number;
  eigenvectors: number[][];
}

export type CanvasPoint = SemanticPoint;

export interface ClusterSummary {
  theme: string;
  volume: string;
  highest_centrality_example: string;
  anomalies_to_investigate: string[];
  complaints_count?: number;
  service_journeys?: string[];
  ticket_queues?: string[];
  reassigned_to?: string[];
}

export interface NarrativeStream {
  dominant_operational_axis: string;
  total_tickets: number;
  clusters: ClusterSummary[];
}

export interface ClusterStory {
  id: number;
  theme: string;
  volume: string;
  dominant_axis: string;
  exemplar: string;
  anomalies: string[];
  summary: string;
  complaints_count: number;
  service_journeys: string[];
  ticket_queues: string[];
  reassigned_to: string[];
}

export interface DashboardFeedResponse {
  ui_cloud_data: CanvasPoint[];
  ai_executive_brief: string;
  cluster_stories: ClusterStory[];
  eigenvalues: number[];
  available_fields?: string[];
}

export interface UploadResponse {
  status: string;
}

export type ViewMode = "global" | "federated";
export type ClusteringDimension = "reason" | "category";

export interface TerritoryOffset {
  key: string;
  offset: [number, number, number];
  centroid: [number, number, number];
  eigenvalue: number;
  axis: [number, number, number];
  label: string;
}

export interface QueueCorrelation {
  queue: string;
  pct: string;
}

export interface TooltipInfo {
  ticketId: string;
  reason: string;
  queue: string;
  issue: string;
  centrality: number;
  coordinates: [number, number, number];
  eigenvectors: number[][];
  queueCorrelation: QueueCorrelation[];
}
