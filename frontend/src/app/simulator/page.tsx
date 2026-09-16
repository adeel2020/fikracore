import { redirect } from "next/navigation";

/**
 * /simulator redirects to /simulator/investigate (default workspace).
 */
export default function SimulatorPage({
  searchParams,
}: {
  searchParams?: { scenario?: string; run?: string };
}) {
  const scenario = searchParams?.scenario || "DEMO-001";
  const run = searchParams?.run;
  const qs = [scenario && `scenario=${scenario}`, run && `run=${run}`]
    .filter(Boolean)
    .join("&");
  redirect(`/simulator/investigate${qs ? `?${qs}` : ""}`);
}
