# Monitoring and Observability

## Overview

The project includes a complete observability stack:

| Tool | Purpose | URL |
|------|---------|-----|
| **Prometheus** | Metrics collection | http://localhost:9090 |
| **Alertmanager** | Alert routing | http://localhost:9093 |
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

### Serving-State Metrics

```python
# 1 when a model is loaded, 0 otherwise (drives the ApiModelNotLoaded alert)
model_loaded
model_info{model_name, model_version}
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
- **Aliases** (the `champion` alias marks the version the API serves)
- Model metadata and descriptions
- Model lineage

> **Note:** MLflow *stages* (`Staging`/`Production`) are deprecated and removed
> in MLflow 3. This project uses the `champion` alias instead. The alias is only
> moved by the promotion gate in `src/models/promote.py`, which compares each
> new version against the incumbent on the held-out test split.

### Accessing MLflow

1. Navigate to http://localhost:5000
2. Select the `news-classifier` experiment
3. Compare runs and metrics
4. Register best models to the registry

---

## Alerts

Alerting rules live in `configs/alert_rules.yml` and are loaded by Prometheus
via `rule_files`. Alerts are routed through Alertmanager
(`configs/alertmanager.yml`).

### Configured Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| `ApiDown` | `up{job="api"} == 0` for 2m | critical |
| `ApiModelNotLoaded` | `model_loaded == 0` for 2m | critical |
| `ApiHighErrorRate` | 5xx ratio > 5% for 5m | critical |
| `ApiHighLatencyP95` | p95 latency > 1s for 5m | warning |
| `ApiRateLimitSustained` | sustained 429s for 10m | warning |
| `ApiLowConfidencePredictions` | median confidence < 0.5 for 15m | warning |

### Routing Alerts

The default Alertmanager receiver has no integration, so alerts appear in the
Alertmanager UI only. To send them somewhere real, add a
`slack_configs`/`pagerduty_configs`/`webhook_configs` block to the `default`
receiver in `configs/alertmanager.yml` (and the `alertmanager-config`
ConfigMap in `k8s/09-alertmanager-deployment.yml`).

### Grafana Alerts

1. Open a dashboard panel
2. Click "Alert" tab
3. Configure conditions and notifications
4. Set up notification channels (email, Slack, etc.)
