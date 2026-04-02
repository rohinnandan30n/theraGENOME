# Penetration Testing - THIS WEEK ACTION PLAN

## Quick Start

**Estimated Time This Week:** 4-6 hours  
**Effort Level:** Medium (RFP creation + vendor research)  
**Complexity:** Coordinating external security assessment

---

## Timeline Overview

```
THIS WEEK (Apr 2-6): RFP & VENDOR SELECTION BEGINS
NEXT 2 WEEKS (Apr 7-20): PROPOSALS RECEIVED & EVALUATED
WEEK 3-4 (Apr 21-May 4): CONTRACTING & ENVIRONMENT PREP
WEEK 5-7 (May 5-25): PENETRATION TESTING EXECUTION
WEEK 8-12 (May 26-Jun 30): REMEDIATION PHASE
```

---

## ACTION PLAN (This Week)

### TODAY (Apr 2) - Market Research (1 hour)
```
Identify 5-7 security firms with HIPAA pen testing experience

SEARCH CRITERIA:
✅ HIPAA penetration testing experience
✅ AWS infrastructure expertise
✅ Kubernetes/container security
✅ Located in US (for compliance)
✅ HIPAA insurance/certifications

INITIAL VENDOR LIST TO RESEARCH:

1. Nessus/Tenable Services
   Website: tenable.com
   Services: Enterprise pen testing, HIPAA-certified
   Contact: Request consultation

2. Rapid7
   Website: rapid7.com
   Services: Advanced pen testing, healthcare specialists
   Contact: Sales inquiry

3. CrowdStrike Services / Falcon Complete
   Website: crowdstrike.com
   Services: Comprehensive security assessment
   Contact: Sales team

4. Mandiant (FireEye)
   Website: fireeye.com
   Services: Advanced persistent threat testing
   Contact: Healthcare vertical sales

5. Bishop Fox
   Website: bishopfox.com
   Services: Application security + infrastructure
   Contact: Consultation request

6. Coalfire
   Website: coalfire.com
   Services: HIPAA compliance, pen testing
   Contact: HIPAA consultants

7. NetSPI
   Website: netspi.com
   Services: Full-stack penetration testing
   Contact: Healthcare team

RESEARCH STEPS:
1. Visit website
2. Note: Healthcare experience, certifications, pricing range
3. Look for HIPAA/healthcare case studies
4. Identify primary contact
5. Document in vendor_list.csv

OUTPUT: Shortlist of 5-7 firms with contact info
```

### TOMORROW (Apr 3) - RFP Finalization (2 hours)
```
Customize RFP template for TheraGenome

CUSTOMIZATION STEPS:

1. Update placeholders:
   ☐ Replace [DATE] with actual dates (May 3 test start)
   ☐ Update [ACCOUNT_ID] with AWS staging account
   ☐ Customize [CLUSTER_NAME] to real K8s cluster name
   ☐ Add actual API endpoints (3-5 examples)
   ☐ Specify database system (PostgreSQL 15)
   ☐ Budget range: $20,000-$40,000 (adjust if needed)

2. Define test scope precisely:
   ☐ List ALL systems that WILL be tested
   ☐ Clarify what WON'T be tested (production, physical, DoS)
   ☐ Confirm de-identification of test data
   ☐ Define testing window (May 3-19, 2026)

3. Review legal terms:
   ☐ ROE (Rules of Engagement) - clear boundaries
   ☐ Liability limitations - reviewed by legal
   ☐ NDA provisions - standard
   ☐ Confidentiality - sensitive findings

4. Finalize deliverables:
   ☐ Report format (PDF + Word + slides)
   ☐ Finding classification scheme (CVSS 3.1)
   ☐ Timeline for delivery (within 2 weeks of testing)
   ☐ Support/clarification period (2 weeks post-delivery)

SAVE AS: PENETRATION_TESTING_RFP.docx
```

