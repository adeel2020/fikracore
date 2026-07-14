import { ComplaintDashboardView } from "@/components/features/complaint-dashboard-view";
import { Suspense } from "react";

export default function ComplaintDashboardPage() {
  return (
    <div style={{ height: "calc(100dvh - 72px)", display: "flex", flexDirection: "column" }}>
      <Suspense fallback={<div>Loading...</div>}>
        <ComplaintDashboardView />
      </Suspense>
    </div>
  );
}
