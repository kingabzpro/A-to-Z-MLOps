# 🤖 News Classification MLOps

[![Python 3.12+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MLOps](https://img.shields.io/badge/MLOps-Enabled-green.svg)](https://mlops.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Experimental-orange.svg)](https://kubernetes.io/)

A production-ready MLOps pipeline for news classification demonstrating end-to-end machine learning operations—from data ingestion to model deployment and monitoring.

## ✨ Key Features

- 🔄 **Complete Pipeline**: Automated data processing, training, and deployment with Prefect orchestration
- 🚀 **Production API**: FastAPI with single & batch prediction, auth, rate limiting, and caching
- 📊 **Full Observability**: Prometheus metrics, Grafana dashboards, and MLflow experiment tracking
- 🐳 **Container-Ready**: Docker Compose for local dev, Kubernetes manifests for production
- 🧪 **Comprehensive Testing**: Unit, integration, and load testing with Locust
- 🔐 **Security**: API key authentication and configurable rate limiting

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/kingabzpro/A-to-Z-MLOps.git
cd A-to-Z-MLOps
cp .env.example .env  # Configure your API_KEY and KAGGLE credentials

# Launch all services
docker-compose up -d
```

### Access Services

| Service | URL |
|---------|-----|
| 🚀 API & Docs | http://localhost:7860/docs |
| 📊 MLflow | http://localhost:5000 |
| 📈 Grafana | http://localhost:3000 |
| 🔍 Prometheus | http://localhost:9090 |
| ⚙️ Prefect | http://localhost:4200 |

### Test the API

```bash
# Single prediction
curl -X POST "http://localhost:7860/predict" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"title": "Apple releases new iPhone with AI features"}'

# Batch prediction (up to 100 titles)
curl -X POST "http://localhost:7860/predict/batch" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"titles": ["Tech startup raises funding", "Football team wins match"]}'
```

## 📚 Documentation

**For detailed documentation, visit our [Wiki](../../wiki):**

- [Quick Start Guide](../../wiki/Quick-Start) — Detailed setup instructions
- [Project Structure](../../wiki/Project-Structure) — Codebase organization
- [API Reference](../../wiki/API-Reference) — Endpoint documentation
- [Configuration](../../wiki/Configuration) — Environment variables and settings
- [Monitoring](../../wiki/Monitoring) — Grafana, Prometheus, MLflow setup
- [Testing](../../wiki/Testing) — Running tests and load testing
- [Cloud Deployment](../../wiki/Cloud-Deployment) — AWS, GKE, AKS guides
- [Development](../../wiki/Development) — Local dev setup and contributing
- [Troubleshooting](../../wiki/Troubleshooting) — Common issues and solutions

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](../../wiki/Development#git-workflow) and submit a PR.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest tests/ -v`)
4. Commit and push
5. Open a Pull Request

---

> 🌟 **Star this repo** if you find it helpful for your MLOps journey!
