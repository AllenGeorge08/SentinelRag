"""Whole pipeline tests — FastAPI enqueue + RQ worker round-trip (no mocks).

Note: The full end-to-end flow (/chat → RQ worker → /job-status) requires a
background `rq worker` process running separately and is intentionally not
covered here.
"""

from fastapi.testclient import TestClient

from app.rag.server import app

client = TestClient(app)


def test_root_endpoint_is_healthy():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Server is up and running"


def test_chat_enqueues_job_and_returns_job_id():
    response = client.post("/chat", params={"query": "What is prompt injection?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "job_id" in data
    assert isinstance(data["job_id"], str)
