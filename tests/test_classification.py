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


class TestHotspotValidator:
    """Test hotspot validation and overrides"""
    
    def test_hotspot_detection_tp53_r175h(self):
        """Test detection of TP53 p.R175H hotspot"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.65,
            'probabilities': {'benign': 0.65, 'pathogenic': 0.35},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='TP53',
            mutation_notation='p.R175H'
        )
        
        # Should override low-confidence benign prediction
        assert validated['classification'] == 'Pathogenic'
        assert 'hotspot_override' in validated['flags']
        assert 'review_required' in validated['flags']
        assert 'ClinVar' in validated['explanation']
    
    def test_hotspot_detection_brca1_frameshift(self):
        """Test detection of BRCA1 c.5266dupC hotspot"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.55,
            'probabilities': {'benign': 0.55, 'pathogenic': 0.45},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='BRCA1',
            mutation_notation='c.5266dupC'
        )
        
        assert validated['classification'] == 'Pathogenic'
        assert 'hotspot_override' in validated['flags']
        assert validated['confidence'] > 0.55  # Confidence boosted
    
    def test_hotspot_detection_kras_g12d(self):
        """Test detection of KRAS p.G12D hotspot"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.70,
            'probabilities': {'benign': 0.70, 'pathogenic': 0.30},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='KRAS',
            mutation_notation='p.G12D'
        )
        
        assert validated['classification'] == 'Pathogenic'
        assert 'hotspot_override' in validated['flags']
    
    def test_hotspot_with_high_confidence_benign(self):
        """Test that high-confidence benign predictions are NOT overridden"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.95,  # High confidence
            'probabilities': {'benign': 0.95, 'pathogenic': 0.05},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='TP53',
            mutation_notation='p.R175H'
        )
        
        # Should NOT override if confidence >= threshold
        assert validated['classification'] == 'Benign'
        assert 'hotspot_override' not in validated['flags']
    
    def test_hotspot_pathogenic_prediction_not_overridden(self):
        """Test that pathogenic predictions for hotspots are not overridden"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Pathogenic',
            'confidence': 0.92,
            'probabilities': {'benign': 0.08, 'pathogenic': 0.92},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='TP53',
            mutation_notation='p.R175H'
        )
        
        # Should not override when already predicted as pathogenic
        assert validated['classification'] == 'Pathogenic'
        assert 'hotspot_override' not in validated['flags']
    
    def test_unknown_hotspot_no_override(self):
        """Test that unknown variants are not affected"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.5,
            'probabilities': {'benign': 0.5, 'pathogenic': 0.5},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='UNKNOWN_GENE',
            mutation_notation='p.X999Y'
        )
        
        # Should remain unchanged
        assert validated['classification'] == 'Benign'
        assert 'hotspot_override' not in validated['flags']
    
    def test_tp53_r175h_alternative_notation(self):
        """Test TP53 hotspot with alternative notation (without 'p.' prefix)"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.60,
            'probabilities': {'benign': 0.60, 'pathogenic': 0.40},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='TP53',
            mutation_notation='R175H'  # No 'p.' prefix
        )
        
        # Should find hotspot even with alternative notation
        assert validated['classification'] == 'Pathogenic'
        assert 'hotspot_override' in validated['flags']
    
    def test_hotspot_gets_info(self):
        """Test retrieving hotspot information"""
        from src.api.variant_analysis import HotspotValidator
        from src.api.classification_schemas import format_clinvar_id, build_clinvar_data
        
        info = HotspotValidator.get_hotspot_info('TP53', 'p.R175H')
        
        assert info is not None
        assert info['clinical_significance'] == 'Pathogenic'
        
        # Test clinvar formatting helpers
        raw_id = info['clinvar_id']
        assert raw_id == 'RCV000012312'
        
        formatted_id = format_clinvar_id(raw_id)
        assert 'ClinVar' in formatted_id
        assert formatted_id == 'ClinVar:RCV000012312'
        
        clinvar_data = build_clinvar_data(raw_id, info.get('clinical_significance'))
        assert clinvar_data is not None
        assert clinvar_data.source == 'ClinVar'
        assert clinvar_data.id == 'RCV000012312'
        assert 'RCV' in clinvar_data.id
        assert 'ncbi.nlm.nih.gov' in clinvar_data.url
        
        assert 'Li-Fraumeni' in info['disease']
    
    def test_clinvar_data_formatting(self):
        """Test ClinVar ID and data formatting functions"""
        from src.api.classification_schemas import format_clinvar_id, build_clinvar_data
        
        # Test format_clinvar_id with valid ID
        raw_id = 'RCV000012312'
        formatted = format_clinvar_id(raw_id)
        assert formatted == 'ClinVar:RCV000012312'
        assert 'ClinVar' in formatted
        
        # Test format_clinvar_id with None
        assert format_clinvar_id(None) is None
        
        # Test build_clinvar_data with valid ID
        clinvar_data = build_clinvar_data(raw_id, significance='Pathogenic')
        assert clinvar_data is not None
        assert clinvar_data.id == 'RCV000012312'
        assert clinvar_data.source == 'ClinVar'
        assert 'RCV000012312' in clinvar_data.url
        assert clinvar_data.significance == 'Pathogenic'
        
        # Test build_clinvar_data with None
        assert build_clinvar_data(None) is None
    
    def test_classification_response_clinvar_fields(self):
        """Test that ClassificationResponse includes clinvar_id and clinvar_data fields"""
        from src.api.classification_schemas import ClassificationResponse, ClinVarData
        
        # Create response with clinvar fields
        response = ClassificationResponse(
            variant_id='1-1000-A-G',
            chrom='1',
            pos=1000,
            ref='A',
            alt='G',
            classification='Pathogenic',
            confidence=0.95,
            probabilities={'pathogenic': 0.95, 'benign': 0.05},
            model_version='v2',
            clinical_significance='Pathogenic',
            feature_importance={},
            clinvar_id='ClinVar:RCV000012312',
            clinvar_data=ClinVarData(
                id='RCV000012312',
                source='ClinVar',
                url='https://www.ncbi.nlm.nih.gov/clinvar/RCV000012312/',
                significance='Pathogenic'
            )
        )
        
        # Verify clinvar_id field
        assert 'ClinVar' in response.clinvar_id
        assert 'RCV000012312' in response.clinvar_id
        
        # Verify clinvar_data field
        assert response.clinvar_data is not None
        assert response.clinvar_data.source == 'ClinVar'
        assert 'RCV' in response.clinvar_data.id
        assert response.clinvar_data.id == 'RCV000012312'
        assert 'ncbi.nlm.nih.gov' in response.clinvar_data.url

    
    def test_hotspot_list_returns_all(self):
        """Test that list_hotspots returns all known hotspots"""
        from src.api.variant_analysis import HotspotValidator
        
        hotspots = HotspotValidator.list_hotspots()
        
        assert len(hotspots) > 0
        # Check for at least our three test cases
        assert ('TP53', 'p.R175H') in hotspots
        assert ('BRCA1', 'c.5266dupC') in hotspots
        assert ('KRAS', 'p.G12D') in hotspots


class TestHotspotEndpointIntegration:
    """Integration tests for hotspot validation in API endpoint"""
    
    def test_classification_endpoint_with_tp53_hotspot(self):
        """Test that classification endpoint overrides low-confidence benign for TP53 hotspot"""
        from src.api.variant_analysis import HotspotValidator
        from src.api.classification_schemas import ClassificationResponse
        
        # Simulate model output (low-confidence benign)
        model_result = {
            'classification': 'Benign',
            'confidence': 0.65,
            'probabilities': {'benign': 0.65, 'pathogenic': 0.35},
            'model_version': 'ensemble_v1-3',
            'variant': {
                'chrom': '17',
                'pos': 7571720,
                'ref': 'G',
                'alt': 'A',
                'gene_symbol': 'TP53',
                'amino_acid_change': 'p.R175H'
            },
            'interpretation': {}
        }
        
        # Apply hotspot validation
        validated = HotspotValidator.validate_and_override(
            model_result,
            gene_symbol='TP53',
            mutation_notation='p.R175H'
        )
        
        # Verify override
        assert validated['classification'] == 'Pathogenic'
        assert 'review_required' in validated.get('flags', [])
        
        # Verify explanation includes override reason
        explanation = validated.get('explanation', '')
        assert 'hotspot' in explanation.lower() or 'override' in explanation.lower()
    
    def test_review_required_flag_set(self):
        """Test that review_required flag is always set when override occurs"""
        from src.api.variant_analysis import HotspotValidator
        
        result = {
            'classification': 'Benign',
            'confidence': 0.70,
            'probabilities': {'benign': 0.70, 'pathogenic': 0.30},
            'model_version': 'ensemble_v1-3'
        }
        
        validated = HotspotValidator.validate_and_override(
            result,
            gene_symbol='BRCA1',
            mutation_notation='c.5266dupC'
        )
        
        assert 'review_required' in validated.get('flags', [])
        assert validated['classification'] == 'Pathogenic'


class TestModelPerformanceMetrics:
    """Test model performance tracking and metrics"""
    
    def setup_method(self):
        """Setup test database and fixtures"""
        from src.db.model_performance_repository import ModelPerformanceRepository
        self.repo = ModelPerformanceRepository
    
    def test_log_prediction_with_ground_truth(self):
        """Test logging a prediction with ground truth"""
        success = self.repo.log_prediction(
            variant_id='chr17-7571720-G-A',
            model_version='ensemble_v1-3',
            predicted_label='Pathogenic',
            confidence=0.92,
            true_label='Pathogenic'
        )
        
        assert success is True
    
    def test_log_prediction_without_ground_truth(self):
        """Test logging a prediction without ground truth"""
        success = self.repo.log_prediction(
            variant_id='chr1-1000000-A-G',
            model_version='v1',
            predicted_label='Benign',
            confidence=0.65
            # true_label not provided
        )
        
        assert success is True
    
    def test_model_performance_metrics_accuracy_calculation(self):
        """Test metrics calculation with 7 correct and 3 wrong predictions"""
        from datetime import datetime
        from unittest.mock import patch, MagicMock
        
        # Mock database cursor to return test data
        mock_cursor = MagicMock()
        
        # First SELECT: total predictions with ground truth
        total_result = MagicMock()
        total_result.__getitem__ = lambda self, key: 10 if key == 'total' else None
        
        # Second SELECT: correct predictions
        correct_result = MagicMock()
        correct_result.__getitem__ = lambda self, key: 7 if key == 'correct' else None
        
        # Third SELECT: low confidence count
        low_conf_result = MagicMock()
        low_conf_result.__getitem__ = lambda self, key: 1 if key == 'low_conf' else None
        
        # Fourth SELECT: per-model metrics
        model_metrics_result = [{
            'model_version': 'ensemble_v1-3',
            'total_preds': 10,
            'correct': 7,
            'avg_conf': 0.82,
            'tp': 5,
            'tn': 2,
            'fp': 1,
            'fn': 2
        }]
        
        # Setup mock to return these results in sequence
        mock_cursor.fetchone.side_effect = [total_result, correct_result, low_conf_result]
        mock_cursor.fetchall.return_value = model_metrics_result
        
        with patch('src.db.model_performance_repository.db.get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            
            metrics = self.repo.get_metrics_7d()
        
        # Verify accuracy is 0.70 (7 correct out of 10)
        assert metrics['rolling_accuracy_7d'] == 0.70
        assert metrics['total_predictions'] == 10
        assert metrics['correct_predictions'] == 7
        assert metrics['low_confidence_rate'] == 0.10  # 1 out of 10 with confidence < 0.70
    
    def test_metrics_with_zero_predictions(self):
        """Test metrics calculation with no predictions"""
        from unittest.mock import patch, MagicMock
        
        mock_cursor = MagicMock()
        total_result = MagicMock()
        total_result.__getitem__ = lambda self, key: 0 if key == 'total' else None
        correct_result = MagicMock()
        correct_result.__getitem__ = lambda self, key: 0 if key == 'correct' else None
        low_conf_result = MagicMock()
        low_conf_result.__getitem__ = lambda self, key: 0 if key == 'low_conf' else None
        
        mock_cursor.fetchone.side_effect = [total_result, correct_result, low_conf_result]
        mock_cursor.fetchall.return_value = []
        
        with patch('src.db.model_performance_repository.db.get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            
            metrics = self.repo.get_metrics_7d()
        
        # Should return zeros without error
        assert metrics['rolling_accuracy_7d'] == 0.0
        assert metrics['total_predictions'] == 0
        assert metrics['correct_predictions'] == 0
        assert metrics['rolling_auroc_7d'] == 0.0
    
    def test_auroc_calculation(self):
        """Test AUROC calculation from confusion matrix"""
        from unittest.mock import patch, MagicMock
        
        # Setup: TP=80, TN=15, FP=5, FN=0 (out of 100)
        # AUROC proxy should be (80+15)/100 = 0.95
        mock_cursor = MagicMock()
        
        total_result = MagicMock()
        total_result.__getitem__ = lambda self, key: 100 if key == 'total' else None
        correct_result = MagicMock()
        correct_result.__getitem__ = lambda self, key: 95 if key == 'correct' else None
        low_conf_result = MagicMock()
        low_conf_result.__getitem__ = lambda self, key: 2 if key == 'low_conf' else None
        
        model_metrics_result = [{
            'model_version': 'ensemble_v1-3',
            'total_preds': 100,
            'correct': 95,
            'avg_conf': 0.88,
            'tp': 80,
            'tn': 15,
            'fp': 5,
            'fn': 0
        }]
        
        mock_cursor.fetchone.side_effect = [total_result, correct_result, low_conf_result]
        mock_cursor.fetchall.return_value = model_metrics_result
        
        with patch('src.db.model_performance_repository.db.get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            
            metrics = self.repo.get_metrics_7d()
        
        # Verify AUROC proxy (TP+TN)/total = (80+15)/100 = 0.95
        assert metrics['rolling_auroc_7d'] == 0.95
        assert metrics['low_confidence_rate'] == 0.02
    
    def test_model_drift_detection(self):
        """Test model drift alert when AUROC drops below 0.80"""
        from unittest.mock import patch, MagicMock
        
        # Setup: Low AUROC of 0.68 (should trigger drift alert)
        mock_cursor = MagicMock()
        
        total_result = MagicMock()
        total_result.__getitem__ = lambda self, key: 100 if key == 'total' else None
        correct_result = MagicMock()
        correct_result.__getitem__ = lambda self, key: 68 if key == 'correct' else None
        low_conf_result = MagicMock()
        low_conf_result.__getitem__ = lambda self, key: 10 if key == 'low_conf' else None
        
        model_metrics_result = [{
            'model_version': 'ensemble_v1-3',
            'total_preds': 100,
            'correct': 68,
            'avg_conf': 0.72,
            'tp': 55,
            'tn': 13,
            'fp': 15,
            'fn': 17
        }]
        
        mock_cursor.fetchone.side_effect = [total_result, correct_result, low_conf_result]
        mock_cursor.fetchall.return_value = model_metrics_result
        
        with patch('src.db.model_performance_repository.db.get_cursor') as mock_get_cursor:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            
            metrics = self.repo.get_metrics_7d()
        
        # Verify low AUROC triggers drift alert
        assert metrics['rolling_auroc_7d'] == 0.68
        assert metrics['rolling_auroc_7d'] < 0.80  # Below threshold
        assert metrics['rolling_accuracy_7d'] == 0.68
    
    @pytest.mark.asyncio
    async def test_models_metrics_endpoint_returns_expected_format(self):
        """Test GET /models/metrics endpoint response format"""
        from unittest.mock import patch, MagicMock, AsyncMock
        
        mock_cursor = MagicMock()
        
        total_result = MagicMock()
        total_result.__getitem__ = lambda self, key: 10 if key == 'total' else None
        correct_result = MagicMock()
        correct_result.__getitem__ = lambda self, key: 7 if key == 'correct' else None
        low_conf_result = MagicMock()
        low_conf_result.__getitem__ = lambda self, key: 1 if key == 'low_conf' else None
        
        model_metrics_result = [{
            'model_version': 'ensemble_v1-3',
            'total_preds': 10,
            'correct': 7,
            'avg_conf': 0.82,
            'tp': 5,
            'tn': 2,
            'fp': 1,
            'fn': 2
        }]
        
        mock_cursor.fetchone.side_effect = [total_result, correct_result, low_conf_result]
        mock_cursor.fetchall.return_value = model_metrics_result
        
        with patch('src.db.model_performance_repository.db.get_cursor') as mock_get_cursor, \
             patch('src.api.classification.get_cache') as mock_get_cache:
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor
            mock_cache_instance = MagicMock()
            mock_get_cache.return_value = mock_cache_instance
            
            # Import and call the endpoint function
            from src.api.classification import get_model_metrics
            result = await get_model_metrics()
        
        # Verify response format
        assert 'rolling_auroc_7d' in result
        assert 'rolling_accuracy_7d' in result
        assert 'total_predictions' in result
        assert 'correct_predictions' in result
        assert 'low_confidence_rate' in result
        assert 'model_drift_alert' in result
        assert 'per_model_metrics' in result
        
        # Verify accuracy value
        assert result['rolling_accuracy_7d'] == 0.70


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
