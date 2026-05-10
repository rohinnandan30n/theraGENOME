#!/usr/bin/env python3
"""
AUROC (Area Under ROC Curve) Evaluation
Calculate and analyze model performance metrics
"""

import sys
import numpy as np
from sklearn.metrics import roc_curve, auc, roc_auc_score, confusion_matrix, classification_report
from src.ml.model_manager import ModelRegistry
from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.classifier import PathogenicityClassifier

print("\n" + "="*80)
print("  MODEL AUROC (AREA UNDER ROC CURVE) ANALYSIS")
print("="*80 + "\n")

# Create diverse test set with labels
test_cases = [
    # Pathogenic cases (label=1)
    {
        'features': {
            'phyloP_score': 5.5,
            'SIFT_score': 0.01,
            'PolyPhen_score': 0.98,
            'CADD_score': 32.0,
            'gnomAD_freq': 0.00001,
            'REVEL_score': 0.85,
            'MutationTaster_score': 0.95,
            'FathmM_score': 0.92,
            'variant_type': 'Substitution',
            'amino_acid_change': 'R175H'
        },
        'label': 1,
        'name': 'TP53 R175H (Pathogenic)'
    },
    {
        'features': {
            'phyloP_score': 4.2,
            'SIFT_score': 0.0,
            'PolyPhen_score': 1.0,
            'CADD_score': 35.0,
            'gnomAD_freq': 0.000001,
            'REVEL_score': 0.95,
            'MutationTaster_score': 1.0,
            'FathmM_score': 1.0,
            'variant_type': 'Deletion',
            'amino_acid_change': 'FS'
        },
        'label': 1,
        'name': 'BRCA1 Frameshift (Pathogenic)'
    },
    {
        'features': {
            'phyloP_score': 6.0,
            'SIFT_score': 0.02,
            'PolyPhen_score': 0.99,
            'CADD_score': 28.0,
            'gnomAD_freq': 0.00001,
            'REVEL_score': 0.88,
            'MutationTaster_score': 0.92,
            'FathmM_score': 0.90,
            'variant_type': 'Substitution',
            'amino_acid_change': 'G123A'
        },
        'label': 1,
        'name': 'Highly Conserved (Pathogenic)'
    },
    {
        'features': {
            'phyloP_score': 5.0,
            'SIFT_score': 0.05,
            'PolyPhen_score': 0.92,
            'CADD_score': 25.0,
            'gnomAD_freq': 0.00005,
            'REVEL_score': 0.80,
            'MutationTaster_score': 0.85,
            'FathmM_score': 0.88,
            'variant_type': 'Substitution',
            'amino_acid_change': 'D100H'
        },
        'label': 1,
        'name': 'Damaging Missense (Pathogenic)'
    },
    # Benign cases (label=0)
    {
        'features': {
            'phyloP_score': -3.5,
            'SIFT_score': 0.95,
            'PolyPhen_score': 0.05,
            'CADD_score': 8.0,
            'gnomAD_freq': 0.02,
            'REVEL_score': 0.15,
            'MutationTaster_score': 0.1,
            'FathmM_score': 0.12,
            'variant_type': 'SNP',
            'amino_acid_change': 'L50M'
        },
        'label': 0,
        'name': 'Common Variant (Benign)'
    },
    {
        'features': {
            'phyloP_score': -2.0,
            'SIFT_score': 1.0,
            'PolyPhen_score': 0.01,
            'CADD_score': 5.0,
            'gnomAD_freq': 0.05,
            'REVEL_score': 0.1,
            'MutationTaster_score': 0.05,
            'FathmM_score': 0.08,
            'variant_type': 'SNP',
            'amino_acid_change': 'S100S'
        },
        'label': 0,
        'name': 'Silent Mutation (Benign)'
    },
    {
        'features': {
            'phyloP_score': -4.0,
            'SIFT_score': 0.98,
            'PolyPhen_score': 0.02,
            'CADD_score': 6.0,
            'gnomAD_freq': 0.03,
            'REVEL_score': 0.12,
            'MutationTaster_score': 0.08,
            'FathmM_score': 0.10,
            'variant_type': 'SNP',
            'amino_acid_change': 'V200V'
        },
        'label': 0,
        'name': 'Tolerated Variant (Benign)'
    },
    {
        'features': {
            'phyloP_score': -1.5,
            'SIFT_score': 0.92,
            'PolyPhen_score': 0.08,
            'CADD_score': 10.0,
            'gnomAD_freq': 0.01,
            'REVEL_score': 0.20,
            'MutationTaster_score': 0.15,
            'FathmM_score': 0.18,
            'variant_type': 'SNP',
            'amino_acid_change': 'A75T'
        },
        'label': 0,
        'name': 'Likely Tolerated (Benign)'
    },
]

