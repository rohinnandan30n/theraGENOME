# Dev 3 — Drug Safety & Toxicity API

## Overview

The **Drug Safety & Toxicity API** is a comprehensive service for clinical drug safety decisions, pharmacogenomics (PGx) recommendations, drug-drug interaction (DDI) checking, and adverse event tracking. It integrates with **PharmGKB**, **DrugBank**, and **FDA FAERS** for real-world evidence.

## Key Features

✅ **Toxicity Prediction** — ML-based toxicity scoring for compounds (SMILES input)  
✅ **Pharmacogenomics (PGx)** — Gene-drug interaction recommendations from PharmGKB  
✅ **Drug-Drug Interactions (DDI)** — Graph-based interaction checking (PostgreSQL + Neo4j)  
✅ **Adverse Events (FAERS)** — FDA adverse event reports via openFDA API  
✅ **Caching** — Redis caching for fast lookups  
✅ **Kafka Integration** — Consumer for `omics_processed` events from Dev 4  
✅ **ETL Scripts** — Automated syncing of PharmGKB, DrugBank, and FAERS data

---

## Project Structure

```
src/
├── api/
│   ├── drugs.py              # Main API routes
│   ├── schemas.py            # Request/response Pydantic models
├── db/
│   ├── connection.py         # PostgreSQL connection + session management
│   ├── repository.py         # Base CRUD repository
│   ├── drug_safety_repository.py  # Domain repositories (Drug, PGx, DDI, AE)
│   └── neo4j_ddi_graph.py   # Neo4j graph operations for DDI
├── external_apis/
│   ├── pharmgkb_api.py       # PharmGKB client
│   ├── drugbank_api.py       # DrugBank client (DDI)
│   └── faers_api.py          # FDA FAERS client
├── cache/
│   └── redis_cache.py        # Redis caching utilities
├── messaging/
│   ├── kafka_consumer.py     # Kafka consumer for omics_processed
│   └── kafka_producer.py     # Kafka producer for results
├── ml/
│   └── toxicity_model.py     # ML model loading + inference
├── schemas/
│   ├── drug_schema.py        # SQLAlchemy ORM models
│   └── pgx_schema.py         # Pydantic PGx models
├── main.py                   # FastAPI app entry point
└── config.py                 # Environment configuration

scripts/
├── sync_pharmgkb_drugbank.py # ETL: Sync drugs + PGx
└── sync_faers.py             # ETL: Sync adverse events
```

---

## API Endpoints

### 1. **Predict Toxicity**
```bash
POST /api/v1/drugs/predict-toxicity
Content-Type: application/json

{
  "compound_smiles": "CC(C)Cc1ccc(cc1)C(C)C(O)=O",
  "patient_id": "patient_001"
}

Response:
{
  "compound_smiles": "...",
  "patient_id": "patient_001",
  "toxicity_score": 0.32,
  "risk_level": "low",
  "shap_values": { ... }
}
```

### 2. **Get PGx Recommendation**
```bash
GET /api/v1/drugs/pgx?gene=CYP2C9&drug=warfarin

Response:
{
  "gene": "CYP2C9",
  "drug": "warfarin",
  "recommendation": "Patients with CYP2C9 *2/*2 or *2/*3 variants require 30-50% dose reduction",
  "evidence_level": "1A",
  "phenotype_categories": ["Warfarin metabolism"],
  "source": "PharmGKB",
  "url": "https://www.pharmgkb.org/..."
}
```

### 3. **Check Drug-Drug Interaction**
```bash
POST /api/v1/drugs/ddi
Content-Type: application/json

{
  "drug_a": "warfarin",
  "drug_b": "aspirin"
}

Response:
{
  "drug_a": "warfarin",
  "drug_b": "aspirin",
  "interaction_found": true,
  "interaction_type": "Pharmacodynamic",
  "severity": "Major",
  "description": "Aspirin increases anticoagulant effect, raising bleeding risk",
  "severity_level": 3,
  "source": "local_knowledge_base"
}
```

### 4. **Fetch FAERS Adverse Events**
```bash
GET /api/v1/drugs/faers/aspirin?limit=10

Response:
{
  "drug": "aspirin",
  "total_results": 45203,
  "returned": 10,
  "events": [
    {
      "report_id": "12345678",
      "date": "2024-01-15",
      "serious": true,
      "drugs": ["aspirin"],
      "reactions": ["Gastrointestinal hemorrhage", "Severe bleeding"],
      "outcomes": ["Hospitalization"]
    }
  ],
  "source": "FDA-FAERS (openFDA)"
}
```

### 5. **Health Check**
```bash
GET /health

Response:
{
  "status": "ok",
  "service": "dev3-drug-safety-toxicity-api"
}
```

---

## Database Schema

### PostgreSQL Tables

**drugs**
```sql
id (PK) | name | drugbank_id | description | category | created_at | updated_at
```

**pgx_recommendations**
```sql
id | gene | drug_id (FK) | recommendation | evidence_level | phenotype_categories | source | created_at
```

**drug_drug_interactions**
```sql
id | drug_a_id (FK) | drug_b_id (FK) | interaction_type | severity | description | source | created_at
```

**adverse_events**
```sql
id | drug_id (FK) | event_type | event_count | seriousness_level | outcomes (JSON) | source | created_at
```

