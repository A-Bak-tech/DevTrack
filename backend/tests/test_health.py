
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "devtrack-api"
    }


def test_unknown_route():
    response = client.get("/api/v1/not-a-route")

    assert response.status_code == 404
