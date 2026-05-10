#!/usr/bin/env python3
"""
Test Models Functionality
Verify that all models load and work properly
"""

import sys
import traceback
from src.ml.model_manager import ModelRegistry
from src.ml.classifier import PathogenicityClassifier
from src.ml.feature_preprocessor import FeaturePreprocessor

print("\n" + "="*70)
print("  THERAGENOME MODELS TESTING")
print("="*70 + "\n")

# Test 1: Model Discovery
print("TEST 1: Model Discovery")
print("-" * 70)
try:
    registry = ModelRegistry('./models')
    print(f"[OK] Model registry initialized at ./models\n")
    print(f"Discovered models:")
    if registry.model_metadata:
        for model_id, meta in registry.model_metadata.items():
            print(f"  • {model_id}")
            print(f"    - Path: {meta['path']}")
            print(f"    - Type: {meta['model_type']}")
        print(f"\n[OK] Found {len(registry.model_metadata)} models\n")
    else:
        print("[WARN] No models discovered\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    traceback.print_exc()

# Test 2: Feature Preprocessor
print("\nTEST 2: Feature Preprocessor")
print("-" * 70)
try:
    preprocessor = FeaturePreprocessor()
    feature_names = preprocessor.get_feature_names()
    print("[OK] Feature preprocessor initialized")
    print(f"   Features available: {len(feature_names)}")
    print(f"   Sample features: {feature_names[:5]}...\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    traceback.print_exc()

# Test 3: Classifier Initialization
print("\nTEST 3: Pathogenicity Classifier Initialization")
print("-" * 70)
try:
    for version in ['v1', 'v2', 'v3']:
        try:
            classifier = PathogenicityClassifier(default_version=version)
            print(f"[OK] Classifier v{version} initialized successfully")
        except Exception as e:
            print(f"[WARN] Classifier v{version} failed: {e}")
    print()
except Exception as e:
    print(f"[FAIL] {e}\n")
    traceback.print_exc()

# Test 4: Classification Test
print("\nTEST 4: Classification Test (Sample)")
print("-" * 70)
try:
    classifier = PathogenicityClassifier(default_version='v2')
    
    # Create sample features (exact names required by preprocessor)
    test_features = {
        'phyloP_score': 3.5,           # Evolutionary conservation (-14 to 6)
        'SIFT_score': 0.02,            # Protein impact (0 to 1, lower = damaging)
        'PolyPhen_score': 0.95,        # Protein impact (0 to 1, higher = damaging)
        'CADD_score': 28.5,            # Combined score (0 to 99, higher = more damaging)
        'gnomAD_freq': 0.0001,         # Population frequency (0 to 1)
        'REVEL_score': 0.75,           # Ensemble pathogenicity (0 to 1)
        'MutationTaster_score': 0.8,   # Mutation impact (0 to 1)
        'FathmM_score': 0.7,           # Functional impact (0 to 1)
        'variant_type': 'Substitution', # Type: SNP, Deletion, Insertion, etc.
        'amino_acid_change': 'D123H'   # Protein change notation
    }
    
    result = classifier.classify(test_features)
    print("[OK] Classification successful")
    print(f"   Variant: {result.get('variant', 'N/A')}")
    print(f"   Classification: {result.get('classification', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 'N/A'):.4f}")
    print(f"   Probabilities: B={result.get('probabilities', {}).get('benign', 'N/A'):.4f}, P={result.get('probabilities', {}).get('pathogenic', 'N/A'):.4f}\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    traceback.print_exc()

print("="*70)
print("  TESTING COMPLETE")
print("="*70 + "\n")
