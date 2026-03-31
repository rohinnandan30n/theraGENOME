# TheraGenome Database Schema Documentation

## Overview

This document describes the core patient identity schema for TheraGenome, a HIPAA-compliant genomics and clinical data platform. The schema is managed using Alembic migrations and distributed to all development teams.

---

## Table: `patients`

**Purpose:** Core patient demographics and identity table - the anchor point for all patient data.

**HIPAA Classification:** SENSITIVE - Contains protected health information (PHI)

### Column Definitions

| Column | Type | Nullable | Default | Purpose |
|--------|------|----------|---------|---------|
| `patient_id` | UUID | NO | `gen_random_uuid()` | Primary key - unique patient identifier (v4 UUID) |
| `first_name` | VARCHAR(255) | NO | - | Patient's first name |
| `last_name` | VARCHAR(255) | NO | - | Patient's last name |
| `date_of_birth` | DATE | NO | - | Patient's date of birth (for age calculation) |
| `sex` | VARCHAR(20) | YES | - | Biological sex: M / F / Other / Prefer not to say |
| `ethnicity` | VARCHAR(255) | YES | - | Patient's self-identified ethnicity |
| `created_at` | TIMESTAMPTZ | NO | `NOW()` | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMPTZ | NO | `NOW()` | Last modification timestamp (UTC) |
| `deleted_at` | TIMESTAMPTZ | YES | NULL | Soft delete marker (NULL = active record) |

### Indexes

```sql
-- Primary key (automatic)
CREATE UNIQUE INDEX idx_patients_patient_id ON patients(patient_id);

-- Frequently queried fields
CREATE INDEX idx_patients_date_of_birth ON patients(date_of_birth);
CREATE INDEX idx_patients_created_at ON patients(created_at);

-- Soft delete queries
CREATE INDEX idx_patients_deleted_at ON patients(deleted_at);
```

**Index Strategy:**
- `patient_id`: Unique constraint for fast identity lookups
- `date_of_birth`: Supports age-based queries and medical record searches
- `deleted_at`: Enables efficient filtering of active/inactive records
- `created_at`: Supports temporal queries and audit trails

---

## Key Design Decisions

### 1. **UUID Primary Key**
- **Why:** Database-independent, cryptographically secure, no sequential guessing
- **Format:** PostgreSQL native UUID type (UUID RFC 4122 v4)
- **Generation:** `gen_random_uuid()` at insert time (server-side)
- **Distribution:** No merge conflicts when data is replicated

### 2. **Soft Delete Pattern**
- **Why:** HIPAA requires data retention; hard deletes lose audit trail
- **Implementation:** `deleted_at` TIMESTAMPTZ column
- **Query Pattern:** `WHERE deleted_at IS NULL` returns active patients
- **Retention:** All deleted records remain in database for compliance

### 3. **Timezone-Aware Timestamps**
- **Why:** Medical data spans global clinics; must track exact moment of event
- **Format:** TIMESTAMPTZ (PostgreSQL) = timestamp with time zone
- **Storage:** Always UTC internally; displayed in local zone per client
- **Audit:** `created_at` and `updated_at` provide full audit trail

### 4. **Demographics as Nullable**
- **sex:** Nullable (5% of patients prefer not to answer)
- **ethnicity:** Nullable (privacy concerns, optional reporting)
- **Rationale:** Respect patient autonomy while retaining records for analytics

---

## Foreign Key Usage Pattern

All tables referencing patients must use:

```sql
ALTER TABLE <table_name> 
ADD CONSTRAINT fk_<table_name>_patient_id 
FOREIGN KEY (patient_id) 
REFERENCES patients(patient_id) 
ON DELETE RESTRICT;
  -- RESTRICT prevents accidental deletion of patient from being cascaded
```

**Example for Clinical Events:**
```sql
CREATE TABLE clinical_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    -- ... other columns ...
    CONSTRAINT fk_clinical_events_patient_id 
        FOREIGN KEY (patient_id) 
        REFERENCES patients(patient_id) 
        ON DELETE RESTRICT
);
```

---

## Migration Pipeline

### For Development Teams (Dev 1, Dev 2, Dev 3)

**Step 1: Initialize Alembic (First time setup)**
```bash
# Clone/pull the TheraGenome repository
cd thergenome

# Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database URL
cp .env.example .env
# Edit .env with your database credentials
```

**Step 2: Apply Migrations**
```bash
# View migration status
alembic current

# Run all pending migrations
alembic upgrade head

# Run specific migration
alembic upgrade 001_create_patients_table
```

**Step 3: Seed Test Data (Optional)**
```bash
# Generate 100 synthetic patients
python scripts/seed_patients.py

# Or generate custom count
python scripts/seed_patients.py 500
```

**Step 4: Verify Schema**
```bash
# Connect to PostgreSQL
psql -U <user> -d thergenome_dev

-- Check patients table exists
\d patients

-- Count seeded records
SELECT COUNT(*) FROM patients WHERE deleted_at IS NULL;
```

### For Schema Updates (All Contributors)

**If you need to modify the patients table:**

1. **Create new migration:**
   ```bash
   cd alembic
   alembic revision --autogenerate -m "add_email_column"
   # Or manually create: alembic/versions/002_<name>.py
   ```

2. **Test migration:**
   ```bash
   alembic upgrade head
   # Test thoroughly
   alembic downgrade -1  # Rollback if needed
   alembic upgrade head  # Re-apply
   ```

3. **Export updated schema:**
   ```bash
   python scripts/export_schema.py
   ```

