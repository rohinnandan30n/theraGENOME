# HIPAA Security & Compliance Checklist for TheraGenome

## Overview

HIPAA (Health Insurance Portability and Accountability Act) requires healthcare applications to implement comprehensive security and privacy controls. This checklist covers requirements for the TheraGenome patient schema and database infrastructure.

---

## 📋 Pre-Deployment Compliance Checklist

### Table Structure & Design

- [ ] **UUID Primary Keys Used**
  - ✅ Implemented in patient_schema.sql
  - Ensures: No sequential ID guessing attacks
  - Verify: `SELECT column_name, data_type FROM information_schema.columns WHERE table_name='patients' AND column_name='patient_id';`

- [ ] **Soft Delete Pattern Implemented**
  - ✅ `deleted_at` TIMESTAMPTZ column present
  - Ensures: Audit trail preserved, data retention compliance
  - Verify: `SELECT deleted_at FROM patients WHERE deleted_at IS NOT NULL;` (should show retention records)

- [ ] **Timezone-Aware Timestamps**
  - ✅ All timestamps use TIMESTAMPTZ (with UTC)
  - Ensures: Accurate audit trail of all events
  - Verify: `SELECT column_name, data_type FROM information_schema.columns WHERE table_name='patients' AND data_type='timestamp with time zone';`

- [ ] **Minimal PII in Database**
  - ✅ Only demographics, no credit cards/SSN/passwords
  - Ensure: Sensitive fields (SSN) encrypted separately if added
  - Standard: `first_name`, `last_name`, `date_of_birth` only

- [ ] **Table Comments & Field Documentation**
  - ✅ Implemented: Table and column comments in patient_schema.sql
  - Ensures: Compliance documentation
  - Verify: `SELECT obj_description('patients'::regclass, 'pg_class');`

---

### Database-Level Security

- [ ] **PostgreSQL Extensions Enabled**
  - ✅ UUID extension present: `CREATE EXTENSION "uuid-ossp"`
  - ✅ Consider: `pgcrypto` for sensitive column encryption

```sql
-- Enable encryption extension (Optional but recommended)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

- [ ] **Role-Based Access Control (RBAC) Configured**
  - ⚠️ TODO: Must implement before production

```sql
-- Create roles
CREATE ROLE clinician_group WITH LOGIN;
CREATE ROLE researcher_group WITH LOGIN;
CREATE ROLE admin_group WITH LOGIN;

-- Grant minimum required permissions
GRANT SELECT, INSERT, UPDATE ON patients TO clinician_group;
GRANT SELECT ON patients TO researcher_group;  -- Read-only
GRANT ALL ON patients TO admin_group;

-- Restrict direct access
REVOKE ALL ON patients FROM PUBLIC;
```

- [ ] **Connection Encryption (TLS)**
  - ⚠️ TODO: Configure PostgreSQL with SSL certificates
  - Requirement: All client connections must use `sslmode=require`

```env
# In .env or connection strings
DATABASE_URL=postgresql://user:password@db_host:5432/thergenome_dev?sslmode=require
```

- [ ] **Encryption at Rest**
  - ⚠️ TODO: Enable full-disk encryption on database server
  - Options:
    - PostgreSQL: pgcrypto for column-level encryption
    - OS-level: dm-crypt (Linux) / BitLocker (Windows) / FileVault (Mac)
    - Cloud: RDS Encryption (AWS), Cloud SQL (GCP), etc.

```sql
-- Optional: Encrypt sensitive columns with pgcrypto
ALTER TABLE patients 
ADD COLUMN first_name_encrypted bytea;

UPDATE patients 
SET first_name_encrypted = pgp_sym_encrypt(first_name, 'secret_key');
```

---

### Access Control & Authentication

- [ ] **Database User Isolation**
  - ⚠️ TODO: Each developer gets individual credentials (never shared `postgres` user)

```sql
-- Create individual user for each developer
CREATE ROLE dev1_user WITH LOGIN PASSWORD 'strong_password_dev1';
CREATE ROLE dev2_user WITH LOGIN PASSWORD 'strong_password_dev2';
CREATE ROLE dev3_user WITH LOGIN PASSWORD 'strong_password_dev3';

