export interface StructuredAgentResponse {
  issue_summary: string;
  mandatory_prechecks: string[];
  depends_on: string[];
  assignment_target: string;
  message?: string | null;
}
