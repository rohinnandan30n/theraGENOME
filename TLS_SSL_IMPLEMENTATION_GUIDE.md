# TLS/SSL Implementation Guide for TheraGenome

**Status:** Implementation Steps for Critical Item #1  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for HIPAA Compliance

---

## Overview

This guide provides step-by-step instructions for enabling TLS/SSL encryption for all in-transit communications in TheraGenome production environment.

### Components to Secure:
1. ✅ API Endpoints (Ingress) - HSTS, TLS 1.2+
2. ✅ Variant API (TypeScript/Deno) - TLS support
3. ✅ PostgreSQL Database - SSL connections
4. ✅ inter-Service Communication - mTLS (optional but recommended)
5. ✅ Kafka Communication - TLS (separate)

---

## Prerequisites

- Kubernetes 1.24+ cluster running
- `kubectl` installed and configured
- `helm` 3.10+ installed
- Domain name (e.g., theragenome.example.com) with DNS control
- AWS Route53 access (for DNS01 ACME challenge) or use HTTP01 challenge

---

## Phase 1: Install cert-manager (5 minutes)

### Step 1: Add Helm repository
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
```

### Step 2: Create cert-manager namespace
```bash
kubectl create namespace cert-manager
```

### Step 3: Install cert-manager CRDs
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.crds.yaml
```

### Step 4: Install cert-manager Helm chart
```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --version v1.13.0 \
  --values - <<EOF
global:
  leaderElection:
    namespace: cert-manager
installCRDs: false
serviceAccount:
  create: true
EOF
```

### Step 5: Verify cert-manager installation
```bash
kubectl get pods -n cert-manager
kubectl get crd | grep cert-manager
```

**Expected Output:**
- 3 cert-manager pods running
- cert-manager CRDs installed

---

## Phase 2: Deploy Certificate Issuers (5 minutes)

### Step 1: Update cert-manager issuer configuration

**File:** `k8s/04-tls-certificate-issuer.yaml`

Update the following:
```yaml
# Change email to your admin email
email: admin@theragenome.com

# For HTTP01 challenge (simpler, recommended first):
solvers:
- http01:
    ingress:
      class: nginx

# For DNS01 challenge (wildcard support):
# Set AWS_ACCESS_KEY_ID and secret-access-key in AWS credentials secret
```

### Step 2: Create AWS Route53 credentials secret (if using DNS01)
```bash
kubectl create secret generic aws-route53-credentials \
  --from-literal=secret-access-key='YOUR_AWS_SECRET_ACCESS_KEY' \
  -n cert-manager
```

### Step 3: Deploy cert-manager issuers
```bash
kubectl apply -f k8s/04-tls-certificate-issuer.yaml
```

### Step 4: Verify ClusterIssuer status
```bash
kubectl describe clusterissuer letsencrypt-prod
kubectl describe clusterissuer letsencrypt-staging
kubectl get clusterissuer
```

**Expected Output:**
- Status: Ready=True for both issuers

---

## Phase 3: Deploy TLS Ingress and Endpoints (10 minutes)

### Step 1: Update domain in ingress configuration

**File:** `k8s/05-tls-ingress-and-endpoints.yaml`

Replace `theragenome.example.com` with your actual domain:
```bash
sed -i 's/theragenome.example.com/your-domain.com/g' k8s/05-tls-ingress-and-endpoints.yaml
```

### Step 2: Ensure NGINX Ingress Controller is installed
```bash
# Check if NGINX ingress exists
kubectl get ingressclass nginx

# If not, install it:
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### Step 3: Deploy ingress and variant API
```bash
kubectl apply -f k8s/05-tls-ingress-and-endpoints.yaml
```

### Step 4: Monitor certificate issuance
```bash
# Watch certificate creation
kubectl get certificate -n theragenome -w

# Check certificate details
kubectl describe certificate theragenome-tls -n theragenome
kubectl describe certificate variant-api-tls -n theragenome

# View the secret
kubectl get secret theragenome-tls -n theragenome -o yaml
```

**Expected Output:**
- Certificates should reach `Ready=True` within 1-2 minutes
- TLS secrets created in theragenome namespace

---

## Phase 4: Configure PostgreSQL SSL (15 minutes)

### Step 1: Generate PostgreSQL SSL certificates

```bash
# Create temporary directory
mkdir -p /tmp/postgres-certs
cd /tmp/postgres-certs

