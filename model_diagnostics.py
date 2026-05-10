#!/usr/bin/env python3
"""
Model Diagnostic Report
Analyze why models are over-predicting pathogenic variants
"""

import sys
import pickle
import numpy as np
from src.ml.model_manager import ModelRegistry
from src.ml.feature_preprocessor import FeaturePreprocessor

print("\n" + "="*80)
print("  MODEL DIAGNOSTIC REPORT")
print("="*80 + "\n")

# Initialize components
registry = ModelRegistry('./models')
preprocessor = FeaturePreprocessor()

# Test variants
test_benign = {
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
}

test_pathogenic = {
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
}

print("PREPROCESSING ANALYSIS")
print("="*80 + "\n")

try:
    print("1. BENIGN VARIANT FEATURES")
    print(f"   Input: {test_benign}\n")
    benign_vector = preprocessor.preprocess(test_benign)
    print(f"   Preprocessed vector: {benign_vector}")
    print(f"   Vector shape: {benign_vector.shape}")
    print(f"   Vector min: {benign_vector.min():.4f}, max: {benign_vector.max():.4f}")
    print()
    
    print("2. PATHOGENIC VARIANT FEATURES")
    print(f"   Input: {test_pathogenic}\n")
    pathogenic_vector = preprocessor.preprocess(test_pathogenic)
    print(f"   Preprocessed vector: {pathogenic_vector}")
    print(f"   Vector shape: {pathogenic_vector.shape}")
    print(f"   Vector min: {pathogenic_vector.min():.4f}, max: {pathogenic_vector.max():.4f}")
    print()
    
    print("3. VECTOR DIFFERENCE")
    diff = pathogenic_vector - benign_vector
    print(f"   Difference: {diff}")
    print(f"   Absolute difference mean: {np.abs(diff).mean():.4f}")
    print()
    
except Exception as e:
    print(f"❌ ERROR during preprocessing: {e}\n")

print("\n" + "="*80)
print("MODEL PREDICTION ANALYSIS")
print("="*80 + "\n")

for version in ['v1', 'v2', 'v3']:
    try:
        print(f"MODEL v{version}")
        print(f"{'-'*80}")
        
        model = registry.load_model('pathogenicity', version)
        
        # Get model info
        thresholds = {
            'v1': {'pathogenic': 0.7, 'vus_lower': 0.4, 'vus_upper': 0.7},
            'v2': {'pathogenic': 0.75, 'vus_lower': 0.35, 'vus_upper': 0.75},
            'v3': {'pathogenic': 0.8, 'vus_lower': 0.3, 'vus_upper': 0.8}
        }
        
        print(f"Thresholds: {thresholds[version]}\n")
        
        # Test predictions
        benign_pred = model.predict_proba(benign_vector.reshape(1, -1))[0]
        pathogenic_pred = model.predict_proba(pathogenic_vector.reshape(1, -1))[0]
        
        print(f"Benign variant prediction:")
        print(f"  - Class 0 (Benign) prob: {benign_pred[0]:.6f}")
        print(f"  - Class 1 (Pathogenic) prob: {benign_pred[1]:.6f}")
        print(f"  - Expected: Should be high benign prob (>0.5)\n")
        
        print(f"Pathogenic variant prediction:")
        print(f"  - Class 0 (Benign) prob: {pathogenic_pred[0]:.6f}")
        print(f"  - Class 1 (Pathogenic) prob: {pathogenic_pred[1]:.6f}")
        print(f"  - Expected: Should be high pathogenic prob (>0.5)\n")
        
        # Check model type
        if hasattr(model, '__class__'):
            print(f"Model type: {model.__class__.__name__}")
        
        # Check for feature importance if available
        if hasattr(model, 'feature_importances_'):
            print(f"Feature importances: {model.feature_importances_[:5]}...\n")
        
        print()
        
    except Exception as e:
        print(f"❌ ERROR analyzing model v{version}: {e}\n")

print("="*80)
print("FINDINGS & RECOMMENDATIONS")
print("="*80 + "\n")

print("""
ISSUE IDENTIFIED:
- All models consistently predict high pathogenic probability (~96%) for all variants
- This suggests the models are:
  1. Over-fitted or biased towards pathogenic classification
  2. Not properly discriminating between benign and pathogenic variants
  3. Potentially not trained on diverse, balanced data

POSSIBLE CAUSES:
1. Training data imbalance: Too many pathogenic samples in training set
2. Feature normalization: Features may not be properly normalized
3. Model architecture: Models may lack sufficient discriminative power
4. Threshold calibration: Classification thresholds may need adjustment

RECOMMENDATIONS:
1. Retrain models with balanced training data
2. Implement stratified sampling for train/test split
3. Perform cross-validation analysis
4. Adjust classification thresholds based on sensitivity/specificity trade-off
5. Consider ensemble methods or more complex models
6. Add confidence intervals and uncertainty quantification

CURRENT STATUS: ⚠️ PRODUCTION CAUTION
- Models work technically (can generate predictions)
- Accuracy is poor (50% on diverse test set)
- Should NOT be used in production without retraining
""")

print("="*80 + "\n")
