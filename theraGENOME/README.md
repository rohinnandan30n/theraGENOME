# TheraGenome Patient Database Schema - Task 4.1 Complete

## 🎉 Project Overview

This repository contains the complete PostgreSQL migration pipeline, patient schema definition, and seed data generation system for TheraGenome. The schema is managed through Alembic and distributed to Dev 1, Dev 2, and Dev 3 as the authoritative patient data foundation.

---

## 📁 Project Structure

```
TheraGenome/
├── alembic/                          # Alembic migration framework
│   ├── versions/                     # Migration files (versioned)
│   │   ├── 001_create_patients_table.py
│   │   └── __init__.py
│   ├── env.py                        # Migration environment config
│   ├── script.py.mako                # Migration template
│   └── __init__.py
│
├── schemas/                          # Schema definitions
│   └── patient_schema.sql            # ⭐ FK ANCHOR - Distribute to teams
│
├── scripts/                          # Utility scripts
│   ├── seed_patients.py              # Generate 100 synthetic patients
│   ├── export_schema.py              # Export schema to SQL file
│   ├── db_connection.py              # Database connection utilities
│   └── __init__.py
│
├── SCHEMA_DOCUMENTATION.md           # Complete schema reference (📚 Read First)
├── ALEMBIC_GUIDE.md                  # Migration workflow guide
├── SEED_DATA_GUIDE.md                # Seed script documentation
├── TEAM_DISTRIBUTION.md              # Team sync & responsibilities
├── HIPAA_CHECKLIST.md                # Security & compliance requirements
├── README.md                         # This file
│
├── alembic.ini                       # Alembic configuration
├── requirements.txt                  # Python dependencies
├── .env.example                      # Database configuration template
└── .gitignore
```

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone & Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd TheraGenome

# Create Python virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
# OR
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Database
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# Ensure PostgreSQL is running on localhost:5432
```

### Step 3: Run Alembic Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Verify schema created
psql -U <user> -d thergenome_dev -c "\d patients"
```

### Step 4: Seed Test Data (Optional)
```bash
# Generate 100 synthetic patients
python scripts/seed_patients.py

# Verify data
psql -U <user> -d thergenome_dev -c "SELECT COUNT(*) FROM patients;"
```

**🎯 Done!** Your database is ready.

---

## 📚 Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[SCHEMA_DOCUMENTATION.md](SCHEMA_DOCUMENTATION.md)** | Complete reference for patients table, design decisions, query examples, ERD | 15 min |
| **[ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md)** | How to create, apply, and manage database migrations | 20 min |
| **[SEED_DATA_GUIDE.md](SEED_DATA_GUIDE.md)** | How to generate synthetic test data with Faker | 10 min |
| **[TEAM_DISTRIBUTION.md](TEAM_DISTRIBUTION.md)** | How to share schema with Dev teams and keep in sync | 10 min |
| **[HIPAA_CHECKLIST.md](HIPAA_CHECKLIST.md)** | Security & compliance requirements (⚠️ Important) | 20 min |

---

## 🗂️ Core Artifacts

### ⭐ **patient_schema.sql** - The FK Anchor
This is the **authoritative patient table definition**. All development teams must use this as the foundation for their domain tables.

**Distribute this file to:**
- Dev 1 (Clinical Events)
- Dev 2 (Genomic Results)  
- Dev 3 (Medications)

**Key features:**
- UUID primary key (`gen_random_uuid()`)
- Demographics: first_name, last_name, date_of_birth, sex, ethnicity
- Audit trail: created_at, updated_at, deleted_at (soft delete)
- Indexes: patient_id (unique), date_of_birth, deleted_at, created_at

### 📝 Alembic Migration Pipeline
All schema changes are versioned in `alembic/versions/`:

```bash
# View migration history
alembic history

# Check current state
alembic current

# Apply specific migration
alembic upgrade 001_create_patients_table
```

### 🧬 Synthetic Patient Generator
Generate realistic test data without real PII:

```bash
# 100 synthetic patients (default)
python scripts/seed_patients.py

# Custom count
python scripts/seed_patients.py 500
```

---

## 🔄 Team Workflow

### For Each Development Team (Dev 1, Dev 2, Dev 3)

#### 1. Initial Setup
```bash
git clone <repo>
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DB credentials
alembic upgrade head              # Apply migrations
python scripts/seed_patients.py   # Load test data
```

