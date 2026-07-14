import { useState, useEffect } from "react";

export interface HeatmapCell {
  row: number;
  col: number;
  value: number;
  count: number;
}

export interface CrosstabData {
  rowLabels: string[];
  colLabels: string[];
  values: HeatmapCell[];
}

function getField(r: any, ...keys: string[]): string {
  for (const k of keys) {
    const v = r[k];
    if (v !== undefined && v !== null && v !== "") return String(v).trim();
  }
  return "";
}

function computeCrosstab(rows: any[], rowKey: string, altRowKey: string, colKey: string, fixedCols?: string[]): CrosstabData {
  const rowVals = [...new Set(rows.map(r => getField(r, rowKey, altRowKey)).filter(Boolean))];
  const colVals = fixedCols || [...new Set(rows.map(r => getField(r, colKey)).filter(Boolean))];

  const counts: Record<string, Record<string, number>> = {};
  rowVals.forEach(r => {
    counts[r] = {};
    colVals.forEach(c => { counts[r][c] = 0; });
  });

  rows.forEach(r => {
    const rv = getField(r, rowKey, altRowKey);
    const cv = getField(r, colKey);
    if (rv && cv && rowVals.includes(rv) && colVals.includes(cv)) {
      counts[rv][cv]++;
    }
  });

  const rowTotals: Record<string, number> = {};
  rowVals.forEach(rv => {
    rowTotals[rv] = Object.values(counts[rv]).reduce((a: number, b: number) => a + b, 0);
  });

  const colTotals: Record<string, number> = {};
  colVals.forEach(cv => {
    colTotals[cv] = rowVals.reduce((sum, rv) => sum + counts[rv][cv], 0);
  });

  const grandTotal = Object.values(rowTotals).reduce((a: number, b: number) => a + b, 0);

  const sortedRows = [...rowVals].sort((a, b) => {
    const maxA = Math.max(...colVals.map(cv => counts[a][cv]));
    const maxB = Math.max(...colVals.map(cv => counts[b][cv]));
    return maxB - maxA;
  });
  const sortedCols = [...colVals].sort((a, b) => {
    const maxA = Math.max(...rowVals.map(rv => counts[rv][a]));
    const maxB = Math.max(...rowVals.map(rv => counts[rv][b]));
    return maxB - maxA;
  });

  const values: HeatmapCell[] = [];
  sortedRows.forEach((rv, ri) => {
    sortedCols.forEach((cv, ci) => {
      const c = counts[rv][cv];
      const pct = grandTotal > 0 ? (c / grandTotal) * 100 : 0;
      values.push({ row: ri, col: ci, value: Math.round(pct * 10) / 10, count: c });
    });
  });

  return { rowLabels: sortedRows, colLabels: sortedCols, values };
}

export interface MonthlyTrendPoint {
  month: string;
  count: number;
  [key: string]: any;
}

