export type LlmProviderId =
  | "openai-gpt"
  | "openai-oss-harmony"
  | "google-gemini"
  | "anthropic-claude"
  | "meta-llama"
  | "deepseek"
  | "mistral"
  | "perplexity"
  | "qwen";

export type LlmProviderMeta = {
  id: LlmProviderId;
  name: string;
  vendor: string;
  messageFormat: string;
  badgeVariant: "default" | "neon" | "alert" | "muted";
};

export const LLM_PROVIDERS: Record<LlmProviderId, LlmProviderMeta> = {
  "openai-gpt": {
    id: "openai-gpt",
    name: "GPT / GPT-X",
    vendor: "OpenAI",
    messageFormat: "Chat Completions (roles)",
    badgeVariant: "default",
  },
  "openai-oss-harmony": {
    id: "openai-oss-harmony",
    name: "GPT-OSS",
    vendor: "OpenAI · Harmony",
    messageFormat: "Harmony channel tokens",
    badgeVariant: "neon",
  },
  "google-gemini": {
    id: "google-gemini",
    name: "Gemini",
    vendor: "Google",
    messageFormat: "Contents / parts",
    badgeVariant: "alert",
  },
  "anthropic-claude": {
    id: "anthropic-claude",
    name: "Claude",
    vendor: "Anthropic",
    messageFormat: "Messages API",
    badgeVariant: "muted",
  },
  "meta-llama": {
    id: "meta-llama",
    name: "Llama",
    vendor: "Meta",
    messageFormat: "[INST] instruct",
    badgeVariant: "default",
  },
  deepseek: {
    id: "deepseek",
    name: "DeepSeek",
    vendor: "DeepSeek",
    messageFormat: "Chat + optional reasoning",
    badgeVariant: "neon",
  },
  mistral: {
    id: "mistral",
    name: "Mistral",
    vendor: "Mistral AI",
    messageFormat: "[INST] / Mixtral",
    badgeVariant: "muted",
  },
  perplexity: {
    id: "perplexity",
    name: "Perplexity",
    vendor: "Perplexity",
    messageFormat: "OpenAI-compatible chat",
    badgeVariant: "default",
  },
  qwen: {
    id: "qwen",
    name: "Qwen",
    vendor: "Alibaba",
    messageFormat: "ChatML / im_start",
    badgeVariant: "alert",
  },
};

export type LlmJinjaTemplate = {
  id: string;
  providerId: LlmProviderId;
  filename: string;
  description: string;
  content: string;
  sampleVars: Record<string, string>;
};

