# 📚 Drug Recommendation Database Structure & Extension Guide

**How to add new drugs to TheraGenome's recommendation engine**

---

## Database Architecture

### Three Main Databases

```
drug_recommendations.py
│
├── GENETIC_DRUG_DATABASE
│   └── Organized by metabolizer status × condition
│       └── Contains 50+ drugs with full specifications
│
├── ANTIBIOTIC_DATABASE  
│   └── Organized by pathogen
│       └── Contains protocols for MRSA, Pseudomonas, etc.
│
└── SAFER_ALTERNATIVES
    └── Organized by original drug
        └── Contains safer/alternative drugs
```

---

## 1. Adding to GENETIC_DRUG_DATABASE

### Structure Template

```python
GENETIC_DRUG_DATABASE = {
    "metabolizer_status": {
        "condition_key": [
            {
                # REQUIRED FIELDS
                "rank": 1,                              # 1, 2, 3, etc.
                "category": "Drug Class - Rank",        # "Antidepressant - First Choice"
                "drug_name": "Generic (Brand)",         # "Sertraline (Zoloft)"
                "brand_names": ["Zoloft", "Lustral"],   # Alternative brands
                
                # DOSING FIELDS
                "initial_dose": "25mg",                 # Starting dose
                "target_dose": "50-75mg",               # Goal therapeutic dose
                "max_dose": "200mg",                    # Safety ceiling
                "dosing_interval": "daily",             # "daily", "Q6H", "Q8-12H", etc.
                
                # TITRATION GUIDANCE
                "titration_schedule": "Increase by 25mg weekly to target",
                
                # INDICATION & MATCHING
                "indication": "Depression, anxiety",
                "genetic_match_score": 9.2,            # 0.0-10.0 (higher = better fit)
                "genetic_reasoning": "Partially metabolized by CYP2D6...",
                
                # MONITORING
                "monitoring_requirements": "TDM at 4-6 weeks; assess mood weekly",
                "expected_outcome": "60-70% symptom improvement by week 8",
                "onset_time": "2-4 weeks with full effect at 8-12 weeks",
                
                # SAFETY
                "contraindications": ["Aneurysm", "Untreated glaucoma"],
                "precautions": ["Serotonin syndrome", "Hyponatremia", "GI upset"],
                "interactions": ["Warfarin", "NSAIDs"],
            },
            # Additional rank 2, 3, etc. drugs for same condition...
        ]
    }
}
```

### Step-by-Step: Add a New Depression Drug

#### 1. Choose the metabolizer status
```python
# For intermediate metabolizers
"intermediate_metabolizer": {
    "Depression/Mood": [
        # Existing drugs...
        
        # ADD NEW DRUG HERE
        {
            "rank": 4,  # New option
            "category": "Antidepressant - Specialized",
            "drug_name": "Bupropion (Wellbutrin)",
            ...
        }
    ]
}
```

#### 2. Fill in dosing information

```python
{
    "initial_dose": "150mg",         # Usually XL formulation
    "target_dose": "300mg",          # Typical therapeutic
    "max_dose": "450mg",             # FDA maximum
    "titration_schedule": "Start 150mg daily, increase by 150mg every 3 days to target 300mg daily",
    "dosing_interval": "daily",
}
```

#### 3. Determine genetic match score

**Scoring Guide**:
- **9.0-10.0**: Excellent - Perfect fit for this metabolizer status
- **8.0-8.9**: Very Good - Great fit, minor concerns
- **7.0-7.9**: Good - Acceptable choice
- **6.0-6.9**: Fair - Use if others don't work
- **<6.0**: Not recommended - Include only if no alternatives

```python
{
    "genetic_match_score": 8.0,  # Bupropion: CYP2D6/3A4 substrate, good for intermediate
    "genetic_reasoning": "Metabolism via CYP2D6 and CYP3A4; good fit for intermediate metabolizers. Advantage: Lower sexual dysfunction risk vs SSRIs.",
}
```

#### 4. Add clinical details