### WEDNESDAY (Apr 4) - RFP Issuance (1-2 hours)
```
Send RFP to selected vendors

STEPS:
1. Email draft to legal counsel - QUICK REVIEW (1 hour)
   Subject: "Pen Testing RFP - Legal Review Request"
   Request: Review by EOD tomorrow for any red flags

2. Upon legal clearance, prepare email package:
   Attachments:
   ☐ PENETRATION_TESTING_RFP.docx (main document)
   ☐ PENETRATION_TESTING_GUIDE.md (reference for vendors)
   ☐ Architecture diagram (if available)
   ☐ API endpoint listing
   ☐ System inventory (technologies + versions)

3. Send to each vendor:
   
   SUBJECT: "Penetration Testing RFP - Healthcare Genomics Platform"
   
   BODY TEMPLATE:
   """
   Dear [Vendor Name],
   
   TheraGenome is seeking proposals for a comprehensive penetration 
   testing assessment of our cloud-based healthcare genomics platform.
   
   Key Details:
   • Scope: Cloud infrastructure + microservices + database security
   • Timeline: Testing begins May 3, 2026 (3-week duration)
   • Environment: AWS staging (isolated from production)
   • Budget: $20,000-$40,000 (board approved)
   • HIPAA Focus: Patient data security + compliance validation
   
   Attached RFP outlines all requirements. We request proposals by 
   [DATE - 2 weeks from send].
   
   Are you interested and available for this engagement? 
   Please confirm Receive/interest by [DATE + 3 days].
   
   Contact for questions: [Your Name, Email, Phone]
   
   Thank you,
   """
   
   SEND TO:
   [ ] sales@vendor1.com
   [ ] sales@vendor2.com
   [ ] sales@vendor3.com
   [ ] sales@vendor4.com
   [ ] sales@vendor5.com

4. Create vendor tracking spreadsheet:
   | Vendor | Sent | Confirmed Interest | Proposal Due | Status |
   |--------|------|-------------------|--------------|--------|
   | ... | Apr 4 | Awaiting | Apr 18 | ⏳ |

EXPECTED OUTCOME: 3-4 firms confirm interest by Apr 7
```

### THURSDAY-FRIDAY (Apr 5-6) - Vendor Outreach & Prep (1-2 hours)
```
Follow up on interest + prepare for evaluations

STEPS:

1. Thu morning - Call/email follow-ups (30 min)
   If no response from vendors by EOD Wed:
   → Call their main number
   → Ask for security services team
   → Confirm RFP receipt
   → Verify proposal deadline understood
   
2. Thu afternoon - Prepare evaluation scorecard (30 min)
   Create spreadsheet for proposal scoring:
   
   | Vendor | Experience | Team | Approach | Cost | Total |
   |--------|-----------|------|----------|------|-------|
   | | /100 | /100 | /100 | /100 | /400 |
   
   Scoring criteria (already detailed in RFP):
   ☐ Qualifications/certifications (40%)
   ☐ Approach & methodology (25%)
   ☐ Timeline/availability (15%)
   ☐ Pricing competitiveness (15%)
   ☐ References/experience (5%)

3. Fri morning - Notify internal stakeholders (30 min)
   Email: Security team, Compliance, Dev lead
   
   Subject: "Penetration Testing RFP Issued - Timeline"
   Body:
   """
   Pen testing RFP issued to [N] vendors targeting May 3 start.
   
   Timeline:
   • Proposals due: Apr 18
   • Selection: Apr 20
   • Contracting: Apr 21-May 1
   • Testing: May 3-19
   • Remediation: May 20-Jun 30
   • Production: Jul 1 (estimated)
   
   Action items for teams:
   ☐ Staging environment readiness verification (next week)
   ☐ Test data preparation (de-identified patient records)
   ☐ On-call team assignment (May 3-19)
   ☐ Internal security review procedures (for findings)
   
   Questions? Contact: [You]
   """

4. Fri afternoon - Prepare staging environment checklist (30 min)
   Document what needs to be ready:
   ☐ Isolated from production ✅ / ⏳ / ❌
   ☐ Test data prepared ✅ / ⏳ / ❌
   ☐ SSL certificates ✅ / ⏳ / ❌
   ☐ Monitoring configured ✅ / ⏳ / ❌
   ☐ Incident response team identified ✅ / ⏳ / ❌
   
   Assign owners to prepare each for Apr 20-30
```

---

## Vendor Selection Criteria Quick Reference

```
MUST HAVE (Non-negotiable):
✅ HIPAA penetration testing experience (5+ years)
✅ AWS infrastructure expertise
✅ Team certifications (CEH, OSCP, GPEN minimum)
✅ Healthcare client references (3 minimum)
✅ Risk/liability insurance ($1M+ general, $2M+ professional)
✅ Availability to start May 3

NICE TO HAVE (Preferred):
✓ Kubernetes/container security experience
✓ Kubernetes cluster penetration testing
✓ OWASP Top 10 application testing
✓ Database security expertise (PostgreSQL)
✓ Experience with genomics/biotech sector
✓ Emergency response capability (24/7)
✓ Competitive pricing (under $30K if possible)
```

---

## Vendor Evaluation Scoring

When proposals arrive (Apr 18), score each using this matrix:

```
PENETRATION TESTING PROPOSAL EVALUATION

Vendor: _________________________
Date Evaluated: __________________
Evaluator: _______________________

SCORING SCALE: 0-10 points per category

A. FIRM QUALIFICATIONS (40% weight = max 40 points)
   ☐ Lead tester certifications (CEH/OSCP/GPEN): ___/9
   ☐ Healthcare/HIPAA background (5+ years): ___/9
   ☐ Team composition and depth: ___/9
   ☐ Insurance & legal framework: ___/9
   ☐ References quality and relevance: ___/4
   SUBTOTAL A: ___/40

B. APPROACH & METHODOLOGY (25% weight = max 25 points)
   ☐ Testing comprehensiveness: ___/7
   ☐ Cloud/AWS specific approach: ___/6
   ☐ Application security testing: ___/6
   ☐ Report quality & detail: ___/4
   ☐ Remediation support: ___/2
   SUBTOTAL B: ___/25

C. SCHEDULE & AVAILABILITY (15% weight = max 15 points)
   ☐ Can start May 3: ___/5
   ☐ 3-week timeline feasible: ___/5
   ☐ Escalation/emergencies: ___/5
   SUBTOTAL C: ___/15

D. PRICING (15% weight = max 15 points)
   [ ] Under $25K: 15 points
   [ ] $25K-$30K: 12 points
   [ ] $30K-$35K: 10 points
   [ ] $35K-$40K: 7 points
   [ ] Over $40K: 0 points
   SUBTOTAL D: ___/15

E. REFERENCES (5% weight = max 5 points)
   Reference 1: [Company] Rating: ___/5
   Reference 2: [Company] Rating: ___/5
   Reference 3: [Company] Rating: ___/5
   SUBTOTAL E (avg of top 2): ___/5

═══════════════════════════════════════════════════════════════
TOTAL SCORE: ___/100

DECISION MATRIX:
85-100: Excellent - Recommend for selection
75-84:  Good - Consider if top choice unavailable
65-74:  Acceptable - Only if limited options
<65:    Not recommended
═══════════════════════════════════════════════════════════════
```

---

## Key Dates & Triggers

```
TRIGGER-BASED MILESTONES:

[Apr 2] TODAY
  Trigger: Item 8 started
  Action: Begin vendor research
  Owner: Security Lead

[Apr 7] RFP DUE TO LEGAL
  Trigger: RFP ready
  Action: Submit to legal counsel
  Owner: Compliance Officer

[Apr 11] RFP ISSUED
  Trigger: Legal clearance received
  Action: Send to 5+ vendors
  Owner: Compliance Officer

[Apr 15] VENDOR INTEREST CHECK
  Trigger: 3-day follow-up window
  Action: Call/email non-responders
  Owner: Security Lead

[Apr 18] PROPOSALS DUE
  Trigger: Submission deadline
  Action: Receive all proposals
  Owner: Compliance Officer

[Apr 20] VENDOR SELECTED
  Trigger: Scoring complete
  Action: Notify winning vendor
  Owner: Security Lead

[May 1] CONTRACT SIGNED
  Trigger: Final negotiations complete
  Action: Execute agreement, transfer fees
  Owner: Finance

[May 3] TESTING BEGINS
  Trigger: Kickoff meeting
  Action: Start penetration testing
  Owner: Tester

[May 19] TESTING ENDS
  Trigger: 3-week window complete
  Action: Collect final findings
  Owner: Tester

[May 26] REPORT RECEIVED
  Trigger: Final report delivery
  Action: Begin findings triage
  Owner: Security Lead

[Jun 30] REMEDIATION COMPLETE
  Trigger: All HIGH+ fixed
  Action: Prepare for production
  Owner: Dev Lead
```

---

## Success Metrics This Week

**By Friday Apr 6:**
```
☐ RFP customized for TheraGenome
☐ RFP reviewed by legal counsel
☐ 5+ security firms identified
☐ RFP sent to all vendors
☐ Vendor tracking spreadsheet created
☐ Internal teams notified of timeline
☐ Staging environment readiness confirmed

SIGN-OFF:

Compliance Officer: _________________ Date: _______
Status: [ ] ON TRACK [ ] DELAYED [ ] BLOCKED
Comments: ___________________________________
```

---

## Next Steps (Next Week - Apr 9-13)

1. Mon Apr 9: Follow up on vendor interest
2. Tue Apr 10: Prepare staging environment for testing
3. Wed Apr 11: Brief incident response team
4. Thu Apr 12: Receive first proposals (likely)
5. Fri Apr 13: Begin proposal evaluation

**Target:** Vendor selected by Apr 20

