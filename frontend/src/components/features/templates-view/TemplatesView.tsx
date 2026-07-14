"use client";

import React from "react";
import { ChevronDown, ChevronRight, Cpu, Plus } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LLM_PROVIDERS,
  type LlmJinjaTemplate,
} from "@/lib/llm-templates";
import { cn } from "@/lib/utils";
import { useTemplates } from "./useTemplates";

const iconStroke = { strokeWidth: 1.5 } as const;

type TemplateAccordionProps = {
  template: LlmJinjaTemplate;
  expanded: boolean;
  active: boolean;
  onToggle: () => void;
  onSelect: () => void;
  onChange: (content: string) => void;
};

const TemplateAccordion = React.memo(({
  template,
  expanded,
  active,
  onToggle,
  onSelect,
  onChange,
}: TemplateAccordionProps) => {
  const provider = LLM_PROVIDERS[template.providerId];

  return (
    <GlassCard
      hover={false}
      className={cn(
        "overflow-hidden transition-all duration-300",
        active && "border-cyan-500/30 ring-1 ring-cyan-500/20"
      )}
    >
      <div className="flex w-full items-center gap-3 px-4 py-3">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className="rounded-lg p-1 text-neutral-400 transition-colors hover:bg-white/10 hover:text-white"
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse template" : "Expand template"}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" {...iconStroke} />
          ) : (
            <ChevronRight className="h-4 w-4" {...iconStroke} />
          )}
        </button>
        <button
          type="button"
          onClick={onSelect}
          className="flex min-w-0 flex-1 flex-col gap-1 text-left transition-colors hover:opacity-90"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-white">{provider.name}</span>
            <Badge variant={provider.badgeVariant}>{provider.messageFormat}</Badge>
          </div>
          <p className="truncate text-xs text-neutral-500">
            {provider.vendor} · {template.filename}
          </p>
        </button>
      </div>

      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-300 ease-in-out",
          expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        )}
      >
        <div className="overflow-hidden">
          <div className="border-t border-white/10 px-4 pb-4 pt-2">
            <p className="mb-3 text-xs leading-relaxed text-neutral-400">
              {template.description}
            </p>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {Object.keys(template.sampleVars).map((key) => (
                <code
                  key={key}
                  className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-cyan-400"
                >
                  {`{{ ${key} }}`}
                </code>
              ))}
            </div>
            <textarea
              value={template.content}
              onChange={(e) => onChange(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              spellCheck={false}
              className="min-h-[160px] w-full resize-y rounded-xl border border-white/10 bg-black/40 p-3 font-mono text-xs leading-relaxed text-neutral-200 placeholder:text-neutral-600 focus:border-cyan-500/40 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
              aria-label={`Edit ${provider.name} Jinja template`}
            />
          </div>
        </div>
      </div>
    </GlassCard>
  );
});
TemplateAccordion.displayName = "TemplateAccordion";

export function TemplatesView() {
  const {
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
  } = useTemplates();

  return (
    <div className="flex h-[calc(100vh-8rem)] min-h-0 flex-col gap-4 lg:flex-row">
      <div className="flex min-h-0 flex-1 flex-col lg:max-w-[52%]">
        <GlassCard className="mb-3 p-4" hover={false}>
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
              <Cpu className="h-4 w-4 text-cyan-400" {...iconStroke} />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-sm font-medium text-white">
                LLM Input Formatters
              </h2>
              <p className="mt-1 text-xs leading-relaxed text-neutral-400">
                Jinja templates shape dataset context, prompts, and metadata into
                provider-native payloads — compatible with Gemini, GPT / GPT-X,
                GPT-OSS (Harmony), Llama, DeepSeek, Mistral, Perplexity, Claude,
                Qwen, and other chat APIs.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="shrink-0 gap-1.5"
              onClick={addTemplate}
            >
              <Plus className="h-3.5 w-3.5" {...iconStroke} />
              Add
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {Object.values(LLM_PROVIDERS).map((p) => (
              <span
                key={p.id}
                className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-neutral-400"
              >
                {p.name}
              </span>
            ))}
            <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-neutral-500">
              + more
            </span>
          </div>
        </GlassCard>

        <p className="mb-2 text-xs text-neutral-500">
          Collapse panels to browse all provider templates
        </p>

        <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {templates.map((template) => (
            <TemplateAccordion
              key={template.id}
              template={template}
              expanded={expandedIds.has(template.id)}
              active={activeId === template.id}
              onToggle={() => toggleExpanded(template.id)}
              onSelect={() => setActiveId(template.id)}
              onChange={(content) => updateContent(template.id, content)}
            />
          ))}
        </div>
      </div>

      <GlassCard className="flex min-h-0 flex-1 flex-col p-6" hover={false}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
              Rendered request preview
            </p>
            <p className="mt-1 text-sm text-white">
              {activeProvider?.name ?? "—"}
            </p>
            <p className="text-xs text-neutral-500">
              {activeProvider?.vendor} · {activeTemplate?.filename}
            </p>
          </div>
          {activeProvider && (
            <Badge variant={activeProvider.badgeVariant}>
              {activeProvider.messageFormat}
            </Badge>
          )}
        </div>

        <pre className="mt-4 min-h-0 flex-1 overflow-auto rounded-xl border border-white/5 bg-black/30 p-4 font-mono text-xs leading-relaxed whitespace-pre-wrap text-neutral-300">
          {preview}
        </pre>

        <div className="mt-4 border-t border-white/10 pt-4">
          <p className="mb-2 text-xs text-neutral-500">
            Jinja variables (sample bindings)
          </p>
          <div className="flex flex-wrap gap-2">
            {activeTemplate &&
              Object.entries(activeTemplate.sampleVars).map(([key, value]) => (
                <span
                  key={key}
                  className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs"
                >
                  <span className="text-cyan-400">{key}</span>
                  <span className="text-neutral-500"> = </span>
                  <span className="text-neutral-300">{value}</span>
                </span>
              ))}
          </div>
        </div>
      </GlassCard>
    </div>
  );
}
