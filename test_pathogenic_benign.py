#!/usr/bin/env python3
"""Test scaler on both pathogenic and benign variants"""

import logging
import numpy as np
from src.ml.classifier import PathogenicityClassifier
from src.ml.feature_preprocessor import FeaturePreprocessor

logging.basicConfig(level=logging.WARNING)

print("\n" + "="*80)
print("MODEL PREDICTION TEST - PATHOGENIC vs BENIGN")
print("="*80 + "\n")

classifier = PathogenicityClassifier(default_version='v1')
preprocessor = FeaturePreprocessor()

# Test cases
test_cases = [
    {
        'name': 'Pathogenic (TP53 R175H)',
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
        }
    },
    {
        'name': 'Benign (Silent Mutation)',
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
        }
    }
]

for test_case in test_cases:
    print(f"Test: {test_case['name']}")
    
    # Get raw features
    feature_vector_raw = preprocessor.preprocess(test_case['features'])
    
    # Get scaled features
    feature_vector_scaled = classifier.current_scaler.transform(feature_vector_raw.reshape(1, -1))[0]
    
    # Raw prediction
    prob_raw = classifier.current_model.predict_proba(feature_vector_raw.reshape(1, -1))[0]
    print(f"  Raw features:     Benign={prob_raw[0]:.4f}, Pathogenic={prob_raw[1]:.4f}")
    
    # Scaled prediction
    prob_scaled = classifier.current_model.predict_proba(feature_vector_scaled.reshape(1, -1))[0]
    print(f"  Scaled features:  Benign={prob_scaled[0]:.4f}, Pathogenic={prob_scaled[1]:.4f}")
    
    # Classifier prediction
    result = classifier.classify(test_case['features'])
    print(f"  Classifier:       Classification={result['classification']}, Benign={result['probabilities']['benign']:.4f}, Pathogenic={result['probabilities']['pathogenic']:.4f}")
    print()

print("="*80 + "\n")
