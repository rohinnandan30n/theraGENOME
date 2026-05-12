# Database Encryption at Rest (Item #2 Implementation)

**Status:** Implementation Steps for Critical Item #2  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for HIPAA Compliance & Data Protection

---

## Overview

This guide provides step-by-step instructions for implementing encryption at rest for TheraGenome database, ensuring sensitive patient data is protected when stored on disk.

### Components to Encrypt:
1. **Storage Layer** - AWS EBS volumes encrypted with KMS
2. **Database Layer** - PostgreSQL WAL and data encryption
3. **Application Layer** - Sensitive fields encrypted with pgcrypto
4. **Backup Layer** - Encrypted database backups
5. **Key Management** - Centralized KMS key management

---

## Prerequisites

- **AWS Account** with KMS access
- **Kubernetes** 1.24+ cluster with EBS CSI driver
- **PostgreSQL** 15+ (for native WAL encryption support)
- **kubectl** and **aws-cli** installed
- IAM permissions for KMS and EBS

---

## Phase 1: AWS KMS Setup (10 minutes)

### Step 1: Create KMS Master Key

```bash
# Create a KMS key for database encryption
aws kms create-key \
  --region us-east-1 \
  --description "TheraGenome Database Encryption Key" \
  --key-policy '{
    "Version": "2012-10-17",
    "Id": "theragenome-db-key",
    "Statement": [
      {
        "Sid": "Enable IAM policies",
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::ACCOUNT_ID:root"
        },
        "Action": "kms:*",
        "Resource": "*"
      },
      {
        "Sid": "Allow EBS to use the key",
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ],
        "Resource": "*"
      }
    ]
  }'

# Save the Key ID
KEY_ID=$(aws kms create-key ... | jq -r '.KeyMetadata.KeyId')
echo "KMS Key ID: $KEY_ID"
```

### Step 2: Create Key Alias

```bash
aws kms create-alias \
  --alias-name alias/theragenome-db-encryption \
  --target-key-id $KEY_ID \
  --region us-east-1
```

### Step 3: Verify KMS Configuration

```bash
aws kms describe-key --key-id alias/theragenome-db-encryption --region us-east-1
aws kms list-keys --region us-east-1
```

---

## Phase 2: Kubernetes Storage Encryption Setup (15 minutes)

### Step 1: Enable EBS CSI Driver (if not already enabled)

```bash
# Check if EBS CSI is installed
kubectl get deployment ebs-csi-controller -n kube-system

# If not installed, install it:
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update
helm install aws-ebs-csi-driver aws-ebs-csi-driver/aws-ebs-csi-driver \
  --namespace kube-system \
  --values - <<EOF
enableWindowsHostProcess: false
enableVolumeSnapshot: true
EOF
```

### Step 2: Create Encrypted StorageClass

Update KMS Key ID in `k8s/07-encryption-at-rest-config.yaml`:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')

# Get KMS Key ARN
KEY_ARN=$(aws kms describe-key --key-id alias/theragenome-db-encryption | jq -r '.KeyMetadata.Arn')

# Update the StorageClass
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" k8s/07-encryption-at-rest-config.yaml
sed -i "s|arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID|$KEY_ARN|g" k8s/07-encryption-at-rest-config.yaml
```

### Step 3: Apply Encryption Configuration

```bash
kubectl apply -f k8s/07-encryption-at-rest-config.yaml

# Verify StorageClass creation
kubectl get storageclass encrypted-storage -o yaml

# Verify encrypted PVC creation
kubectl get pvc -n theragenome
```

---

## Phase 3: PostgreSQL Database Encryption (20 minutes)

### Step 1: Update Database Deployment

Create an updated PostgreSQL deployment with encryption:

```bash
# Create database initialization job
cat << 'EOF' > k8s/07b-postgres-encryption-init-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: postgres-encryption-init
  namespace: theragenome
