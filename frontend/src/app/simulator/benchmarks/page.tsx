import { WorkspacePage } from "../_components/workspace-page";

export default function BenchmarksPage() {
  return (
    <WorkspacePage
      config={{
        workspace: "benchmarks",
        title: "Benchmarks",
        subtitle: "H1-H4 result summaries, MCP parity, regression health, and calibration trends.",
        capability: "benchmark artifacts / regression reports",
        emptyTitle: "No benchmark state available",
        emptyBody: "Benchmark artifacts are not present in the current simulation payload. Run the backend benchmark suite to populate this view.",
      }}
    />
  );
}
