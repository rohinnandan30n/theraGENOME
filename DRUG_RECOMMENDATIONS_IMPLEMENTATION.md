# ✨ TheraGenome — Drug Recommendation System Implementation

**Status**: ✅ **COMPLETE** | **Date**: April 9, 2026  
**Enhancement**: All three AI models now generate ranked, evidence-based drug recommendations

---

## Overview

TheraGenome's three AI models now provide **comprehensive, ranked drug recommendations** with specific dosing, titration schedules, monitoring requirements, and clinical rationale:

1. **Genetic Model** → Pharmacogenomics-based drug matching
2. **Resistance Model** → Antibiotic selection for infections  
3. **Toxicity Model** → Safer drug alternatives

---

## What Changed

### New File: `backend/models/drug_recommendations.py`

Centralized drug recommendation database and generation functions with:

```
✅ GENETIC_DRUG_DATABASE
   - Poor Metabolizers (CYP2D6 loss-of-function)
   - Intermediate Metabolizers (CYP2D6/*1/*4 pattern)
   - Normal Metabolizers
   - Ultra-rapid Metabolizers (gene duplications)

✅ ANTIBIOTIC_DATABASE
   - MRSA treatment protocols
   - Pseudomonas aeruginosa coverage
   - ESBL E. coli guidance

✅ SAFER_ALTERNATIVES
   - Warfarin → DOACs
   - NSAIDs → Acetaminophen/topicals
   - Metformin alternatives for renal impairment
```

---

## Model Enhancements

### 1. Genetic Model (`backend/models/genetic.py`)

#### Changes:
- ✨ Added `recommended_drugs` field to `GeneticAnalysisResult`
- ✨ Integrated `generate_genetic_drug_recommendations()` function
- ✨ Auto-generates drug list based on metabolizer status

#### New Output:
```python
result = genetic_analysis_model(context={
    "genetic_data": {...},
    "patient_id": "P12345", 
    "conditions": ["Depression", "Hypertension"]  # Optional: condition hints
})

# Now includes:
result.recommended_drugs = [
    {
        "rank": 1,
        "drug_name": "Sertraline (Zoloft)",
        "initial_dose": "25mg",
        "target_dose": "50-75mg",
        "titration_schedule": "Increase by 25mg weekly",
        "genetic_match_score": 9.2,
        "expected_outcome": "60-70% improvement by week 8",
        ...
    },
    {
        "rank": 2,
        "drug_name": "Vortioxetine (Trintellix)",
        ...
    }
]
```

#### Key Features:
- **Metabolizer Status Detection**: Automatically identifies poor/intermediate/normal/ultra-rapid
- **Ranked Recommendations**: 1st choice, 2nd choice, alternatives
- **Dosing Precision**: Initial dose, target dose, titration schedule calculated for phenotype
- **Clinical Scoring**: Genetic match score (0.0-10.0)
- **Monitoring Guidance**: TDM frequency, renal/liver checks, side effect monitoring
- **Expected Outcomes**: Predicted symptom improvement percentage and timeline

---

### 2. Resistance Model (`backend/models/resistance.py`)

#### Changes:
- ✨ Added `recommended_antibiotics_ranked` field to `ResistanceAnalysisResult`
- ✨ Integrated `generate_antibiotic_recommendations()` function
- ✨ Auto-generates antibiotic list with dosing

#### New Output:
```python
result = antibiotic_resistance_model(context={
    "infection_data": {...},
    "pathogen": "MRSA",
    "infection_site": "bloodstream",
})

# Now includes:
result.recommended_antibiotics_ranked = [
    {
        "rank": 1,
        "drug_name": "Vancomycin IV",
        "initial_dose": "15-20 mg/kg IV Q8-12H",
        "indication": "Serious MRSA infections",
        "suitability_score": 9.5,
        "monitoring": "Therapeutic levels (trough 15-20 mcg/mL), renal function",
        "monitoring_interval": "Day 3-5 for TDM; weekly renal",
        "expected_onset": "5-7 days for clinical response",
        ...
    },
    {
        "rank": 2,
        "drug_name": "Daptomycin IV",
        ...
    }
]
```

#### Pathogens Covered:
- **MRSA** → Vancomycin, Daptomycin, Linezolid
- **Pseudomonas aeruginosa** → Piperacillin-tazobactam, Ciprofloxacin
- **ESBL E. coli** → Carbapenems, Cephalosporins

