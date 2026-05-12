# TASK 4.6 QUICKSTART — Multi-Omics Ingestion Pipeline

**Deploy in 10 minutes** | **Status**: ✅ PRODUCTION READY

---

## 🚀 QUICK START

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Kafka 3.3+ (optional for events)
- Docker & Docker Compose (recommended)

---

## ⚡ 5-MINUTE SETUP

### Step 1: Install Dependencies (2 min)
```bash
cd c:\Users\shiva\Desktop\TheraGenome

# Install all requirements
pip install -r requirements.txt
```

### Step 2: Apply Database Migrations (1 min)
```bash
# Create tables: rna_results, protein_results
alembic upgrade head
```

### Step 3: Start Kafka (optional, 1 min)
```bash
# If using Docker Compose
docker-compose up -d kafka zookeeper

# Or skip if not using Kafka
```

### Step 4: Start Omics Service (1 min)
```bash
cd scripts
python -m uvicorn omics_ingestion_service:app --port 8006
```

**Service is ready at:** http://localhost:8006

---

## 🧪 TEST IT (5 MINUTES)

### Create Test Data

**RNA-seq Test File:**
```bash
# Create sample count matrix
cat > test_counts.csv << 'EOF'
gene_id,Sample1_Case,Sample2_Case,Sample3_Case,Sample1_Control,Sample2_Control
ENSG00000012048,5000,5200,4800,2000,1950
ENSG00000141510,8000,8500,7800,4000,3950
ENSG00000012049,1000,950,1100,500,480
ENSG00000012050,100,120,90,50,55
ENSG00000000003,2000,2100,1950,1500,1480
EOF
```

**Proteomics Test File:**
```bash
cat > test_proteins.tsv << 'EOF'
Protein IDs	Gene names	LFQ intensity Sample1	LFQ intensity Sample2	Peptides	Sequence coverage [%]	Molecular weight
sp|P08684|CYP3A4	CYP3A4	2000000	1950000	45	92.5	119.6
sp|P11712|CYP2C9	CYP2C9	1500000	1480000	35	88.2	55.7
sp|P00533|EGFR	EGFR	3000000	3100000	78	95.1	134.2
EOF
```

### Upload RNA-seq Data
```bash
PATIENT_ID="550e8400-e89b-12d3-a456-426614174000"

curl -X POST http://localhost:8006/omics/rna-seq/process \
  -F "patient_id=$PATIENT_ID" \
  -F "file=@test_counts.csv" \
  -F "case_samples=Sample1_Case,Sample2_Case,Sample3_Case" \
  -F "control_samples=Sample1_Control,Sample2_Control" \
  | jq '.'

# Expected Response:
# {
#   "status": "processing",
#   "patient_id": "550e8400-e89b-12d3-a456-426614174000",
#   "data_type": "rna-seq",
#   "file": "test_counts.csv",
#   "message": "RNA-seq processing started in background"
# }
```

### Upload Proteomics Data
```bash
curl -X POST http://localhost:8006/omics/proteomics/process \
  -F "patient_id=$PATIENT_ID" \
  -F "file=@test_proteins.tsv" \
  | jq '.'

# Expected Response:
# {
#   "status": "processing",
#   "patient_id": "550e8400-e89b-12d3-a456-426614174000",
#   "data_type": "proteomics",
#   "file": "test_proteins.tsv",
#   "message": "Proteomics processing started in background"
# }
```

### Check Statistics
```bash
# Wait 30 seconds for background processing
sleep 30

curl http://localhost:8006/omics/stats | jq '.'

# Should show:
# {
#   "total_rna_results": 5,           # or more
#   "total_protein_results": 3,       # or more
#   "patients_with_rna": 1,
#   "patients_with_proteomics": 1,
#   "timestamp": "2026-03-31T..."
# }
```

### Query Results
```bash
# Get RNA results
curl "http://localhost:8006/omics/patients/${PATIENT_ID}/rna" | jq '.results[0]'

# Get Protein results
curl "http://localhost:8006/omics/patients/${PATIENT_ID}/proteins" | jq '.results[0]'
```

