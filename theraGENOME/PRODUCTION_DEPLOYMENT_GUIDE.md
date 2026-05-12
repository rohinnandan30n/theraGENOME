# TheraGenome Production Deployment Guide

## 📋 Pre-Deployment Checklist

### Security & Compliance
- [ ] All endpoints have TLS/SSL enabled
- [ ] Database passwords rotated and stored in secure vault
- [ ] HIPAA audit logging enabled and tested
- [ ] Network policies configured and tested
- [ ] Secrets encrypted at rest
- [ ] Security scanning passed (container images)

### Infrastructure
- [ ] Kubernetes cluster provisioned (1.24+)
- [ ] Persistent storage configured (50GB+ for database)
- [ ] Load balancer configured with SSL termination
- [ ] DNS configured to point to load balancer
- [ ] Backup and disaster recovery tested

### Testing
- [ ] All unit tests passing locally
- [ ] Integration tests successful against staging
- [ ] Load testing completed (minimum 1000 req/s)
- [ ] Security audit completed
- [ ] Compliance review completed

---

## 🚀 Deployment Steps

### 1. Prerequisites

```bash
# Install tools
- kubectl 1.24+
- docker 20.10+
- helm 3.10+
- gcloud CLI (if using GCP)

# Get credentials
gcloud container clusters get-credentials theragenome-prod --region us-central1

# Verify connectivity
kubectl cluster-info
```

### 2. Build and Push Docker Images

```bash
# Build Python API image
docker build -t theragenome/api:1.0.0 .
docker push theragenome/api:1.0.0

# Build TypeScript image
docker build -f Dockerfile.deno -t theragenome/variant-api:1.0.0 .
docker push theragenome/variant-api:1.0.0

# Verify images
docker images | grep theragenome
```

### 3. Configure Secrets & ConfigMaps

```bash
# Create namespace
kubectl apply -f k8s/00-namespace-config.yaml

# Update secrets with actual values BEFORE deployment
kubectl edit secret theragenome-secrets -n theragenome

# Verify ConfigMap
kubectl get configmap -n theragenome
```

### 4. Deploy Database

```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f k8s/02-database-deployment.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod \
    -l app=postgresql \
    -n theragenome \
    --timeout=300s

# Run migrations
kubectl exec -it postgresql-0 -n theragenome -- \
    psql -U postgres -d thergenome_dev -c "SELECT version();"

# Apply Alembic migrations
kubectl run -it --image=theragenome/api:1.0.0 \
    --restart=Never \
    -n theragenome \
    migration-job -- \
    alembic upgrade head
```

### 5. Deploy Application Services

```bash
# Apply API deployment
kubectl apply -f k8s/01-api-deployment.yaml

# Wait for deployment
kubectl rollout status deployment/theragenome-api -n theragenome --timeout=5m

# Verify pods are running
kubectl get pods -n theragenome -l app=theragenome-api
```

### 6. Configure Network & Security

```bash
# Apply network policies
kubectl apply -f k8s/03-network-security.yaml

# Verify network policies
kubectl get networkpolicies -n theragenome
```

### 7. Setup Ingress & TLS

```bash
# Update Ingress with actual domain
kubectl set env deployment/theragenome-api \
    SERVER_NAME=theragenome.example.com \
    -n theragenome

# Apply Ingress
kubectl apply -f k8s/03-network-security.yaml

# Verify Ingress IP
kubectl get ingress -n theragenome
```

### 8. Health Checks & Monitoring

```bash
# Check API readiness
kubectl get service theragenome-api -n theragenome

# Get API endpoint
API_IP=$(kubectl get svc theragenome-api -n theragenome -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$API_IP:8000/health

# Check pod logs
kubectl logs -f deployment/theragenome-api -n theragenome -c api
```

---

## 🔍 Post-Deployment Validation

### 1. Database Connectivity

```bash
# Connect to database
kubectl exec -it postgresql-0 -n theragenome -- \
    psql -U postgres -d thergenome_dev -c "\dt"

# Check audit logging
kubectl exec -it postgresql-0 -n theragenome -- \
    psql -U postgres -d thergenome_dev -c "SELECT * FROM pg_stat_statements LIMIT 5;"
```

### 2. API Functionality

```bash
# Test classification endpoint
curl -X POST http://localhost:8000/api/v1/classify \
    -H "Content-Type: application/json" \
    -d '{
        "phyloP_score": 2.0,
        "SIFT_score": 0.1,
        "PolyPhen_score": 0.8,
        "CADD_score": 25.0
    }'

# Test patient endpoint
curl -X GET http://localhost:8000/api/v1/patients \
    -H "Authorization: Bearer $API_TOKEN"
```

### 3. Monitoring & Logging

```bash
# Setup log aggregation (ELK/Loki)
kubectl apply -f monitoring/promtail-config.yaml

# Setup metrics (Prometheus)
kubectl apply -f monitoring/prometheus-config.yaml

# Check metrics
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# Visit http://localhost:9090
```

---

## 📊 Scaling & Performance

### Horizontal Pod Autoscaling

```bash
# HPA automatically scales based on metrics
kubectl get hpa -n theragenome

# Adjust thresholds
kubectl autoscale deployment theragenome-api \
    --min=3 \
    --max=10 \
    --cpu-percent=70 \
    -n theragenome
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 50
```

---

## 🆘 Rollback & Recovery

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/theragenome-api -n theragenome

# Rollback to previous version
kubectl rollout undo deployment/theragenome-api -n theragenome

# Rollback to specific revision
kubectl rollout undo deployment/theragenome-api -n theragenome --to-revision=2
```

### Database Backup & Recovery

```bash
# Backup database
kubectl exec postgresql-0 -n theragenome -- \
    pg_dump -U postgres thergenome_dev > backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i postgresql-0 -n theragenome -- \
    psql -U postgres thergenome_dev < backup-20260402.sql
```

---

## 📈 Monitoring & Alerts

### Key Metrics to Monitor

- API Response Time (p50, p95, p99)
- Database Connection Pool Usage
- Kafka Message Lag
- Pod CPU/Memory Usage
- Failed Request Rate
- Authentication Failures

### Setup Alerts

```yaml
# Example Prometheus alert
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} errors/sec"
```

---

## 🔒 Security Hardening Checklist

- [ ] Enable Pod Security Policies
- [ ] Configure RBAC for cluster access
- [ ] Setup network policies for pod communication
- [ ] Enable audit logging for Kubernetes API
- [ ] Configure image scanning/vulnerability detection
- [ ] Setup secret rotation (90 days)
- [ ] Enable encryption at rest for etcd
- [ ] Configure firewall rules for ingress/egress

---

## 📞 Support & Troubleshooting

### Common Issues

**Pod stuck in Pending**
```bash
kubectl describe pod <pod-name> -n theragenome
kubectl get events -n theragenome --sort-by='.lastTimestamp'
```

**Database connection errors**
```bash
kubectl logs <api-pod> -n theragenome
# Check if DB is ready
kubectl get pod -n theragenome -l app=postgresql
```

**High latency**
```bash
# Check load on nodes
kubectl top nodes
kubectl top pods -n theragenome
```

---

## 📝 Documentation Links

- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Security Hardening Guide](https://kubernetes.io/docs/concepts/security/)
- [HIPAA Compliance Guide](./HIPAA_CHECKLIST.md)
- [API Documentation](./docs/)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

**Last Updated:** April 2, 2026  
**Version:** 1.0  
**Status:** Production Ready
