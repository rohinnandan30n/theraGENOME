from typing import Dict, Any, Tuple, Optional
import numpy as np
import pickle
import logging
import os
from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.model_manager import get_registry
from src.ml.interpreters import SHAPInterpreter

logger = logging.getLogger(__name__)


class PathogenicityClassifier:
    """Unified interface for pathogenicity classification"""
    
    # Fallback thresholds if metadata not available
    CLASSIFICATION_THRESHOLDS = {
        'v1': {'pathogenic': 0.7, 'vus_lower': 0.4, 'vus_upper': 0.7},
        'v2': {'pathogenic': 0.75, 'vus_lower': 0.35, 'vus_upper': 0.75},
        'v3': {'pathogenic': 0.8, 'vus_lower': 0.3, 'vus_upper': 0.8}
    }
    
    def __init__(self, model_name: str = 'pathogenicity', default_version: str = 'v2'):
        """Initialize classifier"""
        self.model_name = model_name
        self.default_version = default_version
        self.preprocessor = FeaturePreprocessor()
        self.registry = get_registry()
        self.current_model = None
        self.current_version = None
        self.current_interpreter = None
        self.current_threshold = None
        self.current_scaler = None  # ✅ Feature scaler
        
        # Load default model
        self._load_model(default_version)
        logger.info(f"Pathogenicity classifier initialized with {model_name}:{default_version}")
    
    def _load_model(self, version: str):
        """Load model, interpreter, threshold, and scaler from metadata"""
        try:
            model = self.registry.load_model(self.model_name, version)
            self.current_model = model
            self.current_version = version
            
            # Load threshold and scaler from metadata
            model_info = self.registry.get_model_info(self.model_name, version)
            if model_info and 'performance' in model_info and 'threshold' in model_info['performance']:
                self.current_threshold = model_info['performance']['threshold']
                logger.info(f"Loaded optimized threshold for {version}: {self.current_threshold:.4f}")
            else:
                # Fallback: compute midpoint threshold if metadata unavailable
                default_thresholds = self.CLASSIFICATION_THRESHOLDS.get(version, self.CLASSIFICATION_THRESHOLDS['v2'])
                self.current_threshold = default_thresholds['pathogenic']
                logger.warning(f"Metadata threshold not found, using fallback: {self.current_threshold:.4f}")
            
            # Load scaler if available
            if model_info and 'scaler_path' in model_info:
                scaler_path = model_info['scaler_path']
                if os.path.exists(scaler_path):
                    try:
                        with open(scaler_path, 'rb') as f:
                            self.current_scaler = pickle.load(f)
                        logger.info(f"Loaded feature scaler for {version} from {scaler_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load scaler: {e}, will use raw features")
                        self.current_scaler = None
                else:
                    logger.warning(f"Scaler file not found: {scaler_path}, will use raw features")
                    self.current_scaler = None
            else:
                logger.warning(f"No scaler path in metadata, will use raw features")
                self.current_scaler = None
            
            # Initialize interpreter
            feature_names = self.preprocessor.get_feature_names()
            self.current_interpreter = SHAPInterpreter(model, feature_names)
            
            logger.info(f"Loaded model {self.model_name}:{version}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def classify(self, features: Dict[str, Any], version: str = None, 
                include_interpretation: bool = True) -> Dict[str, Any]:
        """
        Classify variant pathogenicity.
        
        Args:
            features: Dictionary of variant features
            version: Model version to use (default: self.default_version)
            include_interpretation: Include SHAP-based feature importance
        
        Returns:
            Classification result with confidence and feature importance
        """
        try:
            # Load different version if requested
            if version and version != self.current_version:
                self._load_model(version)
            
            # Preprocess features to get raw vector
            feature_vector = self.preprocessor.preprocess(features)
            
            # Apply scaler if available (prevents distribution shift)
            if self.current_scaler is not None:
                try:
                    feature_vector = self.current_scaler.transform(feature_vector.reshape(1, -1))[0]
                    logger.debug(f"Applied scaler to features: {feature_vector[:3]}...")
                except Exception as e:
                    logger.warning(f"Failed to apply scaler: {e}, using raw features")
            
            # Get prediction
            if hasattr(self.current_model, 'predict_proba'):
                probabilities = self.current_model.predict_proba(feature_vector.reshape(1, -1))[0]
                benign_prob = float(probabilities[0])
                pathogenic_prob = float(probabilities[1])
            else:
                # For binary classifiers without predict_proba
                prediction = self.current_model.predict(feature_vector.reshape(1, -1))[0]
                pathogenic_prob = float(prediction)
                benign_prob = 1.0 - pathogenic_prob
            
            # Determine classification using optimized threshold
            # Use threshold from model metadata (set during training)
            optimal_threshold = self.current_threshold if self.current_threshold else 0.5
            
            # VUS thresholds (band around the optimal threshold)
            vus_margin = 0.15  # ±15% margin around threshold
            vus_lower = max(0.0, optimal_threshold - vus_margin)
            vus_upper = min(1.0, optimal_threshold + vus_margin)
            
            if pathogenic_prob >= optimal_threshold + vus_margin:
                classification = 'Pathogenic'
                confidence = pathogenic_prob
            elif pathogenic_prob <= optimal_threshold - vus_margin:
                classification = 'Benign'
                confidence = benign_prob
            else:
                classification = 'VUS'  # Variant of Uncertain Significance
                confidence = min(pathogenic_prob, benign_prob)
            
            result = {
                'variant': self._format_variant_info(features),
                'classification': classification,
                'confidence': confidence,
                'probabilities': {
                    'benign': benign_prob,
                    'pathogenic': pathogenic_prob
                },
                'model_version': self.current_version,
                'thresholds': {
                    'optimal': optimal_threshold,
                    'vus_lower': vus_lower,
                    'vus_upper': vus_upper
                }
            }
            
            # Add interpretation if requested
            if include_interpretation:
                try:
                    interpretation = self.current_interpreter.explain(feature_vector, pathogenic_prob)
                    result['interpretation'] = interpretation
                except Exception as e:
                    logger.warning(f"Failed to generate interpretation: {str(e)}")
                    result['interpretation'] = None
            
            return result
        
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}", exc_info=True)
            raise
    
    def batch_classify(self, variants_list: list, version: str = None) -> list:
        """Classify multiple variants"""
        results = []
        for variant in variants_list:
            try:
                result = self.classify(variant, version, include_interpretation=False)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to classify variant: {str(e)}")
                results.append({
                    'variant': variant,
                    'error': str(e),
                    'classification': 'ERROR'
                })
        
        return results
    
    def _format_variant_info(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Format variant information"""
        return {
            'chrom': features.get('chrom'),
            'pos': features.get('pos'),
            'ref': features.get('ref'),
            'alt': features.get('alt'),
            'gene_symbol': features.get('gene_symbol'),
            'amino_acid_change': features.get('amino_acid_change')
        }
    
    def get_model_info(self, version: str = None) -> Dict[str, Any]:
        """Get model metadata"""
        v = version or self.current_version
        return self.registry.get_model_info(self.model_name, v)
    
    def list_available_models(self) -> list:
        """List all available model versions"""
        return self.registry.list_models(self.model_name)