### Neo4j Graph Structure (DDI Graph)

**Nodes:**
- `Drug {id, name, drugbank_id}`

**Edges:**
- `(Drug)-[:INTERACTS_WITH]→(Drug) {interaction_type, severity, description}`

---

## Setup & Installation

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

pip install -r requirements.txt
```

### 2. Set Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

**.env template:**
```env
APP_ENV=development
APP_PORT=8003

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/theragenome

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_OMICS_PROCESSED=omics_processed

# External APIs
PHARMGKB_API_KEY=
DRUGBANK_API_KEY=

# Service URLs
DEV1_SERVICE_URL=http://localhost:8001

# ML Model
TOXICITY_MODEL_PATH=models/toxicity_model.joblib
```

### 3. Initialize Databases

**PostgreSQL:**
```bash
python -c "
import asyncio
from src.db.connection import init_db
asyncio.run(init_db())
"
```

**Neo4j:**
```bash
python -c "
import asyncio
from src.db.neo4j_ddi_graph import Neo4jDDIGraph

async def init():
    graph = Neo4jDDIGraph()
    await graph.init_schema()
    await graph.close()

asyncio.run(init())
"
```

---

## Running the Service

### Development Server
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Production Server
```bash
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8003
```

---

## ETL Scripts

### Sync PharmGKB & DrugBank Data
```bash
python scripts/sync_pharmgkb_drugbank.py
```

**What it does:**
- Fetches drugs from PharmGKB API
- Syncs PGx clinical annotations
- Stores in PostgreSQL

### Sync FDA FAERS Adverse Events
```bash
python scripts/sync_faers.py
```

**What it does:**
- Fetches adverse events via openFDA API
- Aggregates by event type & drug
- Stores in PostgreSQL

**Schedule (Recommended):**
- PharmGKB sync: Weekly
- FAERS sync: Weekly or Daily for high-priority drugs

---

## Caching Strategy

**Redis Keys:**
```
pgx:{gene}:{drug}           # PGx recommendations (TTL: 24h)
ddi:{drug_a}:{drug_b}       # DDI lookups (TTL: 24h)
faers:{drug_name}           # FAERS data (TTL: 24h)
drug:{drug_id}              # Drug info (TTL: 7d)
```

**Bypass cache (if needed):**
```bash
# Clear Redis cache
redis-cli FLUSHDB
```

---

## Kafka Integration

### Consuming: `omics_processed` Topic

**Expected Message Format:**
```json
{
  "patient_id": "P001",
  "drug_list": ["aspirin", "metformin"],
  "gene_expression": {
    "CYP2C9": 1.2,
    "CYP3A4": 0.8
  }
}
```

**Consumer:** Automatically starts when service starts
- Triggers PGx lookups for each gene + drug
- Checks DDI for drug combinations
- Runs toxicity predictions
- Stores results

### Emitting: `drug_safety_results` Topic (optional)

Results can be emitted back for audit logging:
```json
{
  "patient_id": "P001",
  "drug_name": "aspirin",
  "toxicity_score": 0.32,
  "pgx_results": { ... },
  "ddi_warnings": [ ... ]
}
```

---

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

---

## Logging

Logs are output to stdout with DEBUG level in development:
```
[2024-03-31 10:15:42 INFO] Cache hit for PGx: CYP2C9+warfarin
[2024-03-31 10:15:43 INFO] Fetching FAERS data for aspirin
[2024-03-31 10:15:50 INFO] Emitted drug safety result for patient P001: metformin
```

Configure log level in `src/config.py` or via environment variable `LOG_LEVEL`.

---

## Common Issues & Troubleshooting

### **PostgreSQL Connection Error**
```
psycopg.OperationalError: could not connect to server
```
→ Ensure PostgreSQL is running:
```bash
brew services start postgresql  # macOS
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
```

### **Neo4j Connection Error**
```
neo4j.exceptions.ServiceUnavailable: Could not connect
```
→ Ensure Neo4j is running:
```bash
docker run -d -p 7687:7687 -e NEO4J_INITIAL_PASSWORD=password neo4j
```

### **Redis Connection Error**
```
redis.exceptions.ConnectionError: Connection refused
```
→ Start Redis:
```bash
brew services start redis  # macOS
docker run -d -p 6379:6379 redis
```

### **Kafka Consumer Not Starting**
→ Check Kafka is running and topic exists:
```bash
kafka-topics --list --bootstrap-server localhost:9092
kafka-topics --create --topic omics_processed --bootstrap-server localhost:9092
```

---

## Related Services

- **Dev 1 — Genomics & Variant API** (port 8001)
- **Dev 2 — Pathogen & Resistance API** (port 8002)
- **Dev 3 — Drug Safety & Toxicity API** (port 8003) ← **You are here**
- **Dev 4 — Core Platform & Orchestration** (port 8004)

---

## Performance Metrics

Expected response times (cached):
- `POST /predict-toxicity`: **< 50ms**
- `GET /pgx`: **< 30ms**
- `POST /ddi`: **< 20ms**
- `GET /faers/{drug}`: **< 100ms**

---

## Contributing

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) code style
- Add tests for new features
- Document API changes in this README
- Run `pytest` before committing

---

## License

Part of the TheraGenome backend project.
