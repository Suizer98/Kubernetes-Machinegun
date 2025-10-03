#!/bin/bash

echo "🔫 Deploying Kubernetes Machine Gun..."

# Check if kubectl is working
echo "Checking Kubernetes connection..."
kubectl cluster-info

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Build FastAPI image
echo "Building FastAPI image..."
eval $(minikube docker-env)
docker build -f Dockerfile.fastapi -t fastapi:latest .

# Deploy database
echo "Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f k8s/redis.yaml

# Wait for database to be ready
echo "Waiting for database to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n machine-gun --timeout=60s

# Deploy FastAPI
echo "Deploying FastAPI..."
kubectl apply -f k8s/fastapi.yaml

# Deploy Nginx
echo "Deploying Nginx..."
kubectl apply -f k8s/nginx.yaml

# Deploy Prometheus
echo "Deploying Prometheus..."
kubectl apply -f k8s/prometheus.yaml

# Deploy Grafana
echo "Deploying Grafana..."
kubectl apply -f k8s/monitoring.yaml
kubectl apply -f k8s/grafana-dashboard-config.yaml

# Deploy Machine Gun
echo "Deploying Machine Gun..."
kubectl apply -f k8s/machine-gun.yaml

# Wait for services to be ready
echo "Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=fastapi -n machine-gun --timeout=60s
kubectl wait --for=condition=ready pod -l app=nginx -n machine-gun --timeout=60s
kubectl wait --for=condition=ready pod -l app=prometheus -n machine-gun --timeout=60s
kubectl wait --for=condition=ready pod -l app=grafana -n machine-gun --timeout=60s
kubectl wait --for=condition=ready pod -l app=machine-gun -n machine-gun --timeout=60s

# Get service information
echo "Getting service information..."
kubectl get svc -n machine-gun

echo "Deployment complete!"
echo ""
echo "Setting up port forwarding..."
kubectl port-forward svc/grafana -n machine-gun 3000:3000 &
kubectl port-forward svc/nginx -n machine-gun 8080:80 &
echo "   - Grafana: http://localhost:3000"
echo "   - FastAPI: http://localhost:8080"
echo ""
echo "🔫 To start the machine gun:"
echo "minikube kubectl -- exec -it deployment/machine-gun -n machine-gun -- \\"
echo "  python3 machine_gun.py --attack=ddos --target=http://nginx --duration=60 --rps=1000"
echo ""
echo "📊 To check logs:"
echo "kubectl logs -f deployment/fastapi -n machine-gun"
echo "kubectl logs -f deployment/nginx -n machine-gun"
echo "kubectl logs -f deployment/prometheus -n machine-gun"
echo "kubectl logs -f deployment/grafana -n machine-gun"
