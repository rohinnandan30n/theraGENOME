# TheraGenome API Load Test Suite

This directory contains a comprehensive load testing suite for the TheraGenome API using **Locust**.

## Overview

The load test simulates realistic user behavior with multiple API endpoints and includes:
- Weighted task distribution matching production usage patterns
- Realistic test payloads from genomic/drug interaction data
- Automated SLA monitoring and validation
- Comprehensive HTML and JSON reporting

## Features

### Task Distribution

The `VariantUser` class simulates users performing the following tasks:
- **POST /variant/analyze** (weight: 5) - Variant analysis requests
- **POST /pathogen/analyze** (weight: 3) - Pathogen analysis requests
- **POST /drug/analyze** (weight: 3) - Drug interaction analysis requests
- **GET /reports/{patient_id}** (weight: 2) - Report retrieval requests

### Test Configuration

- **Duration**: 60 seconds
- **Concurrent Users**: 50
- **Ramp-up Rate**: 5 users/second
- **Target Host**: localhost:8000

### SLA Thresholds

The test validates the following SLAs:
- `/variant/analyze`: p95 response time < 2000ms ✓
- `/pathogen/analyze`: p95 response time < 1500ms ✓
- `/drug/analyze`: p95 response time < 1500ms ✓
- **Overall Error Rate**: < 1% ✓

### Realistic Payloads

Test data includes realistic genomic and medical data:
- **5 Variant Analysis Payloads** - Real genetic variants (TP53, BRCA2, KRAS, MSH2, APC)
- **3 Pathogen Analysis Payloads** - Realistic pathogenic profiles (SARS-CoV-2, TB, Malaria)
- **3 Drug Analysis Payloads** - Real drug-gene interactions (Metformin, Warfarin, Clopidogrel)
- **10 Patient IDs** - For report retrieval testing

## Installation

### Prerequisites

```bash
# Install Locust
pip install locust

# Verify installation
locust --version
```

### Setup Test Environment

Ensure the API is running:

```bash
# Terminal 1: Start the API
cd /path/to/theragenome
python -m uvicorn src.api.main:app --host localhost --port 8000

# Terminal 2: Run the load test (from this directory)
python run_load_test.py
```

## Running the Load Test

### Option 1: Using the Run Script (Recommended)

```bash
cd load_tests
python run_load_test.py
```

This will:
1. Launch Locust with predefined parameters
2. Run for 60 seconds with 50 users ramping up at 5/sec
3. Generate SLA validation
4. Produce HTML and JSON reports

### Option 2: Using Locust CLI Directly

```bash
cd load_tests

# Headless mode (automated testing)
locust -f locustfile.py \
  --host http://localhost:8000 \
  -u 50 \
  -r 5 \
  --run-time 60s \
  --headless

# Web UI mode (interactive)
locust -f locustfile.py \
  --host http://localhost:8000 \
  -u 50 \
  -r 5 \
  --run-time 60s
# Then open http://localhost:8089 in browser
```

### Option 3: Programmatic Usage

```python
from locustfile import VariantUser, sla_monitor
from locust import HttpLocust, TaskSet, events

# Use in your test scripts
```

## Reports

### HTML Report

Generated at: `load_test_report.html`

Features:
- ✓ Visual SLA pass/fail status
- ✓ Endpoint performance metrics (RPS, latencies)
- ✓ Response time percentiles (p50, p95, p99)
- ✓ Error rate analysis
- ✓ Test configuration details
- ✓ Professional styling with color-coded results

Open in browser:
```bash
open load_test_report.html  # macOS
xdg-open load_test_report.html  # Linux
start load_test_report.html  # Windows
```

### JSON Report

Generated at: `load_test_results.json`

Contains machine-readable data:
```json
{
  "timestamp": "2026-05-06 12:34:56",
  "duration_seconds": 60,
  "total_users": 50,
  "ramp_up_rate": 5,
  "sla_results": {
    "/api/v1/variant/analyze": {
      "threshold_ms": 2000,
      "p95_ms": 1234.56,
      "met": true
    },
    ...
  },
  "endpoint_metrics": {
    "/api/v1/variant/analyze": {
      "count": 450,
      "failures": 2,
      "error_rate": 0.0044,
      "rps": 7.5,
      "p50_ms": 234.12,
      "p95_ms": 1234.56,
      "p99_ms": 1856.78,
      ...
    }
  }
}
```

## Test Payload Files

### Fixture Location
`../fixtures/load_test_payloads.json`

### Payload Categories

#### Variant Analysis Payloads
```json
{
  "chrom": "17",
  "pos": 41244394,
  "ref": "T",
  "alt": "G",
  "gene": "TP53",
  "hgvs_c": "c.524A>C",
  "hgvs_p": "p.R175H",
  "variant_class": "missense_variant",
  "freq_gnomad": 0.00015,
  "sift_score": 0.02,
  "polyphen_score": 0.95,
  "cadd_score": 28.1,
  "conservation_phylop": 9.5,
  "zygosity": "heterozygous"
}
```

