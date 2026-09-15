import type { StorytellerPayload } from "@/lib/api/qna";
import type { MarkRouteTrace, MarkVisualState } from "@/lib/mark-capability-graph";

export type MarkPresentation = Pick<StorytellerPayload, "narrative" | "visual_explanation">;

export function presentationPayload(answer: string, spoken: string | undefined, presentation?: MarkPresentation): StorytellerPayload {
  return {
    incident_id: presentation?.narrative?.incident_id || presentation?.visual_explanation?.incident_id || "",
    intent: "story",
    answer,
    spoken_answer: spoken,
    ...presentation,
  };
}

export function presentationOrb(presentation?: MarkPresentation | null): string | null {
  const type = presentation?.visual_explanation?.primary_widget;
  if (!type) return null;
  if (/topology|domain|impact/.test(type)) return "digital-assets";
  if (/action/.test(type)) return "automation";
  if (/evidence/.test(type)) return "knowledge";
  if (/kpi/.test(type)) return "predictions";
  return "correlation";
}

export function presentationRouteTrace(
  state: MarkVisualState,
  presentation?: MarkPresentation | null
): MarkRouteTrace {
  const widgets = presentation?.visual_explanation?.widgets ?? [];
  const primaryType = presentation?.visual_explanation?.primary_widget ?? widgets[0]?.type ?? "";
  const widgetTypes = widgets.map((widget) => widget.type).join(" ");
  const text = `${primaryType} ${widgetTypes}`.toLowerCase();
  const activeServiceIds = new Set<string>();
  const activeConnectorIds = new Set<string>(["gbrain"]);
  const activeNamespaces = new Set<string>();

  if (/topology|domain|impact/.test(text)) {
    activeServiceIds.add("topology");
    activeConnectorIds.add("nautobot");
    activeNamespaces.add("twin/*");
    activeNamespaces.add("domains/*");
  }

  if (/evidence|kpi|timeline|metric|log|trace|alert/.test(text)) {
    activeServiceIds.add("telemetry_evidence");
    activeConnectorIds.add("grafana_lgtm");
    activeNamespaces.add("grafana/*");
  }

  if (/correlation|causal|hypothesis/.test(text)) {
    activeServiceIds.add("correlation");
    activeNamespaces.add("correlation/*");
  }

  if (presentation?.narrative || /story|narrative/.test(text)) {
    activeServiceIds.add("storytelling");
    activeNamespaces.add("storytelling/*");
    activeNamespaces.add("incidents/*");
  }

  if (presentation?.narrative?.next_actions?.length || /action/.test(text)) {
    activeServiceIds.add("fcaps_learning");
    activeNamespaces.add("learning/*");
    activeNamespaces.add("assets/*");
  }

  if (presentation?.narrative?.claims?.some((claim) => claim.fcaps?.length)) {
    activeServiceIds.add("fcaps_learning");
    activeNamespaces.add("learning/*");
  }

  if (/rtr|ticket|journey|aola|ola/.test(text)) {
    activeServiceIds.add("mobile_rtr_intelligence");
    activeNamespaces.add("rtr/*");
  }

  return {
    state,
    activeEngineId: "telecom_brain",
    activeServiceIds: Array.from(activeServiceIds),
    activeConnectorIds: Array.from(activeConnectorIds),
    activeNamespaces: Array.from(activeNamespaces),
    claimIds: presentation?.narrative?.claims?.map((claim) => claim.id).filter(Boolean),
    summary: primaryType || "telecom brain route",
  };
}

// =====================================================================
// MOBILE CORE RTR TICKET JOURNEY PRESENTATION CONTRACTS (ISOLATED)
// =====================================================================

export interface SynchronizedVisualHop {
  hop_number: number;
  assigned_queue: string;
  time_spent_hours: number;
  idle_waiting_hours: number;
  active_triage_hours: number;
  sla_status: "ACHIEVED" | "AT_RISK" | "BREACHED";
  cue_start_offset_ms: number;
  pause_duration_ms: number;
  spoken_cue_text: string;
  action_taken: string;
  finding_code?: string | null;
  reassignment_reason?: string | null;
  reassigned_to_queue?: string | null;
  is_bounced_back_to_rtr?: boolean;
}

export interface RTRJourneyOverlayPresentation {
  ticket_token: string;
  subscriber_token: string;
  current_status: string;
  aola_rtr_hours: number;
  aola_achieved: boolean;
  ola_noc_hours: number;
  ola_achieved: boolean;
  sla_e2e_hours: number;
  sla_achieved: boolean;
  delinquent_queue?: string | null;
  hops: SynchronizedVisualHop[];
  spoken_script?: string;
}

