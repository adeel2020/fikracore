import { WorkspacePage } from "../_components/workspace-page";

export default function LearnPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "learn",
        title: "Learn",
        subtitle: "Candidate knowledge, SME validation, promotion, and rollback state.",
        capability: "H3 / learn",
        emptyTitle: "No learning state available",
        emptyBody: "The active scenario has not exposed candidate or promoted knowledge. Switch to an H3/H4 scenario or continue evidence collection.",
      }}
    />
  );
}
