"""Test suite for Digital Twin Projection Endpoint."""

from fastapi.testclient import TestClient
from engine_stack.engines.telecom_brain.api.capability_api import router, _find_repo_root
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_find_repo_root():
    root = _find_repo_root()
    assert root.exists()
    assert (root / "artifacts").exists()

def test_digital_twin_projection_endpoint():
    response = client.post("/api/v1/fikracore/scenarios/SCN-001/digital-twin-projection")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "SCN-001"
    assert "total_nodes" in data
