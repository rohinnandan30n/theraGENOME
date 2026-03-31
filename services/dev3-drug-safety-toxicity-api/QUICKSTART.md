# Quick Start Guide — Dev 3 Drug Safety API

Get the Dev 3 service up and running in 5 minutes!

## 🚀 Option 1: Docker Compose (Recommended)

### Prerequisites
- Docker & Docker Compose installed

### Steps

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```
   
   This starts:
   - PostgreSQL (port 5432)
   - Neo4j (port 7687, UI: 7474)
   - Redis (port 6379)
   - Kafka (port 9092)

2. **Wait for healthchecks (30-60 seconds):**
   ```bash
   docker-compose logs -f
   ```

3. **Check all services are healthy:**
   ```bash
   docker-compose ps
   ```

4. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

5. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults should work with Docker)
   ```

6. **Initialize databases:**
   ```bash
   python -c "
   import asyncio
   from src.db.connection import init_db
   asyncio.run(init_db())
   print('✅ PostgreSQL schema created')
   "
   ```

7. **Start the API:**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
   ```

8. **Test the API:**
   ```bash
   # In another terminal
   curl http://localhost:8003/health
   # Should return: {"status":"ok","service":"dev3-drug-safety-toxicity-api","version":"0.1.0"}
   ```

9. **Open API docs:**
   ```
   http://localhost:8003/docs
   ```

---

## 🔧 Option 2: Manual Local Setup

### Prerequisites
- PostgreSQL 14+
- Neo4j 5.0+
- Redis 7.0+
- Python 3.10+
- Kafka (optional for basic testing)

### Steps

1. **Create Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cat > .env << EOF
   APP_ENV=development
   APP_PORT=8003
   LOG_LEVEL=INFO
   
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/theragenome
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password
   REDIS_URL=redis://localhost:6379/0
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   TOXICITY_MODEL_PATH=models/toxicity_model.joblib
   EOF
   ```

3. **Start PostgreSQL:**
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   
   # Or Docker
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:16
   ```

4. **Start Neo4j:**
   ```bash
   docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5.15
   ```

5. **Start Redis:**
   ```bash
   # macOS
   brew services start redis
   
   # Or Docker
   docker run -d -p 6379:6379 redis:7
   ```

6. **Initialize databases:**
   ```bash
   python -c "
   import asyncio
   from src.db.connection import init_db
   asyncio.run(init_db())
   print('✅ PostgreSQL initialized')
   "
   ```

7. **Start the API:**
   ```bash
   uvicorn src.main:app --reload
   ```

---

## 📝 First Test Requests

### 1. Health Check
```bash
curl http://localhost:8003/health
```

### 2. Predict Toxicity
```bash
curl -X POST http://localhost:8003/api/v1/drugs/predict-toxicity \
  -H "Content-Type: application/json" \
  -d '{
    "compound_smiles": "CC(C)Cc1ccc(cc1)C(C)C(O)=O",
    "patient_id": "P001"
  }'
```

### 3. Get PGx Recommendation
```bash
curl "http://localhost:8003/api/v1/drugs/pgx?gene=CYP2C9&drug=warfarin"
```

### 4. Check Drug-Drug Interaction
```bash
curl -X POST http://localhost:8003/api/v1/drugs/ddi \
  -H "Content-Type: application/json" \
  -d '{"drug_a": "warfarin", "drug_b": "aspirin"}'
```

### 5. Get FAERS Adverse Events
```bash
curl "http://localhost:8003/api/v1/drugs/faers/aspirin?limit=5"
```

---

## 🔄 Sync Data (Optional)

Load sample data into your database:

```bash
# Sync PharmGKB + DrugBank data
python scripts/sync_pharmgkb_drugbank.py

# Sync FDA FAERS adverse events
python scripts/sync_faers.py
```

---

## 🛑 Cleanup

### Stop Docker containers:
```bash
docker-compose down
```

### Remove data volumes (⚠️ deletes database):
```bash
docker-compose down -v
```

### Stop Python environment:
```bash
deactivate
```

---

## 📊 View Services

| Service | URL | Info |
|---------|-----|------|
| FastAPI Docs | http://localhost:8003/docs | Interactive API docs |
| Neo4j Browser | http://localhost:7474 | Graph DB explorer (user: neo4j, pass: password) |
| Kafka Topics | N/A | Use `kafka-topics` CLI |

---

## 🐛 Troubleshooting

**Port already in use:**
```bash
# Find process using port 8003
lsof -i :8003

# Or change port in config
```

**Database connection refused:**
```bash
# Check if PostgreSQL is running
psql -U user -h localhost -d theragenome

# Or use Docker
docker ps | grep postgres
```

**Redis connection error:**
```bash
# Test Redis
redis-cli ping  # Should return "PONG"
```

**Kafka not available:**
```bash
# List Kafka broker
kafka-broker-api-versions --bootstrap-server localhost:9092
```

---

## 📚 Next Steps

1. ✅ **Review README.md** for comprehensive API documentation
2. ✅ **Explore /docs** endpoint for interactive API testing
3. ✅ **Read API endpoint details** in README
4. ✅ **Set up IDE debugging** in VS Code / PyCharm
5. ✅ **Run unit tests** with `pytest tests/`

---

## 🤝 Support

- **Issues?** Check README.md troubleshooting section
- **Architecture questions?** See TheraGenome_Backend_Task_Breakdown.docx
- **Related services:** Dev 1 (8001), Dev 2 (8002), Dev 4 (8004)

Good luck! 🚀
