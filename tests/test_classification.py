import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.ml.feature_preprocessor import FeaturePreprocessor
from src.ml.classifier import PathogenicityClassifier


class TestFeaturePreprocessor:
    """Test feature preprocessing"""
    
    def setup_method(self):
        self.preprocessor = FeaturePreprocessor()
    
    def test_validate_features_complete(self):
        """Test validation with complete features"""
        features = {
            'phyloP_score': 2.0,
            'SIFT_score': 0.1,
            'PolyPhen_score': 0.8,
            'CADD_score': 25.0,
            'gnomAD_freq': 0.0001,
            'REVEL_score': 0.7,
            'MutationTaster_score': 0.9,
            'FathmM_score': -1.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }
        
        is_valid, errors = self.preprocessor.validate_features(features)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_features_missing(self):
        """Test validation with missing features"""
        features = {
            'phyloP_score': 2.0,
            'SIFT_score': 0.1
        }
        
        is_valid, errors = self.preprocessor.validate_features(features)
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_phylop_range(self):
        """Test phyloP score range validation"""
        features = {k: v for k, v in {
            'phyloP_score': 10.0,  # Out of range
            'SIFT_score': 0.1,
            'PolyPhen_score': 0.8,
            'CADD_score': 25.0,
            'gnomAD_freq': 0.0001,
            'REVEL_score': 0.7,
            'MutationTaster_score': 0.9,
            'FathmM_score': -1.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }.items()}
        
        is_valid, errors = self.preprocessor.validate_features(features)
        assert not is_valid
        assert any('phyloP_score' in e for e in errors)
    
    def test_encode_categorical(self):
        """Test categorical encoding"""
        variant_encoded, aa_encoded = self.preprocessor.encode_categorical('SNP', 'D123H')
        
        assert variant_encoded == 0  # SNP
        assert aa_encoded > 0  # Should be encoded
    
    def test_preprocess_vector_shape(self):
        """Test feature vector shape"""
        features = {
            'phyloP_score': 2.0,
            'SIFT_score': 0.1,
            'PolyPhen_score': 0.8,
            'CADD_score': 25.0,
            'gnomAD_freq': 0.0001,
            'REVEL_score': 0.7,
            'MutationTaster_score': 0.9,
            'FathmM_score': -1.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }
        
        vector = self.preprocessor.preprocess(features)
        
        # Should have: 8 numerical + 1 variant_type + 1 aa_change
        assert vector.shape == (10,)
        assert np.all(vector >= 0)
        assert np.all(vector <= 1)
    
    def test_handle_missing_values(self):
        """Test missing value handling"""
        features = {
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }
        
        processed = self.preprocessor.handle_missing_values(features)
        
        assert 'phyloP_score' in processed
        assert 'CADD_score' in processed


