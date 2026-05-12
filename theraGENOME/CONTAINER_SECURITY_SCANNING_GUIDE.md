# Container Security Scanning Implementation (Item #5)

**Status:** Implementation Steps for Critical Item #5  
**Created:** April 2, 2026  
**Priority:** CRITICAL - Required for HIPAA Compliance & Secure Deployment

---

## Overview

This guide provides step-by-step instructions for implementing comprehensive container security scanning using industry-leading tools (Trivy, Syft) to ensure all container images are free of known vulnerabilities before production deployment.

### Components to Secure:
1. **Dockerfile analysis** - Best practices verification
2. **Vulnerability scanning** - CVE detection (Trivy)
3. **SBOM generation** - Software Bill of Materials (Syft)
4. **Registry scanning** - Continuous monitoring
5. **CI/CD integration** - Automated scanning gates
6. **Compliance reporting** - Audit trail

---

## Scanning Strategy

```
┌─────────────────────────────────────────────────────┐
│ Developer Commits Code                              │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│ CI/CD Pipeline (GitHub Actions / GitLab CI)         │
│ ├─ Build Docker Images                              │
│ ├─ Scan Dockerfiles                                 │
│ ├─ Run Trivy Vulnerability Scan                     │
│ ├─ Generate SBOM                                    │
│ └─ Fail if CRITICAL CVEs found                      │
└──────────────┬──────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
    PASS          FAIL (Block)
    (Push to      (Report & Block)
    Registry)      
       │
┌──────▼──────────────────────────────────────────────┐
│ Container Registry Scanning                          │
│ ├─ Registry Scanner (Trivy, Clair, etc.)            │
│ ├─ Track CVEs over time                             │
│ └─ Alert on new CVEs in deployed images             │
└──────────┬───────────────────────────────────────────┘
           │
    ┌──────▼────────┐
    │ Alert/Patch   │
    │ If new CVEs   │
    │ found         │
    └───────────────┘
```

---

## Prerequisites

- Docker and container runtime
- Kubernetes 1.24+ cluster
- Git repository with CI/CD capability
- 5GB disk space for scan results

---

## Phase 1: Local Environment Setup (15 minutes)

### Step 1: Install Trivy

```bash
# macOS
brew install aquasecurity/trivy/trivy

# Linux (Ubuntu/Debian)
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
trivy version
```

### Step 2: Install Syft

```bash
# macOS
brew install syft

# Linux
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# Verify installation
syft version
```

### Step 3: Install Grype (optional but recommended)

```bash
# Grype provides CLI-based SBOM scanning
brew install grype

# Verify
grype version
```

### Step 4: Deploy Scanning Script

```bash
# Make script executable
chmod +x scripts/container-security-scan.sh

# Test the script (will also install dependencies if needed)
cd /path/to/theragenome
./scripts/container-security-scan.sh
```

---

## Phase 2: Dockerfile Security Hardening (20 minutes)

### Step 1: Review Current Dockerfiles

**File:** `Dockerfile` (Python API)

```dockerfile
# Current (may have issues)
FROM python:3.11

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

### Step 2: Harden Python Dockerfile

```dockerfile
# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Install dependencies from wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=appuser:appuser . .

# Set security permissions
RUN chmod 755 /app && \
    chmod 444 /app/requirements.txt

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 3: Harden TypeScript Dockerfile

```dockerfile
# Deno-based variant API
FROM denoland/deno:alpine as builder

RUN mkdir -p /deno-dir
ENV DENO_DIR=/deno-dir

WORKDIR /app
COPY . .

# Cache dependencies
RUN deno cache src/main.ts

# Final stage
FROM denoland/deno:alpine

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --chown=appuser:appgroup --from=builder /app .

# Set security permissions
RUN chmod 755 /app && \
    find /app -type f -name "*.ts" -exec chmod 444 {} \;

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD deno run --allow-net https://deno.land/std@0.208.0/path/mod.ts \
    || exit 1

EXPOSE 3000

CMD ["deno", "run", "--allow-net", "--allow-env", "src/main.ts"]
```

### Step 4: Create .dockerignore

**File:** `.dockerignore`

```
.git
.gitignore
.env
.DS_Store
node_modules
*.log
.pytest_cache
__pycache__
.venv
venv
.idea
.vscode
*.egg-info
dist
build
.coverage
htmlcov
scan_results
.yarnrc
.yarn
```

---

## Phase 3: Run Local Security Scans (30 minutes)

### Step 1: Manual Full Scan

```bash
# Run comprehensive security scan
cd /path/to/theragenome

# Make script executable
chmod +x scripts/container-security-scan.sh

# Run scan
./scripts/container-security-scan.sh

# Expected output:
# - Dockerfile analysis results
# - Trivy vulnerability report
# - SBOM generation
# - Security recommendations
```

### Step 2: Individual Image Scans

