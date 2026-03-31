"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from src.main import app


@pytest.fixture
def client():
    """Create TestClient for FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test /health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "service" in response.json()

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
        assert "endpoints" in response.json()


class TestToxicityPredictionEndpoint:
    """Test toxicity prediction endpoint."""

    def test_predict_toxicity_valid_request(self, client):
        """Test toxicity prediction with valid compound."""
        response = client.post(
            "/api/v1/drugs/predict-toxicity",
            json={
                "compound_smiles": "CC(C)Cc1ccc(cc1)C(C)C(O)=O",
                "patient_id": "P001",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Check for valid toxicity score range (0-1)
        assert 0 <= data["toxicity_score"] <= 1
        # Check that risk_level is one of the expected values
        assert data["risk_level"] in ["low", "medium", "high"]
        # Check that features_used are present
        assert "features_used" in data
        assert "shap_values" in data
        # Verify features_used has the 10 molecular descriptors
        assert len(data["features_used"]) == 10

    def test_predict_toxicity_missing_smiles(self, client):
        """Test toxicity prediction fails without SMILES."""
        response = client.post(
            "/api/v1/drugs/predict-toxicity",
            json={"patient_id": "P001"},
        )
        assert response.status_code == 422  # Validation error


class TestPGxEndpoint:
    """Test PGx recommendation endpoint."""

    def test_get_pgx_valid_params(self, client):
        """Test PGx endpoint with valid parameters."""
        with patch("src.external_apis.pharmgkb_api.get_pgx_recommendation") as mock_pgx:
            mock_pgx.return_value = {
                "gene": "CYP2C9",
                "drug": "warfarin",
                "recommendation": "Reduce dose",
                "evidence_level": "1A",
                "source": "PharmGKB",
            }

            response = client.get(
                "/api/v1/drugs/pgx",
                params={"gene": "CYP2C9", "drug": "warfarin"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["gene"] == "CYP2C9"
            assert data["drug"] == "warfarin"

    def test_get_pgx_missing_gene(self, client):
        """Test PGx endpoint fails without gene."""
        response = client.get(
            "/api/v1/drugs/pgx",
            params={"drug": "warfarin"},
        )
        assert response.status_code == 422


class TestDDIEndpoint:
    """Test DDI checking endpoint."""

    def test_check_ddi_valid_request(self, client):
        """Test DDI check with valid drugs."""
        with patch("src.external_apis.drugbank_api.check_drug_interaction") as mock_ddi:
            mock_ddi.return_value = {
                "drug_a": "warfarin",
                "drug_b": "aspirin",
                "interaction_found": True,
                "interaction_type": "Pharmacodynamic",
                "severity": "Major",
                "description": "Increases bleeding risk",
                "source": "local_knowledge_base",
            }

            response = client.post(
                "/api/v1/drugs/ddi",
                json={"drug_a": "warfarin", "drug_b": "aspirin"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["interaction_found"] is True
            assert data["severity"] == "Major"

    def test_check_ddi_missing_drug(self, client):
        """Test DDI check fails without both drugs."""
        response = client.post(
            "/api/v1/drugs/ddi",
            json={"drug_a": "warfarin"},
        )
        assert response.status_code == 422

    def test_check_ddi_no_interaction(self, client):
        """Test DDI check returns no interaction."""
        with patch("src.external_apis.drugbank_api.check_drug_interaction") as mock_ddi:
            mock_ddi.return_value = {
                "drug_a": "unknown1",
                "drug_b": "unknown2",
                "interaction_found": False,
                "interaction_type": None,
                "severity": None,
                "description": "No known interaction",
                "source": "local_knowledge_base",
            }

            response = client.post(
                "/api/v1/drugs/ddi",
                json={"drug_a": "unknown1", "drug_b": "unknown2"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["interaction_found"] is False


class TestFAERSEndpoint:
    """Test FAERS adverse events endpoint."""

    def test_get_faers_valid_drug(self, client):
        """Test FAERS endpoint with valid drug."""
        with patch("src.external_apis.faers_api.get_adverse_events") as mock_faers:
            mock_faers.return_value = {
                "drug": "aspirin",
                "total_results": 100,
                "returned": 2,
                "events": [
                    {
                        "report_id": "12345",
                        "date": "2024-01-15",
                        "serious": 1,
                        "drugs": ["aspirin"],
                        "reactions": ["Gastrointestinal hemorrhage"],
                    }
                ],
            }

            response = client.get(
                "/api/v1/drugs/faers/aspirin",
                params={"limit": 10},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["drug"] == "aspirin"
            assert data["total_results"] == 100

    def test_get_faers_default_limit(self, client):
        """Test FAERS endpoint uses default limit."""
        with patch("src.external_apis.faers_api.get_adverse_events") as mock_faers:
            mock_faers.return_value = {
                "drug": "drug",
                "total_results": 0,
                "returned": 0,
                "events": [],
            }

            response = client.get("/api/v1/drugs/faers/drug")

            assert response.status_code == 200
            # Verify default limit was used (10)
            mock_faers.assert_called_once()


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_external_api_timeout(self, client):
        """Test handling of external API timeout."""
        with patch("src.external_apis.pharmgkb_api.get_pgx_recommendation") as mock_pgx:
            mock_pgx.side_effect = TimeoutError("Connection timeout")

            response = client.get(
                "/api/v1/drugs/pgx",
                params={"gene": "CYP2C9", "drug": "warfarin"},
            )

            assert response.status_code == 502  # Bad Gateway

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/drugs/predict-toxicity",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
