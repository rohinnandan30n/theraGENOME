#!/usr/bin/env python3
"""Debug script to verify training and inference pipeline"""

import logging
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, roc_curve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("TRAINING/INFERENCE DEBUG")
print("="*80 + "\n")

# 1. Create simple synthetic data
np.random.seed(42)
n_samples = 2000
X = np.random.randn(n_samples, 10)
decision_boundary = X[:, 0] * 1.5 + X[:, 1] * 0.8
y = (decision_boundary > np.percentile(decision_boundary, 50)).astype(int)

print(f"Step 1: Synthetic data created")
print(f"  X shape: {X.shape}, y distribution: {np.unique(y, return_counts=True)[1]}")
print(f"  X range: [{X.min():.2f}, {X.max():.2f}]")

# 2. Train/val split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\nStep 2: Split data")
print(f"  X_train shape: {X_train.shape}, X_val shape: {X_val.shape}")

# 3. Fit scaler on training data only
scaler = StandardScaler()
scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_val_scaled = scaler.transform(X_val)

print(f"\nStep 3: Scale features")
print(f"  Scaler fitted on X_train: mean={scaler.mean_[:3]}, std={scaler.scale_[:3]}")
print(f"  X_train_scaled range: [{X_train_scaled.min():.2f}, {X_train_scaled.max():.2f}]")
print(f"  X_val_scaled range: [{X_val_scaled.min():.2f}, {X_val_scaled.max():.2f}]")

# 4. Train model
rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=15, class_weight='balanced', n_jobs=-1)
rf.fit(X_train_scaled, y_train)

# Check predictions during training
y_pred_val = rf.predict(X_val_scaled)
auroc_train = roc_auc_score(y_val, rf.predict_proba(X_val_scaled)[:, 1])
print(f"\nStep 4: Train RF model on scaled data")
print(f"  RF AUROC on val set: {auroc_train:.4f}")

# 5. Calibrate model
calibrated = CalibratedClassifierCV(rf, method='isotonic', cv=5)
calibrated.fit(X_train_scaled, y_train)

y_prob_calibrated = calibrated.predict_proba(X_val_scaled)
auroc_cal = roc_auc_score(y_val, y_prob_calibrated[:, 1])
print(f"\nStep 5: Calibrate model")
print(f"  Calibrated AUROC on val set: {auroc_cal:.4f}")
print(f"  Sample calibrated probs on benign: {y_prob_calibrated[y_val == 0][:5]}")
print(f"  Sample calibrated probs on pathogenic: {y_prob_calibrated[y_val == 1][:5]}")

# 6. Save model and scaler
model_path = './debug_model_test.pkl'
scaler_path = './debug_scaler_test.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(calibrated, f)
with open(scaler_path, 'wb') as f:
    pickle.dump(scaler, f)
print(f"\nStep 6: Saved model and scaler")

# 7. Load model and scaler
with open(model_path, 'rb') as f:
    loaded_model = pickle.load(f)
with open(scaler_path, 'rb') as f:
    loaded_scaler = pickle.load(f)
print(f"\nStep 7: Loaded model and scaler")

# 8. Test on validation data
y_prob_loaded = loaded_model.predict_proba(X_val_scaled)
auroc_loaded = roc_auc_score(y_val, y_prob_loaded[:, 1])
print(f"\nStep 8: Predictions on val set with loaded model")
print(f"  AUROC: {auroc_loaded:.4f}")
print(f"  Sample probs on benign: {y_prob_loaded[y_val == 0][:5]}")
print(f"  Sample probs on pathogenic: {y_prob_loaded[y_val == 1][:5]}")

# 9. Test on test features (like real inference)
# Create test features with same distribution as X (N(0,1))
X_test = np.random.randn(10, 10)
X_test_scaled = loaded_scaler.transform(X_test)
y_test_prob = loaded_model.predict_proba(X_test_scaled)
print(f"\nStep 9: Predictions on new test features (N(0,1) distribution)")
print(f"  X_test range: [{X_test.min():.2f}, {X_test.max():.2f}]")
print(f"  X_test_scaled range: [{X_test_scaled.min():.2f}, {X_test_scaled.max():.2f}]")
print(f"  Sample test probs: {y_test_prob[:5]}")

# 10. Test on [0,1] normalized features (like real variants)
X_test_normalized = np.random.uniform(0, 1, (10, 10))
X_test_norm_scaled = loaded_scaler.transform(X_test_normalized)
y_test_norm_prob = loaded_model.predict_proba(X_test_norm_scaled)
print(f"\nStep 10: Predictions on [0,1] normalized features")
print(f"  X_test_normalized range: [{X_test_normalized.min():.2f}, {X_test_normalized.max():.2f}]")
print(f"  X_test_norm_scaled range: [{X_test_norm_scaled.min():.2f}, {X_test_norm_scaled.max():.2f}]")
print(f"  Sample normalized probs: {y_test_norm_prob[:5]}")

# Cleanup
os.remove(model_path)
os.remove(scaler_path)

print("\n" + "="*80 + "\n")
