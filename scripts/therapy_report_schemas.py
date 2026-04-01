"""
Therapy Decision Report Schemas
Pydantic models for request/response validation and database models
"""

from typing import List, Dict, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum


# ========== ENUMS ==========

class ReportStatus(str, Enum):
    """Report completion status"""
    COMPLETE = "complete"
    PARTIAL = "partial"
    ERROR = "error"
    TIMEOUT = "timeout"


class ServiceStatus(str, Enum):
    """Individual service call status"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    SKIPPED = "skipped"


class ToxicityRisk(str, Enum):
    """Toxicity risk level"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ========== REQUEST SCHEMAS ==========

class TherapyReportGenerateRequest(BaseModel):
    """Request to generate a therapy decision report"""
    
    patient_id: UUID = Field(..., description="UUID of patient")
    sample_id: str = Field(..., description="Sample identifier", min_length=1, max_length=50)
    drug_candidates: List[str] = Field(
        ..., 
        description="List of candidate drugs to evaluate",
        min_items=1,
        max_items=20
    )
    clinician_id: Optional[str] = Field(None, description="Clinician requesting the report")
    
    class Config:
        example = {
            "patient_id": "123e4567-e89b-12d3-a456-426614174000",
            "sample_id": "SAMPLE_001",
            "drug_candidates": ["Warfarin", "Aspirin", "Clopidogrel"]
        }


# ========== RESPONSE SCHEMAS ==========

class VariantSummary(BaseModel):
    """Summary of variant classification results from Dev 1"""
    
    chrom: str = Field(..., description="Chromosome")
    pos: int = Field(..., description="Position")
    ref: str = Field(..., description="Reference allele")
    alt: str = Field(..., description="Alternative allele")
    gene_symbol: Optional[str] = None
    amino_acid_change: Optional[str] = None
    classification: str = Field(..., description="Pathogenic/Benign/VUS")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")
    model_version: str = Field(default="v2")
    prediction_scores: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="SIFT, PolyPhen, CADD, etc."
    )
    
    class Config:
        example = {
            "chrom": "17",
            "pos": 41244394,
            "ref": "T",
            "alt": "G",
            "gene_symbol": "BRCA1",
            "amino_acid_change": "D123H",
            "classification": "Pathogenic",
            "confidence": 0.95,
            "model_version": "v2",
            "prediction_scores": {
                "CADD_score": 30.0,
                "PolyPhen_score": 0.95,
                "SIFT_score": 0.01
            }
        }


class ResistanceSummary(BaseModel):
    """Summary of resistance prediction results from Dev 2"""
    
    pathogen_id: str = Field(..., description="Pathogen identifier")
    pathogen_name: Optional[str] = None
    resistance_genes: List[Dict] = Field(
        default_factory=list,
        description="Identified resistance genes with coverage/depth"
    )
    predicted_phenotype: Optional[str] = None
    prediction_confidence: float = Field(..., ge=0, le=1)
    antimicrobial_recommendation: Optional[str] = None
    model_version: str = Field(default="v1")
    
    class Config:
        example = {
            "pathogen_id": "562",
            "pathogen_name": "Escherichia coli",
            "resistance_genes": [
                {
                    "gene_name": "blaCTX-M-15",
                    "amr_phenotype": "Beta-lactam resistance",
                    "coverage": 0.95
                }
            ],
            "predicted_phenotype": "Beta-lactam resistant",
            "prediction_confidence": 0.92,
            "model_version": "v1"
        }


class ToxicitySummary(BaseModel):
    """Summary of toxicity prediction results from Dev 3"""
    
    drug_id: str = Field(..., description="Drug identifier")
    drug_name: Optional[str] = None
    toxicity_risk: ToxicityRisk = Field(..., description="Risk level")
    toxicity_confidence: float = Field(..., ge=0, le=1)
    pgx_interactions: List[Dict] = Field(
        default_factory=list,
        description="Pharmacogenomic interactions"
    )
    adverse_events: List[Dict] = Field(
        default_factory=list,
        description="Known adverse events"
    )
    dosing_recommendation: Optional[str] = None
    model_version: str = Field(default="v1")
    
    class Config:
        example = {
            "drug_id": "DB00001",
            "drug_name": "Warfarin",
            "toxicity_risk": "Medium",
            "toxicity_confidence": 0.88,
            "pgx_interactions": [
                {
                    "gene": "CYP2C9",
                    "phenotype": "EM",
                    "impact": "Normal metabolism"
                }
            ],
            "dosing_recommendation": "Standard dose"
        }


