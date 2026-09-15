import { WorkspacePage } from "../_components/workspace-page";

export default function LabPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "lab",
        title: "Simulator Lab",
        subtitle: "Scenario library, run controls, replay, and run comparison context.",
        capability: "scenario registry / simulation lifecycle",
        emptyTitle: "No simulator lab state available",
        emptyBody: "Scenario registry or simulation state is unavailable. Refresh the backend scenario registry to continue.",
      }}
    />
  );
}