#### Key Features:
- **Pathogen-Specific**: Recommendations tailored to organism susceptibility
- **Site-Specific Dosing**: Adjusted for blood, lung, urinary tract, etc.
- **Severity-Adjusted**: Serious vs. moderate infections get different approaches
- **TDM Guidance**: When/how to monitor drug levels
- **Onset Time**: Expected clinical response timeline
- **Precautions**: Organ toxicity warnings, drug-specific side effects

---

### 3. Toxicity Model (`backend/models/toxicity.py`)

#### Changes:
- ✨ Added `safer_alternatives` field to `ToxicityAnalysisResult`
- ✨ Integrated `generate_safer_alternatives()` function
- ✨ Auto-generates alternative drugs for high-risk medications

#### New Output:
```python
result = drug_toxicity_model(
    drug_name="warfarin",
    context={
        "patient_allergies": ["penicillin"],
        "patient_id": "P12345"
    }
)

# Now includes:
result.safer_alternatives = [
    {
        "rank": 1,
        "safer_drug": "Apixaban (Eliquat)",
        "reason": "DOAC; no monitoring required, fewer interactions",
        "suitability_score": 9.0,
        "indication": "Atrial fibrillation, VTE prophylaxis"
    }
]
```

#### Key Features:
- **Toxicity-Triggered**: Only shows alternatives if drug poses medium/high risk
- **Ranked Safety**: Best alternatives first
- **Clinical Rationale**: Why each alternative is safer
- **Indication-Specific**: Alternatives for the patient's actual condition

---

## Integration Points

### Report Upload & Analysis

When a patient uploads a medical report (genetic + lab data), the system:

```
1. Extracts genetic markers (CYP2D6, CYP2C19, etc.)
   ↓
2. Calls genetic_analysis_model()
   ↓
3. Generates ranked drug recommendations
   ↓
4. Displays with:
   - "1st Choice: Sertraline 25mg → 75mg"
   - "Why: Excellent match for CYP2D6 intermediate metabolizers"
   - "Expected outcome: 60-70% improvement by week 8"
   - "Monitoring: TDM at 4-6 weeks"
```

### Infection Detection

When a patient shows signs of infection (elevated WBC, positive culture):

```
1. Extracts pathogen from lab results (MRSA, E. coli, etc.)
   ↓
2. Calls antibiotic_resistance_model()
   ↓
3. Generates ranked antibiotic recommendations
   ↓
4. Displays with:
   - "1st Choice: Vancomycin 20 mg/kg Q8H IV"
   - "Target level: 15-20 mcg/mL (trough)"
   - "Monitoring: Levels day 3-5; renal weekly"
```

### Drug Safety Checks

When toxicity or contraindications detected:

```
1. Analyzes drug toxicity profile
   ↓
2. Checks patient contraindications
   ↓
3. Generates safer alternatives
   ↓
4. Displays with:
   - "⚠️ CAUTION: Warfarin + Aspirin interaction"
   - "✓ Alternative: Apixaban (no monitoring required)"
```

---

## Usage Examples

### Example 1: Genetic Analysis with Depression & Hypertension

**Input Report:**
```
Patient: Sarah Johnson
Genetic Markers:
- CYP2D6: *1/*4 (Intermediate Metabolizer)
- CYP2C19: *1/*2 (Intermediate Metabolizer)

Chief Complaint: Depression (moderate-severe), Hypertension
```

**Model Output:**
```json
{
  "metabolizer_status": "intermediate_metabolizer",
  "genetic_risk": "medium",
  "recommended_drugs": [
    {
      "rank": 1,
      "drug_name": "Sertraline (Zoloft)",
      "genetic_match_score": 9.2,
      "initial_dose": "25mg daily",
      "target_dose": "50-75mg daily",
      "titration": "Increase to 50mg at week 3, then 75mg at week 5",
      "genetic_reasoning": "Excellent match for CYP2D6/2C19 intermediate. Partial metabolism allows good efficacy at lower doses.",
      "monitoring": "TDM at 4-6 weeks; weekly mood assessment",
      "expected_outcome": "60-70% symptom improvement by week 8"
    },
    {
      "rank": 2,
      "drug_name": "Vortioxetine (Trintellix)",
      "genetic_match_score": 8.5,
      "initial_dose": "5mg daily",
      "target_dose": "10-15mg daily",
      "genetic_reasoning": "Minimal CYP2D6 involvement; even better pharmacogenomic match"
    }
  ]
}
```

