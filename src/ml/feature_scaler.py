"""
Feature Scaler with Statistics Capture
Properly fits scaler on training data only to prevent data leakage
"""
import numpy as np
import json
import os
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class FeatureScaler:
    """
    Learns scaling parameters from training data and applies them consistently.
    CRITICAL: fit() must only be called on training data to prevent leakage.
    """
    
    def __init__(self, feature_names=None):
        self.feature_names = feature_names or [f"feature_{i}" for i in range(10)]
        self.scaler = StandardScaler()
        self.is_fit = False
        self.train_mean = None
        self.train_std = None
        self.train_min = None
        self.train_max = None
    
    def fit(self, X_train):
        """
        FIT ONLY ON TRAINING DATA - NEVER on test or full dataset!
        Captures statistics that will be used for all scaling.
        """
        if self.is_fit:
            logger.warning("⚠️  Scaler already fit! Refitting will corrupt learned parameters.")
        
        # Fit StandardScaler on training data only
        self.scaler.fit(X_train)
        
        # Capture statistics for diagnostic purposes
        self.train_mean = np.mean(X_train, axis=0)
        self.train_std = np.std(X_train, axis=0)
        self.train_min = np.min(X_train, axis=0)
        self.train_max = np.max(X_train, axis=0)
        
        self.is_fit = True
        
        logger.info(f"✅ Scaler fit on {X_train.shape[0]} training samples, {X_train.shape[1]} features")
        logger.info(f"   Train mean: {self.train_mean}")
        logger.info(f"   Train std:  {self.train_std}")
        
        return self
    
    def transform(self, X):
        """
        Apply learned scaling to new data (train or test).
        This ONLY transforms - never refits.
        """
        if not self.is_fit:
            raise ValueError("❌ Scaler not fit yet. Call fit(X_train) first!")
        
        X_scaled = self.scaler.transform(X)
        
        # Optional: detect and warn about out-of-range values
        out_of_range_mask = (X < self.train_min) | (X > self.train_max)
        n_out_of_range = np.sum(out_of_range_mask)
        if n_out_of_range > 0:
            pct = (n_out_of_range / X.size) * 100
            logger.warning(f"⚠️  {pct:.1f}% of features are out-of-training-range")
        
        return X_scaled
    
    def fit_transform(self, X_train):
        """Fit and transform in one step (train data only!)"""
        self.fit(X_train)
        return self.transform(X_train)
    
    def save_statistics(self, path):
        """Save learned statistics to JSON for inspection"""
        stats = {
            'train_mean': self.train_mean.tolist() if self.train_mean is not None else None,
            'train_std': self.train_std.tolist() if self.train_std is not None else None,
            'train_min': self.train_min.tolist() if self.train_min is not None else None,
            'train_max': self.train_max.tolist() if self.train_max is not None else None,
            'feature_names': self.feature_names,
            'is_fit': self.is_fit
        }
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Saved scaler statistics to {path}")
    
    def get_statistics(self):
        """Get statistics dict for diagnostics"""
        return {
            'mean': self.train_mean,
            'std': self.train_std,
            'min': self.train_min,
            'max': self.train_max
        }
