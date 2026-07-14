import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { PipelineStageId } from "../types/domain-adaptation.types";
import {
  DEFAULT_LLM_TEMPLATES,
  buildPreprocessVariables,
  estimateTokens,
  renderTemplatePreview,
  LLM_PROVIDERS,
} from "@/lib/llm-templates";
import {
  fetchSftDatasets,
  fetchSftConfig,
  updateSftConfig,
  triggerSftTraining,
  fetchSftTrainStatus,
  triggerSftEvaluation,
  fetchSftEvaluationResults,
  stopSftTraining,
  streamSftTrainStatus,
  SftDataset,
  SftConfig,
  SftTrainStatus,
  SftEvaluationResults
} from "@/lib/api/sft";

export function useDomainAdaptation() {
  // Stage States
  const [pipelineStage, setPipelineStage] = useState<PipelineStageId>("preprocess");
  const [autoOptimize, setAutoOptimize] = useState(true);

  // Loaded SFT data
  const [datasets, setDatasets] = useState<SftDataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [activeConfig, setActiveConfig] = useState<SftConfig | null>(null);
  const [trainStatus, setTrainStatus] = useState<SftTrainStatus | null>(null);
  const [evalResults, setEvalResults] = useState<SftEvaluationResults | null>(null);

  // Hyperparameters states
  const [activeMethod, setActiveMethod] = useState<"corda" | "pissa">("corda");
  const [lr, setLr] = useState<number>(0.0001);
  const [epochs, setEpochs] = useState<number>(2);
  const [batchSize, setBatchSize] = useState<number>(1);
  const [microBatchSize, setMicroBatchSize] = useState<number>(4);
  const [gradAccum, setGradAccum] = useState<number>(4);
  const [loraR, setLoraR] = useState<number>(16);
  const [loraAlpha, setLoraAlpha] = useState<number>(32);
  const [maxSeqLen, setMaxSeqLen] = useState<number>(256);

  // Form templates
  const [templateId, setTemplateId] = useState(DEFAULT_LLM_TEMPLATES[0].id);
  const [structuredPayload, setStructuredPayload] = useState<string | null>(null);
  const [embedComplete, setEmbedComplete] = useState(false);

  // Evaluation sorting and search
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<string>("total_tickets_evaluated");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Copy logs state
  const [copiedLogs, setCopiedLogs] = useState(false);

  // Loading states
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [submittingConfig, setSubmittingConfig] = useState(false);
  const [startingTraining, setStartingTraining] = useState(false);
  const [stoppingTraining, setStoppingTraining] = useState(false);
  const [startingEval, setStartingEval] = useState(false);

  const logConsoleRef = useRef<HTMLPreElement>(null);

  const handleCopyLogs = useCallback(() => {
    if (!trainStatus?.logs) return;
    navigator.clipboard.writeText(trainStatus.logs.join(""));
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  }, [trainStatus?.logs]);

  const refreshEvaluationResults = useCallback(async () => {
    try {
      const results = await fetchSftEvaluationResults();
      if (results.status === "ready") {
        setEvalResults(results);
      }
    } catch (err) {
      console.error("Failed to fetch evaluation results:", err);
    }
  }, []);

  const loadInitialData = useCallback(async () => {
    setLoadingDatasets(true);
    setLoadingConfig(true);
    try {
      const sftDatasets = await fetchSftDatasets();
      setDatasets(sftDatasets);
      if (sftDatasets.length > 0) {
        setSelectedDatasetId(sftDatasets[0].id);
      }
    } catch (err) {
      console.warn("Failed to load SFT datasets from backend.", err);
    } finally {
      setLoadingDatasets(false);
    }

    try {
      const sftCfg = await fetchSftConfig();
      setActiveConfig(sftCfg);
      setLr(sftCfg.learning_rate);
      setEpochs(sftCfg.epochs);
      setBatchSize(sftCfg.batch_size || 1);
      setMicroBatchSize(sftCfg.micro_batch_size);
      setGradAccum(sftCfg.gradient_accumulation_steps);
      setLoraR(sftCfg.lora.r);
      setLoraAlpha(sftCfg.lora.alpha);
      setMaxSeqLen(sftCfg.max_seq_length);
    } catch (err) {
      console.error("Failed to load SFT config from backend", err);
    } finally {
      setLoadingConfig(false);
    }

    refreshEvaluationResults();
  }, [refreshEvaluationResults]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // SSE Stream Subscriber
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const startStreaming = () => {
      unsubscribe = streamSftTrainStatus(
        (data) => {
          setTrainStatus((prev) => {
            const prevLogs = prev?.logs || [];
            const newFullLogs = [...prevLogs, ...data.new_logs];
            if (newFullLogs.length > 500) {
              newFullLogs.splice(0, newFullLogs.length - 500);
            }
            return {
              ...data,
              logs: newFullLogs
            };
          });

          if (data.state === "TRAINING" || data.state === "MERGING" || data.state === "EVALUATING") {
            setPipelineStage(data.state === "EVALUATING" ? "evaluate" : "finetune");
          } else if (data.state === "COMPLETED") {
            setPipelineStage("evaluate");
            refreshEvaluationResults();
          }
        },
        (err) => {
          console.error("SFT SSE Stream connection error:", err);
        }
      );
    };

    startStreaming();

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [refreshEvaluationResults]);

  // Auto-scroll log console
  useEffect(() => {
    if (logConsoleRef.current) {
      logConsoleRef.current.scrollTop = logConsoleRef.current.scrollHeight;
    }
  }, [trainStatus?.logs]);

  const template = useMemo(() => {
    return DEFAULT_LLM_TEMPLATES.find((t) => t.id === templateId) ?? DEFAULT_LLM_TEMPLATES[0];
  }, [templateId]);

  const provider = useMemo(() => {
    return LLM_PROVIDERS[template.providerId];
  }, [template.providerId]);

  const currentDataset = useMemo(() => {
    return datasets.find((d) => d.id === selectedDatasetId) ||
      (datasets.length > 0 ? datasets[0] : null);
  }, [datasets, selectedDatasetId]);

  const preprocessVars = useMemo(() => {
    if (!currentDataset) return {};
    const dummyMockDataset = {
      id: currentDataset.id,
      name: currentDataset.name,
      rows: currentDataset.rows,
      columns: [
        { name: "category", type: "string" },
        { name: "question", type: "string" },
        { name: "answer", type: "string" }
      ]
    };
    return buildPreprocessVariables(dummyMockDataset, template);
  }, [currentDataset, template]);

  const preprocessPreview = useMemo(
    () => renderTemplatePreview(template.content, preprocessVars),
    [template.content, preprocessVars]
  );

  const tokenEstimate = useMemo(
    () => estimateTokens(structuredPayload ?? ""),
    [structuredPayload]
  );

  const handleStopTraining = useCallback(async () => {
    setStoppingTraining(true);
    try {
      await stopSftTraining();
      const status = await fetchSftTrainStatus();
      setTrainStatus(status);
    } catch (err) {
      console.error("Failed to stop training:", err);
    } finally {
      setStoppingTraining(false);
    }
  }, []);

  const handleSaveConfig = useCallback(async () => {
    setSubmittingConfig(true);
    try {
      await updateSftConfig({
        learning_rate: lr,
        epochs: epochs,
        batch_size: batchSize,
        micro_batch_size: microBatchSize,
        gradient_accumulation_steps: gradAccum,
        r: loraR,
        alpha: loraAlpha,
        max_seq_length: maxSeqLen
      });
      const sftCfg = await fetchSftConfig();
      setActiveConfig(sftCfg);
    } catch (err) {
      console.error("Failed to update config on backend:", err);
    } finally {
      setSubmittingConfig(false);
    }
  }, [lr, epochs, batchSize, microBatchSize, gradAccum, loraR, loraAlpha, maxSeqLen]);

  const handleStartTraining = useCallback(async () => {
    setStartingTraining(true);
    try {
      await updateSftConfig({
        learning_rate: lr,
        epochs: epochs,
        batch_size: batchSize,
        micro_batch_size: microBatchSize,
        gradient_accumulation_steps: gradAccum,
        r: loraR,
        alpha: loraAlpha,
        max_seq_length: maxSeqLen
      });
      await triggerSftTraining(activeMethod);
      const status = await fetchSftTrainStatus();
      setTrainStatus(status);
    } catch (err) {
      console.error("Failed to trigger SFT training:", err);
    } finally {
      setStartingTraining(false);
    }
  }, [lr, epochs, batchSize, microBatchSize, gradAccum, loraR, loraAlpha, maxSeqLen, activeMethod]);

  const handleStartEvaluation = useCallback(async () => {
    setStartingEval(true);
    try {
      await triggerSftEvaluation();
      const status = await fetchSftTrainStatus();
      setTrainStatus(status);
    } catch (err) {
      console.error("Failed to trigger evaluation:", err);
    } finally {
      setStartingEval(false);
    }
  }, []);

  const applyPreprocess = useCallback(() => {
    setStructuredPayload(preprocessPreview);
    setEmbedComplete(false);
    setPipelineStage("embed");
  }, [preprocessPreview]);

  const runEmbed = useCallback(() => {
    setEmbedComplete(true);
    setPipelineStage("finetune");
  }, []);

  const handleSort = useCallback((field: string) => {
    setSortField((prevField) => {
      if (prevField === field) {
        setSortDirection((prevDir) => (prevDir === "asc" ? "desc" : "asc"));
        return prevField;
      } else {
        setSortDirection("desc");
        return field;
      }
    });
  }, []);

  const sortedCategories = useMemo(() => {
    if (!evalResults?.results?.category_breakdown) return [];

    const list = Object.entries(evalResults.results.category_breakdown).map(([name, stats]) => ({
      name,
      ...stats
    }));

    const filtered = list.filter((item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    filtered.sort((a: any, b: any) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();

      if (valA < valB) return sortDirection === "asc" ? -1 : 1;
      if (valA > valB) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [evalResults, searchQuery, sortField, sortDirection]);

  return {
    pipelineStage,
    setPipelineStage,
    autoOptimize,
    setAutoOptimize,
    datasets,
    selectedDatasetId,
    setSelectedDatasetId,
    activeConfig,
    trainStatus,
    evalResults,
    activeMethod,
    setActiveMethod,
    lr,
    setLr,
    epochs,
    setEpochs,
    batchSize,
    setBatchSize,
    microBatchSize,
    setMicroBatchSize,
    gradAccum,
    setGradAccum,
    loraR,
    setLoraR,
    loraAlpha,
    setLoraAlpha,
    maxSeqLen,
    setMaxSeqLen,
    templateId,
    setTemplateId,
    structuredPayload,
    embedComplete,
    searchQuery,
    setSearchQuery,
    sortField,
    sortDirection,
    copiedLogs,
    loadingDatasets,
    loadingConfig,
    submittingConfig,
    startingTraining,
    stoppingTraining,
    startingEval,
    logConsoleRef,
    handleCopyLogs,
    handleStopTraining,
    handleSaveConfig,
    handleStartTraining,
    handleStartEvaluation,
    applyPreprocess,
    runEmbed,
    handleSort,
    template,
    provider,
    currentDataset,
    preprocessVars,
    preprocessPreview,
    tokenEstimate,
    sortedCategories,
  };
}
