import { useState, useEffect } from "react";
import { Task, VectorDensityDataPoint, GraphHopsData, LatencyDataPoint } from "../types/telemetry.types";

export function useRealtimeValue(
  base: number,
  variance: number,
  enabled: boolean,
  interval = 1800
): number {
  const [value, setValue] = useState(base);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      const drift = (Math.random() - 0.5) * variance * 2;
      setValue((prev) => Math.max(0, Math.min(100, prev + drift)));
    }, interval);
    return () => clearInterval(t);
  }, [base, variance, interval, mounted, enabled]);

  return mounted ? value : base;
}

export function useRealtimeArray(
  length: number,
  base: number,
  variance: number,
  enabled: boolean,
  interval = 2000
): number[] {
  const [data, setData] = useState<number[]>(Array(length).fill(base));
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    setData(() =>
      Array.from({ length }, () => base + (Math.random() - 0.5) * variance)
    );
    const t = setInterval(() => {
      setData((prev) =>
        prev.map(() => base + (Math.random() - 0.5) * variance)
      );
    }, interval);
    return () => clearInterval(t);
  }, [length, base, variance, interval, mounted, enabled]);

  return data;
}

export function useAgentCycle(enabled: boolean): string {
  const phases = ["Planning", "Executing", "Verifying", "Complete"] as const;
  const [phase, setPhase] = useState(0);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setPhase((p) => (p + 1) % phases.length);
    }, 2500);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return mounted ? phases[phase] : "Planning";
}

export function useVectorData(enabled: boolean): VectorDensityDataPoint[] {
  const [data, setData] = useState<VectorDensityDataPoint[]>(
    Array.from({ length: 20 }, (_, i) => ({ index: i, score: 0.75 }))
  );
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    setData(() =>
      Array.from({ length: 20 }, (_, i) => ({
        index: i,
        score: Math.random() * 0.5 + 0.5,
      }))
    );
    const t = setInterval(() => {
      setData((prev) =>
        prev.map((d) => ({
          ...d,
          score: Math.max(
            0,
            Math.min(1, d.score + (Math.random() - 0.5) * 0.2)
          ),
        }))
      );
    }, 1500);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return data;
}

export function useGraphHops(enabled: boolean): GraphHopsData {
  const [hops, setHops] = useState<GraphHopsData>({ "1-Hop": 35, "2-Hop": 22, "3-Hop": 12 });
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    setHops({
      "1-Hop": Math.floor(Math.random() * 40 + 20),
      "2-Hop": Math.floor(Math.random() * 30 + 15),
      "3-Hop": Math.floor(Math.random() * 20 + 5),
    });
    const t = setInterval(() => {
      setHops({
        "1-Hop": Math.floor(Math.random() * 40 + 20),
        "2-Hop": Math.floor(Math.random() * 30 + 15),
        "3-Hop": Math.floor(Math.random() * 20 + 5),
      });
    }, 3000);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return hops;
}

export function useTasksStream(enabled: boolean): Task[] {
  const [tasks, setTasks] = useState<Task[]>([
    { id: "T-1024", label: "Network Anomaly Diagnosis", status: "executing", progress: 68 },
    { id: "T-1025", label: "RAG Index Optimization", status: "verifying", progress: 91 },
    { id: "T-1026", label: "CKG Entity Resolution", status: "planning", progress: 12 },
    { id: "T-1027", label: "SLA Compliance Report", status: "queued", progress: 0 },
  ]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setTasks((prev) =>
        prev.map((task) => {
          if (task.status === "executing") {
            const p = Math.min(100, task.progress + Math.floor(Math.random() * 8 + 2));
            return { ...task, progress: p, status: p >= 100 ? "complete" : "executing" };
          }
          if (task.status === "verifying") {
            const p = Math.min(100, task.progress + Math.floor(Math.random() * 4 + 1));
            return { ...task, progress: p, status: p >= 100 ? "complete" : "verifying" };
          }
          if (task.status === "planning" && Math.random() > 0.92) {
            return { ...task, status: "executing" };
          }
          return task;
        })
      );
    }, 2500);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return tasks;
}

export function useWaveformStream(enabled: boolean): number[] {
  const [waveform, setWaveform] = useState<number[]>(
    Array.from({ length: 30 }, () => 25)
  );
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    setWaveform(Array.from({ length: 30 }, () => Math.random() * 40 + 10));
    const t = setInterval(() => {
      setWaveform((prev) => [
        ...prev.slice(1),
        Math.random() * 40 + 10,
      ]);
    }, 300);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return waveform;
}

export function useContextLatencyStream(enabled: boolean): LatencyDataPoint[] {
  const [data, setData] = useState<LatencyDataPoint[]>(
    Array.from({ length: 20 }, (_, i) => ({ t: i, v: 65 }))
  );
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    const t = setInterval(() => {
      setData((prev) => [
        ...prev.slice(1),
        { t: prev.length, v: 40 + Math.random() * 50 },
      ]);
    }, 1200);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return data;
}

export function useWeightDataStream(enabled: boolean): { name: string; weight: number }[] {
  const [weightData, setWeightData] = useState<{ name: string; weight: number }[]>(
    Array.from({ length: 6 }, (_, i) => ({ name: `R${i + 1}`, weight: 50 }))
  );
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || !enabled) return;
    setWeightData(
      Array.from({ length: 6 }, (_, i) => ({
        name: `R${i + 1}`,
        weight: Math.random() * 100,
      }))
    );
    const t = setInterval(() => {
      setWeightData((prev) =>
        prev.map((d) => ({
          ...d,
          weight: Math.max(5, Math.min(100, d.weight + (Math.random() - 0.5) * 20)),
        }))
      );
    }, 2000);
    return () => clearInterval(t);
  }, [mounted, enabled]);

  return weightData;
}

export function useTelemetryStream(enabled: boolean) {
  // Real-Time simulate state values
  const systemLoad = useRealtimeValue(42, 8, enabled, 1500);
  const activeRequests = useRealtimeValue(7, 3, enabled, 1200);
  const throughput = useRealtimeValue(25.4, 4, enabled, 1800);
  const sessionTime = useRealtimeValue(168, 5, enabled, 3000);
  const modelHealth = useRealtimeValue(96, 3, enabled, 2000);
  const concurrentSessions = useRealtimeValue(15, 2, enabled, 2500);
  const queryPieData = useRealtimeArray(3, 40, 15, enabled, 2000);

  const successRate = useRealtimeValue(87, 5, enabled, 2000);
  const autoRate = useRealtimeValue(72, 8, enabled, 2500);
  const humanRate = useRealtimeValue(28, 8, enabled, 2500);
  const currentPhase = useAgentCycle(enabled);

  const vectorData = useVectorData(enabled);
  const hit = useRealtimeValue(65, 8, enabled, 1500);
  const miss = useRealtimeValue(22, 6, enabled, 1500);
  const fallback = useRealtimeValue(13, 4, enabled, 1500);
  const avgScore = useRealtimeValue(74, 5, enabled, 2000);

  const graphHops = useGraphHops(enabled);
  const tasks = useTasksStream(enabled);
  const waveform = useWaveformStream(enabled);
  const contextLatencyData = useContextLatencyStream(enabled);
  const weightData = useWeightDataStream(enabled);

  return {
    systemLoad,
    activeRequests,
    throughput,
    sessionTime,
    modelHealth,
    concurrentSessions,
    queryPieData,
    successRate,
    autoRate,
    humanRate,
    currentPhase,
    vectorData,
    hit,
    miss,
    fallback,
    avgScore,
    graphHops,
    tasks,
    waveform,
    contextLatencyData,
    weightData,
  };
}



