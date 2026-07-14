import os
import sys
import chromadb

def inspect():
    db_path = "./chroma_db"
    if not os.path.exists(db_path):
        print(f"Error: ChromaDB path '{db_path}' does not exist.")
        return

    client = chromadb.PersistentClient(path=db_path)
    collections = client.list_collections()
    
    print("\n=== Chroma Vector Database Inspection ===")
    print(f"Persist Directory: {os.path.abspath(db_path)}")
    print(f"Total Collections: {len(collections)}")
    print("-" * 50)

    for c in collections:
        col = client.get_collection(c.name)
        count = col.count()
        print(f"\nCollection Name: '{c.name}'")
        print(f"Total Vectorized Items: {count}")
        
        if count == 0:
            continue
            
        data = col.get()
        
        schemas = []
        summaries = []
        regular_chunks = []
        
        for idx, meta in enumerate(data.get("metadatas", [])):
            doc_id = data["ids"][idx]
            doc_text = data["documents"][idx] if data.get("documents") else ""
            
            if meta and meta.get("is_schema") is True:
                schemas.append((doc_id, meta.get("table_name"), meta.get("source")))
            elif meta and meta.get("is_summary") is True:
                summaries.append((doc_id, meta.get("source"), len(doc_text)))
            else:
                regular_chunks.append((doc_id, meta.get("source") if meta else None, len(doc_text)))

        print(f"  └─ Schema Metadata Nodes: {len(schemas)}")
        print(f"  └─ Analytical Summaries:  {len(summaries)}")
        print(f"  └─ Regular Text Chunks:   {len(regular_chunks)}")

        if schemas:
            print("\n  --> Table Schemas Stored in Vector DB:")
            print(f"  {'Node ID':<50} | {'SQLite Table':<40} | {'Source File'}")
            print(f"  {'-'*50}-|-{'-'*40}-|-{'-'*30}")
            for doc_id, table_name, source in schemas:
                print(f"  {doc_id:<50} | {str(table_name):<40} | {str(source)}")

        if summaries:
            print("\n  --> Dataset Summaries (first 5):")
            print(f"  {'Node ID':<50} | {'Source File':<40} | {'Length (chars)'}")
            print(f"  {'-'*50}-|-{'-'*40}-|-{'-'*15}")
            for doc_id, source, length in summaries[:5]:
                print(f"  {doc_id:<50} | {str(source):<40} | {length}")

if __name__ == "__main__":
    try:
        inspect()
    except Exception as e:
        print(f"Failed to inspect ChromaDB: {e}", file=sys.stderr)
