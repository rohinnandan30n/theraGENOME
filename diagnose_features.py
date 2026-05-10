#!/usr/bin/env python3
"""
Diagnostic: Show normalized features for test cases
"""
import sys
import os
sys.path.insert(0, '.')

from src.ml.feature_preprocessor import FeaturePreprocessor

test_cases = [
    {
        'name': 'TP53 R175H (Pathogenic)',
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
        'name': 'Common Variant (Benign)',
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
        }
    }
]

preprocessor = FeaturePreprocessor()

print("\n" + "="*80)
print("FEATURE PREPROCESSING ANALYSIS")
print("="*80 + "\n")

for tc in test_cases:
    print(f"{tc['name']}:")
    print("-" * 80)
    
    vector = preprocessor.preprocess(tc['features'])
    
    print(f"Normalized vector: {vector}")
    print(f"  phyloP_score (0.0-1.0):     {vector[0]:.4f}  (from raw {tc['features']['phyloP_score']})")
    print(f"  SIFT_score (0.0-1.0):       {vector[1]:.4f}  (from raw {tc['features']['SIFT_score']})")
    print(f"  PolyPhen_score (0.0-1.0):   {vector[2]:.4f}  (from raw {tc['features']['PolyPhen_score']})")
    print(f"  CADD_score (0.0-1.0):       {vector[3]:.4f}  (from raw {tc['features']['CADD_score']})")
    print(f"  gnomAD_freq (0.0-1.0):      {vector[4]:.4f}  (from raw {tc['features']['gnomAD_freq']})")
    print(f"  REVEL_score (0.0-1.0):      {vector[5]:.4f}  (from raw {tc['features']['REVEL_score']})")
    print(f"  MutationTaster_score:       {vector[6]:.4f}  (from raw {tc['features']['MutationTaster_score']})")
    print(f"  FathmM_score (0.0-1.0):     {vector[7]:.4f}  (from raw {tc['features']['FathmM_score']})")
    print(f"  variant_type_encoded:       {vector[8]:.4f}")
    print(f"  aa_change_encoded:          {vector[9]:.4f}")
    print()

print("\n" + "="*80)
print("INTERPRETATION")
print("="*80 + "\n")
print("""
The normalized features look reasonable (in 0.0-1.0 range). However, the training
data was generated with random N(0,1) features, while test data uses realistic
biological values. This domain mismatch causes the model to be uncertain.

The models show:
- ALL predictions output probability 0.0 or 1.0 (extreme)
- This indicates the model is extrapolating far beyond its training distribution

ROOT CAUSE:
- Training: Random synthetic N(0,1) features
- Testing: Real biological features with different distributions
- Model: Learns from one distribution, tested on another

SOLUTION:
Generate training data from realistic biological feature distributions instead
of random N(0,1). This way models learn the actual relationships between
biological features and pathogenicity labels.
""")
