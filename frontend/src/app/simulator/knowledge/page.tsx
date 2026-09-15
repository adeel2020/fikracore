import { WorkspacePage } from "../_components/workspace-page";

export default function KnowledgePage() {
  return (
    <WorkspacePage
      config={{
        workspace: "knowledge",
        title: "Knowledge Core",
        subtitle: "Domain/service coverage, knowledge states, gaps, orphans, and stale records.",
        capability: "Step 4.7 / inspect knowledge",
        emptyTitle: "No knowledge inventory available",
        emptyBody: "The workspace is connected to the active scenario context, but the backend has not returned inventory data yet.",
      }}
    />
  );
}
