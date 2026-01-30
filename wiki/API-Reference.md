# API Reference

## Endpoints Overview

| Endpoint | Method | Description | Rate Limit | Auth Required |
|----------|--------|-------------|------------|---------------|
| `/` | GET | Web UI for testing | 100/min | No |
| `/info` | GET | Model metadata and health | 100/min | No |
| `/predict` | POST | Single title prediction | 30/min | Yes |
| `/predict/batch` | POST | Batch prediction (up to 100 titles) | 10/min | Yes |
| `/metrics` | GET | Prometheus metrics | - | No |
| `/docs` | GET | Swagger API documentation | - | No |

---

## Authentication

Protected endpoints require an API key passed via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key" ...
```

---

## Single Prediction

**Endpoint:** `POST /predict`

**Request:**
```bash
curl -X POST "http://localhost:7860/predict" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"title": "Breaking tech news about AI breakthrough"}'
```

**Response:**
```json
{
  "category": "tech",
  "confidence": 0.89
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | News title (min 3 characters) |

**Response Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `category` | string | Predicted category (tech, sport, business, politics, entertainment) |
| `confidence` | float | Prediction confidence (0-1) |

---

## Batch Prediction

**Endpoint:** `POST /predict/batch`

Process up to 100 news titles in a single request.

**Request:**
```bash
curl -X POST "http://localhost:7860/predict/batch" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"titles": ["Tech startup raises funding", "Football team wins championship", "New policy announced"]}'
```

**Response:**
```json
{
  "predictions": [
    {"title": "Tech startup raises funding", "category": "tech", "confidence": 0.92, "error": null},
    {"title": "Football team wins championship", "category": "sport", "confidence": 0.95, "error": null},
    {"title": "New policy announced", "category": "politics", "confidence": 0.78, "error": null}
  ],
  "total": 3,
  "successful": 3,
  "failed": 0
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `titles` | array[string] | Yes | List of news titles (1-100 items, each min 3 chars) |

**Response Schema:**
| Field | Type | Description |
|-------|------|-------------|
| `predictions` | array | List of prediction results |
| `predictions[].title` | string | Original title |
| `predictions[].category` | string | Predicted category |
| `predictions[].confidence` | float | Prediction confidence |
| `predictions[].error` | string | Error message if prediction failed |
| `total` | int | Total number of titles submitted |
| `successful` | int | Number of successful predictions |
| `failed` | int | Number of failed predictions |

---

## Model Info

**Endpoint:** `GET /info`

**Request:**
```bash
curl "http://localhost:7860/info"
```

**Response:**
```json
{
  "model_name": "news_classifier_logistic",
  "model_version": "1",
  "status": "healthy",
  "categories": ["tech", "sport", "business", "politics", "entertainment"]
}
```

---

## Health Check

**Endpoint:** `GET /health`

**Request:**
```bash
curl "http://localhost:7860/health"
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Rate Limiting

When rate limit is exceeded, the API returns HTTP `429 Too Many Requests`:

```json
{
  "detail": "Rate limit exceeded",
  "retry_after": "60 seconds"
}
```

The response includes a `Retry-After` header indicating when to retry.

### Default Rate Limits

| Endpoint | Limit |
|----------|-------|
| Default | 10000/minute |
| `/predict` | 3000/minute |
| `/predict/batch` | 1000/minute |

Rate limits can be customized via environment variables:
- `RATE_LIMIT_DEFAULT`
- `RATE_LIMIT_PREDICT`
- `RATE_LIMIT_BATCH`

---

## Error Responses

### 401 Unauthorized
```json
{"detail": "Invalid or missing API key"}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 429 Rate Limited
```json
{"detail": "Rate limit exceeded", "retry_after": "60 seconds"}
```

### 503 Service Unavailable
```json
{"detail": "Model not available"}
```
