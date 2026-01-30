# News Classification MLOps

> **Production-Ready MLOps Pipeline for News Classification**

An end-to-end MLOps pipeline demonstrating best practices in machine learning operations, from data ingestion to model deployment and monitoring.

## Overview

This project implements a complete MLOps pipeline for news classification using BBC articles from Kaggle. It showcases industry-standard practices for:

- **Data Pipeline**: Automated data ingestion, preprocessing, and validation
- **Model Training**: Experiment tracking, hyperparameter tuning, and model versioning
- **Model Serving**: RESTful API with authentication, rate limiting, and batch inference
- **Orchestration**: Workflow management with dependency resolution
- **Monitoring**: Real-time metrics, performance tracking, and alerting
- **Testing**: Unit tests, integration tests, and load testing
- **Deployment**: Container-based deployment with Docker and Kubernetes support

## Features

### Complete MLOps Pipeline
- Automated data processing and feature engineering
- Model training with hyperparameter optimization
- Experiment tracking and model registry
- CI/CD pipeline with automated testing

### Production-Ready API
- FastAPI-based REST service with async support
- **Batch prediction endpoint** for processing multiple titles efficiently
- API key authentication with configurable rate limiting (slowapi)
- Model versioning and A/B testing support
- Comprehensive API documentation with Swagger/OpenAPI

### Monitoring and Observability
- Real-time metrics collection with Prometheus
- Interactive dashboards with Grafana
- Model performance monitoring and drift detection
- System health and resource utilization tracking

### Workflow Orchestration
- Prefect-based workflow management
- Dependency resolution and error handling
- Scheduled and event-driven execution
- Flow visualization and debugging

### Comprehensive Testing
- Unit tests for all core components
- Integration tests for API endpoints
- Load testing with Locust
- Model validation and performance testing

### Container-Based Deployment
- Multi-stage Docker builds for optimization
- Docker Compose for local development
- Kubernetes manifests for production deployment
- Environment-specific configurations

### Security Best Practices
- Secure secret management
- API authentication and authorization
- Network policies and access control
- Container security scanning

## Architecture

```mermaid
graph TB
    subgraph "Data Layer"
        A[Kaggle Dataset] --> B[Data Processing]
        B --> C[Feature Engineering]
        C --> D[Data Validation]
    end

    subgraph "Model Layer"
        E[Model Training] --> F[Hyperparameter Tuning]
        F --> G[Model Evaluation]
        G --> H[Model Registry]
    end

    subgraph "API Layer"
        I[FastAPI Service] --> J[Model Inference]
        I --> J2[Batch Inference]
        I --> K[Authentication]
        I --> L[Rate Limiting]
    end

    subgraph "Monitoring Layer"
        M[Prometheus] --> N[Metrics Collection]
        N --> O[Grafana Dashboard]
        P[MLflow Tracking] --> Q[Experiment Tracking]
    end

    subgraph "Orchestration Layer"
        R[Prefect] --> S[Workflow Management]
        S --> T[Scheduled Jobs]
        S --> U[Error Handling]
    end

    D --> E
    H --> I
    I --> M
    I --> P
    E --> P
    R --> E
    R --> B

    style A fill:#e1f5fe
    style I fill:#f3e5f5
    style R fill:#e8f5e8
    style M fill:#fff3e0
```

## Prerequisites

### Required Software
- **Docker**: 20.10+ and **Docker Compose**: 2.0+
- **Python**: 3.10+ (for local development)
- **Git**: For version control

### Optional (for Kubernetes deployment)
- **Kubernetes**: 1.20+ cluster
- **kubectl**: Configured to access your cluster
- **Ingress Controller**: For external access (nginx/traefik)

### Required Accounts
- **Kaggle**: For dataset access
- **GitHub**: For CI/CD (if using GitHub Actions)
- **Container Registry**: Docker Hub, GHCR, or similar

---

## Wiki Navigation

- [Quick Start](Quick-Start) - Get up and running
- [Project Structure](Project-Structure) - Understand the codebase
- [API Reference](API-Reference) - Endpoint documentation
- [Configuration](Configuration) - Environment variables and settings
- [Monitoring](Monitoring) - Grafana, Prometheus, MLflow
- [Testing](Testing) - Test suite documentation
- [Cloud Deployment](Cloud-Deployment) - AWS, GKE, AKS guides
- [Development](Development) - Local development setup
- [Troubleshooting](Troubleshooting) - Common issues and solutions