export function useAnalysis() {
  const [loading, setLoading] = useState(true);
  const [queueVsReassigned, setQueueVsReassigned] = useState<CrosstabData | null>(null);
  const [issuesVsReassigned, setIssuesVsReassigned] = useState<CrosstabData | null>(null);
  const [reassignmentReasonVsReassigned, setReassignmentReasonVsReassigned] = useState<CrosstabData | null>(null);
  const [queueVsIssues, setQueueVsIssues] = useState<CrosstabData | null>(null);
  const [issuesVsReasons, setIssuesVsReasons] = useState<CrosstabData | null>(null);
  const [monthlyTrendData, setMonthlyTrendData] = useState<MonthlyTrendPoint[]>([]);
  const [mean, setMean] = useState(0);
  const [stdDev, setStdDev] = useState(0);
  const [topIssuesList, setTopIssuesList] = useState<string[]>([]);
  const [topReasonsList, setTopReasonsList] = useState<string[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const stored = typeof window !== "undefined" ? localStorage.getItem("uploaded_telemetry") : null;
        let rows: any[] = [];
        if (stored) {
          try {
            rows = JSON.parse(stored);
          } catch (e) {}
        }
        if (!rows || rows.length === 0) {
          const res = await fetch("/Operations_Dashboard_Data_Template.json");
          rows = await res.json();
        }

        const filtered = rows.filter((r: any) => {
          const q = getField(r, "Ticket_Queue", "Queue");
          return q !== "IN" && q !== "RAN";
        });

        const reassigned = filtered.filter((r: any) => getField(r, "Ticket_Status", "Status") === "Reassigned");
        const reassignedWithReason = reassigned.filter((r: any) => getField(r, "Reassignment_Reason").trim() !== "");

        // Discover top 5 issue categories and top 5 reassignment reasons dynamically
        const catCountsMap: Record<string, number> = {};
        const reasonCountsMap: Record<string, number> = {};
        rows.forEach((r: any) => {
          const cat = getField(r, "Issue_Category", "Category");
          if (cat) catCountsMap[cat] = (catCountsMap[cat] || 0) + 1;
          const reason = getField(r, "Reassignment_Reason");
          if (reason && reason.trim() !== "") reasonCountsMap[reason] = (reasonCountsMap[reason] || 0) + 1;
        });

        const topIssues = Object.keys(catCountsMap)
          .sort((a, b) => catCountsMap[b] - catCountsMap[a])
          .slice(0, 5);
        const topReasons = Object.keys(reasonCountsMap)
          .sort((a, b) => reasonCountsMap[b] - reasonCountsMap[a])
          .slice(0, 5);

        setTopIssuesList(topIssues);
        setTopReasonsList(topReasons);

        setQueueVsReassigned(computeCrosstab(reassigned, "Ticket_Queue", "Queue", "Reassigned_To"));
        setIssuesVsReassigned(computeCrosstab(reassigned, "Issue_Category", "Category", "Reassigned_To"));
        setReassignmentReasonVsReassigned(computeCrosstab(reassignedWithReason, "Reassignment_Reason", "Reassignment_Reason", "Reassigned_To"));
        setQueueVsIssues(computeCrosstab(filtered, "Issue_Category", "Category", "Ticket_Queue"));
        setIssuesVsReasons(computeCrosstab(reassigned, "Issue_Category", "Category", "Reassignment_Reason", topReasons));

        // Compute Monthly Trend & Statistics
        const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const monthlyCounts = Array(12).fill(0);

        // Track monthly counts for dynamic top issues and reasons
        const issueCountsMap: Record<string, number[]> = {};
        topIssues.forEach(issue => {
          issueCountsMap[issue] = Array(12).fill(0);
        });

        const reasonCountsMapMonthly: Record<string, number[]> = {};
        topReasons.forEach(reason => {
          reasonCountsMapMonthly[reason] = Array(12).fill(0);
        });

        rows.forEach((r: any) => {
          const ds = r.Create_Date || "";
          const parts = ds.split("-");
          if (parts.length === 3) {
            const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
            if (!isNaN(dt.getTime())) {
              const monthIdx = dt.getMonth();
              if (monthIdx >= 0 && monthIdx < 12) {
                // 1. Overall monthly count
                monthlyCounts[monthIdx]++;

                // 2. Dynamic top issues counts
                const cat = getField(r, "Issue_Category", "Category");
                if (cat && issueCountsMap[cat]) {
                  issueCountsMap[cat][monthIdx]++;
                }

                // 3. Dynamic top reasons counts
                const reason = getField(r, "Reassignment_Reason");
                if (reason && reasonCountsMapMonthly[reason]) {
                  reasonCountsMapMonthly[reason][monthIdx]++;
                }
              }
            }
          }
        });

        const total = monthlyCounts.reduce((a, b) => a + b, 0);
        const calculatedMean = total > 0 ? total / 12 : 0;

        const variance = total > 0 
          ? monthlyCounts.reduce((sum, count) => sum + Math.pow(count - calculatedMean, 2), 0) / 12 
          : 0;
        const calculatedStdDev = Math.sqrt(variance);

        // Calculate MoM deltas for top issues
        const issueDeltasAbs: Record<string, number[]> = {};
        const issueDeltasPct: Record<string, number[]> = {};
        topIssues.forEach(issue => {
          issueDeltasAbs[issue] = Array(12).fill(0);
          issueDeltasPct[issue] = Array(12).fill(0);
          const counts = issueCountsMap[issue];
          for (let i = 0; i < 12; i++) {
            if (i === 0) continue;
            const prevVal = counts[i - 1];
            const currVal = counts[i];
            issueDeltasAbs[issue][i] = currVal - prevVal;
            issueDeltasPct[issue][i] = prevVal > 0 
              ? Math.round(((currVal - prevVal) / prevVal) * 100)
              : 0;
          }
        });

        // Calculate MoM deltas for top reasons
        const reasonDeltasAbs: Record<string, number[]> = {};
        const reasonDeltasPct: Record<string, number[]> = {};
        topReasons.forEach(reason => {
          reasonDeltasAbs[reason] = Array(12).fill(0);
          reasonDeltasPct[reason] = Array(12).fill(0);
          const counts = reasonCountsMapMonthly[reason];
          for (let i = 0; i < 12; i++) {
            if (i === 0) continue;
            const prevVal = counts[i - 1];
            const currVal = counts[i];
            reasonDeltasAbs[reason][i] = currVal - prevVal;
            reasonDeltasPct[reason][i] = prevVal > 0 
              ? Math.round(((currVal - prevVal) / prevVal) * 100)
              : 0;
          }
        });

        const trendPoints = months.map((m, idx) => {
          const point: MonthlyTrendPoint = {
            month: m,
            count: monthlyCounts[idx]
          };

          topIssues.forEach(issue => {
            point[issue] = issueCountsMap[issue][idx];
            point[`${issue}_deltaAbs`] = issueDeltasAbs[issue][idx];
            point[`${issue}_deltaPct`] = issueDeltasPct[issue][idx];
          });

          topReasons.forEach(reason => {
            point[reason] = reasonCountsMapMonthly[reason][idx];
            point[`${reason}_deltaAbs`] = reasonDeltasAbs[reason][idx];
            point[`${reason}_deltaPct`] = reasonDeltasPct[reason][idx];
          });

          return point;
        });

        setMonthlyTrendData(trendPoints);
        setMean(calculatedMean);
        setStdDev(calculatedStdDev);
      } catch (e) {
        console.error("Failed to load analysis data:", e);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return {
    queueVsReassigned,
    issuesVsReassigned,
    reassignmentReasonVsReassigned,
    queueVsIssues,
    issuesVsReasons,
    monthlyTrendData,
    mean,
    stdDev,
    loading,
    topIssuesList,
    topReasonsList
  };
}