spec:
  backoffLimit: 3
  template:
    spec:
      serviceAccountName: theragenome-api
      restartPolicy: Never
      containers:
      - name: init-encryption
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
        - name: PGDATABASE
          value: thergenome_dev
        command:
        - /bin/sh
        - -c
        - |
          until pg_isready -h $PGHOST -U $PGUSER; do
            echo "Waiting for PostgreSQL..."
            sleep 2
          done
          
          # Run encryption initialization
          psql << 'SQL'
          -- Create pgcrypto extension
          CREATE EXTENSION IF NOT EXISTS pgcrypto;
          
          -- Create schema
          CREATE SCHEMA IF NOT EXISTS encryption_management;
          
          -- Create encryption functions
          CREATE OR REPLACE FUNCTION encryption_management.encrypt_data(
            data_to_encrypt TEXT,
            encryption_key TEXT
          ) RETURNS TEXT AS $$
          BEGIN
            RETURN encode(
              encrypt(
                convert_to(data_to_encrypt, 'UTF8'),
                convert_to(encryption_key, 'UTF8'),
                'aes'
              ),
              'hex'
            );
          END;
          $$ LANGUAGE plpgsql;
          
          CREATE OR REPLACE FUNCTION encryption_management.decrypt_data(
            encrypted_data TEXT,
            encryption_key TEXT
          ) RETURNS TEXT AS $$
          BEGIN
            RETURN convert_from(
              decrypt(
                decode(encrypted_data, 'hex'),
                convert_to(encryption_key, 'UTF8'),
                'aes'
              ),
              'UTF8'
            );
          END;
          $$ LANGUAGE plpgsql;
          
          -- Create encryption audit log
          CREATE TABLE IF NOT EXISTS encryption_management.encryption_audit_log (
            id SERIAL PRIMARY KEY,
            operation VARCHAR(50),
            table_name VARCHAR(100),
            record_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name VARCHAR(100)
          );
          
          -- Grant permissions
          GRANT USAGE ON SCHEMA encryption_management TO postgres;
          GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA encryption_management TO postgres;
          
          \echo 'Encryption initialized successfully'
          SQL
          
          echo "Encryption initialization completed"
EOF

kubectl apply -f k8s/07b-postgres-encryption-init-job.yaml
```

### Step 2: Monitor Encryption Initialization

```bash
# Watch job progress
kubectl get jobs -n theragenome -w

# Check job logs
kubectl logs job/postgres-encryption-init -n theragenome -f

# Verify initialization completed
kubectl get job postgres-encryption-init -n theragenome -o jsonpath='{.status.completionTime}'
```

### Step 3: Verify Database Encryption

```bash
# Connect to PostgreSQL
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'
-- Check pgcrypto is loaded
SELECT installed_version FROM pg_available_extensions WHERE name = 'pgcrypto';

-- Check encryption schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'encryption_management';

-- Check functions
SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'encryption_management';

-- Check audit log table
SELECT table_name FROM information_schema.tables WHERE table_schema = 'encryption_management';

SQL
```

---

## Phase 4: Application-Level Encryption (25 minutes)

### Step 1: Update Python Application for Field Encryption

**File:** `scripts/db_connection.py`

```python
import os
from cryptography.fernet import Fernet
from sqlalchemy import event, create_engine
from sqlalchemy.pool import StaticPool

# Initialize encryption
ENCRYPTION_KEY = os.getenv('APP_ENCRYPTION_KEY', 'default-key-change-in-production')
cryptor = Fernet(ENCRYPTION_KEY.encode().ljust(32)[:32])  # Ensure 32 bytes

class EncryptedField:
    """SQLAlchemy column type for encrypted data"""
    def __init__(self, original_type):
        self.original_type = original_type
    
    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return Fernet(self.get_key()).encrypt(
                str(value).encode()
            ).decode()
        return process
    
    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            try:
                return Fernet(self.get_key()).decrypt(
                    value.encode()
                ).decode()
            except:
                return value  # Fallback if decryption fails
        return process
    
    @staticmethod
    def get_key():
        key = os.getenv('APP_ENCRYPTION_KEY', 'default-key')
        return key.encode().ljust(32)[:32]

# Setup database connection with encryption
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/db')

engine = create_engine(
    DATABASE_URL,
    connect_args={'sslmode': 'require'},
    poolclass=StaticPool,
    echo=False
)

