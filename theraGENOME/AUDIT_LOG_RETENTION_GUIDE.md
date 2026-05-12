# 6-Year Audit Log Retention Implementation Guide

## Overview

This guide implements a comprehensive 6-year audit log retention system for HIPAA compliance. The system:
- **Retains** all audit logs for 6 years (2,190 days)
- **Archives** logs older than 6 years to long-term storage
- **Deletes** logs after 7 years retention period
- **Verifies** archive integrity and completion
- **Monitors** retention compliance across all audit tables

**HIPAA Compliance Impact:** ✅ Meets 6-year documentation retention requirement (45 CFR §164.316)

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Active Database Logs                       │
│  (audit.logged_actions, access_log, query_log)              │
│  Retention: 0-6 years → Indexed for fast queries            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Daily Archival
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Retention Management Layer                       │
│  • Archive tracking table                                    │
│  • Archive procedures (PL/pgSQL)                            │
│  • Verification functions                                   │
│  • Cleanup procedures                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Monthly Archive
                     │ Weekly Backup
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           Long-Term Storage (6-7 year hold)                  │
│  • Encrypted backups on PersistentVolume                     │
│  • Optional S3 archival for disaster recovery               │
│  • Compressed tarball format with metadata                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Tables

| Table | Purpose | Retention | Growth |
|-------|---------|-----------|--------|
| `audit.logged_actions` | DML changes (INSERT/UPDATE/DELETE) | 6 years | ~1-5MB/day |
| `audit.access_log` | User access attempts | 6 years | ~100KB/day |
| `audit.query_log` | Query execution tracking | 6 years | ~500KB/day |
| `retention_management.archive_metadata` | Archive tracking | 7 years | ~10KB/archive |

**Storage Estimate:**
- Daily growth: ~6MB combined
- 6-year retention: ~13TB active database
- Compressed archive: ~30% of original size (~4TB)

---

## Phase 1: Prerequisites & Planning

### 1.1 Verify Audit Infrastructure

Confirm existing audit tables are present:

```bash
kubectl exec -it -n theragenome postgresql-0 -- psql -U theragenome_admin theragenome_dev -c "
SELECT 
  schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size('\"' || schemaname || '\".\"' || tablename || '\"')) as size
FROM pg_tables 
WHERE schemaname = 'audit'
ORDER BY tablename;"
```

Expected output:
```
 schemaname │     tablename     │  size
────────────┼───────────────────┼─────────
 audit      │ access_log        │ 124 MB
 audit      │ logged_actions    │ 2456 MB
 audit      │ query_log         │ 89 MB
```

### 1.2 Check Available Storage

Verify PersistentVolume capacity:

```bash
kubectl get pvc -n theragenome
kubectl describe pvc audit-log-archive -n theragenome
```

Expected:
```
NAME                    CAPACITY   ACCESS MODES   STATUS   
audit-log-archive       500Gi      RWO            Bound
```

### 1.3 Verify Encryption Keys

Confirm StorageClass encryption:

```bash
kubectl get storageclass encrypted-storage -o yaml | grep -A 5 "parameters:"
```

Should show KMS key ID inline.

### 1.4 Setup S3 (Optional for Cloud Archival)

If using AWS S3:

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket theragenome-audit-backups-$(date +%s) \
  --region us-east-1

# Enable versioning (for accidental deletion recovery)
aws s3api put-bucket-versioning \
  --bucket theragenome-audit-backups-XXXXX \
  --versioning-configuration Status=Enabled

# Enable server-side encryption
aws s3api put-bucket-encryption \
  --bucket theragenome-audit-backups-XXXXX \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:us-east-1:ACCOUNT:key/KEY-ID"
      }
    }]
  }'

# Set lifecycle policy (delete after 7 years + 30 days)
aws s3api put-bucket-lifecycle-configuration \
  --bucket theragenome-audit-backups-XXXXX \
  --lifecycle-configuration '{
    "Rules": [{
      "Id": "Delete-after-7-years",
      "Status": "Enabled",
      "Expiration": {"Days": 2585}
    }]
  }'
```

---

## Phase 2: Install Retention Management Schema

### 2.1 Apply Configuration

```bash
# Create ConfigMap with retention policies
kubectl apply -f k8s/17-audit-log-retention.yaml
```

Verify ConfigMap created:

```bash
kubectl get cm -n theragenome | grep retention
```

### 2.2 Execute Schema Installation

Connect to PostgreSQL and run retention policy setup:

```bash
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev \
  -f /dev/stdin << 'SQL'
