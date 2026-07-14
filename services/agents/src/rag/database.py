import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

# Place the task database in backend/rag/data/
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "tasks.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            progress REAL DEFAULT 0.0,
            metadata TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_task(task_id: str, task_type: str) -> str:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO tasks (task_id, task_type, status, progress, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, task_type, "PENDING", 0.0, now, now)
    )
    conn.commit()
    conn.close()
    return task_id

def update_task(
    task_id: str,
    status: str,
    progress: float,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    meta_json = json.dumps(metadata) if metadata is not None else None
    
    cursor.execute(
        """
        UPDATE tasks 
        SET status = ?, progress = ?, metadata = COALESCE(?, metadata), error = ?, updated_at = ?
        WHERE task_id = ?
        """,
        (status, progress, meta_json, error, now, task_id)
    )
    conn.commit()
    conn.close()

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "task_id": row["task_id"],
        "task_type": row["task_type"],
        "status": row["status"],
        "progress": row["progress"],
        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        "error": row["error"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }
