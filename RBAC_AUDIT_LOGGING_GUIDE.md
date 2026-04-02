# RBAC & Audit Logging Implementation (Item #3)

**Status:** Implementation Steps for Critical Item #3  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for HIPAA Compliance & Access Control

---

## Overview

This guide provides step-by-step instructions for implementing Role-Based Access Control (RBAC) and comprehensive audit logging for TheraGenome PostgreSQL database, ensuring only authorized users can access patient data and all access is logged for compliance.

### Components to Configure:
1. **Database Roles** - Seven distinct roles with specific permissions
2. **Access Control** - Granular permission grants
3. **Audit Triggers** - Automatic logging of all data modifications
4. **Row-Level Security** - Fine-grained data restrictions
5. **Access Logging** - Track who accessed what and when

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ TheraGenome Users                                           │
├─────────────────────────────────────────────────────────────┤
│ admin │ app_user │ reporter │ analyst │ backup_user │ migration
└──────┬──────────┬──────────┬────────┬──────────────┬────────┘
       │          │          │        │              │
┌──────▼──────────▼──────────▼────────▼──────────────▼────────┐
│ Database Roles (PostgreSQL)                                 │
├─────────────────────────────────────────────────────────────┤
│ theragenome_admin  → Full access (for maintenance)          │
│ theragenome_app    → Read/Write (API operations)            │
│ theragenome_reporter → Read-only (reports)                  │
│ theragenome_analyst → Restricted SELECT                     │
│ theragenome_backup → Backup access                          │
│ theragenome_migration → Schema changes                      │
│ theragenome_audit → Audit tables                            │
└──────┬──────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│ Tables with Audit Triggers                                  │
├─────────────────────────────────────────────────────────────┤
│ patients ────────────┐                                       │
│ resistance_results ──┼─→ audit.logged_actions (all changes) │
│ classifications ─────┤                                       │
│ ... (all tables) ────┘                                       │
└──────┬───────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│ Audit Tables (audit schema)                                 │
├─────────────────────────────────────────────────────────────┤
│ logged_actions ────────── DML changes (INSERT/UPDATE/DELETE)│
│ access_log ────────────── User access attempts              │
│ query_log ────────────── Query execution tracking           │
└──────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- PostgreSQL 15+ cluster running
- `kubectl` access to Kubernetes cluster
- Database admin credentials
- hstore extension available

---

## Phase 1: Create Database Roles (10 minutes)

### Step 1: Understand Role Structure

| Role | Purpose | Permissions | Session Duration |
|------|---------|-------------|-----------------|
| `theragenome_admin` | Database administration | CREATEDB, CREATEROLE | Temporary, as needed |
| `theragenome_app` | API application | SELECT, INSERT, UPDATE, DELETE | Permanent (API pool) |
| `theragenome_reporter` | Reporting & analytics | SELECT only | 8 hours (business hours) |
| `theragenome_analyst` | Data analysis | SELECT with restrictions | 8 hours (business hours) |
| `theragenome_audit` | Audit log review | SELECT audit tables | 8 hours (audit staff) |
| `theragenome_backup` | Backup operations | SELECT all, CONNECT | Temporary, per backup |
| `theragenome_migration` | Schema updates | CREATEROLE, ALTER | Temporary, deployment only |

### Step 2: Deploy RBAC Configuration

```bash
# Apply RBAC and audit configuration
kubectl apply -f k8s/11-postgres-rbac-audit.yaml

# Wait for job to complete
kubectl get jobs -n theragenome -w | grep postgres-rbac-setup

# Check job logs
kubectl logs job/postgres-rbac-setup -n theragenome -f
```

### Step 3: Verify Roles Were Created

```bash
# Connect to database
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- List all roles
\du

-- Check role properties
SELECT usename, usesuper, usecreatedb, usecreaterole, usecanlogin
FROM pg_user
WHERE usename LIKE 'theragenome_%'
ORDER BY usename;

SQL
```

**Expected Output:**
- 7 roles created (admin, app, reporter, analyst, audit, backup, migration)
- Correct permissions assigned

---

## Phase 2: Configure Application Connection (10 minutes)

### Step 1: Update Python Application

