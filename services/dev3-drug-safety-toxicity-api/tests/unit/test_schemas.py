"""
Unit tests for Pydantic request/response schemas.
"""
import pytest
from pydantic import ValidationError
from src.api.schemas import (
    ToxicityPredictRequest,
    ToxicityPredictResponse,
    PGxResponse,
    DDIRequest,
    DDIResponse,
)


class TestToxicityPredictRequest:
    """Test suite for toxicity prediction request schema."""

    def test_valid_request(self):
        """Test valid toxicity prediction request."""
        req = ToxicityPredictRequest(
            compound_smiles="CC(C)Cc1ccc(cc1)C(C)C(O)=O",
            patient_id="P001",
        )
        assert req.compound_smiles == "CC(C)Cc1ccc(cc1)C(C)C(O)=O"
        assert req.patient_id == "P001"

    def test_smiles_required(self):
        """Test SMILES is required."""
        with pytest.raises(ValidationError):
            ToxicityPredictRequest(patient_id="P001")

    def test_patient_id_optional(self):
        """Test patient_id is optional."""
        req = ToxicityPredictRequest(compound_smiles="CC")
        assert req.patient_id is None

    def test_empty_smiles(self):
        """Test empty SMILES is allowed."""
        req = ToxicityPredictRequest(compound_smiles="")
        assert req.compound_smiles == ""


class TestToxicityPredictResponse:
    """Test suite for toxicity prediction response schema."""

    def test_valid_response(self):
        """Test valid toxicity prediction response."""
        resp = ToxicityPredictResponse(
            compound_smiles="CC(C)Cc1ccc(cc1)C(C)C(O)=O",
            toxicity_score=0.32,
            risk_level="low",
        )
        assert resp.toxicity_score == 0.32
        assert resp.risk_level == "low"

    def test_response_with_shap_values(self):
        """Test response with SHAP values."""
        resp = ToxicityPredictResponse(
            compound_smiles="CC",
            toxicity_score=0.15,
            risk_level="low",
            shap_values={"feature1": 0.1, "feature2": 0.05},
        )
        assert resp.shap_values is not None
        assert resp.shap_values["feature1"] == 0.1

    def test_toxicity_score_required(self):
        """Test toxicity_score is required."""
        with pytest.raises(ValidationError):
            ToxicityPredictResponse(
                compound_smiles="CC",
                risk_level="low",
            )


class TestPGxResponse:
    """Test suite for PGx response schema."""

    def test_valid_response(self):
        """Test valid PGx response."""
        resp = PGxResponse(
            gene="CYP2C9",
            drug="warfarin",
            recommendation="Reduce dose by 30-50%",
            evidence_level="1A",
        )
        assert resp.gene == "CYP2C9"
        assert resp.evidence_level == "1A"

    def test_response_with_phenotypes(self):
        """Test response with phenotype categories."""
        resp = PGxResponse(
            gene="CYP2C9",
            drug="warfarin",
            recommendation="Guidance",
            evidence_level="1A",
            phenotype_categories=["Poor metabolizer", "Intermediate metabolizer"],
        )
        assert len(resp.phenotype_categories) == 2

    def test_gene_required(self):
        """Test gene is required."""
        with pytest.raises(ValidationError):
            PGxResponse(
                drug="warfarin",
                recommendation="Guidance",
                evidence_level="1A",
            )


class TestDDIRequest:
    """Test suite for DDI request schema."""

    def test_valid_request(self):
        """Test valid DDI request."""
        req = DDIRequest(drug_a="warfarin", drug_b="aspirin")
        assert req.drug_a == "warfarin"
        assert req.drug_b == "aspirin"

    def test_both_drugs_required(self):
        """Test both drugs are required."""
        with pytest.raises(ValidationError):
            DDIRequest(drug_a="warfarin")

    def test_case_sensitive_drugs(self):
        """Test drug names preserve case."""
        req = DDIRequest(drug_a="Warfarin", drug_b="ASPIRIN")
        assert req.drug_a == "Warfarin"
        assert req.drug_b == "ASPIRIN"


class TestDDIResponse:
    """Test suite for DDI response schema."""

    def test_valid_response(self):
        """Test valid DDI response."""
        resp = DDIResponse(
            drug_a="warfarin",
            drug_b="aspirin",
            interaction_type="Pharmacodynamic",
            severity="Major",
            description="Increases bleeding risk",
        )
        assert resp.severity == "Major"
        assert resp.interaction_type == "Pharmacodynamic"

    def test_response_with_optional_fields(self):
        """Test response with all optional fields."""
        resp = DDIResponse(
            drug_a="warfarin",
            drug_b="aspirin",
        )
        assert resp.interaction_type is None
        assert resp.severity is None

    def test_drug_names_required(self):
        """Test drug names are required."""
        with pytest.raises(ValidationError):
            DDIResponse(drug_a="warfarin")