#### 2. Daily Workflow
```bash
# Before starting work
git pull origin main
alembic current                   # Check migration status
alembic upgrade head              # Apply any new migrations

# After making schema changes
alembic revision -m "descriptive_name"
# Edit alembic/versions/###_descriptive_name.py
alembic upgrade head              # Test locally
# Test downgrade to ensure reversibility
alembic downgrade -1
alembic upgrade head

# Commit when ready
git add alembic/versions/###_descriptive_name.py
git add schemas/patient_schema.sql  # If modified
git commit -m "feat(schema): description"
git push origin main
```

#### 3. Creating Domain Tables
Always reference patients via FK:

```sql
CREATE TABLE clinical_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_clinical_events_patient_id 
        FOREIGN KEY (patient_id) 
        REFERENCES patients(patient_id) 
        ON DELETE RESTRICT
);

CREATE INDEX idx_clinical_events_patient_id ON clinical_events(patient_id);
```

---

## 🔐 Security & HIPAA

**Before deploying to production, complete:**
- [ ] RBAC role-based access control
- [ ] TLS encryption for connections
- [ ] Encryption at rest (full-disk or column-level)
- [ ] Backup strategy with encryption
- [ ] Query audit logging
- [ ] De-identification views for researchers
- [ ] Row-level security policies

**See [HIPAA_CHECKLIST.md](HIPAA_CHECKLIST.md) for full compliance requirements.**

---

## 🛠️ Common Commands Reference

### Alembic

```bash
# Migration management
alembic history              # View all migrations
alembic current              # Check current version
alembic upgrade head         # Apply all pending migrations
alembic downgrade -1         # Rollback last migration
alembic revision -m "name"   # Create new migration

# Preview before applying
alembic upgrade head --sql   # Show SQL that will run

# Specific migration
alembic upgrade 001_create_patients_table
alembic downgrade 001_create_patients_table
```

### Database

```bash
# Connect to database
psql -U postgres -d thergenome_dev

-- Inside psql
\d patients                  # Describe table
\di patients_*              # List indexes
\dp patients                # Check permissions
SELECT * FROM patients LIMIT 5;  # Query data

-- Check schema version
SELECT version FROM alembic_version;

-- Soft delete query
SELECT * FROM patients WHERE deleted_at IS NULL;

-- Calculate ages
SELECT 
    patient_id,
    first_name,
    EXTRACT(YEAR FROM AGE(NOW(), date_of_birth)) as age
FROM patients;
```

### Scripts

```bash
# Generate seed data
python scripts/seed_patients.py           # 100 patients (default)
python scripts/seed_patients.py 500       # 500 patients

# Export schema
python scripts/export_schema.py           # Updates schemas/patient_schema.sql

# Test database connection
python -c "from scripts.db_connection import engine; print('✅ Connected')"
```

---

## 📊 Database Schema Overview

### Patients Table (Core)

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `patient_id` | UUID | NO | Primary key (unique identifier) |
| `first_name` | VARCHAR(255) | NO | Patient's first name |
| `last_name` | VARCHAR(255) | NO | Patient's last name |
| `date_of_birth` | DATE | NO | For age calculation & medical history |
| `sex` | VARCHAR(20) | YES | M/F/Other/Prefer not to say |
| `ethnicity` | VARCHAR(255) | YES | Patient's ethnicity |
| `created_at` | TIMESTAMPTZ | NO | Record creation (UTC) |
| `updated_at` | TIMESTAMPTZ | NO | Last modification (UTC) |
| `deleted_at` | TIMESTAMPTZ | YES | Soft delete marker (NULL=active) |

### Indexes (4 Total)

```
idx_patients_patient_id      (UNIQUE) - Fast identity lookups
idx_patients_date_of_birth           - Age/date range queries
idx_patients_deleted_at              - Soft delete filtering
idx_patients_created_at              - Temporal queries
```

---

## 🗺️ Entity Relationship Diagram

### Current (v1.0)
```
┌──────────────────────┐
│    patients          │  (Foundation)
├──────────────────────┤
│ PK: patient_id (UUID)│
│ Demographics (8 col) │
│ Timestamps (3 col)   │
└──────────────────────┘
```

