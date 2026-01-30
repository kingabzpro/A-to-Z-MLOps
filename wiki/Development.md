# Development

## Local Development Setup

### 1. Install Dependencies

```bash
# Install uv for fast package management
pip install uv

# Install project dependencies
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

### 3. Run Services Locally

```bash
# Start supporting services (database, MLflow, etc.)
docker-compose up -d mlflow prometheus grafana

# Run API locally for development
python -m src.api.main
```

---

## Code Quality

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Formatting

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/
```

### Linting

```bash
# Run flake8
flake8 src/ tests/

# Run pylint (optional)
pylint src/
```

### Type Checking

```bash
# Run mypy
mypy src/
```

---

## Adding New Models

### 1. Update Model Configuration

Edit `configs/model_params.yaml`:

```yaml
new_model:
  param1: [value1, value2]
  param2: [value3, value4]
```

### 2. Modify Training Script

Update `src/models/train.py` to support the new model type.

### 3. Add Tests

Create tests in `tests/unit/test_models.py`:

```python
def test_new_model_training():
    model = train_model(model_type="new_model")
    assert model is not None
    assert hasattr(model, "predict")
```

### 4. Update Documentation

Document the new model in this wiki and update API docs if needed.

---

## Extending API Endpoints

### 1. Add New Endpoint

Edit `src/api/main.py`:

```python
@app.post("/new-endpoint", tags=["Feature"])
async def new_endpoint(request: NewRequest) -> NewResponse:
    # Implementation
    pass
```

### 2. Add Pydantic Models

```python
class NewRequest(BaseModel):
    field: str = Field(..., description="Field description")

class NewResponse(BaseModel):
    result: str
```

### 3. Add Authentication (if needed)

```python
@app.post(
    "/new-endpoint",
    dependencies=[Depends(get_api_key)],
)
async def new_endpoint(...):
    pass
```

### 4. Add Metrics

```python
from prometheus_client import Counter

new_endpoint_counter = Counter(
    'new_endpoint_requests_total',
    'Total new endpoint requests'
)

@app.post("/new-endpoint")
async def new_endpoint(...):
    new_endpoint_counter.inc()
    # ...
```

### 5. Write Tests

```python
def test_new_endpoint(client, api_headers):
    response = client.post(
        "/new-endpoint",
        json={"field": "value"},
        headers=api_headers
    )
    assert response.status_code == 200
```

---

## Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Use imperative, present-tense:

```
Add batch prediction endpoint
Fix rate limiting bug
Update API documentation
Refactor model training logic
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and add tests
3. Run linting and tests locally
4. Push and create PR
5. Wait for CI checks to pass
6. Request review
7. Merge after approval
