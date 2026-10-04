import { redirect } from "next/navigation";

/**
 * /simulator redirects to /simulator/investigate (default workspace).
 */
export default async function SimulatorPage({
  searchParams,
}: {
  searchParams?: Promise<{ scenario?: string; run?: string }>;
}) {
  const resolvedParams = searchParams ? await searchParams : {};
  const scenario = resolvedParams?.scenario;
  const run = resolvedParams?.run;
  const qs = [scenario && `scenario=${scenario}`, run && `run=${run}`]
    .filter(Boolean)
    .join("&");
  redirect(`/simulator/investigate${qs ? `?${qs}` : ""}`);
}