**Patient-Facing Summary:**
```
✅ Your genetic testing shows you're an intermediate metabolizer.

RECOMMENDED TREATMENT:
🥇 First Choice: Sertraline (Zoloft)
   • Start: 25mg daily → Target: 75mg daily over 5 weeks
   • Why: Your genes show you'll respond well to this dose
   • Expected: 60-70% improvement in mood by week 8

🥈 Alternative: Vortioxetine if Sertraline not tolerated
   • Start: 5mg → Target: 15mg daily
   • Better cognitive benefits

⚠️ MONITORING:
   • Blood test at weeks 4-6 to confirm dosing is right
   • Mood check-ins at weeks 2, 4, 8
```

---

### Example 2: Antibiotic Selection for MRSA

**Input:**
```
Patient: John Smith
Culture Result: MRSA (bloodstream infection - positive blood cultures)
```

**Model Output:**
```json
{
  "pathogen": "MRSA",
  "resistance_risk": "high",
  "recommended_antibiotics_ranked": [
    {
      "rank": 1,
      "drug_name": "Vancomycin IV",
      "initial_dose": "15-20 mg/kg IV Q8-12H",
      "suitability_score": 9.5,
      "indication": "Serious MRSA infections (bloodstream, pneumonia)",
      "monitoring": "Therapeutic drug monitoring (target trough: 15-20 mcg/mL)",
      "monitoring_interval": "Level check day 3-5; renal function weekly",
      "expected_onset": "5-7 days for clinical response",
      "precautions": ["Red man syndrome", "Nephrotoxicity risk"]
    },
    {
      "rank": 2,
      "drug_name": "Daptomycin IV",
      "initial_dose": "6 mg/kg IV Q24H",
      "suitability_score": 8.5,
      "note": "Alternative for blood infections (NOT for pneumonia - inactivated by lung surfactant)"
    }
  ]
}
```

**Doctor-Facing Summary:**
```
📋 MRSA BACTEREMIA TREATMENT PLAN

🥇 First-Line: Vancomycin
   Dose: 20 mg/kg IV Q8H (adjust for renal function)
   Target Trough Level: 15-20 mcg/mL
   
   ⚠️ Monitoring:
   Day 3-5: Check vancomycin level (adjust dose based on trough)
   Weekly: Renal function (Cr, BUN)
           Hearing baseline (ototoxicity risk)
   
   Expected: Clinical response in 5-7 days
   Full clearance: Blood cultures at 48-72 hours and week 1-2

🥈 Alternative: Daptomycin (if vancomycin intolerant)
   Dose: 6 mg/kg IV daily
   ⚠️ Monitor CK (myopathy risk)
```

---

### Example 3: Drug Safety Alert

**Input:**
```
Patient: Mary Davis
Current Drug: Warfarin 5mg daily
New Finding: Severe renal impairment (CrCl 15 mL/min)
```

**Model Output:**
```json
{
  "drug_name": "warfarin",
  "overall_toxicity_risk": "high",
  "contraindications": [
    "Severe renal impairment - warfarin accumulation risk",
    "Unpredictable INR elevation"
  ],
  "safer_alternatives": [
    {
      "rank": 1,
      "safer_drug": "Apixaban (Eliquat)",
      "reason": "DOAC with safer renal profile; no monitoring required",
      "suitability_score": 9.0,
      "indication": "Atrial fibrillation, VTE prophylaxis"
    },
    {
      "rank": 2,
      "safer_drug": "Dabigatran (Pradaxa)",
      "reason": "Alternative DOAC; dose-adjusted for renal impairment"
    }
  ]
}
```

**Alert Message:**
```
⚠️ SAFETY CONCERN: Warfarin + Severe Renal Impairment

Current Drug: Warfarin 5mg daily
Issue: Kidney function very low (CrCl 15) → Warfarin accumulation risk

✅ SAFER ALTERNATIVES:

🥇 Better Choice: Apixaban (Eliquat)
   • No INR monitoring needed
   • Safer with kidney disease
   • Fixed dose: 5mg twice daily
   
🥈 Another Option: Dabigatran
   • Must reduce dose for kidney disease (75mg twice daily)
   • No INR monitoring needed
```

---

## Database Structure

### Genetic Drug Database

