from typing import Dict, Any, List, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeaturePreprocessor:
    """Preprocess variant features for ML model input"""
    
    # Feature columns expected by the model
    REQUIRED_FEATURES = [
        'phyloP_score',           # Evolutionary conservation
        'SIFT_score',             # Protein impact prediction
        'PolyPhen_score',         # Protein impact prediction
        'CADD_score',             # Combined pathogenicity score
        'gnomAD_freq',            # Population frequency
        'REVEL_score',            # Ensemble pathogenicity
        'MutationTaster_score',   # Mutation impact
        'FathmM_score',           # Functional impact
        'variant_type',           # SNP, Indel, etc.
        'amino_acid_change'       # Protein-level change
    ]
    
    CATEGORICAL_FEATURES = ['variant_type', 'amino_acid_change']
    
    # Categorical feature encodings
    VARIANT_TYPE_ENCODING = {
        'SNP': 0,
        'Deletion': 1,
        'Insertion': 2,
        'Substitution': 3,
        'InDel': 4,
        'Unknown': 5
    }
    
    AA_CHANGE_ENCODING = {}  # Can be expanded with 20 amino acids
    
    def __init__(self):
        """Initialize feature preprocessor"""
        # Build amino acid encoding
        amino_acids = ['A', 'R', 'N', 'D', 'C', 'G', 'H', 'I', 'L', 'K', 
                      'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V', 'X', 'STOP']
        for i, aa in enumerate(amino_acids):
            self.AA_CHANGE_ENCODING[aa] = i
        
        # Initialize numerical features
        self.NUMERICAL_FEATURES = [f for f in self.REQUIRED_FEATURES if f not in self.CATEGORICAL_FEATURES]
        
        logger.info("Feature preprocessor initialized")
    
    def validate_features(self, features: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input features"""
        errors = []
        
        for required in self.REQUIRED_FEATURES:
            if required not in features:
                errors.append(f"Missing required feature: {required}")
        
        # Validate numerical ranges
        if 'phyloP_score' in features:
            val = features['phyloP_score']
            if not (-14.0 <= val <= 6.0):
                errors.append(f"phyloP_score out of range: {val} (expected -14 to 6)")
        
        if 'CADD_score' in features:
            val = features['CADD_score']
            if not (0.0 <= val <= 99.0):
                errors.append(f"CADD_score out of range: {val} (expected 0 to 99)")
        
        if 'gnomAD_freq' in features:
            val = features['gnomAD_freq']
            if not (0.0 <= val <= 1.0):
                errors.append(f"gnomAD_freq out of range: {val} (expected 0 to 1)")
        
        return len(errors) == 0, errors
    
    def encode_categorical(self, variant_type: str, aa_change: str) -> Tuple[int, int]:
        """Encode categorical features"""
        variant_encoded = self.VARIANT_TYPE_ENCODING.get(variant_type, 5)  # 5 = Unknown
        
        # Extract amino acids from change string (e.g., "D123H" -> "D" and "H")
        try:
            ref_aa = aa_change[0].upper() if aa_change else 'X'
            alt_aa = aa_change[-1].upper() if aa_change and len(aa_change) > 1 else 'X'
        except:
            ref_aa = alt_aa = 'X'
        
        ref_encoded = self.AA_CHANGE_ENCODING.get(ref_aa, 18)  # 18 = X (unknown)
        alt_encoded = self.AA_CHANGE_ENCODING.get(alt_aa, 18)
        
        return variant_encoded, (ref_encoded * 20 + alt_encoded)  # Combine as single feature
    
    def handle_missing_values(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Handle missing feature values with defaults"""
        processed = features.copy()
        
        # Default values for missing numerical features
        defaults = {
            'phyloP_score': 0.0,
            'SIFT_score': 0.5,
            'PolyPhen_score': 0.5,
            'CADD_score': 15.0,
            'gnomAD_freq': 0.001,
            'REVEL_score': 0.5,
            'MutationTaster_score': 0.5,
            'FathmM_score': 0.5,
        }
        
        for feature, default in defaults.items():
            if feature not in processed:
                logger.warning(f"Missing feature {feature}, using default: {default}")
                processed[feature] = default
        
        return processed
    
    def preprocess(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Preprocess features for model input.
        Returns feature vector ready for ML model.
        """
        # Validate
        is_valid, errors = self.validate_features(features)
        if not is_valid:
            raise ValueError(f"Feature validation failed: {'; '.join(errors)}")
        
        # Handle missing values
        processed = self.handle_missing_values(features)
        
        # Extract and normalize numerical features
        feature_vector = []
        
        for feat_name in self.NUMERICAL_FEATURES:
            val = processed.get(feat_name, 0.0)
            
            # Normalize to 0-1 range (feature-specific normalization)
            if feat_name == 'phyloP_score':
                val = (val + 14.0) / 20.0  # Range -14 to 6
            elif feat_name == 'CADD_score':
                val = val / 99.0  # Range 0 to 99
            elif feat_name in ['SIFT_score', 'PolyPhen_score', 'REVEL_score', 
                             'MutationTaster_score', 'FathmM_score']:
                val = val  # Already 0-1
            
            # Clamp to [0, 1] range to handle out-of-range values
            val = max(0.0, min(1.0, val))
            
            feature_vector.append(val)
        
        # Encode categorical features
        variant_type = processed.get('variant_type', 'Unknown')
        aa_change = processed.get('amino_acid_change', 'X')
        variant_encoded, aa_encoded = self.encode_categorical(variant_type, aa_change)
        
        # Normalize categorical encodings
        feature_vector.append(variant_encoded / 6.0)  # 0-6 range
        feature_vector.append(aa_encoded / 400.0)     # 0-400 range
        
        return np.array(feature_vector, dtype=np.float32)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names in order"""
        return self.NUMERICAL_FEATURES + ['variant_type_encoded', 'aa_change_encoded']
