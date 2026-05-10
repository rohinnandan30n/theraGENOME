#!/usr/bin/env python3
"""Test if scaler is actually being applied during classification"""

import logging
import numpy as np
from src.ml.classifier import PathogenicityClassifier
from src.ml.feature_preprocessor import FeaturePreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("SCALER APPLICATION TEST")
print("="*80 + "\n")

classifier = PathogenicityClassifier(default_version='v1')
preprocessor = FeaturePreprocessor()

# Test variant
test_features = {
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

# Step 1: Preprocess features
feature_vector_raw = preprocessor.preprocess(test_features)
print(f"1. Raw preprocessed features (before scaling):")
print(f"   Shape: {feature_vector_raw.shape}")
print(f"   Values: {feature_vector_raw}")
print(f"   Min/Max: [{feature_vector_raw.min():.4f}, {feature_vector_raw.max():.4f}]")

# Step 2: Apply scaler manually
if classifier.current_scaler:
    feature_vector_scaled = classifier.current_scaler.transform(feature_vector_raw.reshape(1, -1))[0]
    print(f"\n2. After scaling:")
    print(f"   Shape: {feature_vector_scaled.shape}")
    print(f"   Values: {feature_vector_scaled}")
    print(f"   Min/Max: [{feature_vector_scaled.min():.4f}, {feature_vector_scaled.max():.4f}]")
    
    # Step 3: Get raw model prediction
    prob_raw = classifier.current_model.predict_proba(feature_vector_raw.reshape(1, -1))[0]
    print(f"\n3. Model prediction on RAW features:")
    print(f"   Benign prob: {prob_raw[0]:.4f}, Pathogenic prob: {prob_raw[1]:.4f}")
    
    # Step 4: Get scaled model prediction
    prob_scaled = classifier.current_model.predict_proba(feature_vector_scaled.reshape(1, -1))[0]
    print(f"\n4. Model prediction on SCALED features:")
    print(f"   Benign prob: {prob_scaled[0]:.4f}, Pathogenic prob: {prob_scaled[1]:.4f}")
    
    # Step 5: Classifier classify method
    print(f"\n5. Classifier.classify() result:")
    result = classifier.classify(test_features)
    print(f"   Classification: {result['classification']}")
    print(f"   Benign prob: {result['probabilities']['benign']:.4f}")
    print(f"   Pathogenic prob: {result['probabilities']['pathogenic']:.4f}")
else:
    print("ERROR: No scaler found!")

print("\n" + "="*80 + "\n")
