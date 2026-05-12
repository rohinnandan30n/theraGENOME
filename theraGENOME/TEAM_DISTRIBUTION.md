# TheraGenome Database Team Distribution Package

## Overview

This package contains the complete Alembic migration pipeline, patient schema definition, seed data scripts, and documentation for distributed development across Dev 1, Dev 2, and Dev 3. All shared schema changes are managed and versioned through Alembic.

---

## 📦 Package Contents

### Core Files (Distribute to All Teams)
- `patient_schema.sql` - **Authoritative patient table definition** ✨ PRIMARY ARTIFACT
- `alembic/` - Alembic migration pipeline (all versions)
- `scripts/seed_patients.py` - Synthetic patient data generation
- `requirements.txt` - Python dependencies
- `.env.example` - Database configuration template

### Documentation (Reference)
- `SCHEMA_DOCUMENTATION.md` - Complete schema reference
- `ALEMBIC_GUIDE.md` - Migration workflow guide
- `SEED_DATA_GUIDE.md` - Data generation instructions
- `HIPAA_CHECKLIST.md` - Security & compliance requirements

### Configuration
- `alembic.ini` - Alembic configuration
- `alembic/env.py` - Migration environment setup
- `alembic/script.py.mako` - Migration template

---

## 🚀 Quick Start for Each Development Team

### First-Time Setup (Dev 1, Dev 2, Dev 3)

```bash
# 1️⃣  Clone repository
git clone <repository-url>
cd thergenome

# 2️⃣  Create Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3️⃣  Install dependencies
pip install -r requirements.txt

# 4️⃣  Configure database connection
cp .env.example .env
# Edit .env with your local PostgreSQL credentials
# DATABASE_URL=postgresql://user:password@localhost:5432/thergenome_dev

# 5️⃣  Apply Alembic migrations
alembic upgrade head

# 6️⃣  Verify schema created
psql -U <user> -d thergenome_dev -c "\d patients"

# 7️⃣  (Optional) Seed synthetic test data
python scripts/seed_patients.py 100
```

### Verify Installation

```bash
# Check migration status
alembic current

# Test database connection
python -c "import db_connection; print('✅ Connected')"

# Query seeded patients  
psql -U <user> -d thergenome_dev -c "SELECT COUNT(*) FROM patients WHERE deleted_at IS NULL;"
```

---

## 📋 Schema as FK Anchor

The `patients` table serves as the **foreign key anchor** for all other domain tables. All teams must reference it consistently.

### Pattern for New Tables

When creating any new domain table, use this FK pattern:

```sql
CREATE TABLE clinical_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    -- ... other columns ...
    CONSTRAINT fk_clinical_events_patient_id 
        FOREIGN KEY (patient_id) 
        REFERENCES patients(patient_id) 
        ON DELETE RESTRICT  -- Prevent accidental patient deletion
);
```

### Available Patient Identifiers for Joins

All tables in TheraGenome **must** reference patients via:

```sql
-- Option 1: Direct FK (preferred)
FOREIGN KEY (patient_id) REFERENCES patients(patient_id)

-- Option 2: Join pattern
SELECT * FROM clinical_events ce
JOIN patients p ON ce.patient_id = p.patient_id
WHERE p.deleted_at IS NULL
```

**Never use other identifiers** to reference patients (no separate IDs, no strings, no guessing).

---

## 🔄 Migration Workflow

### Scenario 1: Pulling Updates from Remote

**When you see new migration files in git:**

```bash
# 1. Update your local code
git pull origin main

# 2. Check pending migrations
alembic upgrade --sql head  # Preview (don't apply yet)

# 3. Apply migrations
alembic upgrade head

# 4. Verify new schema
alembic current
psql -U <user> -d thergenome_dev -c "\d"
```

### Scenario 2: Creating New Schema Changes

**If you need to add a new table or modify patients:**

