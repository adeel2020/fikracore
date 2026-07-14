import os
import asyncio
import uuid
import logging
from backend.rag.pipelines.ingestion import run_ingestion
from backend.rag.services.qna import RAGQueryEngine
from backend.rag.database import init_db, create_task, get_task

logging.basicConfig(level=logging.INFO)

async def test_multi_turn_chat():
    print("Initializing Database...")
    init_db()
    
    # Create temporary guide text file
    temp_file = "test_conversation_doc.txt"
    with open(temp_file, "w") as f:
        f.write(
            "VoLTE Connectivity troubleshooting guide:\n"
            "If a user complains about mobile connectivity issues, first verify the SIM profile.\n"
            "Preconditions: SIM status must be ACTIVE in HLR registry and balance must be above zero.\n"
            "If preconditions are met, check the error code. For PLMN Forbidden warning, escalate to Core team.\n"
        )
        
    try:
        print("Ingesting test document...")
        task_id = str(uuid.uuid4())
        create_task(task_id, "INGESTION")
        await run_ingestion(task_id, temp_file)
        
        # Verify ingestion
        task = get_task(task_id)
        assert task is not None and task["status"] == "COMPLETED", "Ingestion failed!"
        print("Document ingested successfully.")
        
        # First turn query
        engine = RAGQueryEngine()
        query_1 = "What preconditions must be checked for mobile connectivity issues?"
        print(f"\nUser: {query_1}")
        result_1 = await engine.aquery(query_1)
        print(f"Assistant: {result_1['answer']}")
        print(f"Result 1 metadata: hyde_query='{result_1.get('hyde_query')}', source_nodes_count={len(result_1.get('source_nodes', []))}")
        
        assert "ACTIVE" in result_1["answer"] or "HLR" in result_1["answer"], "Failed to retrieve correct preconditions!"
        
        # Second turn: follow-up query relying on history
        query_2 = "What should I do if they are met?"
        print(f"\nUser: {query_2}")
        
        # Construct chat history payload
        chat_history = [
            {"role": "user", "content": query_1},
            {"role": "assistant", "content": result_1["answer"]}
        ]
        
        result_2 = await engine.aquery(query_2, chat_history=chat_history)
        print(f"Assistant: {result_2['answer']}")
        print(f"Result 2 metadata: hyde_query='{result_2.get('hyde_query')}', source_nodes_count={len(result_2.get('source_nodes', []))}")
        if result_2.get('source_nodes'):
            for idx, node in enumerate(result_2['source_nodes']):
                print(f"  - Node {idx+1} (Score: {node.get('score')}): {node.get('content')[:120]}...")
        
        assert "error code" in result_2["answer"].lower() or "plmn forbidden" in result_2["answer"].lower() or "core team" in result_2["answer"].lower(), \
            "Failed to resolve follow-up context using chat history!"
            
        print("\n[SUCCESS] Multi-turn conversational flow verified successfully.")
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    asyncio.run(test_multi_turn_chat())