---

## 📊 EXPECTED RESULTS

### RNA-seq Processing
```json
{
  "gene_id": "ENSG00000012048",
  "gene_name": "BRCA1",
  "log2_fold_change": 1.32,        ← 2^1.32 ≈ 2.5x upregulated
  "padj": 0.0001,                   ← Highly significant
  "significance_flag": "up",
  "effect_size": 1.32,
  "expression_level": "high
"
}
```

### Proteomics Processing
```json
{
  "protein_id": "sp|P08684|CYP3A4",
  "protein_name": "Cytochrome P450 3A4",
  "gene_name": "CYP3A4",
  "log2_intensity": 10.97,          ← log2(2000000) ≈ 10.97
  "protein_class": "enzyme",        ← Drug metabolizing enzyme
  "sequence_coverage": 92.5
}
```

---

## 🔌 CONNECTION POINTS

### Receive From (Upstream)
- **Clinicians**: Upload RNA-seq and proteomics files
- **Lab Info Systems**: Automated file delivery

### Send To (Downstream)
- **PostgreSQL**: Stores rna_results and protein_results
- **Kafka**: publishes omics_processed and toxicity_integration events
- **Dev 3 (Toxicity Guard)**: Receives enriched genomic features

---

## 🛠️ TROUBLESHOOTING

### Issue: "No LFQ intensity columns found"
**Cause**: MaxQuant column naming mismatch  
**Fix**: Ensure columns contain "LFQ intensity" (exact text)  
```bash
# Check column names
head -1 your_file.tsv | tr '\t' '\n' | grep -i lfq
```

### Issue: "PostgreSQL connection refused"
**Cause**: Database not running  
**Fix**:
```bash
# Start PostgreSQL
docker-compose up -d postgres
alembic upgrade head
```

### Issue: "Kafka producer not started"
**Cause**: Kafka not running (non-critical)  
**Fix**: Kafka is optional. Service works without it. To enable:
```bash
docker-compose up -d kafka
```

### Issue: Processing very slow
**Cause**: Large file or slow hardware  
**Solution**: This is normal for first runs. DESeq2 normalization is CPU-intensive.

---

## 📝 TESTING CHECKLIST

- [ ] Requirements installed successfully
- [ ] Migrations applied (`alembic upgrade head`)
- [ ] Service starts without errors (Port 8006)
- [ ] Health check passes: `GET /health`
- [ ] RNA-seq upload accepted
- [ ] Proteomics upload accepted
- [ ] Results stored in database
- [ ] Statistics endpoint works
- [ ] (Optional) Kafka events published

---

## 🎯 WHAT'S HAPPENING BEHIND THE SCENES

1. **File Upload** → FastAPI receives multipart file
2. **Save to Temp** → File written to `/tmp/` with random name
3. **Background Task** → Async processing starts immediately
4. **Normalization** → DESeq2 (RNA) or Log2 (Proteomics)
5. **Analysis** → DE analysis with FDR correction
6. **Database Store** → SQLAlchemy bulk insert
7. **Kafka Publish** → Event to topics
8. **Cleanup** → Temp file deleted
9. **Response**: User gets "processing" status immediately

---

## 📞 API SUMMARY

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/status` | GET | Detailed service status |
| `/omics/rna-seq/process` | POST | Upload RNA-seq data |
| `/omics/proteomics/process` | POST | Upload proteomics data |
| `/omics/patients/{id}/rna` | GET | Query RNA results |
| `/omics/patients/{id}/proteins` | GET | Query protein results |
| `/omics/stats` | GET | Aggregated statistics |

---

##🎊 YOU'RE READY!

✅ All systems operational  
✅ Database configured  
✅ Service running  
✅ Ready to process omics data  

**Next**: Read [`TASK_4_6_DOCUMENTATION.md`](TASK_4_6_DOCUMENTATION.md) for full reference or start uploading data!

---

**Questions?** See [`TASK_4_6_DOCUMENTATION.md`](TASK_4_6_DOCUMENTATION.md) for comprehensive documentation.
