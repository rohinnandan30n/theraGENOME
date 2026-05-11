# theraGENOME API - Development Guide

Complete guide for developers setting up and working with the theraGENOME API locally.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Environment](#development-environment)
3. [Database Setup](#database-setup)
4. [Running the API](#running-the-api)
5. [Testing](#testing)
6. [API Documentation](#api-documentation)
7. [Debugging](#debugging)
8. [Common Issues](#common-issues)

## Quick Start

### 1. Clone and Setup (5 minutes)

```bash
# Clone repository
cd theraGENOME

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Services (3 minutes)

```bash
# Start Docker containers
docker-compose up -d postgres redis

# Wait for services to be healthy
docker-compose ps
```

### 3. Run API (2 minutes)

```bash
# Start development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open Documentation

- Swagger UI: http://localhost:8000/api/docs
- API: http://localhost:8000

## Development Environment

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- A code editor (VS Code recommended)
- Postman or similar API client (optional, but useful)

### Project Structure

```
theraGENOME/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   ├── security.py          # JWT & auth
│   │   ├── routes/
│   │   │   └── therapist_routes.py
│   │   └── services/
│   │       └── therapist_service.py
│   └── database/
│       └── models.py            # SQLAlchemy models
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_security.py
│   └── test_therapist_routes.py
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

### IDE Setup (VS Code)

**Recommended Extensions:**
```
- Python (Microsoft)
- Pylance
- FastAPI
- SQL Database Explorer
- Docker
- REST Client (for API testing)
```

**VS Code Settings (.vscode/settings.json):**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

## Database Setup

### Initialize with Docker

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for PostgreSQL to be ready (check health)
docker-compose ps postgres

# You should see (healthy) status
```

### Apply Migrations

```bash
# If using Alembic (when set up)
alembic upgrade head

# Create tables manually (for now)
cd src/database
python -c "from models import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Verify Database Connection

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d genomic_db

# List tables
\dt

# Exit
\q
```

### Access via pgAdmin (Optional)

1. Navigate to: http://localhost:5050
2. Login with email/password from `.env`
3. Add server: host=postgres, port=5432, user=postgres, password=password

## Running the API

### Development Mode (Hot Reload)

```bash
# Terminal 1: Start all services
docker-compose up -d

# Terminal 2: Run API with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# The server auto-reloads when you save files
```

### Production Mode

```bash
# Build Docker image
docker build -t theragenome-api .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=your-secret \
  theragenome-api

# Or with gunicorn
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Port Configuration

Default ports:
- API: 8000 (http://localhost:8000)
- PostgreSQL: 5432
- Redis: 6379
- pgAdmin: 5050
- Swagger Docs: 8000/api/docs

Change in `.env`:
```
APP_PORT=8001
DB_PORT=5433
REDIS_PORT=6380
```

## Testing

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=src/api --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Test security module
pytest tests/test_security.py -v

# Test specific function
pytest tests/test_security.py::test_verify_admin_token_valid -v

# Test with async output
pytest -v -s tests/

# Run only fast tests
pytest -m "not slow"
```

### Testing with Different Scenarios

```bash
# Test without database
pytest --cov=src/api tests/ -k "not integration"

# Test with specific marker
pytest -m asyncio

# Test specific file pattern
pytest tests/test_*.py
```

### Writing Tests

**Example Test Structure:**
```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Provide test client."""
    from src.api.main import app
    return TestClient(app)

@pytest.mark.asyncio
async def test_endpoint(client):
    """Test an endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## API Documentation

### Interactive Docs

**Swagger UI** (Recommended):
- URL: http://localhost:8000/api/docs
- Try API endpoints directly
- See request/response examples
- Download OpenAPI spec

**ReDoc**:
- URL: http://localhost:8000/api/redoc
- Read-only documentation
- Better for reading

### Manual API Testing

**Using curl:**
```bash
# Get therapists
curl -X GET http://localhost:8000/api/v1/therapists/ \
  -H "Authorization: Bearer valid.jwt.token"

# Create therapist
curl -X POST http://localhost:8000/api/v1/therapists/ \
  -H "Authorization: Bearer valid.jwt.token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Test",
    "email": "test@example.com",
    "license_no": "TH-001",
    "specialization": "Test"
  }'
```

**Using Postman** (or similar):
1. Import API from: http://localhost:8000/api/openapi.json
2. Set Authorization header: `Bearer <token>`
3. Test endpoints with request builder

## Debugging

### Debug Mode

**Using print statements:**
```python
# In your code
logger.debug(f"Variable value: {value}")

# Watch logs in terminal
# Messages with DEBUG level will appear
```

**VS Code Debugger:**

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.api.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

Then press F5 to start debugging.

### Viewing Logs

```bash
# Watch logs in real-time
tail -f logs/app.log

# Filter by level
grep "ERROR" logs/app.log
grep "DEBUG" logs/app.log

# Last 100 lines
tail -100 logs/app.log
```

### Database Debugging

```bash
# Execute SQL directly
docker exec -it theragenome_postgres psql -U postgres -d genomic_db

# Example queries
SELECT * FROM therapists;
SELECT * FROM therapy_sessions;
SELECT COUNT(*) FROM therapists;

# Exit
\q
```

### API Debugging

**Check request/response:**
```python
# Enable verbose logging in main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Network inspection:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Make API request
4. Inspect request/response headers and body

## Common Issues

### Issue: "Connection refused" on database

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Start if not running
docker-compose up -d postgres

# Wait for health check
docker-compose logs postgres
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port
lsof -i :8000  # Or :5432, :6379

# Kill process
kill -9 <PID>

# Or change port in .env
APP_PORT=8001
```

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
pip list | grep fastapi
```

### Issue: Authentication errors

**Solution:**
```bash
# Verify token format (must have 3 parts)
# Expected: header.payload.signature

# Check Authorization header
Authorization: Bearer <token>

# Use token with proper format in tests
valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token.signature"
```

### Issue: Tests fail with import errors

**Solution:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run pytest with proper path
pytest -v tests/

# If still failing, check sys.path in conftest.py
```

### Issue: Changes not reflected after save

**Solution:**
```bash
# Restart dev server (Ctrl+C, then run again)
uvicorn src.api.main:app --reload

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +

# Reinstall in editable mode
pip install -e .
```

## Performance Optimization

### Monitor API Performance

```bash
# Install monitoring tool
pip install locust

# Create load test script (locustfile.py)
from locust import HttpUser, task

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

### Database Query Optimization

```python
# Enable SQL logging in development
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Useful Development Commands

```bash
# Format code
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/

# Dependency security check
safety check

# View installed packages
pip list

# Create requirements from installed packages
pip freeze > requirements.txt

# Generate API documentation
# (Automatic at http://localhost:8000/api/docs)
```

---

**Last Updated:** 2024-01-20
**For Issues:** Create an issue on GitHub or contact development team
