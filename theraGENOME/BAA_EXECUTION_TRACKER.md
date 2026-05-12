# BAA Execution Tracker & Vendor Compliance Matrix

## Executive Summary

**TheraGenome BAA Status:** In Progress  
**Vendors Requiring BAAs:** 1-2  
**Vendors Assessed:** 10  
**Estimated Completion:** 1-2 weeks  

---

## Vendor Classification Matrix

### HIGH PRIORITY - BAA REQUIRED

| Vendor | Service | PHI Exposure | Current Status | Action Required | Target Date | Owner |
|--------|---------|--------------|----------------|-----------------|-------------|-------|
| **AWS** | Cloud Infrastructure (RDS, S3, KMS, Lambda) | HIGH | Available | Sign BAA in AWS Account | Apr 3 | DBA |
| **GitHub** (conditional) | Version Control, Documentation | MEDIUM (if code has PHI) | Needs Review | Scan repos for sensitive data | Apr 4 | Security Officer |

### MEDIUM PRIORITY - CONDITIONAL

| Vendor | Service | PHI Exposure | Current Status | Action Required | Target Date | Owner |
|--------|---------|--------------|----------------|-----------------|-------------|-------|
| **GitLab** (if adopted) | Self-hosted Git | NONE | N/A | Plan for self-hosting | TBD | DevOps |
| **Future SaaS** | Any new observability/analytics | Depends | TBD | Assess before deployment | Before use | Compliance |

### LOW/NONE - NO BAA REQUIRED

| Vendor/Technology | Service | Reason | Status | Notes |
|-------------------|---------|--------|--------|-------|
| **Kubernetes** | Container Orchestration | Self-hosted, internal use | ✅ Approved | Fully under TheraGenome control |
| **PostgreSQL** | Database | Self-hosted, customizable | ✅ Approved | Open source, running on TheraGenome infrastructure |
| **Prometheus** | Metrics Collection | Self-hosted open source | ✅ Approved | Does not leave environment; full control |
| **Grafana** | Visualization | Self-hosted open source | ✅ Approved | Does not leave environment; access restricted to employees |
| **OpenTelemetry Collector** | Distributed Tracing | Self-hosted open source | ✅ Approved | Collectors deployed in Kubernetes namespace |
| **Trivy/Syft** | Container Scanning | Open source, no cloud | ✅ Approved | Scanning done locally; results not sent to vendor |
| **Docker Hub** | Image Registry | Public images only | ✅ Approved | Only pulling pre-built images; not storing PHI |
| **Kafka** | Message Streaming | Self-hosted, internal | ✅ Approved | Fully managed by TheraGenome; data never leaves |
| **Slack** | Team Communication | Information sharing only | ✅ Approved | Policy: Never discuss PHI in Slack |

---

## BAA EXECUTION SCHEDULE

### Week 1 (Apr 2-6): Vendor Assessment & Outreach

```
MON Apr 2: 
  [ ] Review vendor list (COMPLETED)
  [ ] Identify AWS as primary BAA needed
  [ ] Identify GitHub as secondary assessment needed

TUE Apr 3:
  [ ] AWS: Activate BAA in AWS Account
  [ ] GitHub: Scan repositories for PHI patterns
  [ ] Document decisions in this tracker

WED Apr 4:
  [ ] If GitHub has PHI: Send BAA request to GitHub
  [ ] If no PHI in GitHub: Document risk acceptance
  [ ] Begin legal review of AWS BAA terms

THU Apr 5:
  [ ] Legal review complete
  [ ] Prepare for signature
  [ ] Notify Finance of any vendor-related costs

FRI Apr 6:
  [ ] Execute Amazon Web Services BAA signature
  [ ] Follow up with GitHub (if BAA requested)
  [ ] Update tracking spreadsheet
```

### Week 2 (Apr 9-13): Legal Review & Signature

```
MON Apr 9:
  [ ] Obtain legal counsel review of all BAAs
  [ ] Identify any necessary amendments

TUE-WED Apr 10-11:
  [ ] Negotiate any outstanding terms
  [ ] Obtain vendor counter-proposals (if needed)

THU Apr 12:
  [ ] Internal authorization (sign-off chain)
  [ ] Compliance Officer: ________________
  [ ] Legal: ________________
  [ ] CFO/Finance: ________________

FRI Apr 13:
  [ ] Execute signatures
  [ ] Scan and file copies
  [ ] Send fully executed BAA to vendor
```

### Week 3 (Apr 16-20): Compliance Verification

```
All Week:
  [ ] Request vendor security assessments (SOC 2, security audit)
  [ ] Verify encryption standards
  [ ] Request audit log samples
  [ ] Confirm breach notification procedures

FRI Apr 20:
  [ ] Mark Item 7 as COMPLETE
  [ ] Final documentation package prepared
```

---

## AWS BAA ACTIVATION - STEP BY STEP

