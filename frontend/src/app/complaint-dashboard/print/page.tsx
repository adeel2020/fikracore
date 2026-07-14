"use client";

import React, { useState, useEffect, useRef } from "react";
import { fetchComplaintsTelemetry } from "@/lib/api/qna";
import { dispatchStorageEvent } from "@/lib/useLocalStorageData";
import {
  WeeklyComplaintVolume,
  TopRoamingComplaints,
  TelemetryCalendar
} from "@/components/features/complaint-dashboard-view/components/SpatialTrafficTrends";
import {
  AvgQueueTime,
  TotalTicketDistribution,
  TopComplaintCategories
} from "@/components/features/complaint-dashboard-view/components/QueuePerformanceAnalytics";
import {
  TroubleTicketsHandled30Days,
  TopReassignmentsQueue,
  TopRejectionReason,
  PercentageNocTickets
} from "@/components/features/complaint-dashboard-view/components/CoreOperationalMetrics";
import { EarlyWarningDiagnostics } from "@/components/features/complaint-dashboard-view/components/EarlyWarningDiagnostics";

export default function ComplaintDashboardPrintPage() {
  const [loading, setLoading] = useState(true);
  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    // Instantiate background Web Worker for regex database mappings and aggregation
    workerRef.current = new Worker(
      new URL("../../../../../../frontend/src/components/features/complaint-dashboard-view/workers/telemetry.worker.ts", import.meta.url)
    );

    workerRef.current.onmessage = (e: MessageEvent) => {
      const { type, result } = e.data;
      if (type === "PARSE_AND_AGGREGATE_DB_SUCCESS" || type === "AGGREGATE_RAW_TICKETS_SUCCESS") {
        const aggregatedStr = JSON.stringify(result);
        localStorage.setItem("dashboard_data", aggregatedStr);
        dispatchStorageEvent("dashboard_data", aggregatedStr);
        setLoading(false);
      }
    };

    loadTelemetry();

    return () => {
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  const loadTelemetry = async () => {
    try {
      let data: any[] = [];
      let isJsonTemplate = false;
      try {
        const res = await fetch("/Operations_Dashboard_Data_Template.json");
        if (res.ok) {
          const json = await res.json();
          if (Array.isArray(json) && json.length > 0) {
            data = json;
            isJsonTemplate = true;
          }
        }
      } catch (err) {
        console.error("Failed to fetch default JSON telemetry template:", err);
      }

      if (data.length === 0) {
        data = await fetchComplaintsTelemetry();
      }

      if (data.length > 0) {
        if (workerRef.current) {
          if (isJsonTemplate) {
            workerRef.current.postMessage({
              type: "AGGREGATE_RAW_TICKETS",
              data
            });
          } else {
            workerRef.current.postMessage({
              type: "PARSE_AND_AGGREGATE_DB",
              data
            });
          }
        }
      } else {
        setLoading(false);
      }
    } catch (error) {
      console.error("Error loading complaints telemetry:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0B0F19] text-white">
        <span className="text-sm font-semibold tracking-wider animate-pulse">
          PREPARING TELEMETRY CHARTS...
        </span>
      </div>
    );
  }

  return (
    <div className="p-6 bg-[#0B0F19] text-white flex flex-col gap-6 max-w-[500px]" id="complaint-dashboard-content">
      <div id="weekly-volume-card">
        <WeeklyComplaintVolume />
      </div>
      <div id="roaming-complaints-card">
        <TopRoamingComplaints />
      </div>
      <div id="avg-queue-times-card">
        <AvgQueueTime />
      </div>
      <div id="ticket-distribution-card">
        <TotalTicketDistribution />
      </div>
      <div id="top-complaint-categories-card">
        <TopComplaintCategories />
      </div>
      <div id="trouble-tickets-card">
        <TroubleTicketsHandled30Days />
      </div>
      <div id="reassignments-card">
        <TopReassignmentsQueue />
      </div>
      <div id="rejection-reason-card">
        <TopRejectionReason />
      </div>
      <div id="noc-tickets-card">
        <PercentageNocTickets />
      </div>
      <div id="early-warning-card">
        <EarlyWarningDiagnostics />
      </div>
      <div id="telemetry-calendar-card">
        <TelemetryCalendar selectedDate={null} onSelectDate={() => {}} />
      </div>
    </div>
  );
}
