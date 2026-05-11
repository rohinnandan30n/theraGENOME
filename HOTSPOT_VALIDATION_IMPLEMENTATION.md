# Post-Classification Hotspot Validation Implementation

## Overview

This implementation adds post-classification validation to detect and handle known pathogenic hotspots from ClinVar. If a model predicts a low-confidence benign classification for a known pathogenic hotspot, the result is automatically overridden with flags and explanation added.

## Files Modified/Created

### Created Files
1. **src/api/variant_analysis.py** - Core hotspot validation module
   - `HotspotValidator` class with hotspot database
   - Validation and override logic
   - Support for retrieving hotspot information

### Modified Files
1. **src/api/classification.py** - Integration point for hotspot validation
   - Updated `/classify` endpoint to apply hotspot validation
   - Updated `/batch_classify` endpoint to apply hotspot validation to each variant
   - Added import for `HotspotValidator`

2. **src/api/classification_schemas.py** - Response schema updates
   - Added `flags` field to `ClassificationResponse`
   - Added `explanation` field to `ClassificationResponse`
   - Added `flags` and `explanation` fields to `BatchClassification`

3. **tests/test_classification.py** - Added comprehensive test suite
   - `TestHotspotValidator` class with 10+ test cases
   - `TestHotspotEndpointIntegration` class for integration testing

## Hotspot Database

### Current Hotspots (Minimum Required)
The implementation includes three mandatory hotspots plus alternative notations:

#### 1. TP53 p.R175H (Li-Fraumeni Syndrome)
- **ClinVar ID**: RCV000012312
- **Clinical Significance**: Pathogenic
- **Disease**: Li-Fraumeni syndrome
- **Mechanism**: Loss of DNA binding domain
- **gnomAD AF**: 0.00001
- **Supported Notations**:
  - `p.R175H`
  - `R175H` (without p. prefix)

#### 2. BRCA1 c.5266dupC (Breast/Ovarian Cancer)
- **ClinVar ID**: RCV000008886
- **Clinical Significance**: Pathogenic
- **Disease**: Breast and ovarian cancer
- **Mechanism**: Frameshift - premature termination
- **gnomAD AF**: 0.00002
- **Supported Notations**:
  - `c.5266dupC`
  - `5266dupC` (without c. prefix)

#### 3. KRAS p.G12D (Pancreatic Adenocarcinoma)
- **ClinVar ID**: RCV000015420
- **Clinical Significance**: Pathogenic
- **Disease**: Somatic: Pancreatic adenocarcinoma
- **Mechanism**: Constitutive GTPase activity - oncogenic
- **gnomAD AF**: 0.00005
- **Supported Notations**:
  - `p.G12D`
  - `G12D` (without p. prefix)

## Validation Logic

### Override Conditions
The classification override occurs when ALL of the following are true:

1. **Classification is BENIGN** - Model predicts benign variant
2. **Confidence is LOW** - Confidence score < 0.80 (threshold)
3. **Hotspot is KNOWN** - Gene/mutation combination is in hotspot database
4. **Match occurs** - Gene symbol and mutation notation match hotspot entry

### Override Actions
When all conditions are met:

1. **Classification updated**: Changed from "Benign" to "Pathogenic"
2. **Confidence boosted**: Increased by 0.15 (capped at 0.95)
   ```
   new_confidence = min(0.95, old_confidence + 0.15)
   ```
3. **Flags added**:
   - `"hotspot_override"` - Indicates override occurred
   - `"review_required"` - Signals manual review needed
4. **Explanation added**:
   ```
   "Known ClinVar pathogenic hotspot overrides low-confidence benign prediction. 
    ClinVar ID: {clinvar_id}. Disease: {disease}. Mechanism: {mechanism}"
   ```

### Non-Override Scenarios
- High-confidence benign predictions (confidence ≥ 0.80) are NOT overridden
- Predictions already classified as "Pathogenic" are NOT modified
- Unknown variants (not in hotspot database) are NOT affected
- VUS classifications are NOT overridden

## API Response Format

### Single Classification Response
```json
{
  "variant_id": "17-7571720-G-A",
  "chrom": "17",
  "pos": 7571720,
  "ref": "G",
  "alt": "A",
  "classification": "Pathogenic",
  "confidence": 0.80,
  "probabilities": {
    "benign": 0.20,
    "pathogenic": 0.80
  },
  "model_version": "ensemble_v1-3",
  "clinical_significance": "Pathogenic",
  "feature_importance": {},
  "shape_values": {},
  "flags": ["hotspot_override", "review_required"],
  "explanation": "Known ClinVar pathogenic hotspot overrides low-confidence benign prediction. ClinVar ID: RCV000012312. Disease: Li-Fraumeni syndrome. Mechanism: Loss of DNA binding domain"
}
```

### Batch Classification Response
```json
{
  "total_variants": 2,
  "model_version": "ensemble_v1-3",
  "classifications": [
    {
      "variant_id": "17-7571720-G-A",
      "classification": "Pathogenic",
      "confidence": 0.80,
      "probabilities": {"benign": 0.20, "pathogenic": 0.80},
      "flags": ["hotspot_override", "review_required"],
      "explanation": "Known ClinVar pathogenic hotspot overrides low-confidence benign prediction..."
    },
    {
      "variant_id": "13-32890559-G-A",
      "classification": "Benign",
      "confidence": 0.92,
      "probabilities": {"benign": 0.92, "pathogenic": 0.08}
    }
  ]
}
```

