"""Pydantic schemas for multi-omics ingestion and processing."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import uuid


class SignificanceFlag(str, Enum):
    """RNA expression significance."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class ExpressionLevel(str, Enum):
    """Gene expression level classification."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ABSENT = "absent"


class TranscriptBiotype(str, Enum):
    """ENSEMBL transcript biotypes."""
    PROTEIN_CODING = "protein_coding"
    LNCRNA = "lncRNA"
    MIRNA = "miRNA"
    SNCRNA = "snRNA"
    SRPRNA = "snoRNA"
    PSEUDOGENE = "pseudogene"
    UNKNOWN = "unknown"


class ProteinClass(str, Enum):
    """Protein functional classification."""
    ENZYME = "enzyme"
    RECEPTOR = "receptor"
    TRANSPORTER = "transporter"
    STRUCTURAL = "structural"
    STORAGE = "storage"
    HORMONE = "hormone"
    ANTIBODY = "antibody"
    TOXIN = "toxin"
    VIRAL = "viral"
    PRION = "prion"
    UNKNOWN = "unknown"


# ==================== RNA-SEQ SCHEMAS ====================

class RNACountMatrix(BaseModel):
    """RNA-seq count matrix metadata."""
    file_format: str = Field(..., description="CSV or H5AD")
    total_genes: int = Field(..., description="Number of genes")
    total_samples: int = Field(..., description="Number of samples")
    gene_annotation: Optional[str] = Field(None, description="ENSEMBL/GENCODE version")
    sequencing_depth: Optional[Dict[str, float]] = Field(None, description="Reads per sample")


class RNANormalizationParams(BaseModel):
    """RNA-seq normalization parameters."""
    method: str = Field(default="deseq2", description="Normalization method: deseq2, tmm, rle")
    case_group: List[str] = Field(..., description="Sample IDs in case group")
    control_group: List[str] = Field(..., description="Sample IDs in control group")
    min_count: int = Field(default=10, description="Minimum count threshold")
    min_samples: int = Field(default=2, description="Min samples with count > threshold")


class RNAResult(BaseModel):
    """Single RNA-seq differential expression result."""
    patient_id: uuid.UUID
    gene_id: str
    gene_name: str
    log2_fold_change: float = Field(..., description="Log2 fold-change (case/control)")
    p_value: float = Field(..., description="Raw p-value")
    padj: float = Field(..., description="Adjusted p-value (Benjamini-Hochberg)")
    base_mean: Optional[float] = Field(None, description="Mean normalized count")
    case_mean: Optional[float] = Field(None, description="Case group mean")
    control_mean: Optional[float] = Field(None, description="Control group mean")
    significance_flag: Optional[SignificanceFlag] = Field(None)
    effect_size: Optional[float] = Field(None, description="Absolute log2FC")
    expression_level: Optional[ExpressionLevel] = Field(None)
    transcript_biotype: Optional[TranscriptBiotype] = Field(None)
    go_annotations: Optional[Dict[str, Any]] = Field(None, description="Gene Ontology terms")
    pathway_associations: Optional[Dict[str, Any]] = Field(None, description="KEGG/Reactome")
    clinical_relevance: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

    class Config:
        use_enum_values = True

    @validator('padj', 'p_value')
    def validate_pvalue(cls, v):
        if v < 0 or v > 1:
            raise ValueError("P-value must be between 0 and 1")
        return v


class RNAResultResponse(RNAResult):
    """RNA result with database metadata."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RNASeqProcessingResult(BaseModel):
    """RNA-seq processing completion event."""
    patient_id: uuid.UUID
    data_type: str = "rna-seq"
    result_table: str = "rna_results"
    record_count: int
    significant_genes: int = Field(..., description="Genes with padj < 0.05")
    upregulated: int = Field(..., description="Upregulated gene count")
    downregulated: int = Field(..., description="Downregulated gene count")
    processing_duration_seconds: float
    normalization_method: str
    case_samples: int
    control_samples: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== PROTEOMICS SCHEMAS ====================

class ProteomicsMetadata(BaseModel):
    """Proteomics data metadata."""
    file_format: str = Field(default="maxquant", description="MaxQuant output format")
    total_proteins: int = Field(..., description="Total protein groups")
    quantified_proteins: int = Field(..., description="Proteins with quantification")
    ms_engine: Optional[str] = Field(None, description="MaxQuant version or MS engine")
    lfq_column_pattern: Optional[str] = Field(None, description="LFQ intensity column names")


class PostModification(BaseModel):
    """Post-translational modification."""
    modification_type: str = Field(..., description="Phosphorylation, ubiquitination, etc.")
    site: Optional[str] = Field(None, description="Amino acid position")
    localization_probability: Optional[float] = Field(None)


