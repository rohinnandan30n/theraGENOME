# Incident Response Plan & Testing (Item #6)

**Status:** Implementation Steps for Critical Item #6  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for HIPAA Compliance & Business Continuity

---

## Overview

This guide provides comprehensive incident response procedures for TheraGenome, including classification, escalation, response playbooks, and testing procedures to ensure rapid recovery from security and operational incidents.

### Components to Configure:
1. **Incident Classification** - Severity levels and impact assessment
2. **Response Procedures** - Playbooks for common incidents
3. **Communication** - Notification and escalation procedures
4. **Technical Recovery** - Step-by-step recovery playbooks
5. **Post-Incident** - Review and improvement process
6. **Drills & Testing** - Regular scenario testing

---

## Incident Classification

| Severity | Response Time | Scope | Examples |
|----------|---------------|-------|----------|
| **P1 - CRITICAL** | 15 minutes | All systems affected | Data breach, complete outage, ransomware detected |
| **P2 - HIGH** | 1 hour | Major service degradation | API latency >5s, database connection pool exhausted |
| **P3 - MEDIUM** | 4 hours | Minor service impact | Single API endpoint down, elevated error rate |
| **P4 - LOW** | 1 business day | Limited impact | Non-critical feature unavailable, informational alert |

---

## Part 1: Incident Response Team & Roles

### On-Call Rotation

```yaml
# Incident Response Team

On-Call Schedule:
  Primary Responder: Rotates weekly (Monday-Sunday)
  Database Administrator: Always available
  Security Lead: On-call for security incidents
  Product Owner: Available for business decisions

Contact Information (UPDATE WITH REAL CONTACTS):
  Primary Responder: oncall@theragenome.com
  Escalation: security-team@theragenome.com
  Executive Escalation: cto@theragenome.com
  External: Compliance Officer, HIPAA Attorney
```

### Role Responsibilities

```markdown
# Incident Commander (IC)
- [ ] Declare incident and severity level
- [ ] Assemble response team
- [ ] Coordinate communication
- [ ] Make critical decisions
- [ ] Schedule post-incident review

# Technical Lead
- [ ] Diagnose root cause
- [ ] Implement fixes
- [ ] Coordinate rollback if needed
- [ ] Provide technical updates

# Communications Lead
- [ ] Update status page
- [ ] Notify affected users
- [ ] Prepare external statements
- [ ] Track communication timeline

# Security Lead
- [ ] Assess security impact
- [ ] Preserve evidence
- [ ] Coordinate with legal/compliance
- [ ] Post-incident forensics
```

---

## Part 2: Incident Response Playbooks

### Playbook 1: API Service Degradation

**Trigger:** Error rate > 5% OR latency p95 > 5 seconds

**Response Steps:**

1. **Initial Assessment** (5 min)
   ```bash
   # Check current metrics
   kubectl top nodes
   kubectl top pods -n theragenome
   
   # Watch pod logs
   kubectl logs -f deployment/theragenome-api -n theragenome
   
   # Check database status
   kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres \
     -c "SELECT datname, numbackends FROM pg_stat_database WHERE datname = 'thergenome_dev';"
   ```

2. **Scale Investigation** (5-10 min)
   ```bash
   # Check current replicas
   kubectl get deployment theragenome-api -n theragenome -o wide
   
   # Check HPA status
   kubectl get hpa theragenome-api -n theragenome
   
   # View events
   kubectl describe deployment theragenome-api -n theragenome
   ```

3. **Immediate Mitigation** (if P1)
   ```bash
   # Option A: Scale up deployment
   kubectl scale deployment theragenome-api --replicas=5 -n theragenome
   
   # Option B: Rollback to previous version
   kubectl rollout undo deployment/theragenome-api -n theragenome
   ```

4. **Root Cause Analysis** (ongoing)
   - [ ] Check database query performance (slow queries)
   - [ ] Check external service dependencies
   - [ ] Review recent code changes
   - [ ] Check resource constraints
   - [ ] Review APM traces for bottlenecks

