# k8s Deployment Guide

This guide provides instructions for deploying the A-to-Z MLOps project to k8s while keeping sensitive API keys secure.

## Prerequisites

- k8s cluster (1.20+)
- `kubectl` configured to access your cluster
- Docker images pushed to a registry (ghcr.io recommended)

## Important Security Notes

⚠️ **NEVER commit secrets with real values to version control**

This deployment uses k8s Secrets to safely store sensitive data like API keys and credentials. Secrets are NOT stored in the YAML files with real values.

## Deployment Steps

### Step 1: Create the Namespace

```bash
kubectl apply -f k8s/00-namespace.yml
```

### Step 2: Create Secrets Securely

**Using .kube-secrets file (Recommended)**

Configure your secrets in the `.kube-secrets` file with your actual values:

```bash
API_KEY=YOUR_API_KEY
KAGGLE_USERNAME=YOUR_KAGGLE_USERNAME
KAGGLE_API_KEY=YOUR_KAGGLE_API_KEY
GF_SECURITY_ADMIN_PASSWORD=YOUR_GRAFANA_PASSWORD
MLFLOW_TRACKING_URI=http://mlflow:5000
PREFECT_API_URL=http://prefect:4200/api
```

Then create the secret:

```bash
kubectl create secret generic mlops-secrets --from-env-file=.kube-secrets -n mlops
```

⚠️ **Important**: Never commit `.kube-secrets` with real credentials to version control.

### Step 3: Deploy ConfigMap

```bash
kubectl apply -f k8s/02-configmap.yml
```

### Step 4: Deploy Services

Deploy in order (services have dependencies):

```bash
# Core infrastructure services
kubectl apply -f k8s/03-prometheus-deployment.yml
kubectl apply -f k8s/04-grafana-deployment.yml
kubectl apply -f k8s/05-mlflow-deployment.yml
kubectl apply -f k8s/06-prefect-deployment.yml

# Application
kubectl apply -f k8s/07-api-deployment.yml

# Load testing (optional)
kubectl apply -f k8s/08-locust-deployment.yml
```

Or deploy all at once:

```bash
kubectl apply -f k8s/ -n mlops
```

### Step 5: Verify Deployment

Check pod status:

```bash
kubectl get pods -n mlops
```

Watch deployment progress:

```bash
kubectl rollout status deployment/api -n mlops
```

View logs:

```bash
kubectl logs deployment/api -n mlops -f
```

## Accessing Services

### Port Forwarding (Local Development)

```bash
# API
kubectl port-forward svc/api 7860:7860 -n mlops

# MLflow
kubectl port-forward svc/mlflow 5000:5000 -n mlops

# Grafana
kubectl port-forward svc/grafana 3000:3000 -n mlops

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mlops

# Prefect
kubectl port-forward svc/prefect 4200:4200 -n mlops

# Locust
kubectl port-forward svc/locust 8089:8089 -n mlops
```

### Ingress Setup (Production)

For production deployments, use an Ingress controller. Example:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mlops-ingress
  namespace: mlops
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 7860
```

## Managing Secrets

### View secret (metadata only)

```bash
kubectl get secret mlops-secrets -n mlops
```

### Update a secret value

```bash
kubectl patch secret mlops-secrets -n mlops -p \
  '{"data":{"api-key":"'$(echo -n NEW_VALUE | base64)'"}}'
```

### Delete and recreate secret

Update your `.kube-secrets` file with new values, then:

```bash
kubectl delete secret mlops-secrets -n mlops
kubectl create secret generic mlops-secrets --from-env-file=.kube-secrets -n mlops
```

## Storage Notes

Currently, the deployment uses `emptyDir` volumes for persistence. For production:

1. **Persistent Volumes (PV)**: Use `PersistentVolumeClaim` for data persistence
2. **External Storage**: Consider using:
   - Cloud storage (S3, GCS, Azure Blob)
   - Network File System (NFS)
   - Database backends (PostgreSQL for MLflow metadata)

Example modification for PV:

```yaml
volumeClaimTemplates:
- metadata:
    name: storage
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "standard"
    resources:
      requests:
        storage: 50Gi
```

## Scaling Considerations

- **API**: Increase replicas in `07-api-deployment.yml`
- **MLflow**: Consider separate database backend for scalability
- **Prefect**: Use managed Prefect Cloud for production workloads
- **Grafana**: Use managed solutions or external storage

## Cleanup

To remove all deployments:

```bash
kubectl delete namespace mlops
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n mlops

# Check logs
kubectl logs <pod-name> -n mlops
```

### Secret not found

```bash
# Verify secret exists
kubectl get secret mlops-secrets -n mlops

# Verify secret contents (view keys only)
kubectl get secret mlops-secrets -n mlops -o jsonpath='{.data}' | jq 'keys'
```

### Service connectivity

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  sh -c "nslookup mlflow.mlops"

# Test service connection
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://api:7860/info
```

## Best Practices

1. **Secrets Management**:
   - Use HashiCorp Vault or sealed-secrets for production
   - Rotate credentials regularly
   - Use RBAC to limit access

2. **Image Security**:
   - Use specific image tags (not `latest`)
   - Scan images for vulnerabilities
   - Use private registries

3. **Monitoring**:
   - Enable audit logging
   - Monitor resource usage
   - Set up alerts for pod failures

4. **High Availability**:
   - Use multiple replicas
   - Implement Pod Disruption Budgets
   - Use StatefulSets for stateful workloads

5. **Networking**:
   - Use Network Policies to restrict traffic
   - Enable TLS/SSL termination
   - Use service mesh (Istio/Linkerd) for advanced traffic management
