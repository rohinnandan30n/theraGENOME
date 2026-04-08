"""
TheraGenome ML Model Loader
============================
Loads pre-trained ML models from pickle files.
Falls back to mock models if files not found.
"""

import os
import pickle
from pathlib import Path
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = Path(__file__).parent.parent / "models"


def load_pickle_model(model_name: str) -> Optional[Any]:
    """Load a pickled model from disk"""
    model_path = MODELS_DIR / f"{model_name}.pkl"
    
    if not model_path.exists():
        logger.warning(f"Model not found: {model_path}")
        return None
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
            logger.info(f"✅ Loaded model: {model_name}")
            return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        return None


class PathogenicityPredictor:
    """Wrapper for pathogenicity prediction models"""
    
    def __init__(self):
        self.models = {
            "v1": load_pickle_model("pathogenicity_vv1"),
            "v2": load_pickle_model("pathogenicity_vv2"),
            "v3": load_pickle_model("pathogenicity_vv3"),
        }
        self.best_model = self.models.get("v3")  # Use latest version
    
    def predict(self, variant_features: dict[str, Any]) -> dict[str, Any]:
        """
        Predict pathogenicity of a variant.
        
        Falls back to rule-based scoring if model not available.
        """
        if self.best_model and hasattr(self.best_model, 'predict'):
            try:
                # Try to use the model
                result = self.best_model.predict(variant_features)
                return {
                    "pathogenicity": result,
                    "source": "ml_model",
                    "confidence": 0.85
                }
            except Exception as e:
                logger.warning(f"Model prediction failed: {e}. Using rule-based fallback.")
        
        # Rule-based fallback
        return self._rule_based_predict(variant_features)
    
    def _rule_based_predict(self, variant: dict[str, Any]) -> dict[str, Any]:
        """
        Rule-based pathogenicity prediction when ML model unavailable.
        Based on variant effect and ClinVar-like logic.
        """
        effect = variant.get("effect", "").lower()
        gene = variant.get("gene", "").lower()
        
        # More severe effects score higher
        severity_map = {
            "frameshift": 0.95,
            "nonsense": 0.9,
            "loss_of_function": 0.85,
            "gain_of_function": 0.75,
            "missense": 0.5,
            "splice": 0.8,
            "inframe": 0.6,
            "neutral": 0.1,
        }
        
        score = severity_map.get(effect, 0.3)
        
        # Adjust for known drug-metabolism genes
        if gene in ["cyp2d6", "cyp2c19", "tpmt", "hla"]:
            score = min(0.95, score + 0.1)
        
        # Convert score to category
        if score >= 0.8:
            pathogenicity = "pathogenic"
        elif score >= 0.6:
            pathogenicity = "likely_pathogenic"
        elif score >= 0.4:
            pathogenicity = "uncertain"
        elif score >= 0.2:
            pathogenicity = "likely_benign"
        else:
            pathogenicity = "benign"
        
        return {
            "pathogenicity": pathogenicity,
            "source": "rule_based",
            "confidence": min(0.95, 0.5 + (score * 0.45))  # 0.5-0.95 range
        }


# Global predictor instance
pathogenicity_predictor = PathogenicityPredictor()


def get_pathogenicity_prediction(variant: dict[str, Any]) -> tuple[str, float]:
    """
    Get pathogenicity prediction for a variant.
    
    Returns:
        (pathogenicity_class, confidence_score)
    """
    result = pathogenicity_predictor.predict(variant)
    return result["pathogenicity"], result["confidence"]
