## Task 4.4 Quick Start - Get Running in 5 Minutes

**Updated:** March 31, 2026

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites (already installed)
```bash
✅ Python 3.9+
✅ Docker & Docker Compose
✅ PostgreSQL (in container)
✅ All dependencies (in requirements.txt)
```

### Step 2: Start Services (1 minute)
```bash
cd c:\Users\shiva\Desktop\TheraGenome

# Start all containers
docker-compose up -d

# Verify running
docker-compose ps
```

**Check these are running:**
- ✅ `flower-server` (port 8080)
- ✅ `fl-admin-service` (port 8004)
- ✅ `postgres` (port 5432)
- ✅ `redis` (port 6379)

### Step 3: Apply Database Migration (1 minute)
```bash
# Initialize database
alembic upgrade head

# Verify fl_rounds table exists
psql postgresql://postgres:postgres@localhost/theragenome -c "\dt fl_rounds"
```

### Step 4: Test System Health (1 minute)
```bash
# Check admin service
curl http://localhost:8004/health

# Expected response:
# {"status":"healthy","service":"FL Admin Service","timestamp":"..."}

# Check full system status
curl http://localhost:8004/status | jq '.'

# Expected:
# {
#   "status": "healthy",
#   "flower_server_status": "online",
#   "database_status": "online",
#   "min_clients_required": 3,
#   "current_round": null
# }
```

### Step 5: Trigger First Training Round (1 minute)
```bash
# Start round 1
curl -X POST http://localhost:8004/fl/start-round \
  -H "Content-Type: application/json" \
  -d '{
    "round_number": 1,
    "max_clients": 10,
    "timeout_seconds": 300,
    "description": "Initial training round"
  }'

# Expected response:
# {
#   "round_id": "round_1_1711900200.123",
#   "round_number": 1,
#   "status": "initiated",
#   "max_clients": 10,
#   "started_at": "2026-03-31T10:30:00.123456Z",
#   "message": "Round 1 triggered successfully"
# }
```

### Step 6: Monitor Progress (1 minute)
```bash
# Check round status
curl http://localhost:8004/fl/rounds/latest | jq '.status'

# View participation stats
curl http://localhost:8004/fl/stats/participation | jq '.'

# View performance trends
curl http://localhost:8004/fl/stats/performance | jq '.'
```

---

## ✅ Success Criteria

After 5-minute setup, you should see:

✅ Admin service healthy (curl /health returns 200)
✅ Database connected (curl /status shows "online")
✅ Round triggered successfully (returns round_id)
✅ Can query metrics (curl /fl/stats/participation returns json)

---

## 🏥 Optional: Run Hospital Simulator (10 minutes)

Simulate 5 hospitals participating in training:

```bash
# Terminal 2: Start 5 simulated hospital clients
python scripts/fl_client_node.py 5

# Output:
# 🏥 Starting 5 federated learning clients...
# 🏥 Client node_0 (Boston Medical Center) initialized...
# 🏥 Client node_1 (Johns Hopkins Hospital) initialized...
# ...

# The simulator will:
# - Create local training data for each hospital
# - Regularly log metrics to database
# - Simulate different data distributions
```

---

## 📊 Endpoints Quick Reference

| Endpoint | Purpose | Command |
|----------|---------|---------|
| `GET /health` | Health check | `curl http://localhost:8004/health` |
| `GET /status` | System status | `curl http://localhost:8004/status \| jq` |
| `POST /fl/start-round` | Trigger round | `curl -X POST http://localhost:8004/fl/start-round -d '{...}'` |
| `GET /fl/rounds/latest` | Latest round | `curl http://localhost:8004/fl/rounds/latest \| jq` |
| `GET /fl/stats/participation` | Hospital stats | `curl http://localhost:8004/fl/stats/participation \| jq` |
| `GET /fl/stats/performance` | Loss/accuracy trends | `curl http://localhost:8004/fl/stats/performance \| jq` |

---

## 🔍 Verify Database Setup

```bash
# Connect to database
psql postgresql://postgres:postgres@localhost/theragenome

# List tables
\dt

# Check fl_rounds table
SELECT * FROM fl_rounds;

# Exit
\q
```

---

## 🐛 Troubleshooting

### Service Not Running
```bash
# Check container logs
docker-compose logs flower-server
docker-compose logs fl-admin-service

# Restart Services
docker-compose restart
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Reset database
alembic downgrade base
alembic upgrade head
```

### Migration Failed
```bash
# Check migration history
alembic history

# Mark migration as applied
alembic stamp head

# Try upgrade again
alembic upgrade head
```

---

## 📖 Read Next

- **Complete Guide:** [`TASK_4_4_DOCUMENTATION.md`](TASK_4_4_DOCUMENTATION.md) (30 min)
- **Implementation Details:** [`TASK_4_4_FINAL_SUMMARY.md`](TASK_4_4_FINAL_SUMMARY.md) (15 min)
- **Completion Report:** [`TASK_4_4_COMPLETION_REPORT.md`](TASK_4_4_COMPLETION_REPORT.md) (10 min)

---

## 🚀 Next Steps

1. ✅ Get services running (5 min - *you're here*)
2. 🔄 Read complete documentation
3. 🔄 Integrate real hospital client nodes
4. 🔄 Configure differential privacy settings
5. 🔄 Set up monitoring dashboards (Grafana)
6. 🔄 Run production training loops

---

**Status:** Ready to deploy! 🎉
