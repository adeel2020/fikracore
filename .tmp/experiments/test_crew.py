from backend.datastory.crewai_storyteller import run_cluster_story
try:
    print(run_cluster_story("eSIM not active"))
except Exception as e:
    import traceback
    traceback.print_exc()