## Usage Examples

### Direct Hotspot Validator Usage
```python
from src.api.variant_analysis import HotspotValidator

# Check a classification result
model_result = {
    'classification': 'Benign',
    'confidence': 0.65,
    'probabilities': {'benign': 0.65, 'pathogenic': 0.35},
    'model_version': 'ensemble_v1-3'
}

validated = HotspotValidator.validate_and_override(
    model_result,
    gene_symbol='TP53',
    mutation_notation='p.R175H'
)

print(validated['classification'])  # 'Pathogenic'
print(validated['flags'])           # ['hotspot_override', 'review_required']
```

### API Endpoint Usage
```bash
# Single classification with hotspot detection
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

# Response will include:
# "classification": "Pathogenic"
# "flags": ["hotspot_override", "review_required"]
```

### Batch Classification with Hotspots
```bash
curl -X POST "http://localhost:8000/api/v1/classification/batch_classify" \
  -H "Content-Type: application/json" \
  -d '{
    "variants": [
      {
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
      }
    ]
  }'
```

## Test Coverage

### Test Suite: TestHotspotValidator
Located in `tests/test_classification.py`

#### Test Cases

1. **test_hotspot_detection_tp53_r175h**
   - Verifies TP53 p.R175H hotspot detection
   - Confirms override when confidence < 0.80
   - Checks flags and explanation

2. **test_hotspot_detection_brca1_frameshift**
   - Verifies BRCA1 c.5266dupC hotspot detection
   - Confirms confidence boost after override

3. **test_hotspot_detection_kras_g12d**
   - Verifies KRAS p.G12D hotspot detection
   - Tests default confidence threshold

4. **test_hotspot_with_high_confidence_benign**
   - Confirms NO override for confidence ≥ 0.80
   - Tests threshold boundary condition

5. **test_hotspot_pathogenic_prediction_not_overridden**
   - Confirms NO modification for pathogenic predictions
   - Tests that hotspots don't override correct predictions

6. **test_unknown_hotspot_no_override**
   - Confirms unknown variants pass through unchanged
   - Tests negative case

7. **test_tp53_r175h_alternative_notation**
   - Tests TP53 hotspot without "p." prefix
   - Confirms flexible notation support

8. **test_hotspot_gets_info**
   - Tests retrieval of hotspot information
   - Verifies metadata available

9. **test_hotspot_list_returns_all**
   - Tests listing all known hotspots
   - Confirms minimum required hotspots present

### Integration Test: TestHotspotEndpointIntegration

1. **test_classification_endpoint_with_tp53_hotspot**
   - End-to-end test of classification endpoint
   - Verifies hotspot override in response

2. **test_review_required_flag_set**
   - Confirms review_required flag always set on override
   - Tests flag consistency

## Running Tests

```bash
# Run all classification tests
pytest tests/test_classification.py -v

# Run only hotspot tests
pytest tests/test_classification.py::TestHotspotValidator -v

# Run specific test
pytest tests/test_classification.py::TestHotspotValidator::test_hotspot_detection_tp53_r175h -v

# Run with coverage
pytest tests/test_classification.py --cov=src.api.variant_analysis -v
```

## Example Test: TP53 Hotspot Detection

```python
def test_hotspot_detection_tp53_r175h():
    """Test detection of TP53 p.R175H hotspot"""
    from src.api.variant_analysis import HotspotValidator
    
    result = {
        'classification': 'Benign',
        'confidence': 0.65,  # Below 0.80 threshold
        'probabilities': {'benign': 0.65, 'pathogenic': 0.35},
        'model_version': 'ensemble_v1-3'
    }
    
    validated = HotspotValidator.validate_and_override(
        result,
        gene_symbol='TP53',
        mutation_notation='p.R175H'
    )
    
    # Assertions
    assert validated['classification'] == 'Pathogenic'  # ✓ Overridden
    assert 'hotspot_override' in validated['flags']    # ✓ Flag added
    assert 'review_required' in validated['flags']      # ✓ Flag added
    assert 'ClinVar' in validated['explanation']        # ✓ Explanation added
```

## Logging

The implementation logs at different levels:

```
INFO: "Successfully loaded model v1 from path"
WARNING: "Hotspot override triggered for TP53:p.R175H. Model predicted BENIGN..."
INFO: "Classification overridden to Pathogenic for TP53:p.R175H"
ERROR: "Failed to retrieve gene/mutation information"
```

## Future Enhancements

1. **Dynamic Hotspot Updates**
   - Load hotspots from external ClinVar database
   - Automatic updates from RefSeq

2. **Additional Hotspots**
   - EGFR L858R (lung cancer)
   - BRAF V600E (melanoma)
   - Other cancer driver mutations

3. **Weighted Overrides**
   - Different confidence thresholds per disease
   - Somatic vs germline distinction

4. **Audit Trail**
   - Track all override events
   - Generate hotspot override reports

5. **Performance Optimization**
   - Cache hotspot lookups
   - Bulk hotspot validation

## Compatibility

- Python 3.8+
- PyTest 7.4.4+
- Pydantic 2.5.3+
- FastAPI 0.109.2+

## Support for Gene/Mutation Notation

The validator supports multiple notation conventions:

### Protein Notation
- `p.R175H` (HGVS standard)
- `R175H` (shorthand)

### cDNA Notation
- `c.5266dupC` (HGVS standard)
- `5266dupC` (shorthand)

All variations are automatically recognized and matched to hotspot entries.
