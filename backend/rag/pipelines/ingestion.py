import os
import asyncio
import logging
from typing import List
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.schema import Document

from backend.rag.config import rag_settings
from backend.rag.database import update_task
from backend.rag.infrastructure.vector_factory import get_vector_store

logger = logging.getLogger("rag.ingestion")

# Local storage path for parent docstore
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DOCSTORE_PATH = os.path.join(DATA_DIR, "docstore.json")

_cached_docstore = None

def get_docstore() -> SimpleDocumentStore:
    global _cached_docstore
    if _cached_docstore is not None:
        return _cached_docstore
        
    if os.path.exists(DOCSTORE_PATH):
        try:
            _cached_docstore = SimpleDocumentStore.from_persist_path(DOCSTORE_PATH)
            return _cached_docstore
        except Exception as e:
            logger.error(f"Failed to load docstore, creating new one: {e}")
            
    _cached_docstore = SimpleDocumentStore()
    return _cached_docstore

async def run_ingestion(task_id: str, file_path: str, original_filename: str = "") -> None:
    try:
        update_task(task_id, "PROCESSING", 0.1, {"status_message": "Reading file..."})
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".xlsx", ".csv"]:
            documents = []
            try:
                import pandas as pd
                import sqlite3
                import re
                from backend.rag.services.sql_executor import RELATIONAL_DB_PATH
                
                if ext == ".xlsx":
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                # Helper to sanitize identifier for SQLite
                def sanitize_identifier(name: str) -> str:
                    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
                    sanitized = re.sub(r'_+', '_', sanitized)
                    if not re.match(r'^[a-zA-Z_]', sanitized):
                        sanitized = 'col_' + sanitized
                    return sanitized.lower()
                
                table_name = "tbl_" + sanitize_identifier(os.path.splitext(original_filename or os.path.basename(file_path))[0])
                
                # Sanitize DataFrame columns
                original_cols = list(df.columns)
                sanitized_cols = [sanitize_identifier(col) for col in original_cols]
                df.columns = sanitized_cols
                
                # Write to SQLite Database
                logger.info(f"Writing spreadsheet to SQLite table '{table_name}'...")
                conn = sqlite3.connect(RELATIONAL_DB_PATH)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                conn.close()
                logger.info(f"Spreadsheet successfully written to SQLite table '{table_name}'.")
                
                # Construct Schema Description Catalog
                schema_lines = [
                    f"Database Table Name: {table_name}",
                    f"Original Filename: {original_filename or os.path.basename(file_path)}",
                    "Columns, Types, and Sample Values:"
                ]
                for orig_col, sanitized_col in zip(original_cols, sanitized_cols):
                    dtype = str(df[sanitized_col].dtype)
                    unique_vals = df[sanitized_col].dropna().unique()
                    if len(unique_vals) > 0:
                        sample_str = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in unique_vals[:5]])
                        schema_lines.append(f"- Column Name (Original): '{orig_col}' | Sanitized SQL Column Name: '{sanitized_col}' | Type: {dtype} | Sample Values: [{sample_str}]")
                    else:
                        schema_lines.append(f"- Column Name (Original): '{orig_col}' | Sanitized SQL Column Name: '{sanitized_col}' | Type: {dtype} | Sample Values: []")
                
                schema_text = "\n".join(schema_lines)
                logger.info(f"Constructed Schema Description Catalog:\n{schema_text}")
                
                # Parse and embed schema catalog directly as a non-split TextNode
                from llama_index.core.schema import TextNode
                schema_node = TextNode(
                    text=schema_text,
                    id_=f"schema_{table_name}",
                    metadata={
                        "source": original_filename or os.path.basename(file_path),
                        "is_schema": True,
                        "table_name": table_name
                    }
                )
                
                docstore = get_docstore()
                docstore.add_documents([schema_node])
                docstore.persist(DOCSTORE_PATH)
                
                vector_store = await get_vector_store()
                await vector_store.add_nodes([schema_node])
                logger.info("Embedded and persisted schema node in docstore and ChromaDB.")
                
                # Generate standard analytical summary for normal RAG pipeline searches
                summary_lines = [
                    f"Structured Tabular Data Summary for file: {original_filename or os.path.basename(file_path)}",
                    f"Total rows: {len(df)}",
                    f"Columns: {', '.join(original_cols)}",
                    "\n--- Value Counts and Categories for each column (descending order of frequency) ---"
                ]
                
                for col in df.columns:
                    # Map back to original name for human readability
                    orig_name = original_cols[df.columns.get_loc(col)]
                    if df[col].nunique() < 50:
                        counts = df[col].value_counts()
                        summary_lines.append(f"\nColumn '{orig_name}':")
                        for val, count in counts.items():
                            summary_lines.append(f"  - {val}: {count} occurrences")
                    else:
                        summary_lines.append(f"\nColumn '{orig_name}' has high cardinality ({df[col].nunique()} unique values).")
                
                summary_text = "\n".join(summary_lines)
                summary_doc = Document(
                    text=summary_text,
                    metadata={"source": original_filename or os.path.basename(file_path), "is_summary": True}
                )
                documents.append(summary_doc)
                
            except Exception as excel_err:
                logger.error(f"Failed to ingest Excel/CSV: {excel_err}")
                raise excel_err
        else:
            # SimpleDirectoryReader automatically detects file types and parses them
            reader = SimpleDirectoryReader(input_files=[file_path])
            documents = reader.load_data()

        
        if not documents:
            raise ValueError("No text or content extracted from file.")
            
        update_task(task_id, "PROCESSING", 0.3, {"status_message": "Parsing and chunking documents..."})
        
        # Parent-Child split config: 1000-token parents and 200-token children
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=[1000, 200],
            chunk_overlap=20
        )
        
        nodes = node_parser.get_nodes_from_documents(documents)
        
        # Extract leaf (child) nodes and parent nodes
        leaf_nodes = get_leaf_nodes(nodes)
        
        update_task(task_id, "PROCESSING", 0.6, {
            "status_message": f"Persisting parent nodes (Total nodes: {len(nodes)})..."
        })
        
        # Persist all nodes in the document store so parent mappings are preserved
        docstore = get_docstore()
        docstore.add_documents(nodes)
        docstore.persist(DOCSTORE_PATH)
        
        update_task(task_id, "PROCESSING", 0.8, {
            "status_message": f"Indexing {len(leaf_nodes)} child nodes to vector database..."
        })
        
        # Load vector store from factory
        vector_store = await get_vector_store()
        
        # Index the leaf nodes
        await vector_store.add_nodes(leaf_nodes)
        
        update_task(task_id, "COMPLETED", 1.0, {
            "status_message": "Ingestion successful.",
            "filename": original_filename or os.path.basename(file_path),
            "child_nodes_count": len(leaf_nodes),
            "parent_nodes_count": len(nodes) - len(leaf_nodes)
        })
        
    except Exception as e:
        logger.exception(f"Ingestion failed for task {task_id}: {e}")
        update_task(task_id, "FAILED", 1.0, error=str(e))
