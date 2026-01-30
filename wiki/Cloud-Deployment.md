# Cloud Deployment

## AWS EKS Deployment

### 1. Create EKS Cluster

```bash
# Install eksctl if needed
brew install eksctl  # macOS

# Create cluster
eksctl create cluster \
  --name mlops-cluster \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.medium
```

### 2. Configure Container Registry (ECR)

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Create repository
aws ecr create-repository --repository-name a-to-z-mlops

# Build and push image
docker build -t <account-id>.dkr.ecr.us-west-2.amazonaws.com/a-to-z-mlops:latest .
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/a-to-z-mlops:latest
```

### 3. Deploy Services

```bash
# Create namespace and secrets
kubectl apply -f k8s/00-namespace.yml
kubectl create secret generic mlops-secrets \
  --from-env-file=.kube-secrets -n mlops

# Deploy with AWS-specific storage
kubectl apply -f k8s/aws-storage-class.yml  # If available
kubectl apply -f k8s/
```

### 4. Configure Load Balancer

```bash
# Install AWS Load Balancer Controller
helm install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=mlops-cluster
```

---

## Google GKE Deployment

### 1. Create GKE Cluster

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create cluster
gcloud container clusters create mlops-cluster \
  --num-nodes=3 \
  --machine-type=e2-medium \
  --zone=us-central1-a

# Get credentials
gcloud container clusters get-credentials mlops-cluster \
  --zone=us-central1-a
```

### 2. Configure Container Registry (GCR)

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/YOUR_PROJECT_ID/a-to-z-mlops:latest .
docker push gcr.io/YOUR_PROJECT_ID/a-to-z-mlops:latest
```

### 3. Deploy Services

```bash
# Update image references in k8s manifests to use GCR
# Then deploy
kubectl apply -f k8s/
```

### 4. Configure Ingress

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

---

## Azure AKS Deployment

### 1. Create AKS Cluster

```bash
# Create resource group
az group create --name mlops-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group mlops-rg \
  --name mlops-cluster \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group mlops-rg --name mlops-cluster
```

### 2. Configure Container Registry (ACR)

```bash
# Create ACR
az acr create --resource-group mlops-rg --name mlopscr --sku Basic

# Login to ACR
az acr login --name mlopscr

# Build and push
docker build -t mlopscr.azurecr.io/a-to-z-mlops:latest .
docker push mlopscr.azurecr.io/a-to-z-mlops:latest

# Attach ACR to AKS
az aks update -n mlops-cluster -g mlops-rg --attach-acr mlopscr
```

### 3. Deploy Services

```bash
kubectl apply -f k8s/
```

---

## Production Considerations

### High Availability

- Use multiple replicas for API pods
- Configure Pod Disruption Budgets
- Use node affinity for spreading

### Security

- Enable network policies
- Use managed identities for cloud resources
- Rotate secrets regularly
- Enable audit logging

### Monitoring

- Use cloud-native monitoring (CloudWatch, Stackdriver, Azure Monitor)
- Set up alerting for critical metrics
- Configure log aggregation

### Cost Optimization

- Use spot/preemptible instances for non-critical workloads
- Configure autoscaling (HPA/VPA)
- Right-size node pools
