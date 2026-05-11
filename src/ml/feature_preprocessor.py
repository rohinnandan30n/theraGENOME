from typing import Dict, Any, List, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Expected feature vector length for model compatibility
EXPECTED_FEATURE_COUNT = 10

# Protein domain regions by gene (amino acid position ranges)
DOMAIN_REGIONS = {
    "TP53": [(102, 292)],
    "BRCA1": [(1, 1863)],
}


class FeaturePreprocessor:
    """
    Preprocess variant features for ML model input.
    
    Returns a 10-element feature vector in the following order:
    1. phyloP_score (normalized conservation)
    2. SIFT_score (protein impact)
    3. PolyPhen_score (protein impact)
    4. CADD_score (normalized combined pathogenicity)
    5. gnomAD_freq (population frequency)
    6. REVEL_score (ensemble pathogenicity)
    7. MutationTaster_score (mutation impact)
    8. FathmM_score (functional impact)
    9. domain_annotation (1.0 if in known protein domain, 0.0 otherwise)
    10. regulatory_region_flag (1.0 if in regulatory region, 0.0 otherwise)
    11. splice_site_impact (1.0 if splice variant, 0.0 otherwise)
    12. functional_prediction (composite score: mean of normalized scores)
    
    Note: Total = 12 when categorical encodings included; core numerical = 10
    """
    
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
    
    @staticmethod
    def validate_feature_vector(vec: np.ndarray) -> None:
        """
        Validate feature vector length and type.
        
        Args:
            vec: Feature vector to validate
            
        Raises:
            ValueError: If vector length is not EXPECTED_FEATURE_COUNT
        """
        if len(vec) != EXPECTED_FEATURE_COUNT:
            raise ValueError(
                f"Feature vector length mismatch. Expected {EXPECTED_FEATURE_COUNT} features, "
                f"got {len(vec)}. This indicates a mismatch between preprocessing and model training."
            )
    
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
        Returns a 10-element feature vector with the following structure:
        1. phyloP_score (normalized)
        2. SIFT_score (0-1)
        3. PolyPhen_score (0-1)
        4. CADD_score (normalized to 0-1)
        5. gnomAD_freq (0-1)
        6. REVEL_score (0-1)
        7. domain_annotation (1.0 if in known protein domain, 0.0 otherwise)
        8. regulatory_region_flag (1.0 if in regulatory region, 0.0 otherwise)
        9. splice_site_impact (1.0 if splice variant, 0.0 otherwise)
        10. functional_prediction (composite score of SIFT, PolyPhen, CADD)
        """
        # Validate
        is_valid, errors = self.validate_features(features)
        if not is_valid:
            raise ValueError(f"Feature validation failed: {'; '.join(errors)}")
        
        # Handle missing values
        processed = self.handle_missing_values(features)
        
        # Extract and normalize only the first 6 numerical features
        # (phyloP, SIFT, PolyPhen, CADD, gnomAD_freq, REVEL)
        feature_vector = []
        primary_features = ['phyloP_score', 'SIFT_score', 'PolyPhen_score', 
                           'CADD_score', 'gnomAD_freq', 'REVEL_score']
        
        for feat_name in primary_features:
            val = processed.get(feat_name, 0.0)
            
            # Normalize to 0-1 range (feature-specific normalization)
            if feat_name == 'phyloP_score':
                val = (val + 14.0) / 20.0  # Range -14 to 6
            elif feat_name == 'CADD_score':
                val = val / 99.0  # Range 0 to 99
            elif feat_name in ['SIFT_score', 'PolyPhen_score', 'REVEL_score']:
                val = val  # Already 0-1
            
            # Clamp to [0, 1] range to handle out-of-range values
            val = max(0.0, min(1.0, val))
            
            feature_vector.append(val)
        
        # Feature 7: Domain annotation
        domain_annotation = self._compute_domain_annotation(
            processed.get('gene', 'Unknown'),
            processed.get('position', 0)
        )
        feature_vector.append(domain_annotation)
        
        # Feature 8: Regulatory region flag
        regulatory_region_flag = float(processed.get('is_regulatory', False))
        feature_vector.append(regulatory_region_flag)
        
        # Feature 9: Splice site impact
        mutation_type = processed.get('mutation_type', '')
        splice_site_impact = 1.0 if 'splice' in str(mutation_type).lower() else 0.0
        feature_vector.append(splice_site_impact)
        
        # Feature 10: Functional prediction (composite score)
        functional_prediction = self._compute_functional_prediction(processed)
        feature_vector.append(functional_prediction)
        
        # Convert to numpy array
        feature_array = np.array(feature_vector, dtype=np.float32)
        
        # Validate feature count
        assert len(feature_array) == EXPECTED_FEATURE_COUNT, \
            f"Feature vector length mismatch: expected {EXPECTED_FEATURE_COUNT}, got {len(feature_array)}"
        
        # Additional validation
        self.validate_feature_vector(feature_array)
        
        return feature_array
    
    def _compute_domain_annotation(self, gene: str, position: int) -> float:
        """
        Check if variant falls within a known protein domain.
        
        Args:
            gene: Gene symbol (e.g., 'TP53')
            position: Amino acid position (1-based)
            
        Returns:
            1.0 if variant is in a known domain, 0.0 otherwise
        """
        if gene not in DOMAIN_REGIONS:
            return 0.0
        
        try:
            position = int(position)
            for start, end in DOMAIN_REGIONS[gene]:
                if start <= position <= end:
                    return 1.0
        except (ValueError, TypeError):
            pass
        
        return 0.0
    
    def _compute_functional_prediction(self, features: Dict[str, Any]) -> float:
        """
        Compute composite functional prediction score.
        
        Calculates mean of normalized SIFT, PolyPhen, and CADD scores.
        Each component defaults to 0.5 if missing, then result is clamped to [0.0, 1.0].
        
        Args:
            features: Feature dictionary with scoring values
            
        Returns:
            Composite score in range [0.0, 1.0]
        """
        # Get component scores, defaulting to 0.5 if missing
        sift = features.get('SIFT_score', 0.5)
        polyphen = features.get('PolyPhen_score', 0.5)
        cadd_raw = features.get('CADD_score', 20.0)
        
        # Normalize CADD to 0-1 range (CADD range is 0-99)
        cadd_normalized = min(max(cadd_raw / 40.0, 0.0), 1.0)
        
        # Ensure all values are in valid range
        sift = min(max(float(sift), 0.0), 1.0)
        polyphen = min(max(float(polyphen), 0.0), 1.0)
        
        # Compute mean and clamp to [0.0, 1.0]
        composite = (sift + polyphen + cadd_normalized) / 3.0
        composite = min(max(composite, 0.0), 1.0)
        
        return float(composite)
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names in order"""
        return self.NUMERICAL_FEATURES + ['variant_type_encoded', 'aa_change_encoded',
                                         'domain_annotation', 'regulatory_region_flag',
                                         'splice_site_impact', 'functional_prediction']
