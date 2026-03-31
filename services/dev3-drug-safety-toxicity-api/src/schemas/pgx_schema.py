"""
Pydantic models for pharmacogenomics data.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PGxRecommendationResponse(BaseModel):
    """Response model for PGx recommendation."""
    gene: str
    drug: str
    recommendation: str
    evidence_level: Optional[str] = None
    phenotype_categories: Optional[List[str]] = None
    source: str
    url: Optional[str] = None
    implication: Optional[str] = None
    dosing_guidance: Optional[str] = None

    class Config:
        from_attributes = True


class DrugWithPGx(BaseModel):
    """Drug information with associated PGx recommendations."""
    id: int
    name: str
    drugbank_id: Optional[str] = None
    description: Optional[str] = None
    pgx_recommendations: List[PGxRecommendationResponse] = []

    class Config:
        from_attributes = True
