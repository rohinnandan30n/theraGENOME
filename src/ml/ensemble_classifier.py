"""
Ensemble classifier for pathogenicity prediction using multiple XGBoost/scikit-learn models.
Loads three pre-trained models and combines their predictions via majority voting.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging
import joblib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level flag indicating fallback rule-based classification is being used
USING_FALLBACK = False


class EnsemblePathogenicityClassifier:
    """Ensemble classifier using three pre-trained models with majority voting"""
    
    MODEL_PATHS = {
        'v1': './models/pathogenicity_v1.pkl',
        'v2': './models/pathogenicity_v2.pkl',
        'v3': './models/pathogenicity_v3.pkl'
    }
    
    # Feature keys expected from user input
    REQUIRED_INPUT_FEATURES = {
        'cadd_score',
        'sift_score',
        'polyphen2_score',
        'gnomad_af',
        'phylop_score',
        'mutation_type'
    }
    
    def __init__(self, models_base_path: str = None):
        """
        Initialize ensemble classifier.
        
        Args:
            models_base_path: Base path for model files (default: ./models/)
        """
        global USING_FALLBACK
        
        self.loaded_models = []  # List of (path, model) tuples for successfully loaded models
        self.models = {}
        self.models_loaded = {}
        self.fallback_enabled = False
        self.models_base_path = models_base_path or './models/'
        
        # Build model paths
        self.MODEL_PATHS = [
            os.path.join(self.models_base_path, 'pathogenicity_v1.pkl'),
            os.path.join(self.models_base_path, 'pathogenicity_v2.pkl'),
            os.path.join(self.models_base_path, 'pathogenicity_v3.pkl'),
        ]
        
        # Try alternate naming convention too
        self.ALTERNATE_MODEL_PATHS = [
            os.path.join(self.models_base_path, 'pathogenicity_vv1.pkl'),
            os.path.join(self.models_base_path, 'pathogenicity_vv2.pkl'),
            os.path.join(self.models_base_path, 'pathogenicity_vv3.pkl'),
        ]
        
        # Load all models at startup with resilient error handling
        self._load_models_resilient()
        
        # Determine operation mode
        models_count = len(self.loaded_models)
        if models_count >= 2:
            logger.info(
                f"Ensemble classifier initialized with {models_count} models. "
                f"Using ensemble voting (majority vote)."
            )
        elif models_count == 1:
            logger.warning(
                f"Ensemble classifier initialized with degraded mode: "
                f"only 1 of {len(self.MODEL_PATHS)} models loaded. "
                f"Using single model for prediction."
            )
            self.fallback_enabled = False  # Single model is still valid
        else:
            logger.critical(
                "CRITICAL: No models loaded. "
                "Falling back to rule-based classification method."
            )
            self.fallback_enabled = True
            USING_FALLBACK = True
    
    def _load_models_resilient(self):
        """
        Load models with resilient error handling.
        
        Wraps each model load in try/except, validates feature count,
        and collects successfully loaded models.
        """
        for i, path in enumerate(self.MODEL_PATHS):
            try:
                # Try primary path
                abs_path = os.path.abspath(path)
                
                # If primary path doesn't exist, try alternate naming
                if not os.path.exists(abs_path):
                    alt_path = os.path.abspath(self.ALTERNATE_MODEL_PATHS[i])
                    if os.path.exists(alt_path):
                        abs_path = alt_path
                        logger.debug(f"Using alternate path for model {i+1}: {alt_path}")
                
                if not os.path.exists(abs_path):
                    logger.warning(f"Model file not found: {abs_path}")
                    continue
                
                # Load model
                model = joblib.load(abs_path)
                logger.debug(f"Loaded model from {abs_path}")
                
                # Validate feature count immediately after loading
                try:
                    test_input = np.zeros((1, 10))  # 10 = EXPECTED_FEATURE_COUNT
                    _ = model.predict(test_input)
                    logger.debug(f"Model validation passed (accepts 10 features)")
                except Exception as val_e:
                    logger.warning(
                        f"Model validation failed ({abs_path}): {val_e}. "
                        f"Model may expect different feature count."
                    )
                    raise
                
                # Success: add to loaded models
                self.loaded_models.append((abs_path, model))
                self.models[f'v{i+1}'] = model
                self.models_loaded[f'v{i+1}'] = True
                logger.info(f"Model loaded and validated: {abs_path}")
                
            except Exception as e:
                version = f'v{i+1}'
                self.models_loaded[version] = False
                logger.warning(f"Model failed to load or validate (v{i+1}): {e}")

    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get current model loading and health status.
        
        Returns:
            Dict with model count, expected models, fallback status, and loaded paths
        """
        return {
            "models_loaded": len(self.loaded_models),
            "models_expected": len(self.MODEL_PATHS),
            "using_fallback": USING_FALLBACK or self.fallback_enabled,
            "loaded_paths": [p for p, _ in self.loaded_models]
        }
    
    def classify(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify variant pathogenicity using ensemble of models.
        
        Args:
            features: Dictionary with keys: cadd_score, sift_score, polyphen2_score,
                     gnomad_af, phylop_score, mutation_type
        
        Returns:
            Dict with keys: classification, confidence, model_version, flags
        """
        # Validate input features
        self._validate_input_features(features)
        
        # If no models loaded or all failed, use fallback rule-based method
        if self.fallback_enabled or len(self.loaded_models) == 0:
            logger.warning(
                "Using fallback rule-based classification method "
                "(no models available)"
            )
            result = self._fallback_rule_based_classification(features)
            result['flags'] = ['rule_based_fallback']
            # Cap confidence at 0.60 for fallback
            result['confidence'] = min(0.60, result.get('confidence', 0.60))
            return result
        
        try:
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)
            
            # Run inference on loaded models
            predictions = []
            confidences = []
            
            for version_key in sorted(self.models.keys()):
                if not self.models_loaded.get(version_key, False):
                    continue
                
                try:
                    model = self.models[version_key]
                    
                    # Get predictions - handle both direct prediction and probability
                    if hasattr(model, 'predict_proba'):
                        # Get probability for positive class
                        prob = model.predict_proba([feature_vector])[0]
                        if len(prob) == 2:
                            pred = 1 if prob[1] > 0.5 else 0  # Pathogenic: 1, Benign: 0
                            confidence = prob[1]
                        else:
                            pred = np.argmax(prob)
                            confidence = np.max(prob)
                    else:
                        # Direct prediction
                        pred = int(model.predict([feature_vector])[0])
                        confidence = 0.5  # Default confidence for models without probability
                    
                    predictions.append(pred)
                    confidences.append(confidence)
                    
                    logger.debug(f"Model {version_key}: prediction={pred}, confidence={confidence:.3f}")
                    
                except Exception as e:
                    logger.warning(f"Error during prediction with model {version_key}: {str(e)}")
                    continue
            
            # If all predictions failed, fallback to rule-based
            if not predictions:
                logger.warning(
                    "All model predictions failed. "
                    "Falling back to rule-based classification."
                )
                result = self._fallback_rule_based_classification(features)
                result['flags'] = ['rule_based_fallback']
                result['confidence'] = min(0.60, result.get('confidence', 0.60))
                return result
            
            # Determine how many models we have
            models_count = len(self.loaded_models)
            
            if models_count >= 2:
                # Ensemble voting: majority vote for classification
                votes = np.array(predictions)
                majority_pred = 1 if np.sum(votes >= 0.5) > len(votes) / 2 else 0
            else:
                # Single model: use its prediction directly
                majority_pred = predictions[0]
            
            # Mean confidence
            mean_confidence = float(np.mean(confidences))
            
            # Convert prediction to label
            classification = 'Pathogenic' if majority_pred == 1 else 'Benign'
            
            # Build flags list
            flags = []
            if models_count == 1:
                flags.append('degraded_mode')  # Only 1 model available
            
            result = {
                'classification': classification,
                'confidence': mean_confidence,
                'model_version': 'ensemble_v1-3' if models_count >= 2 else 'single_model',
                'ensemble_details': {
                    'predictions': [int(p) for p in predictions],
                    'confidences': [float(c) for c in confidences],
                    'majority_vote': int(majority_pred),
                    'models_used': [v for v in sorted(self.models.keys()) if self.models_loaded.get(v, False)],
                    'models_count': models_count
                },
                'flags': flags
            }
            
            logger.info(
                f"Ensemble classification: {classification} "
                f"(confidence={mean_confidence:.3f}, models={models_count})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ensemble classification failed: {str(e)}", exc_info=True)
            logger.warning("Falling back to rule-based classification")
            result = self._fallback_rule_based_classification(features)
            result['flags'] = ['rule_based_fallback', 'error_recovery']
            result['confidence'] = min(0.60, result.get('confidence', 0.60))
            return result
    
    def _validate_input_features(self, features: Dict[str, Any]):
        """Validate that input features contain all required keys"""
        missing = self.REQUIRED_INPUT_FEATURES - set(features.keys())
        if missing:
            raise ValueError(
                f"Missing required features: {missing}. "
                f"Expected keys: {self.REQUIRED_INPUT_FEATURES}"
            )
        
        # Validate feature ranges
        if not (0 <= features['cadd_score'] <= 99):
            raise ValueError(f"cadd_score out of range: {features['cadd_score']} (0-99)")
        if not (0 <= features['sift_score'] <= 1):
            raise ValueError(f"sift_score out of range: {features['sift_score']} (0-1)")
        if not (0 <= features['polyphen2_score'] <= 1):
            raise ValueError(f"polyphen2_score out of range: {features['polyphen2_score']} (0-1)")
        if not (0 <= features['gnomad_af'] <= 1):
            raise ValueError(f"gnomad_af out of range: {features['gnomad_af']} (0-1)")
        if not (-14 <= features['phylop_score'] <= 6):
            raise ValueError(f"phylop_score out of range: {features['phylop_score']} (-14 to 6)")
    
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Convert input features to model feature vector.
        
        Maps user input keys to model expected format (10 features).
        Returns feature vector with: 
        1-5: CADD, SIFT, PolyPhen, gnomAD, phyloP (scores)
        6: mutation_type (encoded)
        7: domain_annotation
        8: regulatory_region_flag
        9: splice_site_impact
        10: functional_prediction
        """
        # Get numeric score features
        cadd = float(features.get('cadd_score', 0.0)) / 99.0  # Normalize CADD
        sift = float(features.get('sift_score', 0.5))
        polyphen = float(features.get('polyphen2_score', 0.5))
        gnomad = float(features.get('gnomad_af', 0.0))
        phylop = (float(features.get('phylop_score', 0.0)) + 14.0) / 20.0  # Normalize phyloP
        mutation_encoded = self._encode_mutation_type(features.get('mutation_type', 'Unknown'))
        
        # Clamp all scores to [0, 1]
        cadd = max(0.0, min(1.0, cadd))
        sift = max(0.0, min(1.0, sift))
        polyphen = max(0.0, min(1.0, polyphen))
        gnomad = max(0.0, min(1.0, gnomad))
        phylop = max(0.0, min(1.0, phylop))
        
        # Compute new features
        # Feature 7: domain_annotation
        gene = features.get('gene', 'Unknown')
        position = int(features.get('position', 0)) if 'position' in features else 0
        domain_regions = {"TP53": [(102, 292)], "BRCA1": [(1, 1863)]}
        domain_annotation = 0.0
        if gene in domain_regions:
            try:
                for start, end in domain_regions[gene]:
                    if start <= position <= end:
                        domain_annotation = 1.0
                        break
            except (ValueError, TypeError):
                domain_annotation = 0.0
        
        # Feature 8: regulatory_region_flag
        regulatory_region_flag = float(features.get('is_regulatory', False))
        
        # Feature 9: splice_site_impact
        mutation_type = features.get('mutation_type', '')
        splice_site_impact = 1.0 if 'splice' in str(mutation_type).lower() else 0.0
        
        # Feature 10: functional_prediction (composite of SIFT, PolyPhen, CADD)
        functional_prediction = (sift + polyphen + cadd) / 3.0
        functional_prediction = max(0.0, min(1.0, functional_prediction))
        
        # Create feature vector in expected order
        feature_vector = np.array([
            cadd,
            sift,
            polyphen,
            gnomad,
            phylop,
            mutation_encoded,
            domain_annotation,
            regulatory_region_flag,
            splice_site_impact,
            functional_prediction
        ], dtype=np.float32)
        
        return feature_vector
    
    def _encode_mutation_type(self, mutation_type: str) -> float:
        """Encode mutation type as numeric value"""
        encoding_map = {
            'SNP': 0.0,
            'Deletion': 1.0,
            'Insertion': 2.0,
            'Substitution': 3.0,
            'InDel': 4.0,
            'Unknown': 5.0
        }
        return encoding_map.get(mutation_type, 5.0)
    
    def _fallback_rule_based_classification(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback rule-based classification when models are unavailable.
        
        Uses heuristic rules based on variant scores.
        Confidence is capped at 0.60 to signal unreliability.
        """
        logger.critical(
            "CRITICAL WARNING: Using fallback rule-based classification. "
            "Model files were not available at startup."
        )
        
        cadd_score = features.get('cadd_score', 0)
        sift_score = features.get('sift_score', 0)
        polyphen2_score = features.get('polyphen2_score', 0)
        gnomad_af = features.get('gnomad_af', 0)
        
        # Simple rule-based logic
        pathogenic_score = 0
        
        # CADD score contribution
        if cadd_score > 30:
            pathogenic_score += 2
        elif cadd_score > 20:
            pathogenic_score += 1
        
        # SIFT score contribution (lower is more deleterious)
        if sift_score < 0.05:
            pathogenic_score += 2
        elif sift_score < 0.1:
            pathogenic_score += 1
        
        # PolyPhen2 score contribution (higher is more pathogenic)
        if polyphen2_score > 0.9:
            pathogenic_score += 2
        elif polyphen2_score > 0.7:
            pathogenic_score += 1
        
        # gnomAD frequency (rarer variants more likely pathogenic)
        if gnomad_af < 0.01:
            pathogenic_score += 1
        elif gnomad_af > 0.05:
            pathogenic_score -= 1
        
        # Classify based on accumulated score
        if pathogenic_score >= 3:
            classification = 'Pathogenic'
            confidence = min(0.60, 0.4 + (pathogenic_score * 0.15))
        elif pathogenic_score <= -1:
            classification = 'Benign'
            confidence = min(0.60, 0.4 + abs(pathogenic_score) * 0.15)
        else:
            classification = 'VUS'
            confidence = 0.50
        
        return {
            'classification': classification,
            'confidence': float(confidence),
            'model_version': 'fallback_rule-based',
            'fallback': True,
            'rule_score': pathogenic_score,
            'flags': []  # Will be populated by caller
        }
