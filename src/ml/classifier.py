from typing import Dict, Any, Tuple, Optional
import numpy as np
import logging
from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.model_manager import get_registry
from src.ml.interpreters import SHAPInterpreter

logger = logging.getLogger(__name__)


class PathogenicityClassifier:
    """Unified interface for pathogenicity classification"""
    
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
        
        # Load default model
        self._load_model(default_version)
        logger.info(f"Pathogenicity classifier initialized with {model_name}:{default_version}")
    
    def _load_model(self, version: str):
        """Load model and interpreter"""
        try:
            model = self.registry.load_model(self.model_name, version)
            self.current_model = model
            self.current_version = version
            
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
            
            # Preprocess features
            feature_vector = self.preprocessor.preprocess(features)
            
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
            
            # Determine classification
            thresholds = self.CLASSIFICATION_THRESHOLDS.get(self.current_version, 
                                                           self.CLASSIFICATION_THRESHOLDS['v2'])
            
            if pathogenic_prob >= thresholds['pathogenic']:
                classification = 'Pathogenic'
                confidence = pathogenic_prob
            elif pathogenic_prob <= (1 - thresholds['pathogenic']):
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
                'thresholds': thresholds
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
