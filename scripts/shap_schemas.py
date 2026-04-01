"""
SHAP Value Schemas for XAI Explanation (Task 4.5)

Defines the structure for SHAP values from:
- Dev 1: Variant Classification
- Dev 2: Pathogen Resistance Prediction
- Dev 3: Drug Toxicity Prediction

These schemas inject explainability into the LLM prompt
for clinician-understandable explanations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# DEV 1: VARIANT CLASSIFICATION SHAP VALUES
# ============================================================================

class VariantFeatureImportance(BaseModel):
    """Individual feature importance for variant classification."""
    feature_name: str = Field(..., description="Genomic feature name (e.g., 'BRCA1_mutation_status')")
    shap_value: float = Field(..., description="SHAP value contribution to prediction")
    base_value: float = Field(..., description="Base prediction value")
    expected_value: float = Field(..., description="Expected model output")
    feature_value: Any = Field(..., description="Actual feature value for this sample")
    impact_direction: str = Field(..., description="'positive' or 'negative' impact on classification")
    confidence_interval: Dict[str, float] = Field(default_factory=dict, description="95% CI for SHAP value")

    class Config:
        json_schema_extra = {
            "example": {
                "feature_name": "BRCA1_pathogenic_variant",
                "shap_value": 0.45,
                "base_value": 0.12,
                "expected_value": 0.5,
                "feature_value": 1,
                "impact_direction": "positive",
                "confidence_interval": {"lower": 0.42, "upper": 0.48}
            }
        }


class VariantSHAPExplanation(BaseModel):
    """Complete SHAP explanation for variant classification."""
    sample_id: str = Field(..., description="Patient sample identifier")
    classification: str = Field(..., description="Final classification (benign/likely_benign/VUS/likely_pathogenic/pathogenic)")
    probability: float = Field(..., description="Classification confidence (0-1)")
    
    # SHAP values
    top_features: List[VariantFeatureImportance] = Field(..., description="Top 10 contributing features")
    base_value: float = Field(..., description="Model baseline prediction")
    expected_value: float = Field(..., description="Expected model output across dataset")
    
    # Feature interactions
    feature_interactions: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Second-order feature interactions (SHAP interaction indices)"
    )
    
    # Confidence metrics
    uncertainty_estimate: float = Field(..., description="Model uncertainty (std dev of predictions)")
    shap_based_confidence: float = Field(..., description="Confidence based on SHAP value consistency")
    
    # Clinical interpretation
    clinical_significance: str = Field(
        ..., 
        description="'high_risk'|'moderate_risk'|'low_risk'|'benign'"
    )
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "SAMPLE_001",
                "classification": "likely_pathogenic",
                "probability": 0.92,
                "top_features": [
                    {
                        "feature_name": "BRCA1_known_pathogenic",
                        "shap_value": 0.67,
                        "base_value": 0.15,
                        "expected_value": 0.5,
                        "feature_value": 1,
                        "impact_direction": "positive",
                        "confidence_interval": {"lower": 0.64, "upper": 0.70}
                    }
                ],
                "base_value": 0.15,
                "expected_value": 0.5,
                "clinical_significance": "high_risk"
            }
        }


# ============================================================================
# DEV 2: PATHOGEN RESISTANCE PREDICTION SHAP VALUES
# ============================================================================

class ResistanceGeneImportance(BaseModel):
    """Individual resistance gene/feature importance."""
    gene_name: str = Field(..., description="Resistance gene name (e.g., 'mecA', 'rpoB')")
    shap_value: float = Field(..., description="SHAP contribution to resistance prediction")
    gene_presence: bool = Field(..., description="Whether gene is present in sample")
    copy_number: Optional[int] = Field(None, description="Gene copy numbers if relevant")
    expression_level: Optional[float] = Field(None, description="Expression level if quantified")
    mutation_type: Optional[str] = Field(None, description="Type of mutation (SNP/indel/deletion)")
    resistance_class: str = Field(..., description="Antibiotic class conferred by this gene")
    impact_on_phenotype: str = Field(..., description="'high'|'moderate'|'low' impact on resistance")

    class Config:
        json_schema_extra = {
            "example": {
                "gene_name": "mecA",
                "shap_value": 0.55,
                "gene_presence": True,
                "copy_number": 2,
                "expression_level": 8.5,
                "mutation_type": "insertion",
                "resistance_class": "beta_lactam",
                "impact_on_phenotype": "high"
            }
        }


class ResistancePhenotypePrediction(BaseModel):
    """Predicted antibiotic resistance phenotype with SHAP."""
    antibiotic_name: str = Field(..., description="Antibiotic name (e.g., 'Methicillin')")
    predicted_susceptibility: str = Field(..., description="'susceptible'|'intermediate'|'resistant'")
    prediction_probability: float = Field(..., description="Confidence in prediction (0-1)")
    mic_prediction: Optional[float] = Field(None, description="Predicted MIC value")
    breakpoint: Optional[float] = Field(None, description="Clinical breakpoint for comparison")


class ResistanceSHAPExplanation(BaseModel):
    """Complete SHAP explanation for resistance prediction."""
    sample_id: str = Field(..., description="Pathogen sample identifier")
    organism_name: str = Field(..., description="Pathogen organism (e.g., 'Staphylococcus aureus')")
    
    # SHAP values
    contributing_genes: List[ResistanceGeneImportance] = Field(
        ..., 
        description="Top 10 resistance genes by SHAP importance"
    )
    base_value: float = Field(..., description="Model baseline (susceptible baseline)")
    expected_value: float = Field(..., description="Expected resistance probability across dataset")
    
    # Phenotype predictions
    predicted_phenotypes: List[ResistancePhenotypePrediction] = Field(
        ...,
        description="Predicted susceptibility for key antibiotics"
    )
    
    # Gene interactions
    gene_interactions: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Known resistance gene interactions (SHAP interaction indices)"
    )
    
    # Confidence
    uncertainty_estimate: float = Field(..., description="Model uncertainty")
    shap_consistency: float = Field(..., description="SHAP value consistency score")
    
    # Clinical profile
    multi_drug_resistant: bool = Field(..., description="Is organism MDR/XDR?")
    resistance_profile_type: str = Field(
        ...,
        description="'wild_type'|'single_resistance'|'multiple_resistance'|'pan_resistant'"
    )
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "PATHOGEN_001",
                "organism_name": "Staphylococcus aureus",
                "contributing_genes": [
                    {
                        "gene_name": "mecA",
                        "shap_value": 0.72,
                        "gene_presence": True,
                        "copy_number": 1,
                        "mutation_type": "insertion",
                        "resistance_class": "beta_lactam",
                        "impact_on_phenotype": "high"
                    }
                ],
                "base_value": 0.05,
                "expected_value": 0.35,
                "predicted_phenotypes": [
                    {
                        "antibiotic_name": "Methicillin",
                        "predicted_susceptibility": "resistant",
                        "prediction_probability": 0.94
                    }
                ],
                "multi_drug_resistant": True,
                "resistance_profile_type": "multiple_resistance"
            }
        }


# ============================================================================
# DEV 3: DRUG TOXICITY PREDICTION SHAP VALUES
# ============================================================================

class OrganToxicitySHAP(BaseModel):
    """Organ-level toxicity risk with SHAP importance."""
    organ_name: str = Field(..., description="Target organ (liver, kidney, heart, CNS, etc.)")
    toxicity_risk: str = Field(..., description="'none'|'mild'|'moderate'|'severe'|'critical'")
    risk_probability: float = Field(..., description="Probability of toxicity (0-1)")
    shap_base_value: float = Field(..., description="SHAP base value for this organ")
    shap_expected_value: float = Field(..., description="SHAP expected value across population")
    
    # Contributing factors
    top_risk_factors: Dict[str, float] = Field(
        ...,
        description="Top factors contributing to organ toxicity (feature: SHAP value)"
    )
    
    # Biomarkers
    biomarker_indicators: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Relevant biomarkers (ALT, creatinine, troponin, etc.)"
    )
    
    # Interaction effects
    drug_interactions: Optional[List[str]] = Field(
        default_factory=list,
        description="Other drugs that could compound toxicity"
    )
    
    monitoring_recommendations: List[str] = Field(
        default_factory=list,
        description="Clinical monitoring needed for this organ"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "organ_name": "liver",
                "toxicity_risk": "moderate",
                "risk_probability": 0.68,
                "shap_base_value": 0.15,
                "shap_expected_value": 0.25,
                "top_risk_factors": {
                    "hepatic_metabolism": 0.35,
                    "CYP3A4_interaction": 0.25,
                    "elevated_baseline_ALT": 0.15
                },
                "biomarker_indicators": {
                    "ALT": 85,
                    "AST": 72,
                    "total_bilirubin": 1.2
                },
                "monitoring_recommendations": ["Weekly LFTs for first month", "Avoid alcohol"]
            }
        }


class DrugMetabolismSHAP(BaseModel):
    """Drug metabolism pathway importance with SHAP."""
    drug_name: str = Field(..., description="Drug name")
    primary_metabolizer: str = Field(..., description="Primary enzyme pathway (CYP3A4, CYP2D6, etc.)")
    metabolizer_phenotype: str = Field(..., description="'poor'|'intermediate'|'normal'|'ultra'")
    shap_contribution: float = Field(..., description="SHAP value for this pathway")
    genetic_variants: Dict[str, str] = Field(
        default_factory=dict,
        description="Relevant pharmacogenetic variants"
    )
    predicted_drug_level: Optional[float] = Field(None, description="Predicted steady-state concentration")
    therapeutic_window: Optional[Dict[str, float]] = Field(
        None,
        description="{'min': therapeutic_min, 'max': therapeutic_max}"
    )


class ToxicitySHAPExplanation(BaseModel):
    """Complete SHAP explanation for drug toxicity prediction."""
    sample_id: str = Field(..., description="Patient sample identifier")
    drug_name: str = Field(..., description="Drug being assessed")
    
    # Overall toxicity
    overall_toxicity_risk: str = Field(..., description="'low'|'moderate'|'high'|'critical'")
    overall_risk_score: float = Field(..., description="0-1 risk score")
    
    # Organ toxicity breakdown
    organ_toxicities: List[OrganToxicitySHAP] = Field(
        ...,
        description="Toxicity risk for each relevant organ"
    )
    
    # Drug metabolism
    metabolism_profile: DrugMetabolismSHAP = Field(..., description="Drug metabolism pathway analysis")
    
    # Patient factors
    patient_risk_factors: Dict[str, float] = Field(
        default_factory=dict,
        description="Patient demographic/genetic factors affecting toxicity"
    )
    
    # Top contributing features
    top_contributing_features: Dict[str, float] = Field(
        ...,
        description="Top 10 features by SHAP importance for toxicity"
    )
    
    # Drug interactions
    significant_interactions: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Known/predicted interactions with other drugs"
    )
    
    # Recommendations
    dose_adjustment_needed: bool = Field(..., description="Is dose adjustment recommended?")
    recommended_dose_adjustment: Optional[str] = Field(None, description="Specific adjustment (e.g., '50% reduction')")
    monitoring_plan: List[str] = Field(..., description="Clinical monitoring recommendations")
    absolute_contraindications: List[str] = Field(
        default_factory=list,
        description="Absolute contraindications for this patient"
    )
    
    # Confidence
    prediction_confidence: float = Field(..., description="Model confidence (0-1)")
    shap_value_consistency: float = Field(..., description="Consistency of SHAP explanations")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "SAMPLE_001",
                "drug_name": "Warfarin",
                "overall_toxicity_risk": "moderate",
                "overall_risk_score": 0.65,
                "organ_toxicities": [
                    {
                        "organ_name": "liver",
                        "toxicity_risk": "moderate",
                        "risk_probability": 0.68,
                        "shap_base_value": 0.15,
                        "shap_expected_value": 0.25,
                        "top_risk_factors": {"hepatic_metabolism": 0.35}
                    }
                ],
                "metabolism_profile": {
                    "drug_name": "Warfarin",
                    "primary_metabolizer": "CYP2C9",
                    "metabolizer_phenotype": "intermediate",
                    "shap_contribution": 0.42
                },
                "top_contributing_features": {
                    "CYP2C9_polymorphism": 0.42,
                    "VKORC1_variant": 0.28,
                    "age_Over_65": 0.15
                },
                "dose_adjustment_needed": True,
                "recommended_dose_adjustment": "Start with 2.5mg/day instead of 5mg"
            }
        }


# ============================================================================
# UNIFIED XPLAINABILITY SCHEMA
# ============================================================================

class UnifiedXAIExplanation(BaseModel):
    """Unified XAI explanation combining all three services."""
    report_id: str = Field(..., description="TherapyDecisionReport ID")
    patient_id: str = Field(..., description="Patient identifier")
    
    # Individual SHAP explanations
    variant_explanation: Optional[VariantSHAPExplanation] = None
    resistance_explanation: Optional[ResistanceSHAPExplanation] = None
    toxicity_explanation: Optional[ToxicitySHAPExplanation] = None
    
    # Cross-service insights
    feature_interactions_cross_service: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Interactions between variant/resistance/toxicity factors"
    )
    
    # Overall confidence
    explanation_quality_score: float = Field(..., description="Overall SHAP explanation quality (0-1)")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
