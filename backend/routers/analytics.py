from fastapi import APIRouter
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Mock datasets from the frontend
SALES_DATA = [
    {"order_id": "ORD-10482", "region": "EMEA", "revenue": 2840.5, "order_date": "2025-10-12", "segment": "Enterprise"},
    {"order_id": "ORD-10483", "region": "APAC", "revenue": 1299.0, "order_date": "2025-10-13", "segment": "Mid-Market"},
    {"order_id": "ORD-10484", "region": "NA", "revenue": 5420.75, "order_date": "2025-10-13", "segment": "Enterprise"},
    {"order_id": "ORD-10485", "region": "LATAM", "revenue": 890.2, "order_date": "2025-10-14", "segment": "SMB"},
    {"order_id": "ORD-10486", "region": "EMEA", "revenue": 3102.0, "order_date": "2025-10-15", "segment": "Enterprise"},
]

SEGMENTS_DATA = [
    {"customer_id": 10042, "segment": "Champions", "lifetime_value": 18420.0, "churn_risk": 0.04},
    {"customer_id": 10043, "segment": "At Risk", "lifetime_value": 2100.5, "churn_risk": 0.71},
    {"customer_id": 10044, "segment": "Loyal", "lifetime_value": 9320.0, "churn_risk": 0.12},
    {"customer_id": 10045, "segment": "New", "lifetime_value": 480.0, "churn_risk": 0.28},
    {"customer_id": 10046, "segment": "Champions", "lifetime_value": 22100.0, "churn_risk": 0.03},
]

INVENTORY_DATA = [
    {"sku": "SKU-A12", "warehouse": "US-EAST", "quantity": 420, "reorder_flag": False},
    {"sku": "SKU-B07", "warehouse": "EU-WEST", "quantity": 18, "reorder_flag": True},
    {"sku": "SKU-C31", "warehouse": "APAC", "quantity": 156, "reorder_flag": False},
    {"sku": "SKU-D09", "warehouse": "US-WEST", "quantity": 5, "reorder_flag": True},
    {"sku": "SKU-E22", "warehouse": "US-EAST", "quantity": 890, "reorder_flag": False},
]


@router.get("/correlation")
async def get_correlation_matrix() -> dict:
    """
    Compute correlation matrix from all datasets using numeric features.
    Returns correlation matrix with feature names for labeling.
    """
    try:
        # Extract numeric features from all datasets
        numeric_features = {
            "Revenue": [d["revenue"] for d in SALES_DATA],
            "Lifetime Value": [d["lifetime_value"] for d in SEGMENTS_DATA],
            "Churn Risk": [d["churn_risk"] for d in SEGMENTS_DATA],
            "Inventory Qty": [d["quantity"] for d in INVENTORY_DATA],
        }

        # Pad shorter arrays with their mean to match length (5 rows each)
        for key in numeric_features:
            while len(numeric_features[key]) < 5:
                numeric_features[key].append(np.mean(numeric_features[key]))

        # Create DataFrame
        df = pd.DataFrame(numeric_features)

        # Compute correlation matrix
        correlation = df.corr().fillna(0)

        # Convert to list of lists for frontend consumption
        features = correlation.columns.tolist()
        values = []

        for i, row_feature in enumerate(features):
            for j, col_feature in enumerate(features):
                # Normalize correlation to 0-100 range (from -1 to 1)
                corr_value = correlation.iloc[i, j]
                normalized = ((corr_value + 1) / 2) * 100  # Maps -1..1 to 0..100

                values.append({
                    "row": i,
                    "col": j,
                    "value": round(normalized, 1),
                    "correlation": round(corr_value, 3),
                })

        return {
            "features": features,
            "values": values,
            "size": len(features),
        }
    except Exception as e:
        return {"error": str(e), "features": [], "values": [], "size": 0}
