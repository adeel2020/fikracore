import { API_BASE } from "./config";

export type SftDataset = {
  id: string;
  name: string;
  rows: number;
  size_kb: number;
};

export type SftConfig = {
  base_model: string;
  merged_dir: string;
  learning_rate: number;
  epochs: number;
  batch_size: number;
  micro_batch_size: number;
  gradient_accumulation_steps: number;
  max_seq_length: number;
  lora: {
    r: number;
    alpha: number;
    dropout: number;
    target_modules: string[];
  };
};

export type SftConfigUpdate = {
  base_model?: string;
  learning_rate?: number;
  epochs?: number;
  batch_size?: number;
  micro_batch_size?: number;
  gradient_accumulation_steps?: number;
  r?: number;
  alpha?: number;
  max_seq_length?: number;
};

export type SftTrainStatus = {
  state: "IDLE" | "TRAINING" | "MERGING" | "COMPLETED" | "FAILED" | "EVALUATING";
  method: "corda" | "pissa" | null;
  epochs_completed: number;
  total_epochs: number;
  current_loss: number | null;
  current_grad_norm: number | null;
  current_lr: number | null;
  elapsed_time_sec: number;
  eta_sec: number | null;
  error_message: string | null;
  logs: string[];
};

export type CategoryEvaluation = {
  total_tickets_evaluated: number;
  model_confidence_percent: number;
  answer_relevance_percent: number;
  answer_semantic_match_percent: number;
  decision_accuracy_percent: number;
  routing_accuracy_percent: number;
};

export type SftEvaluationResults = {
  status: "ready" | "not_available";
  message?: string;
  results?: {
    global_metrics: {
      model_confidence_percent: number;
      answer_relevance_percent: number;
      answer_semantic_match_percent: number;
      decision_accuracy_percent: number;
      decision_precision_macro_percent: number;
      decision_f1_macro_percent: number;
      routing_accuracy_percent: number;
      routing_precision_macro_percent: number;
      routing_f1_macro_percent: number;
    };
    category_breakdown: Record<string, CategoryEvaluation>;
  };
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

export async function fetchSftDatasets(): Promise<SftDataset[]> {
  const res = await fetch(`${API_BASE}/api/sft/datasets`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchSftConfig(): Promise<SftConfig> {
  const res = await fetch(`${API_BASE}/api/sft/config`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function updateSftConfig(config: SftConfigUpdate): Promise<any> {
  const res = await fetch(`${API_BASE}/api/sft/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function triggerSftTraining(
  method: "corda" | "pissa",
  configOverride?: SftConfigUpdate
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/sft/train?method=${method}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: configOverride ? JSON.stringify(configOverride) : undefined,
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchSftTrainStatus(): Promise<SftTrainStatus> {
  const res = await fetch(`${API_BASE}/api/sft/train/status`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function triggerSftEvaluation(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/sft/evaluate`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchSftEvaluationResults(): Promise<SftEvaluationResults> {
  const res = await fetch(`${API_BASE}/api/sft/evaluate/results`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function stopSftTraining(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/sft/train/stop`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export function streamSftTrainStatus(
  onData: (data: SftTrainStatus & { new_logs: string[] }) => void,
  onError: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/api/sft/train/stream`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onData(data);
    } catch (err) {
      onError(err);
    }
  };

  eventSource.onerror = (err) => {
    onError(err);
    if (eventSource.readyState === EventSource.CLOSED) {
      eventSource.close();
    }
  };

  return () => {
    eventSource.close();
  };
}
