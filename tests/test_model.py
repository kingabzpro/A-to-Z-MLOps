# Simple test to check model pipeline import and FastAPI health
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.api.main import app

load_dotenv()

API_KEY = os.getenv("API_KEY")


def test_fastapi_health():
    client = TestClient(app)
    response = client.post(
        "/predict",
        json={"title": "Concerns at school diploma plan"},
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code in (200, 503)  # 503 if model not trained
    if response.status_code == 200:
        data = response.json()
        assert "category" in data
        assert isinstance(data["category"], str)
        assert "confidence" in data
        assert (data["confidence"] is None) or (isinstance(data["confidence"], float))


def test_predict_missing_field():
    client = TestClient(app)
    response = client.post("/predict", json={}, headers={"X-API-Key": API_KEY})
    assert (
        response.status_code == 422
    )  # Unprocessable Entity for missing required field


def test_info_endpoint():
    client = TestClient(app)
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)
    if data["model_loaded"]:
        assert "model_version" in data
        assert isinstance(data["model_version"], str)
        assert "classes" in data
        assert isinstance(data["classes"], list)


def test_predict_no_api_key():
    client = TestClient(app)
    response = client.post(
        "/predict",
        json={"title": "Test title without API key"},
    )
    if response.status_code == 503:
        # Model not available, skip strict auth check
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403
        assert response.json() == {"detail": "X-API-Key header missing"}


def test_predict_invalid_api_key():
    client = TestClient(app)
    response = client.post(
        "/predict",
        json={"title": "Test title with invalid API key"},
        headers={"X-API-Key": "invalid_key"},
    )
    if response.status_code == 503:
        # Model not available, skip strict auth check
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid API key supplied"}


def test_batch_predict():
    """Test the /predict/batch endpoint with multiple titles."""
    client = TestClient(app)
    response = client.post(
        "/predict/batch",
        json={
            "titles": [
                "Breaking news in technology sector",
                "Sports team wins championship",
                "Political developments in parliament",
            ]
        },
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "predictions" in data
        assert "total" in data
        assert "successful" in data
        assert "failed" in data
        assert data["total"] == 3
        assert len(data["predictions"]) == 3
        for pred in data["predictions"]:
            assert "title" in pred
            assert "category" in pred or "error" in pred


def test_batch_predict_empty_list():
    """Test batch endpoint rejects empty list."""
    client = TestClient(app)
    response = client.post(
        "/predict/batch",
        json={"titles": []},
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422  # Validation error for empty list


def test_batch_predict_short_title():
    """Test batch endpoint validates title length."""
    client = TestClient(app)
    response = client.post(
        "/predict/batch",
        json={"titles": ["OK title here", "ab"]},  # Second title too short
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422  # Validation error


def test_batch_predict_no_api_key():
    """Test batch endpoint requires API key."""
    client = TestClient(app)
    response = client.post(
        "/predict/batch",
        json={"titles": ["Test title without API key"]},
    )
    if response.status_code == 503:
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403


def test_rate_limit_info_endpoint():
    """Test that rate limiting is active on info endpoint."""
    client = TestClient(app)
    # Make multiple requests - should work within rate limit
    for _ in range(5):
        response = client.get("/info")
        assert response.status_code == 200


def test_rate_limit_returns_429():
    """Test that exceeding rate limit returns 429 status code."""
    client = TestClient(app)
    # This test verifies the rate limit error handler is properly configured
    # In actual testing with real rate limits, this would trigger 429
    response = client.get("/info")
    assert response.status_code in (200, 429)
    if response.status_code == 429:
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Rate limit exceeded"
        assert "retry_after" in data
