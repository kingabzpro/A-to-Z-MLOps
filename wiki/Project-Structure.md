# Project Structure

```
A-to-Z-MLOps/
├── src/                          # Source code
│   ├── data/                     # Data processing modules
│   │   ├── download.py              # Kaggle data download
│   │   ├── preprocessing.py         # Data cleaning and preprocessing
│   │   └── validation.py            # Data quality checks
│   ├── models/                   # Model training and evaluation
│   │   ├── train.py                 # Model training with MLflow tracking
│   │   ├── evaluate.py              # Model evaluation metrics
│   │   └── predict.py               # Model inference utilities
│   ├── api/                      # FastAPI application
│   │   ├── main.py                  # FastAPI app and endpoints
│   │   ├── auth.py                  # Authentication middleware
│   │   ├── middleware.py            # Custom middleware
│   │   └── monitoring.py            # Prometheus metrics
│   └── pipelines/                # Prefect workflows
│       ├── pipeline.py              # Main MLOps pipeline
│       ├── flows.py                 # Individual workflow components
│       └── tasks.py                 # Workflow task definitions
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── stress/                   # Load testing scripts
│   └── conftest.py                  # Pytest configuration
├── configs/                      # Configuration files
│   ├── mlflow_config.yaml           # MLflow settings
│   ├── model_params.yaml            # Model hyperparameters
│   ├── grafana/                     # Grafana dashboards and datasources
│   └── prometheus.yml               # Prometheus configuration
├── k8s/                          # Kubernetes manifests (Experimental)
│   ├── 00-namespace.yml             # Namespace definition
│   ├── 02-configmap.yml             # Configuration maps
│   ├── 03-prometheus-deployment.yml # Prometheus deployment
│   ├── 04-grafana-deployment.yml    # Grafana deployment
│   ├── 05-mlflow-deployment.yml     # MLflow deployment
│   ├── 06-prefect-deployment.yml    # Prefect deployment
│   ├── 07-api-deployment.yml        # API deployment
│   ├── 08-locust-deployment.yml     # Locust deployment
│   └── DEPLOYMENT-GUIDE.md          # Detailed K8s guide
├── workflows/                    # CI/CD workflows
│   └── ci-cd.yml                    # GitHub Actions workflow
├── notebooks/                    # Jupyter notebooks
│   ├── 01-exploratory-data-analysis.ipynb
│   ├── 02-model-experimentation.ipynb
│   └── 03-performance-evaluation.ipynb
├── data/                         # Data directory
│   ├── raw/                         # Raw downloaded data
│   ├── processed/                   # Processed training data
│   └── validation/                  # Validation datasets
├── models/                       # Trained models storage
├── images/                       # Documentation images
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local development setup
├── pyproject.toml                # Python project configuration
├── .env.example                  # Environment variables template
└── README.md                     # Project overview
```

## Key Directories

### `src/` - Source Code
The main application code, organized by functionality:
- **data/**: Data ingestion, preprocessing, and validation
- **models/**: Training, evaluation, and inference logic
- **api/**: FastAPI application with endpoints and middleware
- **pipelines/**: Prefect workflow definitions

### `tests/` - Test Suite
Comprehensive testing organized by type:
- **unit/**: Fast, isolated tests for individual functions
- **integration/**: Tests for API and service interactions
- **stress/**: Load testing with Locust

### `configs/` - Configuration
All configuration files in one place:
- MLflow tracking settings
- Model hyperparameters
- Grafana dashboards and datasources
- Prometheus scrape configurations

### `k8s/` - Kubernetes Manifests
Production deployment configurations (experimental):
- Namespace and ConfigMaps
- Service deployments
- Detailed deployment guide
