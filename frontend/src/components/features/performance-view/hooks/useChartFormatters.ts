import { SparklineDataPoint, ThroughputDataPoint, QueryDistDataPoint } from "../types/telemetry.types";

export const getThroughputData = (throughput: number): ThroughputDataPoint[] => [
  { h: "0", v: 12 },
  { h: "2", v: 18 },
  { h: "4", v: 14 },
  { h: "6", v: 22 },
  { h: "8", v: 28 },
  { h: "10", v: 24 },
  { h: "12", v: 32 },
  { h: "14", v: 38 },
  { h: "16", v: 30 },
  { h: "18", v: throughput },
  { h: "20", v: 28 },
  { h: "22", v: 22 },
  { h: "24", v: 25 },
];

export const getMemSparkData = (systemLoad: number): SparklineDataPoint[] => [
  { d: "Sun", v: 40 },
  { d: "Mon", v: 55 },
  { d: "Tue", v: systemLoad },
  { d: "Wed", v: 60 },
  { d: "Thu", v: 80 },
  { d: "Fri", v: 72 },
  { d: "Sat", v: 65 },
];

export const getCacheSparkData = (systemLoad: number): SparklineDataPoint[] => [
  { d: "Sun", v: 30 },
  { d: "Mon", v: 35 },
  { d: "Tue", v: 50 },
  { d: "Wed", v: 45 },
  { d: "Thu", v: systemLoad * 0.6 },
  { d: "Fri", v: 55 },
  { d: "Sat", v: 42 },
];

export const getQueryDistData = (
  queryPieData: number[],
  colors: { green: string; blue: string; orange: string }
): QueryDistDataPoint[] => [
  { name: "Knowledge-RAG", value: Math.max(10, queryPieData[0] || 0), color: colors.green },
  { name: "Action", value: Math.max(5, queryPieData[1] || 0), color: colors.blue },
  { name: "Creative", value: Math.max(3, queryPieData[2] || 0), color: colors.orange },
];