```python
{
    "indication": "Depression, ADHD, smoking cessation",
    "monitoring_requirements": "Baseline ECG (seizure risk); check BP and HR weekly",
    "expected_outcome": "55-65% symptom improvement; energy boost by week 3-4",
    "onset_time": "Faster than SSRIs (1-2 weeks); full effect at 6-8 weeks",
    "precautions": [
        "Seizure risk (0.4% at standard dose, 1% at 450mg)",
        "Hypertension (monitor BP)",
        "Insomnia (dose in morning)",
        "Activation in bipolar patients",
    ],
    "interactions": [
        "CYP3A4 inhibitors (ketoconazole, erythromycin)",
        "Alcohol (increases seizure risk)",
        "Linezolid",
    ],
}
```

#### 5. Complete Example

```python
{
    "rank": 4,
    "category": "Antidepressant - Alternative (Non-SSRI)",
    "drug_name": "Bupropion XL (Wellbutrin)",
    "brand_names": ["Wellbutrin XL", "Aplenzin", "Forfivo"],
    "initial_dose": "150mg XL",
    "target_dose": "300mg XL daily",
    "max_dose": "450mg",
    "dosing_interval": "daily",
    "titration_schedule": "Start 150mg daily, increase to 300mg at day 3, max 450mg at day 6-7",
    "indication": "Depression (especially with fatigue), ADHD, smoking cessation",
    "genetic_match_score": 8.0,
    "genetic_reasoning": "CYP2D6/3A4 substrate; excellent for intermediate metabolizers. Offers dopaminergic effect lacking in SSRIs.",
    "contraindications": [
        "History of seizures",
        "Anorexia/bulimia",
        "Abrupt discontinuation of benzodiazepines/alcohol",
    ],
    "precautions": [
        "Seizure risk increases with dose >300mg",
        "Hypertension (occurs in 10-20%)",
        "Insomnia (dose early in day)",
        "Activation/anxiety in first 1-2 weeks",
        "Risk in bipolar depression (can trigger mania)",
    ],
    "monitoring_requirements": "Baseline ECG; BP monitoring at each visit; seizure precautions. No TDM typically needed.",
    "expected_outcome": "50-65% symptom improvement, especially mood and energy by week 8",
    "onset_time": "Faster than SSRIs: 1-2 weeks for energy boost, 4-6 weeks for full mood effect",
    "interactions": [
        "CYP3A4/2B6 inhibitors: ketoconazole, erythromycin",
        "Alcohol: increases seizure risk",
        "Levodopa: CNS side effects",
        "MAOIs: absolute contraindication",
        "Other seizure-lowering drugs",
    ],
}
```

---

### Metabolizer Status Options

Use exactly one of these as key:

```python
GENETIC_DRUG_DATABASE = {
    "poor_metabolizer":              # CYP450 loss-of-function
    "intermediate_metabolizer":      # CYP450 reduced function  
    "normal_metabolizer":            # Standard CYP450 function
    "ultra_rapid_metabolizer":       # CYP450 gene duplication/high activity
}
```

### Condition Keys

Use exactly one of these as sub-key:

```python
{
    "Depression/Mood":               # Depression, bipolar, mood disorders
    "Hypertension":                  # Blood pressure management
    "Anxiety":                       # Anxiety, panic, OCD, PTSD
    "Pain":                          # Chronic pain, neuropathy
    "Arrhythmias":                   # Cardiac rhythm
    "Migraine":                      # Headache prevention
    "ADHD":                          # Attention deficit
    "GERD":                          # Acid reflux
}
```

---

## 2. Adding to ANTIBIOTIC_DATABASE

### Structure Template

```python
ANTIBIOTIC_DATABASE = {
    "Pathogen_Name": [
        {
            # RANKING & IDENTIFICATION
            "rank": 1,                               # Choice order
            "drug_name": "Vancomycin",              # Must include formulation
            "category": "Glycopeptide",             # Drug class
            
            # DOSING
            "initial_dose": "15-20 mg/kg IV Q8-12H",  # Weight-based
            "target_dose": "15-20 mg/kg Q8H",
            
            # INDICATION & SUITABILITY
            "indication": "Serious MRSA infections (bloodstream, pneumonia)",
            "suitability_score": 9.5,               # 0.0-10.0
            "reasoning": "Gold standard; requires TDM for optimization",
            
            # THERAPEUTIC DRUG MONITORING
            "monitoring": "Therapeutic levels, renal function, hearing baseline; vancomycin levels (target trough 15-20 mcg/mL)",
            "monitoring_interval": "TDM day 3-5; renal function weekly; hearing baseline",
            
            # CLINICAL TIMELINE
            "expected_onset": "5-7 days for clinical response",
            
            # WARNINGS
            "precautions": [
                "Red man syndrome (antihistamine premedication)",
                "Nephrotoxicity (monitor Cr, ensure hydration)",
                "Ototoxicity (baseline hearing test)",
            ],
        }
    ]
}
```