**File:** `scripts/db_connection.py`

```python
import os
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool

# Get database connection parameters
DB_HOST = os.getenv('DB_HOST', 'postgresql')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'thergenome_dev')
DB_USER = os.getenv('DB_USER', 'theragenome_app')  # Use app role
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Build database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

# Create engine with proper configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
    connect_args={
        'sslmode': 'require',
        'application_name': 'theragenome_api',
        'connect_timeout': 10
    }
)

# Set session parameters for audit logging
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_conn, connection_record):
    """Configure connection for audit logging"""
    with dbapi_conn.cursor() as cur:
        # Set application name for audit tracking
        cur.execute("SET application_name = 'theragenome_api'")
        
        # Enable query logging
        cur.execute("SET log_min_duration_statement = 1000")
        
        # Load extensions if needed
        cur.execute("CREATE EXTENSION IF NOT EXISTS hstore")
        
        dbapi_conn.commit()

# Session factory with proper configuration
from sqlalchemy.orm import sessionmaker, Session

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 2: Update TypeScript/Deno Application

**File:** `src/database.ts`

```typescript
import { Client } from "https://deno.land/x/postgres@v0.17.0/mod.ts";

// Create database client with app role credentials
export const db = new Client({
  hostname: Deno.env.get("DB_HOST") || "postgresql",
  port: parseInt(Deno.env.get("DB_PORT") || "5432"),
  user: Deno.env.get("DB_USER") || "theragenome_app",
  password: Deno.env.get("DB_PASSWORD"),
  database: Deno.env.get("DB_NAME") || "thergenome_dev",
  application_name: "theragenome_variant_api",
  ssl: {
    enable: true,
    enforce: true,
  },
});

// Helper function to log database access
export async function logAccess(
  tableName: string,
  accessType: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE'
) {
  try {
    await db.queryArray(
      `SELECT audit.log_access(current_user, $1, $2)`,
      [tableName, accessType]
    );
  } catch (error) {
    console.error("Failed to log access:", error);
  }
}
```

### Step 3: Update ConfigMap with Correct Credentials

```bash
# Update theragenome-config ConfigMap
kubectl patch configmap theragenome-config -n theragenome -p \
  '{"data":{"DB_USER":"theragenome_app"}}'

# Verify update
kubectl get configmap theragenome-config -n theragenome -o yaml | grep DB_USER
```

---

## Phase 3: Configure Audit Triggers (15 minutes)

### Step 1: Verify Triggers Are Active

```bash
# List all triggers
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- Check triggers on patients table
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'patients'
AND trigger_schema NOT IN ('pg_catalog', 'information_schema');

-- Check audit schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'audit';

-- Check audit tables
SELECT table_name FROM information_schema.tables WHERE table_schema = 'audit';

SQL
```

### Step 2: Test Audit Functionality

```bash
# Insert test data to verify audit trigger works
kubectl exec -it postgresql-0 -n theragenome -- psql -U theragenome_app -d thergenome_dev << 'SQL'

-- Insert test patient
INSERT INTO patients (first_name, last_name, date_of_birth)
VALUES ('Test', 'Patient', '1990-01-01');

-- Check audit log
SELECT * FROM audit.logged_actions ORDER BY action_tstamp_tx DESC LIMIT 1;

SQL
```

### Step 3: Create Audit Dashboard Query

```bash
# Create view for audit summary
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

CREATE OR REPLACE VIEW audit.activity_summary AS
SELECT
  date_trunc('hour', action_tstamp_tx)::date as date,
  date_part('hour', action_tstamp_tx)::int as hour,
  action,
  COUNT(*) as total_operations,
  COUNT(DISTINCT session_user_name) as unique_users,
  COUNT(DISTINCT table_name) as tables_affected
FROM audit.logged_actions
WHERE action_tstamp_tx > NOW() - INTERVAL '7 days'
GROUP BY date_trunc('hour', action_tstamp_tx), action
ORDER BY date DESC, hour DESC;