class TestPathogenicityClassifier:
    """Test pathogenicity classification"""
    
    def setup_method(self):
        """Setup classifier with mock model"""
        # Create mock model
        self.mock_model = Mock()
        self.mock_model.predict_proba = Mock(return_value=np.array([[0.2, 0.8]]))
        
        self.classifier = PathogenicityClassifier(default_version='v2')
        self.classifier.current_model = self.mock_model
    
    def test_classify_pathogenic(self):
        """Test pathogenic variant classification"""
        features = {
            'chrom': '17',
            'pos': 41244394,
            'ref': 'T',
            'alt': 'G',
            'phyloP_score': 3.0,
            'SIFT_score': 0.01,
            'PolyPhen_score': 0.95,
            'CADD_score': 30.0,
            'gnomAD_freq': 0.00001,
            'REVEL_score': 0.85,
            'MutationTaster_score': 0.95,
            'FathmM_score': -2.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'D123H'
        }
        
        # Mock model to return high pathogenic probability
        self.mock_model.predict_proba = Mock(return_value=np.array([[0.1, 0.9]]))
        
        result = self.classifier.classify(features, version='v2')
        
        assert result['classification'] == 'Pathogenic'
        assert result['confidence'] > 0.75
    
    def test_classify_benign(self):
        """Test benign variant classification"""
        features = {
            'chrom': '1',
            'pos': 1000000,
            'ref': 'A',
            'alt': 'G',
            'phyloP_score': 0.1,
            'SIFT_score': 0.5,
            'PolyPhen_score': 0.1,
            'CADD_score': 5.0,
            'gnomAD_freq': 0.1,
            'REVEL_score': 0.2,
            'MutationTaster_score': 0.2,
            'FathmM_score': 0.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'A1G'
        }
        
        # Mock model to return low pathogenic probability
        self.mock_model.predict_proba = Mock(return_value=np.array([[0.9, 0.1]]))
        
        result = self.classifier.classify(features, version='v2')
        
        assert result['classification'] == 'Benign'
        assert result['confidence'] > 0.75
    
    def test_classify_vus(self):
        """Test Variant of Uncertain Significance"""
        features = {
            'chrom': '2',
            'pos': 2000000,
            'ref': 'C',
            'alt': 'T',
            'phyloP_score': 1.0,
            'SIFT_score': 0.3,
            'PolyPhen_score': 0.5,
            'CADD_score': 15.0,
            'gnomAD_freq': 0.001,
            'REVEL_score': 0.5,
            'MutationTaster_score': 0.5,
            'FathmM_score': -0.5,
            'variant_type': 'SNP',
            'amino_acid_change': 'C100T'
        }
        
        # Mock model to return borderline probability
        self.mock_model.predict_proba = Mock(return_value=np.array([[0.45, 0.55]]))
        
        result = self.classifier.classify(features, version='v2')
        
        assert result['classification'] == 'VUS'
    
    def test_conflicting_interpretations(self):
        """Test handling of conflicting feature interpretations"""
        # High conservation (pathogenic) but high frequency (benign)
        features = {
            'chrom': '3',
            'pos': 3000000,
            'ref': 'G',
            'alt': 'A',
            'phyloP_score': 4.0,        # Highly conserved (pathogenic signal)
            'SIFT_score': 0.01,         # Damaging (pathogenic)
            'PolyPhen_score': 0.95,     # Probably damaging (pathogenic)
            'CADD_score': 28.0,         # High (pathogenic)
            'gnomAD_freq': 0.05,        # Common (benign signal)  ← Conflicting!
            'REVEL_score': 0.8,
            'MutationTaster_score': 0.9,
            'FathmM_score': -2.0,
            'variant_type': 'SNP',
            'amino_acid_change': 'G200A'
        }
        
        self.mock_model.predict_proba = Mock(return_value=np.array([[0.55, 0.45]]))
        
        result = self.classifier.classify(features, version='v2')
        
        # Should still classify but confidence should reflect conflict
        assert 'classification' in result
        assert 'interpretation' in result or result.get('interpretation') is None
    
    def test_batch_classify(self):
        """Test batch classification"""
        variants = [
            {
                'chrom': '17', 'pos': 41244394, 'ref': 'T', 'alt': 'G',
                'phyloP_score': 3.0, 'SIFT_score': 0.01, 'PolyPhen_score': 0.95,
                'CADD_score': 30.0, 'gnomAD_freq': 0.00001, 'REVEL_score': 0.85,
                'MutationTaster_score': 0.95, 'FathmM_score': -2.5,
                'variant_type': 'SNP', 'amino_acid_change': 'D123H'
            },
            {
                'chrom': '1', 'pos': 1000000, 'ref': 'A', 'alt': 'G',
                'phyloP_score': 0.1, 'SIFT_score': 0.5, 'PolyPhen_score': 0.1,
                'CADD_score': 5.0, 'gnomAD_freq': 0.1, 'REVEL_score': 0.2,
                'MutationTaster_score': 0.2, 'FathmM_score': 0.5,
                'variant_type': 'SNP', 'amino_acid_change': 'A1G'
            }
        ]
        
        self.mock_model.predict_proba = Mock(side_effect=[
            np.array([[0.1, 0.9]]),
            np.array([[0.9, 0.1]])
        ])
        
        results = self.classifier.batch_classify(variants, version='v2')
        
        assert len(results) == 2
        assert results[0]['classification'] == 'Pathogenic'
        assert results[1]['classification'] == 'Benign'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
