# 🔧 Configuration

## Environment Variables

The application uses environment variables for configuration. Create a `.env` file from the template:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `API_KEY` | API authentication key | `my_secure_key_123` |
| `KAGGLE_USERNAME` | Kaggle username for data download | `johndoe` |
| `KAGGLE_API_KEY` | Kaggle API key | `abc123xyz` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `MODEL_NAME` | MLflow model name | `news_classifier_logistic` |
| `MODEL_VERSION` | Model version to deploy | `1` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `3600` |
| `MLFLOW_TRACKING_URI` | MLflow server URI | `http://mlflow:5000` |
| `PREFECT_API_URL` | Prefect server URL | `http://prefect:4200/api` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Rate Limiting Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `RATE_LIMIT_DEFAULT` | Default rate limit | `100/minute` |
| `RATE_LIMIT_PREDICT` | `/predict` endpoint limit | `30/minute` |
| `RATE_LIMIT_BATCH` | `/predict/batch` endpoint limit | `10/minute` |

### Port Configuration

| Variable | Description | Default |
|----------|-------------|----------|
| `API_PORT` | FastAPI service port | `7860` |
| `PROMETHEUS_PORT` | Prometheus port | `9090` |
| `GRAFANA_PORT` | Grafana port | `3000` |
| `MLFLOW_PORT` | MLflow port | `5000` |
| `PREFECT_PORT` | Prefect port | `4200` |
| `LOCUST_PORT` | Locust port | `8089` |

> ⚠️ **Security Note**: Never commit your `.env` file to version control.

---

## Model Configuration

Model hyperparameters are configured in [`configs/model_params.yaml`](../configs/model_params.yaml):

```yaml
logistic:
  classifier__C: [0.1, 1.0, 10.0]
  classifier__penalty: ['l2']
  tfidf__ngram_range: [[1, 1], [1, 2]]
  tfidf__max_features: [5000, 10000]

svm:
  classifier__C: [0.1, 1.0, 10.0]
  classifier__penalty: ['l2']
  tfidf__ngram_range: [[1, 1], [1, 2]]

rf:
  classifier__n_estimators: [50, 100, 200]
  classifier__max_depth: [10, 20, None]
  tfidf__max_features: [5000, 10000]
```

### Supported Models

| Model | Description |
|-------|-------------|
| `logistic` | Logistic Regression with TF-IDF |
| `svm` | Support Vector Machine with TF-IDF |
| `rf` | Random Forest with TF-IDF |

---

## MLflow Configuration

MLflow settings in [`configs/mlflow_config.yaml`](../configs/mlflow_config.yaml):

```yaml
tracking_uri: http://mlflow:5000
experiment_name: news-classifier
artifact_location: ./mlruns
```

---

## Prometheus Configuration

Prometheus scrape targets in [`configs/prometheus.yml`](../configs/prometheus.yml):

```yaml
scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:7860']
    metrics_path: /metrics
```

---

## Grafana Configuration

Grafana dashboards and datasources are in `configs/grafana/`:

- `datasource.yml` - Prometheus datasource configuration
- `dashboard-provider.yml` - Dashboard provisioning
- `dashboard.json` - Pre-configured MLOps dashboard