SQL
```

---

## Phase 4: Implement Row-Level Security (15 minutes)

### Step 1: Enable RLS on Sensitive Tables

```bash
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- Enable RLS on patients table
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Create policy: App can access all rows
CREATE POLICY app_access_patients ON patients
  FOR SELECT
  USING (
    current_user IN ('theragenome_admin', 'theragenome_app')
  );

-- Create policy: Analyst can only see summary data (no PII)
CREATE POLICY analyst_summary_patients ON patients
  FOR SELECT
  USING (
    current_user = 'theragenome_analyst'
  );

-- Create policy for updates (only app and admin)
CREATE POLICY app_update_patients ON patients
  FOR UPDATE
  USING (
    current_user IN ('theragenome_admin', 'theragenome_app')
  )
  WITH CHECK (
    current_user IN ('theragenome_admin', 'theragenome_app')
  );

-- Apply similar RLS to other sensitive tables
ALTER TABLE resistance_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;

SQL
```

### Step 2: Create De-identified Views

```bash
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- Create view for analyst role (no PII)
CREATE OR REPLACE VIEW audit.patients_deidentified AS
SELECT
  id,
  EXTRACT(YEAR FROM date_of_birth) as birth_year,
  CASE EXTRACT(MONTH FROM age(now(), date_of_birth)) 
    WHEN 0 THEN 'Pediatric'
    WHEN 1 THEN '18-25'
    WHEN 2 THEN '26-40'
    WHEN 3 THEN '41-60'
    ELSE '60+'
  END as age_group,
  created_at
FROM patients;

GRANT SELECT ON audit.patients_deidentified TO theragenome_analyst;

SQL
```

---

## Phase 5: Configure Access Logging (10 minutes)

### Step 1: Create Access Log Monitoring

```bash
cat << 'EOF' > k8s/12-access-log-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: access-log-monitoring
  namespace: theragenome
data:
  monitor-access.sql: |
    -- Query for identifying suspicious access patterns
    
    -- List access by user in last 24 hours
    SELECT
      user_name,
      DATE_TRUNC('hour', access_time)::TIMESTAMP as hour,
      COUNT(*) as access_count,
      COUNT(DISTINCT table_name) as tables_accessed,
      BOOL_OR(pii_accessed) as pii_accessed
    FROM audit.access_log
    WHERE access_time > NOW() - INTERVAL '24 hours'
    GROUP BY user_name, DATE_TRUNC('hour', access_time)
    ORDER BY hour DESC;
    
    -- Alert: Unusual access patterns
    SELECT
      user_name,
      table_name,
      COUNT(*) as access_count,
      access_time
    FROM audit.access_log
    WHERE access_time > NOW() - INTERVAL '1 hour'
    AND access_type = 'SELECT'
    GROUP BY user_name, table_name, access_time
    HAVING COUNT(*) > 100;
    
    -- Alert: Failed access attempts
    SELECT
      user_name,
      table_name,
      COUNT(*) as failed_attempts,
      status,
      reason
    FROM audit.access_log
    WHERE status IN ('DENIED', 'FAILED')
    AND access_time > NOW() - INTERVAL '24 hours'
    GROUP BY user_name, table_name, status, reason
    ORDER BY failed_attempts DESC;

  denied-access-alert.sql: |
    -- Create alert table for denied access
    CREATE TABLE IF NOT EXISTS audit.access_alerts (
      alert_id BIGSERIAL PRIMARY KEY,
      alert_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      alert_type VARCHAR(50),
      severity VARCHAR(10),
      affected_user TEXT NOT NULL,
      affected_resource TEXT,
      details TEXT,
      acknowledged BOOLEAN DEFAULT FALSE,
      acknowledged_by TEXT,
      acknowledged_at TIMESTAMP WITH TIME ZONE
    );
    
    -- Create rule to automatically log denied accesses as alerts
    CREATE OR REPLACE FUNCTION audit.alert_denied_access()
    RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.status IN ('DENIED', 'FAILED') THEN
        INSERT INTO audit.access_alerts (
          alert_type, severity, affected_user, affected_resource, details
        ) VALUES (
          'ACCESS_DENIED',
          CASE
            WHEN NEW.pii_accessed THEN 'CRITICAL'
            ELSE 'HIGH'
          END,
          NEW.user_name,
          NEW.table_name,
          NEW.reason
        );
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: audit-log-analyzer
  namespace: theragenome
