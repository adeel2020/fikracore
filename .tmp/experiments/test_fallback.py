import os
from backend.datastory.crewai_storyteller import run_cluster_story

if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

print(run_cluster_story("eSIM not active"))