4. **Commit and distribute:**
   ```bash
   git add alembic/versions/<new_migration>.py
   git add schemas/patient_schema.sql
   git commit -m "feat(schema): add email column to patients table"
   git push origin main
   ```

5. **Other teams sync:**
   ```bash
   git pull origin main
   alembic upgrade head
   ```

---

## Entity Relationship Diagram (ERD)

```
┌─────────────────────────────────────┐
│          patients                   │  (Core Patient Identity)
├─────────────────────────────────────┤
│ PK  │ patient_id      (UUID)        │
│     │ first_name      (VARCHAR 255) │
│     │ last_name       (VARCHAR 255) │
│     │ date_of_birth   (DATE)        │
│     │ sex             (VARCHAR 20)  │
│     │ ethnicity       (VARCHAR 255) │
│     │ created_at      (TIMESTAMPTZ) │
│     │ updated_at      (TIMESTAMPTZ) │
│     │ deleted_at      (TIMESTAMPTZ) │
└─────────────────────────────────────┘
         ▲
         │ (FK: patient_id)
         │ (Relationships to be added)
         │
┌─────────────────────────────────────┐
│    clinical_events (future)         │
├─────────────────────────────────────┤
│ PK  │ event_id     (UUID)           │
│ FK  │ patient_id   (UUID) ──────────┤─── references patients
│     │ event_date   (TIMESTAMPTZ)    │
│     │ event_type   (VARCHAR 100)    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    genomics_results (future)        │
├─────────────────────────────────────┤
│ PK  │ result_id    (UUID)           │
│ FK  │ patient_id   (UUID) ──────────┤─── references patients
│     │ test_name    (VARCHAR 255)    │
│     │ result_date  (TIMESTAMPTZ)    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    medications (future)             │
├─────────────────────────────────────┤
│ PK  │ med_id       (UUID)           │
│ FK  │ patient_id   (UUID) ──────────┤─── references patients
│     │ med_name     (VARCHAR 255)    │
│     │ start_date   (DATE)           │
└─────────────────────────────────────┘
```

---

## Query Examples

### Find Active Patients
```sql
SELECT * FROM patients 
WHERE deleted_at IS NULL 
ORDER BY created_at DESC;
```

### Find Patient by ID
```sql
SELECT * FROM patients 
WHERE patient_id = '550e8400-e29b-41d4-a716-446655440000'
AND deleted_at IS NULL;
```

### Calculate Patient Age
```sql
SELECT 
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    EXTRACT(YEAR FROM AGE(NOW(), date_of_birth)) AS age
FROM patients 
WHERE deleted_at IS NULL;
```

### Soft Delete a Patient
```sql
UPDATE patients 
SET deleted_at = NOW(), updated_at = NOW()
WHERE patient_id = '550e8400-e29b-41d4-a716-446655440000';
```

### Demographics Report (Aggregation)
```sql
SELECT 
    sex,
    ethnicity,
    COUNT(*) as patient_count,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(NOW(), date_of_birth)))) as avg_age
FROM patients 
WHERE deleted_at IS NULL
GROUP BY sex, ethnicity
ORDER BY patient_count DESC;
```

---

## Security & Compliance

### HIPAA Considerations
- ✅ Patient records are encrypted at rest (enable in PostgreSQL)
- ✅ Soft delete preserves audit trail
- ✅ Timestamps track all modifications
- ✅ UUIDs prevent sequential patient ID guessing
- ⚠️ Ensure role-based access control (RBAC) on this table

### Recommended Access Pattern (PostgreSQL ROLES)
```sql
-- Create roles
CREATE ROLE clinician LOGIN PASSWORD 'password';
CREATE ROLE researcher LOGIN PASSWORD 'password';

-- Grant clinician full access (for patient care)
GRANT SELECT, INSERT, UPDATE ON patients TO clinician;

-- Grant researcher read-only access (for de-identified research)
GRANT SELECT ON patients TO researcher;

-- Audit access
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

### Encryption Recommendations
- Enable PostgreSQL `pgcrypto` for sensitive columns
- Use application-level encryption for additional PII protection
- Implement TLS for all database connections

---

## Performance Notes

### Current Indexes (4)
- **idx_patients_patient_id:** Unique lookup (instantaneous)
- **idx_patients_date_of_birth:** Age/date range queries
- **idx_patients_created_at:** Temporal queries
- **idx_patients_deleted_at:** Active patient filtering

### Monitoring Recommendations
- Monitor table size as it grows (implement archiving at 10M+ records)
- Check index usage with: `SELECT * FROM pg_stat_user_indexes`
- Set up alerts for slow queries exceeding 100ms

---

## Table Statistics (Initial)

After seeding with 100 synthetic records:
- **Rows:** 100
- **Total Size:** ~50 KB
- **Avg. Row Size:** ~500 bytes
- **Suggested Maintenance:** VACUUM & ANALYZE after large inserts

---

## Maintenance Tasks

### Weekly
```sql
-- Recalculate table statistics for query planner
ANALYZE patients;
```

### Monthly
```sql
-- Remove unused index bloat
VACUUM ANALYZE patients;
```

### Quarterly
```sql
-- Full maintenance with exclusive lock
VACUUM FULL ANALYZE patients;
```

---

## Related Documentation

- [Alembic Migration Guide](../ALEMBIC_GUIDE.md) - Comprehensive migration instructions  
- [Seed Data Generation](../SEED_DATA_GUIDE.md) - Synthetic patient data generation
- [HIPAA Security Checklist](../HIPAA_CHECKLIST.md) - Compliance requirements

---

**Last Updated:** March 31, 2026  
**Schema Version:** 1.0  
**Maintained By:** Database Architecture Team
