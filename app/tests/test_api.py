from fastapi.testclient import TestClient
from app.main import app
import pytest


client = TestClient(app)

@pytest.mark.asyncio
async def test_get_health_not_initialized():
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() ==  {
        "status": "healthy",
        "bot":  "not initialized",
        "dispatcher":  "not initialized"
    }