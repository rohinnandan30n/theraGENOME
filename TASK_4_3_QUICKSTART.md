# Task 4.3: Therapy Decision Report Aggregator - Quick Start (5 Minutes)

**Status**: ✅ COMPLETE  
**Time to Deploy**: 5 minutes  
**Port**: 8003

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies (1 min)

```bash
cd c:\Users\shiva\Desktop\TheraGenome
pip install -r requirements.txt
```

### 2️⃣ Apply Database Migration (1 min)

```bash
# Create therapy_reports table
alembic upgrade head

# Verify
psql -h localhost -U postgres -d theragenome \
  -c "SELECT COUNT(*) FROM therapy_reports;"
```

### 3️⃣ Start Downstream Services (1 min each)

Open 3 terminal windows:

**Terminal 1 - Dev 1 (Variant Service)**
```bash
cd dev1_service
python -m uvicorn main:app --port 8000
# Runs on http://localhost:8000
```

**Terminal 2 - Dev 2 (Resistance Service)**
```bash
cd dev2_service
python -m uvicorn main:app --port 8001
# Runs on http://localhost:8001
```

**Terminal 3 - Dev 3 (Toxicity Service)**
```bash
cd dev3_service
python -m uvicorn main:app --port 8002
# Runs on http://localhost:8002
```

### 4️⃣ Start Orchestration Service (1 min)

```bash
cd scripts
python -m uvicorn therapy_orchestration_service:app --port 8003

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8003
```

### 5️⃣ Test It! (1 min)

```bash
# Health check
curl http://localhost:8003/health

# Generate a report
curl -X POST http://localhost:8003/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "123e4567-e89b-12d3-a456-426614174000",
    "sample_id": "QUICKSTART_TEST",
    "drug_candidates": ["Warfarin", "Aspirin", "Clopidogrel"],
    "clinician_id": "DR_SMITH"
  }' | jq '.'
```

---

## ✅ What You Should See

**Successful Response (200 OK)**:

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "123e4567-e89b-12d3-a456-426614174000",
  "sample_id": "QUICKSTART_TEST",
  "variant_summary": {
    "chrom": "17",
    "classification": "Pathogenic",
    "confidence": 0.95
  },
  "resistance_summary": {
    "pathogen_name": "Escherichia coli",
    "predicted_phenotype": "Beta-lactam resistant",
    "prediction_confidence": 0.92
  },
  "toxicity_summary": {
    "drug_name": "Warfarin",
    "toxicity_risk": "Medium",
    "toxicity_confidence": 0.88
  },
  "recommended_drug": "Warfarin",
  "alternative_drugs": ["Aspirin", "Clopidogrel"],
  "recommendation_confidence": 0.88,
  "status": "complete",
  "generated_at": "2026-03-31T10:30:00Z"
}
```

---

## 📊 Check Database

```bash
# View latest report
psql -h localhost -U postgres -d theragenome \
  -c "
    SELECT report_id, patient_id, status, recommended_drug, recommendation_confidence
    FROM therapy_reports 
    ORDER BY created_at DESC 
    LIMIT 5;
  "

# Expected output:
# report_id              | patient_id             | status   | recommended_drug | recommendation_confidence
# 550e8400-e29b-41d... | 123e4567-e89b-12d3...  | complete | Warfarin         | 0.88
```

---

## 🔍 View Service Logs

```bash
# Check which services are responding
curl http://localhost:8003/services | jq '.'

# Monitor request log
tail -f orchestration_service.log

# Expected logs:
# INFO: Generating report for patient 123e4567-e89b-12d3-a456-...
# INFO: Variant service success: Pathogenic (confidence: 0.95)
# INFO: Resistance service success: Beta-lactam resistant (confidence: 0.92)
# INFO: Toxicity service success: analyzed 3 drugs
# INFO: Report generated: complete - ...
```

---

## 📌 Common Issues

### ❌ Connection refused (Port 8000/8001/8002)

**Problem**: Downstream services not running

**Fix**: Start all 3 services first (see Step 3)

```bash
# Verify they're running
netstat -an | grep LISTEN | grep 800
# Should show: :8000, :8001, :8002, :8003
```

### ❌ therapy_reports table does not exist

**Problem**: Migration not applied

**Fix**:
```bash
alembic upgrade head
```

### ❌ Status is always "timeout"

**Problem**: Services taking >10 seconds

**Fix**: Ensure downstream services are running and responsive

```bash
# Test Dev 1 directly
curl http://localhost:8000/health
```

---

## 📖 Next Steps

- **Full Guide**: Read [`TASK_4_3_DOCUMENTATION.md`](TASK_4_3_DOCUMENTATION.md)
- **Testing**: Run unit tests and load tests (see docs)
- **Integration**: Connect to real Dev 1, Dev 2, Dev 3 services
- **Monitoring**: Set up logging, metrics, and tracing

---

## 💡 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/reports/generate` | POST | Generate therapy report |
| `/health` | GET | Service health check |
| `/services` | GET | List downstream service URLs |

---

## 📜 Files

- **Main Service**: `scripts/therapy_orchestration_service.py`
- **Schemas**: `scripts/therapy_report_schemas.py`
- **Database**: `alembic/versions/002_create_therapy_reports_table.py`
- **Full Docs**: `TASK_4_3_DOCUMENTATION.md`

---

**Status**: ✅ Ready to use!