-- Grant to group roles
GRANT clinician_group TO dev1_user;
GRANT clinician_group TO dev2_user;
GRANT clinician_group TO dev3_user;
```

- [ ] **pg_hba.conf Configured for Authentication**
  - ⚠️ TODO: Specify authentication method (scram-sha-256 recommended)

```
# /etc/postgresql/.../pg_hba.conf
# IPv4 connections
host    database    user    127.0.0.1/32    scram-sha-256
host    database    user    all             reject      # Deny other hosts
```

- [ ] **API Token/Session Management** (if using web interface)
  - ⚠️ TODO: Implement short-lived tokens (15-30 min expiration)
  - Use OAuth 2.0 or JWT with RSA signing

---

### Log & Audit Trail

- [ ] **Query Audit Logging Enabled**
  - ⚠️ TODO: Enable PostgreSQL query logging

```sql
-- PostgreSQL configuration
ALTER SYSTEM SET log_connections = ON;
ALTER SYSTEM SET log_disconnections = ON;
ALTER SYSTEM SET log_statement = 'all';  -- Or 'ddl' for schema changes only
ALTER SYSTEM SET log_duration = ON;
SELECT pg_reload_conf();
```

- [ ] **Change Audit Trail**
  - ✅ Implemented: `created_at`, `updated_at`, `deleted_at` on patients
  - ✅ Soft delete preserves historical records

```sql
-- Verify audit trail functionality
SELECT 
    patient_id,
    first_name,
    created_at,
    updated_at,
    deleted_at
FROM patients
ORDER BY updated_at DESC
LIMIT 10;
```

- [ ] **Alembic Migration Tracking**
  - ✅ All schema changes versioned and reversible
  - Verify: `alembic history` shows all migrations
  - Ensure: Each migration includes upgrade/downgrade procedures

---

### Data Integrity & Backup

- [ ] **Foreign Key Constraints Enforced**
  - ✅ Implemented: FK references with `ON DELETE RESTRICT`
  - Ensures: No orphaned records

```sql
-- Example verified in schema
CONSTRAINT fk_clinical_events_patient_id 
    FOREIGN KEY (patient_id) 
    REFERENCES patients(patient_id) 
    ON DELETE RESTRICT;
```

- [ ] **Backup Strategy Documented**
  - ⚠️ TODO: Implement automated backups

```bash
#!/bin/bash
# Daily backup script
BACKUP_DIR="/backups/postgresql"
DB_NAME="thergenome_dev"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -U postgres -Fc $DB_NAME > $BACKUP_DIR/backup_${TIMESTAMP}.dump

# Archive backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.dump" -mtime +30 -delete

# Test restore capability
echo "✅ Backup created at $BACKUP_DIR/backup_${TIMESTAMP}.dump"
```

- [ ] **Backup Encryption**
  - ⚠️ TODO: Encrypt backup files in transit and at rest

```bash
# Encrypt backup with GPG
gpg --symmetric --cipher-algo AES256 backup_20260331.dump
# Creates: backup_20260331.dump.gpg

# Decrypt for restore
gpg -d backup_20260331.dump.gpg | pg_restore -U postgres -Fc -d thergenome_dev
```

- [ ] **Disaster Recovery Plan**
  - ⚠️ TODO: Document recovery procedure
  - Test: Monthly restore drills

---

### Data Retention & Purging

- [ ] **Data Retention Policy Defined**
  - ⚠️ TODO: Document retention periods by data type
  - Example: Patient records retained 7 years minimum (medical records standard)

```sql
-- Query soft-deleted records older than retention period
SELECT 
    patient_id,
    deleted_at,
    AGE(NOW(), deleted_at) as deletion_age
FROM patients
WHERE deleted_at IS NOT NULL
AND deleted_at < NOW() - INTERVAL '7 years'
ORDER BY deleted_at DESC;
```

- [ ] **Purge Process Documented**
  - ⚠️ TODO: Define hard-delete procedure (annual or as needed)
  - Requirement: Legal review before permanent data destruction

```sql
-- NEVER execute in production without legal approval
-- Caution: This permanently deletes data
-- BEGIN TRANSACTION;
-- DELETE FROM patients WHERE deleted_at < NOW() - INTERVAL '7 years';
-- ROLLBACK;  -- For testing only
```

---

### Database Monitoring & Anomaly Detection

- [ ] **Monitoring Setup**
  - ⚠️ TODO: Configure database monitoring tools
  - Tools: CloudWatch (AWS), Stackdriver (GCP), Datadog, New Relic

```sql
-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Monitor slow queries
SELECT 
    query,
    calls,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- Queries slower than 100ms
