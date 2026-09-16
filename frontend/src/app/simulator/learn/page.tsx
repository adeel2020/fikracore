import { WorkspacePage } from "../_components/workspace-page";

export default function LearnPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "learn",
        title: "Learn",
        subtitle: "Candidate knowledge, SME validation, promotion, and rollback state.",
        capability: "Learn",
        emptyTitle: "No learning state available",
        emptyBody: "The active scenario has not exposed candidate or promoted knowledge. Switch to a Learn or Anticipate scenario or continue evidence collection.",
      }}
    />
  );
}
