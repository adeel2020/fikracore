const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export type ChartOptionItem = {
  name: string;
  dom_id: string;
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
  const res = await fetch(`${API_BASE}/api/qna/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchQnaTelemetry(sessionId: string): Promise<QnaTelemetry> {
  const res = await fetch(`${API_BASE}/api/qna/telemetry/${sessionId}`);
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  return data.telemetry;
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
  sessionId: string
): Promise<QnaChatResponse> {
  const res = await fetch(`${API_BASE}/api/qna/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: query,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function sendMobileCoreAnalystMessage(
  query: string,
  sessionId: string
): Promise<QnaChatResponse> {
  const res = await fetch(`${API_BASE}/api/qna/mobile-core-analyst`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: query,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function streamMobileCoreAnalystMessage(
  query: string,
  sessionId: string,
  userRole: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/qna/mobile-core-analyst/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: query,
      user_role: userRole,
    }),
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

export async function streamOrchestrateMessage(
  query: string,
  sessionId: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/qna/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: query,
    }),
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

export type SkillItem = {
  name: string;
  description: string;
  role?: string;
};

export async function fetchSkills(): Promise<SkillItem[]> {
  const res = await fetch(`${API_BASE}/api/qna/skills`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
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