### Pathogen Database Keys

```python
ANTIBIOTIC_DATABASE = {
    "MRSA":                          # Methicillin-resistant S. aureus
    "VRSA":                          # Vancomycin-resistant S. aureus
    "Pseudomonas aeruginosa":        # Gram-negative aerobe
    "E. coli (ESBL)":                # Extended-spectrum beta-lactamase producer
    "Enterococcus":                  # Gram-positive coccus
    "Acinetobacter baumannii":       # Multidrug-resistant gram-negative
    "Candida":                       # Fungal (for systemic infections)
}
```

### Step-by-Step: Add Daptomycin for MRSA

```python
{
    "rank": 2,
    "drug_name": "Daptomycin IV",
    "category": "Cyclic lipopeptide",
    "initial_dose": "6 mg/kg IV",
    "target_dose": "6-10 mg/kg IV daily",
    "indication": "Skin/soft tissue MRSA, bacteremia (NOT for pneumonia)",
    "suitability_score": 8.5,
    "reasoning": "Good for bloodstream MRSA. Lipophilic = lung penetration poor (inactivated by surfactant). Good for endocarditis.",
    "monitoring": "Renal function, CK levels (myopathy risk), eosinophilia",
    "monitoring_interval": "CK weekly x 4 weeks, then monthly; Cr at baseline and day 3",
    "expected_onset": "2-3 days for clinical improvement",
    "precautions": [
        "Muscle toxicity: elevated CK, myopathy, rhabdomyolysis",
        "CNS effects: confusion, rare seizures",
        "ABSOLUTE CONTRAINDICATION: Do NOT use for pneumonia (inactivated by lung surfactant)",
        "Renal dosing: 4-6 mg/kg Q48H if CrCl <30",
    ],
}
```

---

## 3. Adding to SAFER_ALTERNATIVES

### Structure Template

```python
SAFER_ALTERNATIVES = {
    "original_drug_name": [
        {
            "rank": 1,                              # Alternative priority
            "safer_drug": "Alternative Drug Name",
            "reason": "Why it's safer (2-3 sentences)",
            "suitability_score": 9.0,               # 0.0-10.0  
            "indication": "When to use this alternative",
        }
    ]
}
```

### Step-by-Step: Add Anticoagulant Alternatives to Warfarin

```python
{
    "rank": 1,
    "safer_drug": "Apixaban (Eliquat)",
    "reason": "DOAC with superior renal safety; predictable kinetics; no INR monitoring; lower bleeding risk",
    "suitability_score": 9.5,
    "indication": "Atrial fibrillation with renal impairment, VTE",
},
{
    "rank": 2,
    "safer_drug": "Dabigatran (Pradaxa)",
    "reason": "Another DOAC option; dose-adjusted for renal function (75mg BID if CrCl <30)",
    "suitability_score": 9.0,
    "indication": "Alternative DOAC if Apixaban contraindicated",
},
{
    "rank": 3,
    "safer_drug": "Edoxaban (Savaysa)",
    "reason": "DOAC with ok renal profile (use 30mg daily if CrCl <60)",
    "suitability_score": 8.5,
    "indication": "Alternative if others not tolerated",
}
```

---

## Adding Functions to Drug Recommendations Module

### To add a new generation function:

```python
def generate_[domain]_recommendations(
    primary_parameter: str,
    context_parameters: list = None
) -> list[dict[str, Any]]:
    """
    Generate [domain] recommendations.
    
    Parameters:
    -----------
    primary_parameter : str
        Main categorization (e.g., metabolizer_status, pathogen, drug_name)
    context_parameters : list, optional
        Additional context (conditions, infection site, allergies)
    
    Returns:
    --------
    list[dict[str, Any]]
        Ranked list of recommendations sorted by rank
    """
    context_parameters = context_parameters or []
    recommendations = []
    
    # 1. Get base recommendations from database
    db_entries = RECOMMENDATION_DATABASE.get(primary_parameter, {})
    
    # 2. Filter by context if available
    if context_parameters:
        for context in context_parameters:
            db_entries = db_entries.get(context, []) or list(db_entries.values())[0]
    
    # 3. Sort by rank
    recommendations = sorted(db_entries, key=lambda x: x.get("rank", 999))
    
    logger.info(f"✅ Generated {len(recommendations)} recommendations for {primary_parameter}")
    return recommendations
```

