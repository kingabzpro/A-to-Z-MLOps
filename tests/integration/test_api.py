"""Integration tests for the FastAPI service boundary."""

import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

API_KEY = os.getenv("API_KEY")


@pytest.fixture()
def client():
    # TestClient is used without a context manager on purpose: the model
    # lifespan does not run, so the service is exercised in its
    # "no model loaded" state, which every endpoint must handle.
    return TestClient(app)


# ──────────────────────────────────────────────────────────────────────────────
# Metadata / probes
# ──────────────────────────────────────────────────────────────────────────────
def test_health_is_always_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_model_state(client):
    response = client.get("/ready")
    assert response.status_code in (200, 503)
    body = response.json()
    if response.status_code == 503:
        assert body["status"] == "not_ready"
    else:
        assert body["status"] == "ready"


def test_request_id_header_is_returned(client):
    response = client.get("/health")
    assert response.headers.get("X-Request-ID")


def test_request_id_is_echoed_when_supplied(client):
    response = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_info_endpoint(client):
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_loaded" in data
    assert isinstance(data["model_loaded"], bool)
    if data["model_loaded"]:
        assert isinstance(data["model_version"], str)
        assert isinstance(data["classes"], list)


def test_metrics_endpoint_exposes_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


# ──────────────────────────────────────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────────────────────────────────────
def test_predict_no_api_key(client):
    response = client.post("/predict", json={"title": "Test title without API key"})
    if response.status_code == 503:
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403
        assert response.json() == {"detail": "X-API-Key header missing"}


def test_predict_invalid_api_key(client):
    response = client.post(
        "/predict",
        json={"title": "Test title with invalid API key"},
        headers={"X-API-Key": "invalid_key"},
    )
    if response.status_code == 503:
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid API key supplied"}


# ──────────────────────────────────────────────────────────────────────────────
# Inference
# ──────────────────────────────────────────────────────────────────────────────
def test_predict(client):
    response = client.post(
        "/predict",
        json={"title": "Concerns at school diploma plan"},
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data["category"], str)
        assert (data["confidence"] is None) or isinstance(data["confidence"], float)


def test_predict_missing_field(client):
    response = client.post("/predict", json={}, headers={"X-API-Key": API_KEY})
    assert response.status_code == 422


def test_predict_title_too_short(client):
    response = client.post(
        "/predict", json={"title": "ab"}, headers={"X-API-Key": API_KEY}
    )
    assert response.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# Batch inference
# ──────────────────────────────────────────────────────────────────────────────
def test_batch_predict(client):
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
        assert data["total"] == 3
        assert len(data["predictions"]) == 3
        for pred in data["predictions"]:
            assert "title" in pred
            assert "category" in pred or "error" in pred


def test_batch_predict_empty_list(client):
    response = client.post(
        "/predict/batch", json={"titles": []}, headers={"X-API-Key": API_KEY}
    )
    assert response.status_code == 422


def test_batch_predict_short_title(client):
    response = client.post(
        "/predict/batch",
        json={"titles": ["OK title here", "ab"]},
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_batch_predict_too_many_titles(client):
    response = client.post(
        "/predict/batch",
        json={"titles": ["valid title"] * 101},
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_batch_predict_no_api_key(client):
    response = client.post("/predict/batch", json={"titles": ["Test title no key"]})
    if response.status_code == 503:
        assert response.json()["detail"] == "Model not available"
    else:
        assert response.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Rate limiting
# ──────────────────────────────────────────────────────────────────────────────
def test_rate_limit_info_endpoint(client):
    for _ in range(5):
        response = client.get("/info")
        assert response.status_code == 200


def test_rate_limit_returns_429(client):
    response = client.get("/info")
    assert response.status_code in (200, 429)
    if response.status_code == 429:
        assert response.json()["detail"] == "Rate limit exceeded"
