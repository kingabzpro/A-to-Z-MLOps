# Quick Start

## Docker Compose (Recommended)

The fastest way to get started is using Docker Compose, which spins up all services with pre-configured monitoring and orchestration.

### 1. Clone the Repository
```bash
git clone https://github.com/kingabzpro/A-to-Z-MLOps.git
cd A-to-Z-MLOps
```

### 2. Environment Setup
```bash
# Copy the environment template
cp .env.example .env

# Edit the environment file with your settings
nano .env
```

Required environment variables:
```env
# API Configuration
API_KEY=your_secure_api_key_here
CACHE_TTL=3600

# Kaggle Configuration
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_API_KEY=your_kaggle_api_key

# Model Configuration
MODEL_NAME=news_classifier_logistic
MODEL_VERSION=1

# Rate Limiting (optional)
RATE_LIMIT_DEFAULT=10000/minute
RATE_LIMIT_PREDICT=3000/minute
RATE_LIMIT_BATCH=1000/minute

# Optional: Custom Ports
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
MLFLOW_PORT=5000
PREFECT_PORT=4200
API_PORT=7860
LOCUST_PORT=8089
```

> **Security Note**: Never commit your `.env` file to version control. Add it to `.gitignore`.

### 3. Launch Services
```bash
# Start all services in detached mode
docker-compose up -d

# Verify all services are running
docker-compose ps

# View logs for all services
docker-compose logs -f
```

### 4. Access Services
Once running, access the services at:

| Service | URL | Description |
|---------|-----|-------------|
| FastAPI App | [http://localhost:7860](http://localhost:7860) | API Documentation at `/docs` |
| MLflow | [http://localhost:5000](http://localhost:5000) | Model tracking and registry |
| Grafana | [http://localhost:3000](http://localhost:3000) | Monitoring dashboards (admin/admin) |
| Prometheus | [http://localhost:9090](http://localhost:9090) | Metrics collection |
| Prefect | [http://localhost:4200](http://localhost:4200) | Workflow orchestration |
| Locust | [http://localhost:8089](http://localhost:8089) | Load testing interface |

### 5. Run the Pipeline
```bash
# Trigger the MLOps pipeline via API
curl -X POST "http://localhost:7860/run-pipeline" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json"

# Or trigger via Prefect UI
# Navigate to http://localhost:4200 and run the "mlops_pipeline" flow
```

### 6. Stop Services
```bash
# Stop and remove all containers
docker-compose down

# Stop and remove volumes (data will be lost)
docker-compose down -v
```

---

## Kubernetes (Experimental)

> **Note**: Kubernetes deployment is currently experimental and intended for advanced users. Production deployment requires additional configuration for persistence, security, and networking.

### Prerequisites for K8s
- Working Kubernetes cluster (local: minikube, kind; cloud: EKS, GKE, AKS)
- `kubectl` configured and cluster access
- Container registry access for image pushing

### Quick K8s Deployment

#### 1. Create Namespace and Secrets
```bash
# Create the namespace
kubectl apply -f k8s/00-namespace.yml

# Create secrets from environment file
cat << EOF > .kube-secrets
API_KEY=your_api_key
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_API_KEY=your_kaggle_api_key
GF_SECURITY_ADMIN_PASSWORD=your_grafana_password
EOF

kubectl create secret generic mlops-secrets --from-env-file=.kube-secrets -n mlops
```

#### 2. Deploy Infrastructure
```bash
# Deploy core services
kubectl apply -f k8s/02-configmap.yml
kubectl apply -f k8s/03-prometheus-deployment.yml
kubectl apply -f k8s/04-grafana-deployment.yml
kubectl apply -f k8s/05-mlflow-deployment.yml
kubectl apply -f k8s/06-prefect-deployment.yml

# Deploy application
kubectl apply -f k8s/07-api-deployment.yml

# Optional: Load testing
kubectl apply -f k8s/08-locust-deployment.yml
```

#### 3. Access Services
```bash
# Use port forwarding for local access
kubectl port-forward svc/api 7860:7860 -n mlops &
kubectl port-forward svc/mlflow 5000:5000 -n mlops &
kubectl port-forward svc/grafana 3000:3000 -n mlops &
kubectl port-forward svc/prometheus 9090:9090 -n mlops &
kubectl port-forward svc/prefect 4200:4200 -n mlops &
```

For detailed Kubernetes instructions, see [k8s/DEPLOYMENT-GUIDE.md](../k8s/DEPLOYMENT-GUIDE.md).