5. **Resolution**
   - Option 1: Deploy fix
   - Option 2: Rollback changes
   - Option 3: Scale infrastructure

6. **Communication**
   - Update status page every 15 minutes
   - Notify affected users via email
   - Post incident summary

---

### Playbook 2: Database Connection Pool Exhaustion

**Trigger:** `pg_stat_activity_count > 80`

**Response Steps:**

1. **Immediate Assessment** (2 min)
   ```bash
   # Connect to PostgreSQL
   kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev
   
   # Check connections
   SELECT datname, numbackends FROM pg_stat_database WHERE datname = 'thergenome_dev';
   SELECT pid, usename, application_name, state FROM pg_stat_activity LIMIT 20;
   SELECT * FROM pg_stat_activity WHERE state != 'idle';
   ```

2. **Identify Problems** (5 min)
   ```sql
   -- Find long-running queries
   SELECT pid, now() - pg_stat_activity.query_start as duration, query
   FROM pg_stat_activity
   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
   
   -- Find idle transactions
   SELECT pid, usename, application_name, state_change
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
   ORDER BY state_change;
   ```

3. **Remediation** (by severity)
   ```bash
   # For idle transactions
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'idle in transaction'
   AND state_change < now() - interval '10 minutes';
   
   # For stuck queries (only if necessary)
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE pid <> pg_backend_pid()
   AND state != 'idle'
   AND query_start < now() - interval '30 minutes';
   ```

4. **Restart API if Needed**
   ```bash
   kubectl rollout restart deployment/theragenome-api -n theragenome
   ```

5. **Root Cause**
   - [ ] Review application connection pool settings
   - [ ] Check for database operation timeouts
   - [ ] Review spike in traffic
   - [ ] Check for slow queries introduced in recent deployment

---

### Playbook 3: Security Incident - Unauthorized Access Detected

**Trigger:** Unusual access patterns OR failed login spike

**Response Steps:**

1. **Immediate Actions** (preserve evidence)
   ```bash
   # DO NOT clear logs or audit tables
   
   # Create isolated environment for investigation
   kubectl create namespace incident-forensics
   
   # Dump audit logs
   kubectl exec -it postgresql-0 -n theragenome -- \
     pg_dump -Fc -t audit.* thergenome_dev > audit_backup.dump
   
   # Export access logs
   kubectl get logs -n theragenome > api_access_logs.txt
   ```

2. **Assess Scope** (10 min)
   ```bash
   # Check what was accessed
   kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'
   SELECT DISTINCT user_name, table_name, COUNT(*) 
   FROM audit.access_log
   WHERE access_time > NOW() - INTERVAL '1 hour'
   AND status = 'SUCCESS'
   GROUP BY user_name, table_name
   ORDER BY COUNT(*) DESC;
   SQL
   ```

3. **Containment**
   - [ ] Reset compromised credentials
   - [ ] Revoke unauthorized access
   - [ ] Isolate affected systems
   - [ ] Enable enhanced monitoring

4. **Recovery**
   - [ ] Restore from backup (if data corruption)
   - [ ] Apply security patches
   - [ ] Rotate encryption keys
   - [ ] Redeploy affected services

5. **Legal/Compliance**
   - [ ] Preserve all evidence
   - [ ] Notify HIPAA compliance officer
   - [ ] Document timeline
   - [ ] Prepare breach notification

---

### Playbook 4: Database Backup Failure

**Trigger:** Backup job fails or backup recovery test fails

**Response Steps:**

1. **Assessment** (5 min)
   ```bash
   # Check backup job status
   kubectl get cronjob postgres-encrypted-backup -n theragenome -o wide
   kubectl get jobs -n theragenome | grep backup
   kubectl logs job/postgres-encrypted-backup-xyz -n theragenome
   ```

2. **Diagnosis** (10 min)
   ```bash
   # Check database health
   kubectl exec -it postgresql-0 -n theragenome -- \
     pg_dump -d thergenome_dev > /tmp/test_dump.sql
   
   # Check storage
   kubectl exec -it postgresql-0 -n theragenome -- df -h
   ```

