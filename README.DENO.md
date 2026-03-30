# Deno Variant Results API - Task 1.4

Complete REST API for storing, retrieving, and auditing variant classification results per patient.

## Overview

This is a **Deno TypeScript** REST API that manages variant pathogenicity classification results with:
- Complete result history per patient
- Soft-delete support with audit logging
- Pagination and date-range filtering
- PostgreSQL audit triggers for compliance
- Zero-trust security with patient isolation

## Architecture

### Stack
- **Runtime**: Deno (TypeScript)
- **Framework**: Oak (Deno's Express-like web framework)
- **Database**: PostgreSQL 14+
- **Auth**: User ID via HTTP headers (x-user-id)

### Project Structure
```
src/
├── main.ts              # Application entry point
├── types.ts             # TypeScript type definitions
├── db.ts                # Database connection & initialization
├── repository.ts        # Data access layer
├── routes_app.ts        # REST API endpoints
├── schemas/
│   ├── variant_results_schema.sql      # Main results table
│   └── variant_audit_log_schema.sql    # Audit triggers
tests/
└── variant_results.test.ts    # Integration tests
deno.json                # Deno configuration
.env.deno               # Environment variables
```

## Database Schema

### variant_results Table
```sql
CREATE TABLE variant_results (
    result_id UUID PRIMARY KEY,
    patient_id UUID NOT NULL (FK → patients.patient_id),
    variant_id VARCHAR(255),
    chrom VARCHAR(2),
    pos INTEGER,
    ref VARCHAR(1000),
    alt VARCHAR(1000),
    prediction VARCHAR(50) CHECK (IN 'Pathogenic', 'Benign', 'VUS'),
    confidence FLOAT (0-1),
    probabilities JSONB,
    model_version VARCHAR(10),
    feature_importance JSONB,
    clinical_notes TEXT,
    created_by UUID (FK → users.user_id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN,
    metadata JSONB
)
```

### variant_audit_log Table
With automatic triggers on INSERT/UPDATE/DELETE:
```sql
CREATE TABLE variant_audit_log (
    audit_id UUID PRIMARY KEY,
    result_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    operation VARCHAR(10) CHECK (IN 'INSERT', 'UPDATE', 'DELETE'),
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    changed_by UUID,
    changed_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB
)
```

## REST API Endpoints

### Create Result
```
POST /patients/{patient_id}/variant-results
Content-Type: application/json
X-User-ID: <user-uuid>

{
  "variant_id": "rs123456",
  "chrom": "17",
  "pos": 41244394,
  "ref": "T",
  "alt": "G",
  "prediction": "Pathogenic|Benign|VUS",
  "confidence": 0.87,
  "probabilities": {"benign": 0.13, "pathogenic": 0.87},
  "model_version": "v2",
  "feature_importance": {...},
  "clinical_notes": "Optional clinical notes",
  "metadata": {}
}

Response: 201 Created
{
  "result": {
    "result_id": "<uuid>",
    "patient_id": "<uuid>",
    ...
  }
}
```

### List Results (with Filtering)
```
GET /patients/{patient_id}/variant-results?limit=20&offset=0&start_date=2024-01-01&end_date=2024-12-31&prediction=Pathogenic&model_version=v2

Query Parameters:
- limit: 1-100 (default 20)
- offset: Pagination offset
- start_date: ISO format (2024-01-01)
- end_date: ISO format
- prediction: Pathogenic|Benign|VUS
- model_version: v1|v2|v3
- include_deleted: true|false (default false)
- sort_by: created_at|confidence (default created_at)
- sort_order: ASC|DESC (default DESC)

Response: 200 OK
{
  "data": [{...}, ...],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_next": true
}
```

### Get Single Result
```
GET /patients/{patient_id}/variant-results/{result_id}

Response: 200 OK
{
  "result": {...}
}
```

### Update Result
```
PUT /patients/{patient_id}/variant-results/{result_id}
Content-Type: application/json
X-User-ID: <user-uuid>

{
  "prediction": "Benign",
  "clinical_notes": "Updated notes",
  "metadata": {...}
}

Response: 200 OK
{
  "result": {...}
}
```

### Delete Result (Soft Delete)
```
DELETE /patients/{patient_id}/variant-results/{result_id}
X-User-ID: <user-uuid>

Response: 204 No Content
```

### Get Result Audit History
```
GET /patients/{patient_id}/variant-results/{result_id}/audit?limit=50&offset=0

Response: 200 OK
{
  "data": [
    {
      "audit_id": "<uuid>",
      "operation": "INSERT|UPDATE|DELETE",
      "old_data": {...},
      "new_data": {...},
      "changed_fields": ["prediction", "clinical_notes"],
      "changed_by": "<user-uuid>",
      "changed_at": "2024-03-30T12:00:00Z"
    },
    ...
  ],
  "total": 3,
  "has_next": false
}
```

### Get Patient Audit Log
```
GET /patients/{patient_id}/audit?limit=50&offset=0&start_date=2024-01-01&end_date=2024-12-31

Response: 200 OK
{
  "data": [{...}, ...],
  "total": 15,
  "has_next": false
}
```

### Get Prediction Statistics
```
GET /patients/{patient_id}/statistics

Response: 200 OK
{
  "statistics": {
    "total": 42,
    "pathogenic_count": 8,
    "benign_count": 30,
    "vus_count": 4,
    "avg_confidence": 0.87,
    "last_result_date": "2024-03-30T12:00:00Z"
  }
}
```

## Setup & Installation

### Prerequisites
- Deno 1.40+
- PostgreSQL 14+
- Node.js/npm (optional, for package management)

### Installation

1. **Install Deno** (if not already installed):
```bash
# macOS / Linux
curl -fsSL https://deno.land/install.sh | sh

# Windows (PowerShell)
irm https://deno.land/install.ps1 | iex
```

2. **Setup Database**:
```sql
-- Create database
CREATE DATABASE theragenome;

-- Connect to database
\c theragenome;

-- Create app user
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE theragenome TO app_user;

-- Create base patient table (from Dev 4)
CREATE TABLE patients (
  patient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

3. **Configure Environment**:
```bash
cp .env.deno .env
# Edit .env with your database credentials
```

4. **Run Application**:
```bash
# Development mode
deno run --allow-net --allow-env --allow-read src/main.ts

# Or with Deno task
deno task dev
```

5. **Run Tests**:
```bash
# All tests
deno test --allow-net --allow-env --allow-read tests/

# Or with Deno task
deno task test
```

## API Examples

### Create a Variant Result
```bash
curl -X POST http://localhost:3000/patients/550e8400-e29b-41d4-a716-446655440000/variant-results \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 550e8400-e29b-41d4-a716-446655440001" \
  -d '{
    "variant_id": "rs123456",
    "chrom": "17",
    "pos": 41244394,
    "ref": "T",
    "alt": "G",
    "prediction": "Pathogenic",
    "confidence": 0.87,
    "probabilities": {"benign": 0.13, "pathogenic": 0.87},
    "model_version": "v2"
  }'