-- Source the retention policy SQL from ConfigMap
\copy (SELECT pg_catalog.current_database()) to '/tmp/db.txt'
SELECT * FROM (VALUES (pg_read_file('/etc/postgresql-config/retention-policy.sql'))) as content;
SQL
```

**Alternative (direct SQL):**

```bash
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  theragenome_dev << 'EOF'
-- Copy and paste the SQL from k8s/17-audit-log-retention.yaml
-- [retention-policy.sql section]
EOF
```

### 2.3 Verify Schema Installation

```bash
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c "
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_schema = 'retention_management'
ORDER BY routine_name;"
```

Expected output:
```
     routine_name      │ routine_type
──────────────────────┼──────────────
 archive_old_logs     │ PROCEDURE
 cleanup_expired_logs │ PROCEDURE
 verify_archive       │ FUNCTION
```

---

## Phase 3: Deploy Archival CronJob

### 3.1 Create PersistentVolumeClaim

```bash
# Extract PVC from manifest
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: audit-log-archive
  namespace: theragenome
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: encrypted-storage
  resources:
    requests:
      storage: 500Gi
EOF
```

Wait for PVC to bind:

```bash
kubectl get pvc -n theragenome audit-log-archive -w
```

### 3.2 Deploy Archival CronJob (Daily at 3 AM UTC)

```bash
# Apply archival CronJob
kubectl apply -f k8s/17-audit-log-retention.yaml -n theragenome
```

Verify deployment:

```bash
kubectl get cronjob -n theragenome | grep audit
```

Expected:
```
NAME                         SCHEDULE     SUSPEND   ACTIVE   LAST SCHEDULE
audit-log-archiver           0 3 * * *    False     0        12m
audit-log-cleanup            0 4 1 * *    False     0        <none>
audit-log-backup             0 1 * * 0    False     0        2d
```

### 3.3 Test Archival Manually (First Run)

Trigger immediate archival:

```bash
# Create manual Job for testing
kubectl create job --from=cronjob/audit-log-archiver \
  -n theragenome \
  audit-archiver-test-$(date +%s)

# Watch logs
kubectl logs -n theragenome -l job-name -f --tail=50
```

Expected log output:
```
Starting audit log archival...
Archiving 15234 records from audit.logged_actions
Archiving 2156 records from audit.access_log
Archiving 4892 records from audit.query_log
Archival completed in 42s
```

### 3.4 Verify Archive Metadata

```bash
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c "
SELECT source_table, records_archived, archive_file_path, 
       archive_date, retention_until
FROM retention_management.archive_metadata
ORDER BY archive_date DESC
LIMIT 5;"
```

---

## Phase 4: Deploy Cleanup CronJob

### 4.1 Deploy Monthly Cleanup (First of Month at 4 AM UTC)

```bash
# Already included in 17-audit-log-retention.yaml
kubectl get cronjob -n theragenome audit-log-cleanup -o yaml
```

### 4.2 Verify Cleanup Configuration

```bash
kubectl get cronjob -n theragenome audit-log-cleanup -o jsonpath='{.spec.schedule}'
# Output: 0 4 1 * *  (First day of month, 4 AM UTC)
```

### 4.3 Review Cleanup Logic

The cleanup procedure:
1. Identifies logs older than **7 years** (2,555 days)
2. Verifies archives exist for those records
3. Only deletes records if corresponding archive is **verified**
4. Reports deletion count for audit trail

This 1-year safety window (6-year retention + 1-year deletion delay) ensures:
- ✅ Archives are verified before deletion
- ✅ Recovery possible if archive verification fails
- ✅ Manual archive inspection possible
- ✅ HIPAA compliance maintained

---

## Phase 5: Deploy Backup CronJob

### 5.1 Deploy Weekly Backup (Sunday 1 AM UTC)

```bash
# Already included in 17-audit-log-retention.yaml
kubectl get cronjob -n theragenome audit-log-backup -o yaml
```

### 5.2 Test Backup Manually

```bash
# Trigger manual backup job
kubectl create job --from=cronjob/audit-log-backup \
  -n theragenome \
  audit-backup-test-$(date +%s)

# Monitor
kubectl logs -n theragenome -l job-name -f
```

### 5.3 Verify S3 Upload (if configured)

```bash
# Check S3 bucket
aws s3 ls s3://theragenome-audit-backups/weekly-backups/ --recursive

# Get backup details
aws s3api head-object \
  --bucket theragenome-audit-backups \
  --key weekly-backups/audit_backup_20260402_010000.tar.gz
```

---

## Phase 6: Setup Archive Monitoring & Reporting

### 6.1 Create Monitoring ConfigMap

```bash
# Already in 17-audit-log-retention.yaml as "audit-log-monitoring"
kubectl get cm -n theragenome audit-log-monitoring -o yaml
```

### 6.2 Run Retention Status Report

```bash
# Connect to database
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev << 'EOF'