class ProteinResult(BaseModel):
    """Single proteomics result (MaxQuant output)."""
    patient_id: uuid.UUID
    protein_id: str = Field(..., description="Protein group ID")
    protein_name: str
    gene_name: Optional[str] = Field(None)
    uniprot_id: Optional[str] = Field(None, description="UniProt accession")
    lfq_intensity: float = Field(..., description="Raw LFQ intensity (not log2)")
    log2_intensity: float = Field(..., description="Log2-normalized LFQ")
    peptide_count: Optional[int] = Field(None, description="Total quantified peptides")
    unique_peptides: Optional[int] = Field(None)
    razor_peptides: Optional[int] = Field(None)
    sequence_coverage: Optional[float] = Field(None, description="% sequence coverage")
    molecular_weight: Optional[float] = Field(None, description="kDa")
    protein_probability: Optional[float] = Field(None, description="Score 0-1")
    intensity_ratio: Optional[float] = Field(None, description="Case/control ratio")
    fold_change: Optional[float] = Field(None, description="Log2 fold-change")
    protein_class: Optional[ProteinClass] = Field(None)
    pathway_associations: Optional[Dict[str, Any]] = Field(None, description="KEGG/Reactome")
    post_modifications: Optional[List[PostModification]] = Field(None)
    tissue_expression: Optional[Dict[str, Any]] = Field(None)
    disease_associations: Optional[Dict[str, Any]] = Field(None)
    drug_target_info: Optional[Dict[str, Any]] = Field(None)
    clinical_significance: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

    class Config:
        use_enum_values = True

    @validator('log2_intensity')
    def validate_log2(cls, v):
        if v < -20 or v > 40:  # Reasonable bounds for log2-normalized proteomics
            raise ValueError("Log2 intensity out of reasonable range")
        return v


class ProteinResultResponse(ProteinResult):
    """Protein result with database metadata."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProteomicsProcessingResult(BaseModel):
    """Proteomics processing completion event."""
    patient_id: uuid.UUID
    data_type: str = "proteomics"
    result_table: str = "protein_results"
    record_count: int
    detected_proteins: int = Field(..., description="Proteins with LFQ > 0")
    drug_targets: int = Field(..., description="Proteins in DrugBank")
    enzymes: int = Field(..., description="Classified as enzymes")
    receptors: int = Field(..., description="Classified as receptors")
    processing_duration_seconds: float
    normalization_method: str = "log2"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== UPLOAD & INTEGRATION SCHEMAS ====================

class OmicsUploadRequest(BaseModel):
    """Generic omics upload request."""
    patient_id: uuid.UUID
    sample_id: str = Field(..., description="Sample identifier")
    data_type: str = Field(..., description="rna-seq or proteomics")
    case_samples: Optional[List[str]] = Field(None, description="For RNA-seq: case group")
    control_samples: Optional[List[str]] = Field(None, description="For RNA-seq: control group")


class OmicsIntegrationEvent(BaseModel):
    """Event published to Kafka after successful processing."""
    event_type: str = Field(default="omics_processed")
    patient_id: uuid.UUID
    data_type: str = Field(..., description="rna-seq or proteomics")
    result_table: str
    record_count: int
    processing_duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="success", description="success or error")
    error_message: Optional[str] = Field(None)


class ToxicityGuardIntegration(BaseModel):
    """Integration message to Toxicity Guard (Dev 3)."""
    patient_id: uuid.UUID
    enriched_features: Dict[str, Any] = Field(..., description="RNA + protein signals")
    rna_genes: List[str] = Field(..., description="Differentially expressed genes")
    protein_targets: List[str] = Field(..., description="Drug target proteins")
    integration_timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== STATISTICS & ANALYTICS ====================

class OmicsStatistics(BaseModel):
    """Statistics for omics ingestion."""
    total_patients: int
    rna_patients: int = Field(..., description="Patients with RNA-seq data")
    proteomics_patients: int = Field(..., description="Patients with proteomics data")
    total_genes: int = Field(..., description="Unique genes across all patients")
    total_proteins: int = Field(..., description="Unique proteins across all patients")
    significant_genes: int = Field(..., description="Genes with padj < 0.05")
    drug_target_proteins: int = Field(..., description="Proteins in drug databases")
    last_ingestion: datetime


class OmicsQualityMetrics(BaseModel):
    """Quality control metrics for omics data."""
    data_type: str
    median_sequence_depth: Optional[float] = Field(None, description="RNA-seq only")
    median_peptides_per_protein: Optional[float] = Field(None, description="Proteomics only")
    missing_data_percentage: float
    outlier_samples: List[str]
    quality_pass_rate: float = Field(..., description="0-1 scale")
    flags: List[str] = Field(default_factory=list, description="QC warnings")