# Generate CA certificate
openssl req -new -nodes -x509 -days 3650 \
  -keyout ca.key -out ca.crt \
  -subj "/CN=TheraGenome-CA"

# Generate server certificate
openssl req -new -nodes -x509 -days 3650 \
  -keyout server.key -out server.crt \
  -addext "subjectAltName=DNS:postgresql.theragenome.svc.cluster.local,DNS:postgresql" \
  -subj "/CN=postgresql.theragenome.svc.cluster.local"

# Generate DH parameters (takes ~2-3 minutes)
openssl dhparam -out dh.pem 2048

# Set correct permissions
chmod 600 server.key ca.key

# Verify certificates
openssl x509 -in server.crt -text -noout
openssl x509 -in ca.crt -text -noout
```

### Step 2: Create Kubernetes secret for PostgreSQL SSL

```bash
# First, update the secret in 06-postgresql-ssl-config.yaml
# Or create it directly:
kubectl create secret tls postgresql-server-certs \
  --cert=/tmp/postgres-certs/server.crt \
  --key=/tmp/postgres-certs/server.key \
  -n theragenome

# Add CA certificate
kubectl create secret generic postgresql-ca-cert \
  --from-file=ca.crt=/tmp/postgres-certs/ca.crt \
  -n theragenome
```

### Step 3: Update PostgreSQL ConfigMap and Secret

```bash
# Deploy PostgreSQL SSL configuration
kubectl apply -f k8s/06-postgresql-ssl-config.yaml
```

### Step 4: Restart PostgreSQL StatefulSet

```bash
# Delete existing pods to force restart with new SSL config
kubectl delete pod postgresql-0 -n theragenome

# Watch restoration
kubectl get pods -n theragenome -w

# Wait for pod to be ready
kubectl wait --for=condition=ready pod \
  -l app=postgresql \
  -n theragenome \
  --timeout=300s
```

### Step 5: Verify PostgreSQL SSL

```bash
# Connect to PostgreSQL pod
kubectl exec -it postgresql-0 -n theragenome -- /bin/bash

# Inside the pod, check SSL status
psql -U postgres -c "SHOW ssl;"

# Should output: on
```

---

## Phase 5: Update Application Configuration (10 minutes)

### Step 1: Update ConfigMap with TLS settings

Update `k8s/00-namespace-config.yaml`:
```yaml
data:
  DB_HOST_TLS: "postgresql.theragenome.svc.cluster.local"
  DB_PORT_TLS: "5432"
  DB_SSL_MODE: "require"
  REDIS_ENABLE_TLS: "true"
  KAFKA_SECURITY_PROTOCOL: "SSL"
  TLS_MIN_VERSION: "1.2"
```

### Step 2: Update application code to use TLS

**Python (FastAPI):**
```python
# In db_connection.py
import ssl
from sqlalchemy import create_engine

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_REQUIRED
ssl_context.load_verify_locations('path/to/ca.crt')

DATABASE_URL = "postgresql+psycopg2://user:pass@postgresql:5432/thergenome_dev?sslmode=require"

# Or with SSL context:
engine = create_engine(
    DATABASE_URL,
    connect_args={'sslmode': 'require', 'ssl_certfile': 'path/to/cert.crt'}
)
```

**TypeScript (Deno):**
```typescript
// In database connection
const dbConfig = {
  hostname: Deno.env.get("DB_HOST"),
  port: parseInt(Deno.env.get("DB_PORT") || "5432"),
  user: Deno.env.get("DB_USER"),
  password: Deno.env.get("DB_PASSWORD"),
  database: Deno.env.get("DB_NAME"),
  ssl: true,  // Enable SSL
  certFile: "/etc/tls/certs/ca.crt",  // Or use system CA bundle
};
```

### Step 3: Deploy updated applications

```bash
kubectl apply -f k8s/01-api-deployment.yaml
kubectl apply -f k8s/05-tls-ingress-and-endpoints.yaml
```

---

## Phase 6: Verification and Testing (15 minutes)

### Test 1: HTTPS Connectivity
```bash
# Get the LoadBalancer IP
kubectl get svc -n ingress-nginx

