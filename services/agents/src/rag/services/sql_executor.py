import os
import sqlite3
import logging
from typing import List, Dict, Any

logger = logging.getLogger("rag.sql_executor")

# Set up local database path matching backend/rag/data/rag_relational.db
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
RELATIONAL_DB_PATH = os.path.join(DATA_DIR, "rag_relational.db")

def execute_sql_query(sql_query: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query against the local SQLite database in a safe read-only format
    and returns the results as a list of dictionaries.
    """
    conn = None
    try:
        logger.info(f"Executing SQLite query: {sql_query}")
        # Connect to SQLite file (creates it if it does not exist)
        conn = sqlite3.connect(RELATIONAL_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enforce SQLite query safety (basic validation)
        cleaned_query = sql_query.strip().lower()
        forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "create", "replace", "truncate"]
        if any(keyword in cleaned_query for keyword in forbidden_keywords):
            raise ValueError("Execution rejected: Only SELECT queries are permitted.")
            
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        logger.info(f"Query executed successfully, retrieved {len(results)} rows.")
        return results
    except Exception as e:
        logger.error(f"Failed to execute SQL query '{sql_query}': {e}", exc_info=True)
        raise e
    finally:
        if conn:
            conn.close()
