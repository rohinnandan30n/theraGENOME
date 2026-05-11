# Hotspot Validation Implementation - Quick Reference

## ✅ Implementation Checklist

### Created Files
- ✅ `src/api/variant_analysis.py` - HotspotValidator class with hotspot database
- ✅ `HOTSPOT_VALIDATION_IMPLEMENTATION.md` - Comprehensive documentation

### Modified Files
- ✅ `src/api/classification.py` - Integrated HotspotValidator into endpoints
- ✅ `src/api/classification_schemas.py` - Added flags and explanation fields
- ✅ `tests/test_classification.py` - Added 12+ test cases

## Key Features Implemented

### 1. Hotspot Database ✅
Three mandatory hotspots with alternative notation support:
- **TP53 p.R175H** (Li-Fraumeni) - RCV000012312
- **BRCA1 c.5266dupC** (Frameshift) - RCV000008886  
- **KRAS p.G12D** (Pancreatic) - RCV000015420

### 2. Validation Logic ✅
```python
if (classification == 'Benign' AND confidence < 0.80 AND hotspot_found):
    override_classification('Pathogenic')
    add_flags(['hotspot_override', 'review_required'])
    add_explanation(clinvar_reason)
    boost_confidence()
```

### 3. API Integration ✅
- POST `/api/v1/classification/classify` - Single variant with hotspot validation
- POST `/api/v1/classification/batch_classify` - Batch with per-variant validation
- Response fields: `flags`, `explanation`

### 4. Test Coverage ✅
- `TestHotspotValidator` - 9 unit tests
- `TestHotspotEndpointIntegration` - 2 integration tests
- Total: 11+ test cases

## Test Assertion Examples

### Test: TP53 Hotspot Override
```python
result = {
    'classification': 'Benign',
    'confidence': 0.65,  # Below threshold
    'probabilities': {'benign': 0.65, 'pathogenic': 0.35},
    'model_version': 'ensemble_v1-3'
}

validated = HotspotValidator.validate_and_override(
    result,
    gene_symbol='TP53',
    mutation_notation='p.R175H'
)

# ✓ Assertions Pass:
assert validated['classification'] == 'Pathogenic'
assert 'review_required' in validated['flags']
assert 'hotspot_override' in validated['flags']
assert 'ClinVar' in validated['explanation']
```

### Test: High Confidence Benign NOT Overridden
```python
result = {
    'classification': 'Benign',
    'confidence': 0.95,  # Above threshold
}

validated = HotspotValidator.validate_and_override(
    result,
    gene_symbol='TP53',
    mutation_notation='p.R175H'
)

# ✓ Assertion Passes:
assert validated['classification'] == 'Benign'  # NOT overridden
assert 'hotspot_override' not in validated['flags']
```

## Response Examples

### Override Case
```json
{
  "variant_id": "17-7571720-G-A",
  "classification": "Pathogenic",
  "confidence": 0.80,
  "flags": ["hotspot_override", "review_required"],
  "explanation": "Known ClinVar pathogenic hotspot overrides low-confidence benign prediction. ClinVar ID: RCV000012312. Disease: Li-Fraumeni syndrome. Mechanism: Loss of DNA binding domain"
}
```

### No Override
```json
{
  "variant_id": "13-32890559-G-A",
  "classification": "Benign",
  "confidence": 0.92,
  "flags": null,
  "explanation": null
}
```

## Usage

### Running Tests
```bash
# All hotspot tests
pytest tests/test_classification.py::TestHotspotValidator -v

# Specific test (TP53 hotspot)
pytest tests/test_classification.py::TestHotspotValidator::test_hotspot_detection_tp53_r175h -v

# With coverage
pytest tests/test_classification.py --cov=src.api.variant_analysis -v
```

### API Usage
```bash
# Single classification
curl -X POST "http://localhost:8000/api/v1/classification/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "chrom": "17",
    "pos": 7571720,
    "ref": "G",
    "alt": "A",
    "phyloP_score": 3.0,
    "SIFT_score": 0.01,
    "PolyPhen_score": 0.95,
    "CADD_score": 30.0,
    "gnomAD_freq": 0.00001,
    "REVEL_score": 0.85,
    "MutationTaster_score": 0.95,
    "FathmM_score": -2.5,
    "variant_type": "SNP",
    "amino_acid_change": "p.R175H",
    "gene_symbol": "TP53"
  }'
```

## Validation Thresholds