# Test HTTPS connection
curl -v https://theragenome.example.com/health

# Expected: HTTP/2 200 OK with valid certificate
```

### Test 2: Certificate Details
```bash
# Check certificate validity
openssl s_client -connect theragenome.example.com:443 -showcerts

# Should show:
# - Subject: CN=theragenome.example.com
# - Issuer: CN=Let's Encrypt
# - Valid dates
```

### Test 3: TLS Protocol Version
```bash
# Check TLS version
curl -v --tlsv1.2 https://theragenome.example.com/health

# TLS 1.1 should fail:
curl -v --tlsv1.1 https://theragenome.example.com/health
# Expected: error or connection refused
```

### Test 4: Database SSL
```bash
# SSH into PostgreSQL pod
kubectl exec -it postgresql-0 -n theragenome -- /bin/bash

# From the pod, test SSL connection
psql -h localhost -U postgres -c "SELECT version();" \
  --set sslmode=require

# From outside the cluster
psql -h postgresql.theragenome.svc.cluster.local \
  -U postgres \
  -c "SELECT version();" \
  --set sslmode=require
```

### Test 5: Check Pod Logs for SSL Errors
```bash
# API logs
kubectl logs -n theragenome deployment/theragenome-api --tail=50

# Variant API logs
kubectl logs -n theragenome deployment/variant-api --tail=50

# Look for: "SSL Certificate verified" or connection errors
```

---

## Phase 7: Monitoring and Certificates Renewal

### Automatic Renewal
```bash
# cert-manager automatically renews certificates 30 days before expiry
# No manual action needed

# Check renewal status
kubectl get certificate -n theragenome -o wide
```

### Alert Configuration
```yaml
# Add to your monitoring system (Prometheus, etc.):
# Alert when certificate expires in < 7 days
labels:
  severity: warning
  certificate_name: theragenome-tls
  ttl_days: 7
```

### Monitoring Command
```bash
# List all certificates with expiry dates
kubectl get certificate -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.renewalTime}{"\n"}{end}'
```

---

## Troubleshooting

### Certificate Not Issuing
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager -f

# Check certificate resource
kubectl describe certificate theragenome-tls -n theragenome

# Check challenge status
kubectl get challenges -n theragenome
kubectl describe challenge <challenge-name> -n theragenome
```

### SSL Handshake Failure
```bash
# Check ingress configuration
kubectl describe ingress theragenome-ingress -n theragenome

# Check TLS secret
kubectl get secret theragenome-tls -n theragenome -o yaml

# Verify secret is mounted correctly
kubectl get pod <api-pod-name> -n theragenome -o yaml | grep -A 5 volumeMounts
```

### PostgreSQL SSL Connection Errors
```bash
# Check PostgreSQL logs
kubectl logs postgresql-0 -n theragenome --tail=100 | grep -i ssl

# Verify certificates in pod
kubectl exec -it postgresql-0 -n theragenome -- \
  ls -la /var/run/secrets/kubernetes.io/certs/

# Test connection from another pod
kubectl run -it psql-test --image=postgres --restart=Never \
  -n theragenome -- \
  psql -h postgresql -U postgres -c "SELECT version();" \
  --set sslmode=require
```

---

## Post-Implementation

### Update Compliance Audit
- [x] Mark Item #1 as COMPLETE in compliance audit
- [ ] Document certificate strategy for team
- [ ] Create certificate renewal procedures
- [ ] Train team on TLS troubleshooting

### Next Steps
1. Move to **Item 2: Implement database encryption (at-rest)**
2. Set up key management for encryption keys
3. Configure EBS/storage encryption in Kubernetes

---

## Commands Reference

```bash
# Quick status check
kubectl get certificate,secret -n theragenome
kubectl get ingress -n theragenome -o wide
kubectl logs -n cert-manager deployment/cert-manager --tail=20

# Force renewal (if needed)
kubectl delete secret theragenome-tls -n theragenome
kubectl delete certificate theragenome-tls -n theragenome
kubectl apply -f k8s/05-tls-ingress-and-endpoints.yaml

# Full restart
kubectl rollout restart deployment/theragenome-api -n theragenome
kubectl rollout restart deployment/variant-api -n theragenome
kubectl rollout restart statefulset/postgresql -n theragenome
```

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
