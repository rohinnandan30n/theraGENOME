"""
Unit tests for ML toxicity model with enhanced feature extraction.
"""
import pytest
import numpy as np
from src.ml.toxicity_model import (
    extract_molecular_features,
    extract_features,
    predict_toxicity,
    get_model_info,
    _get_feature_importance,
    _format_features,
)


class TestMolecularFeatureExtraction:
    """Test suite for molecular feature extraction."""

    def test_extract_features_valid_smiles(self):
        """Test feature extraction from valid SMILES."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"  # Ibuprofen
        features = extract_molecular_features(smiles)

        assert isinstance(features, np.ndarray)
        assert len(features) == 10
        assert all(isinstance(f, (int, float, np.floating)) for f in features)
        assert features[0] > 0  # Molecular weight should be > 0

    def test_extract_features_empty_smiles(self):
        """Test feature extraction from empty SMILES."""
        smiles = ""
        features = extract_molecular_features(smiles)

        assert isinstance(features, np.ndarray)
        assert len(features) == 10
        assert np.all(features == 0)

    def test_extract_features_methane(self):
        """Test feature extraction for simple molecule."""
        smiles = "C"  # Methane
        features = extract_molecular_features(smiles)

        assert features[0] > 0  # MW
        assert features[6] == 1  # Heavy atoms

    def test_extract_features_benzene(self):
        """Test feature extraction for aromatic compound."""
        smiles = "c1ccccc1"  # Benzene
        features = extract_molecular_features(smiles)

        assert features[5] > 0  # Aromatic rings
        assert features[6] > 0  # Heavy atoms

    def test_extract_features_ethanol(self):
        """Test feature extraction with oxygen."""
        smiles = "CCO"  # Ethanol
        features = extract_molecular_features(smiles)

        assert features[2] > 0  # H-bond donors
        assert features[3] > 0  # H-bond acceptors

    def test_extract_features_aniline(self):
        """Test feature extraction with nitrogen."""
        smiles = "Nc1ccccc1"  # Aniline
        features = extract_molecular_features(smiles)

        assert features[2] > 0  # H-bond donors (from NH2)
        assert features[3] > 0  # H-bond acceptors

    def test_extract_features_fluorinated(self):
        """Test feature extraction with halogens."""
        smiles = "FC(F)(F)c1ccccc1"  # Trifluoromethylbenzene
        features = extract_molecular_features(smiles)

        assert features[8] == 3  # Halogen count

    def test_extract_features_sulfur_compound(self):
        """Test feature extraction with sulfur."""
        smiles = "CS(C)=O"  # DMSO
        features = extract_molecular_features(smiles)

        assert features[9] > 0  # Sulfur count

    def test_extract_features_complex_toxin(self):
        """Test feature extraction for complex compound."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"  # Ibuprofen
        features = extract_molecular_features(smiles)

        # Verify reasonable values
        assert 100 < features[0] < 300  # MW between 100-300
        assert features[6] > 10  # Multiple heavy atoms

    def test_extract_features_backward_compatibility(self):
        """Test backward compatibility with old API."""
        smiles = "CC"  # Ethane
        features_old = extract_features(smiles)
        features_new = extract_molecular_features(smiles).tolist()

        assert features_old == features_new


class TestToxicityPrediction:
    """Test suite for toxicity prediction."""

    def test_predict_toxicity_valid_compound(self):
        """Test toxicity prediction returns valid output."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        result = predict_toxicity(smiles)

        assert isinstance(result, dict)
        assert "toxicity_score" in result
        assert "risk_level" in result
        assert "confidence" in result
        assert "shap_values" in result
        assert "features_used" in result
        assert 0 <= result["toxicity_score"] <= 1
        assert result["risk_level"] in ["low", "medium", "high"]
        assert 0 <= result["confidence"] <= 1

    def test_predict_toxicity_risk_classification(self):
        """Test risk level classification."""
        # Low toxicity
        smiles_low = "C"
        result_low = predict_toxicity(smiles_low)
        if result_low["toxicity_score"] < 0.33:
            assert result_low["risk_level"] == "low"

        # High toxicity
        smiles_high = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        result_high = predict_toxicity(smiles_high)
        if result_high["toxicity_score"] > 0.66:
            assert result_high["risk_level"] == "high"

    def test_predict_toxicity_empty_smiles(self):
        """Test prediction with empty SMILES."""
        result = predict_toxicity("")

        assert isinstance(result, dict)
        assert "toxicity_score" in result
        assert 0 <= result["toxicity_score"] <= 1

    def test_predict_toxicity_consistency(self):
        """Test prediction is consistent for same input."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"

        result1 = predict_toxicity(smiles)
        result2 = predict_toxicity(smiles)

        assert result1["toxicity_score"] == result2["toxicity_score"]
        assert result1["risk_level"] == result2["risk_level"]

    def test_predict_toxicity_has_shap_values(self):
        """Test prediction includes SHAP explanations."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        result = predict_toxicity(smiles)

        assert result["shap_values"] is not None
        assert isinstance(result["shap_values"], dict)
        assert len(result["shap_values"]) > 0

    def test_predict_toxicity_has_formatted_features(self):
        """Test prediction includes formatted features."""
        smiles = "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        result = predict_toxicity(smiles)

        assert result["features_used"] is not None
        assert isinstance(result["features_used"], dict)
        assert "molecular_weight" in result["features_used"]
        assert "hydrophobicity_logp" in result["features_used"]


class TestFeatureFormatting:
    """Test suite for feature formatting utilities."""

    def test_format_features(self):
        """Test feature formatting."""
        features = np.array([180, 1.2, 2, 3, 45, 5, 10, 80, 2, 1], dtype=np.float32)
        formatted = _format_features(features)

        assert isinstance(formatted, dict)
        assert len(formatted) == 10
        assert "molecular_weight" in formatted
        assert "hydrophobicity_logp" in formatted
        assert formatted["molecular_weight"] == 180.0

    def test_get_feature_importance(self):
        """Test SHAP value generation."""
        features = np.array([180, 1.2, 2, 3, 45, 5, 10, 80, 2, 1], dtype=np.float32)
        shap_values = _get_feature_importance(features)

        assert isinstance(shap_values, dict)
        assert len(shap_values) <= 5  # Top 5 features
        assert all(0 <= v <= 1 for v in shap_values.values())


class TestModelInfo:
    """Test suite for model information."""

    def test_get_model_info(self):
        """Test model info retrieval."""
        info = get_model_info()

        assert isinstance(info, dict)
        assert "status" in info
        assert "features_count" in info
        assert info["features_count"] == 10

