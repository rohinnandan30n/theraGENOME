# Business Associate Agreements (BAA) Implementation Guide

## Overview

A Business Associate Agreement (BAA) is a **legally required contract** between a HIPAA-covered entity (TheraGenome) and any vendor that handles, transmits, or processes Protected Health Information (PHI). Without BAAs, you cannot use vendors for HIPAA-regulated tasks.

**HIPAA Requirement:** 45 CFR §164.504(e) - "Ensure that any Business Associate to whom it provides Protected Health Information agrees to implement and use appropriate safeguards"

**Compliance Status:** ⏳ **BLOCKING** - Cannot deploy to production without signed BAAs

---

## Part 1: Vendor Classification & BAA Requirement Assessment

### 1.1 What is a Business Associate?

A vendor is a **Business Associate** requiring a BAA if they:

| Criteria | Examples | BAA Required |
|----------|----------|--------------|
| **Access PHI** | Database hosts storing patient data, API endpoints processing genomics | ✅ YES |
| **Process PHI** | Machine learning services analyzing patient variants, data analytics platforms | ✅ YES |
| **Transmit PHI** | Cloud storage of patient records, email services with PHI | ✅ YES |
| **Create/Receive PHI** | Laboratory information systems, EHR systems | ✅ YES |
| **Audit/Operate Infrastructure** | Cloud providers (AWS, Azure, GCP), data center operators | ✅ YES |
| **No PHI Contact** | CDNs if not caching PHI, monitoring tools if logs don't contain PHI | ❌ NO |

### 1.2 TheraGenome Vendor Inventory

**Identify all vendors and classify:**

