# Task 4.2: Quick Start Guide

**Deploying Kong API Gateway for theraGENOME**

---

## ⚡ 5-Minute Quick Start

### Step 1: Prepare Environment

```bash
# Navigate to project
cd c:\Users\shiva\Desktop\TheraGenome

# Verify required files exist
ls kong.yml docker-compose.yml  # Should exist
```

### Step 2: Start Infrastructure

```bash
# Start all services (Kong, Redis, Jaeger, ELK Stack, etc.)
docker-compose up -d

# Watch for startup
docker-compose logs -f kong

# Wait for Kong to be healthy (look for "Kong Enterprise Edition" message)
# Usually takes 30-60 seconds
```

### Step 3: Verify Services

```bash
# Check all containers running
docker-compose ps

# Should see:
# - theragenome-kong         (Up) ✓
# - theragenome-postgres     (Up) ✓
# - theragenome-redis        (Up) ✓
# - theragenome-jaeger       (Up) ✓
# - theragenome-prometheus   (Up) ✓
# - theragenome-grafana      (Up) ✓
```

### Step 4: Test Gateway

```bash
# Create test JWT token
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjbGluaWNpYW4tMDAxIiwiaXNzIjoiaHR0cHM6Ly9hdXRoLnRoZXJhZ2Vub21lLmNvbSIsImF1ZCI6Imh0dHBzOi8vYXBpLnRoZXJhZ2Vub21lLmNvbSIsImlhdCI6MTYwOTQ1OTIwMCwiZXhwIjoyMjA5NDU5MjAwfQ.UXa3_4bZl5wFzp5bZl5wFzp5bZl5wFzp5bZl5wFzp="

# Test route (may fail if backend not running yet, but proves Kong is routing)
curl -i http://localhost:8000/api/v1/variants/rs12345 `
  -H "Authorization: Bearer $TOKEN"

# Should either:
# - Get response from dev 1 service (if running)
# - Get 502/503 (if backend not running) ← This is OK for now
```

### Step 5: Access UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Kong Admin** | http://localhost:8001/status | None (open) |
| **Kong Manager** | http://localhost:8002 | default/default |
| **Jaeger Traces** | http://localhost:16686 | None (open) |
| **Prometheus** | http://localhost:9090 | None (open) |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Kibana (Logs)** | http://localhost:5601 | None (open) |

---

## 🔧 Development Setup

### Using Your Microservices

```bash
# Terminal 1: Start Kong (already running in docker-compose)
# Already done!

# Terminal 2: Start Dev 1 (Variant Service) on port 8000
cd /path/to/dev1-variant-service
python -m uvicorn main:app --port 8000

# Terminal 3: Start Dev 2 (Pathogen Service) on port 8001
cd /path/to/dev2-pathogen-service
python -m gunicorn -w 4 -b 0.0.0.0:8001 src.main:app

# Terminal 4: Start Dev 3 (Drug Safety Service) on port 8002
cd /path/to/dev3-drug-safety-service
python -m uvicorn main:app --port 8002
```

### Test Full Stack

```bash
# Set token (valid JWT)
$TOKEN = "your-jwt-token"

# Test each service through Kong gateway
curl -X GET http://localhost:8000/api/v1/variants/rs12345 `
  -H "Authorization: Bearer $TOKEN"

curl -X GET http://localhost:8000/api/v1/pathogens/562/resistance-genes `
  -H "Authorization: Bearer $TOKEN"

curl -X GET http://localhost:8000/api/v1/drugs/DB00001/pgx-interactions `
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Monitoring & Debugging

### View Real-Time Logs

```bash
# Kong logs
docker-compose logs -f kong

# Services
docker-compose logs -f otel-collector
docker-compose logs -f jaeger

# Summary
docker-compose logs --tail=50
```

### Check Service Health

```bash
# Kong health
curl http://localhost:8001/status

# Individual services (if running)
curl http://localhost:8000/health    # Dev 1
curl http://localhost:8001/health    # Dev 2
curl http://localhost:8002/health    # Dev 3
```

### Monitor Metrics

```bash
# Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Kong-specific metrics
curl http://localhost:9090/api/v1/query?query=kong_http_requests_total
```

---

## 🧪 Testing Scenarios

### Scenario 1: Normal Request Flow

