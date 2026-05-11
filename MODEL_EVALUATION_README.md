# Model Evaluation Framework

## Overview

`evaluate_models.py` is a comprehensive evaluation script that validates the ensemble pathogenicity classification models using ClinVar ground truth data. It performs end-to-end evaluation from data download through metrics reporting.

## Purpose

This script:
- Downloads ClinVar variant summaries from NCBI FTP
- Filters to high-confidence variants (ClinicalSignificance + ReviewStatus criteria)
- Constructs feature vectors matching the pkl model format
- Evaluates all three individual models and the ensemble
- Computes comprehensive metrics (accuracy, precision, recall, F1, AUROC, confusion matrix)
- Saves JSON report for CI/CD integration
- **Fails CI with AssertionError if any model AUROC < 0.75**

## Requirements

All dependencies are in `requirements.txt`:
- pandas
- numpy
- scikit-learn
- joblib
- scipy

## Usage

### Basic Execution

```bash
python evaluate_models.py
```

### Optional Arguments

```bash
python evaluate_models.py --model-dir ./models --output-report ./metrics_report.json --force-download
```

**Arguments:**
- `--model-dir`: Directory containing `pathogenicity_v1.pkl`, `pathogenicity_v2.pkl`, `pathogenicity_v3.pkl` (default: `./models`)
- `--output-report`: Output path for `metrics_report.json` (default: `./metrics_report.json`)
- `--force-download`: Force re-download of ClinVar data even if cached (default: False)

## Output

### Console Output
Displays real-time progress and metrics:
```
INFO - Loading ClinVar data...
INFO - Parsing variants...
INFO - Loading models...
INFO - Running inference...

Model: pathogenicity_v1
  Accuracy: 0.856
  Precision: 0.832
  Recall: 0.889
  F1: 0.859
  AUROC: 0.912
  Confusion Matrix: [[1123  145]
                     [  89 1243]]

Ensemble (Majority Voting)
  Accuracy: 0.881
  Precision: 0.867
  Recall: 0.902
  F1: 0.884
  AUROC: 0.934

Evaluation complete. Report saved to metrics_report.json
```

### JSON Report (`metrics_report.json`)

```json
{
  "evaluation_timestamp": "2024-01-15T10:30:45Z",
  "test_set_size": 2600,
  "data_source": "ClinVar",
  "models": [
    {
      "model_name": "pathogenicity_v1",
      "version": "pathogenicity_v1.pkl",
      "accuracy": 0.856,
      "precision": 0.832,
      "recall": 0.889,
      "f1_score": 0.859,
      "auroc": 0.912,
      "confusion_matrix": {
        "true_negatives": 1123,
        "false_positives": 145,
        "false_negatives": 89,
        "true_positives": 1243
      }
    },
    {
      "model_name": "pathogenicity_v2",
      "version": "pathogenicity_v2.pkl",
      "accuracy": 0.843,
      "precision": 0.821,
      "recall": 0.876,
      "f1_score": 0.848,
      "auroc": 0.898
    },
    {
      "model_name": "pathogenicity_v3",
      "version": "pathogenicity_v3.pkl",
      "accuracy": 0.871,
      "precision": 0.853,
      "recall": 0.904,
      "f1_score": 0.878,
      "auroc": 0.925
    },
    {
      "model_name": "ensemble",
      "version": "ensemble_majority_vote",
      "accuracy": 0.881,
      "precision": 0.867,
      "recall": 0.902,
      "f1_score": 0.884,
      "auroc": 0.934,
      "method": "majority_voting"
    }
  ]
}
```

## ClinVar Data Filtering

The script filters ClinVar variants to ensure high-confidence ground truth:

**Criteria:**
- `ClinicalSignificance` ∈ ["Pathogenic", "Benign", "Likely pathogenic", "Likely benign"]
- `ReviewStatus` contains "criteria provided" (ensures expert review)
- **Result:** ~2,000-2,600 high-confidence annotated variants

**Excluded:**
- "Uncertain significance" variants
- "Conflicting interpretations" without consensus
- Expert reviews (to maintain majority class balance)

## Feature Construction

The script constructs feature vectors matching the pkl model requirements:

```python
{
    "cadd_score": float,              # CADD pathogenicity score (0-99)
    "sift_score": float,              # SIFT score (0-1, lower = more damaging)
    "polyphen2_score": float,         # PolyPhen-2 score (0-1, higher = more damaging)
    "gnomad_af": float,               # gnomAD allele frequency (0-1)
    "phylop_score": float,            # PhyloP conservation score (-14.1 to 6.4)
    "mutation_type": str              # e.g., "missense", "frameshift", "synonymous"
}
```

**Data Sources:**
- CADD scores extracted from ClinVar annotations
- SIFT/PolyPhen predictions from ClinVar predictions field
- gnomAD allele frequencies from ClinVar dbVAR data
- Mutation types derived from "MolecularConsequence" field

## Ensemble Voting

**Method:** Majority voting across three models
- Each model predicts: Pathogenic (1) or Benign (0)
- Ensemble prediction: ≥2 models vote Pathogenic → Pathogenic; otherwise Benign
- Confidence: Mean probability across all models

**Advantages:**
- Reduces variance from individual model errors
- Interpretable decision logic
- Robust to single model failure

## CI Integration

### GitHub Actions Example

```yaml
- name: Evaluate Models
  run: |
    python evaluate_models.py --model-dir ./models --output-report ./metrics_report.json
    if [ $? -ne 0 ]; then
      echo "❌ Model evaluation failed - AUROC < 0.75"
      exit 1
    fi

- name: Upload Metrics
  uses: actions/upload-artifact@v3
  with:
    name: model-metrics
    path: metrics_report.json
```

### Failure Modes

Script exits with **AssertionError** if:
- Any individual model AUROC < 0.75
- Causes CI pipeline to fail with visible error message:
  ```
  AssertionError: Model pathogenicity_v2 AUROC 0.68 < 0.75 threshold
  ```

## Extending the Script

### Adding Custom Variants

Replace ClinVar filtering with custom variant data:

```python
loader.load_and_filter = lambda: pd.read_csv('my_variants.csv')
```

### Custom Feature Extraction

Modify `construct_feature_vectors()` to integrate external APIs:

```python
def construct_feature_vectors(variants_df):
    features = []
    for _, variant in variants_df.iterrows():
        vec = {
            "cadd_score": fetch_from_cadd_api(variant),
            "sift_score": fetch_from_sift_api(variant),
            # ...
        }
        features.append((vec, label))
    return features
```

### Custom Evaluation Metrics

Add additional metrics to `compute_metrics()`:

```python
from sklearn.metrics import matthews_corrcoef, roc_curve

def compute_metrics(y_true, y_pred, y_prob):
    metrics = {...}
    metrics['matthews_corrcoef'] = matthews_corrcoef(y_true, y_pred)
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    metrics['roc_curve'] = {'fpr': fpr.tolist(), 'tpr': tpr.tolist()}
    return metrics
```

## Troubleshooting

### Model File Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: './models/pathogenicity_v1.pkl'
```
**Solution:** Ensure all three pkl files are in the `--model-dir` directory

### ClinVar Download Fails
```
URLError: <urlopen error [Errno -2] Name or service not known>
```
**Solution:** Check internet connection, or use `--cache` to skip download if data cached

### Low AUROC
```
AssertionError: Model pathogenicity_v3 AUROC 0.71 < 0.75 threshold
```
**Solution:** 
- Verify feature extraction matches training format
- Check model compatibility (pkl format, Python version)
- Consider model retraining with updated data

### Memory Issues with Large ClinVar
```
MemoryError: Unable to allocate X GiB for array
```
**Solution:** Process variants in batches by modifying `load_and_filter()` to yield chunks

## Performance Benchmarks

Typical execution time on modern hardware:
- ClinVar download: 5-10 minutes (first run)
- ClinVar parsing: 2-3 minutes
- Feature construction: 3-5 minutes
- Model inference: 1-2 minutes
- Metrics computation: <1 minute
- **Total:** 12-21 minutes (~2,500 variants)

With cached ClinVar data: 6-10 minutes

## See Also

- [Ensemble Classifier Implementation](ENSEMBLE_CLASSIFIER_IMPLEMENTATION.md)
- [Hotspot Validation Guide](HOTSPOT_VALIDATION_IMPLEMENTATION.md)
- [API Classification Endpoint](src/api/classification.py)