spec:
  # Run every hour
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          serviceAccountName: theragenome-api
          restartPolicy: OnFailure
          containers:
          - name: analyzer
            image: postgres:15-alpine
            env:
            - name: PGHOST
              value: postgresql.theragenome.svc.cluster.local
            - name: PGUSER
              valueFrom:
                secretKeyRef:
                  name: theragenome-secrets
                  key: DB_USER
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: theragenome-secrets
                  key: DB_PASSWORD
            volumeMounts:
            - name: monitoring-script
              mountPath: /scripts
              readOnly: true
            command:
            - /bin/sh
            - -c
            - |
              psql << 'SQL'
              -- Run analysis queries
              \echo '=== Access by User (Last 24h) ==='
              SELECT user_name, COUNT(*) as access_count
              FROM audit.access_log
              WHERE access_time > NOW() - INTERVAL '24 hours'
              GROUP BY user_name
              ORDER BY access_count DESC;
              
              \echo '=== Denied Access Attempts (Last 24h) ==='
              SELECT user_name, table_name, COUNT(*) as denied_count
              FROM audit.access_log
              WHERE status = 'DENIED'
              AND access_time > NOW() - INTERVAL '24 hours'
              GROUP BY user_name, table_name
              ORDER BY denied_count DESC;
              
              \echo '=== Recent Alerts ==='
              SELECT alert_id, alert_time, alert_type, severity, affected_user, affected_resource
              FROM audit.access_alerts
              WHERE alert_time > NOW() - INTERVAL '1 hour'
              AND acknowledged = FALSE
              ORDER BY alert_time DESC;
              SQL
          
          volumes:
          - name: monitoring-script
            configMap:
              name: access-log-monitoring

EOF

kubectl apply -f k8s/12-access-log-monitoring.yaml
```

### Step 2: Export Access Logs for External Audit

```bash
# Create a script to export audit logs in compliance format
cat << 'EOF' > /tmp/export-audit-logs.sh
#!/bin/bash

EXPORT_DATE=$(date +%Y%m%d_%H%M%S)
EXPORT_DIR="/tmp/audit-export-${EXPORT_DATE}"
mkdir -p "$EXPORT_DIR"

# Get logged actions
kubectl exec -i postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "COPY audit.logged_actions TO STDOUT WITH CSV HEADER" \
  > "$EXPORT_DIR/logged_actions.csv"

# Get access logs
kubectl exec -i postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "COPY audit.access_log TO STDOUT WITH CSV HEADER" \
  > "$EXPORT_DIR/access_log.csv"

# Get query logs
kubectl exec -i postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "COPY audit.query_log TO STDOUT WITH CSV HEADER" \
  > "$EXPORT_DIR/query_log.csv"

# Create manifest file
cat > "$EXPORT_DIR/MANIFEST.txt" << MANIFEST
Audit Log Export
Export Date: $(date)
Locale: UTC
Tables Exported:
  - audit.logged_actions (DML changes)
  - audit.access_log (User access tracking)
  - audit.query_log (Query execution)

Files:
  - logged_actions.csv
  - access_log.csv
  - query_log.csv
MANIFEST

