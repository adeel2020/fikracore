import { WorkspacePage } from "../_components/workspace-page";

export default function DiscoverPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "discover",
        title: "Discover",
        subtitle: "Knowledge gap and unknown boundary analysis.",
        capability: "Discover",
        emptyTitle: "No discover state available",
        emptyBody: "This scenario has no knowledge-gap payload yet. Select a scenario with Discover support or run evidence collection from the simulator.",
      }}
    />
  );
}
