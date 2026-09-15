import { redirect } from "next/navigation";

/**
 * /simulator redirects to /simulator/investigate (default workspace).
 */
export default function SimulatorPage({
  searchParams,
}: {
  searchParams?: { scenario?: string; run?: string };
}) {
  const scenario = searchParams?.scenario || "H4-WI-001";
  const run = searchParams?.run;
  const qs = [scenario && `scenario=${scenario}`, run && `run=${run}`]
    .filter(Boolean)
    .join("&");
  redirect(`/simulator/investigate${qs ? `?${qs}` : ""}`);
}