-- Total logs by age (monitor disk growth)
SELECT 
  'logged_actions' as table_name,
  DATE_TRUNC('year', action_tstamp_tx)::DATE as year,
  COUNT(*) as record_count,
  ROUND(SUM(OCTET_LENGTH(row_data::TEXT)) / 1024 / 1024, 2) as size_mb
FROM audit.logged_actions
GROUP BY DATE_TRUNC('year', action_tstamp_tx)
UNION ALL
SELECT
  'access_log',
  DATE_TRUNC('year', access_time)::DATE,
  COUNT(*),
  ROUND(SUM(OCTET_LENGTH(reason::TEXT)) / 1024 / 1024, 2)
FROM audit.access_log
GROUP BY DATE_TRUNC('year', access_time)
ORDER BY year DESC;

EOF
```

### 6.3 Archive Status Dashboard

```bash
# Get archive summary
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c "
SELECT 
  source_table,
  COUNT(*) as total_archives,
  SUM(records_archived) as total_records_archived,
  COUNT(CASE WHEN verified THEN 1 END) as verified_count,
  ROUND(AVG(EXTRACT(EPOCH FROM (verified_date - archive_date))), 0) as avg_verification_secs
FROM retention_management.archive_metadata
GROUP BY source_table;"
```

### 6.4 Compliance Status

```bash
# Check if all archives within retention period
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c "
SELECT 
  'COMPLIANT' as status,
  COUNT(*) as total_archives,
  COUNT(CASE WHEN retention_until > NOW() THEN 1 END) as within_retention,
  COUNT(CASE WHEN verified THEN 1 END) as verified,
  MIN(retention_until) as earliest_retention_date,
  MAX(retention_until) as latest_retention_date
