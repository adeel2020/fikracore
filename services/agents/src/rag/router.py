from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agenticaiops_shared.guardrails import check_guardrail_standalone

from rag.database import create_task, get_task, update_task
from rag.services.qna import long_term_memory_query_engine

logger = logging.getLogger("rag.router")
router = APIRouter(prefix="/api/rag", tags=["rag"])
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TEMP_DIR = os.environ.get("RAG_TEMP_DIR") or os.path.join(WORKSPACE_ROOT, ".scratch", "rag_temp")


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=8000)
    session_id: str | None = None


class RAGSearchResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str] = []


class RAGIngestRequest(BaseModel):
    file_path: str = Field("", description="Path to file or directory to ingest")
    collection_name: str = Field("default", description="Target collection for ingestion")


@router.post("/search")
async def search(req: RAGSearchRequest) -> RAGSearchResponse:
    rejection = check_guardrail_standalone(req.query, agent_role="RAG Engine", agent_goal="Retrieve and synthesize information from documents")
    if rejection:
        raise HTTPException(status_code=400, detail=rejection)
    try:
        result = await long_term_memory_query_engine.aquery(req.query, [])
        sources = []
        for node in result.get("source_nodes", []):
            text = getattr(node, "text", str(node))[:100] if node else ""
            sources.append(text)
        return RAGSearchResponse(
            session_id=req.session_id or "default",
            answer=result.get("answer", ""),
            sources=sources,
        )
    except Exception as e:
        logger.error("RAG search failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/ingest/list")
async def list_ingested():
    try:
        from rag.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT task_id, status, metadata, updated_at FROM tasks WHERE task_type = 'INGESTION' ORDER BY updated_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        files = []
        for row in rows:
            meta = json.loads(row["metadata"]) if row["metadata"] else {}
            filename = meta.get("filename") or f"Document {row['task_id'][:8]}"
            files.append({
                "task_id": row["task_id"],
                "filename": filename,
                "status": row["status"],
                "child_nodes": meta.get("child_nodes_count", 0),
                "parent_nodes": meta.get("parent_nodes_count", 0),
                "timestamp": row["updated_at"],
            })
        return files
    except Exception as e:
        logger.warning("Failed to list ingested files: %s", e)
        return []


@router.post("/ingest")
async def ingest_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".txt", ".pdf", ".xlsx", ".csv", ".md"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")

    os.makedirs(TEMP_DIR, exist_ok=True)
    task_id = str(uuid.uuid4())
    temp_file_path = os.path.join(TEMP_DIR, f"{task_id}{ext}")

    with open(temp_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    create_task(task_id, "INGESTION")
    from rag.pipelines.ingestion import run_ingestion
    background_tasks.add_task(run_ingestion, task_id, temp_file_path, file.filename)
    return {"task_id": task_id, "status": "PENDING"}


@router.get("/ingest/status/{task_id}")
async def get_ingest_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Ingestion task not found.")
    return task


@router.delete("/ingest/{task_id}")
async def delete_ingested_file(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Ingestion task not found.")

    filename = task.get("metadata", {}).get("filename", "")
    from rag.pipelines.ingestion import get_docstore, DOCSTORE_PATH
    docstore = get_docstore()

    # Remove nodes from docstore
    nodes_to_delete = []
    for doc_id, node in docstore.docs.items():
        meta = node.metadata if hasattr(node, "metadata") else {}
        if meta.get("source") == filename or meta.get("file_name") == filename:
            nodes_to_delete.append(doc_id)
    for doc_id in nodes_to_delete:
        del docstore.docs[doc_id]
    docstore.persist(DOCSTORE_PATH)

    # Remove from tasks DB
    from rag.database import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()

    return {"status": "deleted", "task_id": task_id, "nodes_removed": len(nodes_to_delete)}


@router.get("/chart-screenshot/{element_id}")
async def get_chart_screenshot(element_id: str):
    """Capture a screenshot of a dashboard chart element via Puppeteer."""
    script_paths = [
        os.path.join(WORKSPACE_ROOT, "frontend", "scripts", "capture_chart.js"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "scripts", "capture_chart.js"),
    ]
    script_path = next((p for p in script_paths if os.path.exists(p)), None)
    if not script_path:
        raise HTTPException(status_code=500, detail="capture_chart.js not found — must run from project root or set WORKSPACE_ROOT")

    frontend_dir = os.path.dirname(os.path.dirname(script_path))
    scratch_dir = "/tmp"
    output_path = os.path.join(scratch_dir, f"{element_id}.png")

    if not os.path.exists(script_path):
        raise HTTPException(status_code=500, detail=f"capture_chart.js not found at {script_path}")

    env = os.environ.copy()
    env["NODE_PATH"] = os.path.join(frontend_dir, "node_modules")
    cmd = ["node", script_path, element_id, output_path, "3000"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=frontend_dir, env=env, timeout=30)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Puppeteer failed: {result.stderr}")
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Screenshot file was not created")
        with open(output_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return {"chart_screenshot": b64, "element_id": element_id}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Puppeteer screenshot timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot capture failed: {str(e)}")
