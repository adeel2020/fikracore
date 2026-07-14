import { useState, useCallback, useMemo } from "react";
import {
  DEFAULT_LLM_TEMPLATES,
  LLM_PROVIDERS,
  renderTemplatePreview,
  type LlmJinjaTemplate,
  type LlmProviderId,
} from "@/lib/llm-templates";

function createTemplateId(): string {
  return `custom-${Date.now()}`;
}

export function useTemplates() {
  const [templates, setTemplates] = useState<LlmJinjaTemplate[]>(DEFAULT_LLM_TEMPLATES);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(
    () => new Set([DEFAULT_LLM_TEMPLATES[0].id])
  );
  const [activeId, setActiveId] = useState<string>(DEFAULT_LLM_TEMPLATES[0].id);

  const activeTemplate = templates.find((t) => t.id === activeId) ?? templates[0];
  const activeProvider = activeTemplate
    ? LLM_PROVIDERS[activeTemplate.providerId]
    : null;

  const preview = useMemo(
    () =>
      activeTemplate
        ? renderTemplatePreview(activeTemplate.content, activeTemplate.sampleVars)
        : "",
    [activeTemplate]
  );

  const toggleExpanded = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const updateContent = useCallback((id: string, content: string) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === id ? { ...t, content } : t))
    );
  }, []);

  const addTemplate = useCallback(() => {
    const id = createTemplateId();
    const providerId: LlmProviderId = "openai-gpt";
    const provider = LLM_PROVIDERS[providerId];
    const next: LlmJinjaTemplate = {
      id,
      providerId,
      filename: "custom_provider.jinja",
      description: `Custom Jinja formatter for ${provider.name}-compatible APIs.`,
      content: `{\n  "model": "{{ model }}",\n  "messages": [\n    { "role": "system", "content": "{{ system_prompt }}" },\n    { "role": "user", "content": "{{ user_prompt }}" }\n  ]\n}`,
      sampleVars: {
        model: "custom-model",
        system_prompt: "You are a data storytelling agent.",
        user_prompt: "Describe {{ dataset }} for {{ audience }}.",
        dataset: "sales_q4_2025.csv",
        audience: "analysts",
      },
    };
    setTemplates((prev) => [...prev, next]);
    setExpandedIds((prev) => new Set(prev).add(id));
    setActiveId(id);
  }, []);

  return {
    templates,
    expandedIds,
    activeId,
    activeTemplate,
    activeProvider,
    preview,
    toggleExpanded,
    setActiveId,
    updateContent,
    addTemplate,
  };
}