#### Pathogen Analysis Payloads
```json
{
  "pathogen_name": "SARS-CoV-2",
  "lineage": "Omicron-XBB.1.5",
  "mutation_profile": ["S:L452R", "S:F486V", ...],
  "severity_score": 7.2,
  "transmission_score": 8.5,
  "virulence_markers": ["high_transmissibility", ...],
  "prevalence_region": "North America",
  "prevalence_percentage": 45.3
}
```

#### Drug Analysis Payloads
```json
{
  "drug_name": "Metformin",
  "dosage_mg": 1000,
  "frequency": "twice daily",
  "patient_genotype": {
    "CYP2C9": "*1/*1",
    "CYP3A4": "*1/*1",
    ...
  },
  "age_years": 45,
  "weight_kg": 75.0,
  ...
}
```

## SLA Monitoring

### How SLAs Are Tracked

1. **Request Recording** - Every request is recorded with endpoint, response time, and success status
2. **Percentile Calculation** - Response times are sorted; p50, p95, p99 are computed
3. **Threshold Comparison** - Percentiles are compared against defined thresholds
4. **Error Rate** - Total failures / total requests calculated and compared against 1% threshold

### SLA Results Output

The test produces:

```
--- SLA Results ---
✓ PASS | /api/v1/variant/analyze: p95=1234.56ms (threshold: 2000ms)
✓ PASS | /api/v1/pathogen/analyze: p95=1123.45ms (threshold: 1500ms)
✓ PASS | /api/v1/drug/analyze: p95=1289.34ms (threshold: 1500ms)
✓ PASS | error_rate: 0.0044 (threshold: 0.01)

✓ All SLAs passed!
```

### Test Failure Conditions

The test fails and exits with code 1 if:
- Any endpoint's p95 response time exceeds its threshold
- Overall error rate exceeds 1%

## Troubleshooting

### "Connection refused" Error

```
Error: Failed to connect to http://localhost:8000
```

**Solution**: Ensure the API is running on port 8000:
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Start the API if not running
python -m uvicorn src.api.main:app --host localhost --port 8000
```

### "Payloads file not found" Warning

```
Warning: Payloads file not found: .../fixtures/load_test_payloads.json
```

**Solution**: Ensure fixture file exists at correct path:
```bash
# Verify file location
ls -la fixtures/load_test_payloads.json

# Recreate if missing
mkdir -p fixtures
# Copy load_test_payloads.json to fixtures/
```

### High Error Rates

```
✗ FAIL | error_rate: 0.045 > threshold=0.01
```

**Causes**:
- API is under-resourced
- Endpoints not implemented
- Network issues
- API rate limiting active

**Solutions**:
1. Check API logs for errors
2. Verify endpoint implementations
3. Increase test timeout
4. Check network connectivity

### Response Times Exceed Thresholds

**Causes**:
- API performance degraded
- Database slow queries
- Network latency
- Insufficient server resources

**Solutions**:
1. Profile the API code
2. Check database query performance
3. Monitor server resources during test
4. Consider caching/optimization

## Customization

### Modify Test Parameters

Edit `run_load_test.py`:
```python
users = 50  # Increase for more load
spawn_rate = 5  # Users per second
run_time = "60s"  # Test duration
```

### Adjust SLA Thresholds

Edit `locustfile.py`:
```python
SLA_THRESHOLDS = {
    '/api/v1/variant/analyze': 2000,  # Change threshold
    '/api/v1/pathogen/analyze': 1500,
    '/api/v1/drug/analyze': 1500,
}

MAX_ERROR_RATE = 0.01  # 1%
```

### Add More Test Payloads

Edit `fixtures/load_test_payloads.json`:
```json
{
  "variant_analyze": [
    { /* existing payload */ },
    { /* new payload */ }
  ]
}
```

### Change Task Weights

Edit `locustfile.py` VariantUser class:
```python
@task(5)  # Weight 5
def variant_analyze(self):
    ...

@task(3)  # Weight 3
def pathogen_analyze(self):
    ...
```

## Performance Recommendations

### For Production Readiness

1. **Baseline Testing**: Run against production environment with realistic data
2. **Stress Testing**: Gradually increase users to find breaking points
3. **Endurance Testing**: Run for 24+ hours to detect memory leaks
4. **Spike Testing**: Suddenly increase users to test auto-scaling
5. **Chaos Testing**: Introduce failures to test resilience

### Optimal Results

```bash
# Stress test - gradually increase load
locust -f locustfile.py --host http://localhost:8000 \
  -u 200 -r 10 --run-time 5m

# Spike test
locust -f locustfile.py --host http://localhost:8000 \
  -u 500 -r 50 --run-time 2m

# Endurance test
locust -f locustfile.py --host http://localhost:8000 \
  -u 50 -r 5 --run-time 24h
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run Load Tests
  run: |
    pip install locust
    cd load_tests
    python run_load_test.py
    
- name: Check SLA Results
  run: |
    python -c "
    import json
    with open('load_test_results.json') as f:
      data = json.load(f)
    if not data['sla_passed']:
      exit(1)
    "
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://locust.io/docs/basic-concepts.html)
- [Performance Testing Guide](https://en.wikipedia.org/wiki/Load_testing)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review Locust logs
3. Inspect `load_test_results.json` for detailed metrics
4. Check API server logs for backend issues