class ServiceCallResult(BaseModel):
    """Result of a single service call"""
    
    status: ServiceStatus = Field(..., description="success/timeout/error")
    latency_ms: Optional[int] = Field(None, description="Milliseconds taken")
    error_message: Optional[str] = None
    data: Optional[Dict] = None


class TherapyDecisionReport(BaseModel):
    """Complete therapy decision report aggregating all three services"""
    
    report_id: UUID = Field(..., description="Report unique identifier")
    patient_id: UUID = Field(..., description="Patient UUID")
    sample_id: str = Field(..., description="Sample identifier")
    
    # Service results
    variant_summary: Optional[VariantSummary] = None
    resistance_summary: Optional[ResistanceSummary] = None
    toxicity_summary: Optional[ToxicitySummary] = None
    
    # Recommendations
    recommended_drug: Optional[str] = Field(None, description="Best drug recommendation")
    alternative_drugs: List[str] = Field(default_factory=list)
    recommendation_confidence: float = Field(..., ge=0, le=1)
    recommendation_rationale: Optional[str] = None
    
    # Input
    drug_candidates: List[str] = Field(...)
    
    # Status
    status: ReportStatus = Field(..., description="complete/partial/error/timeout")
    variant_service_status: ServiceStatus
    resistance_service_status: ServiceStatus
    toxicity_service_status: ServiceStatus
    
    # Metadata
    generated_at: datetime
    created_by: Optional[str] = None
    clinician_id: Optional[str] = None
    
    class Config:
        example = {
            "report_id": "550e8400-e29b-41d4-a716-446655440000",
            "patient_id": "123e4567-e89b-12d3-a456-426614174000",
            "sample_id": "SAMPLE_001",
            "variant_summary": {
                "chrom": "17",
                "pos": 41244394,
                "ref": "T",
                "alt": "G",
                "classification": "Pathogenic",
                "confidence": 0.95
            },
            "resistance_summary": {
                "pathogen_id": "562",
                "predicted_phenotype": "Beta-lactam resistant",
                "prediction_confidence": 0.92
            },
            "toxicity_summary": {
                "drug_id": "DB00001",
                "toxicity_risk": "Low",
                "toxicity_confidence": 0.88
            },
            "recommended_drug": "Warfarin",
            "recommendation_confidence": 0.91,
            "status": "complete",
            "generated_at": "2026-03-31T10:30:00Z"
        }


class TherapyReportCreateDB(BaseModel):
    """Database model for storing therapy reports"""
    
    report_id: UUID
    patient_id: UUID
    sample_id: str
    variant_summary: Optional[Dict]
    variant_classification: Optional[str]
    variant_confidence: Optional[float]
    variant_result_id: Optional[UUID]
    resistance_summary: Optional[Dict]
    predicted_phenotype: Optional[str]
    resistance_confidence: Optional[float]
    resistance_result_id: Optional[UUID]
    toxicity_summary: Optional[Dict]
    toxicity_risk: Optional[str]
    toxicity_confidence: Optional[float]
    drug_interactions: Optional[Dict]
    recommended_drug: Optional[str]
    alternative_drugs: Optional[List[str]]
    recommendation_confidence: float
    recommendation_rationale: Optional[str]
    drug_candidates: List[str]
    status: str
    variant_service_status: str
    resistance_service_status: str
    toxicity_service_status: str
    variant_latency_ms: Optional[int]
    resistance_latency_ms: Optional[int]
    toxicity_latency_ms: Optional[int]
    error_messages: Optional[Dict]
    created_by: Optional[str]
    clinician_id: Optional[str]
    created_at: datetime
    updated_at: datetime
