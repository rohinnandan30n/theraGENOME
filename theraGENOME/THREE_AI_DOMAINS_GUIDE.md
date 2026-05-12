# 🧬🦠💊 Three AI Domains Integration Guide

## Overview

The TheraGenome chatbot now integrates **three specialized AI systems**:

1. **🧬 Genetic Analysis AI** - Pharmacogenomics & variant analysis
2. **🦠 Antibiotic Resistance AI** - Infection diagnosis & treatment recommendations  
3. **💊 Drug Toxicity AI** - Drug safety, interactions & contraindications

Each domain has its own response templates, specialized formatting, and data handling.

---

## Architecture

```
User Question
      ↓
Intent Detector (identifies: genetic, infection, or drug question)
      ↓
Module Router (routes to correct AI model)
      ↓
Three AI Systems:
  ├─ genetic_analysis_model()        [backend/models/genetic.py]
  ├─ antibiotic_resistance_model()   [backend/models/resistance.py]
  └─ drug_toxicity_model()           [backend/models/toxicity.py]
      ↓
Decision Engine (processes outputs)
      ↓
Frontend Formatter (domain-specific UI rendering)
      ↓
Chat Display (color-coded, domain-specific bubbles)
```

---

## Domain 1: 🧬 Genetic Analysis

### What It Does
- Analyzes patient genetic variants
- Identifies metabolizer status (poor, intermediate, rapid, ultra-rapid)
- Detects gene-drug interactions
- Assesses genetic risk (low, medium, high)

### Backend Integration
**File:** `backend/models/genetic.py`

**Function:** `genetic_analysis_model(context)`

**Input:**
```python
{
    "genetic_data": "...",      # VCF file summary or genetic markers
    "patient_id": "..."          # Patient identifier
}
```

**Output:**
```json
{
    "analysis_id": "uuid",
    "timestamp": "ISO-8601",
    "patient_metabolizer_status": "poor_metabolizer",
    "gene_drug_interactions": [
        {
            "gene": "CYP2D6",
            "drug": "codeine",
            "interaction_type": "reduced_efficacy",
            "severity": "high",
            "recommendation": "avoid_or_adjust_dose"
        }
    ],
    "variants_detected": [
        {
            "gene": "CYP2D6",
            "variant": "*4/*4",
            "effect": "loss_of_function",
            "pathogenicity": "pathogenic",
            "clinical_significance": "Poor metabolizer..."
        }
    ],
    "risk_alleles": ["rs123...", "rs456..."],
    "overall_genetic_risk": "high"
}
```