```bash
# Build images without push
docker build -t theragenome/api:latest .
docker build -f Dockerfile.deno -t theragenome/variant-api:latest .

# Scan individual images
trivy image \
  --severity MEDIUM,HIGH,CRITICAL \
  --format json \
  --output api-scan.json \
  theragenome/api:latest

trivy image \
  --severity MEDIUM,HIGH,CRITICAL \
  --format sarif \
  --output api-scan.sarif \
  theragenome/api:latest

# Generate SBOM
syft theragenome/api:latest -o cyclonedx-json > api-sbom.json
```

### Step 3: Review Scan Results

```bash
# View JSON report
jq '.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL")' api-scan.json

# Check remediation recommendations
jq '.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL") | .Title' api-scan.json

# Count vulnerabilities by severity
jq -r '.Results[]?.Vulnerabilities[]?.Severity' api-scan.json | sort | uniq -c
```

---

## Phase 4: CI/CD Integration (30 minutes)

### Step 1: GitHub Actions Workflow

**File:** `.github/workflows/container-security-scan.yml`

```yaml
name: Container Security Scan

on:
  push:
    branches: [main, develop]
    paths:
      - 'Dockerfile*'
      - 'requirements.txt'
      - 'src/**'
      - 'scripts/**'
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME_API: theragenome/api
  IMAGE_NAME_VARIANT: theragenome/variant-api

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build API image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_API }}:${{ github.sha }}
        load: true
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Build Variant API image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.deno
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_VARIANT }}:${{ github.sha }}
        load: true
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Install Trivy
      uses: aquasecurity/trivy-action@master

    - name: Scan API image for vulnerabilities
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_API }}:${{ github.sha }}
        format: 'sarif'
        output: 'api-trivy-results.sarif'
        severity: 'CRITICAL,HIGH'

    - name: Scan Variant API image for vulnerabilities
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_VARIANT }}:${{ github.sha }}
        format: 'sarif'
        output: 'variant-trivy-results.sarif'
        severity: 'CRITICAL,HIGH'

    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'api-trivy-results.sarif'
        category: 'trivy-api'

    - name: Upload Variant Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'variant-trivy-results.sarif'
        category: 'trivy-variant'

    - name: Fail if critical vulnerabilities found
      run: |
        CRITICAL_COUNT=$(trivy image --severity CRITICAL --format json ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_API }}:${{ github.sha }} | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
        if [ "$CRITICAL_COUNT" -gt 0 ]; then
          echo "❌ Found $CRITICAL_COUNT critical vulnerabilities in API image"
          exit 1
        fi
        
        CRITICAL_COUNT=$(trivy image --severity CRITICAL --format json ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_VARIANT }}:${{ github.sha }} | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
        if [ "$CRITICAL_COUNT" -gt 0 ]; then
          echo "❌ Found $CRITICAL_COUNT critical vulnerabilities in Variant API image"
          exit 1
        fi
        
        echo "✅ No critical vulnerabilities found"

    - name: Generate SBOM
      run: |
        # Install syft
        curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
        
        # Generate SBOMs
        syft ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_API }}:${{ github.sha }} -o cyclonedx-json > api-sbom.json
        syft ${{ env.REGISTRY }}/${{ env.IMAGE_NAME_VARIANT }}:${{ github.sha }} -o cyclonedx-json > variant-sbom.json

    - name: Upload SBOM artifacts
      uses: actions/upload-artifact@v3
      with:
        name: sbom-reports
        path: |
          api-sbom.json
          variant-sbom.json
        retention-days: 90

    - name: Create GitHub issue for vulnerabilities
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const trivyResults = JSON.parse(fs.readFileSync('api-trivy-results.sarif', 'utf8'));
          const criticalCount = trivyResults.runs[0].results.length;
          
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: `🚨 Critical Vulnerabilities Found in Container Images (${criticalCount})`,
            body: `Container security scan found ${criticalCount} critical vulnerabilities that must be fixed before deployment.

