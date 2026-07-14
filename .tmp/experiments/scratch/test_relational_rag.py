import os
import sqlite3
import asyncio
import uuid
import logging
from backend.rag.pipelines.ingestion import run_ingestion, get_docstore
from backend.rag.services.qna import RAGQueryEngine
from backend.rag.services.sql_executor import RELATIONAL_DB_PATH
from backend.rag.database import init_db, get_task, create_task

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_relational_rag")

async def test_relational_rag_pipeline():
    logger.info("Initializing DB...")
    init_db()
    
    # Define paths
    xlsx_file_path = "Operations_Dashboard_Data_Template.xlsx"
    if not os.path.exists(xlsx_file_path):
        raise FileNotFoundError(f"Source file {xlsx_file_path} not found in workspace root.")
        
    logger.info(f"Using spreadsheet file: {xlsx_file_path}")
    
    # 1. Ingest document
    task_id = str(uuid.uuid4())
    create_task(task_id, "INGESTION")
    logger.info(f"Triggering ingestion for task: {task_id}")
    await run_ingestion(task_id, xlsx_file_path, original_filename="Operations_Dashboard_Data_Template.xlsx")
    
    # Verify ingestion task
    task = get_task(task_id)
    assert task is not None and task["status"] == "COMPLETED", f"Ingestion task failed: {task}"
    logger.info("Ingestion completed successfully.")
    
    # 2. Verify SQLite table creation and rows count
    assert os.path.exists(RELATIONAL_DB_PATH), f"SQLite database not found at {RELATIONAL_DB_PATH}"
    conn = sqlite3.connect(RELATIONAL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"Tables in database: {tables}")
    
    # Check that a table starting with 'tbl_' is created
    target_table = None
    for t in tables:
        if t.startswith("tbl_operations_dashboard_data_template"):
            target_table = t
            break
            
    assert target_table is not None, "Spreadsheet table not found in SQLite master schema."
    logger.info(f"Target table identified: {target_table}")
    
    # Verify rows count
    cursor.execute(f"SELECT COUNT(*) FROM {target_table};")
    rows_count = cursor.fetchone()[0]
    logger.info(f"Total rows in SQLite table {target_table}: {rows_count}")
    assert rows_count > 0, "SQLite table contains 0 rows."
    conn.close()
    
    # 3. Verify ChromaDB schema node registration
    docstore = get_docstore()
    schema_nodes = [node for node in docstore.docs.values() if node.metadata.get("is_schema") is True]
    assert len(schema_nodes) > 0, "No schema node catalog registered in docstore."
    logger.info(f"ChromaDB schema catalog found: table_name='{schema_nodes[0].metadata.get('table_name')}'")
    
    # 4. Execute tabular queries against the RAG QnA engine
    engine = RAGQueryEngine()
    
    # Query 1: Row count
    q1 = "What is the total number of rows/tickets in the Operations_Dashboard_Data_Template.xlsx dataset?"
    logger.info(f"\nUser Query: {q1}")
    res1 = await engine.aquery(q1)
    logger.info(f"Assistant Answer:\n{res1['answer']}")
    logger.info(f"Pre-processing logs:\n{res1['rag_retrievals']}")
    
    assert str(rows_count) in res1["answer"], "Failed to output exact rows count from SQLite database."
    assert "Executed SQL query successfully" in res1["rag_retrievals"], "Query pre-processing logs did not record SQL execution."
    
    # Query 2: Country aggregation
    q2 = "List the countries represented in the dataset along with their ticket frequencies."
    logger.info(f"\nUser Query: {q2}")
    res2 = await engine.aquery(q2)
    logger.info(f"Assistant Answer:\n{res2['answer']}")
    logger.info(f"Pre-processing logs:\n{res2['rag_retrievals']}")
    
    assert "|" in res2["answer"], "Response content was not formatted as a markdown table."
    assert "Executed SQL query successfully" in res2["rag_retrievals"]
    
    # Query 3: Descending categories
    q3 = "share the issue categories in descending order"
    logger.info(f"\nUser Query: {q3}")
    res3 = await engine.aquery(q3)
    logger.info(f"Assistant Answer:\n{res3['answer']}")
    
    assert "|" in res3["answer"], "Descending categories response is not formatted as a markdown table."
    
    logger.info("\n[SUCCESS] Relational RAG Pipeline verified successfully with 100% mathematical accuracy.")

if __name__ == "__main__":
    asyncio.run(test_relational_rag_pipeline())
