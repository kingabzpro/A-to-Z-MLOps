# Monitoring and Observability

## Overview

The project includes a complete observability stack:

| Tool | Purpose | URL |
|------|---------|-----|
| **Prometheus** | Metrics collection | http://localhost:9090 |
| **Grafana** | Dashboards and visualization | http://localhost:3000 |
| **MLflow** | Experiment tracking | http://localhost:5000 |

---

## Grafana Dashboards

The project includes pre-configured Grafana dashboards for:

### System Overview
- CPU, memory, and disk usage
- Container resource utilization
- Network traffic

### API Performance
- Request rates and throughput
- Response times (p50, p95, p99)
- Error rates by endpoint
- Rate limiting metrics

### Model Metrics
- Predictions per category
- Confidence score distribution
- Cache hit/miss ratios
- Batch vs single prediction volume

### Default Credentials
- **Username**: `admin`
- **Password**: `admin`

---

## Prometheus Metrics

### API Metrics

```python
# Request metrics
http_requests_total{endpoint, method, status}
http_request_duration_seconds{endpoint, method}
```

### Prediction Metrics

```python
# Prediction tracking
news_predictions_total{category}
news_prediction_confidence{category}

# Cache metrics
prediction_cache_hits_total{category}
prediction_cache_misses_total{category}
```

### Rate Limiting Metrics

```python
rate_limit_exceeded_total{endpoint, client_type}
```

### System Metrics

```python
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_network_receive_bytes_total
```

### Example Queries

**Request rate by endpoint:**
```promql
rate(http_requests_total[5m])
```

**95th percentile latency:**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Predictions by category:**
```promql
increase(news_predictions_total[1h])
```

**Cache hit ratio:**
```promql
sum(prediction_cache_hits_total) / (sum(prediction_cache_hits_total) + sum(prediction_cache_misses_total))
```

---

## MLflow Experiment Tracking

MLflow tracks all training experiments:

### Tracked Parameters
- Model type (logistic, svm, rf)
- Hyperparameters (C, penalty, n_estimators, etc.)
- TF-IDF settings (ngram_range, max_features)

### Tracked Metrics
- Accuracy
- Precision (macro/micro)
- Recall (macro/micro)
- F1 Score
- Log Loss
- ROC AUC

### Tracked Artifacts
- Trained model files
- Confusion matrix plots
- ROC curves
- Classification reports

### Model Registry

MLflow Model Registry manages:
- Model versions
- Stage transitions (Staging to Production)
- Model metadata and descriptions
- Model lineage

### Accessing MLflow

1. Navigate to http://localhost:5000
2. Select the `news-classifier` experiment
3. Compare runs and metrics
4. Register best models to the registry

---

## Setting Up Alerts

### Prometheus Alerting Rules

Example alert for high error rate:

```yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

### Grafana Alerts

1. Open a dashboard panel
2. Click "Alert" tab
3. Configure conditions and notifications
4. Set up notification channels (email, Slack, etc.)