FROM retention_management.archive_metadata;"
```

---

## Phase 7: Verification & Testing

### 7.1 Verify Archive Integrity

Test archive verification function:

```bash
# Get recent archive ID
ARCHIVE_ID=$(kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -tc "
SELECT archive_id FROM retention_management.archive_metadata 
ORDER BY archive_date DESC LIMIT 1")

# Verify it
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c "
SELECT * FROM retention_management.verify_archive($ARCHIVE_ID);"
```

### 7.2 Test Recovery from Archive

Simulate archive recovery:

```bash
# List an archived backup
kubectl exec -it -n theragenome postgresql-0 -- ls -lh /audit-archive/

# Restore test (extract to verify)
kubectl exec -it -n theragenome postgresql-0 -- \
  tar -tzf /audit-archive/logs_2026_04_02_0300.sql.gz | head -20
```

### 7.3 Validate Compression

```bash
# Check archive sizes
kubectl exec -it -n theragenome postgresql-0 -- bash -c "
echo '=== Archive Sizes ==='
du -sh /audit-archive/*
echo '=== Compression Ratio ==='
ls -lS /audit-archive/ | awk '{print \$9, \$5}' | tail -5"
```

### 7.4 Performance Impact Test

Run archival during low-traffic window and monitor:

```bash
# Monitor database load during archival
watch -n 2 "kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev -c \
  'SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = \"active\";'"
```

---

## Phase 8: Monitoring & Alerts

### 8.1 Add Prometheus Metrics

Add job to Prometheus scrape config to track archival success:

```yaml
# In k8s/13-prometheus-monitoring.yaml, add:
  - job_name: 'audit-retention'
    static_configs:
      - targets: ['localhost:9187']
    relabel_configs:
      - source_labels: [__param_target]
        target_label: instance
```

### 8.2 Archive Size Alert

Monitor archive directory growth:

```bash
# Create alert rule
kubectl exec -it -n theragenome postgresql-0 -- bash -c "
du -sk /audit-archive | awk '{print \$1/1024/1024 \" GB\"}'"
```

Alert when:
- Archive size > 450GB (90% of 500GB PVC)
- Archive growth > 50GB/month (unusual)
- Archival job failures > 2 consecutive runs

### 8.3 Cleanup Verification

Verify cleanup runs successfully:

```bash
# Check cleanup job status
kubectl get jobs -n theragenome | grep cleanup

# View cleanup logs
kubectl logs -n theragenome -l job-name=audit-log-cleanup-xxxxx --all-containers
```

---

## Phase 9: Documentation & Compliance

### 9.1 Retention Policy Document

Save this document as: `AUDIT_RETENTION_POLICY.txt`

```text
AUDIT LOG RETENTION POLICY
TheraGenome - HIPAA Compliance

1. RETENTION PERIOD
   - Active retention: 6 years (2,190 days) in PostgreSQL
   - Archive retention: 7 years (2,555 days) on encrypted storage
   - Safety window: 1 year (365 days) between archive and deletion

2. ARCHIVAL SCHEDULE
   - Daily: 3:00 AM UTC - Archive logs older than 6 years
   - Weekly: 1:00 AM UTC Sunday - Backup all archives to S3
   - Monthly: 4:00 AM UTC 1st - Delete logs older than 7 years (post-verification)

3. STORAGE
   - Active database: ~13TB (6-year retention)
   - Backup storage: ~4TB (compressed, encrypted)
   - Total S3: Lifecycle delete after 2,585 days

4. VERIFICATION
   - Archive integrity verified before deletion
   - All archives encrypted with AES-256
   - Backup verification: Weekly test restore

5. COMPLIANCE IMPACT
   - Meets 45 CFR §164.316 (Documentation)
   - Demonstrates HIPAA readiness for audit
   - Provides evidence for compliance verification

6. RESPONSIBLE PARTIES
   - Database Administrator: Monitor archival jobs
   - Compliance Officer: Quarterly retention audit
   - Security Team: Verify encryption and access controls

7. INCIDENT REPORTING
   - Archival failure: Page on-call DBA
   - Verification failure: Security incident response
   - Manual deletion: Requires 2-person approval + audit log
```

### 9.2 Audit Trail of Archival

Create audit table entry for all archival operations:

```bash
# Log each archival run (append to compliance audit log)
kubectl exec -it -n theragenome postgresql-0 -- psql \
  -U theragenome_admin \
  -d theragenome_dev << 'EOF'
INSERT INTO audit.access_log (
  access_time, user_name, client_address, action, reason, status
) VALUES (
  NOW(),
  'retention_service',
  '10.0.0.0',
  'ARCHIVAL',
  'Scheduled audit log archival - 6-year retention',
  'SUCCESS'
);
EOF
```

---

## Troubleshooting

### Issue: Archival Job Fails with "Disk Space"

**Symptom:**
```
ERROR: could not write to directory '/audit-archive'
```

**Solution:**
1. Check PVC usage: `kubectl get pvc audit-log-archive -o wide`
2. Increase PVC size if needed (requires deletion and recreation)
3. Manually clean old archives if necessary

### Issue: Cleanup Deletes Unverified Archives

**Symptom:**
```
WARNING: Attempting to delete 50000 records with unverified archive
```

**Prevention:**
- Cleanup only runs if `verified = TRUE`
- Check verification status: `SELECT * FROM retention_management.archive_metadata WHERE verified = FALSE`

### Issue: Archival Job Timeout

**Symptom:**
```
Job exceeded 3600 second timeout
```

**Solution:**
1. Monitor log sizes: Archives > 1GB may need timeout increase
2. Adjust `backoffLimit` in CronJob spec
3. Run archival during low-traffic window (already configured: 3 AM UTC)

### Issue: S3 Upload Fails

**Symptom:**
```
ERROR: Access Denied for S3 bucket operation
```

**Solution:**
1. Verify AWS credentials in pod environment
2. Check IAM policy for s3:PutObject permission
3. Verify bucket exists in correct region
4. Test manually: `aws s3 ls s3://bucket-name/`

---

## Compliance Verification Checklist

Before production deployment, verify:

- [ ] Retention policy SQL schema installed
- [ ] All 3 archival CronJobs deployed and tested
- [ ] Archive PersistentVolume encrypted
- [ ] First archival job completed successfully
- [ ] Archive metadata tracked in database
- [ ] S3 lifecycle policy configured (if using cloud)
- [ ] Backup restoration tested
- [ ] Monitoring alerts configured
- [ ] Team trained on recovery procedures
- [ ] Compliance documentation signed

**Implementation Time:** 2-4 hours
**Ongoing Maintenance:** 30 min/month (monitoring)
**Team Training:** 1 hour

---

## Status Summary

✅ **Item 9 Complete: 6-Year Audit Log Retention**

**What's Implemented:**
- Daily archival (3 AM UTC) via PL/pgSQL procedures
- Monthly cleanup (1st of month, 4 AM UTC) with verification gates
- Weekly backups (Sunday 1 AM UTC) to encrypted S3
- Archive metadata tracking with integrity verification
- Automatic encryption on archives and backups

**Compliance Impact:**
- Demonstrates HIPAA documentation retention (45 CFR §164.316)
- Provides audit trail of all archival operations
- Enables compliance officer to verify retention policy execution

**Production Readiness:**
- All CronJobs configured with retry logic
- Resource limits set to prevent resource exhaustion
- Error handling with descriptive logging
- Manual testing procedures documented

**Next Steps:**
1. Apply manifests: `kubectl apply -f k8s/17-audit-log-retention.yaml`
2. Test first archival run manually
3. Train team on retention procedures
4. Move to Item #7: Business Associate Agreements (BAA)

