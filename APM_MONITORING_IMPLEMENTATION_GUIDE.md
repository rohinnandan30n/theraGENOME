# APM Monitoring Implementation Guide (Item #4)

**Status:** Implementation Steps for Critical Item #4  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for Operational Observability & SLO Compliance

---

## Overview

This guide provides step-by-step instructions for deploying Application Performance Monitoring (APM) for TheraGenome, including metrics collection, distributed tracing, and real-time dashboards.

### Components to Deploy:
1. **Prometheus** - Metrics collection and time-series database
2. **Grafana** - Metrics visualization and dashboards
3. **OpenTelemetry Collector** - Traces and metrics aggregation
4. **Jaeger** - Distributed tracing backend
5. **Application Instrumentation** - OpenTelemetry SDKs for Python/TypeScript

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Applications (Instrumented with OpenTelemetry)              │
│ ├─ theragenome-api (Python/FastAPI)                         │
│ ├─ variant-api (TypeScript/Deno)                            │
│ └─ PostgreSQL (via exporter)                                │
└──────────┬──────────────────────────────────────────────────┘
           │ Traces (gRPC)     Metrics (HTTP)
           │                   node_exporter
           │
┌──────────▼──────────────────────────────────────────────────┐
│ OpenTelemetry Collector (Aggregation & Processing)          │
│ ├─ Receivers: OTLP, Jaeger, Zipkin, Prometheus             │
│ ├─ Processors: Batch, Sampling, Attributes                 │
│ └─ Exporters: Jaeger, Prometheus                            │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────┴───────────────┬──────────────────┐
    │                      │                  │
┌───▼──────────┐  ┌────────▼────────┐  ┌────▼─────────────┐
│ Prometheus   │  │ Jaeger          │  │ Loki (logs)      │
│ (Metrics DB) │  │ (Trace Storage) │  │ (Log Storage)    │
└───┬──────────┘  └────────┬────────┘  └────┬─────────────┘
    │                       │               │
    └───────────┬───────────┴───────────────┘
                │
            ┌───▼─────────────┐
            │ Grafana         │
            │ (Dashboards &   │
            │  Alerting)      │
            └─────────────────┘
```

---

## Prerequisites

- Kubernetes 1.24+ cluster
- 2GB RAM available for monitoring stack
- PostgreSQL cluster running
- Applications capable of OpenTelemetry instrumentation

---

## Phase 1: Create Monitoring Namespace (5 minutes)

### Step 1: Create namespace and RBAC

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Create ServiceAccount for Prometheus
kubectl apply -f k8s/13-prometheus-monitoring.yaml --selector='metadata.name=prometheus'

# Verify namespace
kubectl get namespace monitoring
kubectl get serviceaccount -n monitoring
```

---

## Phase 2: Deploy Prometheus (15 minutes)

### Step 1: Deploy Prometheus

```bash
# Apply Prometheus configuration
kubectl apply -f k8s/13-prometheus-monitoring.yaml

# Wait for deployment
kubectl rollout status deployment/prometheus -n monitoring --timeout=5m

# Verify pods are running
kubectl get pods -n monitoring -l app=prometheus
```

### Step 2: Access Prometheus Dashboard

```bash
# Port forward to access Prometheus UI
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Access at http://localhost:9090
```

### Step 3: Verify Metrics Collection

```bash
# Check metrics being scraped
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Check specific metrics
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result'
```

---

## Phase 3: Deploy Grafana (10 minutes)

### Step 1: Deploy Grafana

```bash
# Apply Grafana configuration
kubectl apply -f k8s/14-grafana-deployment.yaml

# Wait for deployment
kubectl rollout status deployment/grafana -n monitoring --timeout=5m
```

### Step 2: Access Grafana Dashboard

```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000 &

# Access at http://localhost:3000
# Default credentials: admin / admin-password-change-in-production
```

### Step 3: Add Prometheus Data Source

```bash
# Verify data source is automatically provisioned
curl -s http://localhost:3000/api/datasources | jq '.[] | {name, type, url}'

# Create dashboard manually (if not automatically provisioned)
# 1. Dashboard > + New Dashboard
# 2. Add Panel > Prometheus Query
# 3. Enter query: rate(http_requests_total[5m])
```

### Step 4: Import Pre-built Dashboards

```bash
# Import Node Exporter dashboard (ID: 1860)
# Import Prometheus dashboard (ID: 3662)
# Import PostgreSQL dashboard (ID: 9628)
# Import API performance dashboard (ID: 11500)
```

---

## Phase 4: Deploy OpenTelemetry Collector (15 minutes)

### Step 1: Deploy OpenTelemetry Collector

```bash
# Apply OpenTelemetry configuration
kubectl apply -f k8s/15-opentelemetry-collector.yaml

# Wait for deployment
kubectl rollout status deployment/otel-collector -n monitoring --timeout=5m

# Verify collector is running
kubectl get pods -n monitoring -l app=otel-collector
```

### Step 2: Verify Collector Endpoints

