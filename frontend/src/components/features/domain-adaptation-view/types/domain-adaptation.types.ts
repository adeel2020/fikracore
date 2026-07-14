import { Sparkles, Gauge, type LucideIcon } from "lucide-react";

export const PIPELINE_STAGES = [
  { id: "preprocess", label: "Preprocess" },
  { id: "embed", label: "Embed" },
  { id: "finetune", label: "Fine-tune" },
  { id: "evaluate", label: "Evaluate" },
] as const;

export type PipelineStageId = (typeof PIPELINE_STAGES)[number]["id"];

export interface FineTuneMethod {
  id: "corda" | "pissa";
  name: string;
  tagline: string;
  description: string;
  highlights: string[];
  badgeVariant: "default" | "neon";
  icon: LucideIcon;
  color: string;
}

export const METHODS: FineTuneMethod[] = [
  {
    id: "corda",
    name: "CorDA (Context Adaptation)",
    tagline: "IPM Covariance Optimization",
    description:
      "Context-oriented Decomposition Adaptation — analyzes the base model activation covariance to align adapters directly with domain context.",
    highlights: [
      "Production-grade telecom context grounding",
      "Covariance-informed weight decomposition (IPM)",
      "Strict policy-aware response retention",
      "Superior long-term alignment stability"
    ],
    badgeVariant: "default",
    icon: Sparkles,
    color: "cyan"
  },
  {
    id: "pissa",
    name: "PiSSA (Principal SVD Adaptation)",
    tagline: "High-Energy Convergence",
    description:
      "Principal Singular values and Singular vectors Adaptation — initializes LoRA adapters in the dominant energy spaces of base model weights.",
    highlights: [
      "Extremely fast structural convergence",
      "SVD-based feature energy mapping",
      "Strong storytelling and stylistic lock-in",
      "Highly efficient parameter representation"
    ],
    badgeVariant: "neon",
    icon: Gauge,
    color: "fuchsia"
  },
];