ORDER BY mean_time DESC;
```

- [ ] **Anomaly Alerts Configured**
  - ⚠️ TODO: Set up alerts for:
    - Unusual query patterns
    - Bulk access to patient data
    - High disk usage
    - Connection timeouts

Example alert rules:
```yaml
alerts:
  - name: bulk_patient_access
    condition: "SELECT COUNT(*) FROM audit_log WHERE table='patients' AND rows_affected > 1000 AND timestamp > NOW() - INTERVAL '5 min'"
    threshold: 1  # Any match = alert
    
  - name: after_hours_access
    condition: "EXTRACT(HOUR FROM timestamp) NOT IN (9,10,11,12,13,14,15,16,17)"
    threshold: 5 # Multiple accesses
```

---

### De-Identification & Privacy

- [ ] **De-Identification Policy**
  - ⚠️ TODO: Implement view for research (de-identified data)

```sql
-- Create de-identified view for researchers
CREATE VIEW patients_deidentified AS
SELECT 
    -- Hash the identifying info
    MD5(first_name || last_name || date_of_birth::text) as patient_hash,
    -- Keep age but not DOB
    EXTRACT(YEAR FROM AGE(NOW(), date_of_birth)) as age_years,
    -- Keep demographics
    sex,
    ethnicity,
    -- Blur timestamps to month level
    DATE_TRUNC('month', created_at) as created_month
FROM patients
WHERE deleted_at IS NULL;

-- Grant access only to researcher role
GRANT SELECT ON patients_deidentified TO researcher_group;
REVOKE SELECT ON patients FROM researcher_group;  -- No direct access
```

- [ ] **Row-Level Security (RLS) Implemented** ⭐
  - ⚠️ TODO: Clinicians see only their own patients

```sql
-- Enable RLS on patients table
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Clinician can only see patients assigned to them  
CREATE POLICY clinician_own_patients ON patients
    FOR SELECT
    USING (clinician_id = current_user_id());

-- Researcher sees only de-identified data
CREATE POLICY researcher_deidentified ON patients
    FOR SELECT
    USING (current_user_role = 'researcher')
    WITH (check (is_deidentified = true));
```

---

### Third-Party & Vendor Management

- [ ] **Vendor Security Agreements**
  - ⚠️ TODO: Verify all database hosting/cloud providers have:
    - HIPAA Business Associate Agreements (BAA)
    - SOC 2 Type II certification
    - Encryption commitments

**Recommended Providers:**
- ✅ AWS RDS (with encryption)
- ✅ Google Cloud SQL (with encryption)
- ✅ Azure Database for PostgreSQL
- ✅ Self-hosted on encrypted infrastructure

---

### Application-Level Security

- [ ] **Input Validation**
  - ✅ Alembic migrations validate schema
  - ⚠️ TODO: Application must validate inputs

```python
# Example: Validate patient data
from pydantic import BaseModel, EmailStr, constr, validator
from datetime import date

class PatientCreate(BaseModel):
    first_name: constr(min_length=1, max_length=255)
    last_name: constr(min_length=1, max_length=255)
    date_of_birth: date
    sex: str | None = None  # Optional
    ethnicity: str | None = None
    
    @validator('date_of_birth')
    def validate_dob(cls, v):
        age = (date.today() - v).days / 365.25
        if age < 0 or age > 150:
            raise ValueError('Invalid date of birth')
        return v
```

- [ ] **SQL Injection Prevention**
  - ✅ Using SQLAlchemy ORM (parameterized queries)
  - ⚠️ TODO: Never build raw SQL strings

```python
# ✅ SAFE: Using SQLAlchemy
from sqlalchemy import select
stmt = select(Patient).where(Patient.patient_id == patient_id)