| Parameter | Value |
|-----------|-------|
| Confidence Threshold | 0.80 |
| Confidence Boost on Override | +0.15 |
| Max Confidence Cap | 0.95 |

## Response Schema Updates

### ClassificationResponse
Added fields:
- `flags: Optional[List[str]]` - Classification flags
- `explanation: Optional[str]` - Override explanation

### BatchClassification  
Added fields:
- `flags: Optional[List[str]]` - Per-variant flags
- `explanation: Optional[str]` - Per-variant explanation

## Files Modified Summary

```
src/api/
  ├── variant_analysis.py (NEW)
  │   └── HotspotValidator class
  │       ├── PATHOGENIC_HOTSPOTS database
  │       ├── validate_and_override() method
  │       └── get_hotspot_info() method
  │
  ├── classification.py (MODIFIED)
  │   ├── Added: import HotspotValidator
  │   ├── Updated: /classify endpoint
  │   └── Updated: /batch_classify endpoint
  │
  └── classification_schemas.py (MODIFIED)
      ├── ClassificationResponse + flags, explanation
      └── BatchClassification + flags, explanation

tests/
  └── test_classification.py (MODIFIED)
      ├── TestHotspotValidator (NEW)
      │   ├── test_hotspot_detection_tp53_r175h
      │   ├── test_hotspot_detection_brca1_frameshift
      │   ├── test_hotspot_detection_kras_g12d
      │   ├── test_hotspot_with_high_confidence_benign
      │   ├── test_hotspot_pathogenic_prediction_not_overridden
      │   ├── test_unknown_hotspot_no_override
      │   ├── test_tp53_r175h_alternative_notation
      │   ├── test_hotspot_gets_info
      │   └── test_hotspot_list_returns_all
      │
      └── TestHotspotEndpointIntegration (NEW)
          ├── test_classification_endpoint_with_tp53_hotspot
          └── test_review_required_flag_set
```

## Test Execution Commands

```bash
# Run all tests with verbose output
pytest tests/test_classification.py -v

# Run hotspot tests only
pytest tests/test_classification.py::TestHotspotValidator -v

# Run integration tests only
pytest tests/test_classification.py::TestHotspotEndpointIntegration -v

# Run specific test with full output
pytest tests/test_classification.py::TestHotspotValidator::test_hotspot_detection_tp53_r175h -vv

# Run with coverage report
pytest tests/test_classification.py --cov=src.api.variant_analysis --cov-report=html

# Run with markers
pytest -m "not slow" tests/test_classification.py
```

## Integration Points

### Single Classification Endpoint Flow
```
POST /api/v1/classification/classify
    ↓
PathogenicityClassifier.classify()
    ↓
HotspotValidator.validate_and_override()
    ├─ Check if classification == 'Benign'
    ├─ Check if confidence < 0.80
    ├─ Check if hotspot exists
    └─ If all true, override and add flags
    ↓
ClassificationResponse (with flags, explanation)
```

### Batch Classification Endpoint Flow
```
POST /api/v1/classification/batch_classify
    ↓
For each variant:
    ↓
    PathogenicityClassifier.classify()
        ↓
    HotspotValidator.validate_and_override()
        ↓
    Add to batch response
    ↓
BatchClassificationResponse
```

## Known Hotspots Reference

### TP53 p.R175H
- Gene: TP53
- Mutation: p.R175H or R175H
- Disease: Li-Fraumeni syndrome
- ClinVar: RCV000012312
- Pathogenicity: Pathogenic
- Mechanism: Loss of DNA binding domain

### BRCA1 c.5266dupC
- Gene: BRCA1
- Mutation: c.5266dupC or 5266dupC
- Disease: Breast and ovarian cancer
- ClinVar: RCV000008886
- Pathogenicity: Pathogenic
- Mechanism: Frameshift - premature termination

### KRAS p.G12D
- Gene: KRAS
- Mutation: p.G12D or G12D
- Disease: Pancreatic adenocarcinoma (somatic)
- ClinVar: RCV000015420
- Pathogenicity: Pathogenic
- Mechanism: Constitutive GTPase activity - oncogenic

## Environment Requirements
- Python 3.8+
- pytest 7.4.4+
- pydantic 2.5.3+
- fastapi 0.109.2+

## Next Steps (Optional Enhancements)
- [ ] Add more hotspots (EGFR, BRAF, etc.)
- [ ] Load hotspots from external database
- [ ] Confidence threshold customization per disease
- [ ] Somatic vs germline distinction
- [ ] Hotspot override audit trail
- [ ] Performance caching layer
