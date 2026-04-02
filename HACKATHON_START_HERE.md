# 🚀 HACKATHON 2-DAY SPRINT - EXECUTION COMMANDS

**Status: ALL FILES CREATED ✅**
- ✅ api_server.py (FastAPI backend with variant classification)
- ✅ dashboard.html (Vue.js interactive UI)
- ✅ Dockerfile.hackathon (Docker image builder)
- ✅ requirements_hackathon.txt (Python dependencies)
- ✅ demo_variants.json (Sample variant data)
- ✅ k8s/hackathon-deployment.yaml (Kubernetes manifests)

---

## ⚡ FAST-TRACK: START HERE (5 MINUTES)

### STEP 1: Install Python Dependencies (2 min)

Open PowerShell and run:

```powershell
cd C:\Users\Rohin Nandan\Theragenome
pip install -r requirements_hackathon.txt
```

Expected output: Successfully installed fastapi, uvicorn, psycopg2-binary, python-multipart

---

### STEP 2: Verify Database Tables Exist (1 min)

Before running, verify these tables exist:

```sql
-- If tables don't exist, run in PostgreSQL:

CREATE TABLE IF NOT EXISTS variants (
    id SERIAL PRIMARY KEY,
    gene VARCHAR(100),
    mutation VARCHAR(100),
    classification VARCHAR(50),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100),
    resource VARCHAR(255),
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### STEP 3: Run Backend Locally (Test First)

```powershell
cd C:\Users\Rohin Nandan\Theragenome
python api_server.py
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Server is now running!**

---

### STEP 4: Test in Browser (New PowerShell Window)

While server is running, go to: **http://localhost:8000**

You should see:
- 🧬 **TheraGenome** header
- ✓ **System Healthy** badge
- 🔒 **HIPAA Encrypted & Audited** badge
- Upload area with "Load Demo Data" button

Click **"Load Demo Data"** → Watch it process 5 variants in real-time ✨

---

## 📦 DOCKER & KUBERNETES (Next Steps)

### STEP 5: Build Docker Image

```powershell
cd C:\Users\Rohin Nandan\Theragenome

# Build the image
docker build -f Dockerfile.hackathon -t theragenome/hackathon:latest .

# Verify it built
docker images | grep hackathon
```

Expected: theragenome/hackathon with "latest" tag

---

### STEP 6: Deploy to Kubernetes

```powershell
# Apply the deployment
kubectl apply -f k8s/hackathon-deployment.yaml

# Check status
kubectl get pods -n staging

# Watch it come up (Ctrl+C to exit)
kubectl logs -f deployment/theragenome-hackathon -n staging
```

Expected: Pods starting, health checks passing

---

### STEP 7: Port-Forward to Test K8s Deployment

```powershell
# In a new PowerShell window, port-forward the service
kubectl port-forward svc/theragenome-hackathon-svc 8000:8000 -n staging
```

Then go to: **http://localhost:8000** again

Everything should work exactly the same! 🎉

---

## 🔄 QUICK COMMANDS

### Check if Backend is Running
```bash
curl http://localhost:8000/health
```

### Process Demo Data Programmatically
```bash
curl -X POST http://localhost:8000/api/v1/classify `
  -F "file=@demo_variants.json"
```

### View Results
```bash
curl http://localhost:8000/api/v1/results | jq
```

### View Audit Logs (Compliance Proof)
```bash
curl http://localhost:8000/api/v1/audit-log | jq
```

---

## ✅ SUCCESS CHECKLIST

By Tomorrow (Apr 3) EOD:

- [ ] Backend runs without errors
- [ ] Dashboard loads in browser
- [ ] "Load Demo Data" processes 5 variants
- [ ] Results table shows classifications (PATHOGENIC, BENIGN, VUS)
- [ ] Stats show counts correctly
- [ ] Docker image builds successfully
- [ ] Pods deploy to Kubernetes
- [ ] K8s health checks passing
- [ ] Can access app via kubectl port-forward

---

## 🏆 THURSDAY DEMO (Apr 4 @ 10 AM)

### Live Demo Script

1. **Show the problem** (30 sec)
   - "4M patients get genomic sequencing yearly"
   - "95% of variants never analyzed"
   - "Need fast, secure, compliant platform"

2. **Show the solution** (1 min)
   - "TheraGenome: Real-time variant classification"
   - "Secure on Kubernetes + PostgreSQL"
   - "HIPAA audit logs + encryption"

3. **Live demo** (3 min)
   - Open browser: http://localhost:8000
   - Click "Load Demo Data"
   - Show results processing in real-time
   - Show classifications (pathogenic/benign/VUS)
   - Show drug interactions
   - Show audit logs for compliance proof

4. **Infrastructure proof** (1 min)
   - Show K8s pods running: `kubectl get pods -n staging`
   - Show health metrics: `kubectl logs deployment/theragenome-hackathon -n staging`
   - Show HTTPS lock icon in browser

5. **Impact** (30 sec)
   - "Clinicians get actionable insights instantly"
   - "Patients get better diagnoses faster"
   - "Healthcare systems reduce costs"

---

## 🛠️ TROUBLESHOOTING

### Database Connection Error
**Problem:** `psycopg2.OperationalError: could not connect to server`

**Fix:**
```powershell
# Check PostgreSQL is running
pg_isready

# Or manually set DB connection string
$env:DB_HOST = "localhost"
$env:DB_USER = "app_user"
$env:DB_NAME = "theragenome"
```

### Port Already in Use (8000)
**Problem:** `Address already in use`

**Fix:**
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
python api_server.py --port 8001
```

### Docker Image Not Found in K8s
**Problem:** `ImagePullBackOff` in kubectl

**Fix:**
```powershell
# Use imagePullPolicy: Never to use local image
# (Already set in hackathon-deployment.yaml)

# Or load image into minikube
minikube image load theragenome/hackathon:latest

# Then re-apply deployment
kubectl apply -f k8s/hackathon-deployment.yaml
```

---

## 📊 FILE LOCATIONS

All files in: **C:\Users\Rohin Nandan\Theragenome\**

- `api_server.py` ← Backend API
- `dashboard.html` ← Frontend UI  
- `Dockerfile.hackathon` ← Docker build
- `requirements_hackathon.txt` ← Dependencies
- `demo_variants.json` ← Sample data
- `k8s/hackathon-deployment.yaml` ← K8s manifests

---

## 🎯 NEXT IMMEDIATE ACTIONS

1. **RIGHT NOW**: `pip install -r requirements_hackathon.txt`
2. **THEN**: `python api_server.py`
3. **THEN**: Open browser to http://localhost:8000
4. **THEN**: Click "Load Demo Data"
5. **TOMORROW**: Build Docker & deploy K8s
6. **THURSDAY**: 🏆 DEMO AT 10 AM

---

**You got this! 🚀**

Start with Step 1 above and let me know when you hit any snags!

