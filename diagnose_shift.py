#!/usr/bin/env python3
"""
DIAGNOSTIC: Train vs Test Feature Distribution Shift Analysis
Shows where the distribution mismatch is causing classifier failures
"""
import sys
import os
import numpy as np
sys.path.insert(0, '.')

from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.feature_scaler import FeatureScaler

print("\n" + "="*100)
print("  FEATURE DISTRIBUTION SHIFT DIAGNOSTIC")
print("="*100 + "\n")

# Step 1: Generate TRAINING data (as currently done in train_model.py)
print("STEP 1: Capture Training Data Distribution")
print("-" * 100)

np.random.seed(42)
n_train = 2000
n_features = 10

# This is what train_model.py does - random N(0,1)
X_train = np.random.randn(n_train, n_features)
print(f"Training data: {X_train.shape}")
print(f"  Mean: {np.mean(X_train, axis=0)[:5]}")
print(f"  Std:  {np.std(X_train, axis=0)[:5]}")
print(f"  Min:  {np.min(X_train, axis=0)[:5]}")
print(f"  Max:  {np.max(X_train, axis=0)[:5]}")

train_stats = {
    'mean': np.mean(X_train, axis=0),
    'std': np.std(X_train, axis=0),
    'min': np.min(X_train, axis=0),
    'max': np.max(X_train, axis=0)
}

# Step 2: Generate TEST data (from biological features as in test_accuracy.py)
print("\n\nSTEP 2: Capture Test Data Distribution")
print("-" * 100)

# Create test samples using FeaturePreprocessor (biological features)
preprocessor = FeaturePreprocessor()

test_cases = [
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
        }
    },
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
        }
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
        }
    },
]

X_test = np.array([preprocessor.preprocess(tc['features']) for tc in test_cases])
print(f"Test data: {X_test.shape}")
print(f"  Mean: {np.mean(X_test, axis=0)[:5]}")
print(f"  Std:  {np.std(X_test, axis=0)[:5]}")
print(f"  Min:  {np.min(X_test, axis=0)[:5]}")
print(f"  Max:  {np.max(X_test, axis=0)[:5]}")

test_stats = {
    'mean': np.mean(X_test, axis=0),
    'std': np.std(X_test, axis=0),
    'min': np.min(X_test, axis=0),
    'max': np.max(X_test, axis=0)
}

# Step 3: Compare distributions
print("\n\nSTEP 3: Distribution Shift Analysis")
print("-" * 100)
print(f"{'Feature':<20} {'Train Mean':<15} {'Test Mean':<15} {'Shift (σ)':<15} {'Status':<15}")
print("-" * 100)

flag_count = 0
for i in range(10):
    train_mean = train_stats['mean'][i]
    test_mean = test_stats['mean'][i]
    train_std = train_stats['std'][i]
    
    # How many standard deviations away is test mean from train mean?
    if train_std > 0.01:
        shift_sigma = abs(test_mean - train_mean) / train_std
    else:
        shift_sigma = float('inf')
    
    # Flag if shift > 2 std
    status = f"⚠️  SHIFT" if shift_sigma > 2.0 else "✓ OK"
    if shift_sigma > 2.0:
        flag_count += 1
    
    print(f"F{i:<19} {train_mean:<15.6f} {test_mean:<15.6f} {shift_sigma:<15.2f} {status:<15}")

print(f"\n⚠️  {flag_count}/10 features show significant shift (>2σ from training mean)")

# Step 4: Check out-of-range values
print("\n\nSTEP 4: Out-of-Range Test Values")
print("-" * 100)

out_of_range_count = 0
for i in range(10):
    test_min = test_stats['min'][i]
    test_max = test_stats['max'][i]
    train_min = train_stats['min'][i]
    train_max = train_stats['max'][i]
    
    below_range = test_min < train_min
    above_range = test_max > train_max
    
    if below_range or above_range:
        print(f"Feature {i}: Test [{test_min:.4f}, {test_max:.4f}] vs Train [{train_min:.4f}, {train_max:.4f}]", end="")
        if below_range and above_range:
            print(" ❌ BOTH outside")
            out_of_range_count += 1
        elif below_range:
            print(" ⚠️  BELOW train range")
        else:
            print(" ⚠️  ABOVE train range")

print(f"\n❌ {out_of_range_count}/10 features have test values completely outside training range")

# Step 5: Solution
print("\n\n" + "="*100)
print("  ROOT CAUSE ANALYSIS")
print("="*100 + "\n")

print("""
PROBLEM IDENTIFIED: Feature Distribution Mismatch

Training Data:
  - Generated via: X = np.random.randn(2000, 10)
  - Distribution: N(μ≈0, σ≈1) for all features
  - Models learned patterns in this distribution

Test Data:
  - Generated via: FeaturePreprocessor.preprocess(biological_features)
  - Uses hardcoded normalization to [0, 1] range
  - Distribution completely different from training!

CONSEQUENCE:
  - Models extrapolate far outside their training distribution
  - This causes extreme probabilities (0.0 or 1.0)
  - Poor generalization to realistic biological features

SOLUTION (Multi-step):
  1. ✅ Capture train data statistics during training (done via FeatureScaler)
  2. ✅ Create learned scaler fit ONLY on training data
  3. ✅ Use Pipeline to enforce fit/transform order
  4. ✅ Apply same scaling to both train and test data
  5. ✅ Clip out-of-range test features to [train_min, train_max]
  6. ✅ Verify scaled features fall in [-3, 3] range (3σ from mean)
""")

print("="*100 + "\n")