# ❌ UNSAFE: Never do this
query = f"SELECT * FROM patients WHERE patient_id = '{patient_id}'"
```

---

## 🔍 Compliance Verification Commands

### Run These Regularly

```bash
# 1. Check migration status
alembic current

# 2. Verify table structure
psql -U postgres -c "\d patients"

# 3. Count active patients (should exclude soft-deleted)
psql -U postgres -c "SELECT COUNT(*) FROM patients WHERE deleted_at IS NULL;"

# 4. Verify indexes exist
psql -U postgres -c "SELECT indexname FROM pg_indexes WHERE tablename = 'patients';"

# 5. Check for encryption support
psql -U postgres -c "SELECT * FROM pg_extension WHERE extname = 'pgcrypto';"

# 6. Audit user permissions
psql -U postgres -c "\dp patients"

# 7. Verify TLS connections only
psql -U postgres -c "SHOW ssl;"
```

---

## 📊 Compliance Assessment Matrix

| Control | Status | Evidence | Next Steps |
|---------|--------|----------|-----------|
| UUID Primary Keys | ✅ Done | patient_schema.sql | - |
| Soft Delete Pattern | ✅ Done | deleted_at column | - |
| Audit Trail (created/updated_at) | ✅ Done | Timestamps in schema | - |
| Minimal PII | ✅ Done | Demographics only | Encrypt sensitive fields |
| RBAC Configuration | ⚠️ TODO | Not yet implemented | Create roles/users |
| TLS Connections | ⚠️ TODO | Not yet configured | Update connection strings |
| Encryption at Rest | ⚠️ TODO | Not yet enabled | Enable full-disk encryption |
| Query Audit Logging | ⚠️ TODO | Not yet enabled | Configure PostgreSQL logging |
| Backup Strategy | ⚠️ TODO | Not documented | Implement automated backups |
| Data Retention Policy | ⚠️ TODO | Not documented | Define by data type |
| Monitoring & Alerts | ⚠️ TODO | Not configured | Set up monitoring tools |
| De-Identification Views | ⚠️ TODO | Not created | Build researcher view |
| Row-Level Security | ⚠️ TODO | Not enabled | Enable RLS policies |
| Vendor BAA | ⚠️ TODO | Not signed | Verify provider agreements |

---

## 🚀 HIPAA Readiness Levels

### Level 1: Development ✅
- ✅ Schema designed with compliance in mind
- ✅ Soft deletes & audit trails in place
- Status: **Ready for development**

### Level 2: Testing ⚠️
- ✅ Schema finalized
- ⚠️ RBAC configured (TODO)
- ⚠️ Backups implemented (TODO)
- ⚠️ Monitoring enabled (TODO)
- Status: **In progress - target: Next Sprint**

### Level 3: Staging 🔒
- ✅ All technical controls implemented
- ⚠️ Legal review & BAAs signed (TODO)
- ⚠️ Security audit completed (TODO)
- Status: **Pre-production - target: Before Go-Live**

### Level 4: Production 🛡️
- ✅ Full compliance verified
- ✅ Monitoring active
- ✅ Response team trained
- ✅ Disaster recovery tested
- Status: **Ready for live patient data**

---

## 📞 Security Team Escalation

**Report security issues:**
- Email: `security@thergenome.io`
- Hotline: `+1-XXX-SEC-TEAM`
- Slack: `#security-incidents`

**For HIPAA-related questions:**
- Compliance Officer: `compliance@thergenome.io`
- Legal: `legal@thergenome.io`

---

## 📚 Supporting Documentation

- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)
- [HIPAA Security Technical Safeguards](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-security.html)
- [AWS HIPAA Compliance](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/)

---

## 📝 Attestation

By implementing this checklist, your TheraGenome deployment acknowledges:

- [ ] HIPAA requirements have been reviewed
- [ ] Security controls have been implemented or scheduled
- [ ] Compliance will be maintained throughout development
- [ ] Security training will be provided to all team members

**Signed By:** ___________________________ Date: ___________

**Reviewed By:** ___________________________ Date: ___________

---

**Last Updated:** March 31, 2026  
**Next Review:** June 30, 2026 (quarterly)  
**Maintained By:** Security & Compliance Team
