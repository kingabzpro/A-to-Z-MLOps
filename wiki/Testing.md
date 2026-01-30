# 🧪 Testing

## Running Tests

### All Tests
```bash
# Run unit and integration tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Single test file
pytest tests/test_model.py -v
```

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Fast, isolated tests for individual functions:

- Model training and evaluation
- Data processing functions
- API endpoint logic
- Utility functions

**Example:**
```python
def test_preprocess_text():
    text = "  Hello WORLD!  "
    result = preprocess_text(text)
    assert result == "hello world"
```

### 2. Integration Tests (`tests/integration/`)

Tests for component interactions:

- API endpoint testing with TestClient
- Database operations
- External service integration
- End-to-end workflows

**Example:**
```python
def test_predict_endpoint(client):
    response = client.post(
        "/predict",
        json={"title": "Tech news about AI"},
        headers={"X-API-Key": "test_key"}
    )
    assert response.status_code == 200
    assert "category" in response.json()
```

### 3. Load Tests (`tests/stress_test.py`)

Performance testing with Locust:

- API throughput testing
- Concurrent request handling
- Batch endpoint performance
- Rate limiting behavior
- Resource utilization

---

## Load Testing with Locust

### Starting Locust

```bash
# Web UI mode
locust -f tests/stress_test.py --host=http://localhost:7860

# Headless mode
locust -f tests/stress_test.py --host=http://localhost:7860 \
  --headless -u 100 -r 10 --run-time 60s
```

### Locust Web UI

Access at http://localhost:8089 to:

1. Set number of users and spawn rate
2. Start/stop tests
3. View real-time statistics
4. Download reports

### Test Scenarios

The stress test includes:

| Task | Weight | Description |
|------|--------|-------------|
| `get_info` | 2 | Health check |
| `single_predict` | 5 | Single prediction |
| `batch_predict` | 3 | Batch prediction (10 titles) |

---

## Coverage Reports

### Generate HTML Report
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Generate XML Report (CI/CD)
```bash
pytest tests/ --cov=src --cov-report=xml
```

### Coverage Thresholds

Enforce minimum coverage:
```bash
pytest tests/ --cov=src --cov-fail-under=80
```

---

## Testing Best Practices

### Fixtures

Use `conftest.py` for shared fixtures:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def api_headers():
    return {"X-API-Key": "test_api_key"}
```

### Mocking External Services

```python
from unittest.mock import patch

@patch('src.models.train.mlflow')
def test_training_logs_to_mlflow(mock_mlflow):
    train_model()
    mock_mlflow.log_metric.assert_called()
```

### Testing Async Endpoints

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_predict():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/predict", json={"title": "test"})
    assert response.status_code == 200
```