"""
Test suite for ensemble classifier fallback behavior.

Tests that when model files are unavailable, the classifier:
1. Sets using_fallback flag to True
2. Returns results with 'rule_based_fallback' in flags
3. Caps confidence at 0.60 for fallback predictions
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ml.ensemble_classifier import EnsemblePathogenicityClassifier, USING_FALLBACK


class TestEnsembleClassifierFallback:
    """Test fallback behavior when models are unavailable"""
    
    @pytest.fixture
    def nonexistent_model_paths(self):
        """Fixture providing non-existent model paths"""
        return [
            '/nonexistent/path/model_1.pkl',
            '/nonexistent/path/model_2.pkl',
            '/nonexistent/path/model_3.pkl',
        ]
    
    @pytest.fixture
    def sample_features(self):
        """Fixture providing valid sample features for classification"""
        return {
            'cadd_score': 25.0,
            'sift_score': 0.03,
            'polyphen2_score': 0.85,
            'gnomad_af': 0.001,
            'phylop_score': 2.5,
            'mutation_type': 'SNP',
            'gene': 'TP53',
            'position': 175,
            'is_regulatory': False
        }
    
    def test_get_model_status_all_models_failed(self, nonexistent_model_paths):
        """
        Test that get_model_status() returns correct values when all models fail to load
        """
        with patch.object(
            EnsemblePathogenicityClassifier, 
            'MODEL_PATHS', 
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            
            status = classifier.get_model_status()
            
            # Assert status structure
            assert 'models_loaded' in status
            assert 'models_expected' in status
            assert 'using_fallback' in status
            assert 'loaded_paths' in status
            
            # Assert no models were loaded
            assert status['models_loaded'] == 0
            assert status['models_expected'] == 3
            assert status['using_fallback'] is True
            assert status['loaded_paths'] == []
    
    def test_fallback_classification_returns_rule_based_flag(self, 
                                                             nonexistent_model_paths,
                                                             sample_features):
        """
        Test that classify() returns 'rule_based_fallback' flag when using fallback
        """
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            result = classifier.classify(sample_features)
            
            # Assert that fallback flag is present
            assert 'flags' in result
            assert 'rule_based_fallback' in result['flags']
    
    def test_fallback_classification_confidence_capped_at_0_60(self,
                                                               nonexistent_model_paths,
                                                               sample_features):
        """
        Test that fallback classification caps confidence at 0.60
        """
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            result = classifier.classify(sample_features)
            
            # Assert confidence is capped at 0.60
            assert result['confidence'] <= 0.60
            assert result['confidence'] >= 0.0
    
    def test_fallback_classification_with_high_pathogenicity_score(self,
                                                                   nonexistent_model_paths):
        """
        Test fallback classification with features suggesting high pathogenicity.
        Confidence should be high but still capped at 0.60.
        """
        high_path_features = {
            'cadd_score': 35.0,  # High CADD
            'sift_score': 0.02,  # Very deleterious
            'polyphen2_score': 0.95,  # Probably damaging
            'gnomad_af': 0.0001,  # Rare variant
            'phylop_score': 3.0,
            'mutation_type': 'SNP',
            'gene': 'BRCA1',
            'position': 500,
            'is_regulatory': False
        }
        
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            result = classifier.classify(high_path_features)
            
            # Should be Pathogenic based on high scores
            assert result['classification'] == 'Pathogenic'
            # But confidence should be capped
            assert result['confidence'] <= 0.60
            # And should have fallback flag
            assert 'rule_based_fallback' in result['flags']
    
    def test_fallback_classification_with_low_pathogenicity_score(self,
                                                                  nonexistent_model_paths):
        """
        Test fallback classification with features suggesting low pathogenicity.
        Confidence should be capped at 0.60.
        """
        low_path_features = {
            'cadd_score': 5.0,  # Low CADD
            'sift_score': 0.5,  # Tolerated
            'polyphen2_score': 0.2,  # Benign
            'gnomad_af': 0.1,  # Common variant
            'phylop_score': -2.0,
            'mutation_type': 'SNP',
            'gene': 'UNKNOWN',
            'position': 0,
            'is_regulatory': False
        }
        
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            result = classifier.classify(low_path_features)
            
            # Should be Benign based on low scores
            assert result['classification'] == 'Benign'
            # Confidence should be capped
            assert result['confidence'] <= 0.60
            # And should have fallback flag
            assert 'rule_based_fallback' in result['flags']
    
    def test_fallback_classification_with_vus_score(self,
                                                    nonexistent_model_paths):
        """
        Test fallback classification that results in VUS (Variant of Uncertain Significance).
        Confidence should be 0.50 (capped at 0.60 but naturally lower).
        """
        vus_features = {
            'cadd_score': 15.0,  # Intermediate CADD
            'sift_score': 0.25,  # Intermediate
            'polyphen2_score': 0.5,  # Intermediate
            'gnomad_af': 0.01,  # Intermediate frequency
            'phylop_score': 0.0,
            'mutation_type': 'Insertion',
            'gene': 'UNKNOWN',
            'position': 0,
            'is_regulatory': False
        }
        
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            result = classifier.classify(vus_features)
            
            # Should be VUS based on intermediate scores
            assert result['classification'] == 'VUS'
            # Confidence should be 0.50
            assert result['confidence'] == 0.50
            # And should have fallback flag
            assert 'rule_based_fallback' in result['flags']
    
    def test_fallback_mode_on_single_model_loaded(self, nonexistent_model_paths):
        """
        Test that with only 1 model loaded, classification works but includes
        degraded_mode flag when ensemble voting would be used.
        """
        # Create a mock model that returns valid predictions
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])  # Pathogenic probability
        
        # Only load first model successfully
        def load_one_model(self):
            # Simulate loading only first model
            self.loaded_models = [('/path/to/model_1.pkl', mock_model)]
            self.models['v1'] = mock_model
            self.models_loaded = {'v1': True, 'v2': False, 'v3': False}
            self.fallback_enabled = False
        
        with patch.object(
            EnsemblePathogenicityClassifier,
            '_load_models_resilient',
            load_one_model
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/test')
            sample_features = {
                'cadd_score': 25.0,
                'sift_score': 0.03,
                'polyphen2_score': 0.85,
                'gnomad_af': 0.001,
                'phylop_score': 2.5,
                'mutation_type': 'SNP',
                'gene': 'TP53',
                'position': 175,
                'is_regulatory': False
            }
            
            result = classifier.classify(sample_features)
            
            # Should have degraded_mode flag
            assert 'degraded_mode' in result.get('flags', [])
            # Should still classify correctly
            assert result['classification'] in ['Pathogenic', 'Benign', 'VUS']
            # Should use single_model mode
            assert result['model_version'] == 'single_model'
    
    def test_model_status_with_zero_models(self, nonexistent_model_paths):
        """
        Test that model_status accurately reflects 0 models loaded
        """
        with patch.object(
            EnsemblePathogenicityClassifier,
            'MODEL_PATHS',
            nonexistent_model_paths
        ):
            classifier = EnsemblePathogenicityClassifier(models_base_path='/nonexistent')
            
            status = classifier.get_model_status()
            
            assert status['models_loaded'] == 0
            assert status['models_expected'] == 3
            assert len(status['loaded_paths']) == 0
    
    def test_model_validation_on_load_failure(self, nonexistent_model_paths):
        """
        Test that model loading handles validation failures gracefully
        """
        # Create a mock model that fails validation (wrong feature count)
        mock_bad_model = MagicMock()
        mock_bad_model.predict.side_effect = ValueError("X has 5 features but expected 10")
        
        with patch('joblib.load', return_value=mock_bad_model):
            with patch('os.path.exists', return_value=True):
                # This should fail validation and not be added to loaded_models
                classifier = EnsemblePathogenicityClassifier(models_base_path='/test')
                
                status = classifier.get_model_status()
                
                # Should have 0 loaded models due to validation failure
                assert status['models_loaded'] == 0
                assert status['using_fallback'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