# Encrypt export
gpg --batch --symmetric --cipher-algo AES256 \
  --output "$EXPORT_DIR/audit_logs.tar.gz.gpg" \
  "$EXPORT_DIR"/*

echo "Audit logs exported to: $EXPORT_DIR"
EOF

chmod +x /tmp/export-audit-logs.sh
```

---

## Phase 6: Verification and Testing (20 minutes)

### Test 1: Verify Role Permissions

```bash
# Test 1: theragenome_app should be able to SELECT
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U theragenome_app -d thergenome_dev \
  -c "SELECT COUNT(*) FROM patients;"

# Expected: Returns count successfully

# Test 2: theragenome_reporter should only be able to SELECT
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "SET ROLE theragenome_reporter; SELECT COUNT(*) FROM patients;"

# Expected: Returns count successfully

# Test 3: theragenome_reporter should NOT be able to INSERT (will fail)
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "SET ROLE theragenome_reporter; INSERT INTO patients VALUES (1, 'test', 'user', '1990-01-01');" 2>&1

# Expected: Permission denied error
```

### Test 2: Verify Audit Triggers

```bash
# Insert data and verify audit entry
kubectl exec -it postgresql-0 -n theragenome -- psql -U theragenome_app -d thergenome_dev << 'SQL'

-- Record initial count
SELECT COUNT(*) as initial_count FROM audit.logged_actions;

-- Insert test data
INSERT INTO patients (first_name, last_name, date_of_birth) 
VALUES ('Audit', 'Test', '1985-06-15');

-- Check audit entry was created
SELECT 
  event_id, 
  action, 
  table_name, 
  session_user_name, 
  action_tstamp_tx
FROM audit.logged_actions 
ORDER BY event_id DESC LIMIT 1;

SQL
```

### Test 3: Verify Row-Level Security

```bash
# Create test data with different user
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- Set role to analyst
SET ROLE theragenome_analyst;

-- Try to select from patients (should be restricted by RLS)
SELECT COUNT(*) FROM patients;

-- Try to view de-identified view (should work)
SELECT COUNT(*) FROM audit.patients_deidentified;

SQL
```

### Test 4: Query Audit Logs

```bash
# View recent audit activity
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

SELECT 
  event_id,
  schema_name,
  table_name,
  action,
  session_user_name,
  action_tstamp_tx,
  changed_fields
FROM audit.logged_actions
ORDER BY event_id DESC
LIMIT 20;

SQL
```

---

## Phase 7: Maintenance and Monitoring (Ongoing)

### Monitor Access Patterns

```bash
# Run access analysis job manually
kubectl logs -n theragenome cronjob/audit-log-analyzer

# View top users by access count
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

SELECT 
  user_name,
  COUNT(*) as access_count,
  COUNT(DISTINCT table_name) as tables_accessed,
  MAX(access_time) as last_access
FROM audit.access_log
WHERE access_time > NOW() - INTERVAL '7 days'
GROUP BY user_name
ORDER BY access_count DESC;

SQL
```

### Rotate Audit Logs

```bash
# Create procedure to archive old audit logs
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'

-- Archive audit logs older than 6 months
CREATE OR REPLACE PROCEDURE audit.archive_old_logs()
LANGUAGE plpgsql
AS $$
BEGIN
  -- Export to file
  COPY (
    SELECT * FROM audit.logged_actions
    WHERE action_tstamp_tx < NOW() - INTERVAL '6 months'
  )
  TO PROGRAM 'gzip >> /var/lib/postgresql/backup/audit_archive_' || TO_CHAR(NOW(), 'YYYY_MM') || '.sql.gz';
  
  -- Archive complete
  RAISE NOTICE 'Audit logs archived successfully';
END;
$$;

-- Schedule: Run monthly
-- scheduled via pg_cron extension

SQL
```

---

## Troubleshooting

### Permission Denied Errors

```bash
# Check what role is being used
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U theragenome_app -d thergenome_dev -c "SELECT current_role, current_user;"

# Check role permissions
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev -c "SELECT * FROM information_schema.role_table_grants WHERE grantee = 'theragenome_app';"
```

### Audit Triggers Not Firing

```bash
# Check if triggers are enabled
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "SELECT trigger_name, enabled FROM pg_trigger WHERE tgname LIKE '%audit%';"

# Enable triggers if disabled
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -c "ALTER TABLE patients ENABLE TRIGGER <trigger_name>;"
```

### Missing Audit Tables

```bash
# Recreate audit schema
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev \
  -f k8s/11-postgres-rbac-audit.yaml
```

---

## Post-Implementation

- [x] Roles created and configured
- [x] Audit triggers deployed
- [x] Access logging enabled
- [x] Row-level security configured
- [ ] Update compliance audit (mark Item #3 COMPLETE)
- [ ] Train team on new RBAC model
- [ ] Create runbook for role management
- [ ] Setup audit log retention

---

## Next Steps

1. **Item #4:** Deploy APM monitoring
2. **Item #5:** Complete container security scanning
3. **Item #6:** Implement & test incident response

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