```

### List Patient Results
```bash
curl -X GET 'http://localhost:3000/patients/550e8400-e29b-41d4-a716-446655440000/variant-results?limit=10&prediction=Pathogenic' \
  -H "Authorization: Bearer <token>"
```

### Get Result Audit History
```bash
curl -X GET 'http://localhost:3000/patients/550e8400-e29b-41d4-a716-446655440000/variant-results/result-uuid/audit' \
  -H "Authorization: Bearer <token>"
```

### Update a Result
```bash
curl -X PUT http://localhost:3000/patients/550e8400-e29b-41d4-a716-446655440000/variant-results/result-uuid \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 550e8400-e29b-41d4-a716-446655440001" \
  -d '{
    "clinical_notes": "Updated clinical assessment",
    "prediction": "Benign"
  }'
```

## Features

### ✅ Soft Deletes
- Results marked as deleted without removal
- Hidden from queries by default
- Recoverable via `include_deleted=true`
- Audit trail preserved

### ✅ Audit Logging
- Automatic triggers on all changes
- Captures before/after states
- Tracks user, timestamp, and changed fields
- Compliant with HIPAA audit requirements

### ✅ Filtering & Search
- Date range queries
- Prediction type filtering
- Model version filtering
- Sort by multiple fields

### ✅ Pagination
- Limit/offset pagination
- Total count included
- `has_next` indicator
- Max 100 items per request

### ✅ Statistics
- Prediction distribution
- Average confidence scores
- Last result date
- Variant count per type

## Performance Considerations

- Indexed queries on `patient_id`, `created_at`, `prediction`
- Composite index for common queries
- Pagination enforced (max 100 per request)
- JSONB columns support efficient filtering

## Security

- Patient data isolation by `patient_id`
- User tracking via `x-user-id` header
- Soft deletes prevent accidental data loss
- Audit log captures all changes
- CORS configurable per environment
- No in-memory caching (stateless for horizontal scaling)

## Deployment

### Docker Deployment
```dockerfile
FROM denoland/deno:latest

WORKDIR /app
COPY . .

RUN deno cache src/main.ts

CMD ["deno", "run", "--allow-net", "--allow-env", "--allow-read", "src/main.ts"]
```

## Status

✅ **TASK 1.4 COMPLETE - DENO VERSION**

All deliverables created:
- PostgreSQL schema with audit triggers
- Deno REST API with Oak framework  
- Complete CRUD operations
- Audit log tracking
- Filtering & pagination
- Comprehensive unit tests