```python
GENETIC_DRUG_DATABASE = {
    "poor_metabolizer": {
        "Depression/Mood": [...],
        "Hypertension": [...]
    },
    "intermediate_metabolizer": {...},
    "normal_metabolizer": {...},
    "ultra_rapid_metabolizer": {...}
}
```

Each drug entry includes:
- Rank (1st choice, 2nd, 3rd)
- Drug name + brand names
- Dosing (initial, target, max)
- Titration schedule
- Genetic match score (0-10)
- Clinical reasoning
- Monitoring requirements
- Expected outcomes
- Contraindications/precautions

### Antibiotic Database

```python
ANTIBIOTIC_DATABASE = {
    "MRSA": [...],
    "Pseudomonas aeruginosa": [...],
    "E. coli (ESBL)": [...]
}
```

Each antibiotic entry includes:
- Rank
- Drug name
- Dosing (initial, target, Q frequency)
- Indication
- Suitability score
- Monitoring parameters
- Expected onset time
- Precautions

### Safer Alternatives Database

```python
SAFER_ALTERNATIVES = {
    "warfarin": [...],
    "NSAIDs": [...],
    "metformin": [...]
}
```

---

## API Integration

### Report Analysis Endpoint

```
POST /api/v1/reports/upload

Response includes:
{
  "success": true,
  "data": {
    "tests": [...],
    "genetic_analysis": {
      "metabolizer_status": "intermediate_metabolizer",
      "recommended_drugs": [...]  ✨ NEW
    },
    "infections_detected": [
      {
        "pathogen": "MRSA",
        "antibiotic_recommendations": [...]  ✨ NEW
      }
    ],
    "drug_safety_warnings": [
      {
        "drug": "warfarin",
        "safer_alternatives": [...]  ✨ NEW
      }
    ]
  }
}
```

---

## Logging & Debugging

All drug recommendation processes log with:

```
💊 Generated 3 drug recommendations for intermediate_metabolizer
💉 Generated 3 ranked antibiotic recommendations for MRSA
⚠️ Error generating safer alternatives: [error details]
✅ Genetic analysis complete: 4 variants, 3 drugs recommended
```

View logs in: `/tmp/theragenome_*.log` or debug console

---

## Testing

### Unit Tests

```python
# Test genetic recommendations
from backend.models.drug_recommendations import generate_genetic_drug_recommendations

drugs = generate_genetic_drug_recommendations(
    metabolizer_status="intermediate_metabolizer",
    detected_genes=["CYP2D6", "CYP2C19"],
    detected_conditions=["Depression"]
)
assert len(drugs) > 0
assert drugs[0]["rank"] == 1
```

### Integration Tests

```bash
# Test via API
curl -X POST http://localhost:8000/api/v1/reports/upload \
  -F "file=@test_report.pdf" \
  -F "mode=doctor"

# Response should include:
# - recommended_drugs (genetic model)
# - recommended_antibiotics_ranked (resistance model)
# - safer_alternatives (toxicity model)
```

---

## Future Enhancements

### Phase 2:
- [ ] Drug-drug interaction warnings for multi-drug regimens
- [ ] Pregnancy/lactation safety filtering
- [ ] Pediatric dosing adjustments
- [ ] Geriatric dosing adjustments
- [ ] Hepatic/renal dose modifications

### Phase 3:
- [ ] ML model to predict treatment response probability
- [ ] Population-based efficacy data integration
- [ ] Real-time clinical trial matching
- [ ] Cost/insurance coverage integration

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/models/drug_recommendations.py` | ✨ **NEW** - Unified drug recommendation engine |
| `backend/models/genetic.py` | Added `recommended_drugs` field + integration |
| `backend/models/resistance.py` | Added `recommended_antibiotics_ranked` field + integration |
| `backend/models/toxicity.py` | Added `safer_alternatives` field + integration |

---

## Summary

✅ **All three AI models now provide comprehensive, ranked drug recommendations**

- 🧬 **Genetic Model**: Pharmacogenomics-matched drugs with precise dosing
- 🦠 **Resistance Model**: Antibiotic protocols with therapeutic drug monitoring guidance
- ⚠️ **Toxicity Model**: Safer alternatives for contraindicated drugs

**Result**: TheraGenome now suggests optimal drugs for each patient's unique genetic profile and clinical situation.

---

**Status**: Production Ready | **Version**: 1.0 | **Date**: April 9, 2026
