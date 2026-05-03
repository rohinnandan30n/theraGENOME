#!/usr/bin/env python3
"""
Generate mock pre-trained models for testing.

Creates sklearn models for pathogenicity classification and registers them.
"""

import sys
import os
import logging
from sklearn.ensemble import RandomForestClassifier
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.model_manager import get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train_mock_model(random_state: int = 42) -> RandomForestClassifier:
    """Train a mock RF model"""
    # Create synthetic training data
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    # Create labels with some pattern
    y = (X[:, 0] + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.5 > 0).astype(int)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=random_state, max_depth=10)
    model.fit(X, y)
    
    logger.info(f"Trained RandomForest with {n_samples} samples")
    return model


def generate_models():
    """Generate and register mock models"""
    try:
        registry = get_registry()
        
        # Generate v1
        logger.info("Generating v1 model...")
        model_v1 = train_mock_model(random_state=42)
        
        path_v1 = registry.save_model(
            'pathogenicity',
            'v1',
            model_v1,
            metadata={
                'model_type': 'sklearn',
                'description': 'RandomForest baseline pathogenicity classifier v1',
                'features': [
                    'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                    'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                    'variant_type_encoded', 'aa_change_encoded'
                ],
                'performance': {
                    'accuracy': 0.82,
                    'sensitivity': 0.78,
                    'specificity': 0.85,
                    'auc_roc': 0.89
                }
            }
        )
        logger.info(f"Saved model v1 to {path_v1}")
        
        # Generate v2
        logger.info("Generating v2 model...")
        model_v2 = train_mock_model(random_state=123)
        
        path_v2 = registry.save_model(
            'pathogenicity',
            'v2',
            model_v2,
            metadata={
                'model_type': 'sklearn',
                'description': 'RandomForest pathogenicity classifier v2 with improved features',
                'features': [
                    'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                    'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                    'variant_type_encoded', 'aa_change_encoded'
                ],
                'performance': {
                    'accuracy': 0.86,
                    'sensitivity': 0.83,
                    'specificity': 0.88,
                    'auc_roc': 0.92
                }
            }
        )
        logger.info(f"Saved model v2 to {path_v2}")
        
        # Generate v3
        logger.info("Generating v3 model...")
        model_v3 = train_mock_model(random_state=456)
        
        path_v3 = registry.save_model(
            'pathogenicity',
            'v3',
            model_v3,
            metadata={
                'model_type': 'sklearn',
                'description': 'RandomForest pathogenicity classifier v3 with ensemble tuning',
                'features': [
                    'phyloP_score', 'SIFT_score', 'PolyPhen_score', 'CADD_score',
                    'gnomAD_freq', 'REVEL_score', 'MutationTaster_score', 'FathmM_score',
                    'variant_type_encoded', 'aa_change_encoded'
                ],
                'performance': {
                    'accuracy': 0.89,
                    'sensitivity': 0.87,
                    'specificity': 0.90,
                    'auc_roc': 0.95
                }
            }
        )
        logger.info(f"Saved model v3 to {path_v3}")
        
        # List registered models
        models = registry.list_models('pathogenicity')
        logger.info(f"Registered {len(models)} model versions:")
        for model in models:
            logger.info(f"  - {model['name']}:{model['version']} ({model['path']})")
    
    except Exception as e:
        logger.error(f"Failed to generate models: {str(e)}", exc_info=True)
        return False
    
    return True


if __name__ == "__main__":
    if generate_models():
        logger.info("Model generation complete")
        sys.exit(0)
    else:
        logger.error("Model generation failed")
        sys.exit(1)
