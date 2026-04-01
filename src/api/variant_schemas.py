from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime


class ClinVarData(BaseModel):
    """ClinVar variant data model"""
    variation_id: Optional[str] = None
    rcv_id: Optional[str] = None
    gene_symbol: Optional[str] = None
    hgvs_expression: Optional[str] = None
    variant_type: Optional[str] = None
    clinical_significance: Optional[str] = None
    review_status: Optional[str] = None


class GnomADFrequencyData(BaseModel):
    """gnomAD allele frequency data model"""
    variant_id: Optional[str] = None
    chrom: Optional[str] = None
    pos: Optional[int] = None
    ref: Optional[str] = None
    alt: Optional[str] = None
    exome_af: Optional[float] = None
    genome_af: Optional[float] = None
    exome_ac: Optional[int] = None
    exome_an: Optional[int] = None
    genome_ac: Optional[int] = None
    genome_an: Optional[int] = None


class EnrichedVariantResponse(BaseModel):
    """Response model for enriched variant data"""
    variant_id: str
    clinvar_data: Optional[ClinVarData] = None
    gnomad_data: Optional[GnomADFrequencyData] = None
    hgvs_mapping: Optional[str] = None
    clinical_significance: Optional[str] = None
    review_status: Optional[str] = None
    allele_frequency: Optional[float] = None
    enriched_metadata: Optional[Dict[str, Any]] = None


class VariantResponse(BaseModel):
    """Generic variant response model"""
    variant_id: str
    data: Dict[str, Any]
