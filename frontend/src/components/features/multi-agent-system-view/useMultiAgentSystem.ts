import { useState } from "react";
import { type Agent, type AgentStatus } from "@/components/ui/multi-agent-system";

export function useMultiAgentSystem() {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: "business",
      name: "Business Analyst",
      role: "Revenue & Churn Insights",
      description: "Identifies business trends and revenue patterns",
      icon: "📊",
      status: "idle",
      color: "cyan",
    },
    {
      id: "technical",
      name: "Technical Analyst",
      role: "Systems & Infrastructure",
      description: "Analyzes system failures and IT bottlenecks",
      icon: "⚙️",
      status: "idle",
      color: "blue",
    },
    {
      id: "visualization",
      name: "Visualization Specialist",
      role: "Chart Recommendations",
      description: "Recommends optimal visualizations",
      icon: "📈",
      status: "idle",
      color: "fuchsia",
    },
    {
      id: "storyteller",
      name: "Data Storyteller",
      role: "Narrative Synthesis",
      description: "Creates unified data-driven narratives",
      icon: "📖",
      status: "idle",
      color: "lime",
    },
  ]);

  const [isRunning, setIsRunning] = useState(false);

  const simulateExecution = async () => {
    setIsRunning(true);

    // Phase 1: Activate business and technical agents (parallel)
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "business" || agent.id === "technical"
          ? { ...agent, status: "active" as AgentStatus }
          : agent
      )
    );

    // Wait for parallel agents to complete
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Mark parallel agents as complete
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "business" || agent.id === "technical"
          ? { ...agent, status: "complete" as AgentStatus }
          : agent
      )
    );

    // Phase 2: Activate visualization agent
    await new Promise((resolve) => setTimeout(resolve, 500));
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "visualization"
          ? { ...agent, status: "active" as AgentStatus }
          : agent
      )
    );

    // Wait for visualization to complete
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mark visualization as complete
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "visualization"
          ? { ...agent, status: "complete" as AgentStatus }
          : agent
      )
    );

    // Phase 3: Activate storyteller
    await new Promise((resolve) => setTimeout(resolve, 500));
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "storyteller"
          ? { ...agent, status: "active" as AgentStatus }
          : agent
      )
    );

    // Wait for storyteller to complete
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mark storyteller as complete
    setAgents((prev) =>
      prev.map((agent) =>
        agent.id === "storyteller"
          ? { ...agent, status: "complete" as AgentStatus }
          : agent
      )
    );

    setIsRunning(false);
  };

  const resetAgents = () => {
    setAgents((prev) =>
      prev.map((agent) => ({ ...agent, status: "idle" as AgentStatus }))
    );
    setIsRunning(false);
  };

  return {
    agents,
    isRunning,
    simulateExecution,
    resetAgents,
  };
}