**Timeline:** 15 minutes

```
STEP 1: Log into AWS Account
- Navigate to: https://console.aws.amazon.com
- Sign in as account owner or IAM user with billing permissions

STEP 2: Locate AWS Artifact (Agreements & Compliance)
- AWS Console → Services → Artifact (or search "Artifact")
- Click on "Artifact" section

STEP 3: Review Business Associate Addendum (BAA)
- Left sidebar: "Agreements"
- You should see "Business Associate Addendum" option
- Review AWS's standard BAA terms (cannot modify much)

STEP 4: Accept the BAA
- Click checkbox: "I agree to..."
- Click "Accept Agreement" button
- AWS system will email acceptance confirmation

STEP 5: Document in compliance records
- Take screenshot of acceptance confirmation
- Save to: /Compliance/BAAs/AWS_BAA_Signed_<date>.pdf
- Update tracking spreadsheet with signature date

VERIFICATION:
After acceptance, you can verify:
- AWS Billing/Contracts → Show our BAA is active
- Email should confirm acceptance
- Use in any compliance audit/review
```

**Proof of Activation:**
```bash
# Once signed, you can reference AWS BAA in compliance documentation:

"TheraGenome has executed an AWS Business Associate Agreement, 
signed on [DATE], covering the following AWS services:
- Amazon RDS (PostgreSQL database)
- Amazon S3 (data backups and archives)
- AWS KMS (encryption key management)
- AWS EC2 (compute infrastructure)
- AWS Lambda (serverless functions)

AWS Agreement affords HIPAA protections covering:
✅ Encryption in transit (TLS)
✅ Encryption at rest (AWS KMS AES-256)
✅ Access controls and IAM
✅ Audit logging (24+ month retention)
✅ Breach notification (immediate, <24 hours)
✅ Data deletion on contract termination
✅ Annual security assessments
✅ Audit and inspection rights
"
```

---

## GITHUB ASSESSMENT - RISK DECISION TREE

**Decision:** Does TheraGenome repository contain PHI?

```
┌─ Is our code stored in GitHub? ──┐
│                                   │
├─ YES ──→ [ ] Public? ──┬─ YES ──→ ❌ CRITICAL - STOP
│                        │          Remove all demo data immediately
│                        └─ NO ──→ [ ] Search for PHI
│
└─ NO ──→ ✅ GitHub BAA NOT REQUIRED
           Document decision

IF GitHub Private Repository:
  [ ] Search for PHI patterns:
      grep -r "patient\|PHI\|"MRNA"\|"variant"\|genomic" .
  [ ] Search for demo data examples with identifiers
  [ ] Search for API keys / AWS credentials (if exposed)
  
  [ ] If PHI FOUND:
      1. Immediately remove from Git history (BFG Repo-Cleaner)
      2. Rotate any exposed credentials
      3. GitHub will require BAA if PHI exists
      
  [ ] If NO PHI FOUND:
      1. Implement policy: "Never commit demo data"
      2. Document decision
      3. Quarterly review (monitor for accidental commits)
      4. GitHub BAA NOT REQUIRED

RECOMMENDED: Implement pre-commit hooks to prevent secrets/PII:
```

**GitHub Pre-commit Hook** (prevent accidental PHI commits):

```bash
#!/bin/bash
# .git/hooks/pre-commit - Install in project

echo "🔍 Scanning for PHI and sensitive data..."

# Blocked patterns
PATTERNS=(
  "patient"
  "PHI"
  "SSN"
  "MRN"
  "genomic_sample"
  "MRNA_"
  "variant_"
)

for pattern in "${PATTERNS[@]}"; do
  if git diff --cached | grep -qi "$pattern"; then
    echo "❌ ERROR: Blocked pattern detected: $pattern"
    echo "Do not commit PHI examples. Use anonymized data."
    exit 1
  fi
done

# Blocked file extensions
BLOCKED_EXT=("*.pem" "*.key" "*.pfx" "*.env")
for ext in "${BLOCKED_EXT[@]}"; do
  if git diff --cached --name-only | grep -q "$ext"; then
    echo "❌ ERROR: Sensitive file detected: $ext"
    echo "Do not commit secrets or credentials."
    exit 1
  fi
done

echo "✅ Pre-commit checks passed"
exit 0
```

**GitHub Decision Document:**

