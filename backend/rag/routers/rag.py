import os
import uuid
import shutil
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException

from backend.rag.database import create_task, get_task
from backend.rag.pipelines.ingestion import run_ingestion
from backend.rag.services.qna import RAGQueryEngine
from backend.rag.tests.eval import run_evaluation

router = APIRouter(prefix="/rag", tags=["RAG Console"])

# Temp upload folder
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

class Message(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class QueryRequest(BaseModel):
    query: str
    chat_history: List[Message] = []


class EvalRequest(BaseModel):
    queries: List[str]

@router.post("/ingest")
async def ingest_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".pdf", ".xlsx", ".csv", ".md"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
        
    # Check if a file with the same filename has already been ingested
    try:
        import sqlite3
        import json
        from backend.rag.database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT task_id, metadata FROM tasks WHERE task_type = 'INGESTION'")
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            if meta.get("filename") == file.filename:
                # Purge old task and associated chunks/tables
                await delete_ingested_file(row["task_id"])
    except Exception:
        pass

    task_id = str(uuid.uuid4())
    temp_file_path = os.path.join(TEMP_DIR, f"{task_id}{ext}")
    
    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    create_task(task_id, "INGESTION")
    
    background_tasks.add_task(run_ingestion, task_id, temp_file_path, file.filename)
    
    return {"task_id": task_id, "status": "PENDING"}

@router.get("/ingest/list")
async def list_ingested_files():
    import sqlite3
    import json
    from backend.rag.database import DB_PATH
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT task_id, status, metadata, updated_at FROM tasks WHERE task_type = 'INGESTION' ORDER BY updated_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        
        task_filenames = set()
        files = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            filename = meta.get("filename") or f"Document {row['task_id'][:8]}"
            task_filenames.add(filename.lower())
            files.append({
                "task_id": row["task_id"],
                "filename": filename,
                "status": row["status"],
                "child_nodes": meta.get("child_nodes_count", 0),
                "parent_nodes": meta.get("parent_nodes_count", 0),
                "timestamp": row["updated_at"]
            })
            
        # Dynamically scan ChromaDB for any schema nodes not in the tasks list
        try:
            from backend.rag.infrastructure.vector_factory import get_vector_store, ChromaVectorStoreWrapper
            from backend.rag.config import rag_settings
            vstore = await get_vector_store()
            if isinstance(vstore, ChromaVectorStoreWrapper):
                for c_name in [rag_settings.chroma_collection_name, f"{rag_settings.chroma_collection_name}-local"]:
                    try:
                        col = vstore.db.get_collection(c_name)
                        res = col.get(where={"is_schema": True})
                        if res and res.get("metadatas"):
                            for meta in res["metadatas"]:
                                if meta:
                                    source = meta.get("source")
                                    table_name = meta.get("table_name")
                                    if source and source.lower() not in task_filenames:
                                        files.append({
                                            "task_id": f"sync_{table_name}",
                                            "filename": source,
                                            "status": "COMPLETED",
                                            "child_nodes": 0,
                                            "parent_nodes": 0,
                                            "timestamp": "2026-07-08T00:00:00"
                                        })
                                        task_filenames.add(source.lower())
                    except Exception:
                        pass
        except Exception as scan_err:
            pass
            
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/ingest/{task_id}")
async def delete_ingested_file(task_id: str):
    import sqlite3
    import json
    import re
    from backend.rag.database import DB_PATH, get_task
    from backend.rag.pipelines.ingestion import DOCSTORE_PATH, get_docstore
    from backend.rag.infrastructure.vector_factory import get_vector_store, ChromaVectorStoreWrapper
    from backend.rag.config import rag_settings

    filename = None
    table_name = None

    if task_id.startswith("sync_"):
        table_name = task_id[5:]
        try:
            vstore = await get_vector_store()
            if isinstance(vstore, ChromaVectorStoreWrapper):
                for c_name in [rag_settings.chroma_collection_name, f"{rag_settings.chroma_collection_name}-local"]:
                    try:
                        col = vstore.db.get_collection(c_name)
                        res = col.get(ids=[f"schema_{table_name}"])
                        if res and res.get("metadatas") and res["metadatas"][0]:
                            filename = res["metadatas"][0].get("source")
                            break
                    except Exception:
                        pass
        except Exception:
            pass
            
        if not filename:
            filename = table_name[4:] + ".xlsx"
    else:
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Ingestion task not found.")
        filename = task["metadata"].get("filename")

    if not filename:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            conn.close()
            return {
                "status": "SUCCESS",
                "message": "Legacy task entry removed from registry. Chunks were not purged as no filename was registered."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete legacy task: {str(e)}")

    try:
        if not table_name:
            ext = os.path.splitext(filename)[1].lower()
            if ext in [".xlsx", ".csv"]:
                def sanitize_identifier(name: str) -> str:
                    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
                    sanitized = re.sub(r'_+', '_', sanitized)
                    if not re.match(r'^[a-zA-Z_]', sanitized):
                        sanitized = 'col_' + sanitized
                    return sanitized.lower()
                table_name = "tbl_" + sanitize_identifier(os.path.splitext(filename)[0])

        if table_name:
            try:
                from backend.rag.services.sql_executor import RELATIONAL_DB_PATH
                conn_rel = sqlite3.connect(RELATIONAL_DB_PATH)
                cursor_rel = conn_rel.cursor()
                cursor_rel.execute(f"DROP TABLE IF EXISTS {table_name};")
                conn_rel.commit()
                conn_rel.close()
            except Exception:
                pass

        try:
            vstore = await get_vector_store()
            if isinstance(vstore, ChromaVectorStoreWrapper):
                for c_name in [rag_settings.chroma_collection_name, f"{rag_settings.chroma_collection_name}-local"]:
                    try:
                        col = vstore.db.get_collection(c_name)
                        if table_name:
                            try:
                                col.delete(ids=[f"schema_{table_name}"])
                            except Exception:
                                pass
                        # Delete using original filename
                        res = col.get(where={"source": filename})
                        if res and res.get("ids"):
                            col.delete(ids=res["ids"])
                        # Also delete using task_id (UUID filename) if present
                        if task_id and not task_id.startswith("sync_"):
                            for ext in [".txt", ".pdf", ".xlsx", ".csv", ".md"]:
                                res_uuid = col.get(where={"file_name": f"{task_id}{ext}"})
                                if res_uuid and res_uuid.get("ids"):
                                    col.delete(ids=res_uuid["ids"])
                                res_path = col.get(where={"source": f"{task_id}{ext}"})
                                if res_path and res_path.get("ids"):
                                    col.delete(ids=res_path["ids"])
                    except Exception:
                        pass
        except Exception:
            pass

        docstore = get_docstore()
        node_ids_to_delete = []
        for node_id, node in list(docstore.docs.items()):
            node_file = node.metadata.get("file_name") or node.metadata.get("source")
            if node_file:
                if node_file == filename or (task_id and str(task_id) in str(node_file)):
                    node_ids_to_delete.append(node_id)
                
        if node_ids_to_delete:
            for nid in node_ids_to_delete:
                docstore.delete_document(nid, raise_error=False)
            docstore.persist(DOCSTORE_PATH)

        if not task_id.startswith("sync_"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            conn.close()

        return {
            "status": "SUCCESS",
            "message": f"Successfully deleted '{filename}' and purged associated chunks/relational tables.",
            "deleted_chunks_count": len(node_ids_to_delete)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/ingest/status/{task_id}")
async def get_ingest_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Ingestion task not found.")
    return task

@router.post("/query")
async def run_query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    engine = RAGQueryEngine()
    history_list = [m.model_dump() for m in request.chat_history]
    result = await engine.aquery(request.query, chat_history=history_list)
    return result


@router.post("/evaluate")
async def evaluate_rag(request: EvalRequest, background_tasks: BackgroundTasks):
    if not request.queries:
        raise HTTPException(status_code=400, detail="Query list cannot be empty.")
        
    task_id = str(uuid.uuid4())
    create_task(task_id, "EVALUATION")
    
    background_tasks.add_task(run_evaluation, task_id, request.queries)
    return {"task_id": task_id, "status": "PENDING"}

@router.get("/evaluate/status/{task_id}")
async def get_evaluate_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Evaluation task not found.")
    return task

@router.get("/chart-screenshot/{element_id}")
async def get_chart_screenshot(element_id: str):
    """Captures a screenshot of a specific dashboard chart element via Puppeteer."""
    import base64
    try:
        from whatsapp_integration.backend.routers.whatsapp_router import capture_chart_image
        image_path = capture_chart_image(element_id)
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return {"chart_screenshot": b64, "element_id": element_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot capture failed: {str(e)}")
