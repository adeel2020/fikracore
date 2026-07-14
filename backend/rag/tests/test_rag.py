import os
import asyncio
import pytest
from backend.rag.pipelines.ingestion import run_ingestion
from backend.rag.services.qna import RAGQueryEngine
from backend.rag.database import get_task, init_db, create_task

@pytest.mark.asyncio
async def test_rag_flow():
    # 1. Initialize Task DB
    init_db()
    
    # 2. Create a dummy test document
    temp_file = "test_doc.txt"
    with open(temp_file, "w") as f:
        f.write(
            "VoLTE Connectivity troubleshooting guide:\n"
            "If a user complains about mobile connectivity issues, first verify the SIM profile.\n"
            "Preconditions: SIM status must be ACTIVE in HLR registry and balance must be above zero.\n"
            "If preconditions are met, check the error code. For PLMN Forbidden warning, escalate to Core team.\n"
        )
        
    try:
        # 3. Trigger ingestion task
        import uuid
        task_id = str(uuid.uuid4())
        create_task(task_id, "INGESTION")
        await run_ingestion(task_id, temp_file)
        
        # 4. Check status in DB
        task = get_task(task_id)
        assert task is not None
        assert task["status"] == "COMPLETED"
        assert task["metadata"]["child_nodes_count"] > 0
        
        # 5. Run a diagnostic query
        engine = RAGQueryEngine()
        result = await engine.aquery("What preconditions must be checked for mobile connectivity issues?")
        
        assert "answer" in result
        assert len(result["source_nodes"]) > 0
        print("\n[Test Result] Generated Answer:", result["answer"])
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    asyncio.run(test_rag_flow())
