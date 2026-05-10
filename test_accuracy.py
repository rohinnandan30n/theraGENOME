#!/usr/bin/env python3
"""
Model Accuracy Evaluation
Comprehensive test of model accuracy and performance metrics
"""

import sys
import json
import traceback
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.ml.model_manager import ModelRegistry, get_registry
from src.ml.classifier import PathogenicityClassifier
from src.ml.feature_preprocessor import FeaturePreprocessor

print("\n" + "="*80)
print("  MODEL ACCURACY & PERFORMANCE EVALUATION")
print("="*80 + "\n")

# Test Variants - Mix of pathogenic, VUS, and benign cases
TEST_VARIANTS = [
    {
        'name': 'TP53 R175H (Known Pathogenic)',
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
        'expected': 'Pathogenic'
    },
    {
        'name': 'BRCA1 Frameshift (Known Pathogenic)',
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
        'expected': 'Pathogenic'
    },
    {
        'name': 'Silent Mutation (Known Benign)',
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
        'expected': 'Benign'
    },
    {
        'name': 'Common Variant (Likely Benign)',
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
        'expected': 'Benign'
    },
    {
        'name': 'Missense - Moderate Impact (VUS)',
        'features': {
            'phyloP_score': 1.5,
            'SIFT_score': 0.05,
            'PolyPhen_score': 0.65,
            'CADD_score': 18.0,
            'gnomAD_freq': 0.001,
            'REVEL_score': 0.55,
            'MutationTaster_score': 0.50,
            'FathmM_score': 0.55,
            'variant_type': 'Substitution',
            'amino_acid_change': 'P53L'
        },
        'expected': 'VUS'
    },
    {
        'name': 'Highly Conservative Position (Likely Pathogenic)',
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
        'expected': 'Pathogenic'
    }
]

# Test each model version
results_by_version = {}

for version in ['v1', 'v2', 'v3']:
    print(f"\n{'='*80}")
    print(f"  MODEL VERSION: pathogenicity:{version}")
    print(f"{'='*80}\n")
    
    try:
        classifier = PathogenicityClassifier(default_version=version)
        version_results = []
        
        correct_predictions = 0
        total_tests = len(TEST_VARIANTS)
        
        for i, test_case in enumerate(TEST_VARIANTS, 1):
            try:
                result = classifier.classify(test_case['features'])
                
                predicted = result.get('classification', 'Unknown')
                expected = test_case['expected']
                confidence = result.get('confidence', 0.0)
                is_correct = (predicted == expected)
                
                if is_correct:
                    correct_predictions += 1
                
                print(f"Test {i}: {test_case['name']}")
                print(f"  Expected: {expected:12} | Predicted: {predicted:12} | {'[PASS]' if is_correct else '[FAIL]'}")
                print(f"  Confidence: {confidence:.4f} | Probs: B={result.get('probabilities', {}).get('benign', 0):.4f}, P={result.get('probabilities', {}).get('pathogenic', 0):.4f}\n")
                
                version_results.append({
                    'test': test_case['name'],
                    'expected': expected,
                    'predicted': predicted,
                    'correct': is_correct,
                    'confidence': float(confidence),
                    'probabilities': result.get('probabilities', {})
                })
                
            except Exception as e:
                print(f"Test {i}: {test_case['name']}")
                print(f"  [ERROR]: {str(e)}\n")
                version_results.append({
                    'test': test_case['name'],
                    'expected': test_case['expected'],
                    'predicted': 'ERROR',
                    'correct': False,
                    'error': str(e)
                })
        
        # Calculate accuracy
        accuracy = (correct_predictions / total_tests) * 100
        
        print(f"\n{'-'*80}")
        print(f"MODEL v{version} SUMMARY")
        print(f"{'-'*80}")
        print(f"Accuracy: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
        print(f"Correct Predictions: {correct_predictions}")
        print(f"Incorrect/Error: {total_tests - correct_predictions}\n")
        
        results_by_version[version] = {
            'accuracy': accuracy,
            'correct': correct_predictions,
            'total': total_tests,
            'test_results': version_results
        }
        
    except Exception as e:
        print(f"[FAILED] to initialize model v{version}: {e}\n")
        traceback.print_exc()

# Overall Summary
print("\n" + "="*80)
print("  OVERALL ACCURACY SUMMARY")
print("="*80 + "\n")

for version in ['v1', 'v2', 'v3']:
    if version in results_by_version:
        stats = results_by_version[version]
        print(f"Model v{version}: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})")

# Best performing model
if results_by_version:
    best_version = max(results_by_version.items(), key=lambda x: x[1]['accuracy'])
    print(f"\n[BEST] Model v{best_version[0]} with {best_version[1]['accuracy']:.1f}% accuracy")

print("\n" + "="*80 + "\n")