### Frontend Rendering
**Template:** `formatGeneticResponse()`  
**CSS Class:** `.response-genetic`  
**Icon:** 🧬  
**Color Scheme:** Green (#1a472a)

**Display Shows:**
- ✅ Metabolizer status
- ✅ Overall genetic risk level
- 👨‍⚕️ Doctor mode: Detailed variants and gene-drug interactions
- 👤 Patient mode: Simplified risk assessment

### Sample Questions
```
"Analyze the patient's genetic data"
"What is the patient's metabolizer status?"
"Which drugs interact with the patient's genes?"
"Show genetic variants"
"CYP2D6 analysis"
"Pharmacogenomic assessment"
```

### Expected UI Flow
1. User asks genetic question
2. Frontend detects intent: `input_genetic_data`
3. Router calls `genetic_analysis_model()`
4. Response shown with 🧬 icon, green styling
5. Doctor mode shows variants + interactions
6. Patient mode shows summary only

---

## Domain 2: 🦠 Antibiotic Resistance

### What It Does
- Identifies pathogen from infection data
- Detects antibiotic resistance markers
- Shows susceptibility profile
- Recommends antibiotics & lists ones to avoid

### Backend Integration
**File:** `backend/models/resistance.py`

**Function:** `antibiotic_resistance_model(context)`

**Input:**
```python
{
    "infection_data": "...",     # Culture/sequencing results
    "pathogen": "..."             # Suspected organism
}
```

**Output:**
```json
{
    "analysis_id": "uuid",
    "timestamp": "ISO-8601",
    "pathogen_identified": "Staphylococcus aureus (MRSA)",
    "susceptibility_profile": {
        "vancomycin": "susceptible",
        "linezolid": "susceptible",
        "oxacillin": "resistant",
        "penicillin": "resistant"
    },
    "resistance_markers": [
        {
            "gene": "mecA",
            "mechanism": "target_modification",
            "antibiotic_class": "beta_lactam",
            "confidence": 0.98
        }
    ],
    "recommended_antibiotics": ["vancomycin", "linezolid"],
    "avoid_antibiotics": ["penicillin", "oxacillin", "erythromycin"],
    "overall_resistance_risk": "high"
}
```

### Frontend Rendering
**Template:** `formatInfectionResponse()`  
**CSS Classes:** 
- `.response-infection` (main)
- `.recommended-meds` (green, drug recommendations)
- `.avoid-meds` (red, contraindicated drugs)
- `.resistance-markers` (purple, technical details)

**Icon:** 🦠  
**Color Scheme:** Purple (#4a235a)

**Display Shows:**
- ✅ Pathogen identified
- ✅ Overall resistance risk
- ✅ Recommended antibiotics (green list)
- ❌ Antibiotics to avoid (red list)
- 👨‍⚕️ Doctor mode: Resistance genes and mechanisms
- 👤 Patient mode: Simple do's and don'ts

### Sample Questions
```
"Identify the pathogen"
"What's resistant to antibiotics?"
"Which antibiotics should we use?"
"Antibiotic resistance profile"
"MRSA susceptibility"
"Infection analysis"
"What drugs to avoid for this infection?"
```

### Expected UI Flow
1. User asks infection question
2. Frontend detects intent: `input_infection_data`
3. Router calls `antibiotic_resistance_model()`
4. Response shown with 🦠 icon, purple styling
5. Doctor mode shows resistance markers
6. Patient mode shows clear recommended vs avoid lists

---

## Domain 3: 💊 Drug Toxicity & Safety

### What It Does
- Screens drug for safety
- Identifies toxicity flags by organ system
- Detects drug-drug interactions
- Shows contraindications
- Calculates therapeutic index

### Backend Integration
**File:** `backend/models/toxicity.py`

**Function:** `drug_toxicity_model(drug_name, context)`

**Input:**
```python
drug_name = "amoxicillin",
context = {
    "co_medications": [...],
    "organ_function": {...},
    "allergies": [...]
}
```

**Output:**
```json
{
    "analysis_id": "uuid",
    "timestamp": "ISO-8601",
    "drug_name": "amoxicillin",
    "overall_toxicity_risk": "medium",
    "toxicity_flags": [
        {
            "organ_system": "hepatic",
            "severity": "moderate",
            "description": "Elevated ALT/AST risk with prolonged use",
            "reversible": true
        }
    ],
    "drug_interactions": [
        {
            "drug_a": "amoxicillin",
            "drug_b": "methotrexate",
            "interaction_type": "synergistic_toxicity",
            "severity": "high",
            "recommendation": "avoid_combination"
        }
    ],
    "max_safe_dose": {
        "adult": "500mg every 8 hours",
        "pediatric": "...dosing"
    },
    "contraindications": [
        "Penicillin allergy",
        "Severe renal impairment"
    ],
    "therapeutic_index": 2.5
}
```

### Frontend Rendering
**Template:** `formatDrugResponse()`  
**CSS Classes:**
- `.response-drug-safety` (main)
- `.contraindications` (red, critical warnings)
- `.toxicity-details` (orange, organ-specific)
- `.drug-interactions` (blue, interaction warnings)

**Icon:** 💊  
**Color Scheme:** Red/Orange (danger-focused)

**Risk Colors:**
- 🟢 **Low Risk**: Green (`risk-low`)
- 🟡 **Medium Risk**: Orange (`risk-medium`)
- 🔴 **High Risk**: Red (`risk-high`)

**Display Shows:**
- ✅ Drug name
- ✅ Overall toxicity risk (color-coded)
- ❌ Contraindications (critical)
- ⚠️ Toxicity flags by organ system
- 👨‍⚕️ Doctor mode: Detailed toxicity + interactions + therapeutic index
- 👤 Patient mode: Simple safety warning

### Sample Questions
```
"Is amoxicillin safe?"
"Check drug toxicity"
"What are the side effects?"
"Drug interactions with methotrexate"
"Is this drug safe for renal patients?"
"Toxicity screening"
"Contraindications for penicillin allergy"
"Safe dose for this drug"
```

### Expected UI Flow
1. User asks drug question
2. Frontend detects intent: `drug_analysis`
3. Router calls `drug_toxicity_model()`
4. Response shown with 💊 icon, red/orange styling
5. Risk level color-coded (low=green, medium=orange, high=red)
6. Doctor mode shows organ toxicity + interactions
7. Patient mode shows clear safety warnings

---

## Intent Detection Keywords

The backend identifies domain automatically through keywords:

### Genetic Intent Keywords
```
genetic data, genome, genomic, dna, vcf, variant, 
cyp2d6, cyp2c19, metabolizer, pharmacogenomic
```

### Infection Intent Keywords
```
infection, pathogen, antibiotic, resistance, amr,
mrsa, susceptibility, culture, organism, bacterial
```

### Drug Intent Keywords
```
drug, medicine, medication, safety, toxicity, dose,
contraindication, allergy, interaction, side effect
```

---

## Response Flow: Complete Example

### User asks: "Is amoxicillin safe for a patient with penicillin allergy?"

**Step 1: Intent Detection**
```python
intent = detect("Is amoxicillin safe for a patient with penicillin allergy?")
# Returns: Intent.DRUG_ANALYSIS
# Confidence: 0.95
# Keywords: ["drug", "safe", "allergy"]
```

**Step 2: Module Routing**
```python
result = router.route(Intent.DRUG_ANALYSIS, context={
    "drug": "amoxicillin",
    "allergies": ["penicillin"]
})
# Calls: drug_toxicity_model()
# Also calls: genetic_analysis_model() if genetic data available
```

**Step 3: AI Model Processing**
```python
tox = drug_toxicity_model(
    drug_name="amoxicillin",
    context={"allergies": ["penicillin"]}
)
# Returns: ToxicityAnalysisResult with:
# - contraindications: ["Penicillin allergy"]
# - overall_toxicity_risk: "high"
# - toxicity_flags: [...]
# - drug_interactions: [...]
```

**Step 4: Decision Engine**
```python
decision = decision_engine.process(
    route_result=result,
    mode="doctor"
)
# Returns: response envelope with:
# - intent: "drug_analysis"
# - template: "DRUG_NOT_RECOMMENDED"
# - variables: {...}
# - explanation: {...}
```

**Step 5: Frontend Rendering**
```javascript
// Controller calls:
buildResponseHTML(
    template="DRUG_NOT_RECOMMENDED",
    variables={drug_name: "amoxicillin", ...},
    explanation={...},
    intent="drug_analysis",
    mode="doctor"
)

// Detects intent  "drug_analysis" and calls:
formatDrugResponse(variables, explanation, mode)

// Returns HTML with:
// - 💊 icon
// - Red styling (contraindicated)
// - Contraindication: "Penicillin allergy"
// - Toxicity details (doctor mode)
// - Risk level: HIGH
```

**Step 6: Frontend Display**
User sees:
```
[DRUG_NOT_RECOMMENDED] [drug_analysis]
💊
Amoxicillin
Toxicity Risk: HIGH (red)

⚠️ Contraindications:
  • Penicillin allergy

Toxicity Flags (doctor mode):
  • hepatic (moderate): Elevated ALT/AST risk with prolonged use
  • renal (mild): Mild creatinine elevation possible in CKD

Drug Interactions (doctor mode):
  • Amoxicillin + Methotrexate: avoid_combination
```

---

## CSS Color Scheme

| Domain | Icon | Color | Hex | CSS Class |
|--------|------|-------|-----|-----------|
| **Genetic** | 🧬 | Green | #1a472a | `.response-genetic` |
| **Infection** | 🦠 | Purple | #4a235a | `.response-infection` |
| **Drug Safety** | 💊 | Red/Orange | #6f2c3d | `.response-drug-safety` |
| **Low Risk** | 🟢 | Green | #2d6a3e | `.risk-low` |
| **Medium Risk** | 🟡 | Orange | #f57c00 | `.risk-medium` |
| **High Risk** | 🔴 | Red | #d32f2f | `.risk-high` |

---

## Testing Checklist

### Genetic Domain Tests
- [ ] Question about genetic variants triggers genetic format
- [ ] Doctor mode shows: metabolizer status, variants, gene-drug interactions
- [ ] Patient mode shows: metabolizer status only
- [ ] 🧬 icon displays correctly
- [ ] Green styling applied

### Infection Domain Tests
- [ ] Question about infection triggers infection format
- [ ] Shows: pathogen, resistance risk, recommended antibiotics
- [ ] Green list: recommended antibiotics
- [ ] Red list: antibiotics to avoid
- [ ] Doctor mode shows: resistance markers with confidence scores
- [ ] 🦠 icon displays correctly
- [ ] Purple styling applied

### Drug Safety Domain Tests
- [ ] Question about drug safety triggers drug format
- [ ] Shows: drug name, toxicity risk, contraindications
- [ ] Risk level color-coded (low=green, medium=orange, high=red)
- [ ] Red contraindications clearly marked
- [ ] Doctor mode shows: toxicity by organ, interactions, therapeutic index
- [ ] Patient mode shows: simple warning only
- [ ] 💊 icon displays correctly
- [ ] Red/orange styling applied

### Cross-Domain Tests
- [ ] Mode switching works between doctor and patient
- [ ] History preserves domain formatting
- [ ] No CSS conflicts between domains
- [ ] Mobile responsive for all domains
- [ ] Error handling works for all intents

---

## Browser Console Debug

Open browser console (F12 → Console) and look for:

```javascript
// Should see one of these depending on intent:
console.log('Intent detected: input_genetic_data');
console.log('Intent detected: input_infection_data');  
console.log('Intent detected: drug_analysis');

// Should see formatting call:
console.log('Formatting as genetic response');
console.log('Formatting as infection response');
console.log('Formatting as drug response');

// Should see backend response with model outputs:
console.log('Chatbot response:', response);
// response.outputs should contain:
//   - genetic_analysis
//   - resistance_analysis
//   - toxicity_analysis
```

---

## Production Notes

### Model Integration Points
When replacing mock models with real AI/ML systems:

1. **Genetic Analysis** (`backend/models/genetic.py`)
   - Replace with: Real bioinformatics pipeline
   - Maintain same output schema (GeneticAnalysisResult)
   - Return same fields: metabolizer_status, variants, risk

2. **Antibiotic Resistance** (`backend/models/resistance.py`)
   - Replace with: ResFinder, CARD-RGI, or similar AMR pipeline
   - Maintain same output schema (ResistanceAnalysisResult)
   - Return same fields: pathogen, susceptibility, resistance_markers

3. **Drug Toxicity** (`backend/models/toxicity.py`)
   - Replace with: QSAR model or FAERS/SIDER database query
   - Maintain same output schema (ToxicityAnalysisResult)
   - Return same fields: toxicity_risk, flags, interactions, contraindications

### Frontend Compatibility
- No frontend changes needed when models are upgraded
- Frontend respects the same schema contracts
- Domain-specific formatting handles all model outputs
- Doctor/patient mode filtering works automatically

---

## Next Steps

1. ✅ Frontend domain-specific formatting implemented
2. ✅ CSS styling for all three domains added
3. ✅ Intent detection routing configured
4. Next: Test all three domains end-to-end
5. Next: Verify doctor/patient mode filtering
6. Next: Deploy to production with real AI models

---

## Files Modified

- `frontend/assets/js/chatbot-controller.js` - Added domain formatters
- `frontend/assets/css/chatbot-styles.css` - Added domain styling
- No backend changes needed (already integrated!)

## Files Referenced (Not Modified)

- `backend/models/genetic.py` - Genetic analysis model
- `backend/models/resistance.py` - Antibiotic resistance model
- `backend/models/toxicity.py` - Drug toxicity model
- `backend/chatbot/router.py` - Module routing logic
- `backend/chatbot/intent_detector.py` - Intent detection
- `backend/chatbot/controller.py` - Main orchestrator

---

**Status:** ✅ Frontend optimized for three AI domains  
**Last Updated:** April 8, 2026  
**Version:** 2.0 - Domain Integration Complete
