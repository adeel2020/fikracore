import { API_BASE } from "./config";

export type ChartOptionItem = {
  name: string;
  dom_id: string;
};

export type SkillItem = {
  name: string;
  description: string;
  role?: string;
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  thoughts?: string;
  statusSteps?: string[];
  persona?: string;
  durationSeconds?: number;
  created_at?: number;
  tokens_consumed?: number;
  tokens_per_second?: number;
  latency_ms?: number;
  structuredResponse?: {
    issue_summary: string;
    mandatory_prechecks: string[];
    depends_on: string[];
    assignment_target: string;
    message?: string | null;
  };
  chartOptions?: ChartOptionItem[];
  preSelectedDomId?: string | null;
  storyteller?: StorytellerPayload;
};

export type QnaTelemetry = {
  memory_pct: number;
  token_cache_pct: number;
  context_window: string;
  latency_ms: number;
  message_count: number;
  estimated_tokens: number;
  tokens_consumed?: number;
  token_cost?: number;
  tokens_per_second?: number;
};

export type HealthResponse = {
  status: string;
  agent_mode: string;
};

export type IncidentQueueItem = {
  incident_id: string;
  tenant_id: string;
  status: string;
  scope: "intra-domain" | "inter-domain";
  score: number;
  domains: string[];
  services: string[];
  owner?: string | null;
  updated_at: string;
};

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (body?.detail) {
      return typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    }
  } catch {
    /* ignore */
  }
  return res.statusText || "Request failed";
}

export async function fetchQnaHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchQnaTelemetry(sessionId: string): Promise<QnaTelemetry> {
  const res = await fetch(`${API_BASE}/api/qna/telemetry/${sessionId}`);
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  return data.telemetry;
}

export async function fetchIncidentQueue(): Promise<IncidentQueueItem[]> {
  const res = await fetch(`${API_BASE}/api/incidents?limit=50`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

/* ------------------------------------------------------------------ */
/* QnA Chat API                                                       */
/* ------------------------------------------------------------------ */

export type QnaChatResponse = {
  session_id: string;
  reply: string;
  messages: ChatMessage[];
  telemetry: QnaTelemetry;
};

export async function sendOrchestrateMessage(
  query: string,
  sessionId: string,
  agent?: string
): Promise<QnaChatResponse> {
  const res = await fetch(`${API_BASE}/api/qna/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: query, agent }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function sendMobileCoreAnalystMessage(
  query: string,
  sessionId: string,
  agent?: string
): Promise<QnaChatResponse> {
  const res = await fetch(`${API_BASE}/api/qna/mobile-core-analyst`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: query, agent }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function streamMobileCoreAnalystMessage(
  query: string,
  sessionId: string,
  userRole: string,
  onChunk: (chunk: string) => void,
  agent?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/qna/mobile-core-analyst/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: query, user_role: userRole, agent }),
  });

  if (!res.ok) throw new Error(await parseError(res));
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        onChunk(chunk);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/* ------------------------------------------------------------------ */
/* Data Storyteller API                                                */
/* ------------------------------------------------------------------ */

const INCIDENT_SLUG_PATTERN = /((?:incidents\/[A-Za-z0-9_-]+|[A-Za-z0-9_-]+\/incidents)\/[A-Za-z0-9._-]+)/;

function extractIncidentSlug(query: string): string | null {
  return query.match(INCIDENT_SLUG_PATTERN)?.[1].replace(/[.,;:!?]+$/, "") ?? null;
}

export type StorytellerPayload = {
  incident_id: string;
  intent: string;
  answer: string;
  spoken_answer?: string | null;
  story?: unknown;
  narrative?: {
    incident_id?: string;
    audience?: string;
    lifecycle_state?: string;
    title?: string;
    executive_summary?: string;
    impact_summary?: string;
    rca_status?: string;
    domains?: string[];
    services?: string[];
    components?: string[];
    claims?: Array<{
      id: string;
      statement: string;
      grade: string;
      confidence: number;
      fcaps?: string[];
      domain?: string | null;
      service_procedure?: string | null;
      object_ref?: string | null;
    }>;
    next_actions?: Array<{
      id: string;
      label: string;
      action_type: string;
      priority: number;
      requires_approval?: boolean;
      rationale?: string | null;
      supports_claim_ids?: string[];
    }>;
    open_questions?: string[];
  } | null;
  visual_explanation?: {
    incident_id?: string;
    audience?: string;
    primary_widget?: string | null;
    widgets?: Array<{
      id: string;
      title: string;
      type: string;
      data?: Record<string, unknown>;
      confidence?: number;
      supports_claim_ids?: string[];
      provenance?: Array<string | Record<string, unknown>>;
    }>;
  } | null;
};

export async function streamStorytellerMessage(
  query: string,
  sessionId: string,
  onChunk: (chunk: string) => void,
  onStatus?: (status: string) => void,
  onPayload?: (payload: StorytellerPayload) => void
): Promise<string> {
  const incidentId = extractIncidentSlug(query);
  const pathIncidentId = incidentId ?? "";

  onStatus?.("[Data Storyteller] generating narrative");
  const res = await fetch(`${API_BASE}/api/incidents/${pathIncidentId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: query }),
  });

  if (!res.ok) throw new Error(await parseError(res));
  const data = (await res.json()) as StorytellerPayload;
  if (typeof data.answer !== "string") {
    throw new Error("Incident storyteller response did not include an answer");
  }
  onChunk(data.answer);
  onPayload?.(data);
  if (typeof data.incident_id !== "string") {
    throw new Error("Incident storyteller response did not include an incident id");
  }
  return data.incident_id;
}

export async function streamOrchestrateMessage(
  query: string,
  sessionId: string,
  onChunk: (chunk: string) => void,
  agent?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/qna/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message: query, agent }),
  });

  if (!res.ok) throw new Error(await parseError(res));
  if (!res.body) throw new Error("No response body");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        onChunk(chunk);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export type ComplaintTelemetry = {
  id: number;
  session_id: string;
  complaint_number: string;
  time_reported: number; // UNIX timestamp
  issue_summary: string;
  assignment_target: string;
  assignment_queue: string | null;
  reassignment_category: string;
  resolution_category: string;
  raw_complaint: string;
};

export async function fetchComplaintsTelemetry(): Promise<ComplaintTelemetry[]> {
  const res = await fetch(`${API_BASE}/api/qna/complaints/telemetry`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
