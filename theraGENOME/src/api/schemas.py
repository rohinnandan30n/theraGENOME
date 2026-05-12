from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IngestionResponse(BaseModel):
    """Response model for file ingestion"""
    job_id: str
    filename: str
    status: str
    variant_count: int = 0
    message: str
    

class VariantRecord(BaseModel):
    """Model for parsed variant record"""
    chrom: str
    pos: int
    ref: str
    alt: str
    qual: Optional[float]
    info: str


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    filename: str
    status: str
    variant_count: int
    created_at: str
    updated_at: str


class IngestionErrorResponse(BaseModel):
    """Response model for ingestion errors"""
    job_id: Optional[str] = None
    error: str
    message: str
    details: Optional[List[str]] = None
