from fastapi.testclient import TestClient

from serving.app import app


def test_app_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
