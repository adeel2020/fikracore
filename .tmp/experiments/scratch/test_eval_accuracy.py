import asyncio
import uuid
from backend.rag.tests.eval import run_evaluation, get_latest_ingested_file, get_pandas_ground_truth
from backend.rag.database import init_db, create_task, get_task

async def test_pandas_eval():
    init_db()
    
    file_info = get_latest_ingested_file()
    print("Latest ingested file:", file_info)
    if not file_info:
        print("No ingested file found. Please run ingestion first.")
        return
        
    file_path, filename = file_info
    
    # Check ground truth calculations
    print("\n--- Ground Truth Verification ---")
    queries = [
        "share the issue categories in descending order",
        "What is the total number of rows/tickets in the Operations_Dashboard_Data_Template.xlsx dataset?",
        "Which rejection reasons are present in the tickets and what are their occurrences?",
        "List the countries represented in the dataset along with their ticket frequencies."
    ]
    for q in queries:
        gt = get_pandas_ground_truth(file_path, q)
        print(f"Query: '{q}'\nGround Truth: {gt}\n")
        
    # Run evaluation
    task_id = str(uuid.uuid4())
    create_task(task_id, "EVALUATION")
    print(f"Triggering evaluation task: {task_id}")
    await run_evaluation(task_id, queries)
    
    task_data = get_task(task_id)
    print("\n--- Evaluation Task Result ---")
    print("Status:", task_data["status"])
    if task_data["status"] == "COMPLETED":
        print("Metrics:", task_data["metadata"]["metrics"])
        for idx, res in enumerate(task_data["metadata"]["detailed_results"]):
            print(f"\nResult {idx+1}: '{res['query']}'")
            print("Pandas Accuracy:", res.get("pandas_accuracy"))
            print("Answer Preview:", res["answer"][:150] + "...")
    else:
        print("Error:", task_data.get("error"))

if __name__ == "__main__":
    asyncio.run(test_pandas_eval())
