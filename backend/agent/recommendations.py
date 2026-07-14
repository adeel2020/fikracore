import numpy as np
from backend.database.db import SessionLocal
from backend.database.models import ComplaintTelemetry
from backend.agent.kg_retriever import kg_retriever

def get_historical_recommendations(query: str, limit: int = 3) -> list[dict]:
    """Retrieves top K historically similar resolved complaints from the SQL database."""
    try:
        # Get query embedding vector
        query_vector, _ = kg_retriever.get_embedding(query)
    except Exception as e:
        print(f"[CBR] Failed to encode query vector: {e}")
        return []

    results = []
    try:
        with SessionLocal() as db:
            # Retrieve all historical complaints
            records = db.query(ComplaintTelemetry).all()
            if not records:
                return []

            # Perform semantic vector similarity search
            scored_records = []
            for rec in records:
                try:
                    # Get or calculate embedding for the historical complaint text
                    rec_vector, _ = kg_retriever.get_embedding(rec.raw_complaint)
                    similarity = float(np.dot(query_vector, rec_vector))
                    scored_records.append((rec, similarity))
                except Exception:
                    continue

            # Sort by similarity descending
            scored_records.sort(key=lambda x: x[1], reverse=True)

            for rec, score in scored_records[:limit]:
                # Return matching records with reasonable similarity threshold
                if score >= 0.50:
                    results.append({
                        "complaint_number": rec.complaint_number,
                        "issue_summary": rec.issue_summary,
                        "assignment_target": rec.assignment_target,
                        "reassignment_category": rec.reassignment_category,
                        "resolution_category": rec.resolution_category,
                        "score": score
                    })
    except Exception as e:
        print(f"[CBR] Error during Case-Based Reasoning retrieval: {e}")
        return []
        
    return results