```bash
# 1. Create migration
alembic revision -m "descriptive_change_name"

# 2. Edit the migration file
#    alembic/versions/###_descriptive_change_name.py

# 3. Test locally
alembic upgrade head
# Test your code...
alembic downgrade -1  # Rollback
alembic upgrade head  # Re-apply

# 4. Export updated schema (if you modified patients table)
python scripts/export_schema.py

# 5. Commit and push
git add alembic/versions/###_descriptive_change_name.py
git add schemas/patient_schema.sql  # If modified
git commit -m "feat(schema): your_description"
git push origin main

# 6. Notify other teams
# Send PR link or slack message describing the schema change
```

---

## 📊 Team Synchronization Matrix

| Scenario | Dev 1 | Dev 2 | Dev 3 | Frequency |
|----------|-------|-------|-------|-----------|
| Pull new migrations | `git pull` → `alembic upgrade head` | Same | Same | Daily |
| Modify patients table | Create migration | Notify others | Wait for merge | As needed |
| Add domain table | Create own migration | Extend with FKs to patients | Sync after | Per feature |
| Run seed data | `python scripts/seed_patients.py` | Same | Same | Weekly/before testing |

---

## 🎯 Core Responsibilities

### Patient Schema Custodian
- Maintain `schemas/patient_schema.sql` as authoritative definition
- Review & approve any changes to patient table structure
- Update documentation when schema changes
- Notify all teams of breaking changes

### Each Development Team (Dev 1, Dev 2, Dev 3)
- ✅ Keep Alembic migrations in sync via git
- ✅ Run `alembic upgrade head` after pulling updates
- ✅ Create new migrations for domain-specific tables
- ✅ Always use `patient_id` FK when referencing patients
- ✅ Document new table relationships in ERD (update SCHEMA_DOCUMENTATION.md)
- ✨ DO NOT modify the patients table independently - coordinate first!

---

## 🗺️ Entity Relationship Diagram (Current & Future)

### Current State (v1.0)
```
┌─────────────────────────┐
│     patients            │ ← Foundation table
├─────────────────────────┤
│ • patient_id (PK, UUID) │
│ • demographics (8 cols) │
│ • timestamps (3 cols)   │
└─────────────────────────┘
```

### Expected Relationships (Future)
```
                      ┌─────────────────────┐
                      │    patients         │ (Foundation)
                      ├─────────────────────┤
                      │ patient_id (UUID)   │
                      │ demographics        │
                      └─────────────────────┘
                             △ FK anchor
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────────────┐   ┌──────────────────┐  ┌──────────────────┐
    │Clinical     │   │Genomic Results   │  │Medications       │
    │Events       │   │                  │  │                  │
    │(Dev 1)      │   │(Dev 2)           │  │(Dev 3)           │
    ├─────────────┤   ├──────────────────┤  ├──────────────────┤
    │event_id(PK) │   │result_id(PK)     │  │med_id(PK)        │
    │patient_id→  │   │patient_id→       │  │patient_id→       │
    │event_type   │   │test_name         │  │med_name          │
    │event_date   │   │result_data       │  │start_date        │
    └─────────────┘   └──────────────────┘  └──────────────────┘
```

---

## 📚 Documentation Reference

### For Getting Started
- Read: `SCHEMA_DOCUMENTATION.md` (5 min) - Overview of patients table
- Read: `ALEMBIC_GUIDE.md` - Setting up migrations (10 min)
- Read: `SEED_DATA_GUIDE.md` - Running seed script (5 min)

### For Team Leads
- Review: `HIPAA_CHECKLIST.md` - Security requirements ⚠️
- Keep: `patient_schema.sql` - Distribution artifact
- Share: Migration notification template (below)

### For Operations/DevOps
- Deploy: Alembic migrations to staging → production
- Monitor: Migration history: `alembic history`
- Verify: Table schema: `psql -c "\d patients"`

---

## 🔐 HIPAA Security Checklist

Before distributing schema to teams, ensure:

- ✅ UUID primary keys (no sequential IDs)
- ✅ Soft delete pattern (data retention audit trail)
- ✅ Timezone-aware timestamps (UTC)
- ✅ Role-based access control configured (RBAC)
- ✅ Encryption at rest enabled in PostgreSQL
- ✅ TLS for database connections
- ✅ Audit logging enabled
- ✅ Regular backups configured

**See `HIPAA_CHECKLIST.md` for full compliance details.**

---