export const DEFAULT_LLM_TEMPLATES: LlmJinjaTemplate[] = [
  {
    id: "openai-gpt",
    providerId: "openai-gpt",
    filename: "openai_chat_completions.jinja",
    description: "Maps story context to OpenAI Chat Completions JSON (GPT-4o, GPT-4.1, etc.).",
    sampleVars: {
      model: "gpt-4.1",
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Summarize churn drivers for sales_q4_2025.csv.",
      temperature: "0.2",
    },
    content: `{# OpenAI — Chat Completions (GPT / GPT-X) #}
{
  "model": "{{ model }}",
  "temperature": {{ temperature }},
  "messages": [
    {
      "role": "system",
      "content": "{{ system_prompt }}"
    },
    {
      "role": "user",
      "content": "{{ user_prompt }}"
    }
  ]
}`,
  },
  {
    id: "openai-oss-harmony",
    providerId: "openai-oss-harmony",
    filename: "harmony_gpt_oss.jinja",
    description: "Harmony channel layout for GPT-OSS / open-weight Harmony runtimes.",
    sampleVars: {
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Explain revenue anomalies for Q4.",
      analysis_channel: "analysis",
    },
    content: `{# OpenAI GPT-OSS — Harmony message format #}
<|start|>system<|channel|>final<|message|>
{{ system_prompt }}<|end|>

<|start|>user<|channel|>final<|message|>
{{ user_prompt }}<|end|>

{% if analysis_channel %}
<|start|>assistant<|channel|>{{ analysis_channel }}<|message|>
{% endif %}`,
  },
  {
    id: "google-gemini",
    providerId: "google-gemini",
    filename: "gemini_generate_content.jinja",
    description: "Gemini GenerateContent request with systemInstruction and user parts.",
    sampleVars: {
      model: "gemini-2.0-flash",
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Highlight top 3 segment trends.",
    },
    content: `{# Google Gemini — generateContent #}
{
  "model": "models/{{ model }}",
  "systemInstruction": {
    "parts": [{ "text": "{{ system_prompt }}" }]
  },
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "{{ user_prompt }}" }]
    }
  ]
}`,
  },
  {
    id: "anthropic-claude",
    providerId: "anthropic-claude",
    filename: "claude_messages.jinja",
    description: "Anthropic Messages API with system string and user blocks.",
    sampleVars: {
      model: "claude-sonnet-4-20250514",
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Draft an executive summary of inventory risk.",
      max_tokens: "4096",
    },
    content: `{# Anthropic Claude — Messages API #}
{
  "model": "{{ model }}",
  "max_tokens": {{ max_tokens }},
  "system": "{{ system_prompt }}",
  "messages": [
    {
      "role": "user",
      "content": [
        { "type": "text", "text": "{{ user_prompt }}" }
      ]
    }
  ]
}`,
  },
  {
    id: "meta-llama",
    providerId: "meta-llama",
    filename: "llama_instruct.jinja",
    description: "Llama 3.x [INST] prompt wrapper for local or hosted inference.",
    sampleVars: {
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Compare enterprise vs SMB churn.",
    },
    content: `{# Meta Llama — instruct template #}
<s>[INST] <<SYS>>
{{ system_prompt }}
<</SYS>>

{{ user_prompt }} [/INST]`,
  },
  {
    id: "deepseek",
    providerId: "deepseek",
    filename: "deepseek_chat.jinja",
    description: "DeepSeek chat with optional reasoning block for R1-style models.",
    sampleVars: {
      model: "deepseek-chat",
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "List statistical outliers in the dataset.",
      enable_reasoning: "true",
    },
    content: `{# DeepSeek — chat (+ optional reasoning) #}
{
  "model": "{{ model }}",
  "messages": [
    { "role": "system", "content": "{{ system_prompt }}" },
    { "role": "user", "content": "{{ user_prompt }}" }
  ]
  {% if enable_reasoning == "true" %},
  "reasoning": { "enabled": true }
  {% endif %}
}`,
  },
  {
    id: "mistral",
    providerId: "mistral",
    filename: "mistral_instruct.jinja",
    description: "Mistral / Mixtral [INST] formatting for instruct endpoints.",
    sampleVars: {
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Summarize warehouse reorder flags.",
    },
    content: `{# Mistral — [INST] instruct #}
<s>[INST] {{ system_prompt }}

{{ user_prompt }} [/INST]`,
  },
  {
    id: "perplexity",
    providerId: "perplexity",
    filename: "perplexity_chat.jinja",
    description: "Perplexity sonar models (OpenAI-compatible chat schema).",
    sampleVars: {
      model: "sonar-pro",
      system_prompt: "You are a data storytelling agent. Cite sources when possible.",
      user_prompt: "What industry benchmarks apply to our Q4 revenue?",
    },
    content: `{# Perplexity — OpenAI-compatible chat #}
{
  "model": "{{ model }}",
  "messages": [
    { "role": "system", "content": "{{ system_prompt }}" },
    { "role": "user", "content": "{{ user_prompt }}" }
  ]
}`,
  },
  {
    id: "qwen",
    providerId: "qwen",
    filename: "qwen_chatml.jinja",
    description: "Qwen ChatML im_start / im_end token envelope.",
    sampleVars: {
      system_prompt: "You are a data storytelling agent.",
      user_prompt: "Generate a narrative for regional sales performance.",
    },
    content: `{# Qwen — ChatML #}
<|im_start|>system
{{ system_prompt }}
<|im_start|>user
{{ user_prompt }}
<|im_start|>assistant
`,
  },
];

export function renderTemplatePreview(
  content: string,
  vars: Record<string, string>
): string {
  let out = content;
  for (const [key, value] of Object.entries(vars)) {
    out = out.replaceAll(`{{ ${key} }}`, value);
    out = out.replaceAll(`{{${key}}}`, value);
  }
  return out;
}

/** Dataset shape used when binding Jinja vars during domain-adaptation preprocess. */
export type PreprocessDataset = {
  name: string;
  rows: number;
  columns: { name: string; type: string }[];
};

/** Merge template defaults with dataset-specific prompts for preprocess. */
export function buildPreprocessVariables(
  dataset: PreprocessDataset,
  template: LlmJinjaTemplate
): Record<string, string> {
  const schema = dataset.columns
    .map((c) => `${c.name}:${c.type}`)
    .join(", ");
  const userPrompt =
    `Preprocess and structure dataset "${dataset.name}" ` +
    `(${dataset.rows.toLocaleString()} rows). ` +
    `Columns: ${schema}. ` +
    `Emit records in ${LLM_PROVIDERS[template.providerId].messageFormat} for embedding.`;

  return {
    ...template.sampleVars,
    dataset: dataset.name,
    schema,
    row_count: String(dataset.rows),
    system_prompt:
      template.sampleVars.system_prompt ??
      "You are a data storytelling agent. Structure raw tabular data for LLM-compatible domain adaptation.",
    user_prompt: userPrompt,
  };
}

export function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.length / 4));
}