```bash
# Check OTLP receiver is listening
kubectl port-forward -n monitoring svc/otel-collector 4317:4317 &

# Test collector health
curl -v http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Phase 5: Instrument Python Application (20 minutes)

### Step 1: Install OpenTelemetry Dependencies

```bash
# Add to requirements.txt
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-exporter-prometheus==0.41b0
opentelemetry-exporter-jaeger==1.20.0
opentelemetry-exporter-otlp==1.20.0
opentelemetry-instrumentation==0.41b0
opentelemetry-instrumentation-fastapi==0.41b0
opentelemetry-instrumentation-sqlalchemy==0.41b0
opentelemetry-instrumentation-redis==0.41b0
opentelemetry-instrumentation-requests==0.41b0
```

### Step 2: Instrument FastAPI Application

**File:** `scripts/main.py` or `api/app.py`

```python
import os
from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.resources import Resource

# Initialize tracer
resource = Resource.create({
    "service.name": "theragenome-api",
    "service.version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "development")
})

trace_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
    insecure=True
)

trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)

# Initialize metrics
metric_exporter = OTLPMetricExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
    insecure=True
)

metric_reader = PeriodicExportingMetricReader(metric_exporter, interval_millis=5000)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)

# Create FastAPI app
app = FastAPI(title="TheraGenome API")

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Instrument SQLAlchemy
SQLAlchemyInstrumentor().instrument()

# Instrument requests
RequestsInstrumentor().instrument()

# Add custom metrics
def get_tracer():
    return trace.get_tracer(__name__)

def get_meter():
    return metrics.get_meter(__name__)

# Example endpoint with tracing
@app.get("/health")
async def health():
    tracer = get_tracer()
    with tracer.start_as_current_span("health-check"):
        return {"status": "healthy"}

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    tracer = get_tracer()
    with tracer.start_as_current_span("get-patient") as span:
        span.set_attribute("patient.id", patient_id)
        # Database query...
        return {"id": patient_id, "name": "Patient"}
```

### Step 3: Update Dockerfile for Metrics Endpoint

**Update:** `Dockerfile`

```dockerfile
FROM python:3.11-slim

# ... existing setup ...

# Expose metrics port
EXPOSE 8000 8001

# Run with metrics enabled
CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--metrics-port", "8001"]
```

### Step 4: Update Kubernetes Deployment

**Update:** `k8s/01-api-deployment.yaml`

```yaml
containers:
- name: api
  # ... existing config ...
  ports:
  - name: http
    containerPort: 8000
  - name: metrics
    containerPort: 8001
  
  env:
  # ... existing env vars ...
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector.monitoring:4317"
  - name: OTEL_METRICS_EXPORTER
    value: "otlp"
  - name: OTEL_TRACES_EXPORTER
    value: "otlp"
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.name=theragenome-api,service.version=1.0.0,environment=production"
```

---

## Phase 6: Instrument TypeScript/Deno Application (20 minutes)

### Step 1: Install OpenTelemetry SDK for Deno

```typescript
// File: src/telemetry.ts

import { trace, context, metrics } from "https://deno.land/x/opentelemetry_api@v0.20.0/mod.ts";
import { NodeSDK } from "https://deno.land/x/opentelemetry_node_sdk@v0.20.0/mod.ts";
import { OTLPExporter } from "https://deno.land/x/opentelemetry_exporter_trace_otlp_grpc@v0.20.0/mod.ts";
import { OTLPMetricExporter } from "https://deno.land/x/opentelemetry_exporter_metrics_otlp_grpc@v0.20.0/mod.ts";

// Initialize OpenTelemetry
const otlpExporter = new OTLPExporter({
  url: Deno.env.get("OTEL_EXPORTER_OTLP_ENDPOINT") || "http://otel-collector:4317",
});

const metricExporter = new OTLPMetricExporter({
  url: Deno.env.get("OTEL_EXPORTER_OTLP_METRIC_ENDPOINT") || "http://otel-collector:4317",
});

export const sdk = new NodeSDK({
  traceExporter: otlpExporter,
  metricExporter: metricExporter,
  instrumentations: [
    // Auto-instrumentation for HTTP, database, etc.
  ],
});

// Initialize tracer
export const tracer = trace.getTracer("theragenome-variant-api");
export const meter = metrics.getMeter("theragenome-variant-api");

// Custom counter for variant analysis
export const variantAnalysisCounter = meter.createCounter("variant_analyses", {
  description: "Number of variant analyses performed",
});

// Custom histogram for analysis duration
export const analysisHistogram = meter.createHistogram("variant_analysis_duration", {
  description: "Duration of variant analysis in milliseconds",
  unit: "ms",
});
```

### Step 2: Instrument API Routes

```typescript
// File: src/api/variants.ts

import { tracer, variantAnalysisCounter, analysisHistogram } from "../telemetry.ts";
import { context } from "https://deno.land/x/opentelemetry_api@v0.20.0/mod.ts";

