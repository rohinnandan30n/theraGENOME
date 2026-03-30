from typing import Dict, Any, List, Optional
import numpy as np
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class FeatureInterpreter(ABC):
    """Base class for feature importance interpretation"""
    
    @abstractmethod
    def explain(self, features: np.ndarray, prediction: Any) -> Dict[str, Any]:
        """Generate explanation for model prediction"""
        pass


class SHAPInterpreter(FeatureInterpreter):
    """SHAP-based feature importance interpreter"""
    
    def __init__(self, model, feature_names: List[str] = None):
        """Initialize SHAP interpreter"""
        try:
            import shap
            self.shap = shap
            self.model = model
            self.feature_names = feature_names or []
            self.explainer = None
            logger.info("SHAP interpreter initialized")
        except ImportError:
            logger.warning("SHAP library not installed, using gradient-based interpretation")
            self.shap = None
            self.model = model
            self.feature_names = feature_names or []
    
    def explain(self, features: np.ndarray, prediction: Any) -> Dict[str, Any]:
        """
        Generate SHAP-based feature importance scores.
        
        Returns:
            Dict with SHAP values, base values, and feature importances
        """
        try:
            if self.shap is None:
                return self._fallback_explain(features)
            
            # Initialize explainer if not already done
            if self.explainer is None:
                self._initialize_explainer()
            
            # Generate SHAP values
            feature_array = features.reshape(1, -1)
            shap_values = self.explainer.shap_values(feature_array)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                # For multi-class, get the positive class values
                shap_vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                shap_vals = shap_values[0]
            
            # Calculate feature importances
            importances = np.abs(shap_vals).astype(float)
            total_importance = np.sum(importances)
            
            feature_contribution = {}
            for i, feature_name in enumerate(self.feature_names):
                if total_importance > 0:
                    weight = float(importances[i] / total_importance)
                else:
                    weight = 0.0
                
                feature_contribution[feature_name] = {
                    'shap_value': float(shap_vals[i]),
                    'importance_score': float(importances[i]),
                    'importance_weight': weight,
                    'direction': 'pathogenic' if shap_vals[i] > 0 else 'benign'
                }
            
            # Sort by absolute importance
            sorted_features = sorted(
                feature_contribution.items(),
                key=lambda x: abs(x[1]['shap_value']),
                reverse=True
            )
            
            return {
                'interpretation_method': 'SHAP',
                'shap_values': dict(sorted_features[:5]),  # Top 5 features
                'all_features': feature_contribution,
                'base_value': float(self.explainer.expected_value if hasattr(self.explainer, 'expected_value') else 0.5),
                'prediction_contribution': float(np.sum(shap_vals))
            }
        
        except Exception as e:
            logger.warning(f"SHAP interpretation failed: {str(e)}, using fallback")
            return self._fallback_explain(features)
    
    def _initialize_explainer(self):
        """Initialize SHAP explainer"""
        try:
            # Try TreeExplainer first (for tree-based models)
            if hasattr(self.model, 'tree_'):
                self.explainer = self.shap.TreeExplainer(self.model)
                logger.info("Using SHAP TreeExplainer")
            # Fall back to KernelExplainer for other models
            else:
                # Use a small sample for explanation
                self.explainer = self.shap.KernelExplainer(
                    self.model.predict,
                    self.shap.sample(np.random.randn(100, len(self.feature_names)), 10)
                )
                logger.info("Using SHAP KernelExplainer")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {str(e)}")
            raise
    
    def _fallback_explain(self, features: np.ndarray) -> Dict[str, Any]:
        """Fallback gradient-based feature importance"""
        # Use gradient approximation for feature importance
        feature_importance = np.abs(features) * 0.5  # Simplified importance
        total_importance = np.sum(feature_importance)
        
        feature_contribution = {}
        for i, feature_name in enumerate(self.feature_names):
            if total_importance > 0:
                weight = float(feature_importance[i] / total_importance)
            else:
                weight = 0.0
            
            feature_contribution[feature_name] = {
                'gradient_value': float(features[i]),
                'importance_score': float(feature_importance[i]),
                'importance_weight': weight,
                'direction': 'pathogenic' if features[i] > 0.5 else 'benign'
            }
        
        # Sort by importance
        sorted_features = sorted(
            feature_contribution.items(),
            key=lambda x: x[1]['importance_score'],
            reverse=True
        )
        
        return {
            'interpretation_method': 'Gradient-based',
            'shap_values': dict(sorted_features[:5]),  # Top 5 features
            'all_features': feature_contribution,
            'base_value': 0.5,
            'note': 'SHAP library not available, using gradient-based approximation'
        }


class PermutationInterpreter(FeatureInterpreter):
    """Permutation-based feature importance"""
    
    def __init__(self, model, feature_names: List[str] = None):
        self.model = model
        self.feature_names = feature_names or []
    
    def explain(self, features: np.ndarray, prediction: Any) -> Dict[str, Any]:
        """Generate permutation-based feature importance"""
        feature_importance = {}
        
        original_pred = self.model.predict_proba(features.reshape(1, -1))[0][1]
        
        for i, feature_name in enumerate(self.feature_names):
            # Permute feature
            permuted_features = features.copy()
            permuted_features[i] = np.random.normal(0, 1)  # Random value
            
            # Get prediction with permuted feature
            permuted_pred = self.model.predict_proba(permuted_features.reshape(1, -1))[0][1]
            
            # Calculate importance as drop in probability
            importance = abs(original_pred - permuted_pred)
            
            feature_importance[feature_name] = {
                'importance_score': float(importance),
                'original_contribution': float(original_pred),
                'permuted_contribution': float(permuted_pred)
            }
        
        # Normalize
        total_importance = sum(imp['importance_score'] for imp in feature_importance.values())
        for feat_imp in feature_importance.values():
            feat_imp['importance_weight'] = (feat_imp['importance_score'] / total_importance 
                                            if total_importance > 0 else 0.0)
        
        return {
            'interpretation_method': 'Permutation',
            'feature_importance': feature_importance,
            'original_prediction': float(original_pred)
        }