3. **Remediation**
   ```bash
   # Re-run backup job manually
   kubectl create job --from=cronjob/postgres-encrypted-backup \
     manual-backup-run -n theragenome
   
   # Monitor
   kubectl logs -f job/manual-backup-run -n theragenome
   ```

4. **Verification**
   ```bash
   # Test backup recovery
   kubectl create job --from=cronjob/postgres-backup-test \
     backup-test-$(date +%s) -n theragenome
   ```

---

## Part 3: Communication Templates

### Initial Alert Template

```md
**INCIDENT #[ID] - [SERVICE NAME] - [SEVERITY]**

**Status:** Investigating

**Affected Services:** [LIST]
**Start Time:** [UTC TIMESTAMP]
**Last Updated:** [UTC TIMESTAMP]

**Symptoms:**
- [SYMPTOM 1]
- [SYMPTOM 2]

**Current Action:**
We are investigating the issue. More updates in 15 minutes.

**Workaround:** [IF AVAILABLE]
```

### Resolution Template

```md
**INCIDENT #[ID] - RESOLVED**

**Status:** Resolved at [TIME] UTC

**Root Cause:** [DESCRIPTION]

**Impact:**
- Duration: [X] minutes
- Users affected: [COUNT]
- Data affected: [NONE/DESCRIPTION]

**Fix Applied:** [DESCRIPTION]

**Next Steps:** Post-incident review scheduled for [DATE/TIME]
```

---

## Part 4: Testing & Drills

### Monthly Drill Schedule

```yaml
Week 1:
  - Monday: API outage simulation
  - Wednesday: Database failure scenario
  
Week 2:
  - Monday: Security incident drill
  - Thursday: Backup recovery test

Week 3:
  - Tuesday: Cascading failure scenario
  - Friday: Communication procedures test

Week 4:
  - Monday: Full disaster recovery test
```

### Drill Execution Checklist

```bash
cat > /tmp/incident-drill.sh << 'EOF'
#!/bin/bash
# Incident Response Drill Script

INCIDENT_ID="DRILL-$(date +%Y%m%d-%H%M%S)"
SCENARIO="$1"

echo "=== Incident Response Drill: $SCENARIO ==="
echo "Incident ID: $INCIDENT_ID"
echo "Start Time: $(date)"
echo ""

case "$SCENARIO" in
  api-outage)
    echo "[ ] 1. Declare incident (S3 - moderate impact)"
    echo "[ ] 2. Page on-call engineer"
    echo "[ ] 3. Check metrics in Prometheus"
    echo "[ ] 4. Check logs in Grafana/Loki"
    echo "[ ] 5. Scale API deployment"
    echo "[ ] 6. Post status update"
    echo "[ ] 7. Resolve incident"
    echo "[ ] 8. Send all-clear notification"
    echo "[ ] 9. Schedule post-incident review"
    ;;
  
  database-failure)
    echo "[ ] 1. Declare incident (S2 - major impact)"
    echo "[ ] 2. Page DBA and IC"
    echo "[ ] 3. Check PostgreSQL health"
    echo "[ ] 4. Verify backup status"
    echo "[ ] 5. Begin failover to standby"
    echo "[ ] 6. Restore from backup if needed"
    echo "[ ] 7. Verify data integrity"
    echo "[ ] 8. Resume normal operations"
    ;;
  
  security-incident)
    echo "[ ] 1. Declare security incident (S1 - critical)"
    echo "[ ] 2. Page security team and IC"
    echo "[ ] 3. Preserve audit logs"
    echo "[ ] 4. Isolate affected systems"
    echo "[ ] 5. Reset compromised credentials"
    echo "[ ] 6. Notify compliance officer"
    echo "[ ] 7. Begin forensics"
    echo "[ ] 8. Implement fixes"
    ;;
esac

echo ""
echo "End Time: $(date)"
echo ""
EOF

chmod +x /tmp/incident-drill.sh

# Run drill
/tmp/incident-drill.sh api-outage
```

### Drill Report Template