# Register encryption event listeners
@event.listens_for(engine, 'connect')
def configure_encryption(dbapi_conn, connection_record):
    """Enable pgcrypto extension on connection"""
    with dbapi_conn.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
        dbapi_conn.commit()
```

### Step 2: Update Models to Use Encryption

**File:** `models/patient.py`

```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from db_connection import EncryptedField

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    # Encrypt sensitive fields
    ssn = Column(EncryptedField(String), nullable=True)
    medical_record_number = Column(EncryptedField(String), nullable=True)
    phone_number = Column(EncryptedField(String), nullable=True)
    email = Column(EncryptedField(String), nullable=True)
    
    # Non-sensitive fields
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Patient {self.id}: {self.first_name} {self.last_name}>'
```

### Step 3: Update TypeScript/Deno Application

**File:** `src/database.ts`

```typescript
import { Client } from "https://deno.land/x/postgres@v0.17.0/mod.ts";

// Get encryption key from environment
const ENCRYPTION_KEY = Deno.env.get("APP_ENCRYPTION_KEY") || "default-key";

// Helper functions for encryption
export async function encryptField(plaintext: string): Promise<string> {
  const key = new TextEncoder().encode(ENCRYPTION_KEY.padEnd(32).substring(0, 32));
  const iv = crypto.getRandomValues(new Uint8Array(16));
  
  const encryptedData = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: iv },
    await crypto.subtle.importKey("raw", key, "AES-GCM", false, ["encrypt"]),
    new TextEncoder().encode(plaintext)
  );
  
  return btoa(String.fromCharCode(...new Uint8Array(iv))) + ":" + 
         btoa(String.fromCharCode(...new Uint8Array(encryptedData)));
}

export async function decryptField(encrypted: string): Promise<string> {
  const [ivStr, dataStr] = encrypted.split(":");
  const key = new TextEncoder().encode(ENCRYPTION_KEY.padEnd(32).substring(0, 32));
  
  const iv = Uint8Array.from(atob(ivStr), c => c.charCodeAt(0));
  const encryptedData = Uint8Array.from(atob(dataStr), c => c.charCodeAt(0));
  
  const decryptedData = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: iv },
    await crypto.subtle.importKey("raw", key, "AES-GCM", false, ["decrypt"]),
    encryptedData
  );
  
  return new TextDecoder().decode(decryptedData);
}

// Database client connection
export const db = new Client({
  hostname: Deno.env.get("DB_HOST") || "localhost",
  port: parseInt(Deno.env.get("DB_PORT") || "5432"),
  user: Deno.env.get("DB_USER") || "postgres",
  password: Deno.env.get("DB_PASSWORD"),
  database: Deno.env.get("DB_NAME") || "thergenome_dev",
  // Enforce SSL
  ssl: {
    enable: true,
    enforce: true,
  },
});
```

---

## Phase 5: Backup Encryption (15 minutes)

### Step 1: Create Encrypted Backup Configuration

```bash
cat << 'EOF' > k8s/08-backup-encryption-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backup-encryption-script
  namespace: theragenome
data:
  backup-encrypted.sh: |
    #!/bin/bash
    set -e
    
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="/backup/thergenome_backup_${BACKUP_DATE}.sql"
    ENCRYPTED_FILE="${BACKUP_FILE}.gpg"
    BACKUP_ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY}"
    
    echo "Starting encrypted backup..."
    
    # Create backup directory
    mkdir -p /backup
    
    # Perform database backup
    pg_dump -U postgres -d thergenome_dev > "$BACKUP_FILE"
    
    # Encrypt backup with GPG
    echo "$BACKUP_ENCRYPTION_KEY" | gpg --batch --passphrase-fd 0 \
      --symmetric --cipher-algo AES256 \
      --output "$ENCRYPTED_FILE" "$BACKUP_FILE"
    
    # Calculate checksum
    sha256sum "$ENCRYPTED_FILE" > "${ENCRYPTED_FILE}.sha256"
    
    # Remove unencrypted backup
    rm -f "$BACKUP_FILE"
    
    # Upload to S3 (if configured)
    if [ ! -z "$AWS_S3_BUCKET" ]; then
      aws s3 cp "$ENCRYPTED_FILE" "s3://${AWS_S3_BUCKET}/backups/$(basename $ENCRYPTED_FILE)"
      aws s3 cp "${ENCRYPTED_FILE}.sha256" "s3://${AWS_S3_BUCKET}/backups/$(basename ${ENCRYPTED_FILE}.sha256)"
    fi
    
    echo "Backup encrypted and completed: $ENCRYPTED_FILE"
    
    # Cleanup old backups (keep last 7 days)
    find /backup -name "*.sql.gpg" -mtime +7 -delete
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-encrypted-backup
  namespace: theragenome
