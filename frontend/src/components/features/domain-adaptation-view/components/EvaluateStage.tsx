"use client";

import React from "react";
import {
  Loader2,
  Award,
  RefreshCw,
  Search,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { SftTrainStatus, SftEvaluationResults } from "@/lib/api/sft";

interface EvaluateStageProps {
  trainStatus: SftTrainStatus | null;
  evalResults: SftEvaluationResults | null;
  startingEval: boolean;
  handleStartEvaluation: () => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  sortField: string;
  sortDirection: "asc" | "desc";
  handleSort: (field: string) => void;
  sortedCategories: any[];
}

export function EvaluateStage({
  trainStatus,
  evalResults,
  startingEval,
  handleStartEvaluation,
  searchQuery,
  setSearchQuery,
  sortField,
  sortDirection,
  handleSort,
  sortedCategories,
}: EvaluateStageProps) {
  // Render sort icon indicator
  const renderSortIcon = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="inline h-4 w-4 ml-1 text-cyan-400" />
    ) : (
      <ChevronDown className="inline h-4 w-4 ml-1 text-cyan-400" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Active Eval state */}
      {trainStatus && trainStatus.state === "EVALUATING" ? (
        <GlassCard
          className="p-8 text-center flex flex-col items-center justify-center border-amber-500/20 bg-amber-500/[0.02]"
          hover={false}
        >
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
          <h4 className="text-lg font-bold text-white">
            Evaluation Thread Running...
          </h4>
          <p className="text-sm text-neutral-400 mt-2 max-w-md leading-relaxed">
            Evaluating model checkpoints on hold-out dataset using asymmetric
            sentence embeddings, Microsoft cross-encoders, and sk-learn metrics.
          </p>
          <pre className="mt-6 max-w-2xl text-left bg-black/80 rounded-xl border border-white/5 p-4 font-mono text-[10px] text-cyan-300 w-full max-h-40 overflow-auto">
            {trainStatus.logs.slice(-10).join("")}
          </pre>
        </GlassCard>
      ) : (
        <>
          {/* Trigger Evaluation if no results exist */}
          {!evalResults && (
            <GlassCard
              className="p-8 text-center flex flex-col items-center justify-center border-white/5 bg-white/[0.01]"
              hover={false}
            >
              <Award className="w-12 h-12 text-neutral-500 mb-4" />
              <h4 className="text-base font-bold text-white">
                No Evaluation Metrics Loaded
              </h4>
              <p className="text-sm text-neutral-400 mt-1 max-w-sm">
                Generate accuracy matrices, BLEU overlap scores, and route
                decisions from the merged model.
              </p>
              <Button
                onClick={handleStartEvaluation}
                disabled={startingEval}
                className="mt-6 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium px-6 py-4 rounded-lg"
              >
                {startingEval ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />{" "}
                    Initializing...
                  </>
                ) : (
                  "Start Asymmetric Evaluation"
                )}
              </Button>
            </GlassCard>
          )}

          {/* Show metrics dashboard if ready */}
          {evalResults?.results && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h4 className="text-base font-bold text-white">
                    Evaluation Results Dashboard
                  </h4>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    Hold-out validation metrics compiled using MS-MARCO graded
                    semantic relevance
                  </p>
                </div>
                <Button
                  onClick={handleStartEvaluation}
                  disabled={startingEval}
                  variant="outline"
                  className="border-white/10 bg-white/5 text-white hover:bg-white/10 text-xs flex items-center gap-1.5"
                >
                  {startingEval ? (
                    <Loader2 className="w-4.5 h-4.5 animate-spin text-cyan-400" />
                  ) : (
                    <RefreshCw className="w-3.5 h-3.5" />
                  )}
                  Re-run Evaluation
                </Button>
              </div>

              {/* Metric Radial / Score Cards */}
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-5">
                {/* Model Confidence */}
                <div className="rounded-xl border border-white/5 bg-black/40 p-4 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-12 h-12 bg-cyan-500/5 blur-xl rounded-full" />
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Model Confidence
                  </span>
                  <p className="mt-2 text-3xl font-extrabold text-cyan-400 tracking-tight">
                    {evalResults.results.global_metrics.model_confidence_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                  <p className="text-[9px] text-neutral-500 mt-3 uppercase font-medium">
                    Logprob extraction
                  </p>
                </div>

                {/* Answer Relevance */}
                <div className="rounded-xl border border-white/5 bg-black/40 p-4 relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-12 h-12 bg-fuchsia-500/5 blur-xl rounded-full" />
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Semantic Relevance
                  </span>
                  <p className="mt-2 text-3xl font-extrabold text-fuchsia-400 tracking-tight">
                    {evalResults.results.global_metrics.answer_relevance_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                  <p className="text-[9px] text-neutral-500 mt-3 uppercase font-medium">
                    multi-qa-cos embeddings
                  </p>
                </div>

                {/* Ground Truth Match */}
                <div className="rounded-xl border border-white/5 bg-black/40 p-4 relative overflow-hidden">
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Ground Truth Match
                  </span>
                  <p className="mt-2 text-3xl font-extrabold text-white tracking-tight">
                    {evalResults.results.global_metrics.answer_semantic_match_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                  <p className="text-[9px] text-neutral-500 mt-3 uppercase font-medium">
                    Sentence similarity
                  </p>
                </div>

                {/* Decision Accuracy */}
                <div className="rounded-xl border border-white/5 bg-black/40 p-4 relative overflow-hidden">
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Decision Accuracy
                  </span>
                  <p className="mt-2 text-3xl font-extrabold text-emerald-400 tracking-tight">
                    {evalResults.results.global_metrics.decision_accuracy_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                  <p className="text-[9px] text-neutral-500 mt-3 uppercase font-medium">
                    Categorical F1 Macro
                  </p>
                </div>

                {/* Routing Accuracy */}
                <div className="rounded-xl border border-white/5 bg-black/40 p-4 relative overflow-hidden">
                  <span className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                    Routing Accuracy
                  </span>
                  <p className="mt-2 text-3xl font-extrabold text-amber-400 tracking-tight">
                    {evalResults.results.global_metrics.routing_accuracy_percent.toFixed(
                      1
                    )}
                    %
                  </p>
                  <p className="text-[9px] text-neutral-500 mt-3 uppercase font-medium">
                    Action Routing hits
                  </p>
                </div>
              </div>

              {/* Graded Breakdown Table */}
              <GlassCard className="p-6 relative" hover={false}>
                <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                  <h5 className="text-sm font-semibold text-white uppercase tracking-wider">
                    Performance Breakdown by Telecom Category
                  </h5>
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-500" />
                    <input
                      type="text"
                      placeholder="Search telecom categories..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-black/40 pl-9 pr-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="overflow-x-auto rounded-xl border border-white/5">
                  <table className="w-full border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-white/5 bg-white/[0.02] text-neutral-400 font-semibold uppercase tracking-wider">
                        <th
                          className="p-4 cursor-pointer hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("name")}
                        >
                          Category {renderSortIcon("name")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("total_tickets_evaluated")}
                        >
                          Questions {renderSortIcon("total_tickets_evaluated")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("decision_accuracy_percent")}
                        >
                          Decision Acc {renderSortIcon("decision_accuracy_percent")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("routing_accuracy_percent")}
                        >
                          Action Acc {renderSortIcon("routing_accuracy_percent")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("model_confidence_percent")}
                        >
                          Confidence {renderSortIcon("model_confidence_percent")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("answer_relevance_percent")}
                        >
                          Relevance {renderSortIcon("answer_relevance_percent")}
                        </th>
                        <th
                          className="p-4 cursor-pointer text-right hover:text-cyan-400 transition-colors"
                          onClick={() => handleSort("answer_semantic_match_percent")}
                        >
                          Semantic {renderSortIcon("answer_semantic_match_percent")}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 bg-black/10">
                      {sortedCategories.map((item) => (
                        <tr
                          key={item.name}
                          className="hover:bg-white/[0.01] transition-colors text-neutral-300"
                        >
                          <td className="p-4 font-medium text-white max-w-xs truncate">
                            {item.name}
                          </td>
                          <td className="p-4 text-right font-mono text-neutral-400">
                            {item.total_tickets_evaluated}
                          </td>
                          <td className="p-4 text-right font-bold text-emerald-400">
                            {item.decision_accuracy_percent.toFixed(1)}%
                          </td>
                          <td className="p-4 text-right font-bold text-amber-400">
                            {item.routing_accuracy_percent.toFixed(1)}%
                          </td>
                          <td className="p-4 text-right font-mono text-neutral-400">
                            {item.model_confidence_percent.toFixed(1)}%
                          </td>
                          <td className="p-4 text-right font-mono text-neutral-400">
                            {item.answer_relevance_percent.toFixed(1)}%
                          </td>
                          <td className="p-4 text-right font-bold text-cyan-400">
                            {item.answer_semantic_match_percent.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                      {sortedCategories.length === 0 && (
                        <tr>
                          <td
                            colSpan={7}
                            className="p-6 text-center text-neutral-500"
                          >
                            No matching telecom categories found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </GlassCard>
            </>
          )}
        </>
      )}
    </div>
  );
}