```md
# Incident Response Drill Report

**Date:** [DATE]
**Scenario:** [SCENARIO NAME]
**Facilitator:** [NAME]
**Participants:** [LIST]

## Objectives
- [ ] Objective 1
- [ ] Objective 2

## Execution Summary
[What happened during the drill]

## Results
- **Response Time:** [X] minutes
- **Time to Resolution:** [X] minutes
- **Communication Delays:** [X] minutes
- **Procedure Gaps Identified:** [LIST]

## Improvements Needed
1. [IMPROVEMENT 1]
2. [IMPROVEMENT 2]

## Follow-up Actions
- [ ] Action 1 (Owner: [NAME], Due: [DATE])
- [ ] Action 2 (Owner: [NAME], Due: [DATE])

## Sign-off
Facilitator: _______________
Incident Commander: _______________
```

---

## Part 5: Post-Incident Review Process

### Timeline Creation

```bash
# Document incident timeline
kubectl get events -n theragenome --sort-by='.lastTimestamp' | tail -100
```

### Root Cause Analysis (RCA)

```markdown
# Root Cause Analysis Format

## What Happened?
[Clear description of incident]

## Timeline
- 14:23 UTC: Alert fired
- 14:25 UTC: Engineer acknowledged
- 14:30 UTC: Causes identified
- 14:35 UTC: Fix deployed
- 14:40 UTC: Issues resolved

## Root Cause
[Single root cause or layer of causes]

## Contributing Factors
1. [Factor 1]
2. [Factor 2]

## Preventive Measures
- [ ] [Measure 1]
- [ ] [Measure 2]
```

---

## Part 6: Testing Details

### Test 1: Failed API Instance

```bash
#!/bin/bash
# Simulates API pod failure

# Kill a running pod
kubectl delete pod -n theragenome \
  $(kubectl get pods -n theragenome -l app=theragenome-api -o jsonpath='{.items[0].metadata.name}')

# Verify:
# - Pod restarts automatically
# - Service automatically re-routes
# - Metrics track the incident
# - Alerts fire appropriately
```

### Test 2: Database Failover

```bash
#!/bin/bash
# Tests database recovery

# Simulate database failure
kubectl exec -it postgresql-0 -n theragenome -- sudo systemctl stop postgresql

# Verify:
# - Application detects connection loss
# - Alerts fire (HIGH or CRITICAL)
# - Failover triggers automatically (if configured)
# - Backup restore procedure works
# - Data integrity verified

# Restore normal operation
kubectl exec -it postgresql-0 -n theragenome -- sudo systemctl start postgresql
```

### Test 3: Full Backup Recovery

```bash
#!/bin/bash
# Tests complete backup recovery

# Create test database
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -c "CREATE DATABASE test_restore;"

# Restore from backup
kubectl exec -it postgresql-0 -n theragenome -- \
  pg_restore -d test_restore /backups/latest.dump

# Verify data
Count=$(kubectl exec -it postgresql-0 -n theragenome -- \
  psql -t -d test_restore -c "SELECT COUNT(*) FROM information_schema.tables")

if [ $Count -gt 0 ]; then
  echo "✅ Backup restore successful"
else
  echo "❌ Backup restore failed"
fi
```

---

## Compliance Checklist

- [ ] Incident response plan documented
- [ ] Roles and responsibilities defined
- [ ] Response procedures (playbooks) created
- [ ] Communication templates prepared
- [ ] Team trained on procedures
- [ ] Quarterly drills scheduled and tested
- [ ] Metrics and logs preserved for compliance
- [ ] Post-incident reviews conducted
- [ ] Improvements tracked and implemented
- [ ] External notification procedures ready

---

## Success Criteria

| Metric | Target | Current |
|--------|--------|---------|
| Mean Time to Detect (MTTD) | < 5 min | [TBD] |
| Mean Time to Respond (MTTR) | < 15 min | [TBD] |
| Mean Time to Resolution (MTTR) | < 30 min | [TBD] |
| Update frequency during incident | Every 15 min | [TBD] |
| First drill completion | Month 1 | [TBD] |
| All staff trained | Month 1 | [TBD] |

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
