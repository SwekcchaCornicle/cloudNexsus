from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ingestion_rejects_wrong_content_type():
    response = client.post(
        "/api/v1/ingestion/jobs",
        files={"file": ("document.txt", b"not html", "text/plain")},
        data={
            "provider": "AWS",
            "service_name": "Lambda",
            "source_url": "https://docs.aws.amazon.com/lambda/",
        },
    )
    assert response.status_code == 415