### Future (Planned)
```
                    ┌─────────────────┐
                    │    patients     │
                    └────────┬────────┘
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Clinical   │  │  Genomic    │  │ Medications │
    │   Events    │  │   Results   │  │             │
    │  (Dev 1)    │  │  (Dev 2)    │  │  (Dev 3)    │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 📋 Checklist for Distribution to Teams

Before sharing with Dev 1, Dev 2, Dev 3:

- [x] `patient_schema.sql` - FK anchor definition
- [x] `alembic/` directory - All migrations
- [x] `scripts/seed_patients.py` - Test data generator
- [x] `requirements.txt` - Dependency list
- [x] `.env.example` - Configuration template
- [x] `SCHEMA_DOCUMENTATION.md` - Reference guide
- [x] `ALEMBIC_GUIDE.md` - Migration workflow
- [x] `SEED_DATA_GUIDE.md` - Seed guide
- [x] `TEAM_DISTRIBUTION.md` - Team coordination
- [x] `HIPAA_CHECKLIST.md` - Security requirements

**Distribution Method:**
```bash
# Commit all files to git
git add .
git commit -m "feat: Patient schema v1.0 for distribution"
git push origin main

# Notify teams via email/slack with setup instructions
```

---

## ⚠️ Important Notes

### Do's ✅
- ✅ Always use `patient_id` UUID when referencing patients
- ✅ Create new migrations for schema changes (don't modify existing ones)
- ✅ Test migrations both up and down (`upgrade` → `downgrade` → `upgrade`)
- ✅ Export schema after patient table changes: `python scripts/export_schema.py`
- ✅ Use soft delete pattern (set `deleted_at` instead of hard delete)
- ✅ Commit migrations to git immediately after testing

### Don'ts ❌
- ❌ Don't modify existing migration files (create new ones instead)
- ❌ Don't share database credentials (use .env files)
- ❌ Don't directly modify the patients table without team coordination
- ❌ Don't use hard deletes (use soft delete pattern)
- ❌ Don't create sequential patient IDs (use UUID)
- ❌ Don't skip testing migrations before committing

---

## 🐛 Troubleshooting

### Migration Won't Apply
```bash
# Check database connection
psql -U postgres -d thergenome_dev -c "SELECT 1"

# Check current migration status
alembic current

# Try again
alembic upgrade head
```

### seed_patients.py Fails
```bash
# Ensure table exists
alembic upgrade head

# Try with smaller batch
python scripts/seed_patients.py 10

# Check database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...'); engine.connect()"
```

### Schema Out of Sync
```bash
# Reset to known good state
alembic downgrade -99   # Downgrade all
alembic upgrade head    # Re-apply all
psql -c "\d patients"   # Verify
```

**For more help, see:**
- [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md#troubleshooting) - Migration troubleshooting
- [SEED_DATA_GUIDE.md](SEED_DATA_GUIDE.md#troubleshooting) - Seed script troubleshooting
- [SCHEMA_DOCUMENTATION.md](SCHEMA_DOCUMENTATION.md#performance-notes) - Performance notes

---

## 📞 Support

**Questions about:**
- **Schema design?** → See [SCHEMA_DOCUMENTATION.md](SCHEMA_DOCUMENTATION.md)
- **Migrations?** → See [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md)
- **Seed data?** → See [SEED_DATA_GUIDE.md](SEED_DATA_GUIDE.md)
- **Team coordination?** → See [TEAM_DISTRIBUTION.md](TEAM_DISTRIBUTION.md)
- **HIPAA compliance?** → See [HIPAA_CHECKLIST.md](HIPAA_CHECKLIST.md)

**Report issues:**
- Create GitHub issue with:
  - Error message & traceback
  - Command you ran
  - Environment (PostgreSQL version, Python version)
  - Steps to reproduce

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.0** | 2026-03-31 | ✅ Initial release: patients table, Alembic pipeline, seed script, documentation |

---

## 🎯 Next Steps

1. **Dev 1:** Create clinical_events table with FK to patients
2. **Dev 2:** Create genomics_results table with FK to patients  
3. **Dev 3:** Create medications table with FK to patients
4. **All Teams:** Coordinate on new domain tables via git PRs
5. **Compliance:** Complete HIPAA checklist before production

---

## 📝 License & Attribution

**Created:** March 31, 2026  
**Maintained By:** Database Architecture Team  
**Contact:** database-team@thergenome.io

---

**Ready to distribute to Dev 1, Dev 2, and Dev 3! 🚀**
