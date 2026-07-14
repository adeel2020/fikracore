import React from "react";
import {
  TopReassignmentsQueue,
  TopRejectionReason,
  PercentageNocTickets,
  TroubleTicketsHandled30Days
} from "./CoreOperationalMetrics";
import {
  AvgQueueTime,
  TotalTicketDistribution,
  TopComplaintCategories,
  SloMeterBar
} from "./QueuePerformanceAnalytics";
import {
  TopRoamingComplaints,
  WeeklyComplaintVolume,
  TelemetryCalendar
} from "./SpatialTrafficTrends";
import { EarlyWarningDiagnostics } from "./EarlyWarningDiagnostics";

interface AnalyticsViewProps {
  selectedDate: string | null;
  onSelectDate: (dateStr: string | null) => void;
}

export const AnalyticsView = React.memo(function AnalyticsView({
  selectedDate,
  onSelectDate
}: AnalyticsViewProps) {
  return (
    <div className="flex flex-col gap-4 w-full z-10 pb-6">
      {/* Row 1: Horizontal stats bar (2 + 2 + 3 + 2 + 2 + 1 = 12 columns) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 w-full">
        <div className="xl:col-span-2 col-span-1">
          <TopReassignmentsQueue />
        </div>
        <div className="xl:col-span-2 col-span-1">
          <TopComplaintCategories />
        </div>
        <div className="xl:col-span-3 col-span-1">
          <TopRoamingComplaints />
        </div>
        <div className="xl:col-span-1 col-span-1">
          <SloMeterBar />
        </div>
        <div className="xl:col-span-2 col-span-1">
          <TopRejectionReason />
        </div>
        <div className="xl:col-span-2 col-span-1">
          <PercentageNocTickets />
        </div>
      </div>

      {/* Main dashboard columns: Left, Center, Right stacked columns */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 w-full">
        {/* Column 1: Weekly Volume + Early Warning Dashboard */}
        <div className="flex flex-col gap-4 col-span-1 h-full">
          <WeeklyComplaintVolume />
          <EarlyWarningDiagnostics />
        </div>

        {/* Column 2: Ticket Distribution + Telemetry Calendar */}
        <div className="flex flex-col gap-4 col-span-1 h-full">
          <TotalTicketDistribution />
          <TelemetryCalendar selectedDate={selectedDate} onSelectDate={onSelectDate} />
        </div>

        {/* Column 3: Avg Time Spent in Queues + Trouble Tickets composed chart */}
        <div className="flex flex-col gap-4 col-span-1 h-full">
          <AvgQueueTime />
          <TroubleTicketsHandled30Days />
        </div>
      </div>
    </div>
  );
});

