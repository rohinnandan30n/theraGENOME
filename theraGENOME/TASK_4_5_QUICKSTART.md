# Task 4.5: Quick Start — 5-Minute Setup

**Objective:** Deploy Medical LLM narrative generation service  
**Time:** 5 minutes  
**Status:** ✅ Production Ready

---

## 🚀 Option A: Local Ollama (Free, No API Keys)

### Step 1: Install Ollama (2 min)

```bash
# macOS/Windows/Linux
Visit: https://ollama.ai
Download and install

# Start Ollama in background
ollama serve &
```

### Step 2: Pull BioMistral (1 min)

```bash
ollama pull biomistral
# Downloads ~4GB, one-time setup
```

### Step 3: Set Configuration (30 sec)

```bash
# Copy environment template
cp .env.example .env

# Edit .env
USE_OPENAI_API=false
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=biomistral
LLM_TEMPERATURE=0.7
```

### Step 4: Apply Database Migration (1 min)

```bash
alembic upgrade head
```

### Step 5: Start Service (30 sec)

```bash
cd scripts
python -m uvicorn smart_reporter_service:app --port 8005 --reload
```

### Step 6: Test (1 min)

```bash
# Generate narrative
curl -X POST http://localhost:8005/reports/123e4567/narrative/full \
  -H "Content-Type: application/json" \
  -d '{
    "include_shap_explanations": true,
    "clinician_id": "test_clinician"
  }' | jq '.narrative_text' | head -20
```

✅ **Done!** Service running on `http://localhost:8005`

---

## 🚀 Option B: OpenAI API (Best Quality, Requires API Key)

### Step 1: Get OpenAI API Key (1 min)

1. Visit https://platform.openai.com
2. Create account
3. Get API key from Settings → API Keys

### Step 2: Set Configuration (1 min)

```bash
cp .env.example .env

# Edit .env
USE_OPENAI_API=true
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
LLM_TEMPERATURE=0.7
```

### Step 3: Apply Database Migration (1 min)

```bash
alembic upgrade head
```

### Step 4: Start Service (1 min)

```bash
cd scripts
python -m uvicorn smart_reporter_service:app --port 8005
```

### Step 5: Test (1 min)

```bash
curl -X POST http://localhost:8005/reports/123e4567/narrative/full \
  -H "Content-Type: application/json" \
  -d '{
    "include_shap_explanations": true
  }' | jq '.narrative_text'
```

✅ **Done!** Service operational

---

## 📌 Quick Reference

### Endpoints

```
GET  /health                    → Health check
GET  /status                    → Config + status
POST /reports/{id}/narrative    → Stream narrative (SSE)
POST /reports/{id}/narrative/full → Full narrative
GET  /narratives/{id}           → Retrieve narrative
GET  /patients/{id}/narratives  → List narratives
GET  /stats                     → Statistics
```

### Database Check

```bash
# Verify table created
psql -U postgres -d theragenome -c "\dt narrative_reports"

# Count narratives
psql -U postgres -d theragenome -c "SELECT COUNT(*) FROM narrative_reports;"
```

### Service Health

```bash
curl http://localhost:8005/health | jq '.'
```

### Streaming Test

```bash
# See real-time streaming
curl -X POST http://localhost:8005/reports/123e4567/narrative \
  -H "Content-Type: application/json" \
  -d '{"include_shap_explanations": true}'
```

---

## 🐛 Troubleshooting

### "Connection refused" (Ollama)
```bash
# Check Ollama is running
ollama serve &

# Verify connection
curl http://localhost:11434/api/status
```

### "OPENAI_API_KEY not found"
```bash
# Set environment variable
export OPENAI_API_KEY=sk-...
env | grep OPENAI
```

### "Database table not found"
```bash
# Apply migration
alembic upgrade head

# Verify
alembic current
```

### "Port 8005 already in use"
```bash
# Use different port
python -m uvicorn smart_reporter_service:app --port 8006
```

### LLM Response Too Slow
- **Ollama:** GPU recommended (set `OLLAMA_MAX_RETRIES=5`)
- **OpenAI:** Check API rate limits

---

## 📊 Performance Expectations

| Backend | Speed | Quality | Cost |
|---------|-------|---------|------|
| **Ollama (Local)** | 15-30s | Good | Free |
| **Ollama (GPU)** | 8-12s | Good | Free |
| **OpenAI GPT-4** | 8-12s | Excellent | $0.08/req |

---

## ✅ Verification Checklist

- [ ] Service starts without errors
- [ ] `/health` returns 200 OK
- [ ] `/status` shows LLM config
- [ ] Database table `narrative_reports` exists
- [ ] Can generate narrative (streaming or full)
- [ ] Narrative stored in database
- [ ] `/stats` returns metrics

---

## 🎯 Next Steps

1. **Test:** Generate test narratives
2. **Monitor:** Check `/stats` endpoint
3. **Integrate:** Connect to Dev 1, 2, 3 SHAP services
4. **Monitor:** Track quality scores
5. **Deploy:** Move to staging/production

---

## 📞 Support

- **Full Docs:** See `TASK_4_5_DOCUMENTATION.md`
- **Config Help:** Check `.env.example`
- **Database:** `TASK_4_3_DOCUMENTATION.md` (therapy_reports)
- **API Schema:** `openapi_specs/`

---

**Status: READY FOR IMMEDIATE USE** ✅