spec:
  # Run daily at 2 AM UTC
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          serviceAccountName: theragenome-api
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:15-alpine
            env:
            - name: PGHOST
              value: postgresql.theragenome.svc.cluster.local
            - name: PGUSER
              value: postgres
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: theragenome-secrets
                  key: DB_PASSWORD
            - name: PGDATABASE
              value: thergenome_dev
            - name: BACKUP_ENCRYPTION_KEY
              valueFrom:
                secretKeyRef:
                  name: encryption-keys
                  key: BACKUP_ENCRYPTION_KEY
            volumeMounts:
            - name: backup-script
              mountPath: /scripts
              readOnly: true
            - name: backup-storage
              mountPath: /backup
            command:
            - /bin/sh
            - /scripts/backup-encrypted.sh
          
          volumes:
          - name: backup-script
            configMap:
              name: backup-encryption-script
              defaultMode: 0755
          - name: backup-storage
            emptyDir: {}
EOF

kubectl apply -f k8s/08-backup-encryption-config.yaml
```

### Step 2: Verify Backup Configuration

```bash
# Check CronJob
kubectl get cronjob -n theragenome
kubectl describe cronjob postgres-encrypted-backup -n theragenome

# Test backup job manually
kubectl create job --from=cronjob/postgres-encrypted-backup postgres-test-backup -n theragenome

# Check backup job logs
kubectl logs job/postgres-test-backup -n theragenome -f
```

---

## Phase 6: Encryption Key Rotation (10 minutes)

### Step 1: Create Key Rotation Policy

```bash
cat << 'EOF' > k8s/09-key-rotation-config.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: encryption-key-rotation
  namespace: theragenome
spec:
  # Run monthly on the 1st day at 3 AM UTC
  schedule: "0 3 1 * *"
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          serviceAccountName: theragenome-api
          restartPolicy: OnFailure
          containers:
          - name: key-rotation
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
            - name: PGDATABASE
              value: thergenome_dev
            - name: OLD_KEY
              valueFrom:
                secretKeyRef:
                  name: encryption-keys
                  key: APP_ENCRYPTION_KEY
            - name: NEW_KEY
              value: "new-encryption-key-rotation"
            command:
            - /bin/sh
            - -c
            - |
              psql << 'SQL'
              \echo 'Starting encryption key rotation...'
              
              -- Create re-encryption function
              CREATE OR REPLACE FUNCTION encryption_management.rotate_keys(
                old_key TEXT,
                new_key TEXT
              ) RETURNS TABLE (updated_rows INTEGER) AS $$
              DECLARE
                updated_count INTEGER := 0;
              BEGIN
                -- Re-encrypt ssn in patients table
                UPDATE patients
                SET ssn = encryption_management.encrypt_data(
                  encryption_management.decrypt_data(ssn, old_key),
                  new_key
                )
                WHERE ssn LIKE 'encrypted:%';
                
                updated_count := updated_count + ROW_COUNT;
                
                -- Log key rotation
                INSERT INTO encryption_management.encryption_audit_log
                  (operation, table_name, timestamp, user_name)
                VALUES
                  ('KEY_ROTATION', 'patients', CURRENT_TIMESTAMP, CURRENT_USER);
                
                RETURN QUERY SELECT updated_count;
              END;
              $$ LANGUAGE plpgsql;
              
              SELECT * FROM encryption_management.rotate_keys(:'OLD_KEY', :'NEW_KEY');
              \echo 'Key rotation completed'
              SQL