| Vendor | Type | Uses/Processes PHI | BAA Needed | Status |
|--------|------|-------------------|-----------|--------|
| AWS | Cloud Infrastructure | Yes (RDS, S3, KMS) | ✅ | To Sign |
| PostgreSQL (open source) | Database | N/A (self-hosted) | ❌ | N/A |
| Kafka | Messaging (self-hosted) | N/A (self-hosted) | ❌ | N/A |
| Kubernetes | Orchestration (self-hosted) | N/A (self-hosted) | ❌ | N/A |
| Prometheus | Monitoring (self-hosted) | Potentially (if logs contain PHI) | ⚠️ | Review |
| Grafana | Visualization (self-hosted) | Potentially (if displays PHI) | ⚠️ | Review |
| OpenTelemetry | Observability (self-hosted) | Yes (traces contain PHI) | ✅ | To Sign |
| Trivy (Aqua Security) | Container Scanning | No (doesn't access PHI) | ❌ | N/A |
| GitHub | Version Control | Maybe (if storing code with PHI patterns) | ⚠️ | Review |
| Docker Hub | Image Registry | No (unless private registry) | ❌ | N/A |
| Slack | Team Communication | No (don't discuss PHI) | ❌ | N/A |
| **TOTAL BAAs REQUIRED** | | | **2-3** | |

### 1.3 Vendor Assessment Template

For each BAA candidate, complete this assessment:

```
VENDOR: [Name]
TYPE: [Cloud Provider / SaaS / Data Processor / Infrastructure]
DATE ASSESSED: [Date]
COMPLIANCE OFFICER: [Name]

PHI Exposure Level:
  [ ] HIGH - Direct access to patient data (RDS, patient APIs)
  [ ] MEDIUM - Process/analyze patient data (ML services, analytics)
  [ ] LOW - Indirect exposure (monitoring, logs)
  [ ] NONE - No PHI contact

Security Controls Review:
  [ ] Encryption in transit (TLS 1.2+)
  [ ] Encryption at rest (AES-256 or KMS)
  [ ] Access controls (RBAC, MFA)
  [ ] Audit logging (6-year retention)
  [ ] Incident response plan
  [ ] Penetration testing results (available)
  [ ] SOC 2 Type II or similar certification

Recommended Action:
  [ ] Require BAA
  [ ] Require BAA with enhanced terms
  [ ] May use without BAA (document risk acceptance)
  [ ] Do not use (unacceptable security posture)

Estimated Timeline to BAA: ______ weeks
```

---

## Part 2: BAA Template & Required Language

### 2.1 BAA Cover Letter Template

```
[Date]

[Vendor Name]
[Vendor Address]

RE: Request for Business Associate Agreement (BAA) - HIPAA Compliance

Dear [Vendor Contact],

TheraGenome is a HIPAA-covered entity providing genomic analysis and precision medicine 
services to patients and healthcare providers. We are implementing a new system that 
requires your services to process Protected Health Information (PHI) as defined by 
HIPAA regulations.

Per 45 CFR §164.504(e), we require all vendors handling PHI to execute a Business 
Associate Agreement. This agreement establishes the legal framework for compliant PHI handling.

Attached is our BAA template. We request that you:

1. Review the terms and confirm your ability to comply
2. Advise of any changes or exceptions required by your organization
3. Provide your own BAA if you prefer (subject to our review)
4. Provide timeline for execution

For questions, please contact our Compliance Officer: [Name, Email, Phone]

We appreciate your partnership and commitment to patient privacy.

Sincerely,

[Your Name]
[Title]
TheraGenome
```

### 2.2 Critical BAA Clauses (Minimum Required)

**CLAUSE 1: Definitions**
```
Protected Health Information (PHI): As defined by 45 CFR §160.103, includes all health 
information that identifies or reasonably can identify an individual, transmitted by or 
maintained in any form or medium by Covered Entity.

Business Associate: [Vendor name] and its subcontractors who have access to PHI.
```

**CLAUSE 2: Permitted Uses and Disclosures**
```
Business Associate shall use or disclose PHI only:
  (a) As necessary to perform services specified in the Service Agreement
  (b) For purposes specified by Covered Entity in writing
  (c) As required by law
  
Business Associate shall NOT use or disclose PHI for any other purpose, including 
marketing, fundraising, or independent research without prior written authorization.
```

**CLAUSE 3: Safeguards (THE CRITICAL CLAUSE)**
```
Business Associate shall implement and maintain administrative, physical, and technical 
safeguards to protect PHI, including:

ADMINISTRATIVE:
  - Designate a Privacy Officer and Security Officer
  - Implement workforce security policies (access controls, authentication)
  - Provide HIPAA training to all staff with PHI access
  - Implement sanctions policy for violations
  - Conduct risk assessments annually

PHYSICAL:
  - Implement facility access controls (badge access, alarms)
  - Ensure workstations are physically secured
  - Implement workstation use policies

TECHNICAL:
  - Encryption in transit (TLS 1.2 or higher)
  - Encryption at rest (AES-256 or equivalent)
  - Access controls (user authentication, strong passwords/MFA)
  - Audit logging (6-year retention minimum)
  - Transmission security (authenticate recipients before disclosure)
```

**CLAUSE 4: Breach Notification**
```
Upon discovery of a breach (unauthorized access/use/disclosure/modification of PHI 
where the risk of harm is not minimal), Business Associate shall:

  1. Notify Covered Entity within 24 hours
  2. Provide affected individual list
  3. Provide description of breach
  4. Provide Security Officer contact
  5. Provide corrective actions taken
  
Business Associate shall notify individuals without unreasonable delay, but no later 
than 60 calendar days after discovery.
```

**CLAUSE 5: Subcontractors**
```
Business Associate shall:
  - Not grant subcontractors access to PHI without prior written approval
  - Ensure subcontractors execute a BAA with equivalent terms
  - Remain liable for subcontractor compliance
```

**CLAUSE 6: Access and Amendment**
```
Business Associate shall:
  - Implement processes for Covered Entity to access/review PHI within 30 days
  - Implement systems to amend PHI as requested by Covered Entity
  - Not deny reasonable requests for access or amendment
```

**CLAUSE 7: Term and Termination**
```
Term: This BAA is effective as of [Date] and continues until terminated.

Termination:
  - Either party may terminate with 30 days written notice
  - Upon termination, Business Associate shall return or securely destroy PhI (at 
    Covered Entity's election) within 30 days, retaining only PHI required by law

Obligations Survive Termination:
  - Breach notification obligations
  - Audit and inspection rights
  - Data protection obligations (if BA chooses to retain PHI for accounting)
```

**CLAUSE 8: Audit and Inspection Rights**
```
Business Associate shall:
  - Provide Covered Entity access to facilities, systems, equipment containing/using PHI
  - Cooperate with Covered Entity's audits and inspections
  - Provide copies of security assessment/compliance reports within 30 days of request
  - Allow Compliance Officer on-site audits (with 48 hours notice)
  - Provide records of all PHI access/use (audit logs) within 60 days of request
```

**CLAUSE 9: Minimum Necessary Policy**
```
Business Associate shall implement and enforce a "Minimum Necessary" policy requiring:
  - PHI access limited to minimum necessary for job function
  - Regular access reviews (at least annually)
  - Documentation of business justification for each access grant
  - Prompt termination of access upon role change
```

**CLAUSE 10: Indemnification**
```
Business Associate shall indemnify and hold harmless Covered Entity from:
  - Losses from Business Associate's violation of this BAA
  - HIPAA penalties assessed for Business Associate's non-compliance
  - Legal fees and damages from Business Associate's breach
```

### 2.3 Full BAA Template (Customizable)

```
═══════════════════════════════════════════════════════════════════════════
BUSINESS ASSOCIATE AGREEMENT

THIS AGREEMENT (this "Agreement") is made effective as of _________, 20__ 
(the "Effective Date"), between:

COVERED ENTITY: TheraGenome, Inc. 
("Covered Entity")

BUSINESS ASSOCIATE: _________________________ 
("Business Associate")

═══════════════════════════════════════════════════════════════════════════

1. DEFINITIONS

All terms used in this Agreement without definition shall have the same meaning 
as established by the Health Insurance Portability and Accountability Act of 1996 
(HIPAA), located at 45 CFR Parts 160 and 164.

"Protected Health Information" or "PHI" means any information that: (a) can be 
used to identify an individual; (b) is received or created by Business Associate 
from, or on behalf of, Covered Entity; (c) relates to health care services or 
payment for health care services provided to an individual.

═══════════════════════════════════════════════════════════════════════════

2. PERMITTED USES AND DISCLOSURES

2.1 Business Associate shall use PHI only to:
    (a) Perform services as specified in the underlying Service Agreement
    (b) Support Covered Entity's health care operations
    (c) Comply with law, including HIPAA requirements
    (d) Support Covered Entity's breach investigation and notification

2.2 Business Associate shall NOT use or disclose PHI for:
    (a) Marketing purposes
    (b) Fundraising activities
    (c) Business purposes unrelated to Covered Entity's healthcare operations
    (d) Independent research or data analysis
    (e) Sharing with third parties without Covered Entity written authorization

2.3 If Business Associate discovers it has used or disclosed PHI in violation 
    of this clause, it shall immediately notify Covered Entity and provide 
    corrective action plan.

═══════════════════════════════════════════════════════════════════════════

3. SECURITY SAFEGUARDS

Business Associate shall implement and maintain safeguards to protect PHI 
including:

3.1 ADMINISTRATIVE SAFEGUARDS
    - Designate Privacy Officer: ________________
    - Designate Security Officer: ________________
    - Implement workforce security policies with documentation
    - Provide HIPAA training to all staff accessing PHI within 30 days of hire
    - Implement sanctions policy for HIPAA violations
    - Conduct annual risk assessments and document findings
    - Maintain policies and procedures documentation

3.2 PHYSICAL SAFEGUARDS
    - Restrict physical access to facilities containing PHI
    - Implement workstation policies defining appropriate use
    - Implement workstation security (locked screens, badge access)
    - Ensure secure storage of PHI (locked cabinets, secured servers)

3.3 TECHNICAL SAFEGUARDS - REQUIRED MINIMUM STANDARDS

    ENCRYPTION:
    - Transmission: TLS 1.2 or higher for all data in transit containing PHI
    - At Rest: AES-256 or equivalent for data stored containing PHI
    - Key Management: Encryption keys stored separately from encrypted data

    ACCESS CONTROLS:
    - User Authentication: Password policies (min 12 chars, complexity), MFA 
      for all administrative access
    - Authorization: Role-based access control (RBAC) limiting PHI access to 
      authorized personnel only
    - Access Review: Quarterly review of active access grants; immediate 
      removal upon job change
    - Logging: Audit logging of all PHI access (read/write/delete) with 
      timestamps for minimum 6 years

    TRANSMISSION SECURITY:
    - Authenticate recipient before disclosing PHI
    - Monitor for unauthorized transmission
    - Maintain logs of all PHI transmissions

═══════════════════════════════════════════════════════════════════════════

4. BREACH NOTIFICATION

4.1 Discovery of Breach: A breach is unauthorized access, use, or disclosure 
    of PHI where the risk of harm is not low.

4.2 Notification Timeline: Upon discovery, Business Associate shall notify 
    Covered Entity within 24 hours via email and phone to:
    Contact: [Covered Entity Compliance Officer]
    Email: [email]
    Phone: [phone]

4.3 Notification Content must include:
    - Date of discovery
    - Description of breach (what happened, who accessed, when)
    - Types of PHI involved
    - Number of individuals potentially affected
    - Names/contact info for affected individuals
    - Business Associate's corrective actions
    - Legal obligation to preserve evidence

4.4 Notification to Individuals: Business Associate shall notify all affected 
    individuals within 60 calendar days of discovery, including:
    - Description of breach
    - Types of PHI involved
    - Steps individuals recommended take
    - Contact info for additional information
    - Notice to credit bureaus (if more than 500 residents of state)

═══════════════════════════════════════════════════════════════════════════

5. SUBCONTRACTORS AND DOWNSTREAM VENDORS

5.1 Business Associate shall NOT permit subcontractors access to PHI without 
    prior written approval from Covered Entity.

5.2 Business Associate shall require all subcontractors to:
    - Execute a BAA with equivalent terms to this Agreement
    - Implement equivalent security safeguards
    - Agree to breach notification within 24 hours

5.3 Business Associate remains fully liable for all subcontractor compliance 
    and is responsible for all subcontractor breaches.

═══════════════════════════════════════════════════════════════════════════

6. MINIMUM NECESSARY POLICY

6.1 Business Associate shall implement a "Minimum Necessary" policy requiring:
    - Limiting PHI access to minimum required for job function
    - Maintaining documentation of business justification for each access grant
    - Quarterly review of active access
    - Immediate removal of access upon job termination or role change

6.2 Business Associate shall provide Covered Entity a summary of its minimum 
    necessary policies within 30 days of BAA execution.

═══════════════════════════════════════════════════════════════════════════

7. AUDIT AND INSPECTION RIGHTS

7.1 Business Associate shall make available to Covered Entity:
    - Facilities, systems, and equipment containing/using PHI
    - All records related to PHI storage, use, transmission
    - Audit logs and access records

7.2 Business Associate shall:
    - Cooperate fully with Covered Entity audits and inspections
    - Provide copies of security assessment reports within 30 days of request
    - Allow Compliance Officer on-site audits with 48 hours notice
    - Correct identified deficiencies within 30-60 days as specified

7.3 Business Associate shall provide:
    - Annual security assessment or SOC 2 Type II report
    - Audit log excerpts upon request (PHI access records)
    - Evidence of staff HIPAA training (certificates)
    - Proof of breach notification procedures
    - Documentation of risk assessments

═══════════════════════════════════════════════════════════════════════════

8. REQUIREMENTS FOR AMENDMENT, ACCESS, AND ACCOUNTING

8.1 Amendment: Business Associate shall implement processes enabling Covered 
    Entity to request amendments to PHI, including:
    - Process to submit amendment requests
    - Timeline: Respond within 30 days
    - Communicate amendments to all users accessing that PHI

8.2 Access: Business Associate shall enable Covered Entity to access PHI held 
    by Business Associate, including:
    - Secure method to retrieve PHI (encrypted download, portal)
    - Timeline: Provide access within 30 days of request
    - Preserve audit trail showing access and by whom

8.3 Accounting of Disclosures: Business Associate shall maintain records of 
    all PHI disclosures and provide to Covered Entity upon request:
    - Date of disclosure
    - Recipient organization/individual
    - Purpose of disclosure
    - PHI types disclosed

═══════════════════════════════════════════════════════════════════════════

9. TERM AND TERMINATION

9.1 EFFECTIVE DATE: This Agreement is effective as of the Effective Date and 
    continues until terminated.

9.2 TERMINATION:
    - Either party may terminate with 30 days written notice
    - Immediately upon material breach and failure to cure within 30 days
    - Upon Covered Entity request if required by law

9.3 Upon Termination:
    - Business Associate shall return all PHI to Covered Entity within 30 days
    - OR if return is not feasible, securely destroy all PHI and provide 
      written certification
    - Retain only PHI if explicitly required by law
    - Destruction method: Certified destruction, NIST-compliant erasure, or 
      shredding

9.4 Survival of Obligations:
    The following provisions survive termination:
    - Breach notification (Section 4)
    - Access and audit rights (Section 7) - for records Business Associate 
      retains
    - Indemnification (Section 11)
    - Confidentiality (Section 13)

═══════════════════════════════════════════════════════════════════════════

10. BUSINESS ASSOCIATE'S OBLIGATIONS AT CONTRACT TERMINATION

Upon termination of this Agreement, Business Associate shall:

a) Return or destroy all PHI as directed by Covered Entity within 30 days
b) Certify in writing compliance with destruction requirements
c) Permit audit of PHI destruction by Covered Entity upon request
d) Except as required by law, return/destroy PHI in all forms, including:
   - Production databases
   - Backup media
   - Development/test environments
   - Cache and temporary storage

═══════════════════════════════════════════════════════════════════════════

11. INDEMNIFICATION

11.1 Business Associate shall indemnify and hold harmless Covered Entity from:
     - HIPAA penalties assessed by HHS for Business Associate's violations
     - Damages awarded in private litigation stemming from Business Associate 
       violations
     - State breach notification law damages
     - Legal fees and costs incurred in defending claims

11.2 This indemnification survives termination of the underlying Service Agreement.

═══════════════════════════════════════════════════════════════════════════

12. DATA BREACH PROVISION

In the event of unauthorized access to three or more residents' PHI, or where 
a breach risk is not low, Business Associate shall:

a) Notify Covered Entity within 24 hours (email + phone call)
b) Notify media in impacted state within 60 days if 500+ residents affected
c) Implement forensic investigation within 72 hours
d) Provide preliminary investigation findings within 7 days
e) Provide detailed incident report within 30 days
f) Implement remediation measures and provide timeline

═══════════════════════════════════════════════════════════════════════════

13. LEGAL COMPLIANCE

13.1 Business Associate shall:
     - Comply with HIPAA Privacy Rule (45 CFR Part 164 Subpart E)
     - Comply with HIPAA Security Rule (45 CFR Part 164 Subpart C)
     - Comply with HIPAA Breach Notification Rule (45 CFR Part 164 Subpart D)
     - Comply with state privacy and data breach notification laws

13.2 Should HIPAA regulations change, Business Associate shall update security 
     measures to maintain compliance and notify Covered Entity of material 
     changes within 30 days.

═══════════════════════════════════════════════════════════════════════════

14. AUTHORITY AND ENFORCEMENT

14.1 Covered Entity: Authorized representative signing below has authority to 
     bind the organization to this Agreement.

14.2 HIPAA Compliance: Both parties acknowledge this Agreement is required by 
     45 CFR §164.504(e) and recognizes HHS/OCR enforcement authority.

═══════════════════════════════════════════════════════════════════════════

IN WITNESS WHEREOF, the parties have executed this Business Associate Agreement 
as of the date first written above.

COVERED ENTITY (TheraGenome):

_____________________________
Name (Print)
Date: _____________________

_____________________________
Title

_____________________________
Signature

_____________________________
Email

_____________________________
Phone

BUSINESS ASSOCIATE:

_____________________________
Organization Name

_____________________________
Name (Print)
Date: _____________________

_____________________________
Title

_____________________________
Signature

_____________________________
Email

_____________________________
Phone

═══════════════════════════════════════════════════════════════════════════
```

---

## Part 3: Vendor-Specific BAA Strategies

### 3.1 AWS BAA

**Status:** ✅ Available (AWS provides Business Associate Agreement)

**Action Steps:**
1. Log into AWS Account (or contact AWS account manager)
2. Navigate to: AWS Artifact → Agreements → Business Associate Addendum
3. Review and accept AWS BAA
4. Document execution date

**AWS BAA Covers:**
- ✅ All AWS services (RDS, S3, KMS, Lambda, etc.)
- ✅ Encryption and access controls
- ✅ Breach notification
- ✅ 12+ month data retention (longer than required)

**Verification:**
```bash
# Check AWS account has BAA active
aws artifact get-account-authorization-summary &| grep -i "baa\|business.*associate"
```

**Timeline:** 1-2 days (sign electronically in AWS Account)

---

### 3.2 OpenTelemetry / Observability Services BAA

**Status:** ⚠️ Partial (OpenTelemetry is open source; self-hosted doesn't need BAA)

**Assessment:**
- Self-hosted OpenTelemetry Collector (Kubernetes): ❌ No BAA needed
- Self-hosted Prometheus (Kubernetes): ❌ No BAA needed
- Self-hosted Grafana (Kubernetes): ❌ No BAA needed
- Managed observability service (e.g., Datadog, New Relic): ✅ **Requires BAA**

**Action:** Since TheraGenome is self-hosting all observability, **no BAA required** for Prometheus/Grafana/OTEL Collector. If you use managed services in future:
- Datadog: Has BAA template
- New Relic: Has BAA template
- Splunk: Has BAA template

**Document Decision:**
```
Observability BAA Decision:

Deployment: Self-hosted in Kubernetes (all open source)
Decision: No BAA required for self-hosted open source components
Rationale: We maintain full control; components don't leave environment
Review Date: Quarterly or upon architecture change
```

---

### 3.3 GitHub BAA (if storing code or docs with PHI patterns)

**Risk Assessment First:**
- [ ] Do you store genomics code with example patient data?
- [ ] Do documentation files reference patient identifiers?
- [ ] Do CI/CD logs contain PHI?

**If ANY above = YES:**
- GitHub has a BAA available for Enterprise customers
- RECOMMENDATION: Use GitLab or on-premises Git server (no BAA needed, full control)

**Action:**
- Review GitHub repositories for PHI: `grep -r "patient\|PHI\|genomic" --include="*.md" --include="*.py" .`
- If found: Implement data masking in documentation + require GitHub Enterprise BAA
- Recommended: Self-host Git on TheraGenome infrastructure (GitLab, Gitea) - no BAA needed

---

## Part 4: BAA Tracking & Compliance Dashboard

### 4.1 BAA Execution Checklist

Create and maintain this spreadsheet (team distribution):

```
═══════════════════════════════════════════════════════════════════════════
BAA EXECUTION TRACKER - TheraGenome
═══════════════════════════════════════════════════════════════════════════

| Vendor | Service | PHI Exposure | BAA Status | Execution Date | Expires | Owner |
|--------|---------|--------------|------------|----------------|---------|-------|
| AWS | Cloud Infrastructure (RDS, S3, KMS) | HIGH | Signed | [DATE] | No expiry | DBA |
| OpenTelemetry | Observability | N/A | N/A - Self-hosted | N/A | N/A | DevOps |
| GitHub | Version Control | LOW (if code scanned) | Pending Review | TBD | TBD | Security |

KEY STATUSES:
□ Not Required - No PHI processing
□ Pending - Vendor request sent, awaiting response
□ Negotiating - Discussing terms, outstanding issues
□ Ready to Sign - Reviewed by legal, pending signatures
□ Signed - BAA executed, documented in file
□ EXPIRED - Needs renewal
```

### 4.2 BAA Renewal Checklist

```
ANNUAL BAA RENEWAL CHECKLIST (Every 12 months)

For each signed BAA:

□ Contact vendor 60 days before expiry if time-limited
□ Review for changes needed (new services, API endpoints, security updates)
□ Notify vendor of new security requirements
□ Obtain current SOC 2 Type II or security assessment
□ Schedule compliance review meeting
□ Execute amended BAA if needed
□ Document renewal date and new expiry
□ Update BAA tracking spreadsheet
```

### 4.3 Regulatory Response Process

**If HIPAA audit/investigation initiated:**

```
1. IMMEDIATE (Within 24 hours):
   - Notify Compliance Officer and Legal
   - Collect all BAA copies and dates
   - Identify any non-compliant vendors (no BAA but process PHI)
   - Notify vendors of investigation

2. DOCUMENTATION (Within 48 hours):
   - Create BAA execution timeline
   - Document business justification for each vendor
   - Prepare vendor security assessment summaries
   - List all PHI access granted to each vendor

3. RESPONSE (Within 30 days):
   - Provide BAAs to investigators
   - Prove security safeguards in place
   - Provide audit trails of vendor PHI access
   - If gap found: Execute retroactive BAA or terminate vendor
```

---

## Part 5: Implementation Steps (Sequence)

### Phase 1: Vendor Assessment (Week 1)

**Step 1.1:** Identify all vendors processing PHI
```bash
# Document all vendors in use
cat > /tmp/vendor_audit.txt << 'EOF'
CLOUD/INFRASTRUCTURE:
- AWS (RDS, S3, KMS)

DEVELOPMENT/DEPLOYMENT:
- Kubernetes (self-hosted)
- Docker Hub (public images only)
- GitHub (code, docs - needs review)

MONITORING/OBSERVABILITY:
- Prometheus (self-hosted)
- Grafana (self-hosted)
- OpenTelemetry (self-hosted)

SECURITY/SCANNING:
- Trivy (open source, self-hosted scanning)

COMMUNICATION:
- Slack (no PHI discussions)
EOF
```

**Step 1.2:** Classify each vendor
```
For each vendor, answer:
1. Does it access/process/transmit PHI? (Yes/No)
2. Can we prevent PHI access? (Yes/No)
3. PHI exposure level? (High/Medium/Low/None)
4. BAA required? (Yes/No)
5. Vendor has pre-built BAA? (Yes/No/Unknown)
```

**Step 1.3:** Document decisions
```
Vendor Assessment Results:

REQUIRES BAA:
✅ AWS - High exposure (database, storage, keys)
   Action: Activate AWS BAA in Account

SELF-HOSTED (no BAA needed):
✅ Kubernetes, Prometheus, Grafana, OTel
   Action: Document decision with rationale

TO REVIEW:
⚠️ GitHub - Only if code contains PHI patterns
   Action: Scan repos for sensitive data

REJECTED (no BAA exists or unreasonable risk):
❌ N/A currently
```

### Phase 2: Vendor Outreach (Week 1-2)

**Step 2.1:** Send BAA requests to vendors requiring one

Use template from Section 2.1:
```bash
# For AWS (already have BAA):
- Log into AWS Console
- AWS Artifact → Agreements → Accept Business Associate Addendum
- Document date of acceptance

# For any other vendors requiring BAA:
- Send formal request letter (Section 2.1 template)
- Include BAA template (Section 2.2)
- Request response within 14 days
- Ask if they have preferred template
```

**Step 2.2:** Track vendor responses
```
Vendor Response Tracker:

AWS:
  - Status: ✅ BAA Available
  - Timeline: 1 day (self-service sign)
  - Owner: DBA
  - Target: Complete Apr 3

Other Vendors:
  - Status: ⏳ Awaiting Response
  - Timeline: 14 days from request
  - Owner: Compliance Officer
  - Follow-up: If no response by day 7, escalate
```

### Phase 3: Legal Review (Week 2)

**Step 3.1:** Have BAA reviewed by legal counsel
```
For each proposed BAA:
[ ] Legal reviews terms
[ ] Flags any non-compliant clauses
[ ] Confirms HIPAA requirements met
[ ] Approves risk profile
[ ] Authorizes signature
```

**Step 3.2:** Negotiate if needed
```
Common Negotiation Points:
1. Data Location - Ensure US data centers only (if required)
2. Subcontractors - Require notification and BA coverage
3. Audit Rights - Bank 30-60 days notice for facility audits
4. Indemnification - Confirm vendor covers HIPAA penalties
5. Term - 3-5 year standard, annual renewal option
6. Data Deletion - 30-day deletion timeline upon termination
```

### Phase 4: Execution (Week 2-3)

**Step 4.1:** Execute BAA with authorized signatories
```
REQUIRED APPROVALS:
□ Compliance Officer (HIPAA designee)
□ General Counsel or Legal Representative
□ Finance/Contract Lead (if financial impact)
□ Executive/C-Level (if vendor is strategic)

EXECUTION METHOD:
□ DocuSign or electronic signature platform
□ Printed, signed, scanned
□ Vendor's eSignature system
□ Email agreement with acceptance
```

**Step 4.2:** Retain documentation
```
BAA Document Retention:
- Retain original executed BAA (5+ years)
- Maintain in secure shared drive or records management system
- Create backup copies
- Track expiration date
- Set renewal reminders 90 days before expiry
```

### Phase 5: Compliance Verification (Week 3)

**Step 5.1:** Verify vendor compliance post-signature
```
Post-signature Checklist:

[ ] Request vendor security assessment (SOC 2 Type II or security audit)
[ ] Verify encryption standards (TLS 1.2+, AES-256)
[ ] Review vendor's breach notification procedures
[ ] Confirm audit logging (6-year retention)
[ ] Schedule initial compliance audit
```

**Step 5.2:** Document completion
```
COMPLIANCE VERIFICATION COMPLETE:

Vendor: ________________
Agreement Signed: __________
Verification Date: __________
Verified By: ________________
Status: ✅ Compliant / ⚠️ Issues Identified / ❌ Non-compliant

If Issues: Remediation Plan: ________________________
```

---

## Part 6: Risk Mitigation for Non-Compliant Vendors

**If you MUST use vendor without BAA (rare scenario):**

```
RISK ACCEPTANCE PROCESS:

1. Document Business Justification
   Why is this vendor necessary despite BAA gap?
   Alternatives considered: ____________________
   
2. Implement Compensating Safeguards
   - Encrypt all PHI before transmission (vendor never sees unencrypted data)
   - Use de-identified/pseudonymized data only
   - Limit PHI fields shared to minimum necessary
   - Implement separate API that vendors cannot see PHI via
   
3. Risk Assessment Signed
   Risk Officer signature authorizing risk acceptance
   Mitigation measures: _______________________
   Review frequency: Quarterly (not annually)
   
4. Executive Approval
   C-Level executive approval of risk
   
5. Monitor Aggressively
   - Monthly vendor security audits
   - Quarterly risk reassessment
   - Immediate action if new PHI exposure identified
   - Plan for BAA execution or vendor replacement
   
NEVER RECOMMEND: Accept PHI vendor without BAA long-term
DURATION: Maximum 90 days (temporary measure only)
```

---

## Task 7 Summary & Action Plan

**Status:** ⏳ IN PROGRESS

**Critical Actions (This Week):**
1. ✅ Identify all vendors (Completed above)
2. ⏳ Contact AWS - Activate BAA (1 day)
3. ⏳ Review GitHub for PHI exposure (1 hour)
4. ⏳ Contact other vendors if needed (ongoing)

**Success Criteria:**
- [ ] AWS BAA activated
- [ ] All vendor BAAs signed or documented as not required
- [ ] BAA tracking spreadsheet completed
- [ ] Legal review completed
- [ ] Compliance Officer sign-off obtained

**Timeline to Item 7 Complete:**
- AWS: 1 day
- Legal review: 1-3 days (if AWS is only BAA needed)
- Compliance approval: 1 day
- **Total: 3-5 days**

**Compliance Impact:**
✅ Once completed: Demonstrates HIPAA vendor management control (45 CFR §164.504)
✅ Enables production deployment
✅ Prevents regulatory penalties for non-compliant vendor use

**Next:** Execute steps in Phase 1-5 above in sequence
