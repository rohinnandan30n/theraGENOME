from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class VariantFeatures(BaseModel):
    """Base model for variant features"""
    chrom: str = Field(..., description="Chromosome (1-22, X, Y, MT)")
    pos: int = Field(..., description="Position (1-based)")
    ref: str = Field(..., description="Reference allele")
    alt: str = Field(..., description="Alternate allele")
    phyloP_score: float = Field(..., description="PhyloP evolutionary conservation score (-14 to 6)")
    SIFT_score: float = Field(..., description="SIFT impact prediction (0-1)")
    PolyPhen_score: float = Field(..., description="PolyPhen-2 score (0-1)")
    CADD_score: float = Field(..., description="CADD pathogenicity score (0-99)")
    gnomAD_freq: float = Field(..., description="gnomAD population frequency (0-1)")
    REVEL_score: float = Field(..., description="REVEL ensemble score (0-1)")
    MutationTaster_score: float = Field(..., description="MutationTaster score (0-1)")
    FathmM_score: float = Field(..., description="FathmM functional impact")
    variant_type: str = Field(..., description="Variant type (SNP, Deletion, Insertion, etc.)")
    amino_acid_change: str = Field(..., description="Amino acid change (e.g., D123H)")
    gene_symbol: Optional[str] = Field(None, description="HGNC gene symbol")


class ClassificationRequest(VariantFeatures):
    """Request model for variant classification"""
    pass


class FeatureImportance(BaseModel):
    """Feature importance from SHAP"""
    shap_value: float = Field(..., description="SHAP value for the feature")
    importance_score: float = Field(..., description="Absolute importance score")
    importance_weight: float = Field(..., description="Normalized importance weight (0-1)")
    direction: str = Field(..., description="Direction of effect (pathogenic/benign)")


class ShapValues(BaseModel):
    """SHAP values and interpretation"""
    interpretation_method: str = Field(..., description="Interpretation method used")
    shap_values: Dict[str, FeatureImportance] = Field(..., description="Top features and their importance")
    base_value: float = Field(..., description="Model base value")
    prediction_contribution: float = Field(..., description="Total contribution to prediction")


class ClassificationResponse(BaseModel):
    """Response model for classification"""
    variant_id: str = Field(..., description="Variant identifier (chrom-pos-ref-alt)")
    chrom: str = Field(..., description="Chromosome")
    pos: int = Field(..., description="Position")
    ref: str = Field(..., description="Reference allele")
    alt: str = Field(..., description="Alternate allele")
    classification: str = Field(..., description="Classification (Pathogenic/Benign/VUS)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    probabilities: Dict[str, float] = Field(..., description="Class probabilities")
    model_version: str = Field(..., description="Model version used")
    clinical_significance: str = Field(..., description="Clinical significance")
    feature_importance: Dict[str, Any] = Field(..., description="Top important features")
    shape_values: Optional[Dict[str, Any]] = Field(None, description="SHAP values and interpretation")


class BatchClassificationRequest(BaseModel):
    """Request model for batch classification"""
    variants: List[ClassificationRequest] = Field(..., description="List of variants to classify")
    max_batch_size: Optional[int] = Field(1000, description="Maximum batch size")


class BatchClassification(BaseModel):
    """Single classification result"""
    variant_id: str = Field(..., description="Variant identifier")
    classification: str = Field(..., description="Classification result")
    confidence: float = Field(..., description="Confidence score")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Class probabilities")
    error: Optional[str] = Field(None, description="Error message if classification failed")


class BatchClassificationResponse(BaseModel):
    """Response model for batch classification"""
    total_variants: int = Field(..., description="Total variants processed")
    classifications: List[BatchClassification] = Field(..., description="Classification results")
    model_version: str = Field(..., description="Model version used")


class ModelPerformance(BaseModel):
    """Model performance metrics"""
    accuracy: Optional[float] = Field(None, description="Overall accuracy")
    sensitivity: Optional[float] = Field(None, description="Sensitivity/Recall")
    specificity: Optional[float] = Field(None, description="Specificity")
    auc_roc: Optional[float] = Field(None, description="Area Under ROC Curve")
    f1_score: Optional[float] = Field(None, description="F1 Score")
    confusion_matrix: Optional[Dict[str, int]] = Field(None, description="Confusion matrix")


class ModelInfoResponse(BaseModel):
    """Response model for model information"""
    model_name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    model_type: str = Field(..., description="Type of model (sklearn, pytorch, etc.)")
    description: str = Field(..., description="Model description")
    features: List[str] = Field(..., description="List of input features")
    performance: Optional[ModelPerformance] = Field(None, description="Performance metrics")
    registered_at: str = Field(..., description="Registration timestamp")