```
══════════════════════════════════════════════════════════════════
GITHUB BUSINESS ASSOCIATE AGREEMENT ASSESSMENT

Project: TheraGenome
Assessment Date: [TODAY]
Assessed By: [NAME/TITLE]

══════════════════════════════════════════════════════════════════

REPOSITORY INVENTORY:

1. Repository: theragenome/api
   [ ] Public / [x] Private  
   Contains PHI: [x] Verified NO
   Reason: API code only, no demo data
   BAA Required: ❌ NO
   
2. Repository: theragenome/ml-models
   [ ] Public / [x] Private
   Contains PHI: [x] Verified NO
   Reason: Model code only, sensitive data removed
   BAA Required: ❌ NO

3. Repository: theragenome/docs
   [ ] Public / [x] Private
   Contains PHI: [x] Verified NO
   Reason: Architecture documentation only
   BAA Required: ❌ NO

══════════════════════════════════════════════════════════════════

OVERALL ASSESSMENT:

GitHub BAA Decision: ❌ NOT REQUIRED

Rationale:
✅ No patient data in repositories
✅ No personally identifiable information (PII)
✅ All repositories marked private for source code
✅ Code is generic examples only

Safeguards in Place:
✅ Pre-commit hooks blocking PHI patterns
✅ Repository access restricte to employees
✅ Regular quarterly scans for accidental commits
✅ Policy documented: No demo data with identifiers

Expiration of Decision: 12 months (Verify Apr 2027)

══════════════════════════════════════════════════════════════════

Risk Acceptance Signed By:

Compliance Officer: ________________________ (Signature)
Date: _____________________

Legal Counsel: ________________________ (Signature)
Date: _____________________
```

---

## DOCUMENTATION CHECKLIST

Use this checklist to ensure BAA process is fully documented:

```
BAA EXECUTION DOCUMENTATION CHECKLIST
Status as of: _______________

VENDOR: ___________________________

□ Vendor Assessment Form Completed
  - PHI exposure level documented
  - Security controls reviewed
  - Business justification recorded

□ BAA Procurement
  - Initial request letter sent (date: _____)
  - Vendor response received (date: _____)
  - BAA template reviewed by vendor

□ Legal Review
  - In-house legal review completed (date: _____)
  - Counsel: ___________________________
  - Concerns identified: ___________________________
  - Resolutions/amendments: ___________________________

□ Negotiations (if applicable)
  - Counter-proposal received (date: _____)
  - Negotiation notes/summary: _______________
  - Final version approved (date: _____)

□ Authorization Chain
  - Compliance Officer approval: _________ (Name, Date)
  - General Counsel approval: _________ (Name, Date)
  - Finance/CFO approval: _________ (Name, Date)
  - Executive/CEO approval: _________ (Name, Date)

□ Execution
  - Signature method: [ ] DocuSign [ ] Print-Sign [ ] Email [ ] Other
  - Signed date: _____________
  - All signatories obtained: Date completed _____________

□ Post-Execution
  - Fully executed copy filed in secure location: __________
  - Copy provided to vendor: Date _____________
  - Backup copy retained: Date copied _____________
  - BAA tracking spreadsheet updated: Date _____________
  - Vendor compliance verification initiated: Date _____________

□ Records Management
  - Original BAA location: _______________________
  - Backup location: _______________________
  - Expiration date (if time-limited): _____________
  - Renewal reminder set: Date _____________

COMPLETION STATUS: 
[ ] Complete - All items checked
[ ] In Progress - Item in work _______________
[ ] Pending - Waiting on _______________
```

---

## VENDOR OUTREACH EMAIL TEMPLATE

**Subject: Business Associate Agreement Required - HIPAA Compliance**

```
Dear [Vendor Contact],

We are expanding our use of [Vendor Name] services for 
[description of service: e.g., "cloud database hosting"]. 

As a healthcare technology company, we are subject to HIPAA 
regulations and our service expansion will involve processing 
Protected Health Information (PHI).

Per 45 CFR §164.504(e), we require all vendors handling PHI 
to execute a Business Associate Agreement. 

Could you please:

1. Confirm your organization is able to execute a BAA
2. Provide your standard BAA template (if available), OR
3. Accept our BAA template (attached)
4. Advise of timeline to execution

Our BAA includes standard HIPAA-required protections:
✓ Encryption in transit and at rest
✓ Access controls and audit logging
✓ 6-year audit retention
✓ Breach notification within 24 hours
✓ Audit rights for compliance verification

We expect to execute within 2-3 weeks. 

Please contact our Compliance Officer with any questions:
[Name]
[Email]
[Phone]

Thank you for your partnership and commitment to patient privacy.

Best regards,

[Your Name]
[Title]
TheraGenome
```

---

## SUCCESS CRITERIA - ITEM 7 COMPLETE

✅ **Item 7 is COMPLETE when:**

1. ✅ AWS BAA activated and documented
2. ✅ GitHub assessment complete (with decision documented)
3. ✅ Legal review of all BAAs completed
4. ✅ All vendor BAAs signed and filed
5. ✅ BAA tracking spreadsheet updated with all details
6. ✅ Compliance Officer sign-off obtained: _________________
7. ✅ Vendor compliance verification initiated for first audit

**Target Completion:** 1-2 weeks (Apr 3-13)

**Next Phase:** Item 8 - Penetration Testing (concurrent with Item 10)