## 📤 Distribution Checklist

### To Share with Dev 1, Dev 2, Dev 3:

- [ ] **patient_schema.sql** - The FK anchor definition
- [ ] `alembic/` directory - All migrations (versioned)
- [ ] `scripts/seed_patients.py` - Consistent test data generation
- [ ] `requirements.txt` - Dependency versions
- [ ] `.env.example` - Configuration template
- [ ] `SCHEMA_DOCUMENTATION.md` - Reference guide
- [ ] `ALEMBIC_GUIDE.md` - Workflow instructions
- [ ] `SEED_DATA_GUIDE.md` - Seed script guide
- [ ] This document: `TEAM_DISTRIBUTION.md`

### Via Git
```bash
git add alembic/ schemas/ scripts/ *.md requirements.txt .env.example
git commit -m "feat: distribute patient schema v1.0 to all teams"
git push origin main

# Notify teams
echo "
🚀 Patient Schema v1.0 Ready for Distribution

All teams should:
1. git pull origin main
2. pip install -r requirements.txt
3. alembic upgrade head
4. python scripts/seed_patients.py 100

Key File: schemas/patient_schema.sql (FK anchor)
Docs: SCHEMA_DOCUMENTATION.md, ALEMBIC_GUIDE.md
" | slack-notify #dev-teams
```

---

## 🔗 Team Communication Template

**Send to each development team when distributing:**

---

### 📬 Message to Dev Teams

Subject: **TheraGenome Patient Schema v1.0 Distribution**

Hi Dev 1/Dev 2/Dev 3,

The patient schema is ready for download and integration. This is the **authoritative database foundation** for the entire platform.

**What's included:**
- `patient_schema.sql` - Core FK anchor table
- Alembic migrations pipeline (all versions)
- Synthetic seed data generator (100 patients)
- Complete documentation

**Your first steps:**
```bash
git pull origin main
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Update with your DB credentials
alembic upgrade head
python scripts/seed_patients.py  # Optional: generate test data
```

**Key points:**
- ✅ All patient references must use `patient_id` UUID FK
- ✅ Never modify the `patients` table independently
- ✅ Create your domain-specific tables with FK to `patients(patient_id)`
- ✅ Keep Alembic migrations in sync via git

**Questions?**
- Schema reference: See `SCHEMA_DOCUMENTATION.md`
- Migration questions: See `ALEMBIC_GUIDE.md`
- Seed data questions: See `SEED_DATA_GUIDE.md`

Looking forward to integrating your domain tables!
—Database Architecture Team

---

---

## 📞 Support & Escalation

### Common Issues

**Issue:** Migration fails to apply
*Solution:* Check database connection: `psql -U <user> -d thergenome_dev -c "SELECT 1;"`

**Issue:** Conflicts in alembic migrations
*Solution:* Pull latest, run `alembic current` to check state, then `alembic upgrade head`

**Issue:** Seed script fails
*Solution:* Ensure `alembic upgrade head` ran first, then try `python scripts/seed_patients.py 10` (small batch)

**Issue:** FK constraint errors
*Solution:* Ensure you're using `patient_id` UUID, not creating your own ID type

---

## 🎓 Learning Resources

- **PostgreSQL UUIDs:** https://www.postgresql.org/docs/current/datatype-uuid.html
- **Alembic Documentation:** https://alembic.sqlalchemy.org/
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/
- **HIPAA Security:** https://www.hhs.gov/hipaa/

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.0** | 2026-03-31 | Initial distribution: patients table with UUID PK, demographics, soft deletes, timestamps, indexes |
| | | 4 indexes optimized for queries |
| | | 100-patient seed data generator |
| | | Alembic migration pipeline ready |

---

## Next Steps

1. ✅ **Distribute this package** to Dev 1, Dev 2, Dev 3
2. ✅ **Have each team run setup** within 24 hours
3. ✅ **Create their domain tables** with FK references
4. ✅ **Coordinate on new migrations** via git PRs
5. ✅ **Weekly sync meetings** to discuss schema changes

---

**Package Created:** March 31, 2026  
**Maintained By:** Database Architecture Team  
**Contact:** database-team@thergenome.io