# Prepare data
preprocessor = FeaturePreprocessor()
registry = ModelRegistry('./models')

X_test = []
y_test = []

for test_case in test_cases:
    try:
        vector = preprocessor.preprocess(test_case['features'])
        X_test.append(vector)
        y_test.append(test_case['label'])
    except Exception as e:
        print(f"Warning: Could not preprocess {test_case['name']}: {e}")

X_test = np.array(X_test)
y_test = np.array(y_test)

print(f"Test Set: {len(y_test)} samples ({np.sum(y_test)} pathogenic, {len(y_test)-np.sum(y_test)} benign)\n")

# Evaluate each model version
auroc_results = {}

for version in ['v1', 'v2', 'v3']:
    print(f"\n{'='*80}")
    print(f"  MODEL VERSION: pathogenicity:v{version}")
    print(f"{'='*80}\n")
    
    try:
        # Load model
        model = registry.load_model('pathogenicity', version)
        
        # Get probability predictions
        y_proba = model.predict_proba(X_test)[:, 1]  # Probability of pathogenic class
        y_pred = model.predict(X_test)
        
        # Calculate AUROC
        auroc = roc_auc_score(y_test, y_proba)
        
        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_test, y_proba)
        
        # Calculate confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        # Calculate metrics
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0  # Precision
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0  # Negative Predictive Value
        
        print(f"AUROC: {auroc:.4f}")
        print(f"\nConfusion Matrix:")
        print(f"  True Negatives:  {tn}")
        print(f"  False Positives: {fp}")
        print(f"  False Negatives: {fn}")
        print(f"  True Positives:  {tp}")
        
        print(f"\nPerformance Metrics:")
        print(f"  Sensitivity (True Positive Rate): {sensitivity:.4f} ({tp}/{tp+fn})")
        print(f"  Specificity (True Negative Rate): {specificity:.4f} ({tn}/{tn+fp})")
        print(f"  Positive Predictive Value (PPV):  {ppv:.4f}")
        print(f"  Negative Predictive Value (NPV):  {npv:.4f}")
        
        print(f"\nROC Curve Points:")
        print(f"  FPR range: {fpr.min():.4f} - {fpr.max():.4f}")
        print(f"  TPR range: {tpr.min():.4f} - {tpr.max():.4f}")
        
        print(f"\nPrediction Details:")
        print(f"  Accuracy: {np.mean(y_pred == y_test):.4f}")
        print(f"  Mean probability (pathogenic): {y_proba.mean():.4f}")
        print(f"  Std probability (pathogenic): {y_proba.std():.4f}")
        
        auroc_results[version] = {
            'auroc': auroc,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'ppv': ppv,
            'npv': npv,
            'fpr': fpr,
            'tpr': tpr,
            'y_proba': y_proba
        }
        
    except Exception as e:
        print(f"❌ ERROR analyzing model v{version}: {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n\n" + "="*80)
print("  AUROC SUMMARY TABLE")
print("="*80 + "\n")

print("Version | AUROC  | Sensitivity | Specificity | PPV    | NPV")
print("-"*65)
for version in ['v1', 'v2', 'v3']:
    if version in auroc_results:
        r = auroc_results[version]
        print(f"  v{version}   | {r['auroc']:.4f} | {r['sensitivity']:11.4f} | {r['specificity']:11.4f} | {r['ppv']:.4f} | {r['npv']:.4f}")

# Interpretation
print("\n" + "="*80)
print("  AUROC INTERPRETATION")
print("="*80 + "\n")

print("""
AUROC Ranges:
- 0.90-1.00: Excellent discrimination
- 0.80-0.90: Good discrimination  
- 0.70-0.80: Fair discrimination
- 0.60-0.70: Poor discrimination
- 0.50-0.60: Very poor discrimination
- 0.50: No discrimination (random)

METRIC DEFINITIONS:
- Sensitivity (TPR): Correctly identified pathogenic (true positive rate)
- Specificity (TNR): Correctly identified benign (true negative rate)
- PPV: When model predicts pathogenic, probability it's correct
- NPV: When model predicts benign, probability it's correct
- AUROC: Overall ability to discriminate between classes

CLINICAL SIGNIFICANCE:
- PPV >95%: Safe for clinical use (low false positive)
- NPV >95%: Reliable negative results
- Sensitivity >90%: Few missed pathogenic variants
- Specificity >90%: Few false pathogenic calls
""")

print("="*80 + "\n")
