import traceback
from backend.datastory.crewai_storyteller import run_cluster_story, _extract_cluster_context, _DEFAULT_CACHE
try:
    from crewai import Agent, Task, Crew
    print("CrewAI imported successfully")
except Exception as e:
    print("CrewAI import failed:", e)

try:
    print(run_cluster_story("eSIM not active"))
except Exception as e:
    print("Run failed")
