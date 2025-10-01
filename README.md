# 🔫 Kubernetes Machine Gun

**Load testing platform for Kubernetes applications**

**Machine Gun** → **Nginx** → **FastAPI** (3 replicas)  
**Prometheus** ← **Grafana** ← **PostgreSQL** + **Redis**

## Quick Start

```bash
# Deploy
chmod +x deploy.sh && ./deploy.sh

# Access services
minikube service grafana -n machine-gun
minikube service prometheus -n machine-gun
minikube service nginx -n machine-gun
```

## 💥 Launch Attacks

```bash
# DDoS (1000 RPS)
minikube kubectl -- exec -it deployment/machine-gun -n machine-gun -- \
  python3 machine_gun.py --attack=ddos --target=http://nginx --duration=60 --rps=1000

# Burst (2000 RPS spike)
minikube kubectl -- exec -it deployment/machine-gun -n machine-gun -- \
  python3 machine_gun.py --attack=burst --target=http://nginx --duration=30 --rps=2000

# Sustained (500 RPS)
minikube kubectl -- exec -it deployment/machine-gun -n machine-gun -- \
  python3 machine_gun.py --attack=sustained --target=http://nginx --duration=300 --rps=500
```

## Monitoring

- **Grafana**: `minikube service grafana -n machine-gun` (admin/admin)
- **Prometheus**: `minikube service prometheus -n machine-gun`
- **FastAPI**: `minikube service nginx -n machine-gun`

## Stop Services

```bash
# Stop all services (clean)
minikube kubectl -- delete namespace machine-gun

# Stop Minikube entirely
minikube stop
```

