#!/usr/bin/env python3
"""
Generate pre-trained models for testing with class balance and proper evaluation.

Creates sklearn models for pathogenicity classification with:
- Diagnosis of training data issues
- Class imbalance correction via SMOTE
- Cross-validation with StratifiedKFold
- ROC curve-based threshold tuning
- Probability calibration
- Validation gates for production readiness
- PROPER FEATURE SCALING (fit on train only, no data leakage)
"""

import sys
import os
import logging
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_curve, auc, roc_auc_score, confusion_matrix, f1_score, classification_report
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.model_manager import get_registry
from src.ml.feature_scaler import FeatureScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def diagnose_data(X, y, data_name: str = "Data"):
    """STEP 1: Diagnose class distribution and feature-label correlation"""
    logger.info(f"\n{'='*80}")
    logger.info(f"DIAGNOSIS: {data_name}")
    logger.info(f"{'='*80}")
    
    unique, counts = np.unique(y, return_counts=True)
    class_dist = {int(c): int(count) for c, count in zip(unique, counts)}
    
    logger.info(f"Class distribution: {class_dist}")
    total = len(y)
    for label, count in class_dist.items():
        pct = (count / total) * 100
        logger.info(f"  Class {label}: {count}/{total} ({pct:.1f}%)")
    
    # Calculate imbalance ratio
    if len(class_dist) == 2:
        ratio = max(counts) / min(counts)
        logger.info(f"Imbalance ratio: {ratio:.2f}:1")
        if ratio > 3:
            logger.warning(f"⚠️  SEVERE IMBALANCE: {ratio:.1f}:1 (threshold: 3:1)")
    
    # Check for feature-label correlation
    logger.info(f"\nFeature-Label Correlation Analysis:")
    correlations = []
    for i in range(X.shape[1]):
        corr = np.abs(np.corrcoef(X[:, i], y)[0, 1])
        correlations.append(corr)
        if corr > 0.95:
            logger.warning(f"  ⚠️  Feature {i}: {corr:.4f} (NEAR-PERFECT correlation!)")
        elif corr > 0.5:
            logger.info(f"  Feature {i}: {corr:.4f} (moderate correlation)")
    
    return class_dist, np.array(correlations)


def train_baseline(X_train, y_train):
    """Train DummyClassifier baseline for comparison"""
    logger.info(f"\n{'='*80}")
    logger.info(f"BASELINE: DummyClassifier")
    logger.info(f"{'='*80}")
    
    baseline = DummyClassifier(strategy='stratified', random_state=42)
    baseline.fit(X_train, y_train)
    
    y_pred = baseline.predict(X_train)
    accuracy = np.mean(y_pred == y_train)
    logger.info(f"Dummy Classifier Accuracy (stratified): {accuracy:.4f}")
    
    return baseline


def apply_smote_or_balance(X, y, method='smote'):
    """STEP 2: Fix class imbalance with SMOTE or class weights"""
    logger.info(f"\n{'='*80}")
    logger.info(f"CLASS BALANCE CORRECTION")
    logger.info(f"{'='*80}")
    
    unique, counts = np.unique(y, return_counts=True)
    
    if method == 'smote':
        try:
            from imblearn.over_sampling import SMOTE
            logger.info("Applying SMOTE oversampling...")
            
            # Target 1:2 ratio (benign:pathogenic) as requested
            benign_count = np.sum(y == 0)
            pathogenic_count = np.sum(y == 1)
            
            if pathogenic_count > benign_count:
                target_ratio = benign_count / pathogenic_count
            else:
                target_ratio = 1.0
            
            smote = SMOTE(sampling_strategy=target_ratio, random_state=42)
            X_balanced, y_balanced = smote.fit_resample(X, y)
            
            logger.info(f"Before SMOTE: {np.sum(y == 0)} benign, {np.sum(y == 1)} pathogenic")
            logger.info(f"After SMOTE:  {np.sum(y_balanced == 0)} benign, {np.sum(y_balanced == 1)} pathogenic")
            
            return X_balanced, y_balanced
        
        except ImportError:
            logger.warning("⚠️  SMOTE not available, using class_weight='balanced' instead")
            return X, y
    
    return X, y


