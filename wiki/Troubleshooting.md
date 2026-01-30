# 🔧 Troubleshooting

## Docker Issues

### Check Docker Status
```bash
# Verify Docker is running
docker info

# Check container status
docker-compose ps

# View container logs
docker-compose logs <service-name>
docker-compose logs api
docker-compose logs mlflow
```

### Common Docker Fixes
```bash
# Restart services
docker-compose restart

# Rebuild containers
docker-compose up -d --build

# Clean up unused resources
docker system prune -a

# Full reset (removes data)
docker-compose down -v
docker-compose up -d
```

### Port Conflicts

If ports are already in use:
```bash
# Find process using port
lsof -i :7860  # macOS/Linux
netstat -ano | findstr :7860  # Windows

# Or change ports in .env
API_PORT=8080
```

---

## API Issues

### Test API Connectivity
```bash
# Health check
curl -X GET "http://localhost:7860/health"

# Model info
curl -X GET "http://localhost:7860/info"
```

### Test Predictions
```bash
# Single prediction
curl -X POST "http://localhost:7860/predict" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"title": "Breaking tech news about AI"}'

# Batch prediction
curl -X POST "http://localhost:7860/predict/batch" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"titles": ["Tech news", "Sports update"]}'
```

### Common API Errors

| Status | Error | Solution |
|--------|-------|----------|
| 401 | Invalid API key | Check `X-API-Key` header matches `API_KEY` env var |
| 422 | Validation error | Ensure title is at least 3 characters |
| 429 | Rate limited | Wait for `Retry-After` duration |
| 503 | Model not available | Check if model is loaded; restart API service |

---

## MLflow Issues

### Check MLflow Status
```bash
# Health check
curl http://localhost:5000/health

# List experiments
curl "http://localhost:5000/api/2.0/mlflow/experiments/list"

# Check specific experiment
curl "http://localhost:5000/api/2.0/mlflow/experiments/get-by-name?experiment_name=news-classifier"
```

### MLflow Container Logs
```bash
docker-compose logs mlflow
```

### Model Not Found

1. Check MLflow UI at http://localhost:5000
2. Verify experiment exists
3. Ensure model is registered in Model Registry
4. Check `MODEL_NAME` and `MODEL_VERSION` env vars

---

## Kubernetes Issues

### Check Pod Status
```bash
# List all pods
kubectl get pods -n mlops

# Describe problematic pod
kubectl describe pod <pod-name> -n mlops

# View pod logs
kubectl logs <pod-name> -n mlops -f

# View previous container logs (after crash)
kubectl logs <pod-name> -n mlops --previous
```

### Check Service Connectivity
```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  sh -c "nslookup api.mlops"

# Test service endpoint
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://api.mlops:7860/health
```

### Common K8s Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Pod CrashLoopBackOff | Check logs, describe pod | Fix config, increase resources |
| ImagePullBackOff | Wrong image name/tag, no registry auth | Fix image reference, add imagePullSecrets |
| Pending pods | No available nodes, resource constraints | Scale cluster, reduce resource requests |
| Service not reachable | Wrong selector, network policy | Check labels match, verify network policies |

---

## Debug Mode

### Enable Debug Logging

Set environment variable:
```env
LOG_LEVEL=DEBUG
```

Or temporarily for Docker Compose:
```bash
docker-compose run --rm -e LOG_LEVEL=DEBUG api python -m src.api.main
```

### Interactive Debugging

```bash
# Shell into running container
docker exec -it a-mlops-api-1 /bin/bash

# Check environment
env | grep -E "API|MODEL|MLFLOW"

# Test Python imports
python -c "from src.models.train import train_model; print('OK')"
```

---

## Performance Issues

### High Latency

1. Check Grafana dashboards for bottlenecks
2. Review Prometheus metrics for slow endpoints
3. Consider:
   - Increasing cache TTL
   - Adding more API replicas
   - Optimizing model inference

### Memory Issues

```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## Getting Help

1. **Check logs** - Most issues are revealed in container/pod logs
2. **Search issues** - Look for similar issues on GitHub
3. **Create an issue** - Include:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Docker version)
   - Relevant logs