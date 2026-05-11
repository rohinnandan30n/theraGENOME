"""
Comprehensive tests for the new API routes.

Tests variant, pathogen, drug, and report endpoints for:
- HTTP status codes
- Response structure and required fields
- Error handling
- Dependency injection
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from src.api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


class TestVariantRoutes:
    """Tests for variant analysis endpoints"""
    
    def test_analyze_variant_post_success(self, client):
        """Test successful POST /api/v1/variant/analyze"""
        payload = {
            "patient_id": "PAT001",
            "gene": "TP53",
            "mutation": "p.R175H",
            "chrom": "17",
            "pos": 7577121,
            "ref": "G",
            "alt": "A"
        }
        
        response = client.post("/api/v1/variant/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "prediction" in data
        assert "confidence" in data
        assert "explanation" in data
        assert "flags" in data
        assert "module_version" in data
        assert "processing_ms" in data
        
        # Check field types
        assert isinstance(data["prediction"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["explanation"], dict)
        assert isinstance(data["flags"], list)
        assert isinstance(data["module_version"], str)
        assert isinstance(data["processing_ms"], int)
        
        # Check confidence is in valid range
        assert 0 <= data["confidence"] <= 1
        
        # Check stub response marker
        assert "stub_response" in data["flags"]
    
    def test_analyze_variant_missing_required_fields(self, client):
        """Test POST /api/v1/variant/analyze with missing required fields"""
        # Missing mutation
        payload = {
            "patient_id": "PAT001",
            "gene": "TP53"
        }
        
        response = client.post("/api/v1/variant/analyze", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_variant_minimal_request(self, client):
        """Test POST /api/v1/variant/analyze with minimal required fields"""
        payload = {
            "patient_id": "PAT002",
            "gene": "BRCA1",
            "mutation": "c.5266dupC"
        }
        
        response = client.post("/api/v1/variant/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["prediction"] in ["Pathogenic", "Benign", "VUS"]
        assert 0 <= data["confidence"] <= 1


class TestPathogenRoutes:
    """Tests for pathogen analysis endpoints"""
    
    def test_analyze_pathogen_post_success(self, client):
        """Test successful POST /api/v1/pathogen/analyze"""
        payload = {
            "patient_id": "PAT003",
            "species": "Streptococcus pneumoniae",
            "gene_list": ["pbp1a", "pbp2b", "pbp2x"]
        }
        
        response = client.post("/api/v1/pathogen/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "prediction" in data
        assert "confidence" in data
        assert "antibiotic_ranking" in data
        assert "explanation" in data
        assert "flags" in data
        assert "module_version" in data
        assert "processing_ms" in data
        
        # Check antibiotic_ranking structure
        assert isinstance(data["antibiotic_ranking"], list)
        if len(data["antibiotic_ranking"]) > 0:
            first_antibiotic = data["antibiotic_ranking"][0]
            assert "antibiotic" in first_antibiotic
            assert "susceptibility" in first_antibiotic
            assert "tier" in first_antibiotic
            assert 0 <= first_antibiotic["susceptibility"] <= 1
        
        # Check prediction is valid
        assert data["prediction"] in ["Susceptible", "Resistant", "Intermediate"]
    
    def test_analyze_pathogen_missing_species(self, client):
        """Test POST /api/v1/pathogen/analyze without species"""
        payload = {
            "patient_id": "PAT004"
        }
        
        response = client.post("/api/v1/pathogen/analyze", json=payload)
        assert response.status_code == 422
    
    def test_analyze_pathogen_with_genome_file(self, client):
        """Test POST /api/v1/pathogen/analyze with genome file path"""
        payload = {
            "patient_id": "PAT005",
            "species": "Escherichia coli",
            "genome_file_path": "/data/genomes/sample.fasta"
        }
        
        response = client.post("/api/v1/pathogen/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "antibiotic_ranking" in data
        assert len(data["antibiotic_ranking"]) > 0


class TestDrugRoutes:
    """Tests for drug analysis endpoints"""
    
    def test_analyze_drug_post_success(self, client):
        """Test successful POST /api/v1/drug/analyze"""
        payload = {
            "patient_id": "PAT006",
            "drug_id": "Amoxicillin",
            "patient_labs": {
                "ALT": 25.0,
                "AST": 30.0,
                "creatinine": 0.9
            },
            "co_medications": ["Aspirin", "Lisinopril"]
        }
        
        response = client.post("/api/v1/drug/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "toxicity_scores" in data
        assert "ddi_flags" in data
        assert "pgx_flags" in data
        assert "overall_risk" in data
        assert "explanation" in data
        assert "flags" in data
        assert "module_version" in data
        assert "processing_ms" in data
        
        # Check toxicity_scores structure
        assert isinstance(data["toxicity_scores"], dict)
        for tox_key, tox_value in data["toxicity_scores"].items():
            assert isinstance(tox_key, str)
            assert isinstance(tox_value, (int, float))
            assert 0 <= tox_value <= 1
        
        # Check risk level
        assert data["overall_risk"] in ["low", "moderate", "high", "contraindicated"]
    
    def test_analyze_drug_missing_required_fields(self, client):
        """Test POST /api/v1/drug/analyze with missing drug_id"""
        payload = {
            "patient_id": "PAT007"
        }
        
        response = client.post("/api/v1/drug/analyze", json=payload)
        assert response.status_code == 422
    
    def test_analyze_drug_with_pgx_data(self, client):
        """Test POST /api/v1/drug/analyze with pharmacogenomic data"""
        payload = {
            "patient_id": "PAT008",
            "drug_id": "Codeine",
            "pgx_data": {
                "CYP2D6_status": "poor_metabolizer",
                "TPMT_status": "wild_type"
            }
        }
        
        response = client.post("/api/v1/drug/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "pgx_flags" in data
        # PGx flags may be populated based on the data
        assert isinstance(data["pgx_flags"], list)
    
    def test_analyze_drug_with_warfarin_interaction(self, client):
        """Test POST /api/v1/drug/analyze with known interaction"""
        payload = {
            "patient_id": "PAT009",
            "drug_id": "NSAIDs",
            "co_medications": ["Warfarin"]
        }
        
        response = client.post("/api/v1/drug/analyze", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "ddi_flags" in data
        assert isinstance(data["ddi_flags"], list)


class TestReportRoutes:
    """Tests for report endpoints"""
    
    def test_get_report_success(self, client):
        """Test successful GET /api/v1/reports/{patient_id}"""
        patient_id = "PAT010"
        
        response = client.get(f"/api/v1/reports/{patient_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "patient_id" in data
        assert "created_at" in data
        assert data["patient_id"] == patient_id
        
        # Check optional fields
        assert "variant_result" in data
        assert "pathogen_result" in data
        assert "drug_result" in data
        assert "narrative" in data
        assert "recommendation" in data
        
        # Check field types
        assert isinstance(data["patient_id"], str)
        assert isinstance(data["created_at"], str)
        
        # Verify created_at is valid ISO 8601 timestamp
        try:
            datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("created_at is not valid ISO 8601 format")
    
    def test_get_report_missing_patient_id(self, client):
        """Test GET /api/v1/reports/ without patient_id"""
        response = client.get("/api/v1/reports/")
        # Should be 404 or 405 (method not allowed) because no patient_id
        assert response.status_code in [404, 405]
    
    def test_get_report_multiple_patients(self, client):
        """Test GET /api/v1/reports/ for multiple different patients"""
        patient_ids = ["PAT011", "PAT012", "PAT013"]
        
        for patient_id in patient_ids:
            response = client.get(f"/api/v1/reports/{patient_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["patient_id"] == patient_id
            assert "created_at" in data
    
    def test_get_report_with_variant_data(self, client):
        """Test that report includes variant analysis data"""
        response = client.get("/api/v1/reports/PAT014")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["variant_result"] is not None:
            assert "prediction" in data["variant_result"]
            assert "confidence" in data["variant_result"]
    
    def test_get_report_with_pathogen_data(self, client):
        """Test that report includes pathogen analysis data"""
        response = client.get("/api/v1/reports/PAT015")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["pathogen_result"] is not None:
            assert "prediction" in data["pathogen_result"]
            assert "species" in data["pathogen_result"]
    
    def test_get_report_with_drug_data(self, client):
        """Test that report includes drug analysis data"""
        response = client.get("/api/v1/reports/PAT016")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["drug_result"] is not None:
            assert "overall_risk" in data["drug_result"]


class TestIntegrationAcrossRoutes:
    """Integration tests across multiple endpoints"""
    
    def test_workflow_variant_then_report(self, client):
        """Test workflow: analyze variant, then get report"""
        # First, analyze a variant
        variant_payload = {
            "patient_id": "PAT017",
            "gene": "KRAS",
            "mutation": "p.G12D"
        }
        
        variant_response = client.post("/api/v1/variant/analyze", json=variant_payload)
        assert variant_response.status_code == 200
        
        variant_data = variant_response.json()
        assert "prediction" in variant_data
        
        # Then, get the report for the same patient
        report_response = client.get("/api/v1/reports/PAT017")
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        assert report_data["patient_id"] == "PAT017"
    
    def test_workflow_all_analyses(self, client):
        """Test complete workflow: all three analyses + report"""
        patient_id = "PAT018"
        
        # Variant analysis
        variant_response = client.post("/api/v1/variant/analyze", json={
            "patient_id": patient_id,
            "gene": "TP53",
            "mutation": "p.R248Q"
        })
        assert variant_response.status_code == 200
        
        # Pathogen analysis
        pathogen_response = client.post("/api/v1/pathogen/analyze", json={
            "patient_id": patient_id,
            "species": "Mycobacterium tuberculosis"
        })
        assert pathogen_response.status_code == 200
        
        # Drug analysis
        drug_response = client.post("/api/v1/drug/analyze", json={
            "patient_id": patient_id,
            "drug_id": "Isoniazid"
        })
        assert drug_response.status_code == 200
        
        # Get consolidated report
        report_response = client.get(f"/api/v1/reports/{patient_id}")
        assert report_response.status_code == 200
        report_data = report_response.json()
        
        # Report should have data from all analyses
        assert report_data["patient_id"] == patient_id
        assert "variant_result" in report_data
        assert "pathogen_result" in report_data
        assert "drug_result" in report_data
    
    def test_all_responses_have_processing_time(self, client):
        """Test that all analysis endpoints return processing_ms"""
        # Variant
        variant_response = client.post("/api/v1/variant/analyze", json={
            "patient_id": "PAT019",
            "gene": "TP53",
            "mutation": "p.R175H"
        })
        variant_data = variant_response.json()
        assert "processing_ms" in variant_data
        assert isinstance(variant_data["processing_ms"], int)
        assert variant_data["processing_ms"] >= 0
        
        # Pathogen
        pathogen_response = client.post("/api/v1/pathogen/analyze", json={
            "patient_id": "PAT020",
            "species": "E. coli"
        })
        pathogen_data = pathogen_response.json()
        assert "processing_ms" in pathogen_data
        assert isinstance(pathogen_data["processing_ms"], int)
        
        # Drug
        drug_response = client.post("/api/v1/drug/analyze", json={
            "patient_id": "PAT021",
            "drug_id": "Metformin"
        })
        drug_data = drug_response.json()
        assert "processing_ms" in drug_data
        assert isinstance(drug_data["processing_ms"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