---

## Validation Checklist

When adding a new drug/antibiotic, verify:

```
REQUIRED FIELDS:
□ rank (integer: 1, 2, 3, etc.)
□ drug_name (string with formulation if needed)
□ initial_dose (string with units)
□ target_dose (string with units)
□ indication (string describing use case)
□ [genetic_match_score | suitability_score | rank] (0.0-10.0)
□ monitoring_requirements (string describing what to monitor)

RECOMMENDED FIELDS:
□ category (drug class/type)
□ genetic_reasoning or reasoning (2-3 sentences why)
□ precautions (list of warnings)
□ expected_outcome (estimated efficacy % and timeline)
□ interactions (list of drug interactions)

OPTIONAL BUT HELPFUL:
□ brand_names (list of alternative brand names)
□ onset_time (expected time to feel effect)
□ max_dose (safety ceiling)
□ contraindications (absolute no-use cases)
□ monitoring_interval (how often to check)
```

---

## Testing New Entries

### Unit Test Template

```python
from backend.models.drug_recommendations import (
    generate_genetic_drug_recommendations,
    generate_antibiotic_recommendations,
    generate_safer_alternatives
)

# Test genetic recommendation  
def test_new_genetic_drug():
    drugs = generate_genetic_drug_recommendations(
        metabolizer_status="intermediate_metabolizer",
        detected_genes=["CYP2D6"],
        detected_conditions=["Depression/Mood"]
    )
    assert len(drugs) >= 1
    assert drugs[0]["drug_name"] == "Sertraline (Zoloft)"
    assert drugs[0]["genetic_match_score"] > 0
    print("✅ Genetic recommendation test PASSED")

# Test antibiotic recommendation
def test_new_antibiotic():
    antibiotics = generate_antibiotic_recommendations(
        pathogen="MRSA",
        infection_site="bloodstream",
        severity="serious"
    )
    assert len(antibiotics) >= 1
    assert antibiotics[0]["rank"] == 1
    assert "Vancomycin" in antibiotics[0]["drug_name"]
    print("✅ Antibiotic recommendation test PASSED")

# Run tests
test_new_genetic_drug()
test_new_antibiotic()
```

---

## Common Mistakes to Avoid

```
❌ WRONG - Inconsistent metabolizer name:
"metaboliser_status" or "metabolism_status"

✅ RIGHT:
"poor_metabolizer" | "intermediate_metabolizer" | 
"normal_metabolizer" | "ultra_rapid_metabolizer"

---

❌ WRONG - Score > 10 or decimal without context:
"genetic_match_score": 15
"genetic_match_score": 8.987

✅ RIGHT:
"genetic_match_score": 9.2  # 0.0-10.0 scale only

---

❌ WRONG - Dosing without units:
"initial_dose": "25"

✅ RIGHT:
"initial_dose": "25mg daily"
"initial_dose": "500mg IV Q6H"
"initial_dose": "20 mg/kg IV Q8-12H"

---

❌ WRONG - Empty lists:
"precautions": []
"interactions": []

✅ RIGHT (leave field out if empty):
# Don't include empty "precautions" field
# or use: "precautions": ["None documented"]
```

---

## Summary

**To add a drug recommendation:**

1. Choose correct database (genetic/antibiotic/alternatives)
2. Choose correct key (metabolizer/pathogen/original drug)
3. Fill ALL required fields
4. Score appropriately (0.0-10.0)
5. Include clinical reasoning
6. Add monitoring guidance
7. List precautions and interactions
8. Test with unit test
9. Verify with full report analysis

**Files affected:**
- `backend/models/drug_recommendations.py` (add to database)
- `backend/models/genetic.py` (calls generate_genetic_drug_recommendations)
- `backend/models/resistance.py` (calls generate_antibiotic_recommendations)
- `backend/models/toxicity.py` (calls generate_safer_alternatives)

---

**Version**: 1.0 | **Date**: April 9, 2026 | **Status**: Production Ready
