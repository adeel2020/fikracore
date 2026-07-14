import os
import pandas as pd
import matplotlib.pyplot as plt
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# ==========================================
# MODULE 1: THE ORCHESTRATOR (CLI WIZARD)
# ==========================================
def interactive_data_loader():
    """Handles Human-in-the-loop CSV reading and schema building before AI execution."""
    print("🤖 AI DATA STORYTELLING SYSTEM")
    print("-" * 50)
    
    file_path = input("1. Enter data file path (e.g., churn_sample.csv): ").strip()
    
    try:
        df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        exit()

    print(f"\n✅ File loaded successfully. Found {len(df.columns)} columns.")
    print("2. Enter a short description for each column (or press Enter to skip).")
    
    schema_descriptions = []
    for col in df.columns:
        desc = input(f"   ➤ Describe '{col}': ").strip()
        if desc:
            schema_descriptions.append(f"- **{col}**: {desc}")
        else:
            schema_descriptions.append(f"- **{col}**: (No description provided)")

    # Build the massive context payload to inject into the Agents
    data_context = f"""
    FILEPATH: {file_path}
    
    DATA DICTIONARY:
    {chr(10).join(schema_descriptions)}
    
    BASIC STATISTICS:
    {df.describe().to_string()}
    """
    
    task_context = input("\n3. Enter the overall business goal/context for this report: ").strip()
    
    return file_path, data_context, task_context

# ==========================================
# MODULE 2: TOOLS
# ==========================================
@tool("Generate Bar Chart Tool")
def generate_chart_tool(filepath: str, x_col: str, y_col: str, chart_title: str) -> str:
    """Generates a bar chart. ONLY use this if the analysts explicitly recommend a visualization."""
    try:
        df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
        plot_df = df.groupby(x_col)[y_col].mean().reset_index().sort_values(by=y_col, ascending=False).head(10)
        
        plt.figure(figsize=(10, 6))
        plt.bar(plot_df[x_col].astype(str), plot_df[y_col], color='#4C72B0')
        plt.title(chart_title)
        plt.xlabel(x_col)
        plt.ylabel(f"Average {y_col}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_path = "insight_chart.png"
        plt.savefig(output_path)
        plt.close()
        return f"SUCCESS: Chart saved as {output_path}. Tell the storyteller to embed this image."
    except Exception as e:
        return f"FAILED to generate chart: {str(e)}"

# ==========================================
# MODULE 3: AGENTS
# ==========================================
biz_agent = Agent(
    role="Business Analyst",
    goal="Identify revenue, churn, and executive-level business trends from the data.",
    backstory="You are an elite MBA analyst. You look at data purely for profitability and retention.",
    verbose=True
)

tech_agent = Agent(
    role="Technical Systems Analyst",
    goal="Identify system failures, errors, latencies, and IT bottlenecks.",
    backstory="You are a senior site reliability engineer. You find where the tech is breaking.",
    verbose=True
)

viz_agent = Agent(
    role="Data Visualization Specialist",
    goal="Read the analysts' reports and generate a chart if they recommend one.",
    backstory="You are a Python data visualizer. If the analysts mention a key relationship between two variables, you use your tool to graph it. If no chart is needed, you do nothing.",
    verbose=True,
    tools=[generate_chart_tool]
)

story_agent = Agent(
    role="Data Storyteller",
    goal="Aggregate all insights into a unified, human-readable markdown blog post.",
    backstory="An elite data journalist. You synthesize the business and tech reports into a compelling narrative. Be very specific and to the point story of the data to facilitate decision making",
    verbose=True
)

# ==========================================
# MODULE 4: EXECUTION
# ==========================================
def main():
    # 1. Run the Human-in-the-Loop CLI Wizard
    filepath, data_context, task_context = interactive_data_loader()
    print("\n🚀 Initiating Multi-Agent Analysis...\n")

    # 2. Define Tasks
    # ASYNC TASKS: Biz and Tech run at the exact same time!
    biz_task = Task(
        description=f"Context: {task_context}\nData Context: {data_context}\nExtract exactly 2 key business insights. If a specific relationship is critical, explicitly state: 'RECOMMEND CHART: [X-axis] vs [Y-axis]'.",
        expected_output="A short business summary, optionally requesting a chart.",
        agent=biz_agent,
        async_execution=True # <--- Architectural Best Practice
    )

    tech_task = Task(
        description=f"Context: {task_context}\nData Context: {data_context}\nExtract exactly 2 technical insights. If a specific technical failure is critical, explicitly state: 'RECOMMEND CHART: [X-axis] vs [Y-axis]'.",
        expected_output="A short technical summary, optionally requesting a chart.",
        agent=tech_agent,
        async_execution=True # <--- Architectural Best Practice
    )

    # SEQUENTIAL TASK: Viz Agent waits for analysts to finish
    viz_task = Task(
        description=f"Review the outputs of the Business and Technical tasks. If either requested a chart, use your tool to generate it using '{filepath}'. If neither requested a chart, simply output 'No visualization required.'",
        expected_output="Confirmation of chart generation or a statement that none was needed.",
        agent=viz_agent,
        context=[biz_task, tech_task] # <--- Explicitly passes previous outputs
    )

    # FINAL TASK: Storyteller aggregates everything
    story_task = Task(
        description="Read the Business report, Technical report, and Visualization status. Write a highly engaging, markdown-formatted executive blog post. If a chart was successfully generated, embed `![Insight Chart](insight_chart.png)` into the narrative.",
        expected_output="A final markdown blog post.",
        agent=story_agent,
        context=[biz_task, tech_task, viz_task]
    )

    # 3. Assemble and Run the Crew
    crew = Crew(
        agents=[biz_agent, tech_agent, viz_agent, story_agent],
        tasks=[biz_task, tech_task, viz_task, story_task],
        process=Process.sequential, # Viz and Story tasks remain sequential
        verbose=True
    )

    result = crew.kickoff()
    
    print("\n" + "="*50)
    print("📝 FINAL SYNTHESIZED REPORT")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()