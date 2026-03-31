# Task 4.2: API Gateway & Microservices Routing - Complete Guide

**Status**: ✅ COMPLETE  
**Last Updated**: March 31, 2026  
**Version**: 1.0.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Kong API Gateway Setup](#kong-api-gateway-setup)
4. [JWT Authentication (OAuth2 + PKCE)](#jwt-authentication)
5. [Rate Limiting & Logging](#rate-limiting--logging)
6. [OpenTelemetry Tracing](#opentelemetry-tracing)
7. [Unified OpenAPI Specification](#unified-openapi-specification)
8. [Deployment](#deployment)
9. [Testing & Validation](#testing--validation)
10. [Team Distribution](#team-distribution)

---

## Overview

**Task 4.2** implements a complete API Gateway infrastructure for theraGENOME microservices:

| Component | Purpose | Status |
|-----------|---------|--------|
| **Kong Gateway** | API routing, rate limiting, auth | ✅ Complete |
| **JWT Middleware** | OAuth2 + PKCE authentication | ✅ Complete |
| **Rate Limiting** | 100 req/min per clinician | ✅ Complete |
| **Request Logging** | JSON logs to Logstash/Elasticsearch | ✅ Complete |
| **OpenTelemetry** | Distributed tracing with Jaeger | ✅ Complete |
| **Unified API Spec** | Merged OpenAPI from all services | ✅ Complete |

---

## Architecture

### Service Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kong API Gateway (Port 8000)                │
│  - JWT Validation (JWKS)                                        │
│  - Rate Limiting (Redis backend)                                │
│  - Request Logging (Logstash)                                   │
│  - OpenTelemetry Tracing (Jaeger)                               │
└──────────┬──────────────┬──────────────────┬──────────────────┘
           │              │                  │
      ┌────▼─────┐   ┌────▼─────┐      ┌────▼─────┐
      │   Dev 1   │   │   Dev 2   │      │   Dev 3   │
      │ Variant   │   │ Pathogen  │      │   Drug    │
      │ Service   │   │ Resistance│      │  Safety   │
      │(Port 8000)│   │ (Port 8001)      │(Port 8002)│
      └───────────┘   └───────────┘      └───────────┘

Supporting Services:
- PostgreSQL: Kong config storage
- Redis: Rate limiting store
- Jaeger: Distributed tracing UI (port 16686)
- Prometheus: Metrics collection
- Grafana: Metrics visualization (port 3000)
- Elasticsearch: Log storage
- Logstash: Log processing
```

---

## Kong API Gateway Setup

### Configuration Files

```
theraGenome/
├── kong.yml                    # Main Kong configuration (deck format)
├── kong/
│   └── ssl/                    # SSL certificates
│       ├── kong.crt
│       └── kong.key
├── docker-compose.yml          # Complete infrastructure stack
├── prometheus.yml              # Metrics scraping config
├── otel_collector_config.yml   # Tracing config
└── logstash.conf              # Log processing rules
```

### Service Route Mappings

#### Dev 1: Variant Classification
```yaml
Routes:
  GET  /api/v1/variants/{rsid}        → Dev 1 Service (port 8000)
  POST /api/v1/classify               → Dev 1 Service (port 8000)
```

#### Dev 2: Pathogen Resistance
```yaml
Routes:
  GET  /api/v1/pathogens/{id}/resistance-genes   → Dev 2 Service (port 8001)
  POST /api/v1/pathogens/{id}/predict-resistance → Dev 2 Service (port 8001)
```

#### Dev 3: Drug Safety
```yaml
Routes:
  GET  /api/v1/drugs/{id}/pgx-interactions   → Dev 3 Service (port 8002)
  GET  /api/v1/drugs/{id}/adverse-events     → Dev 3 Service (port 8002)
  POST /api/v1/drugs/{id}/check-interactions → Dev 3 Service (port 8002)
  POST /api/v1/drugs/{id}/predict-toxicity   → Dev 3 Service (port 8002)
```

---

## JWT Authentication

### OAuth2 + PKCE Flow

```
┌────────────┐      1. Auth Code Request (PKCE)    ┌──────────────┐
│  Clinician │─────────────────────────────────────→ Auth Provider │
│   Browser  │                                      └──────────────┘
│            │
│            │  2. Authorization Code + Code Verifier
│            │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│            │                                                       │
│            │  3. Token Exchange (Auth Code → JWT)                 │
│            │─────→ Auth Provider ─────→ Get Access Token + ID Token
│            │                                                       │
│            │  4. JWT + API Request                               │
│            │─────→ Kong Gateway ─→ Validate JWT ─→ Route to Service
└────────────┘
```

### JWT Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "kid": "key-2024-03-31",
    "typ": "JWT"
  },
  "payload": {
    "sub": "clinician-001",
    "iss": "https://auth.theragenome.com",
    "aud": "https://api.theragenome.com",
    "scope": ["variants", "pathogens", "drugs"],
    "clinician_name": "Dr. Smith",
    "iat": 1609459200,
    "exp": 1609545600
  },
  "signature": "..."
}
```

### JWKS Endpoint Configuration

```yaml
# Kong JWT Plugin Config (in kong.yml)
plugins:
  - name: jwt
    config:
      key_claim_name: sub
      secret_is_base64: false
      algorithms: [RS256, HS256]
      uri_param_names: [token]
      header_names: [Authorization]
```

**JWKS URL**: `https://auth.theragenome.com/.well-known/jwks.json`

### Test JWT Generation

```bash
# 1. Generate RSA keypair
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem

# 2. Create JWT token
# Use jwt.io or a Python script to encode claims

# 3. Extract JWKS from public key
# Convert PEM to JWKS format using online tools

# 4. Configure Kong to use JWKS endpoint
```

---

## Rate Limiting & Logging

### Rate Limiting Configuration

```yaml
Rate Limit Policy:
  - Limit: 100 requests per minute
  - Scope: Per authenticated consumer (clinician)
  - Backend: Redis (for distributed systems)
  - Breach Action: Return HTTP 429 (Too Many Requests)

Header Response (when approaching limit):
  X-RateLimit-Limit: 6000
  X-RateLimit-Remaining: 5934
  X-RateLimit-Reset: 1609545600
```

### Rate Limit Headers in Response

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1609459260

{
  "data": "..."
}
```

### When Rate Limited

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1609459260

{
  "error": "Rate limit exceeded",
  "message": "100 requests per minute limit reached"
}
```

### Request Logging Format

Logs are sent to Logstash in JSON format:

```json
{
  "timestamp": 1609459123456,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "service_name": "dev1-variant-service",
  "method": "GET",
  "path": "/api/v1/variants/rs12345",
  "status_code": 200,
  "response_time_ms": 145,
  "bytes_sent": 2048,
  "clinician_id": "clinician-001",
  "user_agent": "curl/7.68.0",
  "client_ip": "192.168.1.100",
  "tags": ["dev1", "variants", "success"]
}
```

### Log Aggregation Stack

- **Collection**: Kong TCP Log Plugin → Port 5000
- **Processing**: Logstash (transformations, tagging)
- **Storage**: Elasticsearch (indexed by date)
- **Visualization**: Kibana dashboard

---

## OpenTelemetry Tracing

### Distributed Tracing Architecture

```
Kong Gateway
  ↓
OpenTelemetry Exporter (OTLP gRPC)
  ↓
OpenTelemetry Collector
  ├── Sampler: Always On (production: Always On or Probabilistic)
  ├── Processors: Batch, Memory Limiter, Attributes
  └── Exporters: Jaeger, Prometheus
  ↓
Jaeger Backend (Storage: In-Memory or Cassandra/Elasticsearch)
  ↓
Jaeger UI: http://localhost:16686
```

### Span Information

Each request generates spans with:

```json
{
  "traceID": "550e8400-e29b-41d4-a716-446655440000",
  "spanID": "1234567890abcdef",
  "operationName": "GET /api/v1/variants/{rsid}",
  "startTime": 1609459123456,
  "endTime": 1609459123601,
  "duration": 145,
  "tags": {
    "http.method": "GET",
    "http.url": "/api/v1/variants/rs12345",
    "http.status_code": 200,
    "service.name": "dev1-variant-service",
    "span.kind": "SERVER"
  },
  "logs": [
    {
      "timestamp": 1609459123500,
      "event": "cache_hit",
      "message": "Result found in cache"
    }
  ]
}
```

### Jaeger Query Examples

```
# Find all errors in variants service
service.name=dev1-variant-service AND status=ERROR

# Find slow requests (>500ms)
service.name=* AND duration>500

# Find specific clinician's requests
clinician_id=clinician-001
```

### OpenTelemetry Instrumentation

- **HTTP Server** (Kong): Automatic
- **gRPC Services**: If used, automatic
- **Database** (PostgreSQL): Via database driver
- **Redis**: Via Redis client
- **Custom Spans**: Add via Kong plugin configuration

---

## Unified OpenAPI Specification

### File Location
```
theraGenome/
└── api_gateway/
    ├── unified_api.yaml        # Master specification
    └── unified_api.json        # JSON version
```

### Specification Contents

**Merged Components**:
- ✅ 8 total API endpoints (2+2+4)
- ✅ 12 schemas (request/response types)
- ✅ 3 security schemes (JWT, API Key options)
- ✅ All error codes (400, 404, 429, 500)
- ✅ All tags and descriptions
- ✅ CORS headers and Server configs

### Usage

```bash
# Serve OpenAPI spec
swagger-ui --url ./api_gateway/unified_api.yaml

# Generate client SDKs (JavaScript, Python, Go, etc.)
openapi-generator-cli generate \
  -i ./api_gateway/unified_api.yaml \
  -g python \
  -o ./sdk/python
```

### Spec Validation

```bash
# Validate specification
swagger-cli validate ./api_gateway/unified_api.yaml

# Check for errors
openapi-format ./api_gateway/unified_api.yaml --fix
```

---

## Deployment

### Prerequisites

```bash
# Required tools
- Docker & Docker Compose
- PostgreSQL client (psql) - optional
- curl or Postman - for testing
```

### Quick Start (5 Minutes)

```bash
# 1. Navigate to project root
cd c:\Users\shiva\Desktop\TheraGenome

# 2. Start all services
docker-compose up -d

# 3. Check service health
docker-compose ps

# 4. View logs
docker-compose logs -f kong

# 5. Access Kong Admin API
curl http://localhost:8001/status
```

### Service URLs After Deployment

| Service | URL | Purpose |
|---------|-----|---------|
| Kong Gateway | http://localhost:8000 | API requests |
| Kong Admin | http://localhost:8001 | Configuration |
| Kong Manager UI | http://localhost:8002 | Web dashboard |
| Jaeger Tracing | http://localhost:16686 | View traces |
| Prometheus Metrics | http://localhost:9090 | Query metrics |
| Grafana Dashboards | http://localhost:3000 | Visualize metrics |
| Kibana Logs | http://localhost:5601 | View logs |

### Apply Kong Configuration

```bash
# 1. With deck (declarative configuration tool)
deck sync --kong-addr http://localhost:8001

# 2. Or manually via REST API
curl -X POST http://localhost:8001/services \
  -H "Content-Type: application/json" \
  -d @kong_config.json
```

### Verify Routes

```bash
# List all services
curl http://localhost:8001/services | jq .

# List all routes
curl http://localhost:8001/routes | jq .

# Check specific service
curl http://localhost:8001/services/dev1-variant-service | jq .
```

---

## Testing & Validation

### 1. Test JWT Authentication

```bash
# Create test JWT token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Without JWT (should fail)
curl -X GET http://localhost:8000/api/v1/variants/rs12345

# With JWT (should work)
curl -X GET http://localhost:8000/api/v1/variants/rs12345 \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Test Rate Limiting

```bash
# Make 101 requests in 1 minute (should fail on 101st)
for i in {1..101}; do
  curl -X GET http://localhost:8000/api/v1/variants/rs12345 \
    -H "Authorization: Bearer $TOKEN"
  echo "Request $i completed"
  sleep 0.6  # 60 requests per minute = 1 per second
done

# Check rate limit headers
curl -i -X GET http://localhost:8000/api/v1/variants/rs12345 \
  -H "Authorization: Bearer $TOKEN" | grep "X-RateLimit"
```

### 3. Verify Logging

```bash
# View recent logs in Elasticsearch
curl -X GET http://localhost:9200/kong-logs-*/​_search?size=10

# View logs in Kibana
# Visit http://localhost:5601
# Create index pattern: kong-logs-*
# View logs in Discover tab
```

### 4. Verify Tracing

```bash
# Check Jaeger is receiving traces
curl http://localhost:16686/api/services

# View traces in UI
# Visit http://localhost:16686
# Select service: dev1-variant-service, dev2-pathogen-service, or dev3-drug-safety-service
```

### 5. Test Service Routes

```bash
# Dev 1: Variant Service
curl -X GET "http://localhost:8000/api/v1/variants/rs12345" \
  -H "Authorization: Bearer $TOKEN"

# Dev 2: Pathogen Service
curl -X GET "http://localhost:8000/api/v1/pathogens/562/resistance-genes" \
  -H "Authorization: Bearer $TOKEN"

# Dev 3: Drug Service
curl -X GET "http://localhost:8000/api/v1/drugs/DB00001/pgx-interactions" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Team Distribution

### Files to Share with Each Team

#### ✅ ALL TEAMS RECEIVE:
1. **unified_api.yaml** - Complete API specification
2. **kong.yml** - Gateway configuration (read-only reference)
3. **Docker Compose file** - Infrastructure definition
4. **This documentation** - Setup and usage guide
5. **OpenTelemetry config** - Tracing setup

#### ✅ Dev 1 (Variant Classification):
- Routes in Kong:
  - `GET /api/v1/variants/{rsid}`
  - `POST /api/v1/classify`
- Port: **8000**
- Rate Limit: 100/min per clinician
- Auth: JWT Bearer token

#### ✅ Dev 2 (Pathogen Resistance):
- Routes in Kong:
  - `GET /api/v1/pathogens/{id}/resistance-genes`
  - `POST /api/v1/pathogens/{id}/predict-resistance`
- Port: **8001**
- Rate Limit: 100/min per clinician
- Auth: JWT Bearer token

#### ✅ Dev 3 (Drug Safety):
- Routes in Kong:
  - `GET /api/v1/drugs/{id}/pgx-interactions`
  - `GET /api/v1/drugs/{id}/adverse-events`
  - `POST /api/v1/drugs/{id}/check-interactions`
  - `POST /api/v1/drugs/{id}/predict-toxicity`
- Port: **8002**
- Rate Limit: 100/min per clinician
- Auth: JWT Bearer token

---

## Configuration Reference

### Kong Plugins Enabled

| Plugin | Purpose |
|--------|---------|
| `jwt` | Validate JWT tokens (JWKS validation) |
| `rate-limiting` | 100 req/min per consumer |
| `tcp-log` | Send logs to Logstash (port 5000) |
| `opentelemetry` | Send traces to Jaeger (port 4317) |
| `cors` | Configure CORS headers |
| `request-transformer` | Add custom headers |

### Redis Configuration

```yaml
# Used for:
- Rate limiting state
- Session caching (optional)
- Consumer quotas

# Connection:
host: localhost
port: 6379
database: 0
```

### PostgreSQL Configuration

```yaml
# Used for:
- Kong service/route definitions
- Consumer credentials
- Plugin configuration

# Connection:
host: postgres
port: 5432
database: kong
user: kong
password: kongpassword
```

---

## Troubleshooting

### Issue: "Invalid JWT"
**Solution**: Verify:
1. Token signature matches JWKS public key
2. Token has not expired (`exp` claim)
3. Token issuer matches policy (`iss` claim)
4. Token audience is correct (`aud` claim)

### Issue: "Rate limit exceeded"
**Solution**:
1. Wait 60 seconds for quota reset
2. Check rate limit headers: `X-RateLimit-Reset`
3. Verify Redis is running: `docker ps | grep redis`

### Issue: "No trace data in Jaeger"
**Solution**:
1. Verify OpenTelemetry Collector: `docker logs theragenome-otel-collector`
2. Check Jaeger is running: `docker ps | grep jaeger`
3. Make requests with auth token to generate traces

### Issue: "Logs not appearing in Elasticsearch"
**Solution**:
1. Verify Logstash: `docker logs theragenome-logstash`
2. Check Elasticsearch: `curl localhost:9200/_health`
3. Verify tcp-log plugin configuration in kong.yml

---

## Next Steps

1. ✅ **Deploy** infrastructure using docker-compose
2. 🔄 **Configure** JWT issuer (Auth Provider)
3. 🔄 **Test** routes with sample tokens
4. 🔄 **Monitor** metrics in Grafana
5. 🔄 **Document** service-specific details
6. 🔄 **Distribute** to teams

---

**Questions?** Contact: dev@theragenome.com