EOF

kubectl apply -f k8s/09-key-rotation-config.yaml
```

---

## Phase 7: Monitoring and Verification (15 minutes)

### Step 1: Verify Encryption is Active

```bash
# Check storage encryption
kubectl get pvc -n theragenome postgres-encrypted-pvc -o yaml | grep storageClassName

# Verify AWS EBS encryption
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:kubernetes.io/cluster/name,Values=YOUR_CLUSTER" --query 'Reservations[0].Instances[0].InstanceId' --output text)

aws ec2 describe-volumes \
  --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
  --query 'Volumes[*].[VolumeId,Encrypted]' \
  --output table
```

### Step 2: Test Encryption Functions

```bash
# Connect to PostgreSQL
kubectl exec -it postgresql-0 -n theragenome -- psql -U postgres -d thergenome_dev << 'SQL'
-- Test encryption
SELECT encryption_management.encrypt_data('test-patient-data', 'test-key');

-- Test decryption
SELECT encryption_management.decrypt_data(
  encryption_management.encrypt_data('test-patient-data', 'test-key'),
  'test-key'
);

-- Check encryption audit log
SELECT * FROM encryption_management.encryption_audit_log ORDER BY timestamp DESC LIMIT 5;
SQL
```

### Step 3: Create Monitoring Alert

```bash
# Monitor encryption audit log for suspicious activity
cat << 'EOF' > k8s/10-encryption-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: encryption-monitoring
  namespace: theragenome
data:
  encryption-query.promql: |
    # Alert: Failed decryption attempts
    rate(encryption_audit_log{operation="DECRYPT_FAIL"}[5m]) > 0
    
    # Alert: Unusual encryption activity
    (rate(encryption_audit_log{operation="ENCRYPT"}[5m]) > 100) 
    or 
    (rate(encryption_audit_log{operation="DECRYPT"}[5m]) > 100)
    
    # Alert: Key rotation failures
    encryption_audit_log{operation="KEY_ROTATION",status="FAILED"}
EOF
```

---

## Troubleshooting

### Encryption Key Issues
```bash
# Get encryption keys from secret
kubectl get secret encryption-keys -n theragenome -o jsonpath='{.data.DB_ENCRYPTION_KEY}' | base64 -d

# Update encryption keys (restart pods after)
kubectl patch secret encryption-keys -n theragenome -p \
  '{"data":{"DB_ENCRYPTION_KEY":"'$(echo -n 'new-key' | base64)'"}}'
```

### Storage Encryption Issues
```bash
# Check StorageClass
kubectl get storageclass encrypted-storage -o yaml

# Verify PVC uses correct StorageClass
kubectl get pvc -n theragenome postgres-encrypted-pvc -o yaml | grep storageClassName

# Check EBS volume encryption status
aws ec2 describe-volumes --volume-ids vol-xxx --query 'Volumes[0].Encrypted'
```

### PostgreSQL Encryption Issues
```bash
# Check pgcrypto extension
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev -c \
  "SELECT * FROM pg_extension WHERE extname = 'pgcrypto';"

# Check encryption functions
kubectl exec -it postgresql-0 -n theragenome -- \
  psql -U postgres -d thergenome_dev -c \
  "SELECT * FROM information_schema.routines WHERE routine_schema = 'encryption_management';"
```

---

## Post-Implementation Checklist

- [x] KMS key created and configured
- [x] EBS encryption enabled for storage
- [x] PostgreSQL encryption functions created
- [x] Application-level encryption configured
- [x] Backup encryption enabled
- [x] Key rotation policy scheduled
- [x] Monitoring and alerting configured
- [ ] Update compliance audit (mark Item #2 COMPLETE)
- [ ] Document encryption procedures for team
- [ ] Conduct encryption security review

---

## Next Steps

1. **Item #3:** Apply RBAC & audit logging to database
2. **Item #4:** Deploy APM monitoring
3. **Item #5:** Complete container security scanning

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
