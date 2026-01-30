# 📰 News Classification MLOps

Production-ready MLOps pipeline for classifying news articles. Built with FastAPI, Docker, Kubernetes, and modern observability tools.

## What This Is

An end-to-end machine learning pipeline that ingests news data, trains classification models, and serves predictions through a REST API with full monitoring and orchestration.

[🚀 Quick Start](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Quick-Start) | [📚 Documentation](https://github.com/kingabzpro/A-to-Z-MLOps/wiki) | [📡 API Reference](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/API-Reference)

## ✨ Key Capabilities

- **🔄 Automated Pipeline** - Data processing, model training, and deployment orchestrated with Prefect
- **⚡ Production API** - FastAPI with batch prediction, authentication, rate limiting, and caching
- **📊 Full Observability** - Prometheus metrics, Grafana dashboards, MLflow experiment tracking
- **🐳 Container-Ready** - Docker Compose for local development, Kubernetes for production
- **🧪 Comprehensive Testing** - Unit, integration, and load testing with Locust

## 🚀 Quick Start

```bash
git clone https://github.com/kingabzpro/A-to-Z-MLOps.git
cd A-to-Z-MLOps
cp .env.example .env  # Add your API_KEY and Kaggle credentials
docker-compose up -d
```

Access the services:
- **🔥 API & Docs**: http://localhost:7860/docs
- **📈 MLflow Tracking**: http://localhost:5000
- **📉 Grafana Dashboards**: http://localhost:3000
- **🔍 Prometheus Metrics**: http://localhost:9090
- **⚙️ Prefect Orchestration**: http://localhost:4200

Test the API:
```bash
curl -X POST "http://localhost:7860/predict" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"title": "Apple releases new iPhone with AI features"}'
```

## 📚 Documentation

Detailed guides available in the [Wiki](https://github.com/kingabzpro/A-to-Z-MLOps/wiki):

- 🚀 [Quick Start](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Quick-Start) - Complete setup instructions
- 📁 [Project Structure](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Project-Structure) - Codebase organization
- 📡 [API Reference](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/API-Reference) - All endpoints documented
- ⚙️ [Configuration](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Configuration) - Environment variables
- 📊 [Monitoring](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Monitoring) - Observability setup
- ☁️ [Cloud Deployment](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Cloud-Deployment) - AWS, GKE, AKS guides
- 🛠️ [Development](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Development) - Contributing guidelines

## 🤝 Contributing

See the [Development Guide](https://github.com/kingabzpro/A-to-Z-MLOps/wiki/Development) for contribution workflow and coding standards.

---

MIT License - Created for the MLOps community