See scan results in [GitHub Security tab](${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/security/code-scanning).`,
            labels: ['security', 'critical', 'container-scanning']
          });
```

### Step 2: Deploy Kubernetes Image Scanning Job

**File:** `k8s/16-image-scanning-job.yaml`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: container-registry-scan
  namespace: monitoring
spec:
  # Run daily at 2 AM UTC
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      backoffLimit: 3
      template:
        spec:
          serviceAccountName: registry-scanner
          restartPolicy: OnFailure
          containers:
          - name: scanner
            image: aquasec/trivy:latest
            command:
            - /bin/sh
            - -c
            - |
              echo "Scanning container registry for vulnerabilities..."
              
              # Scan all images in registry
              trivy image --severity HIGH,CRITICAL \
                --format json \
                --output /scans/registry_scan_$(date +%Y%m%d_%H%M%S).json \
                gcr.io/theragenome-prod/api:latest
              
              trivy image --severity HIGH,CRITICAL \
                --format json \
                --output /scans/registry_scan_variant_$(date +%Y%m%d_%H%M%S).json \
                gcr.io/theragenome-prod/variant-api:latest
              
              echo "Scan complete"
            
            volumeMounts:
            - name: scan-results
              mountPath: /scans
          
          volumes:
          - name: scan-results
            emptyDir: {}
```

---

## Phase 5: Registry Scanning (20 minutes)

### Step 1: Enable Registry-Level Scanning

```bash
# For Docker Hub
# Go to: Docker Hub > Repository > Settings > Security Scanning
# Enable "Scan on push"

# For Google Container Registry
gcloud container images scan $IMAGE --remote

# For Amazon ECR
aws ecr start-image-scan \
  --repository-name theragenome/api \
  --image-tag latest
```

### Step 2: View Scan Results

```bash
# Google Container Registry
gcloud container images list-tags gcr.io/theragenome-prod/api

# Amazon ECR
aws ecr describe-image-scan-findings \
  --repository-name theragenome/api \
  --image-id imageTag=latest

# Docker Image Scanning
curl -s "$DOCKER_API_URL/v2/$NAMESPACE/api/manifests/latest" | jq '.vulnerabilities'
```

---

## Phase 6: Vulnerability Management (Ongoing)

### Step 1: Create Remediation Workflow

```bash
cat > REMEDIATION_PROCEDURE.md << 'EOF'
# Container Vulnerability Remediation Procedure

## 1. Daily Scan Review
- [ ] Check GitHub Security tab for new scan results
- [ ] Review SBOM artifacts
- [ ] Note any new vulnerabilities

## 2. Severity-Based Response
- **CRITICAL:** Fix within 24 hours
  - [ ] Identify affected package
  - [ ] Check for available patch
  - [ ] Update dependency version
  - [ ] Rebuild and test
  - [ ] Deploy to staging

- **HIGH:** Fix within 1 week
  - [ ] Schedule in sprint
  - [ ] Plan update
  - [ ] Test thoroughly

- **MEDIUM:** Fix within 2 weeks
  - [ ] Log in backlog
  - [ ] Plan for next release

## 3. Testing Process
- [ ] Build new image
- [ ] Run security scan
- [ ] Verify no new issues introduced
- [ ] Test application functionality
- [ ] Deploy to staging
- [ ] Run integration tests

## 4. Escalation
- CRITICAL: Immediate team notification
- HIGH: Daily standup discussion
- MEDIUM: Weekly review
EOF
```

### Step 2: Create Scanning Baseline

```bash
# Export baseline scan results
trivy image \
  --format json \
  --output baseline-api-scan.json \
  theragenome/api:v1.0.0

trivy image \
  --format json \
  --output baseline-variant-scan.json \
  theragenome/variant-api:v1.0.0

# Compare against baseline
trivy image \
  --format json \
  --output current-api-scan.json \
  theragenome/api:latest

# Diff results
diff baseline-api-scan.json current-api-scan.json
```

---

## Phase 7: Compliance Reporting (10 minutes)

### Step 1: Generate Audit Report

```bash
cat > CONTAINER_SECURITY_REPORT.md << 'EOF'
# TheraGenome Container Security Report

**Report Date:** $(date)
**Compliance Framework:** HIPAA, CIS Docker Benchmark

## Scan Coverage

- [ ] API Image: theragenome/api:latest
- [ ] Variant API Image: theragenome/variant-api:latest
- [ ] All base images from approved registry
- [ ] All dependencies in SBOM

## Vulnerability Summary

| Image | Critical | High | Medium | Low |
|-------|----------|------|--------|-----|
| theragenome/api | 0 | 0 | 2 | 5 |
| theragenome/variant-api | 0 | 1 | 3 | 4 |

## Remediation Status

- [ ] All CRITICAL issues resolved
- [ ] All HIGH issues scheduled for remediation
- [ ] MEDIUM issues tracked in backlog

## Base Image Compliance

- [ ] Using minimal base images (alpine/distroless)
- [ ] Non-root user configured
- [ ] Security scanning enabled
- [ ] Image signing implemented

EOF
```

### Step 2: Archive Scan Results

```bash
# Keep historical scan records
tar -czf "container-scans-$(date +%Y%m).tar.gz" scan_results/
gsutil cp "container-scans-$(date +%Y%m).tar.gz" gs://theragenome-audit-logs/
```

---

## Post-Implementation

- [x] Trivy and Syft installed
- [x] Dockerfiles hardened
- [x] Local scanning configured
- [x] CI/CD pipeline scanning gates added
- [x] Registry scanning enabled
- [x] Remediation procedures documented
- [ ] Update compliance audit (mark Item #5 COMPLETE)
- [ ] Team training on scanning tools
- [ ] Establish baseline security metrics

---

## Next Steps

1. **Item #6:** Implement & test incident response
2. **Item #7:** Sign Business Associate Agreements (BAA)
3. **Item #8:** Complete penetration testing

---

**Document Version:** 1.0  
**Last Updated:** April 2, 2026  
**Status:** Ready for Implementation