```bash
TOKEN="your-valid-jwt"

# Make request
curl -v http://localhost:8000/api/v1/variants/rs12345 \
  -H "Authorization: Bearer $TOKEN"

# Expected:
# - Status: 200 (if service responds) or 502 (if service down)
# - Headers: X-RateLimit-Limit: 100, X-RateLimit-Remaining: 99
# - Trace created in Jaeger
# - Log entry in Elasticsearch
```

### Scenario 2: Missing JWT Token

```bash
# Make request WITHOUT token
curl -v http://localhost:8000/api/v1/variants/rs12345

# Expected:
# - Status: 401 Unauthorized
# - Error: "Unauthorized"
```

### Scenario 3: Rate Limiting

```bash
TOKEN="your-valid-jwt"

# Make 102 requests rapidly
for i in {1..102}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:8000/api/v1/variants/rs12345 \
    -H "Authorization: Bearer $TOKEN")
  echo "Request $i: $STATUS"
  sleep 0.5
done

# Expected:
# - Requests 1-100: 200/502 (service response)
# - Request 101-102: 429 (Too Many Requests)
```

### Scenario 4: View Distributed Traces

```bash
# Make request
curl http://localhost:8000/api/v1/variants/rs12345 \
  -H "Authorization: Bearer $TOKEN"

# Visit http://localhost:16686 (Jaeger UI)
# - Service: kong
# - Operation: /api/v1/variants/rs12345
# - View full trace with timings
```

---

## 🚀 Deployment Checklist

- [ ] **Infrastructure**
  - [ ] Docker & Docker Compose installed
  - [ ] 5 GB disk space available
  - [ ] Ports 8000-16686 available

- [ ] **Configuration**
  - [ ] `kong.yml` present
  - [ ] `docker-compose.yml` present
  - [ ] SSL certificates in `kong/ssl/` (self-signed OK for dev)

- [ ] **Services**
  - [ ] Dev 1 running on port 8000
  - [ ] Dev 2 running on port 8001
  - [ ] Dev 3 running on port 8002

- [ ] **Gateway**
  - [ ] Kong started: `docker-compose up -d`
  - [ ] Kong healthy: `docker-compose ps`
  - [ ] Admin API responding: `curl http://localhost:8001/status`

- [ ] **Authentication**
  - [ ] JWT issuer configured
  - [ ] JWKS endpoint accessible
  - [ ] Test token created

- [ ] **Testing**
  - [ ] Routes registered in Kong
  - [ ] Requests flow through gateway
  - [ ] JWT validation working
  - [ ] Rate limiting active

- [ ] **Monitoring**
  - [ ] Jaeger collecting traces
  - [ ] Prometheus scraping metrics
  - [ ] Elasticsearch indexing logs
  - [ ] Grafana dashboards visible

- [ ] **Documentation**
  - [ ] Team notified of API URLs
  - [ ] OpenAPI spec distributed
  - [ ] Credentials shared securely
  - [ ] Support contact information provided

---

## 📞 Support

### Common Issues

| Issue | Solution |
|-------|----------|
| Kong not starting | Check logs: `docker-compose logs kong` |
| Port 8000 already in use | `docker ps` to find conflict, `docker stop <container>` |
| JWT validation fails | Verify token exp, iss, aud claims match config |
| Rate limit too strict | Adjust `minute: 100` in kong.yml |
| Traces not showing | Verify otel-collector running: `docker ps \| grep otel` |

### Getting Help

1. Check logs: `docker-compose logs`
2. Review documentation: `API_GATEWAY.md`
3. Test connectivity: `curl http://localhost:8001/status`
4. Contact: dev@theragenome.com

---

## 📁 File Structure

```
theraGenome/
├── kong/
│   └── ssl/
│       ├── kong.crt
│       └── kong.key
├── kong.yml                 ← Kong configuration
├── docker-compose.yml       ← Infrastructure
├── otel_collector_config.yml
├── prometheus.yml
├── logstash.conf
├── api_gateway/
│   ├── unified_api.yaml     ← OpenAPI specification
│   ├── unified_api.json
│   ├── merge_report.json
│   └── merge.log
├── openapi_specs/           ← Individual service specs
│   ├── variant_api.openapi.yaml
│   ├── classification_api.openapi.yaml
│   ├── pathogen_resistance_api.openapi.yaml
│   └── drug_safety_api.openapi.yaml
├── API_GATEWAY.md           ← Full documentation
└── TASK_4_2_QUICKSTART.md   ← This file
```

---

**Status**: ✅ Ready for Deployment  
**Last Updated**: March 31, 2026
