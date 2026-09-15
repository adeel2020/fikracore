import { WorkspacePage } from "../_components/workspace-page";

export default function PredictPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "predict",
        title: "Predict",
        subtitle: "What-if propagation, blast radius, affected services, and mitigation comparison.",
        capability: "H4 / predict",
        emptyTitle: "No predictive state available",
        emptyBody: "The active scenario has no H4 what-if or blast-radius payload. Choose an H4-capable scenario from Simulator Lab.",
      }}
    />
  );
}
