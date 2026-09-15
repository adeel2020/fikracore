import { WorkspacePage } from "../_components/workspace-page";

export default function DiscoverPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "discover",
        title: "Discover",
        subtitle: "Knowledge gap and unknown boundary analysis.",
        capability: "H2 / discover",
        emptyTitle: "No discover state available",
        emptyBody: "This scenario has no knowledge-gap payload yet. Select a scenario with H2 support or run evidence collection from the simulator.",
      }}
    />
  );
}
