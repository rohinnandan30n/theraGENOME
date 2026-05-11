from typing import Dict, Any, Tuple, Optional
import numpy as np
import logging
from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.model_manager import get_registry
from src.ml.interpreters import SHAPInterpreter
from src.ml.ensemble_classifier import EnsemblePathogenicityClassifier

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
        
        # Initialize ensemble classifier
        self.ensemble_classifier = EnsemblePathogenicityClassifier()
        self.use_ensemble = any(self.ensemble_classifier.models_loaded.values())
        
        # Load default model for fallback
        if not self.use_ensemble:
            self._load_model(default_version)
        
        logger.info(
            f"Pathogenicity classifier initialized. "
            f"Using ensemble: {self.use_ensemble}. Model: {model_name}:{default_version}"
        )
    
    def _load_model(self, version: str):
        """Load model and interpreter for fallback classification"""
        try:
            model = self.registry.load_model(self.model_name, version)
            self.current_model = model
            self.current_version = version
            
            # Initialize interpreter
            feature_names = self.preprocessor.get_feature_names()
            self.current_interpreter = SHAPInterpreter(model, feature_names)
            
            logger.info(f"Loaded model {self.model_name}:{version}")
        except Exception as e:
            logger.warning(f"Failed to load model {version}: {str(e)}. Will use ensemble or fallback only.")
            self.current_model = None
            self.current_version = None
            self.current_interpreter = None
    
    def classify(self, features: Dict[str, Any], version: str = None, 
                include_interpretation: bool = True) -> Dict[str, Any]:
        """
        Classify variant pathogenicity using ensemble or fallback method.
        
        Attempts to use the ensemble classifier with three models. Falls back to
        rule-based method if models are unavailable. Otherwise uses the original
        model-based approach.
        
        Args:
            features: Dictionary of variant features
            version: Model version to use (default: self.default_version)
            include_interpretation: Include SHAP-based feature importance
        
        Returns:
            Classification result with confidence and feature importance
        """
        try:
            # Try ensemble classification first if models are available
            if self.use_ensemble:
                return self._classify_with_ensemble(features, include_interpretation)
            
            # Fallback to original classification method
            return self._classify_with_model(features, version, include_interpretation)
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}", exc_info=True)
            raise
    
    def _classify_with_ensemble(self, features: Dict[str, Any], 
                               include_interpretation: bool = True) -> Dict[str, Any]:
        """Classify using ensemble of three models"""
        try:
            # Map features to ensemble format
            ensemble_features = self._map_features_to_ensemble(features)
            
            # Get ensemble prediction
            ensemble_result = self.ensemble_classifier.classify(ensemble_features)
            
            # Convert ensemble result to API response format
            probabilities = self._estimate_probabilities(ensemble_result)
            
            result = {
                'variant': self._format_variant_info(features),
                'classification': ensemble_result['classification'],
                'confidence': ensemble_result['confidence'],
                'probabilities': probabilities,
                'model_version': ensemble_result['model_version'],
                'thresholds': {
                    'pathogenic': 0.5,
                    'vus_lower': 0.3,
                    'vus_upper': 0.7
                }
            }
            
            # Add ensemble metadata
            if 'ensemble_details' in ensemble_result:
                result['ensemble_metadata'] = ensemble_result['ensemble_details']
            
            # Add interpretation if requested (fallback to simple feature importance)
            if include_interpretation:
                result['interpretation'] = self._generate_simple_interpretation(ensemble_features)
            
            return result
            
        except Exception as e:
            logger.warning(f"Ensemble classification failed: {str(e)}. Falling back to rule-based.")
            # Extract rule-based result if ensemble provides fallback info
            if hasattr(self, 'ensemble_classifier') and self.ensemble_classifier.fallback_enabled:
                ensemble_result = self.ensemble_classifier.classify(
                    self._map_features_to_ensemble(features)
                )
                return self._convert_ensemble_result_to_api_format(
                    ensemble_result, features, include_interpretation
                )
            raise
    
    def _classify_with_model(self, features: Dict[str, Any], version: str = None,
                            include_interpretation: bool = True) -> Dict[str, Any]:
        """Classify using the original model-based approach"""
        # Load different version if requested or if no model is currently loaded
        target_version = version or self.current_version or self.default_version
        
        if not self.current_model or (version and version != self.current_version):
            self._load_model(target_version)
        
        # If still no model, raise error
        if not self.current_model:
            raise RuntimeError(
                f"No classification model available. "
                f"Ensemble models not loaded and fallback model loading failed."
            )
        
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
        if include_interpretation and self.current_interpreter:
            try:
                interpretation = self.current_interpreter.explain(feature_vector, pathogenic_prob)
                result['interpretation'] = interpretation
            except Exception as e:
                logger.warning(f"Failed to generate interpretation: {str(e)}")
                result['interpretation'] = None
        
        return result
    
    def _map_features_to_ensemble(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map from API feature format to ensemble classifier format.
        
        Maps old feature names to new ensemble format:
        - CADD_score -> cadd_score
        - SIFT_score -> sift_score
        - PolyPhen_score -> polyphen2_score
        - gnomAD_freq -> gnomad_af
        - phyloP_score -> phylop_score
        - variant_type -> mutation_type (unchanged)
        """
        ensemble_features = {
            'cadd_score': features.get('CADD_score', 0.0),
            'sift_score': features.get('SIFT_score', 0.5),
            'polyphen2_score': features.get('PolyPhen_score', 0.0),
            'gnomad_af': features.get('gnomAD_freq', 0.0),
            'phylop_score': features.get('phyloP_score', 0.0),
            'mutation_type': features.get('variant_type', 'Unknown')
        }
        return ensemble_features
    
    def _estimate_probabilities(self, ensemble_result: Dict[str, Any]) -> Dict[str, float]:
        """Estimate class probabilities from ensemble result"""
        confidence = ensemble_result['confidence']
        classification = ensemble_result['classification']
        
        if classification == 'Pathogenic':
            return {
                'benign': 1.0 - confidence,
                'pathogenic': confidence
            }
        elif classification == 'Benign':
            return {
                'benign': confidence,
                'pathogenic': 1.0 - confidence
            }
        else:  # VUS
            return {
                'benign': 0.5,
                'pathogenic': 0.5
            }
    
    def _generate_simple_interpretation(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple feature importance based on feature values"""
        cadd = features.get('cadd_score', 0)
        sift = features.get('sift_score', 0.5)
        polyphen = features.get('polyphen2_score', 0)
        gnomad = features.get('gnomad_af', 0)
        
        importance = {}
        
        # Score each feature's contribution
        if cadd > 30:
            importance['cadd_score'] = {'importance': 'High', 'value': cadd}
        if sift < 0.05:
            importance['sift_score'] = {'importance': 'High', 'value': sift}
        if polyphen > 0.9:
            importance['polyphen2_score'] = {'importance': 'High', 'value': polyphen}
        if gnomad < 0.01:
            importance['gnomad_af'] = {'importance': 'Moderate', 'value': gnomad}
        
        return {
            'interpretation_method': 'ensemble_feature_heuristic',
            'top_features': importance
        }
    
    def _convert_ensemble_result_to_api_format(self, ensemble_result: Dict[str, Any],
                                              features: Dict[str, Any],
                                              include_interpretation: bool) -> Dict[str, Any]:
        """Convert ensemble result to API response format"""
        result = {
            'variant': self._format_variant_info(features),
            'classification': ensemble_result['classification'],
            'confidence': ensemble_result['confidence'],
            'probabilities': self._estimate_probabilities(ensemble_result),
            'model_version': ensemble_result['model_version'],
            'thresholds': {'pathogenic': 0.5, 'vus_lower': 0.3, 'vus_upper': 0.7}
        }
        
        if include_interpretation:
            ensemble_features = self._map_features_to_ensemble(features)
            result['interpretation'] = self._generate_simple_interpretation(ensemble_features)
        
        return result
    
    def batch_classify(self, variants_list: list, version: str = None) -> list:
        """
        Classify multiple variants in batch.
        
        Processes a list of variants and returns classification results for each.
        """
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
                    'classification': 'ERROR',
                    'confidence': 0.0,
                    'probabilities': {'benign': 0.5, 'pathogenic': 0.5},
                    'model_version': 'error'
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
