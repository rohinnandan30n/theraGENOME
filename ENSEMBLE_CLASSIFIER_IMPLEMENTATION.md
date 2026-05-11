# Ensemble Pathogenicity Classifier Implementation

## Overview
The variant classification logic has been replaced with an ensemble-based approach that combines predictions from three pre-trained scikit-learn/XGBoost models using majority voting.

## Architecture

### Files Modified
1. **src/ml/ensemble_classifier.py** (NEW)
   - Core ensemble classifier implementation
   - Loads three serialized models: `pathogenicity_v1.pkl`, `pathogenicity_v2.pkl`, `pathogenicity_v3.pkl`
   - Implements majority voting for label classification
   - Implements mean confidence calculation
   - Provides fallback to rule-based classification if all models fail to load

2. **src/ml/classifier.py** (MODIFIED)
   - Updated `PathogenicityClassifier` to use `EnsemblePathogenicityClassifier`
   - Maintains backward compatibility with existing API response schema
   - Implements feature mapping from old format to ensemble format
   - Preserves SHAP interpretation interface for compatibility

3. **requirements.txt** (MODIFIED)
   - Added `joblib==1.3.2` for model serialization/deserialization
   - Added `xgboost==2.0.3` for XGBoost model support

## Ensemble Classifier Details

### Model Loading
- Loads three pre-trained models at startup using `joblib.load()`
- Includes error handling for missing files with try/except blocks
- Logs warnings for each model that fails to load
- Logs CRITICAL warning if all three models fail to load
- Falls back to rule-based classification only if all models fail

### Feature Input
The ensemble classifier accepts features with the following keys:
- `cadd_score`: CADD pathogenicity score (0-99)
- `sift_score`: SIFT impact prediction (0-1)
- `polyphen2_score`: PolyPhen-2 score (0-1)
- `gnomad_af`: gnomAD allele frequency (0-1)
- `phylop_score`: PhyloP conservation score (-14 to 6)
- `mutation_type`: Type of mutation (e.g., SNP, Deletion, Insertion)

### Feature Mapping
The `PathogenicityClassifier._map_features_to_ensemble()` method maps from the existing API format to the ensemble format:
- `CADD_score` → `cadd_score`
- `SIFT_score` → `sift_score`
- `PolyPhen_score` → `polyphen2_score`
- `gnomAD_freq` → `gnomad_af`
- `phyloP_score` → `phylop_score`
- `variant_type` → `mutation_type`

### Ensemble Prediction Logic

#### Classification (Majority Voting)
1. Each model generates a prediction: 1 (Pathogenic) or 0 (Benign)
2. Predictions are aggregated using majority vote
3. If more than half of the models vote "Pathogenic" (≥ 1.5 for 3 models), classification is "Pathogenic"
4. Otherwise, classification is "Benign"

#### Confidence (Mean of Probabilities)
1. Each model's confidence score is extracted (probability of positive class)
2. Confidence scores are averaged across all models that produced predictions
3. Final confidence = mean(confidences)

### Response Format
The ensemble classifier returns a dictionary with:
```python
{
    "classification": "Pathogenic" | "Benign" | "VUS",
    "confidence": float (0.0-1.0),
    "model_version": "ensemble_v1-3",
    "ensemble_details": {
        "predictions": [list of individual model predictions],
        "confidences": [list of individual model confidences],
        "majority_vote": int (0 or 1),
        "models_used": [list of model versions that were loaded]
    }
}
```

### API Response Compatibility
To maintain compatibility with the existing API response schema, the `PathogenicityClassifier` converts the ensemble result to the expected format:
- Maps `classification` field directly
- Converts `confidence` to `benign` and `pathogenic` probabilities
- Sets `model_version` to "ensemble_v1-3"
- Provides simplified feature importance interpretation

### Fallback Rule-Based Classification
If any step fails (all models can't load, prediction errors), the system falls back to rule-based classification:
- Uses heuristic scoring based on feature values
- CADD score: >30 = +2, >20 = +1
- SIFT score: <0.05 = +2, <0.1 = +1
- PolyPhen2 score: >0.9 = +2, >0.7 = +1
- gnomAD frequency: <0.01 = +1, >0.05 = -1
- Final classification based on accumulated score
- Logs CRITICAL warning when falling back to rule-based method
- Returns `model_version`: "fallback_rule-based"

## Usage Examples

### Direct Ensemble Classifier Usage
```python
from src.ml.ensemble_classifier import EnsemblePathogenicityClassifier

classifier = EnsemblePathogenicityClassifier()

features = {
    'cadd_score': 35.5,
    'sift_score': 0.02,
    'polyphen2_score': 0.95,
    'gnomad_af': 0.0001,
    'phylop_score': 2.5,
    'mutation_type': 'Substitution'
}

result = classifier.classify(features)
# Returns: {"classification": "Pathogenic", "confidence": 0.87, "model_version": "ensemble_v1-3", ...}
```

### Through PathogenicityClassifier (API)
```python
from src.ml.classifier import PathogenicityClassifier

classifier = PathogenicityClassifier()

features = {
    'CADD_score': 35.5,
    'SIFT_score': 0.02,
    'PolyPhen_score': 0.95,
    'gnomAD_freq': 0.0001,
    'phyloP_score': 2.5,
    'variant_type': 'Substitution',
    'chrom': '1',
    'pos': 12345,
    'ref': 'A',
    'alt': 'G',
    'gene_symbol': 'BRCA1',
    'amino_acid_change': 'D123H'
}

result = classifier.classify(features, include_interpretation=True)
```

## Error Handling and Logging

### Logging Levels
- **INFO**: Successful model loading, initialization status, classification results
- **DEBUG**: Model path resolution, individual model predictions
- **WARNING**: Individual model failures, failed interpretations
- **CRITICAL**: All models failed to load, falling back to rule-based method

### Model Loading Validation
- Each model file path is validated before loading
- Missing files are caught and logged with specific error messages
- Paths are automatically resolved (relative to current working directory)
- Alternate filename conventions are checked (e.g., `pathogenicity_vv1.pkl`)

## Performance Considerations

### Model Loading
- Models are loaded once at classifier initialization
- Loading errors are handled gracefully without blocking initialization
- Classifier degrades to rule-based method if needed

### Prediction Performance
- Ensemble predictions are computed in parallel-friendly manner
- Each model prediction is independent
- Voting and averaging are lightweight operations
- No SHAP interpretation overhead when using ensemble (simplified interpretation used)

## Testing Models
The implementation has been tested with the following model files:
- `./models/pathogenicity_v1.pkl`
- `./models/pathogenicity_v2.pkl`
- `./models/pathogenicity_v3.pkl`

The actual model files in the repository are named:
- `./models/pathogenicity_vv1.pkl`
- `./models/pathogenicity_vv2.pkl`
- `./models/pathogenicity_vv3.pkl`

The code handles both naming conventions automatically.

## Dependencies
- **joblib>=1.3.2**: For serialized model loading
- **xgboost>=2.0.3**: For XGBoost model support
- **scikit-learn>=1.4.1**: For scikit-learn model support
- **numpy**: For array operations
- **logging**: Python built-in logging module

## Future Enhancements
- Weighted voting based on model performance metrics
- Dynamic model reloading on file changes
- Additional interpretation methods (LIME, attention-based)
- Model-specific confidence calibration
- Performance metrics tracking per model