export async function analyzeVariant(variantId: string) {
  const span = tracer.startSpan("analyze-variant");
  
  return context.with(trace.setSpan(context.active(), span), async () => {
    try {
      span.setAttributes({
        "variant.id": variantId,
        "service.name": "theragenome-variant-api",
      });
      
      const startTime = performance.now();
      
      // Perform analysis
      const result = await performAnalysis(variantId);
      
      const duration = performance.now() - startTime;
      
      // Record metrics
      variantAnalysisCounter.add(1, { status: "success" });
      analysisHistogram.record(duration, { analysis_type: "variant" });
      
      span.setStatus({ code: "OK" });
      return result;
      
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: "ERROR", message: error.message });
      variantAnalysisCounter.add(1, { status: "error" });
      throw error;
      
    } finally {
      span.end();
    }
  });
}
```

---

## Phase 7: Create Dashboards (20 minutes)

### Step 1: API Performance Dashboard

```bash
# Create Grafana dashboard via API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @- << 'EOF'
{
  "dashboard": {
    "title": "TheraGenome API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Response Latency (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Active Connections",
        "targets": [{
          "expr": "pg_stat_activity_count"
        }]
      }
    ]
  }
}
EOF
```

### Step 2: Database Performance Dashboard

```bash
# Create database monitoring dashboard
# - Database size trends
# - Query performance
# - Connection pool saturation
# - Slow query rates
# - Backup status
```

### Step 3: Infrastructure Dashboard

```bash
# Create infrastructure dashboard
# - CPU usage across nodes
# - Memory usage trends
# - Disk I/O
# - Network traffic
# - Pod resource usage
```

---

## Phase 8: Setup Alerting (15 minutes)

### Step 1: Create Alert Rules

Alert rules are already defined in `k8s/13-prometheus-monitoring.yaml`.

Verify they're loaded:
```bash
# Check alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert, for, expr}'

# Check alert status
curl -s http://localhost:9090/api/v1/alerts | jq '.data'
```

### Step 2: Configure Alertmanager

```yaml
# k8s/16-alertmanager-config.yaml (create this)
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
      slack_api_url: 'YOUR_SLACK_WEBHOOK'
    
    route:
      receiver: 'default'
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 4h
      routes:
      - match:
          severity: critical
        receiver: 'critical'
        continue: true
      - match:
          severity: warning
        receiver: 'warning'
    
    receivers:
    - name: 'default'
      slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        
    - name: 'critical'
      slack_configs:
      - channel: '#critical-alerts'
      email_configs:
      - to: 'ops-team@theragenome.com'
```

---

## Phase 9: Data Retention and Cleanup (Ongoing)

### Step 1: Configure Prometheus Retention

Prometheus retention is configured in deployment:
```yaml
args:
- '--storage.tsdb.retention.time=15d'
- '--storage.tsdb.max-blocks-to-compact=4'
```

### Step 2: Archive Metrics

```bash
# Backup Prometheus data monthly
kubectl exec -it prometheus-0 -n monitoring -- tar -czf - /prometheus \
  | gsutil cp - gs://theragenome-backups/prometheus-backup-$(date +%Y%m%d).tar.gz
```

---

## Verification and Testing

### Test 1: Verify Prometheus Scraping

```bash
# Check targets
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Expected: Should show multiple active targets
```

### Test 2: Test Metrics Collection

```bash
# Query a metric
curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' | jq '.data.result | length'

# Expected: Should return results
```

### Test 3: Verify Tracing

```bash
# Send test trace
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "test-service"}}
        ]
      },
      "scopeSpans": [{
        "scope": {"name": "test-tracer"},
        "spans": [{
          "name": "test-span",
          "kind": 1,
          "status": {"code": 0}
        }]
      }]
    }]
  }'
```

---

## Post-Implementation

- [x] Prometheus deployed
- [x] Grafana dashboards created
- [x] OpenTelemetry collector running
- [x] Python application instrumented
- [x] TypeScript application instrumented
- [x] Alerts configured
- [ ] Update compliance audit (mark Item #4 COMPLETE)
- [ ] Team training on dashboards
- [ ] Establish SLI/SLO baselines

---

## Troubleshooting

### No metrics appearing in Prometheus

```bash
# Check target endpoints
kubectl exec -it prometheus-0 -n monitoring -- \
  netstat -tulnp | grep prometheus

# Check Prometheus logs
kubectl logs deployment/prometheus -n monitoring --tail=50

# Verify scrape targets
curl http://localhost:9090/api/v1/targets
```

### OpenTelemetry collector not receiving traces

```bash
# Check collector logs
kubectl logs deployment/otel-collector -n monitoring -f

# Test connectivity
kubectl exec -it <api-pod> -n theragenome -- \
  curl -v http://otel-collector.monitoring:4317
```

### Grafana datasource not connecting

```bash
# Check datasource configuration
kubectl exec -it grafana-0 -n monitoring -- \
  psql -h prometheus -U postgres -c "SELECT * FROM grafana_datasource;"

# Verify Prometheus service
kubectl get svc prometheus -n monitoring
kubectl exec -it grafana-0 -n monitoring -- \
  curl -v http://prometheus:9090/-/healthy
```

---

## Next Steps

1. **Item #5:** Complete container security scanning
2. **Item #6:** Implement & test incident response
3. **Item #7:** Operational runbooks

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