def train_model_with_cv(X, y, version: str = 'v1', random_state: int = 42) -> tuple:
    """STEP 3-5: Train with cross-validation, tuned thresholds, calibration, AND PROPER SCALING"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TRAINING MODEL {version}")
    logger.info(f"{'='*80}")
    
    # Split data BEFORE fitting scaler (critical to prevent data leakage!)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    
    logger.info(f"Train set: {len(y_train)} samples")
    logger.info(f"Val set: {len(y_val)} samples")
    
    # CRITICAL: Fit scaler ONLY on training data
    logger.info(f"\nFitting feature scaler on training data only (prevent leakage)...")
    scaler = FeatureScaler(feature_names=[f"feature_{i}" for i in range(X.shape[1])])
    scaler.fit(X_train)  # ✅ FIT ONLY ON TRAINING DATA
    
    # Transform both train and validation with the SAME learned scaler
    X_train_scaled = scaler.transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    logger.info(f"Scaled train range: [{X_train_scaled.min():.4f}, {X_train_scaled.max():.4f}]")
    logger.info(f"Scaled val range: [{X_val_scaled.min():.4f}, {X_val_scaled.max():.4f}]")
    
    # Apply SMOTE on training data (or fallback to class weights)
    X_train_balanced, y_train_balanced = apply_smote_or_balance(X_train_scaled, y_train, method='smote')
    
    # Train with class weights for robustness
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=random_state,
        max_depth=15,
        class_weight='balanced',  # FIX: Handle class imbalance
        n_jobs=-1
    )
    
    # Cross-validation for evaluation (on scaled data)
    logger.info(f"\nPerforming 5-fold StratifiedKFold cross-validation...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    
    cv_scores = []
    cv_aucs = []
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X_train_balanced, y_train_balanced), 1):
        X_cv_train, X_cv_test = X_train_balanced[train_idx], X_train_balanced[test_idx]
        y_cv_train, y_cv_test = y_train_balanced[train_idx], y_train_balanced[test_idx]
        
        fold_model = RandomForestClassifier(
            n_estimators=100,
            random_state=random_state,
            max_depth=15,
            class_weight='balanced',
            n_jobs=-1
        )
        fold_model.fit(X_cv_train, y_cv_train)
        
        acc = fold_model.score(X_cv_test, y_cv_test)
        y_prob = fold_model.predict_proba(X_cv_test)[:, 1]
        auroc_score = roc_auc_score(y_cv_test, y_prob)
        
        cv_scores.append(acc)
        cv_aucs.append(auroc_score)
        logger.info(f"  Fold {fold}: Accuracy={acc:.4f}, AUROC={auroc_score:.4f}")
    
    logger.info(f"CV Mean Accuracy: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")
    logger.info(f"CV Mean AUROC: {np.mean(cv_aucs):.4f} ± {np.std(cv_aucs):.4f}")
    
    # Train final model on balanced training data (already scaled)
    model.fit(X_train_balanced, y_train_balanced)
    
    # STEP 4: Tune threshold via ROC curve (on scaled val data)
    logger.info(f"\nTuning classification threshold via ROC curve on validation set...")
    y_val_prob = model.predict_proba(X_val_scaled)[:, 1]
    fpr, tpr, thresholds = roc_curve(y_val, y_val_prob)
    
    # Find optimal threshold (Youden's J statistic: TPR - FPR)
    J = tpr - fpr
    optimal_idx = np.argmax(J)
    optimal_threshold = thresholds[optimal_idx]
    
    logger.info(f"Optimal threshold (Youden): {optimal_threshold:.4f}")
    logger.info(f"  TPR at optimal: {tpr[optimal_idx]:.4f}")
    logger.info(f"  FPR at optimal: {fpr[optimal_idx]:.4f}")
    
    # STEP 5: Calibrate probabilities
    logger.info(f"\nCalibrating probabilities with CalibratedClassifierCV (isotonic)...")
    calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=5)
    calibrated_model.fit(X_train_balanced, y_train_balanced)
    
    # Verify calibration improved probability spread
    y_val_prob_before = model.predict_proba(X_val_scaled)[:, 1]
    y_val_prob_after = calibrated_model.predict_proba(X_val_scaled)[:, 1]
    
    std_before = np.std(y_val_prob_before)
    std_after = np.std(y_val_prob_after)
    
    logger.info(f"Probability std dev before calibration: {std_before:.4f}")
    logger.info(f"Probability std dev after calibration: {std_after:.4f}")
    
    if std_after < 0.1:
        logger.warning(f"⚠️  Calibrated probabilities still have low variance ({std_after:.4f})")
    
    return calibrated_model, optimal_threshold, X_val_scaled, y_val, scaler


def validate_and_gate(model, threshold, X_val, y_val, version: str = 'v1'):
    """STEP 6: Validation gate - ensure production readiness"""
    logger.info(f"\n{'='*80}")
    logger.info(f"VALIDATION GATE: {version}")
    logger.info(f"{'='*80}")
    
    # Generate predictions with tuned threshold
    y_val_prob = model.predict_proba(X_val)[:, 1]
    y_val_pred = (y_val_prob >= threshold).astype(int)
    
    # Calculate metrics
    tn, fp, fn, tp = confusion_matrix(y_val, y_val_pred).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0  # True positive rate
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0  # True negative rate
    auroc = roc_auc_score(y_val, y_val_prob)
    f1 = f1_score(y_val, y_val_pred)
    
    logger.info(f"\nValidation Metrics:")
    logger.info(f"  Sensitivity (TPR): {sensitivity:.4f}")
    logger.info(f"  Specificity (TNR): {specificity:.4f}")
    logger.info(f"  AUROC: {auroc:.4f}")
    logger.info(f"  F1-Score: {f1:.4f}")
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    
    # Validation gates
    gate_specificity = specificity > 0.5
    gate_sensitivity = sensitivity > 0.7
    gate_auroc = auroc > 0.7
    
    logger.info(f"\nValidation Gates:")
    logger.info(f"  Specificity > 0.5: {gate_specificity} ({specificity:.4f})")
    logger.info(f"  Sensitivity > 0.7: {gate_sensitivity} ({sensitivity:.4f})")
    logger.info(f"  AUROC > 0.7: {gate_auroc} ({auroc:.4f})")
    
    gates_passed = gate_specificity and gate_sensitivity and gate_auroc
    
    if not gates_passed:
        error_msg = (
            f"VALIDATION FAILED for {version}: "
            f"Specificity={specificity:.4f} (need >0.5), "
            f"Sensitivity={sensitivity:.4f} (need >0.7), "
            f"AUROC={auroc:.4f} (need >0.7)"
        )
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"✅ VALIDATION PASSED for {version}")
    
    return {
        'sensitivity': sensitivity,
        'specificity': specificity,
        'auroc': auroc,
        'f1': f1,
        'threshold': threshold
    }


def train_mock_model(random_state: int = 42) -> tuple:
    """Train a properly balanced RF model with diagnostics, validation, AND proper scaling"""
    # Create synthetic training data with better properties
    n_samples = 2000
    n_features = 10
    
    # ✅ CRITICAL FIX: Generate features in [0,1] range matching real variant distribution
    # Real variant features are normalized to [0,1] by FeaturePreprocessor
    # Training data must match this distribution for the model to work correctly
    np.random.seed(random_state)
    X = np.random.uniform(0, 1, (n_samples, n_features))
    
    # Create labels with clear separation based on feature combinations
    # Pathogenic: high scores on conservation/damage measures (features 0-4)
    # Benign: low scores on conservation/damage measures
    decision_boundary = (
        X[:, 0] * 2.0 +  # High conservation (phyloP) → pathogenic
        (1 - X[:, 1]) * 1.5 +  # Low SIFT score (tolerance) → pathogenic
        X[:, 2] * 1.8 +  # High PolyPhen → pathogenic
        X[:, 3] * 1.2 +  # High CADD → pathogenic
        (1 - X[:, 4]) * 0.8  # Low gnomAD freq → pathogenic
    )
    y = (decision_boundary > np.percentile(decision_boundary, 50)).astype(int)
    
    # Ensure reasonable class balance (not perfect, but better than 95%/5%)
    unique, counts = np.unique(y, return_counts=True)
    logger.info(f"Initial synthetic data class distribution: {dict(zip(unique, counts))}")
    
    # STEP 1: Diagnose
    diagnose_data(X, y, "Synthetic Training Data")
    train_baseline(X[:1600], y[:1600])
    
    # Train model (now with proper scaling)
    model, threshold, X_val_scaled, y_val, scaler = train_model_with_cv(X, y, random_state=random_state)
    
    # STEP 6: Validate
    metrics = validate_and_gate(model, threshold, X_val_scaled, y_val)
    
    logger.info(f"\nModel trained successfully with metrics: {metrics}\n")
    
    return model, metrics, scaler


def generate_models():
    """Generate and register properly trained models with validation"""
    try:
        registry = get_registry()
        
        # Generate v1
        logger.info("\n" + "="*80)
        logger.info("GENERATING v1 MODEL")
        logger.info("="*80)
        model_v1, metrics_v1, scaler_v1 = train_mock_model(random_state=42)
        
        # Save scaler for later use during inference
        scaler_v1_path = os.path.join(registry.models_dir, 'pathogenicity_v1_scaler.pkl')
        with open(scaler_v1_path, 'wb') as f:
            pickle.dump(scaler_v1, f)
        logger.info(f"✅ Saved scaler v1 to {scaler_v1_path}")
        
        path_v1 = registry.save_model(
            'pathogenicity',
            'v1',
            model_v1,
            metadata={
                'model_type': 'sklearn',
                'description': 'RandomForest pathogenicity classifier v1 with SMOTE, calibration, and proper scaling',
                'features': [
                    'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                    'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                    'variant_type_encoded', 'aa_change_encoded'
                ],
                'scaler_path': scaler_v1_path,
                'performance': {
                    'accuracy': metrics_v1.get('sensitivity', 0),
                    'sensitivity': metrics_v1.get('sensitivity', 0),
                    'specificity': metrics_v1.get('specificity', 0),
                    'auc_roc': metrics_v1.get('auroc', 0),
                    'f1_score': metrics_v1.get('f1', 0),
                    'threshold': metrics_v1.get('threshold', 0.5)
                }
            }
        )
        logger.info(f"✅ Saved model v1 to {path_v1}")
        
        # Generate v2
        logger.info("\n" + "="*80)
        logger.info("GENERATING v2 MODEL")
        logger.info("="*80)
        model_v2, metrics_v2, scaler_v2 = train_mock_model(random_state=123)
        
        # Save scaler for later use during inference
        scaler_v2_path = os.path.join(registry.models_dir, 'pathogenicity_v2_scaler.pkl')
        with open(scaler_v2_path, 'wb') as f:
            pickle.dump(scaler_v2, f)
        logger.info(f"✅ Saved scaler v2 to {scaler_v2_path}")
        
        # For v2 metadata update
        metadata_v2 = {
            'model_type': 'sklearn',
            'description': 'RandomForest pathogenicity classifier v2 with SMOTE, calibration, and proper scaling',
            'features': [
                'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                'variant_type_encoded', 'aa_change_encoded'
            ],
            'scaler_path': scaler_v2_path,
            'performance': {
                'accuracy': metrics_v2.get('sensitivity', 0),
                'sensitivity': metrics_v2.get('sensitivity', 0),
                'specificity': metrics_v2.get('specificity', 0),
                'auc_roc': metrics_v2.get('auroc', 0),
                'f1_score': metrics_v2.get('f1', 0),
                'threshold': metrics_v2.get('threshold', 0.5)
            }
        }
        
        path_v2 = registry.save_model(
            'pathogenicity',
            'v2',
            model_v2,
            metadata=metadata_v2
        )
        logger.info(f"✅ Saved model v2 to {path_v2}")
        
        # Generate v3
        logger.info("\n" + "="*80)
        logger.info("GENERATING v3 MODEL")
        logger.info("="*80)
        # Generate v3
        logger.info("\n" + "="*80)
        logger.info("GENERATING v3 MODEL")
        logger.info("="*80)
        model_v3, metrics_v3, scaler_v3 = train_mock_model(random_state=456)
        
        # Save scaler for later use during inference
        scaler_v3_path = os.path.join(registry.models_dir, 'pathogenicity_v3_scaler.pkl')
        with open(scaler_v3_path, 'wb') as f:
            pickle.dump(scaler_v3, f)
        logger.info(f"✅ Saved scaler v3 to {scaler_v3_path}")
        
        path_v3 = registry.save_model(
            'pathogenicity',
            'v3',
            model_v3,
            metadata={
                'model_type': 'sklearn',
                'description': 'RandomForest pathogenicity classifier v3 with ensemble tuning and proper scaling',
                'features': [
                    'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                    'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                    'variant_type_encoded', 'aa_change_encoded'
                ],
                'scaler_path': scaler_v3_path,
                'performance': {
                    'accuracy': metrics_v3.get('sensitivity', 0),
                    'sensitivity': metrics_v3.get('sensitivity', 0),
                    'specificity': metrics_v3.get('specificity', 0),
                    'auc_roc': metrics_v3.get('auroc', 0),
                    'f1_score': metrics_v3.get('f1', 0),
                    'threshold': metrics_v3.get('threshold', 0.5)
                }
            }
        )
        logger.info(f"✅ Saved model v3 to {path_v3}")
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("MODEL GENERATION COMPLETE")
        logger.info("="*80)
        models = registry.list_models('pathogenicity')
        logger.info(f"Registered {len(models)} model versions:")
        for model in models:
            logger.info(f"  - {model['name']}:{model['version']} ({model['path']})")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to generate models: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    if generate_models():
        logger.info("Model generation complete")
        sys.exit(0)
    else:
        logger.error("Model generation failed")
        sys.exit(1)
